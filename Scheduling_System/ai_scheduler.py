from datetime import datetime, timedelta

class SmartAIScheduler:
    def suggest_time(self, doctor_name, date, db, requested_time):
        doctor_id = db.get_or_create_doctor(doctor_name)

        base_time = datetime.strptime(f"{date} {requested_time}", "%Y-%m-%d %H:%M")

        # Search range: up to 8 slots (4 hours in both directions)
        for i in range(1, 9):
            # Check forward
            forward = base_time + timedelta(minutes=30 * i)
            if 9 <= forward.hour < 17:
                if not db.check_conflict(doctor_id, forward):
                    return forward.strftime("%H:%M")

            # Check backward
            backward = base_time - timedelta(minutes=30 * i)
            if 9 <= backward.hour < 17:
                if not db.check_conflict(doctor_id, backward):
                    return backward.strftime("%H:%M")

        return "No available slots"
