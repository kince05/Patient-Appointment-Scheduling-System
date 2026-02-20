from models import Patient, Doctor
from datetime import datetime

class SchedulingError(Exception):
    pass


class Scheduler:

    WORK_START = 9
    WORK_END = 17
    SLOT_MINUTES = 30

    def __init__(self, database):
        self.db = database

    def validate_datetime(self, date_str, time_str):
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            time_obj = datetime.strptime(time_str, "%H:%M")
        except ValueError:
            raise SchedulingError("Invalid date or time format.")

        if time_obj.minute not in (0, 30):
            raise SchedulingError("Appointments must be in 30-minute slots.")

        if not (self.WORK_START <= time_obj.hour < self.WORK_END):
            raise SchedulingError("Appointment must be during working hours (9–17).")

    def book_appointment(self, patient_name, doctor_name, date, time):

        if not patient_name or not doctor_name:
            raise SchedulingError("All fields must be filled.")

        self.validate_datetime(date, time)

        if self.db.check_conflict(doctor_name, date, time):
            raise SchedulingError("Doctor already booked at that time.")

        patient = Patient(patient_name)
        doctor = Doctor(doctor_name)

        self.db.add_appointment(
            patient.get_name(),
            doctor.get_name(),
            date,
            time
        )

    def get_appointments(self):
        return self.db.get_appointments()
