# main.py
# Application entrypoint: wire DB -> Scheduler -> GUI and start the Tk event loop.

import tkinter as tk
from database import DatabaseManager
from scheduler import Scheduler
from gui import AppointmentGUI

def main():
    # initialize database manager (persistence layer)
    db = DatabaseManager("appointments.db")

    # create scheduler (business logic) and inject the DB manager into it
    scheduler = Scheduler(db)

    # start GUI and inject scheduler into GUI layer
    root = tk.Tk()
    app = AppointmentGUI(root, scheduler)
    root.mainloop()

    # on exit, close DB connection
    db.close()

if __name__ == "__main__":
    main()
