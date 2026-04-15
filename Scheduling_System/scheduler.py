def _validate(self, dt):
        if dt.minute not in (0, 30):
            raise SchedulingError("Must be 30-minute slots.")

        if not (9 <= dt.hour < 17):
            raise SchedulingError("Outside working hours.")

        if dt <= datetime.now():
            raise SchedulingError("Must be future time.")
        

    def book_appointment(self, p, d, date, time):
        with self.lock:

            
            if not p or not p.strip():
                raise SchedulingError("Patient name is required.")

            if not d or not d.strip():
                raise SchedulingError("Doctor must be selected.")

            if not date or not date.strip():
                raise SchedulingError("Date is required.")

            if not time or not time.strip():
                raise SchedulingError("Time is required.")

            dt = self._parse_datetime(date, time)
            self._validate(dt)

            pid = self.db.get_or_create_patient(p)
            did = self.db.get_or_create_doctor(d)

            if self.db.check_conflict(did, dt):
                if self.ai_model:
                    suggestion = self.ai_model.suggest_time(d, date, self.db, time)
                    raise SchedulingError(f"Busy. Try {suggestion}")
                raise SchedulingError("Doctor already booked.")

            return self.db.add_appointment(pid, did, dt)

    def get_appointments(self, limit=100):
        rows = self.db.get_appointments(limit)
        return [
            Appointment(
                id=r["id"],
                patient_name=r["patient_name"],
                doctor_name=r["doctor_name"],
                appointment_datetime=r["appointment_datetime"],
                status=r["status"],
                created_at=r["created_at"]
            )
            for r in rows
        ]

    def cancel(self, id):
        self.db.cancel_appointment(id)

    def reschedule(self, id, date, time):
        dt = self._parse_datetime(date, time)
        self._validate(dt)
        self.db.reschedule_appointment(id, dt)

    def get_doctors(self):
        return self.db.get_all_doctors()
