import sqlite3
import tkinter as tk
from tkinter import messagebox

from config import BG_DARK, BG_MAIN, BG_CARD, WHITE, ORANGE, GRAY_TXT, DARK_TXT, LIGHT_BDR, RED_CLR, MUTED, BG_SOFT
from database import db_connect
from security import hash_pw, verify_pw
from ui.scroll import make_scroll_area
from ui.widgets import nice_button, nice_entry, secondary_button, card_frame, page_header
from validators import check_email, check_name, check_password, check_phone


class LoginPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.build_ui()

    def build_ui(self):
        shell = tk.Frame(self, bg=BG_MAIN)
        shell.pack(fill="both", expand=True, padx=38, pady=34)

        left_side = tk.Frame(shell, bg=BG_DARK, width=420, padx=34, pady=34)
        left_side.pack(side="left", fill="both")
        left_side.pack_propagate(False)

        tk.Label(left_side, text="ErrandMate", font=("Segoe UI", 36, "bold"), fg=WHITE, bg=BG_DARK).pack(anchor="w", pady=(70, 6))
        tk.Label(left_side, text="A modern way to post errands, accept local work, and track completion.", font=("Segoe UI", 13), fg="#CBD5E1", bg=BG_DARK, wraplength=310, justify="left").pack(anchor="w", pady=(0, 28))
        tk.Frame(left_side, bg=ORANGE, height=4, width=110).pack(anchor="w", pady=(0, 28))

        for icon, title, desc in [
            ("✓", "Post tasks quickly", "Create clear jobs with price, category and deadline."),
            ("↗", "Accept useful work", "Browse open errands and manage your progress."),
            ("★", "Build trust", "Complete jobs and collect runner ratings."),
        ]:
            row = tk.Frame(left_side, bg=BG_DARK)
            row.pack(fill="x", pady=9)
            tk.Label(row, text=icon, font=("Segoe UI", 13, "bold"), fg=WHITE, bg=ORANGE, width=3, pady=4).pack(side="left", padx=(0, 12))
            copy = tk.Frame(row, bg=BG_DARK)
            copy.pack(side="left", fill="x", expand=True)
            tk.Label(copy, text=title, font=("Segoe UI", 11, "bold"), fg=WHITE, bg=BG_DARK).pack(anchor="w")
            tk.Label(copy, text=desc, font=("Segoe UI", 9), fg="#94A3B8", bg=BG_DARK, wraplength=260, justify="left").pack(anchor="w")

        tk.Label(left_side, text="Group Project 2025/26", font=("Segoe UI", 9), fg="#94A3B8", bg=BG_DARK).pack(side="bottom", anchor="w")

        right_side = tk.Frame(shell, bg=WHITE)
        right_side.pack(side="right", fill="both", expand=True)

        form = card_frame(right_side, padx=42, pady=38)
        form.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(form, text="Welcome back", font=("Segoe UI", 28, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w")
        tk.Label(form, text="Sign in to continue to your workspace.", font=("Segoe UI", 11), fg=GRAY_TXT, bg=WHITE).pack(anchor="w", pady=(4, 26))

        self._field_label(form, "Email Address")
        self.email_field = nice_entry(form, w=38)
        self.email_field.pack(fill="x", pady=(5, 16), ipady=10)

        self._field_label(form, "Password")
        self.pass_field = nice_entry(form, w=38, hidden=True)
        self.pass_field.pack(fill="x", pady=(5, 24), ipady=10)

        nice_button(form, "Login", self.try_login, color=ORANGE, w=32).pack(fill="x")

        divider = tk.Frame(form, bg=LIGHT_BDR, height=1)
        divider.pack(fill="x", pady=22)

        bottom = tk.Frame(form, bg=WHITE)
        bottom.pack()
        tk.Label(bottom, text="New here?", font=("Segoe UI", 10), fg=GRAY_TXT, bg=WHITE).pack(side="left")
        tk.Button(bottom, text="Create an account", font=("Segoe UI", 10, "bold"), fg=ORANGE, bg=WHITE, relief="flat", cursor="hand2", activebackground=WHITE, command=lambda: self.app.go_to("RegisterPage")).pack(side="left")

        self.email_field.bind("<Return>", lambda e: self.try_login())
        self.pass_field.bind("<Return>", lambda e: self.try_login())

    def _field_label(self, parent, text):
        tk.Label(parent, text=text, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, anchor="w").pack(fill="x")

    def try_login(self):
        email = self.email_field.get().strip().lower()
        password = self.pass_field.get()
        if not email or not password:
            messagebox.showerror("Oops!", "Please fill in both fields")
            return
        valid, msg = check_email(email)
        if not valid:
            messagebox.showerror("Invalid Email", msg)
            return
        conn = db_connect()
        user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and verify_pw(password, user["password"]):
            if not user["password"].startswith("pbkdf2_sha256$"):
                new_hash = hash_pw(password)
                conn.execute("UPDATE users SET password=? WHERE id=?", (new_hash, user["id"]))
                conn.commit()
                user = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
            conn.close()
            self.pass_field.delete(0, tk.END)
            self.app.do_login(user)
        else:
            conn.close()
            messagebox.showerror("Login Failed", "Wrong email or password.\nPlease try again.")


class RegisterPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.build_ui()

    def build_ui(self):
        header = tk.Frame(self, bg=BG_DARK, pady=16, padx=24)
        header.pack(fill="x")
        tk.Label(header, text="ErrandMate", font=("Segoe UI", 18, "bold"), fg=WHITE, bg=BG_DARK).pack(side="left")
        tk.Label(header, text="Create New Account", font=("Segoe UI", 14, "bold"), fg="#CBD5E1", bg=BG_DARK).pack(side="left", padx=22)
        tk.Button(header, text="Back to Login", font=("Segoe UI", 10, "bold"), fg=WHITE, bg=BG_CARD, relief="flat", padx=14, pady=7, cursor="hand2", command=lambda: self.app.go_to("LoginPage")).pack(side="right")

        outer, inner = make_scroll_area(self)
        outer.pack(fill="both", expand=True, padx=56, pady=24)
        page_header(inner, "Account setup", "Join ErrandMate", "Create a profile so you can post errands, accept jobs, or do both.")

        card = card_frame(inner, padx=38, pady=30)
        card.pack(fill="x")

        cols = tk.Frame(card, bg=WHITE)
        cols.pack(fill="x")
        left_col = tk.Frame(cols, bg=WHITE)
        left_col.pack(side="left", fill="both", expand=True, padx=(0, 24))
        right_col = tk.Frame(cols, bg=WHITE)
        right_col.pack(side="right", fill="both", expand=True)

        def field(parent, label_txt, is_password=False):
            tk.Label(parent, text=label_txt, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, anchor="w").pack(fill="x", pady=(10, 4))
            e = nice_entry(parent, w=28, hidden=is_password)
            e.pack(fill="x", ipady=9)
            return e

        self.name_e = field(left_col, "Full Name  *")
        self.email_e = field(left_col, "Email Address  *")
        self.phone_e = field(left_col, "Phone Number  *")
        self.pass_e = field(right_col, "Password  *", is_password=True)
        self.pass2_e = field(right_col, "Confirm Password  *", is_password=True)

        tk.Label(right_col, text="Minimum 8 characters, one uppercase letter and one number.", font=("Segoe UI", 9), fg=GRAY_TXT, bg=WHITE, anchor="w").pack(fill="x", pady=(6, 0))
        tk.Label(right_col, text="I want to...", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, anchor="w").pack(fill="x", pady=(18, 8))

        self.role_choice = tk.StringVar(value="both")
        role_frame = tk.Frame(right_col, bg=WHITE)
        role_frame.pack(anchor="w")
        for val, label in [("poster", "Post Tasks"), ("runner", "Run Tasks"), ("both", "Both")]:
            tk.Radiobutton(role_frame, text=label, variable=self.role_choice, value=val, font=("Segoe UI", 10), fg=DARK_TXT, bg=WHITE, activebackground=WHITE, selectcolor=BG_SOFT).pack(side="left", padx=(0, 14))

        self.agree_var = tk.BooleanVar()
        tk.Checkbutton(card, text="I agree to the ErrandMate terms and conditions", variable=self.agree_var, font=("Segoe UI", 10), fg=DARK_TXT, bg=WHITE, activebackground=WHITE, selectcolor=BG_SOFT).pack(anchor="w", pady=(20, 4))

        self.err_label = tk.Label(card, text="", font=("Segoe UI", 10), fg=RED_CLR, bg=WHITE, anchor="w")
        self.err_label.pack(fill="x")

        btn_row = tk.Frame(card, bg=WHITE)
        btn_row.pack(pady=(18, 2))
        nice_button(btn_row, "Create Account", self.do_register, w=22).pack(side="left", padx=8)
        secondary_button(btn_row, "Clear", self.clear_form, w=10).pack(side="left", padx=8)

    def show_error(self, msg):
        self.err_label.config(text="Warning:  " + msg)

    def clear_form(self):
        for f in [self.name_e, self.email_e, self.phone_e, self.pass_e, self.pass2_e]:
            f.delete(0, tk.END)
        self.err_label.config(text="")

    def do_register(self):
        name = self.name_e.get().strip()
        email = self.email_e.get().strip().lower()
        phone = self.phone_e.get().strip()
        pw = self.pass_e.get()
        pw2 = self.pass2_e.get()
        role = self.role_choice.get()

        ok, msg = check_name(name)
        if not ok:
            self.show_error(msg); return
        ok, msg = check_email(email)
        if not ok:
            self.show_error(msg); return
        ok, msg = check_phone(phone)
        if not ok:
            self.show_error(msg); return
        ok, msg = check_password(pw)
        if not ok:
            self.show_error(msg); return
        if pw != pw2:
            self.show_error("Passwords do not match"); return
        if not self.agree_var.get():
            self.show_error("Please agree to the terms and conditions"); return

        conn = db_connect()
        try:
            conn.execute("INSERT INTO users (full_name, email, phone, password, role) VALUES (?,?,?,?,?)", (name, email, phone, hash_pw(pw), role))
            conn.commit()
            messagebox.showinfo("Account Created!", f"Welcome to ErrandMate, {name.split()[0]}!\nYou can now log in.")
            self.clear_form()
            self.app.go_to("LoginPage")
        except sqlite3.IntegrityError:
            self.show_error("This email is already registered. Please use a different one.")
        finally:
            conn.close()
