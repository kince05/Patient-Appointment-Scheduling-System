# Patient Appointment Scheduling System

## Project Overview
A desktop application for booking, viewing, rescheduling, and cancelling patient appointments with doctors.  
The system enforces business rules such as 30-minute time slots, working hours (9:00–17:00), and prevents double-booking the same doctor at the same time.

This is the **Phase 3** version, which includes:
- User authentication (login + registration with role support)
- Object-Oriented Design following SOLID principles
- Layered architecture (GUI → Business Logic → Database)
- Automation via shell scripts

## Features
- **Authentication**: Login and registration (default admin: `admin` / `admin123`)
- **Appointment Management**:
  - Book new appointments
  - View all upcoming appointments
  - Reschedule appointments (right-click in the list)
  - Cancel appointments
- **Business Rules**:
  - 30-minute slot enforcement
  - Working hours validation (9:00 AM – 5:00 PM)
  - Conflict detection (no overlapping appointments for the same doctor)
- **Technologies**:
  - Python 3 + Tkinter GUI
  - SQLite database
  - Object-Oriented Design (Inheritance, Dependency Injection, Separation of Concerns)

## How to Run the Application

1. Make sure you are inside the `Scheduling_System` folder (where `main.py` is located).
2. Run the program:

```bash
python main.py
