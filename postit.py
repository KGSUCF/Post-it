import tkinter as tk
from tkinter import font as tkfont
import json
import os

SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "postit_data.json")

PLACEHOLDER = "Click here to type your note..."

THEMES = {
    "Yellow":   {"bg": "#FFEF5E", "header": "#F5D800", "fg": "#3A2E00", "ph": "#B8A030"},
    "Pink":     {"bg": "#FFB3C6", "header": "#FF6B8A", "fg": "#3A0010", "ph": "#B86080"},
    "Blue":     {"bg": "#B3D9FF", "header": "#6BB5FF", "fg": "#001A3A", "ph": "#5090B8"},
    "Green":    {"bg": "#B8F0B8", "header": "#6BD96B", "fg": "#003A00", "ph": "#40A040"},
    "Orange":   {"bg": "#FFD4A3", "header": "#FFAA55", "fg": "#3A1A00", "ph": "#B87030"},
    "Lavender": {"bg": "#E8D0FF", "header": "#C080FF", "fg": "#1A003A", "ph": "#8050B0"},
}

SIZES = {
    "Small":  (180, 200),
    "Medium": (230, 250),
    "Large":  (280, 300),
}

FONTS = ["Segoe UI", "Arial", "Comic Sans MS", "Trebuchet MS", "Courier New"]

DEFAULT_THEME = "Yellow"
DEFAULT_SIZE  = "Large"
DEFAULT_FONT  = "Segoe UI"
DEFAULT_X, DEFAULT_Y = 100, 100


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
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.root.attributes("-alpha", 0.95)

        data = load_data()
        self.theme_name = data.get("theme", DEFAULT_THEME)
        if self.theme_name not in THEMES:
            self.theme_name = DEFAULT_THEME

        self.size_name = data.get("size", DEFAULT_SIZE)
        if self.size_name not in SIZES:
            self.size_name = DEFAULT_SIZE

        self.font_name = data.get("font", DEFAULT_FONT)
        if self.font_name not in FONTS:
            self.font_name = DEFAULT_FONT

        w, h = SIZES[self.size_name]
        # If the user manually resized, honour that over the size preset
        w = data.get("w", w)
        h = data.get("h", h)
        x = data.get("x", DEFAULT_X)
        y = data.get("y", DEFAULT_Y)
        saved_text = data.get("text", "")

        self.root.geometry(f"{w}x{h}+{x}+{y}")
        self.root.minsize(180, 150)

        self._drag_x = self._drag_y = 0
        self._placeholder_active = False

        self._build_ui(saved_text)
        self.root.bind("<Destroy>", lambda e: self._save())

    # ------------------------------------------------------------------ build

    def _build_ui(self, saved_text):
        t = THEMES[self.theme_name]

        self.root.configure(bg=t["bg"])

        # ---- Header ----
        self.header_frame = tk.Frame(self.root, bg=t["header"], height=32, cursor="fleur")
        self.header_frame.pack(fill="x", side="top")
        self.header_frame.pack_propagate(False)

        self.canvas_h = tk.Canvas(self.header_frame, bg=t["header"], height=32,
                                   highlightthickness=0, bd=0)
        self.canvas_h.pack(fill="both", expand=True)

        for i in range(3):
            cx = 18 + i * 14
            self.canvas_h.create_oval(cx - 5, 8, cx + 5, 24,
                                       outline=t["bg"], width=2, fill=t["header"])

        self.title_lbl = tk.Label(self.canvas_h, text="✏  Post-It", bg=t["header"],
                                   fg=t["fg"], font=("Segoe UI", 10, "bold"))
        self.title_lbl.place(relx=0.5, rely=0.5, anchor="center")

        self.close_btn = tk.Label(self.canvas_h, text="✕", bg=t["header"], fg=t["fg"],
                                   font=("Segoe UI", 10, "bold"), cursor="hand2",
                                   padx=6, pady=2)
        self.close_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-4, y=4)
        self.close_btn.bind("<Button-1>", lambda e: self._close())
        self.close_btn.bind("<Enter>", lambda e: self.close_btn.config(fg="#CC0000"))
        self.close_btn.bind("<Leave>", lambda e: self.close_btn.config(fg=THEMES[self.theme_name]["fg"]))

        for w in (self.header_frame, self.canvas_h, self.title_lbl):
            w.bind("<ButtonPress-1>", self._drag_start)
            w.bind("<B1-Motion>", self._drag_motion)
            w.bind("<Button-3>", self._show_menu)

        # ---- Text area ----
        self.note_font = tkfont.Font(family=self.font_name, size=12)
        self.text = tk.Text(
            self.root,
            bg=t["bg"], fg=t["fg"],
            font=self.note_font,
            relief="flat", bd=0,
            padx=12, pady=8,
            wrap="word",
            insertbackground=t["fg"],
            selectbackground=t["header"],
            selectforeground=t["fg"],
            undo=True,
        )
        self.text.pack(fill="both", expand=True)
        self.text.bind("<Button-3>", self._show_menu)

        if saved_text:
            self.text.insert("1.0", saved_text)
        else:
            self._show_placeholder()

        self.text.bind("<FocusIn>", self._on_focus_in)
        self.text.bind("<FocusOut>", self._on_focus_out)

        # ---- Resize grip ----
        self.grip = tk.Label(self.root, text="⤡", bg=t["header"], fg=t["bg"],
                              font=("Segoe UI", 9), cursor="size_nw_se",
                              width=2, padx=0, pady=0)
        self.grip.place(relx=1.0, rely=1.0, anchor="se")
        self.grip.bind("<ButtonPress-1>", self._resize_start)
        self.grip.bind("<B1-Motion>", self._resize_motion)

    # ---------------------------------------------------------------- theming

    def _apply_theme(self):
        t = THEMES[self.theme_name]
        self.root.configure(bg=t["bg"])
        self.header_frame.configure(bg=t["header"])
        self.canvas_h.configure(bg=t["header"])
        self.canvas_h.itemconfig("all", fill=t["header"], outline=t["bg"])
        self.title_lbl.configure(bg=t["header"], fg=t["fg"])
        self.close_btn.configure(bg=t["header"], fg=t["fg"])
        self.grip.configure(bg=t["header"], fg=t["bg"])
        self.text.configure(
            bg=t["bg"], fg=t["ph"] if self._placeholder_active else t["fg"],
            insertbackground=t["fg"],
            selectbackground=t["header"],
            selectforeground=t["fg"],
        )

    def _apply_font(self):
        self.note_font.configure(family=self.font_name)

    # --------------------------------------------------------------- menu

    def _show_menu(self, event):
        menu = tk.Menu(self.root, tearoff=0)

        # Color submenu
        color_menu = tk.Menu(menu, tearoff=0)
        for name in THEMES:
            color_menu.add_command(
                label=("• " if name == self.theme_name else "  ") + name,
                command=lambda n=name: self._set_theme(n),
            )
        menu.add_cascade(label="Color", menu=color_menu)

        # Size submenu
        size_menu = tk.Menu(menu, tearoff=0)
        for name in SIZES:
            size_menu.add_command(
                label=("• " if name == self.size_name else "  ") + name,
                command=lambda n=name: self._set_size(n),
            )
        menu.add_cascade(label="Size", menu=size_menu)

        # Font submenu
        font_menu = tk.Menu(menu, tearoff=0)
        for name in FONTS:
            font_menu.add_command(
                label=("• " if name == self.font_name else "  ") + name,
                command=lambda n=name: self._set_font(n),
            )
        menu.add_cascade(label="Font", menu=font_menu)

        menu.add_separator()
        menu.add_command(label="Close", command=self._close)

        menu.tk_popup(event.x_root, event.y_root)

    def _set_theme(self, name):
        self.theme_name = name
        self._apply_theme()

    def _set_size(self, name):
        self.size_name = name
        w, h = SIZES[name]
        x, y = self.root.winfo_x(), self.root.winfo_y()
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _set_font(self, name):
        self.font_name = name
        self._apply_font()

    # ---------------------------------------------------------- placeholder

    def _show_placeholder(self):
        self._placeholder_active = True
        self.text.config(fg=THEMES[self.theme_name]["ph"])
        self.text.insert("1.0", PLACEHOLDER)

    def _on_focus_in(self, event):
        if self._placeholder_active:
            self.text.delete("1.0", "end")
            self.text.config(fg=THEMES[self.theme_name]["fg"])
            self._placeholder_active = False

    def _on_focus_out(self, event):
        if not self.text.get("1.0", "end").strip():
            self._show_placeholder()

    # --------------------------------------------------------------- drag

    def _drag_start(self, event):
        self._drag_x = event.x_root - self.root.winfo_x()
        self._drag_y = event.y_root - self.root.winfo_y()

    def _drag_motion(self, event):
        self.root.geometry(f"+{event.x_root - self._drag_x}+{event.y_root - self._drag_y}")

    # -------------------------------------------------------------- resize

    def _resize_start(self, event):
        self._rx, self._ry = event.x_root, event.y_root
        self._rw, self._rh = self.root.winfo_width(), self.root.winfo_height()

    def _resize_motion(self, event):
        nw = max(180, self._rw + event.x_root - self._rx)
        nh = max(150, self._rh + event.y_root - self._ry)
        self.root.geometry(f"{nw}x{nh}+{self.root.winfo_x()}+{self.root.winfo_y()}")

    # --------------------------------------------------------- save / close

    def _save(self):
        text = "" if self._placeholder_active else self.text.get("1.0", "end").rstrip("\n")
        save_data({
            "text":  text,
            "x":     self.root.winfo_x(),
            "y":     self.root.winfo_y(),
            "w":     self.root.winfo_width(),
            "h":     self.root.winfo_height(),
            "theme": self.theme_name,
            "size":  self.size_name,
            "font":  self.font_name,
        })

    def _close(self):
        self._save()
        self.root.destroy()


def main():
    root = tk.Tk()
    PostItApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
