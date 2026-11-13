import tkinter as tk

from config import (
    BG_DARK, ORANGE, WHITE, BLUE, GRAY_TXT, GREEN, LIGHT_BDR, TASK_STATUS_LABELS,
    TASK_STATUS_COLORS, DARK_TXT, MUTED, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL
)
from ui.widgets import nice_button


def _chip(parent, text, color, fg=WHITE):
    return tk.Label(parent, text=f"  {text}  ", font=("Segoe UI", 8, "bold"), fg=fg, bg=color, padx=7, pady=4)


def task_card(parent, task_data, btn_text=None, btn_cmd=None, btn_color=GREEN, extra_buttons=None, show_status=True):
    card = tk.Frame(parent, bg=WHITE, padx=20, pady=18, highlightbackground=LIGHT_BDR, highlightthickness=1)
    card.pack(fill="x", pady=8, padx=10)

    top = tk.Frame(card, bg=WHITE)
    top.pack(fill="x")

    title_col = tk.Frame(top, bg=WHITE)
    title_col.pack(side="left", fill="x", expand=True)
    tk.Label(title_col, text=task_data["title"], font=("Segoe UI", 15, "bold"), fg=BG_DARK, bg=WHITE, anchor="w").pack(anchor="w")

    badges = tk.Frame(title_col, bg=WHITE)
    badges.pack(anchor="w", pady=(8, 0))
    cat = task_data["category"] if task_data["category"] else "Other"
    _chip(badges, cat, MUTED, fg=DARK_TXT).pack(side="left", padx=(0, 6))
    if show_status:
        status = task_data["status"] if "status" in task_data.keys() else "open"
        _chip(badges, TASK_STATUS_LABELS.get(status, status.title()), TASK_STATUS_COLORS.get(status, BLUE)).pack(side="left")

    price_badge = tk.Label(top, text=f"GBP {task_data['price']:.2f}", font=("Segoe UI", 14, "bold"), fg=ORANGE, bg=WHITE, padx=8)
    price_badge.pack(side="right", anchor="n")

    deadline_txt = task_data["deadline"] if task_data["deadline"] else "Flexible"
    poster_name = task_data["poster_name"] if "poster_name" in task_data.keys() else "Unknown"
    runner_name = task_data["runner_name"] if "runner_name" in task_data.keys() and task_data["runner_name"] else None

    info = f"📍 {task_data['location']}   •   ⏰ {deadline_txt}   •   Posted by {poster_name}"
    if runner_name:
        info += f"   •   Runner {runner_name}"
    tk.Label(card, text=info, font=FONT_SMALL, fg=GRAY_TXT, bg=WHITE).pack(anchor="w", pady=(12, 5))

    if task_data["description"]:
        desc = task_data["description"]
        if len(desc) > 220:
            desc = desc[:220].rstrip() + "..."
        tk.Label(card, text=desc, font=FONT_BODY, fg="#334155", bg=WHITE, anchor="w", wraplength=800, justify="left").pack(fill="x", pady=4)

    btn_row = tk.Frame(card, bg=WHITE)
    btn_row.pack(anchor="e", pady=(12, 0))

    if extra_buttons:
        for label, command, color in extra_buttons:
            nice_button(btn_row, label, command, color=color, w=max(10, min(18, len(label) + 2))).pack(side="left", padx=4)

    if btn_text and btn_cmd:
        nice_button(btn_row, btn_text, btn_cmd, color=btn_color, w=max(12, min(18, len(btn_text) + 2))).pack(side="left", padx=4)

    return card


def stat_card(parent, value, label, color):
    card = tk.Frame(parent, bg=WHITE, padx=18, pady=18, highlightbackground=LIGHT_BDR, highlightthickness=1)
    card.pack(side="left", expand=True, fill="x", padx=6)
    tk.Label(card, text=value, font=("Segoe UI", 24, "bold"), fg=color, bg=WHITE).pack(anchor="w")
    tk.Label(card, text=label, font=FONT_SMALL, fg=GRAY_TXT, bg=WHITE).pack(anchor="w", pady=(3, 0))
    return card
