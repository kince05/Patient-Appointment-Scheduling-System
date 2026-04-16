# main.py
import tkinter as tk
import customtkinter as ctk

from database import DatabaseManager
from scheduler import Scheduler
from gui import AppointmentGUI
from auth import AuthService
from login_gui import LoginGUI
from ai_scheduler import SmartAIScheduler


def main():
    db = DatabaseManager("appointments.db")
    ai_model = SmartAIScheduler()
    scheduler = Scheduler(db, ai_model=ai_model)
    auth = AuthService(db)

    try:
        db.create_user("admin", "admin123", "admin")
    except Exception:
        pass

    for doctor in ["Dr Smith", "Dr Adams", "Dr Lee"]:
        try:
            db.get_or_create_doctor(doctor)
        except Exception:
            pass

    root = ctk.CTk()

    def start_app(user):
        root.destroy()
        app_root = ctk.CTk()
        AppointmentGUI(app_root, scheduler, user)
        app_root.mainloop()

    LoginGUI(root, auth, start_app)
    root.mainloop()
    db.close()


if __name__ == "__main__":
    main()
