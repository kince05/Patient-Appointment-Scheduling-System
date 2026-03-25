# scheduler.py
# High-level scheduling logic and validation (business rules).
# This layer is responsible for validating user input, converting to datetime objects,
# checking for conflicts, and calling the database layer.

from datetime import datetime, time
from typing import Optional, List
from models import Patient, Doctor, Appointment
from database import DatabaseManager, DatabaseError

class SchedulingError(Exception):
    """Raise this when user-facing scheduling validations fail."""
    pass

class Scheduler:
    # business-hour constants (24-hour)
    WORK_START = 9      # 09:00 inclusive
    WORK_END = 17       # 17:00 exclusive: last valid slot is 16:30
    SLOT_MINUTES = 30   # 30-minute slots

    def __init__(self, database: DatabaseManager):
        """
        Scheduler receives a DatabaseManager instance via dependency injection.
        This makes it easy to substitute a mock DB in tests.
        """
        self.db = database

    def _parse_datetime(self, date_str: str, time_str: str) -> datetime:
        """
        Convert date and time strings into a single datetime object.
        Validates formatting and returns a datetime.
        """
        try:
            # parse date like "2026-02-20" and time like "09:30"
            date_part = datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
            time_part = datetime.strptime(time_str.strip(), "%H:%M").time()
        except ValueError as e:
            raise SchedulingError("Invalid date or time format. Use YYYY-MM-DD and HH:MM.") from e

        # combine into a full datetime
        combined = datetime.combine(date_part, time_part)
        return combined

    def _validate_slot_and_business_hours(self, dt: datetime) -> None:
        """
        Validate that the datetime is:
        - on a 0 or 30 minute mark
        - within business hours (WORK_START <= hour < WORK_END)
        - in the future (not booking in the past)
        """
        if dt.minute not in (0, self.SLOT_MINUTES):
            raise SchedulingError(f"Appointments must be on {self.SLOT_MINUTES}-minute boundaries (0 or {self.SLOT_MINUTES}).")

        if not (self.WORK_START <= dt.hour < self.WORK_END or (dt.hour == self.WORK_END - 1 and dt.minute == 30 and dt.hour < self.WORK_END)):
            # the additional check ensures 16:30 is allowed when WORK_END==17
            # but prevents 17:00 or later
            pass  # we already validated below more simply

        # simpler explicit check: valid start times are hours in [WORK_START, WORK_END-1]
        # and minute in {0, 30}, or hour == WORK_END -1 with minute==30 is allowed (e.g. 16:30)
        if not (self.WORK_START <= dt.hour < self.WORK_END or (dt.hour == self.WORK_END - 1 and dt.minute == 30)):
            raise SchedulingError(f"Appointment must be during working hours ({self.WORK_START}:00–{self.WORK_END}:00).")

        # prevent booking in the past (local time)
        now = datetime.now()
        if dt <= now:
            raise SchedulingError("Cannot book an appointment in the past. Please select a future date and time.")

    def book_appointment(self, patient_name: str, doctor_name: str, date_str: str, time_str: str) -> int:
        """
        High-level booking method:
         - validates inputs
         - ensures patient/doctor records exist (creates as necessary)
         - checks for conflicts using DB helper
         - inserts the appointment
        Returns: appointment id on success.
        """
        # basic non-empty checks
        if not patient_name or not doctor_name:
            raise SchedulingError("Patient and Doctor names must be provided.")

        # parse date/time and validate slot & business hours
        appt_dt = self._parse_datetime(date_str, time_str)
        self._validate_slot_and_business_hours(appt_dt)

        # normalize names
        p_name = patient_name.strip()
        d_name = doctor_name.strip()

        # get patient/doctor ids (create if they don't exist)
        try:
            patient_id = self.db.get_or_create_patient(p_name)
            doctor_id = self.db.get_or_create_doctor(d_name)
        except DatabaseError as e:
            raise SchedulingError(f"Database error while finding/creating patient or doctor: {e}") from e

        # check conflict at DB level (pre-check gives nicer UX, DB will also block race conditions)
        if self.db.check_conflict(doctor_id, appt_dt):
            raise SchedulingError("Doctor already booked at that time.")

        # attempt to add appointment (DB-level unique constraint protects against race conditions)
        try:
            appt_id = self.db.add_appointment(patient_id, doctor_id, appt_dt)
            return appt_id
        except DatabaseError as e:
            # catch DB conflicts and convert to SchedulingError for UI
            raise SchedulingError(str(e)) from e

    def get_appointments(self, limit: int = 100, doctor_name: Optional[str] = None) -> List[Appointment]:
        """
        Retrieve upcoming appointments and return them as Appointment objects.
        This decouples the DB representation from the UI/business objects.
        """
        rows = self.db.get_appointments(limit=limit, doctor_name=doctor_name)
        result = []
        for r in rows:
            result.append(Appointment(
                patient_name=r["patient_name"],
                doctor_name=r["doctor_name"],
                appointment_datetime=r["appointment_datetime"],
                id=r["id"],
                status=r["status"],
                created_at=r["created_at"]
            ))
        return result

    def reschedule(self, appointment_id: int, new_date: str, new_time: str) -> None:
        """
        Reschedule an appointment by id. Validates the new datetime and attempts to update.
        """
        new_dt = self._parse_datetime(new_date, new_time)
        self._validate_slot_and_business_hours(new_dt)
        try:
            self.db.reschedule_appointment(appointment_id, new_dt)
        except DatabaseError as e:
            raise SchedulingError(str(e)) from e

    def cancel(self, appointment_id: int) -> None:
        """Cancel (mark as cancelled) an appointment row in the DB."""
        self.db.cancel_appointment(appointment_id)
