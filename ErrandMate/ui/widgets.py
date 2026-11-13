import tkinter as tk

from config import (
    ORANGE, ORANGE2, WHITE, DARK_TXT, LIGHT_BDR, GRAY_TXT, MUTED,
    BG_SOFT, RED_CLR, FONT_BODY, FONT_BODY_BOLD, FONT_SMALL, FONT_TITLE
)


def nice_button(parent, txt, cmd, color=ORANGE, txt_color=WHITE, w=15, hover_color=None):
    """Modern flat button implemented with Label so colours render consistently in Tkinter."""
    hover_color = hover_color or ORANGE2
    b = tk.Label(
        parent,
        text=txt,
        bg=color,
        fg=txt_color,
        font=FONT_BODY_BOLD,
        relief="flat",
        cursor="hand2",
        padx=18,
        pady=10,
        width=w,
    )
    b.bind("<Button-1>", lambda e: cmd())
    b.bind("<Enter>", lambda e: b.config(bg=hover_color))
    b.bind("<Leave>", lambda e: b.config(bg=color))
    return b


def secondary_button(parent, txt, cmd, w=15):
    return nice_button(parent, txt, cmd, color=MUTED, txt_color=DARK_TXT, w=w, hover_color=LIGHT_BDR)


def danger_button(parent, txt, cmd, w=15):
    return nice_button(parent, txt, cmd, color=RED_CLR, txt_color=WHITE, w=w, hover_color="#DC2626")


def nice_entry(parent, w=28, hidden=False):
    e = tk.Entry(
        parent,
        font=FONT_BODY,
        bg=WHITE,
        fg=DARK_TXT,
        relief="flat",
        bd=0,
        width=w,
        highlightthickness=1,
        highlightcolor=ORANGE,
        highlightbackground=LIGHT_BDR,
        insertbackground=DARK_TXT,
    )
    if hidden:
        e.config(show="*")
    return e


def card_frame(parent, padx=28, pady=24, bg=WHITE):
    card = tk.Frame(parent, bg=bg, padx=padx, pady=pady, highlightbackground=LIGHT_BDR, highlightthickness=1)
    return card


def section_title(parent, title, subtitle=None, bg=None):
    bg = bg or parent.cget("bg")
    box = tk.Frame(parent, bg=bg)
    box.pack(fill="x", pady=(4, 16))
    tk.Label(box, text=title, font=FONT_TITLE, fg=DARK_TXT, bg=bg).pack(anchor="w")
    if subtitle:
        tk.Label(box, text=subtitle, font=FONT_BODY, fg=GRAY_TXT, bg=bg).pack(anchor="w", pady=(4, 0))
    return box


def page_header(parent, eyebrow, title, subtitle=None):
    box = card_frame(parent, padx=26, pady=22)
    box.pack(fill="x", pady=(0, 18))
    tk.Label(box, text=eyebrow.upper(), font=FONT_SMALL, fg=ORANGE, bg=WHITE).pack(anchor="w")
    tk.Label(box, text=title, font=("Segoe UI", 24, "bold"), fg=DARK_TXT, bg=WHITE).pack(anchor="w", pady=(4, 0))
    if subtitle:
        tk.Label(box, text=subtitle, font=FONT_BODY, fg=GRAY_TXT, bg=WHITE, wraplength=900, justify="left").pack(anchor="w", pady=(6, 0))
    return box


def info_banner(parent, text, bg=BG_SOFT, fg=DARK_TXT):
    banner = tk.Label(parent, text=text, font=FONT_BODY, fg=fg, bg=bg, padx=14, pady=11, anchor="w", justify="left")
    banner.pack(fill="x", pady=(0, 14))
    return banner


def empty_state(parent, title, message, button_text=None, button_cmd=None):
    box = card_frame(parent, padx=30, pady=32)
    box.pack(fill="x", pady=14, padx=10)
    tk.Label(box, text="✨", font=("Segoe UI", 28), bg=WHITE, fg=ORANGE).pack()
    tk.Label(box, text=title, font=("Segoe UI", 16, "bold"), fg=DARK_TXT, bg=WHITE).pack(pady=(8, 2))
    tk.Label(box, text=message, font=FONT_BODY, fg=GRAY_TXT, bg=WHITE, justify="center", wraplength=620).pack(pady=(0, 14))
    if button_text and button_cmd:
        nice_button(box, button_text, button_cmd, w=max(12, min(20, len(button_text) + 2))).pack()
    return box
