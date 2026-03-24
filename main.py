"""
██████╗ ██╗   ██╗██╗     ██╗     ███████╗███████╗██╗   ██╗██╗  ██╗██╗   ██╗██████╗
██╔══██╗██║   ██║██║     ██║     ╚══███╔╝██╔════╝╚██╗ ██╔╝██║  ██║██║   ██║██╔══██╗
██████╔╝██║   ██║██║     ██║      ███╔╝ ███████╗ ╚████╔╝ ███████║██║   ██║██████╔╝
██╔══██╗██║   ██║██║     ██║     ███╔╝  ╚════██║  ╚██╔╝  ██╔══██║██║   ██║██╔══██╗
██║  ██║╚██████╔╝███████╗███████╗███████╗███████║   ██║   ██║  ██║╚██████╔╝██████╔╝
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚══════╝╚══════╝╚══════╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝
RullzsyHUB - Map Manager Tool
"""

import tkinter as tk
from tkinter import ttk, messagebox
import json, os, zipfile, shutil, threading, subprocess, time, re, sys
from pathlib import Path

# ─────────────────────────────────────────────────────────────────────────────
# CONFIG — Edit sesuai kebutuhan
# ─────────────────────────────────────────────────────────────────────────────
JSON_FILE        = "list_map.json"
REPO_DIR         = os.path.dirname(os.path.abspath(__file__))  # folder yg sama dgn script
GITHUB_RAW_BASE  = "https://raw.githubusercontent.com/BD16-XD/VIP-LOGIC-KOK-NYOLONG/refs/heads/main/"
ITEMS_PER_PAGE   = 10

# ─────────────────────────────────────────────────────────────────────────────
# TEMA — Red Dark / Hacker
# ─────────────────────────────────────────────────────────────────────────────
C = {
    "bg"       : "#0a0a0f",
    "surface"  : "#12121a",
    "card"     : "#1a1a26",
    "card2"    : "#1f1f2e",
    "border"   : "#2a1a2a",
    "accent"   : "#cc0000",
    "accent2"  : "#ff3333",
    "accent3"  : "#ff6666",
    "glow"     : "#8b0000",
    "success"  : "#22c55e",
    "warning"  : "#f59e0b",
    "danger"   : "#ef4444",
    "locked"   : "#f59e0b",
    "unlocked" : "#22c55e",
    "text"     : "#e8e8f0",
    "subtext"  : "#888899",
    "dim"      : "#555566",
    "white"    : "#ffffff",
    "input_bg" : "#0f0f1a",
    "hover"    : "#2a0a0a",
}

FONT_TITLE  = ("Consolas", 22, "bold")
FONT_HEADER = ("Consolas", 13, "bold")
FONT_BODY   = ("Consolas", 10)
FONT_SMALL  = ("Consolas", 9)
FONT_MONO   = ("Courier New", 9)
FONT_BTN    = ("Consolas", 10, "bold")
FONT_BRAND  = ("Consolas", 28, "bold")

# ─────────────────────────────────────────────────────────────────────────────
# DATA LAYER
# ─────────────────────────────────────────────────────────────────────────────
def load_data():
    p = os.path.join(REPO_DIR, JSON_FILE)
    if not os.path.exists(p):
        data = {"maps": []}
        save_data(data)
        return data
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    p = os.path.join(REPO_DIR, JSON_FILE)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def build_url(filename):
    """Build GitHub raw URL dari nama file."""
    return GITHUB_RAW_BASE + filename

def extract_filename_from_url(url):
    """Ambil nama file dari URL."""
    return url.split("/")[-1]

def get_all_json_files_in_repo():
    """Ambil semua file .json di repo (exclude list_map.json)."""
    json_files = []
    try:
        for fname in os.listdir(REPO_DIR):
            if fname.endswith(".json") and fname != JSON_FILE:
                json_files.append(fname)
    except Exception:
        pass
    return json_files

def get_tracked_json_files():
    """Ambil semua file .json yang terdaftar di list_map.json."""
    data = load_data()
    tracked = set()
    for m in data.get("maps", []):
        url = m.get("url", "")
        fname = extract_filename_from_url(url)
        if fname:
            tracked.add(fname)
    return tracked

def get_orphaned_json_files():
    """Ambil file .json yg ada di repo tapi tidak ada di list_map.json."""
    all_files = set(get_all_json_files_in_repo())
    tracked = get_tracked_json_files()
    return sorted(list(all_files - tracked))

# ─────────────────────────────────────────────────────────────────────────────
# GIT HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def git_cmd(args, cwd=None):
    """Jalankan perintah git, return (stdout, stderr, returncode)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=cwd or REPO_DIR,
            capture_output=True,
            text=True
        )
        return result.stdout, result.stderr, result.returncode
    except FileNotFoundError:
        return "", "Git not found. Pastikan git sudah terinstall.", 1

def git_push_with_progress(commit_msg, extra_files=None, deleted_files=None, log_cb=None):
    def log(pct, msg):
        if log_cb: log_cb(pct, msg)

    log(0, "⚡ Memulai proses git...")
    
    # Gunakan 'add -A' untuk mencakup SEMUA perubahan (tambah, edit, dan HAPUS)
    log(20, "📁 Menyiapkan perubahan (git add -A)...")
    out, err, code = git_cmd(["add", "-A"])
    if code != 0:
        log(-1, f"❌ Error git add: {err}")
        return False, err

    log(50, f"💾 Committing: {commit_msg}")
    out, err, code = git_cmd(["commit", "-m", commit_msg])
    
    # Jika tidak ada perubahan, kita anggap sukses
    if code != 0 and "nothing to commit" not in out + err:
        log(-1, f"❌ Error git commit: {err or out}")
        return False, err or out

    log(75, "🚀 Push ke GitHub...")
    out, err, code = git_cmd(["push", "origin", "main"])
    if code != 0:
        log(-1, f"❌ Error git push: {err}")
        return False, err

    log(100, "🎉 Sinkronisasi Berhasil!")
    return True, ""

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM WIDGETS
# ─────────────────────────────────────────────────────────────────────────────
class HoverButton(tk.Button):
    def __init__(self, master, hover_bg=None, hover_fg=None, **kw):
        self._normal_bg = kw.get("bg", C["card"])
        self._normal_fg = kw.get("fg", C["text"])
        self._hover_bg  = hover_bg or C["hover"]
        self._hover_fg  = hover_fg or C["white"]
        super().__init__(master, **kw)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)

    def _on_enter(self, _):
        self.config(bg=self._hover_bg, fg=self._hover_fg)

    def _on_leave(self, _):
        self.config(bg=self._normal_bg, fg=self._normal_fg)


class RedEntry(tk.Entry):
    def __init__(self, master, placeholder="", **kw):
        self._ph = placeholder
        kw.setdefault("bg", C["input_bg"])
        kw.setdefault("fg", C["text"])
        kw.setdefault("insertbackground", C["accent2"])
        kw.setdefault("relief", "flat")
        kw.setdefault("font", FONT_BODY)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightcolor", C["accent"])
        kw.setdefault("highlightbackground", C["border"])
        super().__init__(master, **kw)
        if placeholder:
            self._show_placeholder()
            self.bind("<FocusIn>",  self._on_focus_in)
            self.bind("<FocusOut>", self._on_focus_out)

    def _show_placeholder(self):
        self.insert(0, self._ph)
        self.config(fg=C["dim"])

    def _on_focus_in(self, _):
        if self.get() == self._ph:
            self.delete(0, tk.END)
            self.config(fg=C["text"])

    def _on_focus_out(self, _):
        if not self.get():
            self._show_placeholder()

    def get_real(self):
        v = self.get()
        return "" if v == self._ph else v

    def set_value(self, val):
        self.delete(0, tk.END)
        if val:
            self.insert(0, val)
            self.config(fg=C["text"])
        else:
            self._show_placeholder()


class DropZone(tk.Frame):
    """Drag-and-drop zone untuk file ZIP."""
    def __init__(self, master, on_drop=None, **kw):
        kw.setdefault("bg", C["input_bg"])
        kw.setdefault("relief", "flat")
        kw.setdefault("highlightthickness", 2)
        kw.setdefault("highlightbackground", C["border"])
        super().__init__(master, **kw)
        self.on_drop = on_drop
        self._dropped_path = None
        self._build()
        # Aktifkan drop jika tkinterdnd2 tersedia
        self._try_enable_dnd()

    def _build(self):
        self.config(height=90)
        self._label = tk.Label(
            self,
            text="📦  Drag & Drop file .zip di sini\natau klik untuk browse",
            bg=C["input_bg"], fg=C["dim"],
            font=FONT_SMALL, justify="center", cursor="hand2"
        )
        self._label.place(relx=0.5, rely=0.5, anchor="center")
        self._label.bind("<Button-1>", self._browse)
        self.bind("<Button-1>", self._browse)

    def _try_enable_dnd(self):
        try:
            self.drop_target_register("DND_Files")  # type: ignore
            self.dnd_bind("<<Drop>>", self._on_dnd_drop)
        except Exception:
            pass

    def _on_dnd_drop(self, event):
        path = event.data.strip("{}")
        self._handle_file(path)

    def _browse(self, _=None):
        from tkinter import filedialog
        path = filedialog.askopenfilename(filetypes=[("ZIP files", "*.zip")])
        if path:
            self._handle_file(path)

    def _handle_file(self, path):
        if not path.lower().endswith(".zip"):
            self._label.config(text="⚠️  Hanya file .zip yang diterima!", fg=C["danger"])
            return
        self._dropped_path = path
        fname = os.path.basename(path)
        self._label.config(
            text=f"✅  {fname}\n(file siap diupload)",
            fg=C["success"]
        )
        if self.on_drop:
            self.on_drop(path)

    def get_path(self):
        return self._dropped_path

    def reset(self):
        self._dropped_path = None
        self._label.config(
            text="📦  Drag & Drop file .zip di sini\natau klik untuk browse",
            fg=C["dim"]
        )

# ─────────────────────────────────────────────────────────────────────────────
# MAIN APPLICATION
# ─────────────────────────────────────────────────────────────────────────────
class RullzsyHUB(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("RullzsyHUB — Map Manager")
        self.geometry("1100x700")
        self.minsize(900, 600)
        self.configure(bg=C["bg"])

        # State
        self.data          = load_data()
        self.current_page  = 1
        self.filter_mode   = tk.StringVar(value="all")
        self.search_var    = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._refresh())

        self._build_ui()
        self._refresh()

    # ── UI BUILD ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        # ── Header ──
        hdr = tk.Frame(self, bg=C["surface"], height=70)
        hdr.pack(fill="x", side="top")
        hdr.pack_propagate(False)

        brand = tk.Label(
            hdr, text="⬡ RullzsyHUB",
            bg=C["surface"], fg=C["accent2"],
            font=("Consolas", 20, "bold")
        )
        brand.pack(side="left", padx=24, pady=12)

        sub = tk.Label(
            hdr, text="// MAP MANAGER v1.0",
            bg=C["surface"], fg=C["dim"],
            font=("Consolas", 9)
        )
        sub.pack(side="left", pady=20)

        # Status bar kanan atas
        self._status_lbl = tk.Label(
            hdr, text="", bg=C["surface"], fg=C["success"],
            font=FONT_SMALL
        )
        self._status_lbl.pack(side="right", padx=20)

        # ── Separator ──
        tk.Frame(self, bg=C["accent"], height=2).pack(fill="x")

        # ── Toolbar ──
        tb = tk.Frame(self, bg=C["surface"], pady=10)
        tb.pack(fill="x")

        # Search
        tk.Label(tb, text="🔍", bg=C["surface"], fg=C["subtext"], font=FONT_BODY).pack(side="left", padx=(18,4))
        self._search_entry = RedEntry(tb, placeholder="Cari map...", width=28)
        self._search_entry.pack(side="left", ipady=5)
        self._search_entry.bind("<KeyRelease>", lambda e: self._on_search())

        # Filter buttons
        tk.Label(tb, text="Filter:", bg=C["surface"], fg=C["subtext"], font=FONT_SMALL).pack(side="left", padx=(20,6))
        for label, val in [("Semua", "all"), ("Unlocked", "unlocked"), ("Maintenance", "maintenance")]:
            self._make_filter_btn(tb, label, val)

        # Add New Map button
        add_btn = HoverButton(
            tb, text="＋  Add New Map",
            bg=C["accent"], fg=C["white"],
            hover_bg=C["accent2"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=16, pady=5,
            cursor="hand2", command=self._open_add_modal
        )
        add_btn.pack(side="right", padx=18)

        # Cleanup Orphaned Files button
        cleanup_btn = HoverButton(
            tb, text="🗑 JSON Not List",
            bg=C["card"], fg=C["subtext"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=FONT_BTN, relief="flat", padx=12, pady=5,
            cursor="hand2", command=self._open_cleanup_modal
        )
        cleanup_btn.pack(side="right", padx=4)

        # Apply Changes button
        apply_btn = HoverButton(
            tb, text="⬆ Apply",
            bg=C["accent"], fg=C["white"],
            hover_bg=C["accent2"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=14, pady=5,
            cursor="hand2", command=self._apply_changes
        )
        apply_btn.pack(side="right", padx=4)

        # ── Map count info ──
        self._info_frame = tk.Frame(self, bg=C["bg"])
        self._info_frame.pack(fill="x", padx=20, pady=(8,0))
        self._count_lbl = tk.Label(
            self._info_frame, text="", bg=C["bg"],
            fg=C["subtext"], font=FONT_SMALL
        )
        self._count_lbl.pack(side="left")

        # ── Scrollable list area ──
        self._list_frame = tk.Frame(self, bg=C["bg"])
        self._list_frame.pack(fill="both", expand=True, padx=20, pady=8)

        # ── Pagination bar ──
        self._pag_frame = tk.Frame(self, bg=C["bg"])
        self._pag_frame.pack(fill="x", padx=20, pady=(0,12))

    def _make_filter_btn(self, parent, label, val):
        def cmd():
            self.filter_mode.set(val)
            self.current_page = 1
            self._refresh()
        btn = HoverButton(
            parent, text=label,
            bg=C["card"] if self.filter_mode.get() != val else C["accent"],
            fg=C["text"], hover_bg=C["accent"], hover_fg=C["white"],
            font=FONT_SMALL, relief="flat", padx=10, pady=4,
            cursor="hand2", command=cmd
        )
        btn.pack(side="left", padx=3)
        # tag supaya bisa di-refresh warnanya
        btn._val = val
        btn._label = label
        # simpan referensi
        if not hasattr(self, "_filter_btns"):
            self._filter_btns = []
        self._filter_btns.append(btn)

    # ── SEARCH & FILTER ───────────────────────────────────────────────────────
    def _on_search(self):
        self.current_page = 1
        self._refresh()

    def _filtered_maps(self):
        """Return list of (original_index, map_dict) setelah filter & search."""
        q    = self._search_entry.get_real().lower().strip()
        mode = self.filter_mode.get()
        maps = self.data.get("maps", [])
        result = []
        for real_idx, m in enumerate(maps):
            # filter status
            locked = m.get("locked", False)
            if mode == "unlocked"    and locked:      continue
            if mode == "maintenance" and not locked:  continue
            # filter search
            if q and q not in m.get("name", "").lower() and q not in m.get("url", "").lower():
                continue
            result.append((real_idx, m))   # ← simpan index ASLI
        return result

    # ── REFRESH / RENDER ──────────────────────────────────────────────────────
    def _refresh(self):
        # Update filter btn colors
        if hasattr(self, "_filter_btns"):
            cur = self.filter_mode.get()
            for btn in self._filter_btns:
                if btn._val == cur:
                    btn.config(bg=C["accent"], fg=C["white"])
                    btn._normal_bg = C["accent"]
                else:
                    btn.config(bg=C["card"], fg=C["text"])
                    btn._normal_bg = C["card"]

        maps = self._filtered_maps()   # list of (real_idx, map_dict)
        total = len(maps)
        pages = max(1, (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        if self.current_page > pages:
            self.current_page = pages

        start = (self.current_page - 1) * ITEMS_PER_PAGE
        end   = start + ITEMS_PER_PAGE
        page_maps = maps[start:end]

        # Count label
        self._count_lbl.config(
            text=f"Menampilkan {len(page_maps)} dari {total} map  |  "
                 f"Halaman {self.current_page}/{pages}"
        )

        # Clear list
        for w in self._list_frame.winfo_children():
            w.destroy()

        # Render header row
        self._render_header()

        # Render map rows — pakai display_idx (urutan tampil) dan real_idx (index asli di data)
        for display_idx, (real_idx, m) in enumerate(page_maps):
            self._render_row(display_idx, m, real_idx)

        # Render pagination
        self._render_pagination(pages)

    def _render_header(self):
        hdr = tk.Frame(self._list_frame, bg=C["card2"], pady=6)
        hdr.pack(fill="x", pady=(0, 2))
        cols = [("#", 4), ("Nama Map", 28), ("File / URL", 42), ("Status", 10), ("Aksi", 14)]
        for label, w in cols:
            tk.Label(
                hdr, text=label, bg=C["card2"], fg=C["accent2"],
                font=("Consolas", 9, "bold"), width=w, anchor="w"
            ).pack(side="left", padx=(6,0))

    def _render_row(self, display_idx, m, real_idx):
        """
        display_idx : urutan baris di halaman saat ini (0-based) — untuk zebra stripe & nomor tampil
        real_idx    : index ASLI di self.data["maps"] — untuk semua action (lock/edit/delete)
        """
        locked   = m.get("locked", False)
        row_bg   = C["card"] if display_idx % 2 == 0 else C["card2"]
        row      = tk.Frame(self._list_frame, bg=row_bg, pady=4)
        row.pack(fill="x", pady=1)

        # No (nomor urut tampil, bukan index asli)
        page_start = (self.current_page - 1) * ITEMS_PER_PAGE
        display_no = page_start + display_idx + 1
        tk.Label(row, text=str(display_no), bg=row_bg, fg=C["dim"],
                 font=FONT_SMALL, width=4, anchor="w").pack(side="left", padx=(8,0))

        # Nama
        name_color = C["locked"] if locked else C["text"]
        tk.Label(row, text=m.get("name",""), bg=row_bg, fg=name_color,
                 font=("Consolas", 10, "bold"), width=28, anchor="w").pack(side="left", padx=(6,0))

        # URL (truncated)
        url = m.get("url", "")
        fname = extract_filename_from_url(url)
        url_text = fname if fname else url
        tk.Label(row, text=url_text, bg=row_bg, fg=C["subtext"],
                 font=FONT_MONO, width=42, anchor="w").pack(side="left", padx=(6,0))

        # Status badge
        if locked:
            badge_text = "🔒 LOCKED"
            badge_fg   = C["locked"]
        else:
            badge_text = "🔓 UNLOCKED"
            badge_fg   = C["success"]
        tk.Label(row, text=badge_text, bg=row_bg, fg=badge_fg,
                 font=FONT_SMALL, width=12, anchor="w").pack(side="left", padx=(6,0))

        # Action buttons
        btn_frame = tk.Frame(row, bg=row_bg)
        btn_frame.pack(side="left", padx=6)

        # Lock/Unlock — pakai real_idx agar selalu tepat sasaran
        lock_icon = "🔒" if not locked else "🔓"
        lock_fg   = C["warning"] if not locked else C["success"]
        HoverButton(
            btn_frame, text=lock_icon, bg=row_bg, fg=lock_fg,
            hover_bg=C["hover"], hover_fg=C["white"],
            font=("Consolas", 12), relief="flat", padx=4, cursor="hand2",
            command=lambda ri=real_idx: self._toggle_lock(ri)
        ).pack(side="left", padx=2)

        # Edit
        HoverButton(
            btn_frame, text="✏", bg=row_bg, fg=C["accent3"],
            hover_bg=C["hover"], hover_fg=C["white"],
            font=("Consolas", 12), relief="flat", padx=4, cursor="hand2",
            command=lambda ri=real_idx, mm=m: self._open_edit_modal(ri, mm)
        ).pack(side="left", padx=2)

        # Delete
        HoverButton(
            btn_frame, text="✕", bg=row_bg, fg=C["danger"],
            hover_bg="#3a0000", hover_fg=C["white"],
            font=("Consolas", 12, "bold"), relief="flat", padx=4, cursor="hand2",
            command=lambda ri=real_idx, mm=m: self._delete_map(ri, mm)
        ).pack(side="left", padx=2)

    def _render_pagination(self, pages):
        for w in self._pag_frame.winfo_children():
            w.destroy()

        if pages <= 1:
            return

        tk.Label(self._pag_frame, text="Halaman:", bg=C["bg"], fg=C["subtext"],
                 font=FONT_SMALL).pack(side="left", padx=(0,8))

        # Prev
        HoverButton(
            self._pag_frame, text="◀", bg=C["card"], fg=C["text"],
            hover_bg=C["accent"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=10, pady=3,
            cursor="hand2",
            command=lambda: self._go_page(self.current_page - 1)
        ).pack(side="left", padx=2)

        # Page numbers (show max 7 buttons)
        start_p = max(1, self.current_page - 3)
        end_p   = min(pages, start_p + 6)
        for p in range(start_p, end_p + 1):
            is_cur = (p == self.current_page)
            HoverButton(
                self._pag_frame, text=str(p),
                bg=C["accent"] if is_cur else C["card"],
                fg=C["white"] if is_cur else C["text"],
                hover_bg=C["accent2"], hover_fg=C["white"],
                font=FONT_BTN, relief="flat", padx=9, pady=3,
                cursor="hand2",
                command=lambda pp=p: self._go_page(pp)
            ).pack(side="left", padx=2)

        # Next
        HoverButton(
            self._pag_frame, text="▶", bg=C["card"], fg=C["text"],
            hover_bg=C["accent"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=10, pady=3,
            cursor="hand2",
            command=lambda: self._go_page(self.current_page + 1)
        ).pack(side="left", padx=2)

        tk.Label(self._pag_frame, text=f"/ {pages} halaman", bg=C["bg"],
                 fg=C["subtext"], font=FONT_SMALL).pack(side="left", padx=8)

    def _go_page(self, p):
        maps  = self._filtered_maps()
        pages = max(1, (len(maps) + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE)
        self.current_page = max(1, min(p, pages))
        self._refresh()

    # ── ACTIONS ───────────────────────────────────────────────────────────────
    def _toggle_lock(self, idx):
        m = self.data["maps"][idx]
        m["locked"] = not m.get("locked", False)
        save_data(self.data)
        status = "dikunci 🔒" if m["locked"] else "dibuka kuncinya 🔓"
        self._set_status(f"'{m['name']}' {status}", C["warning"])
        self._refresh()

    def _delete_map(self, idx, m):
        # Baris di bawah ini HARUS menjorok ke dalam
        ok = messagebox.askyesno(
            "Konfirmasi Hapus",
            f"Yakin ingin menghapus map:\n\n  {m['name']}\n\nFile akan dihapus dari folder lokal.",
            icon="warning"
        )
        if ok:
            # 1. Hapus file .json fisik secara lokal
            fname = extract_filename_from_url(m.get("url", ""))
            fpath = os.path.join(REPO_DIR, fname)
            
            if fname and os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except Exception as ex:
                    messagebox.showerror("Error", f"Gagal hapus file fisik: {ex}")
                    return
            
            # 2. Hapus dari list data di memori
            self.data["maps"].pop(idx)
            save_data(self.data)
            
            # 3. Update UI (Hanya lokal, sinkronisasi dilakukan lewat tombol APPLY)
            self._set_status(f"'{m['name']}' dihapus lokal. Klik Apply untuk Push.", C["warning"])
            self._refresh()

    def _set_status(self, msg, color=None):
        self._status_lbl.config(text=msg, fg=color or C["success"])
        self.after(4000, lambda: self._status_lbl.config(text=""))

    # ── MODAL BASE ─────────────────────────────────────────────────────────────
    def _make_modal(self, title, width=560, height=520):
        modal = tk.Toplevel(self)
        modal.title(title)
        modal.geometry(f"{width}x{height}")
        modal.configure(bg=C["surface"])
        modal.transient(self)
        modal.grab_set()
        modal.resizable(False, False)
        # Center
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width()  - width)  // 2
        y = self.winfo_y() + (self.winfo_height() - height) // 2
        modal.geometry(f"{width}x{height}+{x}+{y}")

        # Header stripe
        tk.Frame(modal, bg=C["accent"], height=3).pack(fill="x")
        tk.Label(
            modal, text=title, bg=C["surface"], fg=C["accent2"],
            font=FONT_HEADER, pady=14
        ).pack()
        tk.Frame(modal, bg=C["border"], height=1).pack(fill="x", padx=20)

        return modal

    def _label_entry(self, parent, text, placeholder="", width=42):
        tk.Label(parent, text=text, bg=C["surface"], fg=C["subtext"],
                 font=FONT_SMALL, anchor="w").pack(fill="x", padx=28, pady=(12,2))
        e = RedEntry(parent, placeholder=placeholder, width=width)
        e.pack(padx=28, ipady=6, fill="x")
        return e

    # ── ADD MAP MODAL ─────────────────────────────────────────────────────────
    def _open_add_modal(self):
        modal = self._make_modal("⬡ Add New Map", width=560, height=540)
        body  = tk.Frame(modal, bg=C["surface"])
        body.pack(fill="both", expand=True)

        e_name = self._label_entry(body, "Enter name map", "Masukkan nama map...")
        e_file = self._label_entry(body, "Enter name file (.json)", "Nama file otomatis dari ZIP...")

        # Drop zone
        tk.Label(body, text="Upload file .zip", bg=C["surface"], fg=C["subtext"],
                 font=FONT_SMALL, anchor="w").pack(fill="x", padx=28, pady=(14,2))

        zone_frame = tk.Frame(body, bg=C["surface"])
        zone_frame.pack(fill="x", padx=28)

        drop_zone = DropZone(zone_frame, height=90)
        drop_zone.pack(fill="x")

        self._zip_path_add = None
        self._zip_json_files_add = []

        def on_zip_drop(path):
            self._zip_path_add = path
            jsons = []
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    jsons = [n for n in zf.namelist() if n.endswith(".json")]
            except Exception as ex:
                messagebox.showerror("Error", f"Gagal baca zip: {ex}", parent=modal)
                return
            self._zip_json_files_add = jsons
            if jsons:
                fname = os.path.basename(jsons[0])
                e_file.set_value(fname)

        drop_zone.on_drop = on_zip_drop

        # Browse button fallback
        HoverButton(
            zone_frame, text="📂 Browse ZIP",
            bg=C["card"], fg=C["subtext"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=FONT_SMALL, relief="flat", padx=8, pady=3,
            cursor="hand2", command=lambda: on_zip_drop(drop_zone._browse())
        ).pack(anchor="e", pady=4)

        # Progress
        prog_frame = tk.Frame(body, bg=C["surface"])
        prog_frame.pack(fill="x", padx=28, pady=(8,0))
        prog_bar = ttk.Progressbar(prog_frame, length=500, mode="determinate")
        prog_log  = tk.Label(prog_frame, text="", bg=C["surface"], fg=C["subtext"],
                             font=FONT_SMALL, wraplength=480, justify="left")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("red.Horizontal.TProgressbar",
                        troughcolor=C["input_bg"], background=C["accent"],
                        darkcolor=C["accent2"], lightcolor=C["accent2"],
                        bordercolor=C["border"])
        prog_bar.config(style="red.Horizontal.TProgressbar")

        # Buttons
        btn_frame = tk.Frame(body, bg=C["surface"])
        btn_frame.pack(side="bottom", fill="x", padx=28, pady=16)

        def do_upload():
            name  = e_name.get_real().strip()
            fname = e_file.get_real().strip()

            if not name:
                messagebox.showerror("Error", "Nama map tidak boleh kosong!", parent=modal)
                return
            if not fname:
                messagebox.showerror("Error", "Nama file tidak boleh kosong!", parent=modal)
                return
            if not self._zip_path_add:
                messagebox.showerror("Error", "Belum ada file ZIP yang dipilih!", parent=modal)
                return

            # Ensure filename ends with .json
            if not fname.endswith(".json"):
                fname += ".json"

            url = build_url(fname)

            # Check duplicate name
            for m in self.data["maps"]:
                if m["name"].lower() == name.lower():
                    if not messagebox.askyesno("Duplikat", f"Map '{name}' sudah ada. Tetap tambahkan?", parent=modal):
                        return
                    break

            upload_btn.config(state="disabled", text="Uploading...")
            prog_bar.pack(fill="x", pady=(4,0))
            prog_log.pack(fill="x", pady=2)

            def task():
                # Extract JSON from zip and copy langsung ke folder utama repo
                extra_files = []
                try:
                    with zipfile.ZipFile(self._zip_path_add, "r") as zf:
                        all_jsons = [n for n in zf.namelist() if n.endswith(".json")]
                        if all_jsons:
                            src_name = all_jsons[0]
                            dest_path = os.path.join(REPO_DIR, fname)
                            with zf.open(src_name) as src, open(dest_path, "wb") as dst:
                                dst.write(src.read())
                            extra_files.append(fname)  # langsung nama file, tanpa subfolder
                except Exception as ex:
                    self.after(0, lambda: prog_log.config(
                        text=f"❌ Gagal ekstrak zip: {ex}", fg=C["danger"]))
                    self.after(0, lambda: upload_btn.config(state="normal", text="Upload"))
                    return

                # Add to data
                self.data["maps"].append({"name": name, "url": url, "locked": False})
                save_data(self.data)

                def log_cb(pct, msg):
                    def _upd():
                        if pct >= 0:
                            prog_bar["value"] = pct
                        prog_log.config(
                            text=msg,
                            fg=C["success"] if pct == 100 else (C["danger"] if pct < 0 else C["subtext"])
                        )
                    self.after(0, _upd)

                ok, err = git_push_with_progress(
                    f"Add map: {name}", extra_files=extra_files, log_cb=log_cb
                )

                def finish():
                    upload_btn.config(state="normal", text="Upload")
                    if ok:
                        self._set_status(f"✅ '{name}' berhasil ditambahkan & di-push!", C["success"])
                        self._refresh()
                        self.after(1500, modal.destroy)
                    else:
                        messagebox.showerror("Git Error", f"Push gagal:\n{err}", parent=modal)

                self.after(0, finish)

            threading.Thread(target=task, daemon=True).start()

        upload_btn = HoverButton(
            btn_frame, text="⬆  Upload",
            bg=C["accent"], fg=C["white"],
            hover_bg=C["accent2"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=20, pady=7,
            cursor="hand2", command=do_upload
        )
        upload_btn.pack(side="right", padx=(8,0))

        HoverButton(
            btn_frame, text="Batal",
            bg=C["card"], fg=C["text"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=FONT_BTN, relief="flat", padx=14, pady=7,
            cursor="hand2", command=modal.destroy
        ).pack(side="right")

    # ── EDIT MAP MODAL ────────────────────────────────────────────────────────
    def _open_edit_modal(self, idx, m):
        modal = self._make_modal(f"✏  Edit Map — {m['name']}", width=560, height=560)
        body  = tk.Frame(modal, bg=C["surface"])
        body.pack(fill="both", expand=True)

        e_name = self._label_entry(body, "Nama Map", "Nama map...")
        e_name.set_value(m.get("name",""))

        cur_fname = extract_filename_from_url(m.get("url",""))
        e_file = self._label_entry(body, "Nama File (.json)", "Nama file...")
        e_file.set_value(cur_fname)

        # Replace JSON file (optional)
        tk.Label(body, text="Ganti file .json (opsional — drag .zip baru)",
                 bg=C["surface"], fg=C["subtext"], font=FONT_SMALL, anchor="w"
                 ).pack(fill="x", padx=28, pady=(14,2))

        drop_zone = DropZone(body, height=80)
        drop_zone.pack(fill="x", padx=28)

        self._zip_path_edit = None

        def on_zip_drop_edit(path):
            self._zip_path_edit = path
            jsons = []
            try:
                with zipfile.ZipFile(path, "r") as zf:
                    jsons = [n for n in zf.namelist() if n.endswith(".json")]
            except Exception as ex:
                messagebox.showerror("Error", f"Gagal baca zip: {ex}", parent=modal)
                return
            if jsons:
                fname = os.path.basename(jsons[0])
                e_file.set_value(fname)

        drop_zone.on_drop = on_zip_drop_edit

        # Progress
        prog_frame = tk.Frame(body, bg=C["surface"])
        prog_frame.pack(fill="x", padx=28, pady=(8,0))
        prog_bar = ttk.Progressbar(prog_frame, length=500, mode="determinate",
                                   style="red.Horizontal.TProgressbar")
        prog_log  = tk.Label(prog_frame, text="", bg=C["surface"], fg=C["subtext"],
                             font=FONT_SMALL, wraplength=480, justify="left")

        btn_frame = tk.Frame(body, bg=C["surface"])
        btn_frame.pack(side="bottom", fill="x", padx=28, pady=16)

        def do_save():
            new_name  = e_name.get_real().strip()
            new_fname = e_file.get_real().strip()

            if not new_name or not new_fname:
                messagebox.showerror("Error", "Nama dan file tidak boleh kosong!", parent=modal)
                return

            if not new_fname.endswith(".json"):
                new_fname += ".json"

            new_url = build_url(new_fname)

            save_btn.config(state="disabled", text="Menyimpan...")
            prog_bar.pack(fill="x", pady=(4,0))
            prog_log.pack(fill="x", pady=2)

            def task():
                extra_files = []
                deleted_files = []
                
                # PERBAIKAN: Hapus file lama jika nama file berubah atau ada zip baru
                old_fname = cur_fname
                
                # Jika ada zip baru
                if self._zip_path_edit:
                    try:
                        with zipfile.ZipFile(self._zip_path_edit, "r") as zf:
                            all_jsons = [n for n in zf.namelist() if n.endswith(".json")]
                            if all_jsons:
                                src_name = all_jsons[0]
                                dest_path = os.path.join(REPO_DIR, new_fname)
                                with zf.open(src_name) as src, open(dest_path, "wb") as dst:
                                    dst.write(src.read())
                                extra_files.append(new_fname)
                                
                                # Hapus file lama jika nama file berubah
                                if old_fname and old_fname != new_fname:
                                    old_fpath = os.path.join(REPO_DIR, old_fname)
                                    if os.path.exists(old_fpath):
                                        try:
                                            os.remove(old_fpath)
                                            deleted_files.append(old_fname)
                                        except Exception:
                                            pass
                    except Exception as ex:
                        self.after(0, lambda: prog_log.config(
                            text=f"❌ Gagal ekstrak: {ex}", fg=C["danger"]))
                        self.after(0, lambda: save_btn.config(state="normal", text="Apply Changes"))
                        return
                else:
                    # Jika tidak ada zip baru tapi nama file berubah, rename file
                    if old_fname and old_fname != new_fname:
                        old_fpath = os.path.join(REPO_DIR, old_fname)
                        new_fpath = os.path.join(REPO_DIR, new_fname)
                        if os.path.exists(old_fpath):
                            try:
                                os.rename(old_fpath, new_fpath)
                                extra_files.append(new_fname)
                                deleted_files.append(old_fname)
                            except Exception as ex:
                                self.after(0, lambda: prog_log.config(
                                    text=f"❌ Gagal rename file: {ex}", fg=C["danger"]))
                                self.after(0, lambda: save_btn.config(state="normal", text="Apply Changes"))
                                return

                # Update data
                self.data["maps"][idx]["name"] = new_name
                self.data["maps"][idx]["url"]  = new_url
                save_data(self.data)

                def log_cb(pct, msg):
                    def _upd():
                        if pct >= 0:
                            prog_bar["value"] = pct
                        prog_log.config(
                            text=msg,
                            fg=C["success"] if pct == 100 else (C["danger"] if pct < 0 else C["subtext"])
                        )
                    self.after(0, _upd)

                ok, err = git_push_with_progress(
                    f"Edit map: {new_name}", 
                    extra_files=extra_files if extra_files else None,
                    deleted_files=deleted_files if deleted_files else None,
                    log_cb=log_cb
                )

                def finish():
                    save_btn.config(state="normal", text="Apply Changes")
                    if ok:
                        self._set_status(f"✅ '{new_name}' berhasil diupdate!", C["success"])
                        self._refresh()
                        self.after(1500, modal.destroy)
                    else:
                        messagebox.showerror("Git Error", f"Push gagal:\n{err}", parent=modal)

                self.after(0, finish)

            threading.Thread(target=task, daemon=True).start()

        save_btn = HoverButton(
            btn_frame, text="✔  Apply Changes",
            bg=C["accent"], fg=C["white"],
            hover_bg=C["accent2"], hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=18, pady=7,
            cursor="hand2", command=do_save
        )
        save_btn.pack(side="right", padx=(8,0))

        HoverButton(
            btn_frame, text="Batal",
            bg=C["card"], fg=C["text"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=FONT_BTN, relief="flat", padx=14, pady=7,
            cursor="hand2", command=modal.destroy
        ).pack(side="right")

    # ── CLEANUP ORPHANED FILES MODAL ──────────────────────────────────────────
    def _open_cleanup_modal(self):
        orphaned = get_orphaned_json_files()
        
        if not orphaned:
            messagebox.showinfo(
                "Cleanup",
                "✅ Tidak ada file yang orphaned (semua file sudah terdaftar di list_map.json)"
            )
            return
        
        modal = self._make_modal(f"🗑️  Cleanup Orphaned Files ({len(orphaned)})", width=560, height=520)
        body  = tk.Frame(modal, bg=C["surface"])
        body.pack(fill="both", expand=True, padx=28, pady=16)

        info_txt = f"File berikut tidak terdaftar di list_map.json dan dapat dihapus:\n\n"
        tk.Label(
            body, text=info_txt, bg=C["surface"], fg=C["subtext"],
            font=FONT_BODY, justify="left", wraplength=480
        ).pack(anchor="w", pady=(0, 12))

        # Listbox dengan file orphaned
        list_frame = tk.Frame(body, bg=C["input_bg"], relief="flat", 
                              highlightthickness=1, highlightbackground=C["border"])
        list_frame.pack(fill="both", expand=True, pady=(0, 12))

        listbox = tk.Listbox(
            list_frame, bg=C["input_bg"], fg=C["text"],
            font=FONT_MONO, relief="flat", borderwidth=0,
            selectmode="multiple", activestyle="none"
        )
        listbox.pack(side="left", fill="both", expand=True, padx=6, pady=6)

        # Scrollbar
        scrollbar = tk.Scrollbar(list_frame, bg=C["surface"], activebackground=C["accent"])
        scrollbar.pack(side="right", fill="y", padx=(0,6), pady=6)
        listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=listbox.yview)

        # Add items ke listbox
        for fname in orphaned:
            listbox.insert(tk.END, fname)
        
        # Default select semua
        listbox.select_set(0, tk.END)

        def do_cleanup():
            sel_indices = listbox.curselection()
            selected_files = [orphaned[i] for i in sel_indices]
            
            if not selected_files:
                messagebox.showwarning("Cleanup", "Tidak ada file yang dipilih!", parent=modal)
                return
            
            ok = messagebox.askyesno(
                "Konfirmasi",
                f"Yakin ingin menghapus {len(selected_files)} file?\n\n{chr(10).join(selected_files)}",
                icon="warning",
                parent=modal
            )
            
            if not ok:
                return
            
            cleanup_btn.config(state="disabled", text="Menghapus...")
            
            def task():
                deleted_files = []
                for fname in selected_files:
                    fpath = os.path.join(REPO_DIR, fname)
                    try:
                        os.remove(fpath)
                        deleted_files.append(fname)
                    except Exception as ex:
                        pass
                
                if deleted_files:
                    def log_cb(pct, msg):
                        pass
                    
                    ok, err = git_push_with_progress(
                        f"Cleanup orphaned files: {', '.join(deleted_files)[:40]}...",
                        deleted_files=deleted_files,
                        log_cb=log_cb
                    )
                    
                    def finish():
                        cleanup_btn.config(state="normal", text="Hapus")
                        if ok:
                            msg = f"✅ {len(deleted_files)} file berhasil dihapus dari repo!"
                            self._set_status(msg, C["success"])
                            self.after(1500, modal.destroy)
                            self._refresh()
                        else:
                            messagebox.showerror("Git Error", f"Push gagal:\n{err}", parent=modal)
                    
                    self.after(0, finish)
            
            threading.Thread(target=task, daemon=True).start()

        btn_frame = tk.Frame(body, bg=C["surface"])
        btn_frame.pack(side="bottom", fill="x", pady=(12,0))

        cleanup_btn = HoverButton(
            btn_frame, text="🗑️  Hapus",
            bg=C["danger"], fg=C["white"],
            hover_bg="#ef4444", hover_fg=C["white"],
            font=FONT_BTN, relief="flat", padx=18, pady=7,
            cursor="hand2", command=do_cleanup
        )
        cleanup_btn.pack(side="right", padx=(8,0))

        HoverButton(
            btn_frame, text="Batal",
            bg=C["card"], fg=C["text"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=FONT_BTN, relief="flat", padx=14, pady=7,
            cursor="hand2", command=modal.destroy
        ).pack(side="right")

    # ── APPLY CHANGES (global push) ────────────────────────────────────────────
    def _apply_changes(self):
        modal = self._make_modal("⬆ Apply Changes — Push ke GitHub", width=600, height=480)
        body  = tk.Frame(modal, bg=C["surface"])
        body.pack(fill="both", expand=True, padx=0)

        # ── Info Section ──
        info_frame = tk.Frame(body, bg=C["card2"], pady=18, padx=28)
        info_frame.pack(fill="x", pady=(0,2))

        tk.Label(
            info_frame,
            text="Push Perubahan ke GitHub",
            bg=C["card2"], fg=C["accent2"],
            font=("Consolas", 14, "bold")
        ).pack(anchor="w", pady=(0,8))

        desc_frame = tk.Frame(info_frame, bg=C["card2"])
        desc_frame.pack(fill="x")

        tk.Label(
            desc_frame, text="📋", bg=C["card2"], fg=C["accent"],
            font=("Consolas", 12)
        ).pack(side="left", padx=(0,8))

        tk.Label(
            desc_frame,
            text="Sinkronisasi list_map.json & perubahan file ke repository.\nPastikan commit message jelas & deskriptif.",
            bg=C["card2"], fg=C["subtext"],
            font=FONT_SMALL, justify="left"
        ).pack(side="left", fill="x", expand=True)

        # ── Main Content ──
        content = tk.Frame(body, bg=C["surface"])
        content.pack(fill="both", expand=True, padx=28, pady=20)

        # Message input section
        tk.Label(
            content, text="Pesan Commit", bg=C["surface"], fg=C["accent2"],
            font=("Consolas", 11, "bold")
        ).pack(anchor="w", pady=(0,6))

        e_msg = RedEntry(content, placeholder="Deskripsi perubahan (contoh: Update maps v2)", width=54)
        e_msg.pack(fill="x", ipady=8)

        # Progress section (initially hidden)
        prog_frame = tk.Frame(content, bg=C["surface"])
        prog_frame.pack(fill="x", pady=(20,0))

        prog_label = tk.Label(prog_frame, text="Status Push", bg=C["surface"],
                              fg=C["accent2"], font=("Consolas", 11, "bold"))

        prog_bar_container = tk.Frame(prog_frame, bg=C["input_bg"], 
                                     highlightthickness=1, highlightbackground=C["border"],
                                     relief="flat")

        prog_bar = ttk.Progressbar(prog_bar_container, length=520, mode="determinate",
                                   style="red.Horizontal.TProgressbar")

        prog_log = tk.Label(prog_frame, text="", bg=C["surface"], fg=C["subtext"],
                           font=FONT_SMALL, wraplength=520, justify="left")

        # ── Button Frame ──
        btn_frame = tk.Frame(body, bg=C["surface"])
        btn_frame.pack(side="bottom", fill="x", padx=28, pady=16)

        # Separator line
        tk.Frame(btn_frame, bg=C["border"], height=1).pack(fill="x", pady=(0,14))

        def do_push():
            msg = e_msg.get_real().strip() or "Update list_map.json"
            
            # Show progress UI
            prog_label.pack(anchor="w", pady=(0,6))
            prog_bar_container.pack(fill="x")
            prog_bar.pack(fill="both", expand=True, padx=8, pady=8)
            prog_log.pack(anchor="w", pady=(8,0))
            
            push_btn.config(state="disabled", text="⬆  Pushing...", fg=C["dim"])

            def log_cb(pct, txt):
                def _upd():
                    if pct >= 0:
                        prog_bar["value"] = pct
                    
                    color = C["success"] if pct == 100 else (C["danger"] if pct < 0 else C["warning"])
                    prog_log.config(text=txt, fg=color)
                self.after(0, _upd)

            def task():
                save_data(self.data)
                ok, err = git_push_with_progress(msg, log_cb=log_cb)
                def finish():
                    if ok:
                        push_btn.config(state="normal", text="✅ Push Berhasil!", 
                                      fg=C["success"], bg=C["glow"])
                        self._set_status("✅ Push berhasil! Perubahan sudah live di GitHub.", C["success"])
                        self.after(2500, modal.destroy)
                    else:
                        push_btn.config(state="normal", text="⬆  Push", fg=C["white"])
                        messagebox.showerror("Git Error", f"Push gagal:\n{err}", parent=modal)
                self.after(0, finish)

            threading.Thread(target=task, daemon=True).start()

        push_btn = HoverButton(
            btn_frame, text="⬆  Push Sekarang",
            bg=C["glow"], fg=C["white"],
            hover_bg=C["accent2"], hover_fg=C["white"],
            font=("Consolas", 11, "bold"), relief="flat", padx=24, pady=9,
            cursor="hand2", command=do_push
        )
        push_btn.pack(side="right", padx=(12,0))

        HoverButton(
            btn_frame, text="Batal",
            bg=C["card"], fg=C["text"],
            hover_bg=C["card2"], hover_fg=C["text"],
            font=("Consolas", 11, "bold"), relief="flat", padx=20, pady=9,
            cursor="hand2", command=modal.destroy
        ).pack(side="right")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Try tkinterdnd2 for drag-drop support
    try:
        from tkinterdnd2 import TkinterDnD
        class App(TkinterDnD.Tk, RullzsyHUB):
            def __init__(self):
                TkinterDnD.Tk.__init__(self)
                RullzsyHUB.__init__(self)
        app = App()
    except ImportError:
        app = RullzsyHUB()

    app.mainloop()
