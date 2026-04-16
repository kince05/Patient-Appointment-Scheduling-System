import customtkinter as ctk
from tkinter import messagebox, ttk
import threading
from scheduler import SchedulingError
from tkcalendar import DateEntry

ctk.set_appearance_mode("light")   # or "dark"
ctk.set_default_color_theme("blue")


class AppointmentGUI:
    def __init__(self, root, scheduler, user):
        self.root = root
        self.scheduler = scheduler
        self.user = user

        self.root.title(f"Patient Appointment System - {user['username']}")
        self.root.geometry("900x600")

       
        self.header = ctk.CTkLabel(
            root,
            text="Patient Appointment Scheduling System",
            font=("Segoe UI", 20, "bold")
        )
        self.header.pack(pady=10)

     
        self.main_frame = ctk.CTkFrame(root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)

      
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", padx=10, pady=10)

        # Patient
        ctk.CTkLabel(self.input_frame, text="Patient Name").grid(row=0, column=0, padx=10, pady=5)
        self.patient_entry = ctk.CTkEntry(self.input_frame, width=200)
        self.patient_entry.grid(row=0, column=1, padx=10, pady=5)

        # Doctor dropdown
        ctk.CTkLabel(self.input_frame, text="Doctor").grid(row=1, column=0, padx=10, pady=5)
        self.doctor_combo = ctk.CTkComboBox(self.input_frame, values=[], width=200)
        self.doctor_combo.set("")
        self.doctor_combo.grid(row=1, column=1, padx=10, pady=5)

        # Date (simple entry for now)
        ctk.CTkLabel(self.input_frame, text="Date (YYYY-MM-DD)").grid(row=0, column=2, padx=10, pady=5)
        self.date_entry = DateEntry(
            self.input_frame,
            width=15,
            date_pattern="yyyy-mm-dd"
        )
        self.date_entry.grid(row=0, column=3, padx=10, pady=5)

        # Time dropdown
        ctk.CTkLabel(self.input_frame, text="Time").grid(row=1, column=2, padx=10, pady=5)
        self.time_combo = ctk.CTkComboBox(
            self.input_frame,
            values=[
                "09:00","09:30","10:00","10:30","11:00",
                "11:30","12:00","12:30","13:00","13:30",
                "14:00","14:30","15:00","15:30","16:00","16:30"
            ],
            width=150
        )
        self.time_combo.grid(row=1, column=3, padx=10, pady=5)

        # Load doctors
        self.load_doctors()

        # BUTTONS
        self.button_frame = ctk.CTkFrame(self.main_frame)
        self.button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(self.button_frame, text="Book Appointment", command=self.book).pack(side="left", padx=10)
        ctk.CTkButton(self.button_frame, text="Refresh", command=self.view).pack(side="left", padx=10)
        ctk.CTkButton(self.button_frame, text="Clear", command=self.clear_fields).pack(side="left", padx=10)

        # TABLE
        self.tree = ttk.Treeview(
            self.main_frame,
            columns=("id", "patient", "doctor", "datetime", "status"),
            show="headings",
            height=12
        )

        self.tree.heading("id", text="ID")
        self.tree.heading("patient", text="Patient")
        self.tree.heading("doctor", text="Doctor")
        self.tree.heading("datetime", text="Date & Time")
        self.tree.heading("status", text="Status")

        self.tree.column("id", width=50, anchor="center")
        self.tree.column("patient", width=180)
        self.tree.column("doctor", width=160)
        self.tree.column("datetime", width=160)
        self.tree.column("status", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        # Right-click menu
        self.tree.bind("<Button-3>", self._on_right_click)

        self.view()

    # HELPERS 
    def clear_fields(self):
        self.patient_entry.delete(0, "end")
        self.doctor_combo.set("")
        self.date_entry.delete(0, "end")
        self.time_combo.set("")

    def load_doctors(self):
        doctors = self.scheduler.get_doctors()
        self.doctor_combo.configure(values=doctors)
        self.doctor_combo.set("Select Doctor")

    # THREADING
    def book(self):
        threading.Thread(target=self._book_thread).start()

    def _book_thread(self):
        p = self.patient_entry.get()
        d = self.doctor_combo.get()
        date = self.date_entry.get()
        t = self.time_combo.get()

        if not p.strip() or d == "Select Doctor" or not date.strip() or not t.strip():
            self.root.after(0, lambda: messagebox.showerror(
                "Input Error", "Please fill all fields."
            ))
            return

        try:
            appt_id = self.scheduler.book_appointment(p, d, date, t)
            self.root.after(0, lambda: messagebox.showinfo(
                "Success", f"Appointment booked (ID {appt_id})"
            ))
            self.root.after(0, self.view)
            self.root.after(0, self.clear_fields)

        except SchedulingError as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

        except Exception as e:
            self.root.after(0, lambda err=e: messagebox.showerror("Error", str(err)))

 
    def view(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        appointments = self.scheduler.get_appointments(limit=200)

        for appt in appointments:
            dt_txt = appt.appointment_datetime.strftime("%Y-%m-%d %H:%M")
            self.tree.insert("", "end", values=(
                appt.id,
                appt.patient_name,
                appt.doctor_name,
                dt_txt,
                appt.status
            ))

    
    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            return

        values = self.tree.item(item, "values")
        appt_id = int(values[0])

        menu = ctk.CTkToplevel(self.root)
        menu.geometry("200x100")

        ctk.CTkButton(menu, text="Cancel", command=lambda: self._cancel(appt_id)).pack(pady=5)
        ctk.CTkButton(menu, text="Reschedule", command=lambda: self._reschedule_popup(appt_id)).pack(pady=5)

    def _cancel(self, appt_id):
        try:
            self.scheduler.cancel(appt_id)
            messagebox.showinfo("Cancelled", "Appointment cancelled")
            self.view()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _reschedule_popup(self, appt_id):
        dlg = ctk.CTkToplevel(self.root)
        dlg.title("Reschedule")

        ctk.CTkLabel(dlg, text="New Date").pack(pady=5)
        date_e = ctk.CTkEntry(dlg)
        date_e.pack(pady=5)

        ctk.CTkLabel(dlg, text="New Time").pack(pady=5)
        time_e = ctk.CTkEntry(dlg)
        time_e.pack(pady=5)

        def submit():
            try:
                self.scheduler.reschedule(appt_id, date_e.get(), time_e.get())
                messagebox.showinfo("Success", "Rescheduled")
                dlg.destroy()
                self.view()
            except SchedulingError as e:
                messagebox.showerror("Error", str(e))

        ctk.CTkButton(dlg, text="Confirm", command=submit).pack(pady=10)
