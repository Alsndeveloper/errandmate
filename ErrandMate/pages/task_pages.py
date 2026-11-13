import datetime
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

from config import (
    BG_DARK,
    BG_MAIN,
    WHITE,
    ORANGE,
    GRAY_TXT,
    DARK_TXT,
    LIGHT_BDR,
    GREEN,
    RED_CLR,
    BLUE,
    PURPLE,
    YELLOW,
    task_categories,
    TASK_STATUS_LABELS,
    TASK_STATUS_COLORS,
)
from database import db_connect
from ui.cards import task_card, stat_card
from ui.nav import TopNavBar
from ui.scroll import make_scroll_area
from ui.widgets import nice_button, nice_entry, secondary_button, danger_button, section_title, info_banner, empty_state, card_frame, page_header


def now_iso():
    return datetime.datetime.now().isoformat(timespec="seconds")


def fetch_task(task_id):
    conn = db_connect()
    task = conn.execute(
        """
        SELECT t.*, u.full_name as poster_name, u.phone as poster_phone,
               r.full_name as runner_name, r.phone as runner_phone,
               AVG(rt.rating) as runner_rating
        FROM tasks t
        JOIN users u ON t.poster_id = u.id
        LEFT JOIN users r ON t.runner_id = r.id
        LEFT JOIN ratings rt ON rt.runner_id = r.id
        WHERE t.id = ?
        GROUP BY t.id
        """,
        (task_id,),
    ).fetchone()
    conn.close()
    return task


def accept_task_record(task_id, user_id):
    conn = db_connect()
    task = conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
    if not task:
        conn.close()
        return False, "Task not found."
    if task["poster_id"] == user_id:
        conn.close()
        return False, "You cannot accept your own task."
    if task["status"] != "open":
        conn.close()
        return False, "This task is no longer open."
    conn.execute(
        "UPDATE tasks SET runner_id=?, status='accepted', accepted_on=? WHERE id=?",
        (user_id, now_iso(), task_id),
    )
    conn.commit()
    conn.close()
    return True, "Task accepted. You can manage it from My Tasks."


class DashboardPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.navbar = TopNavBar(self, app)
        self.content = tk.Frame(self, bg=BG_MAIN)
        self.content.pack(fill="both", expand=True)

    def load(self):
        for w in self.content.winfo_children():
            w.destroy()
        user = self.app.logged_in_user
        if not user:
            return
        self.navbar.set_username(user["full_name"].split()[0])

        outer, inner = make_scroll_area(self.content)
        outer.pack(fill="both", expand=True, padx=28, pady=18)

        hour = datetime.datetime.now().hour
        greeting = "Good Morning" if hour < 12 else "Good Afternoon" if hour < 17 else "Good Evening"
        page_header(inner, "Dashboard", f"{greeting}, {user['full_name'].split()[0]}!", "Track your errands, active work, earnings and task progress from one clean workspace.")

        conn = db_connect()
        total_open = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='open'").fetchone()[0]
        i_posted = conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id=?", (user["id"],)).fetchone()[0]
        i_active = conn.execute("SELECT COUNT(*) FROM tasks WHERE runner_id=? AND status IN ('accepted','in_progress','awaiting_confirmation')", (user["id"],)).fetchone()[0]
        i_done = conn.execute("SELECT COUNT(*) FROM tasks WHERE (poster_id=? OR runner_id=?) AND status='completed'", (user["id"], user["id"])).fetchone()[0]
        awaiting = conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id=? AND status='awaiting_confirmation'", (user["id"],)).fetchone()[0]
        earnings = conn.execute("SELECT COALESCE(SUM(price),0) FROM tasks WHERE runner_id=? AND status='completed'", (user["id"],)).fetchone()[0]
        conn.close()

        if awaiting:
            info_banner(inner, f"Action needed: {awaiting} task(s) are waiting for your completion confirmation.")

        stats_row = tk.Frame(inner, bg=BG_MAIN)
        stats_row.pack(fill="x", pady=(0, 22))
        for label, count, color in [
            ("Open Tasks", str(total_open), ORANGE),
            ("I Posted", str(i_posted), BLUE),
            ("Active Work", str(i_active), YELLOW),
            ("Completed", str(i_done), GREEN),
            ("Runner Earnings", f"GBP {earnings:.2f}", PURPLE),
        ]:
            stat_card(stats_row, count, label, color)

        tk.Label(inner, text="Quick Actions", font=("Segoe UI", 16, "bold"), fg=DARK_TXT, bg=BG_MAIN).pack(anchor="w", pady=(4, 10))
        actions = tk.Frame(inner, bg=BG_MAIN)
        actions.pack(fill="x", pady=(0, 24))
        for lbl, pg, col in [("Post a Task", "PostTaskPage", ORANGE), ("Browse Tasks", "BrowseTasksPage", BG_DARK), ("My Tasks", "MyTasksPage", BLUE), ("Profile", "ProfilePage", PURPLE)]:
            nice_button(actions, lbl, lambda p=pg: self.app.go_to(p), color=col, w=16).pack(side="left", padx=6, ipady=4)

        tk.Label(inner, text="Latest Open Tasks", font=("Segoe UI", 16, "bold"), fg=DARK_TXT, bg=BG_MAIN).pack(anchor="w", pady=(4, 8))
        conn = db_connect()
        recent = conn.execute(
            """
            SELECT t.*, u.full_name as poster_name
            FROM tasks t JOIN users u ON t.poster_id = u.id
            WHERE t.status = 'open'
            ORDER BY t.posted_on DESC LIMIT 6
            """
        ).fetchall()
        conn.close()

        if not recent:
            self.empty_state(inner, "No open tasks yet.", "Be the first person to post a task for runners to accept.", "Post a Task", "PostTaskPage")
            return

        for t in recent:
            extras = [("View Details", lambda tid=t["id"]: self.app.open_task_details(tid), BG_DARK)]
            if t["poster_id"] != user["id"]:
                task_card(inner, t, btn_text="Accept", btn_cmd=lambda tid=t["id"]: self.accept_task(tid), btn_color=GREEN, extra_buttons=extras)
            else:
                task_card(inner, t, extra_buttons=extras)

    def empty_state(self, parent, title, msg, btn, page):
        empty_state(parent, title, msg, btn, lambda: self.app.go_to(page))

    def accept_task(self, task_id):
        ok, msg = accept_task_record(task_id, self.app.logged_in_user["id"])
        messagebox.showinfo("ErrandMate", msg) if ok else messagebox.showerror("ErrandMate", msg)
        self.load()


class PostTaskPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        TopNavBar(self, app)
        self.build_ui()

    def build_ui(self):
        outer, inner = make_scroll_area(self)
        outer.pack(fill="both", expand=True, padx=70, pady=22)
        page_header(inner, "Create", "Post a New Task", "Add the key details runners need before accepting the job.")
        card = card_frame(inner, padx=38, pady=30)
        card.pack(fill="x")

        def row(label):
            r = tk.Frame(card, bg=WHITE)
            r.pack(fill="x", pady=8)
            tk.Label(r, text=label, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, width=18, anchor="w").pack(side="left")
            return r

        self.title_e = nice_entry(row("Task Title  *"), w=38); self.title_e.pack(side="left", fill="x", expand=True, ipady=7)
        r2 = row("Category  *")
        self.cat_var = tk.StringVar(value=task_categories[0])
        ttk.Combobox(r2, textvariable=self.cat_var, values=task_categories, state="readonly", font=("Segoe UI", 11), width=30).pack(side="left", fill="x", expand=True, ipady=4)
        self.location_e = nice_entry(row("Location  *"), w=38); self.location_e.pack(side="left", fill="x", expand=True, ipady=7)
        self.price_e = nice_entry(row("Price (GBP)  *"), w=38); self.price_e.pack(side="left", fill="x", expand=True, ipady=7)
        self.deadline_e = nice_entry(row("Deadline"), w=38); self.deadline_e.pack(side="left", fill="x", expand=True, ipady=7)
        self.deadline_e.insert(0, "e.g. 25/12/2026 or ASAP"); self.deadline_e.config(fg=GRAY_TXT)
        self.deadline_e.bind("<FocusIn>", lambda e: (self.deadline_e.delete(0, tk.END), self.deadline_e.config(fg=DARK_TXT)) if self.deadline_e.get().startswith("e.g.") else None)
        self.deadline_e.bind("<FocusOut>", lambda e: (self.deadline_e.insert(0, "e.g. 25/12/2026 or ASAP"), self.deadline_e.config(fg=GRAY_TXT)) if not self.deadline_e.get().strip() else None)

        tk.Label(card, text="Description", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(12, 4))
        self.desc_box = tk.Text(card, font=("Segoe UI", 11), height=6, relief="solid", bd=1, bg=WHITE, fg=DARK_TXT, highlightthickness=2, highlightcolor=ORANGE, highlightbackground=LIGHT_BDR)
        self.desc_box.pack(fill="x", pady=(0, 14))
        self.post_err = tk.Label(card, text="", font=("Segoe UI", 10), fg=RED_CLR, bg=WHITE, anchor="w")
        self.post_err.pack(fill="x")
        btns = tk.Frame(card, bg=WHITE); btns.pack(pady=12)
        nice_button(btns, "Post Task", self.submit_task, w=18).pack(side="left", padx=8)
        secondary_button(btns, "Clear", self.clear_form, w=10).pack(side="left", padx=8)

    def submit_task(self):
        user = self.app.logged_in_user
        title = self.title_e.get().strip()
        category = self.cat_var.get()
        location = self.location_e.get().strip()
        price_str = self.price_e.get().strip()
        deadline = self.deadline_e.get().strip()
        desc = self.desc_box.get("1.0", tk.END).strip()
        if deadline.startswith("e.g.") or not deadline:
            deadline = None
        if len(title) < 5:
            self.post_err.config(text="Warning: task title must be at least 5 characters."); return
        if not location:
            self.post_err.config(text="Warning: please enter the location."); return
        try:
            price = float(price_str)
            if price <= 0: raise ValueError
        except ValueError:
            self.post_err.config(text="Warning: price must be a positive number like 5.50."); return
        conn = db_connect()
        conn.execute("INSERT INTO tasks (title, description, category, location, price, deadline, poster_id) VALUES (?,?,?,?,?,?,?)", (title, desc, category, location, price, deadline, user["id"]))
        conn.commit(); conn.close()
        messagebox.showinfo("Posted", f"Your task '{title}' is now live.")
        self.clear_form(); self.app.go_to("MyTasksPage")

    def load(self):
        if hasattr(self, "post_err"):
            self.post_err.config(text="")

    def clear_form(self):
        for e in [self.title_e, self.location_e, self.price_e]: e.delete(0, tk.END)
        self.deadline_e.delete(0, tk.END); self.deadline_e.insert(0, "e.g. 25/12/2026 or ASAP"); self.deadline_e.config(fg=GRAY_TXT)
        self.desc_box.delete("1.0", tk.END); self.post_err.config(text="")


class BrowseTasksPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        TopNavBar(self, app)
        self.build_filters()
        self.result_area = None

    def build_filters(self):
        fbar = tk.Frame(self, bg=WHITE, pady=14, padx=18, highlightbackground=LIGHT_BDR, highlightthickness=1)
        fbar.pack(fill="x")
        self.search_e = nice_entry(fbar, w=24); self.search_e.pack(side="left", padx=(0, 10), ipady=5)
        tk.Label(fbar, text="Category", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(side="left")
        self.cat_filter = ttk.Combobox(fbar, values=["All"] + task_categories, state="readonly", font=("Segoe UI", 10), width=18); self.cat_filter.set("All"); self.cat_filter.pack(side="left", padx=8, ipady=4)
        tk.Label(fbar, text="Sort", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(side="left")
        self.sort_choice = ttk.Combobox(fbar, state="readonly", values=["Newest", "Price Low to High", "Price High to Low"], font=("Segoe UI", 10), width=18); self.sort_choice.set("Newest"); self.sort_choice.pack(side="left", padx=8, ipady=4)
        nice_button(fbar, "Search", self.load, w=10, color=BG_DARK).pack(side="left", padx=8)
        secondary_button(fbar, "Reset", self.reset_filters, w=8).pack(side="left")
        self.search_e.bind("<Return>", lambda e: self.load())

    def reset_filters(self):
        self.search_e.delete(0, tk.END); self.cat_filter.set("All"); self.sort_choice.set("Newest"); self.load()

    def load(self):
        if self.result_area: self.result_area.destroy()
        self.result_area, inner = make_scroll_area(self)
        self.result_area.pack(fill="both", expand=True, padx=18, pady=12)
        user = self.app.logged_in_user
        keyword = self.search_e.get().strip().lower(); cat = self.cat_filter.get(); sort = self.sort_choice.get()
        order = "t.price ASC" if sort == "Price Low to High" else "t.price DESC" if sort == "Price High to Low" else "t.posted_on DESC"
        query = """SELECT t.*, u.full_name as poster_name FROM tasks t JOIN users u ON t.poster_id=u.id WHERE t.status='open'"""
        params = []
        if cat != "All": query += " AND t.category=?"; params.append(cat)
        if keyword:
            query += " AND (LOWER(t.title) LIKE ? OR LOWER(t.description) LIKE ? OR LOWER(t.location) LIKE ?)"
            params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        query += f" ORDER BY {order}"
        conn = db_connect(); tasks = conn.execute(query, params).fetchall(); conn.close()
        tk.Label(inner, text=f"{len(tasks)} open task(s) found", font=("Segoe UI", 11, "bold"), fg=GRAY_TXT, bg=BG_MAIN).pack(anchor="w", pady=(0, 10))
        if not tasks:
            self.empty_state(inner, "No matching tasks", "Try changing the search text, category, or sorting option."); return
        for t in tasks:
            extras = [("View Details", lambda tid=t["id"]: self.app.open_task_details(tid), BG_DARK)]
            if user and t["poster_id"] != user["id"]:
                task_card(inner, t, btn_text="Accept Task", btn_cmd=lambda tid=t["id"]: self.accept(tid), btn_color=GREEN, extra_buttons=extras)
            else:
                task_card(inner, t, extra_buttons=extras)

    def empty_state(self, parent, title, msg):
        empty_state(parent, title, msg)

    def accept(self, task_id):
        ok, msg = accept_task_record(task_id, self.app.logged_in_user["id"])
        messagebox.showinfo("ErrandMate", msg) if ok else messagebox.showerror("ErrandMate", msg)
        self.load()


class MyTasksPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        TopNavBar(self, app)
        self.build_tabs()

    def build_tabs(self):
        tab_bar = tk.Frame(self, bg=WHITE, pady=10, padx=12, highlightbackground=LIGHT_BDR, highlightthickness=1)
        tab_bar.pack(fill="x")
        self.active_tab = tk.StringVar(value="posted")
        self.tab_buttons = {}
        for label, val in [("Tasks I Posted", "posted"), ("Tasks I'm Running", "running"), ("Completed", "done"), ("Cancelled", "cancelled")]:
            rb = tk.Radiobutton(tab_bar, text=label, variable=self.active_tab, value=val, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE, activebackground=WHITE, selectcolor="#F5F3FF", indicatoron=False, padx=18, pady=8, relief="flat", cursor="hand2", command=self.load)
            rb.pack(side="left", padx=4); self.tab_buttons[val] = rb
        tk.Label(tab_bar, text="Search", fg=GRAY_TXT, bg=WHITE, font=("Segoe UI", 9)).pack(side="left", padx=(18, 4))
        self.my_search = nice_entry(tab_bar, w=20); self.my_search.pack(side="left", ipady=4)
        self.my_search.bind("<Return>", lambda e: self.load())
        nice_button(tab_bar, "Apply", self.load, color=BG_DARK, w=8).pack(side="left", padx=6)
        self.tab_content = tk.Frame(self, bg=BG_MAIN); self.tab_content.pack(fill="both", expand=True)

    def load(self):
        for w in self.tab_content.winfo_children(): w.destroy()
        user = self.app.logged_in_user
        if not user: return
        conn = db_connect()
        counts = {
            "posted": conn.execute("SELECT COUNT(*) FROM tasks WHERE poster_id=?", (user["id"],)).fetchone()[0],
            "running": conn.execute("SELECT COUNT(*) FROM tasks WHERE runner_id=? AND status IN ('accepted','in_progress','awaiting_confirmation')", (user["id"],)).fetchone()[0],
            "done": conn.execute("SELECT COUNT(*) FROM tasks WHERE (poster_id=? OR runner_id=?) AND status='completed'", (user["id"], user["id"])).fetchone()[0],
            "cancelled": conn.execute("SELECT COUNT(*) FROM tasks WHERE (poster_id=? OR runner_id=?) AND status='cancelled'", (user["id"], user["id"])).fetchone()[0],
        }
        conn.close()
        self.tab_buttons["posted"].config(text=f"Tasks I Posted ({counts['posted']})")
        self.tab_buttons["running"].config(text=f"Tasks I'm Running ({counts['running']})")
        self.tab_buttons["done"].config(text=f"Completed ({counts['done']})")
        self.tab_buttons["cancelled"].config(text=f"Cancelled ({counts['cancelled']})")

        outer, inner = make_scroll_area(self.tab_content); outer.pack(fill="both", expand=True, padx=18, pady=12)
        tab = self.active_tab.get(); keyword = self.my_search.get().strip().lower()
        base = """SELECT t.*, u.full_name as poster_name, r.full_name as runner_name FROM tasks t JOIN users u ON t.poster_id=u.id LEFT JOIN users r ON t.runner_id=r.id WHERE """
        params = []
        if tab == "posted": where = "t.poster_id=?"; params=[user["id"]]
        elif tab == "running": where = "t.runner_id=? AND t.status IN ('accepted','in_progress','awaiting_confirmation')"; params=[user["id"]]
        elif tab == "done": where = "(t.poster_id=? OR t.runner_id=?) AND t.status='completed'"; params=[user["id"], user["id"]]
        else: where = "(t.poster_id=? OR t.runner_id=?) AND t.status='cancelled'"; params=[user["id"], user["id"]]
        if keyword:
            where += " AND (LOWER(t.title) LIKE ? OR LOWER(t.location) LIKE ? OR LOWER(t.category) LIKE ?)"; params += [f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"]
        conn = db_connect(); tasks = conn.execute(base + where + " ORDER BY t.posted_on DESC", params).fetchall(); conn.close()
        if not tasks:
            msg = {"posted":"You have not posted any tasks yet.", "running":"You are not running any active tasks.", "done":"No completed tasks yet.", "cancelled":"No cancelled tasks."}.get(tab)
            if tab == "posted":
                empty_state(inner, "No posted tasks", msg, "Post a Task", lambda: self.app.go_to("PostTaskPage"))
            elif tab == "running":
                empty_state(inner, "No active work", msg, "Browse Tasks", lambda: self.app.go_to("BrowseTasksPage"))
            else:
                empty_state(inner, "Nothing here yet", msg)
            return
        for t in tasks:
            self.draw_my_task_card(inner, t)

    def draw_my_task_card(self, parent, task):
        extras = [("View", lambda tid=task["id"]: self.app.open_task_details(tid), BG_DARK)]
        user = self.app.logged_in_user
        if task["status"] == "open" and task["poster_id"] == user["id"]:
            extras += [("Edit", lambda tid=task["id"]: self.edit_task(tid), BLUE), ("Cancel", lambda tid=task["id"]: self.cancel_task(tid), RED_CLR)]
        elif task["status"] in ("accepted", "in_progress") and task["poster_id"] == user["id"]:
            extras += [("Cancel", lambda tid=task["id"]: self.cancel_task(tid), RED_CLR)]
        elif task["status"] == "accepted" and task["runner_id"] == user["id"]:
            extras += [("Start", lambda tid=task["id"]: self.start_task(tid), BLUE), ("Abandon", lambda tid=task["id"]: self.abandon_task(tid), RED_CLR)]
        elif task["status"] == "in_progress" and task["runner_id"] == user["id"]:
            extras += [("Submit Done", lambda tid=task["id"]: self.submit_done(tid), GREEN), ("Abandon", lambda tid=task["id"]: self.abandon_task(tid), RED_CLR)]
        elif task["status"] == "awaiting_confirmation" and task["poster_id"] == user["id"]:
            extras += [("Confirm Complete", lambda tid=task["id"]: self.mark_done(tid), GREEN)]
        elif task["status"] == "completed" and task["poster_id"] == user["id"] and task["runner_id"]:
            extras += [("Rate Runner", lambda tid=task["id"]: self.rate_runner(tid), PURPLE)]
        task_card(parent, task, extra_buttons=extras)

    def edit_task(self, task_id):
        task = fetch_task(task_id)
        if not task or task["status"] != "open":
            messagebox.showerror("Edit Task", "Only open tasks can be edited."); return
        EditTaskDialog(self, task, on_save=self.load)

    def start_task(self, task_id):
        conn = db_connect(); conn.execute("UPDATE tasks SET status='in_progress', started_on=? WHERE id=? AND status='accepted'", (now_iso(), task_id)); conn.commit(); conn.close(); self.load()

    def submit_done(self, task_id):
        conn = db_connect(); conn.execute("UPDATE tasks SET status='awaiting_confirmation', submitted_on=? WHERE id=? AND status='in_progress'", (now_iso(), task_id)); conn.commit(); conn.close(); messagebox.showinfo("Submitted", "Task submitted. The poster must now confirm completion."); self.load()

    def mark_done(self, task_id):
        if not messagebox.askyesno("Confirm Completion", "Confirm this task is complete?"): return
        conn = db_connect(); t = conn.execute("SELECT runner_id, status FROM tasks WHERE id=?", (task_id,)).fetchone()
        conn.execute("UPDATE tasks SET status='completed', finished_on=? WHERE id=?", (now_iso(), task_id))
        if t and t["runner_id"]: conn.execute("UPDATE users SET tasks_done=tasks_done+1 WHERE id=?", (t["runner_id"],))
        conn.commit(); conn.close(); messagebox.showinfo("Completed", "Task marked as completed."); self.load()

    def abandon_task(self, task_id):
        if not messagebox.askyesno("Abandon Task", "Give up this task and return it to open listings?"): return
        conn = db_connect(); conn.execute("UPDATE tasks SET runner_id=NULL, status='open', accepted_on=NULL, started_on=NULL, submitted_on=NULL WHERE id=?", (task_id,)); conn.commit(); conn.close(); self.load()

    def cancel_task(self, task_id):
        reason = simpledialog.askstring("Cancel Task", "Optional reason for cancellation:", parent=self)
        if reason is None: return
        conn = db_connect(); conn.execute("UPDATE tasks SET status='cancelled', cancelled_on=?, cancellation_reason=? WHERE id=?", (now_iso(), reason.strip(), task_id)); conn.commit(); conn.close(); self.load()

    def rate_runner(self, task_id):
        task = fetch_task(task_id)
        if not task or not task["runner_id"]:
            messagebox.showerror("Rating", "This task has no runner to rate."); return
        RatingDialog(self, task, self.app.logged_in_user["id"], on_save=self.load)


class TaskDetailsPage(tk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG_MAIN)
        self.app = app
        self.task_id = None
        TopNavBar(self, app)
        self.body = tk.Frame(self, bg=BG_MAIN)
        self.body.pack(fill="both", expand=True)

    def set_task(self, task_id):
        self.task_id = task_id

    def load(self):
        for w in self.body.winfo_children(): w.destroy()
        if not self.task_id: return
        task = fetch_task(self.task_id)
        user = self.app.logged_in_user
        if not task:
            tk.Label(self.body, text="Task not found.", bg=BG_MAIN, fg=RED_CLR, font=("Segoe UI", 14)).pack(pady=40); return
        outer, inner = make_scroll_area(self.body); outer.pack(fill="both", expand=True, padx=60, pady=24)
        page_header(inner, "Task", "Task Details", "Review the full information and use the available action buttons.")
        card = card_frame(inner, padx=32, pady=28); card.pack(fill="x")
        top = tk.Frame(card, bg=WHITE); top.pack(fill="x")
        tk.Label(top, text=task["title"], font=("Segoe UI", 22, "bold"), fg=DARK_TXT, bg=WHITE).pack(side="left")
        tk.Label(top, text=f"GBP {task['price']:.2f}", font=("Segoe UI", 18, "bold"), fg=ORANGE, bg=WHITE).pack(side="right")
        status = TASK_STATUS_LABELS.get(task["status"], task["status"])
        tk.Label(card, text=f"{status}  •  {task['category']}  •  {task['location']}", font=("Segoe UI", 11, "bold"), fg=TASK_STATUS_COLORS.get(task["status"], BLUE), bg=WHITE).pack(anchor="w", pady=(10, 8))
        tk.Label(card, text=f"Deadline: {task['deadline'] or 'Flexible'}", font=("Segoe UI", 10), fg=GRAY_TXT, bg=WHITE).pack(anchor="w")
        tk.Label(card, text=f"Posted by: {task['poster_name']}  |  Phone: {task['poster_phone']}", font=("Segoe UI", 10), fg=GRAY_TXT, bg=WHITE).pack(anchor="w", pady=(2, 0))
        if task["runner_name"]:
            rating = f" | Avg rating: {task['runner_rating']:.1f}/5" if task["runner_rating"] else ""
            tk.Label(card, text=f"Runner: {task['runner_name']}  |  Phone: {task['runner_phone']}{rating}", font=("Segoe UI", 10), fg=GRAY_TXT, bg=WHITE).pack(anchor="w", pady=(2, 0))
        tk.Label(card, text="Description", font=("Segoe UI", 13, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(18, 4))
        tk.Label(card, text=task["description"] or "No description provided.", font=("Segoe UI", 11), fg="#374151", bg=WHITE, wraplength=860, justify="left").pack(anchor="w", fill="x")
        if task["cancellation_reason"]:
            info_banner(card, f"Cancellation reason: {task['cancellation_reason']}", bg="#FEF2F2", fg=RED_CLR)
        btns = tk.Frame(card, bg=WHITE); btns.pack(anchor="e", pady=(22, 0))
        secondary_button(btns, "Back", lambda: self.app.go_to("MyTasksPage"), w=10).pack(side="left", padx=5)
        if task["status"] == "open" and task["poster_id"] != user["id"]:
            nice_button(btns, "Accept Task", lambda tid=task["id"]: self.accept(tid), color=GREEN, w=14).pack(side="left", padx=5)

    def accept(self, task_id):
        ok, msg = accept_task_record(task_id, self.app.logged_in_user["id"])
        messagebox.showinfo("ErrandMate", msg) if ok else messagebox.showerror("ErrandMate", msg)
        self.load()


class EditTaskDialog(tk.Toplevel):
    def __init__(self, parent, task, on_save):
        super().__init__(parent)
        self.task = task; self.on_save = on_save
        self.title("Edit Task"); self.geometry("560x560"); self.configure(bg=BG_MAIN); self.transient(parent); self.grab_set()
        card = card_frame(self, padx=26, pady=22); card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text="Edit Open Task", font=("Segoe UI", 18, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(0, 12))
        def field(label, value=""):
            tk.Label(card, text=label, font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(8,2))
            e = nice_entry(card, w=48); e.pack(fill="x", ipady=6); e.insert(0, value or ""); return e
        self.title_e = field("Title", task["title"])
        self.location_e = field("Location", task["location"])
        self.price_e = field("Price", str(task["price"]))
        self.deadline_e = field("Deadline", task["deadline"] or "")
        tk.Label(card, text="Category", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(8,2))
        self.cat_var = tk.StringVar(value=task["category"] or task_categories[0]); ttk.Combobox(card, textvariable=self.cat_var, values=task_categories, state="readonly").pack(fill="x", ipady=4)
        tk.Label(card, text="Description", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(8,2))
        self.desc = tk.Text(card, height=5, font=("Segoe UI", 10), relief="solid", bd=1); self.desc.pack(fill="x"); self.desc.insert("1.0", task["description"] or "")
        self.err = tk.Label(card, text="", fg=RED_CLR, bg=WHITE); self.err.pack(fill="x", pady=(8,0))
        btns = tk.Frame(card, bg=WHITE); btns.pack(pady=12)
        nice_button(btns, "Save", self.save, w=12).pack(side="left", padx=6); secondary_button(btns, "Cancel", self.destroy, w=10).pack(side="left", padx=6)

    def save(self):
        title = self.title_e.get().strip(); location = self.location_e.get().strip(); deadline = self.deadline_e.get().strip() or None
        try:
            price = float(self.price_e.get().strip())
            if price <= 0: raise ValueError
        except ValueError:
            self.err.config(text="Price must be a positive number."); return
        if len(title) < 5 or not location:
            self.err.config(text="Title must be 5+ characters and location is required."); return
        conn = db_connect(); conn.execute("UPDATE tasks SET title=?, description=?, category=?, location=?, price=?, deadline=? WHERE id=? AND status='open'", (title, self.desc.get("1.0", tk.END).strip(), self.cat_var.get(), location, price, deadline, self.task["id"])); conn.commit(); conn.close()
        self.on_save(); self.destroy()


class RatingDialog(tk.Toplevel):
    def __init__(self, parent, task, reviewer_id, on_save):
        super().__init__(parent)
        self.task = task; self.reviewer_id = reviewer_id; self.on_save = on_save
        self.title("Rate Runner"); self.geometry("430x360"); self.configure(bg=BG_MAIN); self.transient(parent); self.grab_set()
        card = card_frame(self, padx=26, pady=24); card.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Label(card, text=f"Rate {task['runner_name']}", font=("Segoe UI", 18, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w")
        self.rating = tk.IntVar(value=5)
        row = tk.Frame(card, bg=WHITE); row.pack(anchor="w", pady=14)
        for n in range(1, 6):
            tk.Radiobutton(row, text=f"{n}", variable=self.rating, value=n, bg=WHITE, fg=DARK_TXT, selectcolor="#F5F3FF").pack(side="left", padx=8)
        tk.Label(card, text="Review note", font=("Segoe UI", 10, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w")
        self.review = tk.Text(card, height=5, font=("Segoe UI", 10), relief="solid", bd=1); self.review.pack(fill="x", pady=(4,8))
        self.err = tk.Label(card, text="", fg=RED_CLR, bg=WHITE); self.err.pack(fill="x")
        btns = tk.Frame(card, bg=WHITE); btns.pack(pady=8)
        nice_button(btns, "Save Rating", self.save, w=14).pack(side="left", padx=6); secondary_button(btns, "Cancel", self.destroy, w=10).pack(side="left", padx=6)

    def save(self):
        conn = db_connect()
        try:
            conn.execute("INSERT INTO ratings (task_id, reviewer_id, runner_id, rating, review) VALUES (?,?,?,?,?)", (self.task["id"], self.reviewer_id, self.task["runner_id"], self.rating.get(), self.review.get("1.0", tk.END).strip()))
            conn.commit()
        except Exception:
            self.err.config(text="You have already rated this runner for this task."); conn.close(); return
        conn.close(); self.on_save(); self.destroy(); messagebox.showinfo("Rating Saved", "Thank you for rating the runner.")
