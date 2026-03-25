import sqlite3
import hashlib
from datetime import datetime
from typing import Optional, List, Dict

ISO_FMT = "%Y-%m-%dT%H:%M:%S"

class DatabaseError(Exception):
    pass

class DatabaseManager:
    def __init__(self, db_name: str = "appointments.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()

    def create_tables(self):
        with self.conn:
            # USERS TABLE (NEW)
            self.conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('admin','doctor','patient'))
            );
            """)

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
                UNIQUE (doctor_id, appointment_datetime)
            );
            """)

    # -------- AUTH METHODS --------
    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str, role: str) -> int:
        if not username or not password:
            raise DatabaseError("Username and password required.")

        password_hash = self._hash_password(password)

        try:
            with self.conn:
                cur = self.conn.execute(
                    "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                    (username, password_hash, role)
                )
                return cur.lastrowid
        except sqlite3.IntegrityError:
            raise DatabaseError("Username already exists.")

    def authenticate_user(self, username: str, password: str):
        password_hash = self._hash_password(password)

        cur = self.conn.execute(
            "SELECT id, username, role FROM users WHERE username=? AND password_hash=?",
            (username, password_hash)
        )
        row = cur.fetchone()

        if not row:
            return None

        return dict(row)

    # -------- EXISTING METHODS (UNCHANGED) --------
    def get_or_create_patient(self, name: str) -> int:
        cur = self.conn.execute("SELECT id FROM patients WHERE name=?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        with self.conn:
            cur = self.conn.execute("INSERT INTO patients (name) VALUES (?)", (name,))
            return cur.lastrowid

    def get_or_create_doctor(self, name: str) -> int:
        cur = self.conn.execute("SELECT id FROM doctors WHERE name=?", (name,))
        row = cur.fetchone()
        if row:
            return row["id"]
        with self.conn:
            cur = self.conn.execute("INSERT INTO doctors (name) VALUES (?)", (name,))
            return cur.lastrowid

    def add_appointment(self, patient_id: int, doctor_id: int, appointment_dt: datetime) -> int:
        try:
            with self.conn:
                cur = self.conn.execute("""
                    INSERT INTO appointments (patient_id, doctor_id, appointment_datetime, created_at)
                    VALUES (?, ?, ?, ?)
                """, (patient_id, doctor_id, appointment_dt.strftime(ISO_FMT), datetime.now().strftime(ISO_FMT)))
                return cur.lastrowid
        except sqlite3.IntegrityError:
            raise DatabaseError("Doctor already booked at that time.")

    def check_conflict(self, doctor_id: int, appointment_dt: datetime) -> bool:
        cur = self.conn.execute("""
            SELECT 1 FROM appointments
            WHERE doctor_id=? AND appointment_datetime=? AND status='booked'
        """, (doctor_id, appointment_dt.strftime(ISO_FMT)))
        return cur.fetchone() is not None

    def get_appointments(self, limit=100, doctor_name=None):
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
            results.append({
                "id": r["id"],
                "patient_name": r["patient_name"],
                "doctor_name": r["doctor_name"],
                "appointment_datetime": datetime.strptime(r["appointment_datetime"], ISO_FMT),  # <-- convert here
                "status": r["status"],
                "created_at": datetime.strptime(r["created_at"], ISO_FMT),  # <-- convert here
        })
        return results

    def reschedule_appointment(self, appointment_id: int, new_dt: datetime):
        with self.conn:
            self.conn.execute("""
            UPDATE appointments SET appointment_datetime=? WHERE id=?
            """, (new_dt.strftime(ISO_FMT), appointment_id))

    def cancel_appointment(self, appointment_id: int):
        with self.conn:
            self.conn.execute("""
            UPDATE appointments SET status='cancelled' WHERE id=?
            """, (appointment_id,))

    def close(self):
        self.conn.close()
