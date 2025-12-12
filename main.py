# main.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from memory_manager import MemoryManager
from smart_memory.compression_factory import CompressionFactory
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import numpy as np

APP_TITLE = "Smart Memory & Compression Manager"
STATE_FILE = "memory_state.json"


class SmartMemoryApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1100x800")

        # COLORS (no logic changes)
        self.dark_bg = "#1a0033"      # violet dark
        self.dark_text = "#EEEEEE"
        self.button_color = "#4C1A8A" # violet buttons
        self.button_glow = "#6A0DAD"  # neon glow
        self.button_hover = "#7F39FB"

        self.day_mode = False
        self.bg_color = self.dark_bg
        self.text_color = self.dark_text

        # LANGUAGE
        self.lang_ar = False
        self.lang_texts = {
            "en": {
                "title": "Smart Memory & Compression Manager",
                "refresh": "Refresh",
                "save": "Save State",
                "load": "Load State",
                "defrag": "Defragment",
                "compress": "Compress File",
                "free": "Free Selected",
                "toggle_theme": "Toggle Theme",
                "toggle_lang": "AR/EN",
                "usage": "Usage",
                "used_blocks": "Used Blocks",
                "freed": "Block Freed",
                "info_free": "Block is already free",
                "select_warning": "Select a block first"
            },
            "ar": {
                "title": "مدير الذاكرة والضغط الذكي",
                "refresh": "تحديث",
                "save": "حفظ الحالة",
                "load": "تحميل الحالة",
                "defrag": "إعادة تجميع",
                "compress": "ضغط ملف",
                "free": "تحرير المحدد",
                "toggle_theme": "تبديل الثيم",
                "toggle_lang": "EN/AR",
                "usage": "الاستخدام",
                "used_blocks": "الكتل المستخدمة",
                "freed": "تم تحرير الكتلة",
                "info_free": "الكتلة بالفعل فارغة",
                "select_warning": "اختر كتلة أولاً"
            }
        }

        # Memory & Compression
        self.memory = MemoryManager(total_blocks=12)
        self.compressor = CompressionFactory.get("huffman")

        self._build_ui()
        self.refresh()

    # ========================= UI =========================
    def _build_ui(self):
        bg = self.bg_color
        fg = self.text_color

        # Title
        self.title_lbl = tk.Label(self.root, text=self._text("title"),
                                  font=("Segoe UI", 22, "bold"),
                                  bg=bg, fg=fg)
        self.title_lbl.pack(pady=15)

        # Buttons Row
        btn_frame = tk.Frame(self.root, bg=bg)
        btn_frame.pack(fill="x", padx=10, pady=10)

        self.buttons = {}
        btn_list = [
            ("refresh", self.refresh),
            ("save", self.save_state),
            ("load", self.load_state),
            ("defrag", self.defragment),
            ("compress", self.compress_file),
            ("free", self.free_block),
            ("toggle_theme", self.toggle_theme),
            ("toggle_lang", self.toggle_language)
        ]

        for key, cmd in btn_list:
            btn = tk.Label(
                btn_frame,
                text=self._text(key),
                font=("Segoe UI", 10, "bold"),
                bg=self.button_color,
                fg="white",
                padx=14, pady=8,
                cursor="hand2",
                relief="flat",
                borderwidth=0
            )
            btn.pack(side="left", padx=8)

            # Hover effect (neon)
            btn.bind("<Enter>", lambda e, b=btn: b.config(bg=self.button_hover))
            btn.bind("<Leave>", lambda e, b=btn: b.config(bg=self.button_color))
            btn.bind("<Button-1>", lambda e, c=cmd: c())

            self.buttons[key] = btn

        # Memory Bar
        self.usage_canvas = tk.Canvas(self.root, width=1050, height=30,
                                      bg="#29004d", highlightthickness=0)
        self.usage_canvas.pack(pady=10)

        self.usage_lbl = tk.Label(self.root,
                                  text=f"{self._text('usage')}: 0%",
                                  font=("Segoe UI", 12, "bold"),
                                  bg=bg, fg=fg)
        self.usage_lbl.pack()

        # Memory Table
        columns = ("idx", "status", "size", "data")
        self.tree = ttk.Treeview(self.root, columns=columns,
                                 height=15, show="headings")
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(
            "Treeview",
            background="#2e004f",
            foreground="white",
            fieldbackground="#2e004f",
            font=("Segoe UI", 10)
        )
        style.map("Treeview", background=[("selected", "#7F39FB")])

        for col, w in zip(columns, [60, 120, 100, 700]):
            self.tree.heading(col, text=col.upper())
            self.tree.column(col, width=w, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=12, pady=10)

        # Pie Chart
        self.chart_frame = tk.Frame(self.root, bg=bg)
        self.chart_frame.pack(fill="both", expand=False, padx=12, pady=12)

        self.fig = Figure(figsize=(4.5, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)

        self.chart_canvas = FigureCanvasTkAgg(self.fig, master=self.chart_frame)
        self.chart_canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

        # Status bar
        self.status_text = tk.StringVar(value="Ready")
        self.status_lbl = tk.Label(
            self.root,
            textvariable=self.status_text,
            bg=bg,
            fg=fg,
            anchor="w",
            font=("Segoe UI", 10)
        )
        self.status_lbl.pack(fill="x", padx=12, pady=(0, 10))

    # ========================= FUNCTIONS =========================

    def refresh(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        max_size = max((b.size for b in self.memory.memory), default=1)
        for idx, b in enumerate(self.memory.memory, start=1):
            status = "Used" if b.is_allocated else "Free"
            label = b.data or "-"
            item = self.tree.insert("", "end", values=(idx, status, b.size, label))

            if b.is_allocated:
                self.tree.item(item, tags=("used",))
            else:
                self.tree.item(item, tags=("free",))

        # usage
        used = sum(b.size for b in self.memory.memory if b.is_allocated)
        total = sum(b.size for b in self.memory.memory)
        usage_percent = (used / total * 100) if total else 0
        self._animate_memory_bar(usage_percent)

        # pie
        free = total - used
        self._animate_pie(used, free)

        used_blocks = sum(1 for b in self.memory.memory if b.is_allocated)
        self.status_text.set(f"{self._text('used_blocks')}: {used_blocks}")

    def _animate_memory_bar(self, percent):
        self.usage_canvas.delete("all")
        width = 1050
        fill_w = int(percent / 100 * width)

        for i in range(fill_w):
            color = f"#{40 + i//8:02x}00{120 + i//20:02x}"
            self.usage_canvas.create_line(i, 0, i, 30, fill=color)

        self.usage_lbl.config(text=f"{self._text('usage')}: {percent:.1f}%")

    def _animate_pie(self, used, free):
        self.ax.clear()
        if (used + free) == 0:
            self.ax.text(0.5,0.5,"No Data", ha="center", va="center", color=self.text_color)
        else:
            self.ax.pie(
                [used, free],
                labels=["Used", "Free"],
                autopct="%1.1f%%",
                startangle=90,
                colors=["#7F39FB", "#35005c"],
                shadow=True,
                explode=[0.05, 0]
            )
        self.chart_canvas.draw()

    def save_state(self):
        self.memory.save_state(STATE_FILE)
        messagebox.showinfo("Saved", f"State saved to {STATE_FILE}")

    def load_state(self):
        if self.memory.load_state(STATE_FILE):
            self.refresh()
            messagebox.showinfo("Loaded", f"State loaded from {STATE_FILE}")

    def defragment(self):
        self.memory.defragment()
        self.refresh()

    def free_block(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Warning", self._text("select_warning"))
            return

        idx = int(self.tree.item(selected[0])["values"][0]) - 1
        block = self.memory.memory[idx]

        if block.is_allocated:
            block.is_allocated = False
            block.data = None
            self.refresh()
            messagebox.showinfo("Info", self._text("freed"))
        else:
            messagebox.showinfo("Info", self._text("info_free"))

    def compress_file(self):
        file_path = filedialog.askopenfilename(title="Select file to compress")
        if not file_path: return

        with open(file_path, "r") as f:
            data = f.read()

        encoded, tree, ratio, padding = self.compressor.compress(data)
        label = f"File_{file_path.split('/')[-1]}"
        self.memory.best_fit(len(encoded)//8 + 1, label)
        self.refresh()

    def toggle_theme(self):
        self.day_mode = not self.day_mode
        if self.day_mode:
            self.bg_color = "#FFFFFF"
            self.text_color = "#111"
        else:
            self.bg_color = self.dark_bg
            self.text_color = self.dark_text
        self._apply_theme()

    def toggle_language(self):
        self.lang_ar = not self.lang_ar
        for key, b in self.buttons.items():
            b.config(text=self._text(key))
        self.title_lbl.config(text=self._text("title"))
        self.refresh()

    def _text(self, key):
        return self.lang_texts["ar" if self.lang_ar else "en"].get(key, key)

    def _apply_theme(self):
        bg, fg = self.bg_color, self.text_color
        self.root.config(bg=bg)
        self.title_lbl.config(bg=bg, fg=fg)
        self.status_lbl.config(bg=bg, fg=fg)
        self.usage_lbl.config(bg=bg, fg=fg)
        self.chart_frame.config(bg=bg)
        self.refresh()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartMemoryApp(root)
    root.mainloop()
