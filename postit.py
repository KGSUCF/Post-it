import tkinter as tk
from tkinter import font as tkfont
import json
import os
import sys

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "postit_data.json")

NOTE_BG = "#FFEF5E"
HEADER_BG = "#F5D800"
TEXT_FG = "#3A2E00"
SHADOW_COLOR = "#C8B400"

DEFAULT_WIDTH = 280
DEFAULT_HEIGHT = 300
DEFAULT_X = 100
DEFAULT_Y = 100
DEFAULT_TEXT = "Click here to type your note..."
PLACEHOLDER = "Click here to type your note..."


def load_data():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_data(data):
    try:
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


class PostItApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Post-It")
        self.root.overrideredirect(True)  # frameless
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)
        self.root.configure(bg=NOTE_BG)

        data = load_data()
        x = data.get("x", DEFAULT_X)
        y = data.get("y", DEFAULT_Y)
        w = data.get("w", DEFAULT_WIDTH)
        h = data.get("h", DEFAULT_HEIGHT)
        text = data.get("text", "")

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(180, 150)

        self._drag_x = 0
        self._drag_y = 0
        self._resizing = False

        self._build_ui(text)
        self.root.bind("<Destroy>", lambda e: self._save())

    def _build_ui(self, saved_text):
        # Header bar (drag handle)
        self.header = tk.Frame(self.root, bg=HEADER_BG, height=32, cursor="fleur")
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        # Decorative lines on header (notebook spiral look)
        canvas_h = tk.Canvas(self.header, bg=HEADER_BG, height=32,
                              highlightthickness=0, bd=0)
        canvas_h.pack(fill="both", expand=True)
        for i in range(3):
            cx = 18 + i * 14
            canvas_h.create_oval(cx - 5, 8, cx + 5, 24,
                                  outline=NOTE_BG, width=2, fill=HEADER_BG)

        # Title label in header
        lbl = tk.Label(canvas_h, text="✏  Post-It", bg=HEADER_BG,
                        fg=TEXT_FG, font=("Segoe UI", 10, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")

        # Close button
        close_btn = tk.Label(canvas_h, text="✕", bg=HEADER_BG, fg=TEXT_FG,
                              font=("Segoe UI", 10, "bold"), cursor="hand2",
                              padx=6, pady=2)
        close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)
        close_btn.bind("<Button-1>", lambda e: self._close())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg="#CC0000"))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_FG))

        # Drag bindings on header
        for widget in (self.header, canvas_h, lbl):
            widget.bind("<ButtonPress-1>", self._drag_start)
            widget.bind("<B1-Motion>", self._drag_motion)

        # Text area
        note_font = tkfont.Font(family="Segoe UI", size=12)
        self.text = tk.Text(
            self.root,
            bg=NOTE_BG,
            fg=TEXT_FG,
            font=note_font,
            relief="flat",
            bd=0,
            padx=12,
            pady=8,
            wrap="word",
            insertbackground=TEXT_FG,
            selectbackground=HEADER_BG,
            selectforeground=TEXT_FG,
            undo=True,
        )
        self.text.pack(fill="both", expand=True)

        self._placeholder_active = False
        if saved_text:
            self.text.insert("1.0", saved_text)
        else:
            self._show_placeholder()

        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)

        # Resize grip (bottom-right corner)
        grip = tk.Label(self.root, text="⤡", bg=SHADOW_COLOR, fg=NOTE_BG,
                         font=("Segoe UI", 9), cursor="size_nw_se",
                         width=2, padx=0, pady=0)
        grip.place(relx=1.0, rely=1.0, anchor="se")
        grip.bind("<ButtonPress-1>", self._resize_start)
        grip.bind("<B1-Motion>", self._resize_motion)

    # ---- Placeholder helpers ----

    def _show_placeholder(self):
        self._placeholder_active = True
        self.text.config(fg="#B8A030")
        self.text.insert("1.0", PLACEHOLDER)

    def _on_focus_in(self, event):
        if self._placeholder_active:
            self.text.delete("1.0", "end")
            self.text.config(fg=TEXT_FG)
            self._placeholder_active = False

    def _on_focus_out(self, event):
        if not self.text.get("1.0", "end").strip():
            self._show_placeholder()

    # ---- Drag ----

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event):
        x = event.x_root - self._drag_x
        y = event.y_root - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    # ---- Resize ----

    def _resize_start(self, event):
        self._resize_start_x = event.x_root
        self._resize_start_y = event.y_root
        self._resize_start_w = self.root.winfo_width()
        self._resize_start_h = self.root.winfo_height()

    def _resize_motion(self, event):
        dw = event.x_root - self._resize_start_x
        dh = event.y_root - self._resize_start_y
        new_w = max(180, self._resize_start_w + dw)
        new_h = max(150, self._resize_start_h + dh)
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        self.root.geometry(f"{new_w}x{new_h}+{x}+{y}")

    # ---- Save / Close ----

    def _save(self):
        text = "" if self._placeholder_active else self.text.get("1.0", "end").rstrip("\n")
        save_data({
            "text": text,
            "x": self.root.winfo_x(),
            "y": self.root.winfo_y(),
            "w": self.root.winfo_width(),
            "h": self.root.winfo_height(),
        })

    def _close(self):
        self._save()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = PostItApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
