# utils.py
from tkinter import filedialog, messagebox
import math
import threading
import os

def choose_file_and_compress(root, compressor, memory_manager):
    path = filedialog.askopenfilename(title="Select text file to compress", filetypes=[("Text files","*.txt"),("All files","*.*")])
    if not path:
        return
    out_path = filedialog.asksaveasfilename(title="Save compressed as", defaultextension=".bin")
    if not out_path:
        return
    tree_path = out_path + ".tree"
    def worker():
        out, ratio = compressor.compress_file(path, out_path, tree_path=tree_path)
        # measure size in KB roughly
        kb = math.ceil((os.path.getsize(out) - 1) / 1024) if os.path.exists(out) else 1
        memory_manager.allocate_with_policy(kb, f"File_{os.path.basename(out)}", fit_method="best", eviction_policy="lru")
        messagebox.showinfo("Done", f"Compressed to {out} (ratio {ratio}%). Stored ~{kb}KB in memory.")
    threading.Thread(target=worker, daemon=True).start()

# minimal helper for launching main window buttons from main_v2.py
