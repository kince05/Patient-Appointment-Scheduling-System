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
    id: int
    patient_name: str
    doctor_name: str
    appointment_datetime: datetime
    status: str
    created_at: datetime
