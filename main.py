
import tkinter as tk
from database import DatabaseManager
from scheduler import Scheduler
from gui import AppointmentGUI

if __name__ == "__main__":
    db = DatabaseManager()
    scheduler = Scheduler(db)

    root = tk.Tk()
    app = AppointmentGUI(root, scheduler)
    root.mainloop()
