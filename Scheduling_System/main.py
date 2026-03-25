import tkinter as tk
from database import DatabaseManager
from scheduler import Scheduler
from gui import AppointmentGUI
from auth import AuthService
from login_gui import LoginGUI

def main():
    db = DatabaseManager("appointments.db")
    scheduler = Scheduler(db)
    auth = AuthService(db)

    # create default admin
    try:
        db.create_user("admin", "admin123", "admin")
    except:
        pass

    root = tk.Tk()

    def start_app(user):
        root.destroy()
        main_root = tk.Tk()
        AppointmentGUI(main_root, scheduler)
        main_root.mainloop()

    LoginGUI(root, auth, start_app)
    root.mainloop()

    db.close()

if __name__ == "__main__":
    main()
