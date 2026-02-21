# gui.py
# Tkinter-based GUI with clearer layout and a Treeview for displaying appointments.
# The GUI calls methods on Scheduler to perform actions and converts exceptions into user messages.

import tkinter as tk
from tkinter import messagebox, ttk
from scheduler import Scheduler, SchedulingError
from database import DatabaseManager
from typing import Optional

class AppointmentGUI:
    def __init__(self, root: tk.Tk, scheduler: Scheduler):
        """
        Initialize the GUI widgets and wire up event handlers.
        - root: tk.Tk() main window
        - scheduler: instance of Scheduler injected for testability
        """
        self.root = root
        self.scheduler = scheduler

        self.root.title("Patient Appointment Scheduling System")
        self.root.geometry("700x450")

        # --- Input fields ---
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.X)

        tk.Label(frame, text="Patient Name").grid(row=0, column=0, sticky="w")
        tk.Label(frame, text="Doctor Name").grid(row=1, column=0, sticky="w")
        tk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=(20,0))
        tk.Label(frame, text="Time (HH:MM)").grid(row=1, column=2, sticky="w", padx=(20,0))

        self.patient_entry = tk.Entry(frame, width=25)
        self.doctor_entry = tk.Entry(frame, width=25)
        self.date_entry = tk.Entry(frame, width=15)
        self.time_entry = tk.Entry(frame, width=10)

        self.patient_entry.grid(row=0, column=1, pady=2)
        self.doctor_entry.grid(row=1, column=1, pady=2)
        self.date_entry.grid(row=0, column=3, pady=2)
        self.time_entry.grid(row=1, column=3, pady=2)

        # Buttons
        btn_frame = tk.Frame(root, pady=8)
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="Book Appointment", command=self.book).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="View Appointments", command=self.view).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear Fields", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        # --- Treeview for showing appointments ---
        columns = ("id", "patient", "doctor", "datetime", "status")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("patient", text="Patient")
        self.tree.heading("doctor", text="Doctor")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("status", text="Status")
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("patient", width=180)
        self.tree.column("doctor", width=160)
        self.tree.column("datetime", width=160)
        self.tree.column("status", width=80, anchor="center")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

        # Context menu for reschedule/cancel (optional)
        self.tree.bind("<Button-3>", self._on_right_click)  # right-click for context menu

        # Populate initially
        self.view()

    def clear_fields(self):
        """Clear all entry fields."""
        self.patient_entry.delete(0, tk.END)
        self.doctor_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END)
        self.time_entry.delete(0, tk.END)

    def book(self):
        """Read fields and call scheduler.book_appointment. Show success/error messages."""
        p = self.patient_entry.get()
        d = self.doctor_entry.get()
        date = self.date_entry.get()
        t = self.time_entry.get()
        try:
            appt_id = self.scheduler.book_appointment(p, d, date, t)
            messagebox.showinfo("Success", f"Appointment booked (ID {appt_id}).")
            self.view()  # refresh view
            self.clear_fields()
        except SchedulingError as e:
            messagebox.showerror("Scheduling Error", str(e))
        except Exception as e:
            # unexpected error: show message but keep program running
            messagebox.showerror("Error", f"Unexpected error: {e}")

    def view(self):
        """Fetch appointments from scheduler and display them in the treeview."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        appointments = self.scheduler.get_appointments(limit=200)
        for appt in appointments:
            dt_txt = appt.appointment_datetime.strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", tk.END, values=(appt.id, appt.patient_name, appt.doctor_name, dt_txt, appt.status))

    def _on_right_click(self, event):
        """Show a simple context menu on right-click with options to reschedule or cancel."""
        item = self.tree.identify_row(event.y)
        if not item:
            return
        values = self.tree.item(item, "values")
        appt_id = int(values[0])

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cancel Appointment", command=lambda aid=appt_id: self._cancel_confirm(aid))
        menu.add_command(label="Reschedule...", command=lambda aid=appt_id: self._reschedule_prompt(aid))
        menu.post(event.x_root, event.y_root)

    def _cancel_confirm(self, appointment_id: int):
        """Ask user to confirm cancellation, then call scheduler.cancel."""
        if messagebox.askyesno("Confirm Cancel", "Are you sure you want to cancel this appointment?"):
            try:
                self.scheduler.cancel(appointment_id)
                messagebox.showinfo("Cancelled", "Appointment cancelled.")
                self.view()
            except Exception as e:
                messagebox.showerror("Error", f"Could not cancel appointment: {e}")

    def _reschedule_prompt(self, appointment_id: int):
        """Prompt for new date/time and attempt to reschedule."""
        # Simple pop-up dialog using a Toplevel window
        dlg = tk.Toplevel(self.root)
        dlg.title("Reschedule Appointment")
        tk.Label(dlg, text="New Date (YYYY-MM-DD)").grid(row=0, column=0, padx=6, pady=6)
        tk.Label(dlg, text="New Time (HH:MM)").grid(row=1, column=0, padx=6, pady=6)
        date_e = tk.Entry(dlg)
        time_e = tk.Entry(dlg)
        date_e.grid(row=0, column=1, padx=6, pady=6)
        time_e.grid(row=1, column=1, padx=6, pady=6)
        def do_reschedule():
            new_date = date_e.get()
            new_time = time_e.get()
            try:
                self.scheduler.reschedule(appointment_id, new_date, new_time)
                messagebox.showinfo("Rescheduled", "Appointment rescheduled successfully.")
                dlg.destroy()
                self.view()
            except SchedulingError as se:
                messagebox.showerror("Reschedule Error", str(se))
            except Exception as e:
                messagebox.showerror("Error", f"Unexpected error: {e}")

        tk.Button(dlg, text="Reschedule", command=do_reschedule).grid(row=2, column=0, columnspan=2, pady=8)
