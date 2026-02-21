# database.py
# Improved DatabaseManager with normalized schema (patients, doctors, appointments),
# unique constraint to avoid double-booking at the DB level, and helper methods.
# Uses sqlite3.Row as row factory so callers can access columns by name.

import sqlite3
from datetime import datetime
from typing import Optional, List, Dict

ISO_FMT = "%Y-%m-%dT%H:%M:%S"  # ISO-like format for storing datetimes as text

class DatabaseError(Exception):
    """Generic database-layer exception wrapper."""
    pass

class DatabaseManager:
    def __init__(self, db_name: str = "appointments.db"):
        """
        Open a connection to the SQLite database and create tables if they don't exist.
        - check_same_thread=False allows using the connection across threads if needed (simple GUIs).
        - We enable foreign keys to keep referential integrity.
        """
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row  # return rows that behave like dicts
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()

    def create_tables(self):
        """Create normalized tables: patients, doctors, appointments with a uniqueness constraint
        to prevent double-booking a doctor at the same datetime."""
        with self.conn:
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """)
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );
            """)
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_id INTEGER NOT NULL,
                doctor_id INTEGER NOT NULL,
                appointment_datetime TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'booked',
                created_at TEXT NOT NULL,
                FOREIGN KEY (patient_id) REFERENCES patients(id) ON DELETE CASCADE,
                FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE,
                UNIQUE (doctor_id, appointment_datetime) -- DB-level protection against double-book
            );
            """)
            # helpful index for queries by doctor and datetime
            self.conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_appointments_doctor_datetime
            ON appointments(doctor_id, appointment_datetime);
            """)

    # ------------- Patient / Doctor helpers -------------
    def get_or_create_patient(self, name: str) -> int:
        """Return patient id for a given name; create the patient row if it doesn't exist."""
        name = name.strip()
        if not name:
            raise DatabaseError("Patient name cannot be empty.")
        cur = self.conn.execute("SELECT id FROM patients WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        with self.conn:
            cur = self.conn.execute("INSERT INTO patients (name) VALUES (?)", (name,))
            return cur.lastrowid

    def get_or_create_doctor(self, name: str) -> int:
        """Return doctor id for a given name; create the doctor row if it doesn't exist."""
        name = name.strip()
        if not name:
            raise DatabaseError("Doctor name cannot be empty.")
        cur = self.conn.execute("SELECT id FROM doctors WHERE name = ?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        with self.conn:
            cur = self.conn.execute("INSERT INTO doctors (name) VALUES (?)", (name,))
            return cur.lastrowid

    # ------------- Appointment operations -------------
    def add_appointment(self, patient_id: int, doctor_id: int, appointment_dt: datetime) -> int:
        """
        Insert an appointment. The UNIQUE constraint on (doctor_id, appointment_datetime)
        will raise an sqlite3.IntegrityError if a conflict exists — caller should handle/translate it.
        Returns the inserted appointment id.
        """
        appt_txt = appointment_dt.strftime(ISO_FMT)
        created_at = datetime.now().strftime(ISO_FMT)
        try:
            with self.conn:
                cur = self.conn.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_datetime, created_at)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, doctor_id, appt_txt, created_at))
                return cur.lastrowid
        except sqlite3.IntegrityError as e:
            # Translate DB integrity error (e.g. UNIQUE constraint violation) to a clearer exception
            raise DatabaseError("Conflict: doctor already has an appointment at that time.") from e

    def check_conflict(self, doctor_id: int, appointment_dt: datetime) -> bool:
        """Return True if the given doctor already has an appointment at that datetime."""
        appt_txt = appointment_dt.strftime(ISO_FMT)
        cur = self.conn.execute("""
            SELECT 1 FROM appointments
            WHERE doctor_id = ? AND appointment_datetime = ? AND status = 'booked'
            LIMIT 1
        """, (doctor_id, appt_txt))
        return cur.fetchone() is not None

    def get_appointments(self, limit: Optional[int] = 100, doctor_name: Optional[str] = None) -> List[Dict]:
        """
        Return upcoming appointments (joined with patient/doctor names).
        Optional filters: doctor_name (exact match) and limit number of rows.
        Each result is returned as a dict for easy consumption by UI.
        """
        sql = """
        SELECT a.id, p.name as patient_name, d.name as doctor_name,
               a.appointment_datetime, a.status, a.created_at
        FROM appointments a
        JOIN patients p ON a.patient_id = p.id
        JOIN doctors d ON a.doctor_id = d.id
        WHERE a.status = 'booked'
        """
        params = []
        if doctor_name:
            sql += " AND d.name = ?"
            params.append(doctor_name)
        sql += " ORDER BY a.appointment_datetime ASC LIMIT ?"
        params.append(limit)

        cur = self.conn.execute(sql, params)
        rows = cur.fetchall()
        results = []
        for r in rows:
            # parse the stored ISO text back to a datetime object for the caller
            results.append({
                "id": r["id"],
                "patient_name": r["patient_name"],
                "doctor_name": r["doctor_name"],
                "appointment_datetime": datetime.strptime(r["appointment_datetime"], ISO_FMT),
                "status": r["status"],
                "created_at": datetime.strptime(r["created_at"], ISO_FMT),
            })
        return results

    def reschedule_appointment(self, appointment_id: int, new_dt: datetime) -> None:
        """
        Attempt to update an appointment's datetime.
        The UNIQUE constraint will prevent double-booking. Raise DatabaseError on conflict.
        """
        new_txt = new_dt.strftime(ISO_FMT)
        try:
            with self.conn:
                self.conn.execute("""
                    UPDATE appointments
                    SET appointment_datetime = ?
                    WHERE id = ?
                """, (new_txt, appointment_id))
        except sqlite3.IntegrityError as e:
            raise DatabaseError("Conflict when rescheduling: doctor already booked at that time.") from e

    def cancel_appointment(self, appointment_id: int) -> None:
        """Mark an appointment as cancelled. We keep a row for history."""
        with self.conn:
            self.conn.execute("""
                UPDATE appointments
                SET status = 'cancelled'
                WHERE id = ?
            """, (appointment_id,))

    def close(self):
        """Close the DB connection cleanly."""
        self.conn.close()

