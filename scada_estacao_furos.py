"""
SCADA - Estação de Furação FESTO (Indústria 4.0)
Laboratório ECAA02A - UNIFEI
Com Login, Perfis, Tema Claro/Escuro e Logout
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import time
import math

try:
    from PIL import Image, ImageTk, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


# ============================================================
# USUÁRIOS E AVATARES
# ============================================================
USERS = {
    "Igor":    {"password": "123", "color": "#61afef"},
    "Thiago":  {"password": "123", "color": "#98c379"},
    "Luiz":    {"password": "123", "color": "#e5c07b"},
    "Lenarth": {"password": "123", "color": "#c678dd"},
}
AVATAR_PATHS = {user: None for user in USERS}


def make_avatar_image(username, size=48, image_path=None, dark_mode=True):
    if not PIL_AVAILABLE:
        return None
    bg = (30, 30, 36) if dark_mode else (240, 240, 245)
    try:
        if image_path:
            img = Image.open(image_path).convert("RGB")
            img = img.resize((size, size), Image.LANCZOS)
            mask = Image.new("L", (size, size), 0)
            ImageDraw.Draw(mask).ellipse((0, 0, size - 1, size - 1), fill=255)
            out = Image.new("RGB", (size, size), bg)
            out.paste(img, (0, 0), mask)
            return ImageTk.PhotoImage(out)
    except Exception:
        pass
    img = Image.new("RGB", (size, size), bg)
    draw = ImageDraw.Draw(img)
    color = USERS.get(username, {}).get("color", "#61afef")
    draw.ellipse((0, 0, size - 1, size - 1), fill=color)
    initial = username[0].upper() if username else "?"
    try:
        font = ImageFont.truetype("arial.ttf", int(size * 0.5))
        bbox = draw.textbbox((0, 0), initial, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.text(((size - tw) / 2 - bbox[0], (size - th) / 2 - bbox[1]),
                  initial, fill="white", font=font)
    except Exception:
        draw.text((size * 0.35, size * 0.2), initial, fill="white")
    return ImageTk.PhotoImage(img)


# ============================================================
# PALETAS DE TEMA
# ============================================================
THEMES = {
    "dark": {
        "bg_root": "#1e1e24", "bg_header": "#18181f",
        "bg_panel": "#23232c", "bg_panel_alt": "#202029",
        "bg_canvas": "#1a1a22", "bg_input": "#181820",
        "bg_card_ok": "#1d2d25", "bg_card_nok": "#331e21",
        "bg_card_rate": "#1e2638",
        "fg_primary": "#ffffff", "fg_secondary": "#abb2bf",
        "fg_dim": "#828997", "fg_muted": "#5c6370",
        "accent_blue": "#61afef", "accent_green": "#98c379",
        "accent_yellow": "#e5c07b", "accent_orange": "#d19a66",
        "accent_red": "#e06c75", "accent_purple": "#c678dd",
        "grid_line": "#1f1f2e", "border": "#3c3f50",
        "canvas_bg": "#181822", "canvas_inner": "#22242e",
        "btn_secondary": "#3b4048", "btn_secondary_active": "#4e5560",
    },
    "light": {
        "bg_root": "#f0f0f5", "bg_header": "#e4e4ec",
        "bg_panel": "#ffffff", "bg_panel_alt": "#f5f5fa",
        "bg_canvas": "#f8f8fc", "bg_input": "#ffffff",
        "bg_card_ok": "#e6f5eb", "bg_card_nok": "#fce8ea",
        "bg_card_rate": "#e6f0fa",
        "fg_primary": "#1e1e24", "fg_secondary": "#4b5263",
        "fg_dim": "#6c7080", "fg_muted": "#8c909c",
        "accent_blue": "#2c6db5", "accent_green": "#2f8a42",
        "accent_yellow": "#b8860b", "accent_orange": "#b8692a",
        "accent_red": "#c0392b", "accent_purple": "#8e44ad",
        "grid_line": "#e8e8ee", "border": "#c8c8d0",
        "canvas_bg": "#f5f5fa", "canvas_inner": "#e8e8ee",
        "btn_secondary": "#d0d0d8", "btn_secondary_active": "#c0c0c8",
    },
}


# ============================================================
# TELA DE LOGIN
# ============================================================
class LoginScreen:
    def __init__(self, root, on_login):
        self.root = root
        self.on_login = on_login
        self.container = tk.Frame(root, bg="#1e1e24")
        self.container.pack(fill=tk.BOTH, expand=True)
        self.avatar_refs = {}
        self.show_welcome()

    def _clear(self):
        for child in self.container.winfo_children():
            child.destroy()

    def show_welcome(self):
        self._clear()
        wrap = tk.Frame(self.container, bg="#1e1e24")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="⚙", font=("Segoe UI", 60),
                 fg="#61afef", bg="#1e1e24").pack()
        tk.Label(wrap, text="SCADA", font=("Segoe UI", 46, "bold"),
                 fg="#ffffff", bg="#1e1e24").pack()
        tk.Label(wrap, text="Estação de Furação FESTO",
                 font=("Segoe UI", 16), fg="#abb2bf", bg="#1e1e24").pack(pady=(0, 6))
        tk.Label(wrap, text="UNIFEI • ECAA02A • Indústria 4.0",
                 font=("Segoe UI", 10), fg="#5c6370", bg="#1e1e24").pack(pady=(0, 50))

        tk.Button(wrap, text="ENTRAR", font=("Segoe UI", 18, "bold"),
                  bg="#61afef", fg="#18181f", activebackground="#4a9de0",
                  activeforeground="#18181f", relief="flat",
                  padx=80, pady=16, cursor="hand2",
                  command=self.show_profiles).pack()

        tk.Label(wrap, text="Sistema Supervisório • Acesso Restrito",
                 font=("Segoe UI", 8), fg="#4b5263", bg="#1e1e24").pack(pady=(30, 0))

    def show_profiles(self):
        self._clear()
        wrap = tk.Frame(self.container, bg="#1e1e24")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrap, text="Selecione o Perfil", font=("Segoe UI", 24, "bold"),
                 fg="#ffffff", bg="#1e1e24").pack(pady=(0, 8))
        tk.Label(wrap, text="Clique no lápis ✏ para trocar a foto de perfil",
                 font=("Segoe UI", 9), fg="#828997", bg="#1e1e24").pack(pady=(0, 30))

        grid = tk.Frame(wrap, bg="#1e1e24")
        grid.pack()

        for i, username in enumerate(USERS.keys()):
            card = tk.Frame(grid, bg="#23232c", bd=1, relief="solid")
            card.grid(row=0, column=i, padx=10, pady=10, ipadx=14, ipady=16)

            # Container do avatar com overlay de lápis
            av_container = tk.Frame(card, bg="#23232c", width=90, height=90)
            av_container.pack()
            av_container.pack_propagate(False)

            avatar_img = make_avatar_image(username, size=84,
                                           image_path=AVATAR_PATHS[username],
                                           dark_mode=True)
            if avatar_img:
                self.avatar_refs[username] = avatar_img
                av = tk.Label(av_container, image=avatar_img,
                              bg="#23232c", cursor="hand2")
                av.place(x=3, y=3, width=84, height=84)
            else:
                av = tk.Label(av_container, text=username[0].upper(),
                              font=("Segoe UI", 34, "bold"),
                              bg=USERS[username]["color"], fg="white",
                              cursor="hand2")
                av.place(x=3, y=3, width=84, height=84)

            av.bind("<Button-1>", lambda e, u=username: self.change_photo(u))

            # Lápis sobreposto no canto inferior direito do avatar
            pencil = tk.Label(av_container, text="✏",
                              font=("Segoe UI", 12),
                              bg="#3b4048", fg="#ffffff",
                              cursor="hand2", padx=5, pady=1,
                              relief="flat", bd=1)
            pencil.place(relx=1.0, rely=1.0, anchor="se", x=0, y=0)
            pencil.bind("<Button-1>", lambda e, u=username: self.change_photo(u))

            tk.Label(card, text=username, font=("Segoe UI", 13, "bold"),
                     fg="#ffffff", bg="#23232c").pack(pady=(12, 4))

            tk.Button(card, text="Entrar", font=("Segoe UI", 10, "bold"),
                      bg="#2d6930", fg="white", activebackground="#3d8e41",
                      activeforeground="white", relief="flat",
                      cursor="hand2", padx=20, pady=6,
                      command=lambda u=username: self.show_password(u)).pack(fill=tk.X)

        tk.Button(wrap, text="← Voltar", font=("Segoe UI", 10),
                  bg="#1e1e24", fg="#abb2bf", activebackground="#1e1e24",
                  activeforeground="#ffffff", relief="flat",
                  cursor="hand2", command=self.show_welcome).pack(pady=(30, 0))

    def change_photo(self, username):
        if not PIL_AVAILABLE:
            messagebox.showinfo(
                "Pillow não instalado",
                "Para exibir fotos personalizadas instale o Pillow:\n\n"
                "    pip install Pillow"
            )
            return
        path = filedialog.askopenfilename(
            title=f"Escolher foto para {username}",
            filetypes=[("Imagens", "*.png *.jpg *.jpeg *.gif *.bmp"),
                       ("Todos os arquivos", "*.*")]
        )
        if path:
            AVATAR_PATHS[username] = path
            self.show_profiles()

    def show_password(self, username):
        self._clear()
        wrap = tk.Frame(self.container, bg="#1e1e24")
        wrap.place(relx=0.5, rely=0.5, anchor="center")

        avatar_img = make_avatar_image(username, size=110,
                                       image_path=AVATAR_PATHS[username],
                                       dark_mode=True)
        if avatar_img:
            self.avatar_refs["_selected"] = avatar_img
            tk.Label(wrap, image=avatar_img, bg="#1e1e24").pack()
        else:
            tk.Label(wrap, text=username[0].upper(), font=("Segoe UI", 44, "bold"),
                     bg=USERS[username]["color"], fg="white", width=3).pack()

        tk.Label(wrap, text=username, font=("Segoe UI", 20, "bold"),
                 fg="#ffffff", bg="#1e1e24").pack(pady=(12, 4))
        tk.Label(wrap, text="Digite a senha para continuar",
                 font=("Segoe UI", 10), fg="#abb2bf", bg="#1e1e24").pack(pady=(0, 24))

        pw_var = tk.StringVar()
        entry = tk.Entry(wrap, textvariable=pw_var, show="●",
                         font=("Segoe UI", 15), bg="#23232c", fg="#ffffff",
                         insertbackground="#61afef", relief="flat",
                         justify="center", width=22)
        entry.pack(ipady=10)
        entry.focus_set()

        err_label = tk.Label(wrap, text="", font=("Segoe UI", 9),
                             fg="#e06c75", bg="#1e1e24")
        err_label.pack(pady=(10, 0))

        btn_row = tk.Frame(wrap, bg="#1e1e24")
        btn_row.pack(pady=22)

        def try_login():
            if pw_var.get() == USERS[username]["password"]:
                self.on_login(username)
            else:
                err_label.configure(text="❌ Senha incorreta. Tente novamente.")
                pw_var.set("")
                entry.focus_set()

        tk.Button(btn_row, text="Entrar", font=("Segoe UI", 12, "bold"),
                  bg="#2d6930", fg="white", activebackground="#3d8e41",
                  activeforeground="white", relief="flat",
                  padx=34, pady=10, cursor="hand2",
                  command=try_login).pack(side=tk.LEFT, padx=6)

        tk.Button(btn_row, text="Voltar", font=("Segoe UI", 12),
                  bg="#3b4048", fg="white", activebackground="#4e5560",
                  activeforeground="white", relief="flat",
                  padx=34, pady=10, cursor="hand2",
                  command=self.show_profiles).pack(side=tk.LEFT, padx=6)

        entry.bind("<Return>", lambda e: try_login())
        tk.Label(wrap, text="Dica: senha padrão = 123",
                 font=("Segoe UI", 8), fg="#4b5263",
                 bg="#1e1e24").pack(pady=(10, 0))


# ============================================================
# ESTADO DO CLP
# ============================================================
class PlantPLCState:
    def __init__(self):
        self.I_START = False
        self.I_RESET = False
        self.I_POSITION = False
        self.I_STOP = False
        self.I_AUTO_MANUAL = True
        self.I_AUTO_MANUAL_PHYS = True
        self.I_QUIT = False
        self.I_EMERGENCY = True  # Emergência é NF - apenas física

        self.I_TABLE_IND = True
        self.I_DRILL_UP = True
        self.I_DRILL_DOWN = False
        self.I_TEST_UP = True
        self.I_TEST_DOWN = False
        self.I_CLAMP_RELEASED = True
        self.I_CLAMP_LOCKED = False
        self.I_PART_PRESENT = False

        self.Q_DRILL_MOTOR = False
        self.Q_TABLE_MOTOR = False
        self.Q_DRILL_DOWN = False
        self.Q_DRILL_UP = False
        self.Q_TEST_DOWN = False
        self.Q_CLAMP_LOCK = False

        self.R_DRILLED_COUNT = 0
        self.R_REJECT_COUNT = 0

        self.table_slots = [None, None, None, None]
        self.table_angle = 0.0
        self.target_table_angle = 0.0
        self.table_moving = False
        self.drill_pos = 0.0
        self.drill_rpm_angle = 0.0
        self.clamp_pos = 0.0
        self.test_pos = 0.0

        self.mode = "STANDBY"
        self.auto_step = 0
        self.manual_step = 0
        self.test_timer_start = 0.0
        self.drill_spin_delay = 0.0

        self.fault_drill_blocked = False
        self.auto_feed_enabled = False


# ============================================================
# APLICAÇÃO PRINCIPAL
# ============================================================
class FestoScadaApp:
    def __init__(self, root, username="Operador", on_logout=None):
        self.root = root
        self.current_user = username
        self.on_logout = on_logout
        self.dark_mode = True
        self.theme = THEMES["dark"]

        self.root.title("SCADA - Estação de Furação FESTO | Indústria 4.0 (UNIFEI)")
        self.root.geometry("1320x860")
        self.root.minsize(1150, 780)
        self.root.configure(bg=self.theme["bg_root"])

        self.plc = PlantPLCState()
        self.log_messages = []
        self._last_datetime = ""

        self.setup_styles()
        self.build_ui()

        self.log_event("SISTEMA", f"Supervisório iniciado. Operador: {self.current_user}.")

        self.running = True
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.after_id = self.root.after(40, self.update_cycle)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")

    # --------------------------------------------------------
    # CONSTRUÇÃO DA UI
    # --------------------------------------------------------
    def build_ui(self):
        t = self.theme
        self.root.configure(bg=t["bg_root"])

        # ===== TOP BAR =====
        top_bar = tk.Frame(self.root, bg=t["bg_header"], height=64)
        top_bar.pack(fill=tk.X, side=tk.TOP)
        top_bar.pack_propagate(False)

        title_box = tk.Frame(top_bar, bg=t["bg_header"])
        title_box.pack(side=tk.LEFT, padx=16, pady=8)
        tk.Label(title_box, text="ESTAÇÃO DE FURAÇÃO FESTO",
                 font=("Segoe UI", 14, "bold"),
                 fg=t["fg_primary"], bg=t["bg_header"]).pack(anchor="w")
        tk.Label(title_box, text="UNIFEI • ECAA02A SCADA • CLP GE Fanuc Série 90-30 (SNP)",
                 font=("Segoe UI", 9), fg=t["fg_dim"], bg=t["bg_header"]).pack(anchor="w")

        right_group = tk.Frame(top_bar, bg=t["bg_header"])
        right_group.pack(side=tk.RIGHT, padx=16, pady=8)

        # 1) Perfil (avatar + nome) — display, sem clique de foto
        self._build_profile_display(right_group)

        # 2) Botão SAIR (logout/switch account)
        tk.Button(right_group, text="⏻ Sair", font=("Segoe UI", 9, "bold"),
                  bg=t["btn_secondary"], fg=t["accent_red"],
                  activebackground=t["accent_red"], activeforeground="#ffffff",
                  relief="flat", bd=0, cursor="hand2", padx=10, pady=5,
                  command=self.cmd_logout).pack(side=tk.RIGHT, padx=6)

        # 3) Toggle Tema
        tk.Button(right_group, text=("☀" if self.dark_mode else "🌙"),
                  font=("Segoe UI", 13),
                  bg=t["bg_header"], fg=t["accent_yellow"],
                  activebackground=t["bg_panel"], activeforeground=t["accent_yellow"],
                  relief="flat", bd=0, cursor="hand2", padx=6, pady=2,
                  command=self.toggle_theme).pack(side=tk.RIGHT, padx=6)

        # 4) Data/Hora
        self.lbl_datetime = tk.Label(right_group, text="", font=("Consolas", 10),
                                     fg=t["fg_secondary"], bg=t["bg_header"])
        self.lbl_datetime.pack(side=tk.RIGHT, padx=10)
        self.update_datetime(force=True)

        # 5) COM status
        tk.Label(right_group, text="● COM ONLINE", font=("Segoe UI", 9, "bold"),
                 fg=t["accent_green"], bg=t["bg_header"]).pack(side=tk.RIGHT, padx=8)

        # 6) Modo badge
        self.lbl_mode_badge = tk.Label(right_group, text="MODO: STANDBY",
                                       font=("Segoe UI", 10, "bold"),
                                       fg=t["accent_yellow"],
                                       bg=self._mode_badge_bg("STANDBY"),
                                       padx=10, pady=4, relief="ridge")
        self.lbl_mode_badge.pack(side=tk.RIGHT, padx=6)

        # ===== CONTAINER CENTRAL =====
        main_container = tk.Frame(self.root, bg=t["bg_root"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Sinótico (esquerda)
        left_col = tk.Frame(main_container, bg=t["bg_panel"], bd=1, relief="solid")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        canvas_header = tk.Frame(left_col, bg=t["bg_panel_alt"], height=32)
        canvas_header.pack(fill=tk.X)
        tk.Label(canvas_header, text="SINÓTICO EM TEMPO REAL - BANCADA DE PROCESSO",
                 font=("Segoe UI", 10, "bold"),
                 fg=t["fg_secondary"], bg=t["bg_panel_alt"]).pack(side=tk.LEFT, padx=10, pady=4)

        self.canvas = tk.Canvas(left_col, bg=t["bg_canvas"], highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        legend_frame = tk.Frame(left_col, bg=t["bg_panel_alt"], height=28)
        legend_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(legend_frame,
                 text="Legenda: [E] Entrada  |  [F] Furação  |  [T] Teste de Furo  |  [S] Saída",
                 font=("Segoe UI", 8), fg=t["fg_secondary"],
                 bg=t["bg_panel_alt"]).pack(side=tk.LEFT, padx=8, pady=2)

        # Painéis (direita)
        right_col = tk.Frame(main_container, bg=t["bg_root"], width=460)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right_col.pack_propagate(False)

        # KPIs
        kpi_frame = tk.Frame(right_col, bg=t["bg_panel"], bd=1, relief="solid")
        kpi_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(kpi_frame, text="INDICADORES DE PRODUÇÃO (%R0100 / %R0104)",
                 font=("Segoe UI", 9, "bold"),
                 fg=t["accent_blue"], bg=t["bg_panel"]).pack(anchor="w", padx=10, pady=(6, 4))

        kpi_grid = tk.Frame(kpi_frame, bg=t["bg_panel"])
        kpi_grid.pack(fill=tk.X, padx=10, pady=(0, 8))

        k1 = tk.Frame(kpi_grid, bg=t["bg_card_ok"], bd=1, relief="groove")
        k1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        tk.Label(k1, text="FURADAS (OK)", font=("Segoe UI", 8, "bold"),
                 fg=t["accent_green"], bg=t["bg_card_ok"]).pack(pady=(4, 0))
        self.lbl_kpi_ok = tk.Label(k1, text="0", font=("Consolas", 18, "bold"),
                                   fg=t["accent_green"], bg=t["bg_card_ok"])
        self.lbl_kpi_ok.pack(pady=(0, 4))

        k2 = tk.Frame(kpi_grid, bg=t["bg_card_nok"], bd=1, relief="groove")
        k2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(k2, text="NÃO FURADAS (NOK)", font=("Segoe UI", 8, "bold"),
                 fg=t["accent_red"], bg=t["bg_card_nok"]).pack(pady=(4, 0))
        self.lbl_kpi_nok = tk.Label(k2, text="0", font=("Consolas", 18, "bold"),
                                    fg=t["accent_red"], bg=t["bg_card_nok"])
        self.lbl_kpi_nok.pack(pady=(0, 4))

        k3 = tk.Frame(kpi_grid, bg=t["bg_card_rate"], bd=1, relief="groove")
        k3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        tk.Label(k3, text="TAXA APROVAÇÃO", font=("Segoe UI", 8, "bold"),
                 fg=t["accent_blue"], bg=t["bg_card_rate"]).pack(pady=(4, 0))
        self.lbl_kpi_rate = tk.Label(k3, text="100 %", font=("Consolas", 18, "bold"),
                                     fg=t["accent_blue"], bg=t["bg_card_rate"])
        self.lbl_kpi_rate.pack(pady=(0, 4))

        # Botoeiras
        ctrl_frame = tk.Frame(right_col, bg=t["bg_panel"], bd=1, relief="solid")
        ctrl_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(ctrl_frame, text="BOTOEIRAS DO SUPERVISÓRIO (%M0300..%M0305)",
                 font=("Segoe UI", 9, "bold"),
                 fg=t["accent_blue"], bg=t["bg_panel"]).pack(anchor="w", padx=10, pady=(6, 4))

        sel_row = tk.Frame(ctrl_frame, bg=t["bg_panel"])
        sel_row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(sel_row, text="Chave Auto/Manual (%M0305):",
                 font=("Segoe UI", 9), fg=t["fg_secondary"],
                 bg=t["bg_panel"]).pack(side=tk.LEFT)

        self.btn_mode_auto = tk.Button(sel_row, text="AUTOMÁTICO",
                                       font=("Segoe UI", 8, "bold"),
                                       bg="#355c3d", fg="#ffffff",
                                       activebackground="#45784f",
                                       relief="raised", bd=2,
                                       command=self.cmd_set_auto)
        self.btn_mode_auto.pack(side=tk.RIGHT, padx=2)
        self.btn_mode_manual = tk.Button(sel_row, text="MANUAL",
                                         font=("Segoe UI", 8, "bold"),
                                         bg="#414552", fg="#ffffff",
                                         activebackground="#565c6d",
                                         relief="raised", bd=2,
                                         command=self.cmd_set_manual)
        self.btn_mode_manual.pack(side=tk.RIGHT, padx=2)

        btn_grid1 = tk.Frame(ctrl_frame, bg=t["bg_panel"])
        btn_grid1.pack(fill=tk.X, padx=10, pady=4)

        self.btn_start = tk.Button(btn_grid1, text="START (%M0300)",
                                   font=("Segoe UI", 9, "bold"),
                                   bg="#2d6930", fg="#ffffff",
                                   activebackground="#3d8e41",
                                   height=2, relief="raised", bd=3,
                                   command=self.cmd_start)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_stop = tk.Button(btn_grid1, text="STOP (%M0301)",
                                  font=("Segoe UI", 9, "bold"),
                                  bg="#8f2d2d", fg="#ffffff",
                                  activebackground="#b83939",
                                  height=2, relief="raised", bd=3,
                                  command=self.cmd_stop)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_reset = tk.Button(btn_grid1, text="RESET (%M0304)",
                                   font=("Segoe UI", 9, "bold"),
                                   bg="#826620", fg="#ffffff",
                                   activebackground="#a68429",
                                   height=2, relief="raised", bd=3,
                                   command=self.cmd_reset)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        # Linha 2: POSITION + QUIT (emergência removida — apenas física)
        btn_grid2 = tk.Frame(ctrl_frame, bg=t["bg_panel"])
        btn_grid2.pack(fill=tk.X, padx=10, pady=(2, 6))

        self.btn_pos = tk.Button(btn_grid2, text="POSITION (%M0302)",
                                 font=("Segoe UI", 8, "bold"),
                                 bg=t["btn_secondary"], fg="#ffffff",
                                 activebackground=t["btn_secondary_active"],
                                 relief="raised", bd=2,
                                 command=self.cmd_position)
        self.btn_pos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_quit = tk.Button(btn_grid2, text="QUIT (%M0303)",
                                  font=("Segoe UI", 8, "bold"),
                                  bg=t["btn_secondary"], fg="#ffffff",
                                  activebackground=t["btn_secondary_active"],
                                  relief="raised", bd=2,
                                  command=self.cmd_quit)
        self.btn_quit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        # Simulação
        sim_frame = tk.Frame(right_col, bg=t["bg_panel"], bd=1, relief="solid")
        sim_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(sim_frame, text="INTERAÇÃO DE BANCADA & ALIMENTAÇÃO",
                 font=("Segoe UI", 9, "bold"),
                 fg=t["accent_orange"], bg=t["bg_panel"]).pack(anchor="w", padx=10, pady=(6, 4))

        sim_row = tk.Frame(sim_frame, bg=t["bg_panel"])
        sim_row.pack(fill=tk.X, padx=10, pady=(0, 6))

        tk.Button(sim_row, text="＋ Inserir Peça na Entrada",
                  font=("Segoe UI", 8, "bold"),
                  bg="#2e4d6d", fg="#ffffff", relief="groove",
                  command=self.cmd_insert_piece).pack(side=tk.LEFT, fill=tk.X,
                                                       expand=True, padx=(0, 4))

        self.btn_autofeed = tk.Button(sim_row, text="Auto-Alimentação: OFF",
                                      font=("Segoe UI", 8),
                                      bg=t["btn_secondary"], fg="#dcdfe4",
                                      relief="groove",
                                      command=self.cmd_toggle_autofeed)
        self.btn_autofeed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_fault = tk.Button(sim_row, text="Falha de Furo: OFF",
                                   font=("Segoe UI", 8),
                                   bg=t["btn_secondary"], fg="#dcdfe4",
                                   relief="groove",
                                   command=self.cmd_toggle_fault)
        self.btn_fault.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # I/O Diagnóstico
        io_frame = tk.Frame(right_col, bg=t["bg_panel"], bd=1, relief="solid")
        io_frame.pack(fill=tk.X, pady=(0, 8))
        tk.Label(io_frame, text="DIAGNÓSTICO DE I/O (%I e %Q)",
                 font=("Segoe UI", 9, "bold"),
                 fg=t["accent_blue"], bg=t["bg_panel"]).pack(anchor="w", padx=10, pady=(6, 4))

        self.led_canvas = tk.Canvas(io_frame, bg=t["bg_canvas"], height=135,
                                    highlightthickness=0)
        self.led_canvas.pack(fill=tk.X, padx=8, pady=(0, 6))

        # Log
        log_frame = tk.Frame(right_col, bg=t["bg_panel"], bd=1, relief="solid")
        log_frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(log_frame, text="HISTÓRICO DE EVENTOS E ALARMES",
                 font=("Segoe UI", 9, "bold"),
                 fg=t["accent_yellow"], bg=t["bg_panel"]).pack(anchor="w", padx=10, pady=(6, 2))

        self.log_listbox = tk.Listbox(log_frame, bg=t["bg_input"],
                                       fg=t["fg_secondary"],
                                       font=("Consolas", 8),
                                       selectbackground="#2c313a",
                                       relief="flat")
        self.log_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

    # --------------------------------------------------------
    # HELPERS
    # --------------------------------------------------------
    def _build_profile_display(self, parent):
        t = self.theme
        profile_frame = tk.Frame(parent, bg=t["bg_header"])
        profile_frame.pack(side=tk.RIGHT, padx=(4, 0))

        avatar_img = make_avatar_image(self.current_user, size=34,
                                       image_path=AVATAR_PATHS.get(self.current_user),
                                       dark_mode=self.dark_mode)
        if avatar_img:
            self.header_avatar_ref = avatar_img
            tk.Label(profile_frame, image=avatar_img,
                     bg=t["bg_header"]).pack(side=tk.RIGHT)
        else:
            tk.Label(profile_frame, text=self.current_user[0].upper(),
                     font=("Segoe UI", 13, "bold"),
                     bg=USERS[self.current_user]["color"], fg="white",
                     width=2).pack(side=tk.RIGHT)

        tk.Label(profile_frame, text=self.current_user,
                 font=("Segoe UI", 10, "bold"),
                 fg=t["fg_primary"], bg=t["bg_header"]).pack(side=tk.RIGHT, padx=(6, 0))

    def _mode_badge_bg(self, mode):
        if not self.dark_mode:
            return {"AUTO_RUNNING": "#dcf0e0", "MANUAL": "#fef3d0",
                    "EMERGENCY": "#fadada", "STOPPED": "#fadada",
                    "STANDBY": "#e8e8ee"}.get(mode, "#e8e8ee")
        return {"AUTO_RUNNING": "#1b4427", "MANUAL": "#473b18",
                "EMERGENCY": "#5c1d1d", "STOPPED": "#3d2222",
                "STANDBY": "#282c34"}.get(mode, "#282c34")

    # --------------------------------------------------------
    # TEMA / LOGOUT
    # --------------------------------------------------------
    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.theme = THEMES["dark" if self.dark_mode else "light"]
        self.rebuild_ui()
        self.log_event("IHM", f"Tema alterado para {'ESCURO' if self.dark_mode else 'CLARO'}.")

    def rebuild_ui(self):
        saved_logs = list(self.log_messages)
        for child in self.root.winfo_children():
            child.destroy()
        self.setup_styles()
        self.build_ui()
        for entry in saved_logs:
            if hasattr(self, "log_listbox") and self.log_listbox.winfo_exists():
                self.log_listbox.insert(tk.END, entry)
        self.update_kpis()
        self.render_synoptic()
        self.render_io_leds()

    def cmd_logout(self):
        if not messagebox.askyesno("Sair da conta",
                                   f"Deseja sair da conta de {self.current_user}?"):
            return
        self.running = False
        if hasattr(self, "after_id"):
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
        if self.on_logout:
            self.on_logout()

    def update_datetime(self, force=False):
        lbl = getattr(self, "lbl_datetime", None)
        if not lbl or not lbl.winfo_exists():
            return
        now = time.strftime("%d/%m/%Y  %H:%M:%S")
        if force or self._last_datetime != now:
            lbl.configure(text=now)
            self._last_datetime = now

    def on_close(self):
        self.running = False
        if hasattr(self, "after_id"):
            try:
                self.root.after_cancel(self.after_id)
            except Exception:
                pass
        self.root.destroy()

    # --------------------------------------------------------
    # COMANDOS
    # --------------------------------------------------------
    def cmd_start(self):
        if not self.plc.I_EMERGENCY:
            self.log_event("ALERTA", "Comando START rejeitado: Emergência acionada!")
            return
        self.plc.I_START = True
        self.log_event("IHM", "Botoeira START (%M0300) acionada.")
        if self.plc.I_AUTO_MANUAL:
            self.plc.mode = "AUTO_RUNNING"
            self.log_event("PROCESSO", "Modo AUTOMÁTICO habilitado.")

    def cmd_stop(self):
        self.plc.I_STOP = True
        self.plc.mode = "STOPPED"
        self.plc.Q_DRILL_MOTOR = False
        self.plc.Q_TABLE_MOTOR = False
        self.plc.Q_DRILL_DOWN = False
        self.plc.Q_DRILL_UP = False
        self.plc.Q_TEST_DOWN = False
        self.plc.Q_CLAMP_LOCK = False
        self.log_event("SEGURANÇA", "Botoeira STOP (%M0301) acionada! Processo paralisado.")

    def cmd_reset(self):
        self.plc.I_RESET = True
        self.plc.R_DRILLED_COUNT = 0
        self.plc.R_REJECT_COUNT = 0
        self.plc.auto_step = 0
        self.plc.manual_step = 0
        self.plc.mode = "STANDBY"
        self.log_event("IHM", "Botoeira RESET (%M0304) executada: Contadores e estados zerados.")

    def cmd_position(self):
        if not self.plc.I_AUTO_MANUAL and self.plc.mode != "EMERGENCY":
            if not self.plc.table_moving:
                self.plc.Q_TABLE_MOTOR = True
                self.plc.table_moving = True
                self.plc.target_table_angle = (self.plc.table_angle + 90.0) % 360.0
                self.log_event("MANUAL", "Comando POSITION (%M0302): Iniciando avanço de 90°.")
            else:
                self.log_event("MANUAL", "Mesa já em movimento.")
        else:
            self.log_event("ALERTA", "Comando POSITION só opera em modo MANUAL.")

    def cmd_quit(self):
        self.plc.I_QUIT = True
        if self.plc.mode == "AUTO_RUNNING":
            has_pieces = any(slot is not None for slot in self.plc.table_slots) or self.plc.I_PART_PRESENT
            if not has_pieces:
                self.plc.mode = "STANDBY"
                self.log_event("IHM", "Comando QUIT (%M0303): Modo automático desabilitado.")
            else:
                self.log_event("IHM", "QUIT solicitado: Sistema finalizará as peças atuais.")

    def cmd_set_auto(self):
        if not self.plc.I_AUTO_MANUAL_PHYS:
            self.log_event("BLOQUEIO", "Comando rejeitado: Chave física local em MANUAL (prioritária).")
            return
        self.plc.I_AUTO_MANUAL = True
        self.btn_mode_auto.configure(bg="#355c3d")
        self.btn_mode_manual.configure(bg="#414552")
        self.log_event("IHM", "Modo selecionado: AUTOMÁTICO.")

    def cmd_set_manual(self):
        self.plc.I_AUTO_MANUAL = False
        self.plc.mode = "MANUAL"
        self.btn_mode_auto.configure(bg="#414552")
        self.btn_mode_manual.configure(bg="#6e622b")
        self.plc.Q_DRILL_MOTOR = False
        self.plc.Q_DRILL_DOWN = False
        self.plc.Q_TEST_DOWN = False
        self.plc.Q_CLAMP_LOCK = False
        self.log_event("IHM", "Modo selecionado: MANUAL.")

    def cmd_insert_piece(self):
        if self.plc.table_slots[0] is None:
            self.plc.table_slots[0] = {
                "drilled": False, "tested": False, "ok": False,
                "id": len(self.log_messages) + 1
            }
            self.plc.I_PART_PRESENT = True
            self.log_event("ALIMENTAÇÃO", "Peça bruta inserida na ENTRADA.")
        else:
            self.log_event("ALERTA", "Posição de ENTRADA já ocupada!")

    def cmd_toggle_autofeed(self):
        self.plc.auto_feed_enabled = not self.plc.auto_feed_enabled
        if self.plc.auto_feed_enabled:
            self.btn_autofeed.configure(bg="#2e6d44", text="Auto-Alimentação: ON")
            self.log_event("SIMULAÇÃO", "Alimentação contínua ativada.")
        else:
            self.btn_autofeed.configure(bg=self.theme["btn_secondary"],
                                        text="Auto-Alimentação: OFF")
            self.log_event("SIMULAÇÃO", "Alimentação contínua desativada.")

    def cmd_toggle_fault(self):
        self.plc.fault_drill_blocked = not self.plc.fault_drill_blocked
        if self.plc.fault_drill_blocked:
            self.btn_fault.configure(bg="#8f2d2d", text="Falha de Furo: ON")
            self.log_event("DEFEITO", "Injeção de defeito ATIVA.")
        else:
            self.btn_fault.configure(bg=self.theme["btn_secondary"],
                                     text="Falha de Furo: OFF")
            self.log_event("DEFEITO", "Injeção de defeito desativada.")

    def log_event(self, source, msg):
        t_str = time.strftime("%H:%M:%S")
        entry = f"[{t_str}] [{source}] {msg}"
        self.log_messages.append(entry)
        if hasattr(self, "log_listbox") and self.log_listbox.winfo_exists():
            self.log_listbox.insert(tk.END, entry)
            self.log_listbox.see(tk.END)

    # --------------------------------------------------------
    # LOOP DE CONTROLE
    # --------------------------------------------------------
    def update_cycle(self):
        if not self.running:
            return
        self.step_plc_logic()
        self.step_physical_plant()
        self.render_synoptic()
        self.render_io_leds()
        self.update_kpis()
        self.update_datetime()
        self.after_id = self.root.after(40, self.update_cycle)

    def step_plc_logic(self):
        if self.plc.mode in ["EMERGENCY", "STOPPED"]:
            return

        self.plc.I_PART_PRESENT = (self.plc.table_slots[0] is not None)

        if self.plc.auto_feed_enabled and self.plc.mode == "AUTO_RUNNING":
            if self.plc.table_slots[0] is None and not self.plc.table_moving:
                self.plc.table_slots[0] = {
                    "drilled": False, "tested": False, "ok": False,
                    "id": int(time.time() * 10) % 1000
                }
                self.plc.I_PART_PRESENT = True

        if self.plc.mode == "AUTO_RUNNING":
            if self.plc.auto_step == 0:
                has_work = any(slot is not None for slot in self.plc.table_slots)
                if (has_work or self.plc.I_PART_PRESENT) and not self.plc.table_moving:
                    if self.plc.I_DRILL_UP and self.plc.I_TEST_UP and self.plc.I_CLAMP_RELEASED:
                        need_drill = (self.plc.table_slots[1] is not None and
                                      not self.plc.table_slots[1]["drilled"])
                        need_test = (self.plc.table_slots[2] is not None and
                                     not self.plc.table_slots[2]["tested"])
                        if need_drill or need_test:
                            self.plc.auto_step = 20
                        else:
                            if self.plc.table_slots[3] is not None:
                                p = self.plc.table_slots[3]
                                self.log_event(
                                    "SAÍDA",
                                    f"Peça #{p['id']} coletada (Status: "
                                    f"{'OK' if p['ok'] else 'REJEITO'})."
                                )
                                self.plc.table_slots[3] = None
                            self.plc.auto_step = 10
                            self.plc.Q_TABLE_MOTOR = True
                            self.plc.table_moving = True
                            self.plc.target_table_angle = (self.plc.table_angle + 90.0) % 360.0
                            self.log_event("MESA", "Avanço de 90° iniciado.")

            elif self.plc.auto_step == 10:
                if not self.plc.table_moving and self.plc.I_TABLE_IND:
                    self.plc.Q_TABLE_MOTOR = False
                    self.plc.table_slots = [None, self.plc.table_slots[0],
                                            self.plc.table_slots[1], self.plc.table_slots[2]]
                    self.log_event("MESA", "Posicionamento 90° concluído.")
                    self.plc.auto_step = 0

            elif self.plc.auto_step == 20:
                p_drill = self.plc.table_slots[1]
                if p_drill is not None and not p_drill["drilled"]:
                    if not self.plc.I_CLAMP_LOCKED:
                        self.plc.Q_CLAMP_LOCK = True
                    else:
                        self.plc.Q_DRILL_MOTOR = True
                        if self.plc.drill_spin_delay < 1.0:
                            self.plc.drill_spin_delay += 0.05
                        else:
                            self.plc.Q_DRILL_DOWN = True
                            self.plc.Q_DRILL_UP = False
                            if self.plc.I_DRILL_DOWN:
                                p_drill["drilled"] = True
                                self.log_event("FURAÇÃO",
                                               f"Furo concluído na peça #{p_drill['id']}.")

                if p_drill is None or p_drill["drilled"] or self.plc.fault_drill_blocked:
                    if self.plc.drill_pos > 0.0:
                        self.plc.Q_DRILL_DOWN = False
                        self.plc.Q_DRILL_UP = True
                    else:
                        self.plc.Q_DRILL_UP = False
                        if self.plc.I_DRILL_UP:
                            self.plc.Q_DRILL_MOTOR = False
                            self.plc.Q_CLAMP_LOCK = False
                            self.plc.drill_spin_delay = 0.0
                            if self.plc.fault_drill_blocked and p_drill and not p_drill["drilled"]:
                                p_drill["drilled"] = True
                                self.log_event("FURAÇÃO",
                                               f"Furadeira abortou (peça #{p_drill['id']} defeituosa).")

                p_test = self.plc.table_slots[2]
                if p_test is not None and not p_test["tested"]:
                    self.plc.Q_TEST_DOWN = True
                    if self.plc.test_timer_start == 0.0:
                        self.plc.test_timer_start = time.time()
                    elapsed = time.time() - self.plc.test_timer_start
                    if self.plc.I_TEST_DOWN:
                        p_test["tested"] = True
                        p_test["ok"] = True
                        self.plc.R_DRILLED_COUNT += 1
                        self.log_event("TESTE",
                                       f"Peça #{p_test['id']} APROVADA! (%R0100={self.plc.R_DRILLED_COUNT})")
                        self.plc.Q_TEST_DOWN = False
                        self.plc.test_timer_start = 0.0
                    elif elapsed >= 3.0:
                        p_test["tested"] = True
                        p_test["ok"] = False
                        self.plc.R_REJECT_COUNT += 1
                        self.log_event("TESTE",
                                       f"Peça #{p_test['id']} REJEITADA! (%R0104={self.plc.R_REJECT_COUNT})")
                        self.plc.Q_TEST_DOWN = False
                        self.plc.test_timer_start = 0.0
                else:
                    self.plc.Q_TEST_DOWN = False
                    self.plc.test_timer_start = 0.0

                drill_done = (p_drill is None or
                              (p_drill["drilled"] and self.plc.I_DRILL_UP and self.plc.I_CLAMP_RELEASED))
                test_done = (p_test is None or (p_test["tested"] and self.plc.I_TEST_UP))
                if drill_done and test_done:
                    self.plc.auto_step = 0

    def step_physical_plant(self):
        if self.plc.table_moving:
            diff = (self.plc.target_table_angle - self.plc.table_angle) % 360.0
            if 0.1 < diff <= 95.0:
                self.plc.table_angle = (self.plc.table_angle + 6.0) % 360.0
                self.plc.I_TABLE_IND = False
            else:
                self.plc.table_angle = self.plc.target_table_angle
                self.plc.table_moving = False
                self.plc.Q_TABLE_MOTOR = False
                self.plc.I_TABLE_IND = True

        if self.plc.Q_DRILL_DOWN and not self.plc.Q_DRILL_UP:
            if self.plc.fault_drill_blocked:
                if self.plc.drill_pos < 0.45:
                    self.plc.drill_pos += 0.05
            else:
                if self.plc.drill_pos < 1.0:
                    self.plc.drill_pos += 0.06
                    if self.plc.drill_pos >= 1.0:
                        self.plc.drill_pos = 1.0
        elif self.plc.Q_DRILL_UP and not self.plc.Q_DRILL_DOWN:
            if self.plc.drill_pos > 0.0:
                self.plc.drill_pos -= 0.08
                if self.plc.drill_pos <= 0.0:
                    self.plc.drill_pos = 0.0

        self.plc.I_DRILL_UP = (self.plc.drill_pos <= 0.05)
        self.plc.I_DRILL_DOWN = (self.plc.drill_pos >= 0.95)

        if self.plc.Q_DRILL_MOTOR:
            self.plc.drill_rpm_angle = (self.plc.drill_rpm_angle + 30.0) % 360.0

        if self.plc.Q_CLAMP_LOCK:
            if self.plc.clamp_pos < 1.0:
                self.plc.clamp_pos += 0.15
                if self.plc.clamp_pos >= 1.0:
                    self.plc.clamp_pos = 1.0
        else:
            if self.plc.clamp_pos > 0.0:
                self.plc.clamp_pos -= 0.15
                if self.plc.clamp_pos <= 0.0:
                    self.plc.clamp_pos = 0.0

        self.plc.I_CLAMP_RELEASED = (self.plc.clamp_pos <= 0.05)
        self.plc.I_CLAMP_LOCKED = (self.plc.clamp_pos >= 0.95)

        if self.plc.Q_TEST_DOWN:
            p_test = self.plc.table_slots[2]
            target_depth = 1.0 if (p_test and p_test.get("drilled", False)
                                   and not self.plc.fault_drill_blocked) else 0.4
            if self.plc.test_pos < target_depth:
                self.plc.test_pos += 0.06
                if self.plc.test_pos >= target_depth:
                    self.plc.test_pos = target_depth
        else:
            if self.plc.test_pos > 0.0:
                self.plc.test_pos -= 0.1
                if self.plc.test_pos <= 0.0:
                    self.plc.test_pos = 0.0

        self.plc.I_TEST_UP = (self.plc.test_pos <= 0.05)
        self.plc.I_TEST_DOWN = (self.plc.test_pos >= 0.95)

    # --------------------------------------------------------
    # SINÓTICO
    # --------------------------------------------------------
    def render_synoptic(self):
        c = self.canvas
        t = self.theme
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100 or h < 100:
            return

        c.delete("all")
        c.create_rectangle(0, 0, w, h, fill=t["canvas_bg"], outline="")
        for gx in range(0, w, 40):
            c.create_line(gx, 0, gx, h, fill=t["grid_line"], width=1)
        for gy in range(0, h, 40):
            c.create_line(0, gy, w, gy, fill=t["grid_line"], width=1)

        cx = w * 0.48
        cy = h * 0.52
        table_r = min(w, h) * 0.32

        c.create_oval(cx - table_r - 18, cy - table_r - 18,
                      cx + table_r + 18, cy + table_r + 18,
                      fill="#2a2b36", outline=t["border"], width=3)
        c.create_oval(cx - table_r, cy - table_r, cx + table_r, cy + table_r,
                      fill="#343746", outline="#52576b", width=2)

        rad = math.radians(self.plc.table_angle)
        for i in range(4):
            a = rad + (i * math.pi / 2.0)
            ex = cx + table_r * math.cos(a)
            ey = cy + table_r * math.sin(a)
            c.create_line(cx, cy, ex, ey, fill="#20222b", width=2, dash=(4, 2))

        c.create_oval(cx - 30, cy - 30, cx + 30, cy + 30,
                      fill="#222430", outline=t["accent_blue"], width=2)
        c.create_text(cx, cy, text="MESA\nINDEX", font=("Segoe UI", 7, "bold"),
                      fill=t["accent_blue"], justify="center")

        c.create_rectangle(cx + table_r + 4, cy - 10,
                           cx + table_r + 26, cy + 10,
                           fill=t["bg_panel"], outline=t["accent_yellow"], width=1)
        c.create_oval(cx + table_r + 7, cy - 5,
                      cx + table_r + 17, cy + 5,
                      fill=t["accent_green"] if self.plc.I_TABLE_IND else t["fg_muted"], outline="")
        c.create_text(cx + table_r + 34, cy, text="%I0009\nIndutivo",
                      font=("Consolas", 7), fill=t["accent_yellow"], anchor="w")

        station_angles = [math.pi, 3 * math.pi / 2.0, 0.0, math.pi / 2.0]
        station_names = ["1. ENTRADA", "2. FURAÇÃO", "3. TESTE", "4. SAÍDA"]

        for idx, (s_ang, s_name) in enumerate(zip(station_angles, station_names)):
            sx = cx + (table_r * 0.65) * math.cos(s_ang)
            sy = cy + (table_r * 0.65) * math.sin(s_ang)
            c.create_oval(sx - 24, sy - 24, sx + 24, sy + 24,
                          fill=t["canvas_inner"], outline=t["border"], width=2)
            c.create_text(sx, sy, text=f"P{idx+1}", font=("Segoe UI", 8, "bold"),
                          fill=t["fg_muted"])

            piece = self.plc.table_slots[idx]
            if piece is not None:
                if piece.get("ok"):
                    p_color = t["accent_green"]
                elif piece.get("drilled"):
                    p_color = t["accent_orange"]
                else:
                    p_color = t["accent_blue"]
                c.create_oval(sx - 18, sy - 18, sx + 18, sy + 18,
                              fill=p_color, outline="#ffffff", width=2)
                if piece.get("drilled"):
                    c.create_oval(sx - 6, sy - 6, sx + 6, sy + 6,
                                  fill=t["canvas_bg"], outline=t["canvas_inner"], width=1)
                c.create_text(sx, sy + 1, text=f"#{piece['id']}",
                              font=("Segoe UI", 7, "bold"), fill="#181822")

        # --- Estação Entrada ---
        p1_x = cx - table_r - 80
        p1_y = cy
        c.create_rectangle(p1_x - 45, p1_y - 25, p1_x + 45, p1_y + 25,
                           fill=t["bg_panel"], outline=t["accent_blue"], width=1)
        c.create_text(p1_x, p1_y - 8, text="[ ENTRADA ]",
                      font=("Segoe UI", 8, "bold"), fill=t["accent_blue"])
        sensor_ent_color = t["accent_green"] if self.plc.I_PART_PRESENT else t["fg_muted"]
        c.create_oval(p1_x - 30, p1_y + 4, p1_x - 18, p1_y + 16,
                      fill=sensor_ent_color, outline="")
        c.create_text(p1_x - 10, p1_y + 10, text="%I0016 Reflex.",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="w")

        # --- Estação Furação (layout corrigido) ---
        p2_x = cx
        p2_y = cy - table_r - 75
        # Caixa mais alta para acomodar o rótulo da trava com folga
        c.create_rectangle(p2_x - 95, p2_y - 45, p2_x + 95, p2_y + 65,
                           fill=t["bg_panel"], outline=t["accent_yellow"], width=1)
        c.create_text(p2_x, p2_y - 32, text="[ ESTAÇÃO DE FURAÇÃO ]",
                      font=("Segoe UI", 8, "bold"), fill=t["accent_yellow"])

        # Furadeira à esquerda
        drill_col_x = p2_x - 35
        c.create_rectangle(drill_col_x - 12, p2_y - 20,
                           drill_col_x + 12, p2_y + 20,
                           fill="#3e4451", outline="#5c6370")
        drill_head_y = p2_y - 12 + (self.plc.drill_pos * 30)
        c.create_rectangle(drill_col_x - 4, p2_y - 20,
                           drill_col_x + 4, drill_head_y,
                           fill="#abb2bf", outline="")
        motor_col = t["accent_green"] if self.plc.Q_DRILL_MOTOR else t["fg_muted"]
        c.create_oval(drill_col_x - 10, drill_head_y,
                      drill_col_x + 10, drill_head_y + 14,
                      fill=motor_col,
                      outline="#ffffff" if self.plc.Q_DRILL_MOTOR else "")
        c.create_line(drill_col_x, drill_head_y + 14,
                      drill_col_x, drill_head_y + 26,
                      fill="#abb2bf", width=2)

        c.create_oval(drill_col_x + 16, p2_y - 16,
                      drill_col_x + 24, p2_y - 8,
                      fill=t["accent_green"] if self.plc.I_DRILL_UP else t["fg_muted"], outline="")
        c.create_text(drill_col_x + 28, p2_y - 12, text="%I0010 (Sup)",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="w")
        c.create_oval(drill_col_x + 16, p2_y + 8,
                      drill_col_x + 24, p2_y + 16,
                      fill=t["accent_green"] if self.plc.I_DRILL_DOWN else t["fg_muted"], outline="")
        c.create_text(drill_col_x + 28, p2_y + 12, text="%I0011 (Inf)",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="w")

        # Trava à direita — rótulo claramente abaixo do pistão
        clamp_x = p2_x + 45
        clamp_ext = self.plc.clamp_pos * 14
        c.create_rectangle(clamp_x, p2_y - 4, clamp_x + 28, p2_y + 16,
                           fill=t["bg_panel_alt"], outline=t["accent_blue"])
        c.create_rectangle(clamp_x - clamp_ext, p2_y + 1, clamp_x, p2_y + 11,
                           fill=t["accent_green"] if self.plc.I_CLAMP_LOCKED else t["accent_yellow"],
                           outline="")
        # Rótulo "Trava %Q0006" bem abaixo do pistão, sem sobreposição
        c.create_text(clamp_x + 14, p2_y + 38, text="Trava %Q0006",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="n")

        # --- Estação Teste ---
        p3_x = cx + table_r + 90
        p3_y = cy
        c.create_rectangle(p3_x - 45, p3_y - 50, p3_x + 85, p3_y + 50,
                           fill=t["bg_panel"], outline=t["accent_green"], width=1)
        c.create_text(p3_x + 20, p3_y - 36, text="[ TESTE DO FURO ]",
                      font=("Segoe UI", 8, "bold"), fill=t["accent_green"])

        test_col_x = p3_x - 15
        c.create_rectangle(test_col_x - 8, p3_y - 20,
                           test_col_x + 8, p3_y + 15,
                           fill="#3e4451", outline="#5c6370")
        test_probe_y = p3_y - 15 + (self.plc.test_pos * 35)
        c.create_line(test_col_x, p3_y - 20,
                      test_col_x, test_probe_y + 20,
                      fill=t["accent_blue"], width=3)
        c.create_oval(test_col_x - 3, test_probe_y + 20,
                      test_col_x + 3, test_probe_y + 26,
                      fill="#ffffff", outline="")

        c.create_oval(test_col_x + 16, p3_y - 18,
                      test_col_x + 24, p3_y - 10,
                      fill=t["accent_green"] if self.plc.I_TEST_UP else t["fg_muted"], outline="")
        c.create_text(test_col_x + 28, p3_y - 14, text="%I0012 (Sup)",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="w")
        c.create_oval(test_col_x + 16, p3_y + 6,
                      test_col_x + 24, p3_y + 14,
                      fill=t["accent_green"] if self.plc.I_TEST_DOWN else t["fg_muted"], outline="")
        c.create_text(test_col_x + 28, p3_y + 10, text="%I0013 (Inf)",
                      font=("Consolas", 7), fill=t["fg_secondary"], anchor="w")

        if self.plc.test_timer_start > 0:
            elapsed = min(3.0, time.time() - self.plc.test_timer_start)
            c.create_text(p3_x + 20, p3_y + 36,
                          text=f"Tempo: {elapsed:.1f}s / 3.0s",
                          font=("Consolas", 8, "bold"), fill=t["accent_yellow"])

        # --- Estação Saída ---
        p4_x = cx
        p4_y = cy + table_r + 65
        c.create_rectangle(p4_x - 55, p4_y - 20, p4_x + 55, p4_y + 20,
                           fill=t["bg_panel"], outline=t["accent_purple"], width=1)
        c.create_text(p4_x, p4_y, text="[ SAÍDA DE PEÇAS ]",
                      font=("Segoe UI", 8, "bold"), fill=t["accent_purple"])

    # --------------------------------------------------------
    # LEDs DE DIAGNÓSTICO — layout dinâmico para caber tudo
    # --------------------------------------------------------
    def render_io_leds(self):
        c = self.led_canvas
        t = self.theme
        w = c.winfo_width()
        if w < 100:
            return
        c.delete("all")
        c.configure(bg=t["canvas_bg"])

        inputs = [
            ("0001", "START", self.plc.I_START),
            ("0002", "RESET", self.plc.I_RESET),
            ("0003", "POSIT", self.plc.I_POSITION),
            ("0004", "STOP",  self.plc.I_STOP),
            ("0005", "CHAVE", self.plc.I_AUTO_MANUAL),
            ("0008", "EMERG", self.plc.I_EMERGENCY),
            ("0009", "MESA",  self.plc.I_TABLE_IND),
            ("0010", "FUR.S", self.plc.I_DRILL_UP),
            ("0011", "FUR.I", self.plc.I_DRILL_DOWN),
            ("0012", "TST.S", self.plc.I_TEST_UP),
            ("0013", "TST.I", self.plc.I_TEST_DOWN),
            ("0015", "TRAVA", self.plc.I_CLAMP_LOCKED),
            ("0016", "PRES",  self.plc.I_PART_PRESENT),
        ]
        outputs = [
            ("0001", "M.FUR", self.plc.Q_DRILL_MOTOR),
            ("0002", "M.MES", self.plc.Q_TABLE_MOTOR),
            ("0003", "S.DEC", self.plc.Q_DRILL_DOWN),
            ("0004", "S.SUB", self.plc.Q_DRILL_UP),
            ("0005", "S.TST", self.plc.Q_TEST_DOWN),
            ("0006", "S.TRV", self.plc.Q_CLAMP_LOCK),
        ]

        # Coluna do rótulo ("IN %I", "OUT %Q") e padding direito
        label_w = 46
        pad_right = 6
        n_in = len(inputs)
        n_out = len(outputs)

        # Larguras dinâmicas — garante que TODAS as entradas caibam
        col_in = (w - label_w - pad_right) / n_in
        col_out = (w - label_w - pad_right) / n_out

        # ---- Linha 1: Entradas (%I) ----
        c.create_text(4, 22, text="IN %I", font=("Segoe UI", 7, "bold"),
                      fill=t["accent_blue"], anchor="w")
        for i, (addr, name, val) in enumerate(inputs):
            cx_i = label_w + col_in * (i + 0.5)
            color = t["accent_green"] if val else t["btn_secondary"]
            c.create_oval(cx_i - 5, 16, cx_i + 5, 26,
                          fill=color, outline=t["border"])
            c.create_text(cx_i, 36, text=name,
                          font=("Segoe UI", 6), fill=t["fg_dim"])
            c.create_text(cx_i, 45, text=addr,
                          font=("Consolas", 6), fill=t["fg_muted"])

        # ---- Linha 2: Saídas (%Q) ----
        c.create_text(4, 78, text="OUT %Q", font=("Segoe UI", 7, "bold"),
                      fill=t["accent_yellow"], anchor="w")
        for i, (addr, name, val) in enumerate(outputs):
            cx_i = label_w + col_out * (i + 0.5)
            color = t["accent_yellow"] if val else t["btn_secondary"]
            c.create_oval(cx_i - 5, 72, cx_i + 5, 82,
                          fill=color, outline=t["border"])
            c.create_text(cx_i, 92, text=name,
                          font=("Segoe UI", 6), fill=t["fg_secondary"])
            c.create_text(cx_i, 101, text=addr,
                          font=("Consolas", 6), fill=t["fg_muted"])

        # Resetar pulsos momentâneos
        self.plc.I_START = False
        self.plc.I_STOP = False
        self.plc.I_RESET = False
        self.plc.I_POSITION = False
        self.plc.I_QUIT = False

    # --------------------------------------------------------
    # KPIs
    # --------------------------------------------------------
    def update_kpis(self):
        if not hasattr(self, "lbl_kpi_ok") or not self.lbl_kpi_ok.winfo_exists():
            return
        self.lbl_kpi_ok.configure(text=str(self.plc.R_DRILLED_COUNT))
        self.lbl_kpi_nok.configure(text=str(self.plc.R_REJECT_COUNT))
        total = self.plc.R_DRILLED_COUNT + self.plc.R_REJECT_COUNT
        rate = (self.plc.R_DRILLED_COUNT / total * 100.0) if total > 0 else 100.0
        self.lbl_kpi_rate.configure(text=f"{rate:.1f} %")

        mode = self.plc.mode
        self.lbl_mode_badge.configure(text=f"MODO: {mode}",
                                      bg=self._mode_badge_bg(mode))


# ============================================================
# PONTO DE ENTRADA
# ============================================================
if __name__ == "__main__":
    root = tk.Tk()
    root.title("SCADA - Estação de Furação FESTO | Login")
    root.geometry("1100x720")
    root.minsize(900, 600)
    root.configure(bg="#1e1e24")

    app_holder = {"app": None, "login": None}

    def show_login():
        for child in root.winfo_children():
            child.destroy()
        root.title("SCADA - Estação de Furação FESTO | Login")
        root.geometry("1100x720")
        root.minsize(900, 600)
        root.configure(bg="#1e1e24")
        app_holder["login"] = LoginScreen(root, on_login)
        app_holder["app"] = None

    def on_login(username):
        for child in root.winfo_children():
            child.destroy()
        root.geometry("1320x860")
        root.minsize(1150, 780)
        root.title("SCADA - Estação de Furação FESTO | Indústria 4.0 (UNIFEI)")
        app_holder["app"] = FestoScadaApp(root, username, on_logout=show_login)
        app_holder["login"] = None

    show_login()
    root.mainloop()
