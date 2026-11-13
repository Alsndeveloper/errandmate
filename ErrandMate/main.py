import os
import sys
import tkinter as tk

# Ensure current package directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import BG_MAIN, WINDOW_TITLE, WINDOW_SIZE, WINDOW_MIN_SIZE
from database import setup_database
from pages.auth_pages import LoginPage, RegisterPage
from pages.profile_page import ProfilePage
from pages.task_pages import DashboardPage, PostTaskPage, BrowseTasksPage, MyTasksPage, TaskDetailsPage


class ErrandMateApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(WINDOW_TITLE)
        self.geometry(WINDOW_SIZE)
        self.configure(bg=BG_MAIN)
        self.resizable(True, True)
        self.minsize(*WINDOW_MIN_SIZE)

        setup_database()
        self.logged_in_user = None

        self.container = tk.Frame(self, bg=BG_MAIN)
        self.container.pack(fill="both", expand=True)
        self.container.grid_rowconfigure(0, weight=1)
        self.container.grid_columnconfigure(0, weight=1)

        self.pages = {}
        all_pages = [
            LoginPage,
            RegisterPage,
            DashboardPage,
            PostTaskPage,
            BrowseTasksPage,
            MyTasksPage,
            TaskDetailsPage,
            ProfilePage,
        ]

        for page_class in all_pages:
            page = page_class(self.container, self)
            self.pages[page_class.__name__] = page
            page.grid(row=0, column=0, sticky="nsew")

        self.go_to("LoginPage")

    def go_to(self, page_name):
        page = self.pages[page_name]
        if hasattr(page, "load"):
            page.load()
        page.tkraise()

    def open_task_details(self, task_id):
        page = self.pages["TaskDetailsPage"]
        page.set_task(task_id)
        self.go_to("TaskDetailsPage")

    def do_login(self, user):
        self.logged_in_user = dict(user)
        self.go_to("DashboardPage")

    def do_logout(self):
        self.logged_in_user = None
        self.go_to("LoginPage")


if __name__ == "__main__":
    app = ErrandMateApp()
    app.mainloop()
