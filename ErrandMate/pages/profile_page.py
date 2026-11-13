import tkinter as tk
from tkinter import messagebox

from config import BG_DARK, BG_MAIN, WHITE, ORANGE, GRAY_TXT, DARK_TXT, LIGHT_BDR, RED_CLR
from database import db_connect
from security import hash_pw, verify_pw
from ui.nav import TopNavBar
from ui.scroll import make_scroll_area
from ui.widgets import nice_button, nice_entry, secondary_button, card_frame, page_header
from validators import check_name, check_password, check_phone


class ProfilePage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        TopNavBar(self, app)
        self.body = tk.Frame(self, bg=BG_MAIN)
        self.body.pack(fill="both", expand=True)

    def load(self):
        for w in self.body.winfo_children():
            w.destroy()

        user = self.app.logged_in_user
        if not user:
            return

        outer, inner = make_scroll_area(self.body)
        outer.pack(fill="both", expand=True, padx=60, pady=24)

        head_card = tk.Frame(inner, bg=BG_DARK, padx=34, pady=28)
        head_card.pack(fill="x", pady=(0, 18))

        tk.Label(head_card, text=user["full_name"][0].upper(), font=("Segoe UI", 38, "bold"), fg=WHITE, bg=ORANGE, width=2, height=1).pack(anchor="w", pady=(0, 12))
        tk.Label(head_card, text=user["full_name"], font=("Segoe UI", 22, "bold"), fg=WHITE, bg=BG_DARK).pack(anchor="w")
        tk.Label(head_card, text=user["email"], font=("Segoe UI", 11), fg="#CBD5E1", bg=BG_DARK).pack(anchor="w", pady=(4,0))
        tk.Label(head_card, text=user["phone"], font=("Segoe UI", 11), fg="#CBD5E1", bg=BG_DARK).pack(anchor="w", pady=(4, 0))

        conn = db_connect()
        posted_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id=?", (user["id"],)).fetchone()[0]
        done_count = conn.execute("SELECT COUNT(*) FROM tasks WHERE runner_id=? AND status='completed'", (user["id"],)).fetchone()[0]
        avg_rating = conn.execute("SELECT AVG(rating) FROM ratings WHERE runner_id=?", (user["id"],)).fetchone()[0]
        conn.close()

        rating_text = f"{avg_rating:.1f}/5" if avg_rating else "No ratings"

        stat_row = tk.Frame(inner, bg=BG_MAIN)
        stat_row.pack(pady=(0, 16))

        for val, lbl in [
            (str(posted_count), "Tasks Posted"),
            (str(done_count), "Tasks Completed"),
            (rating_text, "Runner Rating"),
            (user["joined_date"][:10], "Joined On"),
        ]:
            sf = card_frame(stat_row, padx=24, pady=16)
            sf.pack(side="left", padx=8)
            tk.Label(sf, text=val, font=("Segoe UI", 20, "bold"), fg=ORANGE, bg=WHITE).pack(anchor="w")
            tk.Label(sf, text=lbl, font=("Segoe UI", 9), fg=GRAY_TXT, bg=WHITE).pack(anchor="w")

        edit_card = card_frame(inner, padx=32, pady=26)
        edit_card.pack(fill="x", pady=(0, 14))

        tk.Label(edit_card, text="Edit Your Profile", font=("Segoe UI", 17, "bold"), fg=BG_DARK, bg=WHITE).pack(anchor="w", pady=(0, 16))

        def make_field_row(lbl):
            r = tk.Frame(edit_card, bg=WHITE)
            r.pack(fill="x", pady=5)
            tk.Label(r, text=lbl, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, width=20, anchor="w").pack(side="left")
            return r

        r_name = make_field_row("Full Name")
        self.edit_name = nice_entry(r_name, w=30)
        self.edit_name.insert(0, user["full_name"])
        self.edit_name.pack(side="left", fill="x", expand=True, ipady=6)

        r_phone = make_field_row("Phone Number")
        self.edit_phone = nice_entry(r_phone, w=30)
        self.edit_phone.insert(0, user["phone"] or "")
        self.edit_phone.pack(side="left", fill="x", expand=True, ipady=6)

        self.edit_role = tk.StringVar(value=user["role"])
        rr = tk.Frame(edit_card, bg=WHITE)
        rr.pack(fill="x", pady=5)
        tk.Label(rr, text="Role", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, width=20, anchor="w").pack(side="left")
        for val, lbl in [("poster", "Post Tasks"), ("runner", "Run Tasks"), ("both", "Both")]:
            tk.Radiobutton(
                rr,
                text=lbl,
                variable=self.edit_role,
                value=val,
                font=("Segoe UI", 10),
                fg=DARK_TXT,
                bg=WHITE,
                activebackground=WHITE,
                selectcolor="#F5F3FF",
            ).pack(side="left", padx=10)

        tk.Label(edit_card, text="Change Password  (leave blank to keep current)", font=("Segoe UI", 11, "bold"), fg=BG_DARK, bg=WHITE).pack(anchor="w", pady=(18, 8))

        r_oldpw = make_field_row("Current Password")
        self.old_pw_e = nice_entry(r_oldpw, w=30, hidden=True)
        self.old_pw_e.pack(side="left", fill="x", expand=True, ipady=6)

        r_newpw = make_field_row("New Password")
        self.new_pw_e = nice_entry(r_newpw, w=30, hidden=True)
        self.new_pw_e.pack(side="left", fill="x", expand=True, ipady=6)

        r_newpw2 = make_field_row("Confirm New Password")
        self.new_pw2_e = nice_entry(r_newpw2, w=30, hidden=True)
        self.new_pw2_e.pack(side="left", fill="x", expand=True, ipady=6)

        tk.Label(
            edit_card,
            text="New password needs: 8+ chars, 1 uppercase letter, 1 number",
            font=("Segoe UI", 8),
            fg=GRAY_TXT,
            bg=WHITE,
            anchor="w",
        ).pack(fill="x", pady=(2, 8))

        self.profile_err = tk.Label(edit_card, text="", font=("Segoe UI", 10), fg=RED_CLR, bg=WHITE, anchor="w")
        self.profile_err.pack(fill="x")

        btn_row = tk.Frame(edit_card, bg=WHITE)
        btn_row.pack(pady=14)
        nice_button(btn_row, "Save Changes", self.save_changes, w=18).pack(side="left", padx=8, ipady=4)
        nice_button(btn_row, "Logout", self.app.do_logout, color=RED_CLR, w=10).pack(side="left", padx=8)

    def save_changes(self):
        user = self.app.logged_in_user
        new_name = self.edit_name.get().strip()
        new_phone = self.edit_phone.get().strip()
        new_role = self.edit_role.get()
        old_pw = self.old_pw_e.get()
        new_pw = self.new_pw_e.get()
        new_pw2 = self.new_pw2_e.get()

        ok, msg = check_name(new_name)
        if not ok:
            self.profile_err.config(text="Warning:  " + msg)
            return

        if new_phone:
            ok, msg = check_phone(new_phone)
            if not ok:
                self.profile_err.config(text="Warning:  " + msg)
                return

        if old_pw or new_pw or new_pw2:
            conn = db_connect()
            db_user = conn.execute("SELECT password FROM users WHERE id=?", (user["id"],)).fetchone()
            conn.close()

            if not verify_pw(old_pw, db_user["password"]):
                self.profile_err.config(text="Warning:  Current password is wrong")
                return

            if new_pw != new_pw2:
                self.profile_err.config(text="Warning:  New passwords do not match")
                return

            ok, msg = check_password(new_pw)
            if not ok:
                self.profile_err.config(text="Warning:  " + msg)
                return

            conn = db_connect()
            conn.execute(
                "UPDATE users SET full_name=?, phone=?, role=?, password=? WHERE id=?",
                (new_name, new_phone, new_role, hash_pw(new_pw), user["id"]),
            )
            conn.commit()
            conn.close()
        else:
            conn = db_connect()
            conn.execute("UPDATE users SET full_name=?, phone=?, role=? WHERE id=?", (new_name, new_phone, new_role, user["id"]))
            conn.commit()
            conn.close()

        conn = db_connect()
        updated = conn.execute("SELECT * FROM users WHERE id=?", (user["id"],)).fetchone()
        conn.close()

        self.app.logged_in_user = dict(updated)
        self.profile_err.config(text="")
        messagebox.showinfo("Saved!", "Your profile has been updated successfully.")
        self.load()
