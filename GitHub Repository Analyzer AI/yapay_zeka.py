import os
import ast
import json
import tkinter as tk
from tkinter import ttk, messagebox
import requests
import base64
import joblib
import re

# Makine Öğrenmesi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
import pandas as pd
import numpy as np
import sys

# --- EXE GÖMÜLÜ DOSYA YOLU AYARI ---
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# --- CONFIG / AYARLAR ---
GITHUB_TOKEN = "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"
MODEL_FILE = resource_path("saved_svm_model.pkl")
VECTORIZER_FILE = resource_path("saved_vectorizer.pkl")

ALLOWED_EXTENSIONS = ('.py', '.js', '.ts', '.java', '.cs', '.cpp', '.c', '.html', '.css', '.md', '.go', '.php')

# ─── RENK PALETİ ────────────────────────────────────────────────
BG_DARK      = "#1E2A3B"
BG_PANEL     = "#253347"
BG_CARD      = "#2E4060"
BG_INPUT     = "#243148"
ACCENT_BLUE  = "#4A9EFF"
ACCENT_CYAN  = "#22D3EE"
ACCENT_GREEN = "#34D399"
ACCENT_AMBER = "#FBBF24"
ACCENT_RED   = "#F87171"
TEXT_PRIMARY = "#EEF4FF"
TEXT_MUTED   = "#8BAAC8"
TEXT_DIM     = "#C0D4F0"
BORDER       = "#3A5070"

FONT_HEADING = ("Consolas", 13, "bold")
FONT_BODY    = ("Consolas", 12)
FONT_SMALL   = ("Consolas", 11)
FONT_MINI    = ("Consolas", 10)
FONT_SCORE   = ("Consolas", 44, "bold")

LEFT_W = 220


class AIAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI Code Intelligence")
        self.root.configure(bg=BG_DARK)
        self.root.resizable(True, True)

        self.root.overrideredirect(True)
        self.root.update_idletasks()
        W, H = 1080, 840
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        self.root.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

        self._drag_x = 0
        self._drag_y = 0
        self._is_maximized = False
        self.model = None
        self.vectorizer = None

        self._build_ui()
        self.root.after(120, self.check_or_train_model)

    # ═══════════════════════════════════════════════════════
    #  UI BUILDER
    # ═══════════════════════════════════════════════════════
    def _build_ui(self):
        # ── ÖZEL HEADER BAR ─────────────────────────────────
        header = tk.Frame(self.root, bg=BG_PANEL, height=58)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        header.bind("<ButtonPress-1>", self._drag_start)
        header.bind("<B1-Motion>",     self._drag_motion)

        tk.Frame(self.root, bg=ACCENT_BLUE, height=2).pack(fill=tk.X)

        # Sol: logo + başlık
        left_h = tk.Frame(header, bg=BG_PANEL)
        left_h.pack(side=tk.LEFT, padx=18, pady=8)
        left_h.bind("<ButtonPress-1>", self._drag_start)
        left_h.bind("<B1-Motion>",     self._drag_motion)

        tk.Label(left_h, text="⬡", font=("Consolas", 20, "bold"),
                 fg=ACCENT_CYAN, bg=BG_PANEL).pack(side=tk.LEFT, padx=(0, 8))
        stack = tk.Frame(left_h, bg=BG_PANEL)
        stack.pack(side=tk.LEFT)
        tk.Label(stack, text="AI Code Intelligence",
                 font=("Consolas", 14, "bold"), fg=TEXT_PRIMARY, bg=BG_PANEL).pack(anchor="w")
        tk.Label(stack, text="Yazılım Kalite Analiz Sistemi",
                 font=FONT_MINI, fg=TEXT_MUTED, bg=BG_PANEL).pack(anchor="w")

        # Sağ: durum + pencere kontrolleri
        right_h = tk.Frame(header, bg=BG_PANEL)
        right_h.pack(side=tk.RIGHT, padx=12)

        # Kapat
        btn_close = tk.Label(right_h, text=" ✕ ", font=("Consolas", 13, "bold"),
                             fg=TEXT_MUTED, bg=BG_PANEL, cursor="hand2")
        btn_close.pack(side=tk.RIGHT, padx=(4, 2))
        btn_close.bind("<Button-1>", lambda e: self.root.destroy())
        btn_close.bind("<Enter>",    lambda e: btn_close.config(fg=ACCENT_RED, bg="#3D1A1A"))
        btn_close.bind("<Leave>",    lambda e: btn_close.config(fg=TEXT_MUTED, bg=BG_PANEL))

        # Büyüt
        btn_max = tk.Label(right_h, text=" ▢ ", font=("Consolas", 13, "bold"),
                           fg=TEXT_MUTED, bg=BG_PANEL, cursor="hand2")
        btn_max.pack(side=tk.RIGHT, padx=(2, 2))
        btn_max.bind("<Button-1>", lambda e: self._maximize())
        btn_max.bind("<Enter>",    lambda e: btn_max.config(fg=ACCENT_GREEN))
        btn_max.bind("<Leave>",    lambda e: btn_max.config(fg=TEXT_MUTED))

        # Küçült
        btn_min = tk.Label(right_h, text=" — ", font=("Consolas", 13, "bold"),
                           fg=TEXT_MUTED, bg=BG_PANEL, cursor="hand2")
        btn_min.pack(side=tk.RIGHT, padx=(2, 4))
        btn_min.bind("<Button-1>", lambda e: self._minimize())
        btn_min.bind("<Enter>",    lambda e: btn_min.config(fg=ACCENT_AMBER))
        btn_min.bind("<Leave>",    lambda e: btn_min.config(fg=TEXT_MUTED))

        # Durum badge
        badge = tk.Frame(right_h, bg=BG_PANEL)
        badge.pack(side=tk.RIGHT, padx=14)
        self.badge_dot = tk.Label(badge, text="●", font=FONT_MINI,
                                  fg=ACCENT_AMBER, bg=BG_PANEL)
        self.badge_dot.pack(side=tk.LEFT, padx=(0, 5))
        self.lbl_status = tk.Label(badge, text="Model kontrol ediliyor...",
                                   font=FONT_MINI, fg=TEXT_DIM, bg=BG_PANEL)
        self.lbl_status.pack(side=tk.LEFT)

        # ── ANA İÇERİK ──────────────────────────────────────
        main = tk.Frame(self.root, bg=BG_DARK)
        main.pack(fill=tk.BOTH, expand=True, padx=18, pady=14)

        left_col = tk.Frame(main, bg=BG_DARK, width=LEFT_W)
        left_col.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 14))
        left_col.pack_propagate(False)

        self._build_score_card(left_col)
        self._build_stats_panel(left_col)

        right_col = tk.Frame(main, bg=BG_DARK)
        right_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self._build_input_card(right_col)
        self._build_report_card(right_col)

        # ── FOOTER ──────────────────────────────────────────
        footer = tk.Frame(self.root, bg=BG_PANEL, height=28)
        footer.pack(fill=tk.X, side=tk.BOTTOM)
        footer.pack_propagate(False)
        tk.Label(footer, text="SVM + TF-IDF  •  Çok Dilli Analiz  •  GitHub API v3",
                 font=FONT_MINI, fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.LEFT, padx=14, pady=5)
        tk.Label(footer, text="© 2025 AI Code Intelligence",
                 font=FONT_MINI, fg=TEXT_MUTED, bg=BG_PANEL).pack(side=tk.RIGHT, padx=14)

    # ── PENCERE KONTROL ─────────────────────────────────────
    def _drag_start(self, e):
        self._drag_x = e.x_root - self.root.winfo_x()
        self._drag_y = e.y_root - self.root.winfo_y()

    def _drag_motion(self, e):
        self.root.geometry(f"+{e.x_root - self._drag_x}+{e.y_root - self._drag_y}")

    def _minimize(self):
        self.root.overrideredirect(False)
        self.root.iconify()
        self.root.bind("<Map>", lambda e: (self.root.overrideredirect(True),
                                           self.root.bind("<Map>", "")))

    def _maximize(self):
        self._is_maximized = not self._is_maximized
        if self._is_maximized:
            self.root.geometry(f"{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0")
        else:
            W, H = 1080, 840
            sw = self.root.winfo_screenwidth()
            sh = self.root.winfo_screenheight()
            self.root.geometry(f"{W}x{H}+{(sw - W) // 2}+{(sh - H) // 2}")

    # ── SKOR KARTI ──────────────────────────────────────────
    def _build_score_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill=tk.X, pady=(0, 10))
        tk.Frame(card, bg=ACCENT_CYAN, height=3).pack(fill=tk.X)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(padx=16, pady=16, fill=tk.X)

        tk.Label(inner, text="MÜHENDİSLİK PUANI",
                 font=("Consolas", 9, "bold"), fg=TEXT_MUTED, bg=BG_CARD).pack()

        self.lbl_score = tk.Label(inner, text="--",
                                  font=FONT_SCORE, fg=TEXT_MUTED, bg=BG_CARD)
        self.lbl_score.pack(pady=(4, 0))

        tk.Label(inner, text="/ 100", font=("Consolas", 12), fg=TEXT_MUTED, bg=BG_CARD).pack()

        bar_w = LEFT_W - 32
        self.canvas_bar = tk.Canvas(inner, width=bar_w, height=10,
                                    bg=BG_INPUT, bd=0, highlightthickness=0)
        self.canvas_bar.pack(pady=(12, 2))
        self.canvas_bar.create_rectangle(0, 0, bar_w, 10, fill=BG_INPUT, outline="")
        self.bar_fg = self.canvas_bar.create_rectangle(0, 0, 0, 10, fill=ACCENT_BLUE, outline="")
        self._bar_w = bar_w

    # ── İSTATİSTİK PANELİ ───────────────────────────────────
    def _build_stats_panel(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill=tk.X, pady=(0, 10))
        tk.Frame(card, bg=ACCENT_BLUE, height=3).pack(fill=tk.X)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(padx=16, pady=14, fill=tk.X)

        tk.Label(inner, text="KOD BLOK ANALİZİ",
                 font=("Consolas", 9, "bold"), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w")
        tk.Frame(inner, bg=BORDER, height=1).pack(fill=tk.X, pady=8)

        self.stat_vars = {}
        stats = [
            ("İYİ",    "✦", ACCENT_GREEN, "iyi"),
            ("ORTA",   "◈", ACCENT_AMBER, "orta"),
            ("ZAYIF",  "◆", ACCENT_RED,   "kotu"),
            ("TOPLAM", "▸", ACCENT_CYAN,  "total"),
        ]
        for label, icon, color, key in stats:
            row = tk.Frame(inner, bg=BG_CARD)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=f"{icon}  {label}", font=FONT_SMALL,
                     fg=color, bg=BG_CARD).pack(side=tk.LEFT)
            var = tk.StringVar(value="—")
            self.stat_vars[key] = var
            tk.Label(row, textvariable=var, font=FONT_HEADING,
                     fg=TEXT_PRIMARY, bg=BG_CARD).pack(side=tk.RIGHT)

        tk.Frame(inner, bg=BORDER, height=1).pack(fill=tk.X, pady=(12, 6))
        self.readme_var = tk.StringVar(value="—")
        self.test_var   = tk.StringVar(value="—")
        for label, var in [("README", self.readme_var), ("TESTLER", self.test_var)]:
            row = tk.Frame(inner, bg=BG_CARD)
            row.pack(fill=tk.X, pady=4)
            tk.Label(row, text=label, font=FONT_SMALL, fg=TEXT_MUTED, bg=BG_CARD).pack(side=tk.LEFT)
            tk.Label(row, textvariable=var, font=FONT_HEADING,
                     fg=TEXT_PRIMARY, bg=BG_CARD).pack(side=tk.RIGHT)

    # ── GİRİŞ KARTI ─────────────────────────────────────────
    def _build_input_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill=tk.X, pady=(0, 12))
        tk.Frame(card, bg=ACCENT_CYAN, height=3).pack(fill=tk.X)

        inner = tk.Frame(card, bg=BG_CARD)
        inner.pack(padx=16, pady=14, fill=tk.X)

        tk.Label(inner, text="REPO URL", font=("Consolas", 9, "bold"),
                 fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", pady=(0, 7))

        entry_row = tk.Frame(inner, bg=BG_INPUT)
        entry_row.pack(fill=tk.X)

        tk.Label(entry_row, text=" ⌥ ", font=("Consolas", 13),
                 fg=ACCENT_BLUE, bg=BG_INPUT).pack(side=tk.LEFT)

        self.ent_repo_url = tk.Entry(
            entry_row, font=FONT_BODY,
            bg=BG_INPUT, fg=TEXT_PRIMARY,
            insertbackground=ACCENT_CYAN,
            relief=tk.FLAT, bd=0
        )
        self.ent_repo_url.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=9)
        self.ent_repo_url.insert(0, "https://github.com/kullanici/repo-adi")
        self.ent_repo_url.bind("<FocusIn>",  self._on_entry_focus)
        self.ent_repo_url.bind("<FocusOut>", self._on_entry_blur)

        self.btn_analyze = tk.Button(
            entry_row,
            text="  ANALİZ ET  →  ",
            font=("Consolas", 11, "bold"),
            bg=ACCENT_BLUE, fg="#0A1828",
            activebackground=ACCENT_CYAN, activeforeground="#0A1828",
            relief=tk.FLAT, bd=0, pady=9,
            cursor="hand2",
            state=tk.DISABLED,
            command=self.start_analysis
        )
        self.btn_analyze.pack(side=tk.RIGHT)
        self.btn_analyze.bind("<Enter>", lambda e: self.btn_analyze.config(bg=ACCENT_CYAN) if str(self.btn_analyze["state"]) != "disabled" else None)
        self.btn_analyze.bind("<Leave>", lambda e: self.btn_analyze.config(bg=ACCENT_BLUE)  if str(self.btn_analyze["state"]) != "disabled" else None)

        tk.Frame(inner, bg=BORDER, height=1).pack(fill=tk.X, pady=(8, 0))

    def _on_entry_focus(self, e):
        if self.ent_repo_url.get() == "https://github.com/kullanici/repo-adi":
            self.ent_repo_url.delete(0, tk.END)

    def _on_entry_blur(self, e):
        if not self.ent_repo_url.get().strip():
            self.ent_repo_url.insert(0, "https://github.com/kullanici/repo-adi")

    # ── RAPOR KARTI ─────────────────────────────────────────
    def _build_report_card(self, parent):
        card = tk.Frame(parent, bg=BG_CARD)
        card.pack(fill=tk.BOTH, expand=True)
        tk.Frame(card, bg=ACCENT_GREEN, height=3).pack(fill=tk.X)

        hrow = tk.Frame(card, bg=BG_CARD)
        hrow.pack(fill=tk.X, padx=16, pady=(10, 0))
        tk.Label(hrow, text="CANLI ANALİZ ÇIKTISI",
                 font=("Consolas", 9, "bold"), fg=TEXT_MUTED, bg=BG_CARD).pack(side=tk.LEFT)

        txt_frame = tk.Frame(card, bg=BG_CARD)
        txt_frame.pack(fill=tk.BOTH, expand=True, padx=16, pady=(8, 14))

        self.txt_report = tk.Text(
            txt_frame,
            bg=BG_INPUT, fg=TEXT_DIM,
            font=FONT_BODY,
            insertbackground=ACCENT_CYAN,
            relief=tk.FLAT, bd=0,
            wrap=tk.WORD,
            padx=14, pady=12,
            selectbackground=ACCENT_BLUE,
            selectforeground=TEXT_PRIMARY,
            spacing1=3, spacing3=3
        )
        self.txt_report.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        sb = tk.Scrollbar(txt_frame, orient=tk.VERTICAL, command=self.txt_report.yview,
                          bg=BG_CARD, troughcolor=BG_INPUT, width=7, bd=0, relief=tk.FLAT)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.txt_report.configure(yscrollcommand=sb.set)

        self.txt_report.tag_configure("cyan",   foreground=ACCENT_CYAN)
        self.txt_report.tag_configure("green",  foreground=ACCENT_GREEN)
        self.txt_report.tag_configure("amber",  foreground=ACCENT_AMBER)
        self.txt_report.tag_configure("red",    foreground=ACCENT_RED)
        self.txt_report.tag_configure("blue",   foreground=ACCENT_BLUE)
        self.txt_report.tag_configure("muted",  foreground=TEXT_MUTED)
        self.txt_report.tag_configure("bold",   font=("Consolas", 12, "bold"), foreground=TEXT_PRIMARY)
        self.txt_report.tag_configure("header", font=("Consolas", 13, "bold"), foreground=ACCENT_CYAN)

        self._append_log("Sistem başlatılıyor... Yapay zeka modeli kontrol ediliyor.\n", "muted")

    # ═══════════════════════════════════════════════════════
    #  YARDIMCI UI METHODLARı
    # ═══════════════════════════════════════════════════════
    def _append_log(self, msg, tag=None):
        self.txt_report.config(state=tk.NORMAL)
        if tag:
            self.txt_report.insert(tk.END, msg + "\n", tag)
        else:
            self.txt_report.insert(tk.END, msg + "\n")
        self.txt_report.see(tk.END)
        self.txt_report.config(state=tk.DISABLED)
        self.root.update()

    def log_to_ui(self, message):
        tag = None
        if message.startswith("[-]"):
            tag = "cyan"
        elif message.startswith("[!]"):
            tag = "amber"
        elif message.startswith("   ->"):
            tag = "muted"
        self._append_log(message, tag)

    def _set_status(self, text, color=ACCENT_AMBER):
        self.lbl_status.config(text=text, fg=color)
        self.badge_dot.config(fg=color)

    def _update_score(self, puan):
        color = ACCENT_GREEN if puan >= 75 else (ACCENT_AMBER if puan >= 50 else ACCENT_RED)
        self.lbl_score.config(text=str(int(puan)), fg=color)
        width = int(self._bar_w * (puan / 100))
        self.canvas_bar.coords(self.bar_fg, 0, 0, width, 10)
        self.canvas_bar.itemconfig(self.bar_fg, fill=color)

    def _update_stats(self, iyi, orta, kotu, total, has_readme, has_tests):
        self.stat_vars["iyi"].set(str(iyi))
        self.stat_vars["orta"].set(str(orta))
        self.stat_vars["kotu"].set(str(kotu))
        self.stat_vars["total"].set(str(total))
        self.readme_var.set("✔ Var" if has_readme else "✘ Yok")
        self.test_var.set("✔ Var"   if has_tests  else "✘ Yok")

    # ═══════════════════════════════════════════════════════
    #  MODEL EĞİTİM / YÜKLEME  (DEĞİŞTİRİLMEDİ)
    # ═══════════════════════════════════════════════════════
    def check_or_train_model(self):
        if os.path.exists(MODEL_FILE) and os.path.exists(VECTORIZER_FILE):
            self._set_status("Model yüklendi — Analize hazır", ACCENT_GREEN)
            self.model = joblib.load(MODEL_FILE)
            self.vectorizer = joblib.load(VECTORIZER_FILE)
            self.btn_analyze.config(state=tk.NORMAL, bg=ACCENT_BLUE)
            self._append_log("✔ Yapay zeka modeli başarıyla yüklendi. Repo linki girerek analizi başlatabilirsiniz.\n", "green")
        else:
            self._set_status("Model eğitiliyor...", ACCENT_AMBER)
            self._append_log("[-] Model bulunamadı, eğitim başlıyor (yalnızca ilk açılışta)...", "cyan")
            self.root.update()

            all_data = []
            files = {"devasa_github_dataset.json": 2, "orta_github_dataset.json": 1, "kotu_github_dataset.json": 0}

            for filename, label in files.items():
                if os.path.exists(filename):
                    with open(filename, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        for item in data:
                            if "code" in item:
                                all_data.append({"code": item["code"], "label": label})

            if len(all_data) == 0:
                messagebox.showerror("Hata", "Model dosyaları bulunamadı! JSON veri setlerini kodla yan yana koyun.")
                return

            df = pd.DataFrame(all_data)
            self.vectorizer = TfidfVectorizer(max_features=2500)
            X = self.vectorizer.fit_transform(df['code'])
            y = df['label'].values

            base_svm = LinearSVC(class_weight="balanced", dual=False, random_state=42)
            self.model = CalibratedClassifierCV(base_svm)
            self.model.fit(X, y)

            joblib.dump(self.model, MODEL_FILE)
            joblib.dump(self.vectorizer, VECTORIZER_FILE)

            self._set_status("Model eğitildi — Analize hazır", ACCENT_GREEN)
            self.btn_analyze.config(state=tk.NORMAL, bg=ACCENT_BLUE)
            self._append_log("✔ Yapay zeka başarıyla eğitildi ve kaydedildi!\n", "green")

    # ═══════════════════════════════════════════════════════
    #  REPO VERİ ÇEKME (DEĞİŞTİRİLMEDİ)
    # ═══════════════════════════════════════════════════════
    def extract_generic_code_blocks(self, code_text):
        blocks = []
        lines = code_text.split("\n")
        current_block = []

        for line in lines:
            current_block.append(line)
            if len("\n".join(current_block)) > 300 or (line.strip() == "}" and len(current_block) > 5):
                blocks.append("\n".join(current_block).strip())
                current_block = []

        if current_block and len("\n".join(current_block).strip()) > 50:
            blocks.append("\n".join(current_block).strip())

        return [b for b in blocks if len(b) > 40]

    def fetch_repo_data(self, repo_url):
        headers = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN != "BURAYA_GITHUB_TOKENUNUZU_YAZIN" and GITHUB_TOKEN.startswith("ghp_") else {}

        parts = repo_url.replace("https://github.com/", "").strip("/").split("/")
        if len(parts) < 2:
            return None, False, False, {}

        owner, repo_name = parts[0], parts[1]
        api_url = f"https://api.github.com/repos/{owner}/{repo_name}"

        has_readme = False
        try:
            readme_res = requests.get(f"{api_url}/readme", headers=headers, timeout=5)
            if readme_res.status_code == 200:
                has_readme = True
        except Exception:
            pass

        blocks_found = []
        has_tests = False
        languages_detected = {}

        try:
            self.log_to_ui("[-] Repo commit geçmişi sorgulanıyor...")
            commits_res = requests.get(f"{api_url}/commits", headers=headers, timeout=5).json()
            if not isinstance(commits_res, list) or len(commits_res) == 0:
                return None, has_readme, has_tests, languages_detected

            sha = commits_res[0]["sha"]
            self.log_to_ui("[-] Repo dosya ağacı indiriliyor...")
            tree_res = requests.get(f"{api_url}/git/trees/{sha}?recursive=1", headers=headers, timeout=6).json()

            if "tree" in tree_res:
                valid_files = [
                    item for item in tree_res["tree"]
                    if item["path"].lower().endswith(ALLOWED_EXTENSIONS) and not any(x in item["path"].lower() for x in ["venv", "env", "node_modules", ".github", "dist", "build"])
                ]

                self.log_to_ui(f"[-] Toplam {len(valid_files)} adet kaynak kod/döküman dosyası algılandı, analiz başlıyor...")

                for item in valid_files:
                    path = item["path"]
                    _, ext = os.path.splitext(path.lower())
                    languages_detected[ext] = languages_detected.get(ext, 0) + 1

                    if "test" in path.lower() or "spec" in path.lower():
                        has_tests = True

                    try:
                        blob_res = requests.get(item["url"], headers=headers, timeout=4).json()
                        if "content" in blob_res:
                            code_text = base64.b64decode(blob_res["content"]).decode('utf-8', errors='ignore')

                            file_blocks_count = 0
                            if ext == ".py":
                                try:
                                    tree = ast.parse(code_text)
                                    for node in ast.walk(tree):
                                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                            func_code = ast.unparse(node)
                                            if len(func_code) > 40:
                                                blocks_found.append(func_code)
                                                file_blocks_count += 1
                                except Exception:
                                    generic_b = self.extract_generic_code_blocks(code_text)
                                    blocks_found.extend(generic_b)
                                    file_blocks_count += len(generic_b)
                            else:
                                generic_b = self.extract_generic_code_blocks(code_text)
                                blocks_found.extend(generic_b)
                                file_blocks_count += len(generic_b)

                            if file_blocks_count > 0:
                                self.log_to_ui(f"   -> {os.path.basename(path)} ({file_blocks_count} segment)")
                    except Exception:
                        continue
        except Exception as e:
            self.log_to_ui(f"[!] Bağlantı veya işleme hatası: {str(e)}")

        return blocks_found, has_readme, has_tests, languages_detected

    # ═══════════════════════════════════════════════════════
    #  ANALİZ BAŞLAT  (DEĞİŞTİRİLMEDİ)
    # ═══════════════════════════════════════════════════════
    def start_analysis(self):
        url = self.ent_repo_url.get().strip()
        if "github.com" not in url:
            messagebox.showwarning("Geçersiz URL", "Lütfen geçerli bir tam GitHub repo adresi girin.")
            return

        self._set_status("Çok dilli repo analizi yürütülüyor...", ACCENT_CYAN)
        self.txt_report.config(state=tk.NORMAL)
        self.txt_report.delete(1.0, tk.END)
        self.txt_report.config(state=tk.DISABLED)
        self.lbl_score.config(text="--", fg=TEXT_MUTED)
        self.canvas_bar.coords(self.bar_fg, 0, 0, 0, 10)
        for k in self.stat_vars:
            self.stat_vars[k].set("—")
        self.readme_var.set("—")
        self.test_var.set("—")
        self.root.update()

        functions, has_readme, has_tests, languages = self.fetch_repo_data(url)

        if functions is None or len(functions) == 0:
            self._set_status("Analiz başarısız.", ACCENT_RED)
            self._append_log("\n[HATA] Repoda analiz edilebilecek düzeyde kod/metin dosyası bulunamadı.", "red")
            return

        X_input = self.vectorizer.transform(functions)
        predictions = self.model.predict(X_input)

        total_func = len(predictions)
        iyi_count  = int(np.sum(predictions == 2))
        orta_count = int(np.sum(predictions == 1))
        kotu_count = int(np.sum(predictions == 0))

        base_code_score = ((iyi_count * 100) + (orta_count * 50)) / total_func
        puan = base_code_score
        rapor_onerileri = []

        if has_readme:
            puan += 5
        else:
            puan -= 15
            rapor_onerileri.append(("KRİTİK", "README dökümantasyonu bulunamadı. Projeyi profesyonel göstermek için mutlaka README.md ekleyin.", "red"))

        if has_tests:
            puan += 5
        else:
            rapor_onerileri.append(("MİMARİ", "Test/spec dosyası tespit edilemedi. Proje kalitesi için test senaryoları eklenmelidir.", "amber"))

        kotu_oran = (kotu_count / total_func) * 100
        if kotu_oran > 35:
            puan -= 10
            rapor_onerileri.append(("KOD KALİTESİ", f"Kod bloklarının %{kotu_oran:.1f}'i zayıf standartta. Refactoring önerilir.", "amber"))

        puan = max(0, min(100, puan))

        self._update_score(puan)
        self._update_stats(iyi_count, orta_count, kotu_count, total_func, has_readme, has_tests)

        lang_summary = "  ".join([f"{k}({v})" for k, v in languages.items()])

        self.txt_report.config(state=tk.NORMAL)
        self.txt_report.delete(1.0, tk.END)

        self.txt_report.insert(tk.END, "═" * 48 + "\n", "muted")
        self.txt_report.insert(tk.END, "  YAPAY ZEKA KOD KALİTE ANALİZ RAPORU\n", "header")
        self.txt_report.insert(tk.END, "═" * 48 + "\n\n", "muted")

        self.txt_report.insert(tk.END, "  DOSYA TÜRLERİ\n", "bold")
        self.txt_report.insert(tk.END, f"  {lang_summary}\n\n", "cyan")

        self.txt_report.insert(tk.END, "  BLOK DAĞILIMI\n", "bold")
        self.txt_report.insert(tk.END, f"  ✦  Başarılı / Kusursuz    : {iyi_count}\n",  "green")
        self.txt_report.insert(tk.END, f"  ◈  Endüstriyel (Orta)    : {orta_count}\n", "amber")
        self.txt_report.insert(tk.END, f"  ◆  Geliştirilmeli (Zayıf): {kotu_count}\n", "red")
        self.txt_report.insert(tk.END, f"  ▸  Toplam                : {total_func}\n\n")

        self.txt_report.insert(tk.END, "─" * 48 + "\n", "muted")
        self.txt_report.insert(tk.END, "  YAPAY ZEKA TAVSİYELERİ\n\n", "bold")

        if not rapor_onerileri:
            self.txt_report.insert(tk.END,
                "  ✔  Harika! Yapay zekamız herhangi bir majör yapısal\n"
                "     eksiklik tespit etmedi. Temiz mühendislik!\n", "green")
        else:
            for seviye, mesaj, tag in rapor_onerileri:
                self.txt_report.insert(tk.END, f"\n  [ {seviye} ]\n", tag)
                self.txt_report.insert(tk.END, f"  {mesaj}\n")

        self.txt_report.insert(tk.END, "\n" + "─" * 48 + "\n", "muted")
        self.txt_report.see(tk.END)
        self.txt_report.config(state=tk.DISABLED)

        self._set_status("Çok dilli analiz başarıyla tamamlandı!", ACCENT_GREEN)


if __name__ == "__main__":
    root = tk.Tk()
    app = AIAnalyzerApp(root)
    root.mainloop()