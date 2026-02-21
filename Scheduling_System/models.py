# models.py
# Simple data models used by the scheduler and database layers.
# Using dataclasses for concise, self-documenting data containers.

from dataclasses import dataclass
from datetime import datetime

@dataclass
class Person:
    """Base class representing a person with a name."""
    name: str

    def get_name(self) -> str:
        """Return the person's name."""
        return self.name

@dataclass
class Patient(Person):
    """Patient entity. Extendable later with more attributes (DOB, MRN, contact, etc.)."""
    pass

@dataclass
class Doctor(Person):
    """Doctor entity. Extendable later with specialty, id, contact info, etc."""
    pass

@dataclass
class Appointment:
    """
    Appointment value object.
    Stores patient name, doctor name and the appointment datetime as a datetime object.
    Use this class to pass appointment info between layers.
    """
    patient_name: str
    doctor_name: str
    appointment_datetime: datetime
    id: int | None = None          # optional DB id
    status: str = "booked"         # booked / cancelled / completed
    created_at: datetime | None = None
