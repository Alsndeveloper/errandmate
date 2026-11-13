import tkinter as tk
from tkinter import ttk

from config import BG_MAIN


def make_scroll_area(parent):
    outer = tk.Frame(parent, bg=BG_MAIN)
    canvas = tk.Canvas(outer, bg=BG_MAIN, highlightthickness=0, bd=0)
    sb = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
    inner = tk.Frame(canvas, bg=BG_MAIN)

    inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
    canvas.configure(yscrollcommand=sb.set)

    def resize_inner(event):
        canvas.itemconfig(window_id, width=event.width)

    canvas.bind("<Configure>", resize_inner)
    canvas.pack(side="left", fill="both", expand=True)
    sb.pack(side="right", fill="y")

    def _on_enter(e):
        canvas.bind_all("<MouseWheel>", lambda ev: canvas.yview_scroll(int(-1 * (ev.delta / 120)), "units"))

    def _on_leave(e):
        canvas.unbind_all("<MouseWheel>")

    canvas.bind("<Enter>", _on_enter)
    canvas.bind("<Leave>", _on_leave)

    return outer, inner
