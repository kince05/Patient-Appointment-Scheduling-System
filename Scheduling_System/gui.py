import tkinter as tk
from tkinter import messagebox, ttk
import threading
from scheduler import SchedulingError
from tkcalendar import DateEntry

class AppointmentGUI:
    def __init__(self, root, scheduler, user):
        self.root = root
        self.scheduler = scheduler
        self.user = user

        self.root.title(f"Patient Appointment System - {user['username']}")
        self.root.geometry("750x500")

        # Input Fields
        frame = tk.Frame(root, padx=10, pady=10)
        frame.pack(fill=tk.X)

        tk.Label(frame, text="Patient Name").grid(row=0, column=0, sticky="w")
        tk.Label(frame, text="Doctor Name").grid(row=1, column=0, sticky="w")
        tk.Label(frame, text="Date (YYYY-MM-DD)").grid(row=0, column=2, sticky="w", padx=(20,0))
        tk.Label(frame, text="Time (HH:MM)").grid(row=1, column=2, sticky="w", padx=(20,0))

        self.patient_entry = tk.Entry(frame, width=25)
        self.doctor_combo = ttk.Combobox(frame, width=23, state="readonly")
        self.doctor_combo.grid(row=1, column=1, pady=2)
        self.date_entry = DateEntry(
            frame,
            width=15,
            background="darkblue",
            foreground="white",
            date_pattern="yyyy-mm-dd"
        )

        self.time_combo = ttk.Combobox(frame, values=[
            "09:00","09:30","10:00","10:30","11:00",
            "11:30","12:00","12:30","13:00","13:30",
            "14:00","14:30","15:00","15:30","16:00","16:30"
        ], width=10, state="readonly")
        

        self.patient_entry.grid(row=0, column=1, pady=2)
        self.doctor_combo.grid(row=1, column=1, pady=2)
        self.date_entry.grid(row=0, column=3, pady=2)
        self.time_combo.grid(row=1, column=3, pady=2)

        self.load_doctors()

        # --- Buttons ---
        btn_frame = tk.Frame(root, pady=8)
        btn_frame.pack(fill=tk.X)

        tk.Button(btn_frame, text="Book Appointment", command=self.book).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Refresh", command=self.view).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Clear Fields", command=self.clear_fields).pack(side=tk.LEFT, padx=5)

        # --- Table ---
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

        # Right-click menu
        self.tree.bind("<Button-3>", self._on_right_click)

        self.view()

    # UI Helpers
  
    def clear_fields(self):
        self.patient_entry.delete(0, tk.END)
        self.doctor_combo.set("")
        self.date_entry.delete(0, tk.END)
        self.time_combo.set("")


    def load_doctors(self):
        doctors = self.scheduler.get_doctors()
        self.doctor_combo['values'] = doctors

  
    # THREADING 

    def book(self):
        threading.Thread(target=self._book_thread).start()

    def _book_thread(self):
        p = self.patient_entry.get()
        d = self.doctor_combo.get()
        date = self.date_entry.get_date().strftime("%Y-%m-%d")
        t = self.time_combo.get()

        if not p.strip() or not d.strip() or not t.strip():
            self.root.after(0, lambda: messagebox.showerror(
                "Input Error",
                "Please fill in Patient, Doctor, and Time fields."
            ))
            return

        try:
            appt_id = self.scheduler.book_appointment(p, d, date, t)
            self.root.after(0, lambda: messagebox.showinfo("Success", f"Appointment booked (ID {appt_id})"))
            self.root.after(0, self.view)
            self.root.after(0, self.clear_fields)

        except SchedulingError as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Scheduling Error", str(err)))

        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

    # ----------------------------
    # VIEW TABLE
    # ----------------------------
    def view(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        appointments = self.scheduler.get_appointments(limit=200)

        for appt in appointments:
            dt_txt = appt.appointment_datetime.strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", tk.END, values=(
                appt.id,
                appt.patient_name,
                appt.doctor_name,
                dt_txt,
                appt.status
            ))

    # ----------------------------
    # RIGHT CLICK MENU
    # ----------------------------
    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return

        values = self.tree.item(item, "values")
        appt_id = int(values[0])

        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Cancel", command=lambda: self._cancel(appt_id))
        menu.add_command(label="Reschedule", command=lambda: self._reschedule_popup(appt_id))
        menu.post(event.x_root, event.y_root)

    def _cancel(self, appt_id):
        try:
            self.scheduler.cancel(appt_id)
            messagebox.showinfo("Cancelled", "Appointment cancelled")
            self.view()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reschedule_popup(self, appt_id):
        dlg = tk.Toplevel(self.root)
        dlg.title("Reschedule")

        tk.Label(dlg, text="New Date (YYYY-MM-DD)").grid(row=0, column=0)
        tk.Label(dlg, text="New Time (HH:MM)").grid(row=1, column=0)

        date_e = tk.Entry(dlg)
        time_e = tk.Entry(dlg)

        date_e.grid(row=0, column=1)
        time_e.grid(row=1, column=1)

        def submit():
            try:
                self.scheduler.reschedule(appt_id, date_e.get(), time_e.get())
                messagebox.showinfo("Success", "Rescheduled")
                dlg.destroy()
                self.view()
            except SchedulingError as e:
                messagebox.showerror("Error", str(e))

        tk.Button(dlg, text="Confirm", command=submit).grid(row=2, column=0, columnspan=2)
