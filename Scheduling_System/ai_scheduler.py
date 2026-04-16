# ai_scheduler.py
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from typing import Optional, List, Dict


@dataclass
class AISuggestion:
    suggested_time: str
    confidence: float
    reason: str
    model_name: str
    model_version: str


class BaseAIScheduler(ABC):
    """
    Strategy interface for AI scheduling models.
    Future models can implement ML-based prediction, no-show scoring,
    patient preference ranking, etc.
    """

    @property
    @abstractmethod
    def model_name(self) -> str:
        pass

    @property
    @abstractmethod
    def model_version(self) -> str:
        pass

    @abstractmethod
    def suggest_time(
        self,
        doctor_name: str,
        date_str: str,
        db,
        requested_time: str
    ) -> Optional[AISuggestion]:
        pass


class SmartAIScheduler(BaseAIScheduler):
    """
    Simple rule-based AI placeholder.
    Works like an explainable recommendation engine until a real ML model is added.
    """

    @property
    def model_name(self) -> str:
        return "SmartAIScheduler"

    @property
    def model_version(self) -> str:
        return "1.0"

    def suggest_time(self, doctor_name: str, date_str: str, db, requested_time: str) -> Optional[AISuggestion]:
        available_slots = [
            "09:00", "09:30", "10:00", "10:30",
            "11:00", "11:30", "12:00", "12:30",
            "13:00", "13:30", "14:00", "14:30",
            "15:00", "15:30", "16:00", "16:30"
        ]

        try:
            requested_dt = datetime.strptime(f"{date_str} {requested_time}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None

        doctor_id = db.get_or_create_doctor(doctor_name)

        best_slot = None
        best_distance = None

        for slot in available_slots:
            slot_dt = datetime.strptime(f"{date_str} {slot}", "%Y-%m-%d %H:%M")

            # skip past times
            if slot_dt <= datetime.now():
                continue

            # skip conflicts
            if db.check_conflict(doctor_id, slot_dt):
                continue

            distance = abs((slot_dt - requested_dt).total_seconds())

            if best_distance is None or distance < best_distance:
                best_slot = slot
                best_distance = distance

        if not best_slot:
            return None

        reason = (
            f"Requested slot was unavailable. Suggested nearest available "
            f"30-minute slot for {doctor_name} on {date_str}."
        )

        return AISuggestion(
            suggested_time=best_slot,
            confidence=0.78,
            reason=reason,
            model_name=self.model_name,
            model_version=self.model_version
        )


class FallbackAIScheduler(BaseAIScheduler):
    """
    Minimal fallback strategy if no intelligent model is configured.
    """

    @property
    def model_name(self) -> str:
        return "FallbackAIScheduler"

    @property
    def model_version(self) -> str:
        return "1.0"

    def suggest_time(self, doctor_name: str, date_str: str, db, requested_time: str) -> Optional[AISuggestion]:
        return None


class AISchedulerRegistry:
    """
    Small registry to support hot-swappable scheduling models.
    Can later be extended to load models by config, version, or validation status.
    """

    def __init__(self, active_model: BaseAIScheduler):
        self._active_model = active_model

    def get_active_model(self) -> BaseAIScheduler:
        return self._active_model

    def swap_model(self, new_model: BaseAIScheduler) -> None:
        self._active_model = new_model
