class Person:
    def __init__(self, name):
        self._name = name  

    def get_name(self):
        return self._name

    def get_role(self):
        return "Person"


class Patient(Person):
    def get_role(self):
        return "Patient"


class Doctor(Person):
    def get_role(self):
        return "Doctor"
