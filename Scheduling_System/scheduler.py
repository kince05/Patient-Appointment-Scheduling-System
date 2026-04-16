# scheduler.py
from __future__ import annotations
from datetime import datetime
from threading import RLock
from typing import Optional, List

from models import Appointment
from database import DatabaseManager, DatabaseError
from ai_scheduler import BaseAIScheduler, AISuggestion


class SchedulingError(Exception):
    pass


class Scheduler:
    WORK_START = 9
    WORK_END = 17
    SLOT_MINUTES = 30

    def __init__(self, db: DatabaseManager, ai_model: Optional[BaseAIScheduler] = None):
        self.db = db
        self.ai_model = ai_model
        self.lock = RLock()

    def set_ai_model(self, ai_model: BaseAIScheduler) -> None:
        """
        Supports safe model swapping without changing core scheduling logic.
        """
        self.ai_model = ai_model

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        try:
            return datetime.strptime(
                f"{date_str.strip()} {time_str.strip()}",
                "%Y-%m-%d %H:%M"
            )
        except ValueError as e:
            raise SchedulingError("Invalid date/time format. Use YYYY-MM-DD and HH:MM.") from e

    def _validate(self, dt: datetime) -> None:
        if dt.minute not in (0, 30):
            raise SchedulingError("Appointments must use 30-minute time slots.")

        if not (self.WORK_START <= dt.hour < self.WORK_END):
            raise SchedulingError("Appointment must be within working hours (09:00–17:00).")

        if dt.hour == self.WORK_END - 1 and dt.minute not in (0, 30):
            raise SchedulingError("Invalid final scheduling slot.")

        if dt >= datetime.strptime(dt.strftime("%Y-%m-%d 17:00"), "%Y-%m-%d %H:%M"):
            raise SchedulingError("Appointments cannot start at or after 17:00.")

        if dt <= datetime.now():
            raise SchedulingError("Appointment must be scheduled in the future.")

    def _normalize_name(self, value: str, label: str) -> str:
        cleaned = (value or "").strip()
        if not cleaned:
            raise SchedulingError(f"{label} is required.")
        return cleaned

    def _build_ai_conflict_message(self, suggestion: Optional[AISuggestion]) -> str:
        if not suggestion:
            return "Doctor already booked at that time."

        return (
            f"Doctor already booked at that time. "
            f"Suggested slot: {suggestion.suggested_time} "
            f"(Model: {suggestion.model_name} v{suggestion.model_version}, "
            f"Confidence: {suggestion.confidence:.0%}). "
            f"Reason: {suggestion.reason}"
        )

    def book_appointment(self, patient_name: str, doctor_name: str, date_str: str, time_str: str) -> int:
        with self.lock:
            patient_name = self._normalize_name(patient_name, "Patient name")
            doctor_name = self._normalize_name(doctor_name, "Doctor")
            date_str = self._normalize_name(date_str, "Date")
            time_str = self._normalize_name(time_str, "Time")

            dt = self._parse_datetime(date_str, time_str)
            self._validate(dt)

            try:
                patient_id = self.db.get_or_create_patient(patient_name)
                doctor_id = self.db.get_or_create_doctor(doctor_name)
            except DatabaseError as e:
                raise SchedulingError(f"Could not prepare booking records: {e}") from e

            if self.db.check_conflict(doctor_id, dt):
                suggestion = None
                if self.ai_model:
                    suggestion = self.ai_model.suggest_time(doctor_name, date_str, self.db, time_str)

                if hasattr(self.db, "add_audit_log"):
                    self.db.add_audit_log(
                        action="BOOKING_CONFLICT",
                        details=self._build_ai_conflict_message(suggestion)
                    )

                raise SchedulingError(self._build_ai_conflict_message(suggestion))

            try:
                appointment_id = self.db.add_appointment(patient_id, doctor_id, dt)

                if hasattr(self.db, "add_audit_log"):
                    self.db.add_audit_log(
                        action="BOOK_APPOINTMENT",
                        details=f"Appointment {appointment_id} booked for {patient_name} with {doctor_name} at {dt}"
                    )

                return appointment_id

            except DatabaseError as e:
                raise SchedulingError(str(e)) from e

    def get_appointments(self, limit: int = 100, doctor_name: Optional[str] = None) -> List[Appointment]:
        rows = self.db.get_appointments(limit=limit, doctor_name=doctor_name)
        return [
            Appointment(
                id=row["id"],
                patient_name=row["patient_name"],
                doctor_name=row["doctor_name"],
                appointment_datetime=row["appointment_datetime"],
                status=row["status"],
                created_at=row["created_at"]
            )
            for row in rows
        ]

    def cancel(self, appointment_id: int) -> None:
        try:
            self.db.cancel_appointment(appointment_id)
            if hasattr(self.db, "add_audit_log"):
                self.db.add_audit_log(
                    action="CANCEL_APPOINTMENT",
                    details=f"Appointment {appointment_id} cancelled"
                )
        except DatabaseError as e:
            raise SchedulingError(str(e)) from e

    def reschedule(self, appointment_id: int, date_str: str, time_str: str, doctor_name: Optional[str] = None) -> None:
        with self.lock:
            dt = self._parse_datetime(date_str, time_str)
            self._validate(dt)

            # Optional safer conflict logic if doctor_name is known
            if doctor_name:
                doctor_id = self.db.get_or_create_doctor(doctor_name)
                if self.db.check_conflict(doctor_id, dt):
                    suggestion = None
                    if self.ai_model:
                        suggestion = self.ai_model.suggest_time(doctor_name, date_str, self.db, time_str)
                    raise SchedulingError(self._build_ai_conflict_message(suggestion))

            try:
                self.db.reschedule_appointment(appointment_id, dt)
                if hasattr(self.db, "add_audit_log"):
                    self.db.add_audit_log(
                        action="RESCHEDULE_APPOINTMENT",
                        details=f"Appointment {appointment_id} moved to {dt}"
                    )
            except DatabaseError as e:
                raise SchedulingError(str(e)) from e

    def get_doctors(self) -> List[str]:
        return self.db.get_all_doctors()
