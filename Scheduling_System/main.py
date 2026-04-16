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

    # AI model (hot-swappable)
    ai_model = SmartAIScheduler()

    scheduler = Scheduler(db, ai_model=ai_model)
    auth = AuthService(db)

    # Create default admin
    try:
        db.create_user("admin", "admin123", "admin")
    except:
        pass

    try:
        db.get_or_create_doctor("Dr Smith")
        db.get_or_create_doctor("Dr Adams")
        db.get_or_create_doctor("Dr Lee")
    except:
        pass


    root = ctk.CTk()

    def start_app(user):
        root.destroy()
        main_root = tk.Tk()
        AppointmentGUI(main_root, scheduler, user)
        main_root.mainloop()

    LoginGUI(root, auth, start_app)
    root.mainloop()
    db.close()

if __name__ == "__main__":
    main()
