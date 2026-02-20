import sqlite3

class DatabaseManager:
    def __init__(self, db_name="appointments.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_name TEXT NOT NULL,
            doctor_name TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL
        )
        """)
        self.conn.commit()

    def add_appointment(self, patient, doctor, date, time):
        self.cursor.execute("""
        INSERT INTO appointments (patient_name, doctor_name, date, time)
        VALUES (?, ?, ?, ?)
        """, (patient, doctor, date, time))
        self.conn.commit()

    def get_appointments(self):
        self.cursor.execute("SELECT * FROM appointments")
        return self.cursor.fetchall()

    def check_conflict(self, doctor, date, time):
        self.cursor.execute("""
        SELECT * FROM appointments
        WHERE doctor_name=? AND date=? AND time=?
        """, (doctor, date, time))
        return self.cursor.fetchone()
