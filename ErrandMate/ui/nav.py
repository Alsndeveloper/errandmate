import tkinter as tk

from config import BG_DARK, BG_CARD, ORANGE, GRAY_TXT, WHITE, FONT_BODY_BOLD, FONT_BODY


class TopNavBar(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_DARK, height=68)
        self.app = app
        self.pack(fill="x")
        self.pack_propagate(False)
        self.build()

    def build(self):
        brand = tk.Frame(self, bg=BG_DARK)
        brand.pack(side="left", padx=(22, 24))
        tk.Label(brand, text="ErrandMate", font=("Segoe UI", 19, "bold"), fg=WHITE, bg=BG_DARK).pack(anchor="w")
        tk.Label(brand, text="Tasks made simple", font=("Segoe UI", 8), fg=GRAY_TXT, bg=BG_DARK).pack(anchor="w")

        nav_pages = [
            ("Home", "DashboardPage"),
            ("Browse", "BrowseTasksPage"),
            ("My Tasks", "MyTasksPage"),
            ("Post Task", "PostTaskPage"),
            ("Profile", "ProfilePage"),
        ]

        for label, page in nav_pages:
            btn = tk.Button(
                self,
                text=label,
                font=FONT_BODY_BOLD,
                fg="#CBD5E1",
                bg=BG_DARK,
                relief="flat",
                cursor="hand2",
                padx=13,
                pady=10,
                activebackground=BG_CARD,
                activeforeground=WHITE,
                command=lambda p=page: self.app.go_to(p),
            )
            btn.pack(side="left", padx=2)

        tk.Button(
            self,
            text="Logout",
            font=FONT_BODY_BOLD,
            fg=WHITE,
            bg=ORANGE,
            relief="flat",
            cursor="hand2",
            padx=16,
            pady=8,
            activebackground=BG_CARD,
            activeforeground=WHITE,
            command=self.app.do_logout,
        ).pack(side="right", padx=18)

        self.user_name_lbl = tk.Label(self, text="", font=FONT_BODY, fg="#CBD5E1", bg=BG_DARK)
        self.user_name_lbl.pack(side="right", padx=10)

    def set_username(self, name):
        self.user_name_lbl.config(text=f"Hi, {name}")
