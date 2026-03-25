import tkinter as tk
from tkinter import messagebox
from auth import AuthService, AuthError

class LoginGUI:
    def __init__(self, root, auth_service, on_success):
        self.root = root
        self.auth = auth_service
        self.on_success = on_success

        root.title("Login")
        root.geometry("300x200")

        tk.Label(root, text="Username").pack()
        self.user = tk.Entry(root)
        self.user.pack()

        tk.Label(root, text="Password").pack()
        self.pw = tk.Entry(root, show="*")
        self.pw.pack()

        tk.Button(root, text="Login", command=self.login).pack(pady=5)
        tk.Button(root, text="Register", command=self.register).pack()

    def login(self):
        try:
            user = self.auth.login(self.user.get(), self.pw.get())
            messagebox.showinfo("Success", f"Welcome {user['username']}")
            self.on_success(user)
        except AuthError as e:
            messagebox.showerror("Error", str(e))

    def register(self):
        try:
            self.auth.register(self.user.get(), self.pw.get())
            messagebox.showinfo("Success", "Account created!")
        except AuthError as e:
            messagebox.showerror("Error", str(e))
