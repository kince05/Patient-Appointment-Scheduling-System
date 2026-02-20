from scheduler import SchedulingError
import tkinter as tk
from tkinter import messagebox

class AppointmentGUI:
    def __init__(self, root, scheduler):
        self.scheduler = scheduler
        self.root = root
        self.root.title("Patient Appointment Scheduling System")

        tk.Label(root, text="Patient Name").grid(row=0, column=0)
        tk.Label(root, text="Doctor Name").grid(row=1, column=0)
        tk.Label(root, text="Date (YYYY-MM-DD)").grid(row=2, column=0)
        tk.Label(root, text="Time (HH:MM)").grid(row=3, column=0)

        self.patient_entry = tk.Entry(root)
        self.doctor_entry = tk.Entry(root)
        self.date_entry = tk.Entry(root)
        self.time_entry = tk.Entry(root)

        self.patient_entry.grid(row=0, column=1)
        self.doctor_entry.grid(row=1, column=1)
        self.date_entry.grid(row=2, column=1)
        self.time_entry.grid(row=3, column=1)

        tk.Button(root, text="Book Appointment", command=self.book).grid(row=4, column=0)
        tk.Button(root, text="View Appointments", command=self.view).grid(row=4, column=1)

        self.output = tk.Text(root, height=10, width=60)
        self.output.grid(row=5, column=0, columnspan=2)

    def book(self):
        try:
            self.scheduler.book_appointment(
                self.patient_entry.get(),
                self.doctor_entry.get(),
                self.date_entry.get(),
                self.time_entry.get()
            )
            messagebox.showinfo("Success", "Appointment booked successfully!")
        

        except SchedulingError as e:
            messagebox.showerror("Scheduling Error", str(e))
            
        except Exception as e:
            messagebox.showerror("System Error", str(e))

    def view(self):
        self.output.delete(1.0, tk.END)
        appointments = self.scheduler.get_appointments()
        for appt in appointments:
