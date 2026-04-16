# auth.py
from database import DatabaseManager, DatabaseError


class AuthError(Exception):
    pass


class AuthService:
    ALLOWED_ROLES = {"admin", "doctor", "patient"}

    def __init__(self, db: DatabaseManager):
        self.db = db

    def register(self, username: str, password: str, role: str = "patient") -> int:
        username = (username or "").strip()
        password = password or ""
        role = (role or "patient").strip().lower()

        if len(username) < 3:
            raise AuthError("Username must be at least 3 characters long.")

        if len(password) < 6:
            raise AuthError("Password must be at least 6 characters long.")

        if role not in self.ALLOWED_ROLES:
            raise AuthError("Invalid role selected.")

        try:
            return self.db.create_user(username, password, role)
        except DatabaseError as e:
            raise AuthError(str(e)) from e

    def login(self, username: str, password: str):
        username = (username or "").strip()
        password = password or ""

        if not username or not password:
            raise AuthError("Username and password are required.")

        user = self.db.authenticate_user(username, password)
        if not user:
            raise AuthError("Invalid username or password.")

        return user
