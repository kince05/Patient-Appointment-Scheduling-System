from database import DatabaseManager, DatabaseError

class AuthError(Exception):
    pass

class AuthService:
    def __init__(self, db: DatabaseManager):
        self.db = db

    def register(self, username, password, role="patient"):
        try:
            return self.db.create_user(username, password, role)
        except DatabaseError as e:
            raise AuthError(str(e))

    def login(self, username, password):
        user = self.db.authenticate_user(username, password)
        if not user:
            raise AuthError("Invalid username or password.")
        return user
