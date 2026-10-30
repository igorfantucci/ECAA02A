"""
SCADA - Estação de Furação FESTO (Indústria 4.0)
Laboratório ECAA02A - UNIFEI
Simulador & Sistema Supervisório Completo em Python
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time
import math
import threading

class PlantPLCState:
    """
    Representação em tempo real da Memória do CLP GE Fanuc 90-30
    e dos atuadores/sensores físicos da bancada FESTO.
    """
    def __init__(self):
        # Entradas Físicas (%I) e Virtuais (%M)
        self.I_START = False         # %I0001 / %M0300
        self.I_RESET = False         # %I0002 / %M0304
        self.I_POSITION = False      # %I0003 / %M0302
        self.I_STOP = False          # %I0004 / %M0301
        self.I_AUTO_MANUAL = True    # %I0005 / %M0305 (True = Auto, False = Manual)
        self.I_AUTO_MANUAL_PHYS = True # Chave física local
        self.I_QUIT = False          # %I0006 / %M0303
        self.I_EMERGENCY = True      # %I0008 (NF: True = Normal/Fechado, False = Pressionado/Aberto)
        
        # Sensores de campo (%I)
        self.I_TABLE_IND = True      # %I0009 Sensor indutivo posição 90º da mesa (NA)
        self.I_DRILL_UP = True       # %I0010 Fim de curso superior furadeira (NA)
        self.I_DRILL_DOWN = False    # %I0011 Fim de curso inferior furadeira (NA)
        self.I_TEST_UP = True        # %I0012 Fim de curso superior do teste (NA)
        self.I_TEST_DOWN = False     # %I0013 Fim de curso inferior do teste (NA)
        self.I_CLAMP_RELEASED = True # %I0014 Peça liberada (NA)
        self.I_CLAMP_LOCKED = False  # %I0015 Peça travada (NA)
        self.I_PART_PRESENT = False  # %I0016 Sensor reflexivo presença na entrada (NA)

        # Saídas Físicas (%Q)
        self.Q_DRILL_MOTOR = False   # %Q0001 Motor rotação furadeira
        self.Q_TABLE_MOTOR = False   # %Q0002 Motor rotação mesa
        self.Q_DRILL_DOWN = False    # %Q0003 Solenoide descida furadeira
        self.Q_DRILL_UP = False      # %Q0004 Solenoide subida furadeira
        self.Q_TEST_DOWN = False     # %Q0005 Solenoide descida teste
        self.Q_CLAMP_LOCK = False    # %Q0006 Solenoide avanço trava

        # Registradores (%R)
        self.R_DRILLED_COUNT = 0     # %R0100 Peças furadas com sucesso
        self.R_REJECT_COUNT = 0      # %R0104 Peças não furadas / rejeitadas

        # Estado mecânico contínuo da planta (para renderização visual)
        # Posições na mesa: 0 = Entrada, 1 = Furação, 2 = Teste, 3 = Saída
        # Cada posição pode ter: None (vazio), ou dict com propriedades da peça
        self.table_slots = [None, None, None, None]
        self.table_angle = 0.0       # Ângulo atual da mesa (0 a 360 graus)
        self.target_table_angle = 0.0
        self.table_moving = False

        # Posição física da furadeira (0.0 = Topo, 1.0 = Fundo atingido)
        self.drill_pos = 0.0
        # Rotação da broca
        self.drill_rpm_angle = 0.0

        # Posição física da trava (0.0 = Liberada, 1.0 = Travada)
        self.clamp_pos = 0.0

        # Posição física do testador (0.0 = Topo, 1.0 = Fundo atingido)
        self.test_pos = 0.0

        # Lógica de controle interna do CLP
        self.mode = "STANDBY"        # STANDBY, AUTO_RUNNING, MANUAL, STOPPED, EMERGENCY
        self.auto_step = 0
        self.manual_step = 0
        self.test_timer_start = 0.0
        self.drill_spin_delay = 0.0

        # Injeção de defeitos para testes de validação
        self.fault_drill_blocked = False # Simula que a broca não consegue furar peça dura
        self.auto_feed_enabled = False   # Insere novas peças automaticamente

class FestoScadaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("SCADA - Estação de Furação FESTO | Indústria 4.0 (UNIFEI)")
        self.root.geometry("1260x820")
        self.root.minsize(1100, 750)
        self.root.configure(bg="#1e1e24")

        self.plc = PlantPLCState()
        self.log_messages = []

        self.setup_styles()
        self.build_ui()
        
        # Registrar evento de inicialização
        self.log_event("SISTEMA", "Supervisório SCADA iniciado. Comunicação simulador ativa.")

        # Iniciar thread/loop de execução de ciclo
        self.running = True
        self.after_id = self.root.after(40, self.update_cycle)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#1e1e24")
        style.configure("Header.TLabel", background="#1e1e24", foreground="#ffffff", font=("Segoe UI", 16, "bold"))
        style.configure("SubHeader.TLabel", background="#1e1e24", foreground="#a0a0b0", font=("Segoe UI", 10))
        style.configure("Panel.TFrame", background="#2b2b36", relief="ridge")
        style.configure("Card.TFrame", background="#23232c", relief="solid", borderwidth=1)
        style.configure("CardTitle.TLabel", background="#23232c", foreground="#61afef", font=("Segoe UI", 10, "bold"))
        style.configure("Value.TLabel", background="#23232c", foreground="#98c379", font=("Consolas", 14, "bold"))

    def build_ui(self):
        # 1. Top Bar / Header
        top_bar = tk.Frame(self.root, bg="#18181f", height=60)
        top_bar.pack(fill=tk.X, side=tk.TOP, padx=0, pady=0)

        title_box = tk.Frame(top_bar, bg="#18181f")
        title_box.pack(side=tk.LEFT, padx=16, pady=8)
        lbl_title = tk.Label(title_box, text="ESTAÇÃO DE FURAÇÃO FESTO", font=("Segoe UI", 14, "bold"), fg="#ffffff", bg="#18181f")
        lbl_title.pack(anchor="w")
        lbl_sub = tk.Label(title_box, text="UNIFEI • ECAA02A SCADA • CLP GE Fanuc Série 90-30 (SNP)", font=("Segoe UI", 9), fg="#8c8d9a", bg="#18181f")
        lbl_sub.pack(anchor="w")

        # Status do Modo e Comunicação no Header
        status_box = tk.Frame(top_bar, bg="#18181f")
        status_box.pack(side=tk.RIGHT, padx=16, pady=8)

        self.lbl_comm_status = tk.Label(status_box, text="● COM ONLINE (SNP: COM1/19200)", font=("Segoe UI", 9, "bold"), fg="#98c379", bg="#18181f")
        self.lbl_comm_status.pack(side=tk.RIGHT, padx=10)

        self.lbl_mode_badge = tk.Label(status_box, text="MODO: STANDBY", font=("Segoe UI", 10, "bold"), fg="#e5c07b", bg="#332e1d", padx=10, pady=4, relief="ridge")
        self.lbl_mode_badge.pack(side=tk.RIGHT, padx=10)

        # 2. Container Central dividido em duas colunas:
        # Coluna Esquerda: Sinótico Animado da Planta (Mesa, Furadeira, Testador, Sensores)
        # Coluna Direita: Painel de Controle Operacional, Tag Monitor e Alarmes
        main_container = tk.Frame(self.root, bg="#1e1e24")
        main_container.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)

        # Coluna Esquerda: Sinótico
        left_col = tk.Frame(main_container, bg="#262630", bd=1, relief="solid")
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 6))

        canvas_header = tk.Frame(left_col, bg="#202029", height=32)
        canvas_header.pack(fill=tk.X)
        tk.Label(canvas_header, text="SINÓTICO EM TEMPO REAL - BANCADA DE PROCESSO", font=("Segoe UI", 10, "bold"), fg="#abb2bf", bg="#202029").pack(side=tk.LEFT, padx=10, pady=4)

        # Canvas da Planta
        self.canvas = tk.Canvas(left_col, bg="#1a1a22", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Legenda do Canvas
        legend_frame = tk.Frame(left_col, bg="#202029", height=28)
        legend_frame.pack(fill=tk.X, padx=8, pady=(0, 8))
        tk.Label(legend_frame, text="Legenda: [E] Entrada  |  [F] Furação  |  [T] Teste de Furo  |  [S] Saída de Peças", font=("Segoe UI", 8), fg="#abb2bf", bg="#202029").pack(side=tk.LEFT, padx=8, pady=2)

        # Coluna Direita: Controles e Painéis
        right_col = tk.Frame(main_container, bg="#1e1e24", width=460)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(6, 0))
        right_col.pack_propagate(False)

        # 2.1 Painel de Contadores / KPIs
        kpi_frame = tk.Frame(right_col, bg="#23232c", bd=1, relief="solid")
        kpi_frame.pack(fill=tk.X, pady=(0, 8))
        
        tk.Label(kpi_frame, text="INDICADORES DE PRODUÇÃO (%R0100 / %R0104)", font=("Segoe UI", 9, "bold"), fg="#61afef", bg="#23232c").pack(anchor="w", padx=10, pady=(6, 4))
        
        kpi_grid = tk.Frame(kpi_frame, bg="#23232c")
        kpi_grid.pack(fill=tk.X, padx=10, pady=(0, 8))

        # KPI Aprovadas
        k1 = tk.Frame(kpi_grid, bg="#1d2d25", bd=1, relief="groove")
        k1.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 4))
        tk.Label(k1, text="FURADAS (OK)", font=("Segoe UI", 8, "bold"), fg="#98c379", bg="#1d2d25").pack(pady=(4, 0))
        self.lbl_kpi_ok = tk.Label(k1, text="0", font=("Consolas", 18, "bold"), fg="#98c379", bg="#1d2d25")
        self.lbl_kpi_ok.pack(pady=(0, 4))

        # KPI Rejeitadas
        k2 = tk.Frame(kpi_grid, bg="#331e21", bd=1, relief="groove")
        k2.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        tk.Label(k2, text="NÃO FURADAS (NOK)", font=("Segoe UI", 8, "bold"), fg="#e06c75", bg="#331e21").pack(pady=(4, 0))
        self.lbl_kpi_nok = tk.Label(k2, text="0", font=("Consolas", 18, "bold"), fg="#e06c75", bg="#331e21")
        self.lbl_kpi_nok.pack(pady=(0, 4))

        # KPI Total e Eficiência
        k3 = tk.Frame(kpi_grid, bg="#1e2638", bd=1, relief="groove")
        k3.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(4, 0))
        tk.Label(k3, text="TAXA APROVAÇÃO", font=("Segoe UI", 8, "bold"), fg="#61afef", bg="#1e2638").pack(pady=(4, 0))
        self.lbl_kpi_rate = tk.Label(k3, text="100 %", font=("Consolas", 18, "bold"), fg="#61afef", bg="#1e2638")
        self.lbl_kpi_rate.pack(pady=(0, 4))

        # 2.2 Painel de Comando da IHM (Botoeiras Virtuais %M)
        ctrl_frame = tk.Frame(right_col, bg="#23232c", bd=1, relief="solid")
        ctrl_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(ctrl_frame, text="BOTOEIRAS DO SUPERVISÓRIO (%M0300..%M0305)", font=("Segoe UI", 9, "bold"), fg="#61afef", bg="#23232c").pack(anchor="w", padx=10, pady=(6, 4))

        # Chave seletora Auto/Manual
        sel_row = tk.Frame(ctrl_frame, bg="#23232c")
        sel_row.pack(fill=tk.X, padx=10, pady=4)
        tk.Label(sel_row, text="Chave Auto/Manual (%M0305):", font=("Segoe UI", 9), fg="#abb2bf", bg="#23232c").pack(side=tk.LEFT)
        
        self.btn_mode_auto = tk.Button(sel_row, text="AUTOMÁTICO", font=("Segoe UI", 8, "bold"), bg="#355c3d", fg="#ffffff", activebackground="#45784f", relief="raised", bd=2, command=self.cmd_set_auto)
        self.btn_mode_auto.pack(side=tk.RIGHT, padx=2)
        self.btn_mode_manual = tk.Button(sel_row, text="MANUAL", font=("Segoe UI", 8, "bold"), bg="#414552", fg="#ffffff", activebackground="#565c6d", relief="raised", bd=2, command=self.cmd_set_manual)
        self.btn_mode_manual.pack(side=tk.RIGHT, padx=2)

        # Botões operacionais (START, STOP, RESET, QUIT, POSITION, EMERGENCY)
        btn_grid1 = tk.Frame(ctrl_frame, bg="#23232c")
        btn_grid1.pack(fill=tk.X, padx=10, pady=4)

        self.btn_start = tk.Button(btn_grid1, text="START (%M0300)", font=("Segoe UI", 9, "bold"), bg="#2d6930", fg="#ffffff", activebackground="#3d8e41", height=2, relief="raised", bd=3, command=self.cmd_start)
        self.btn_start.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_stop = tk.Button(btn_grid1, text="STOP (%M0301)", font=("Segoe UI", 9, "bold"), bg="#8f2d2d", fg="#ffffff", activebackground="#b83939", height=2, relief="raised", bd=3, command=self.cmd_stop)
        self.btn_stop.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_reset = tk.Button(btn_grid1, text="RESET (%M0304)", font=("Segoe UI", 9, "bold"), bg="#826620", fg="#ffffff", activebackground="#a68429", height=2, relief="raised", bd=3, command=self.cmd_reset)
        self.btn_reset.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        btn_grid2 = tk.Frame(ctrl_frame, bg="#23232c")
        btn_grid2.pack(fill=tk.X, padx=10, pady=(2, 6))

        self.btn_pos = tk.Button(btn_grid2, text="POSITION (%M0302)", font=("Segoe UI", 8, "bold"), bg="#3b4048", fg="#ffffff", activebackground="#4e5560", relief="raised", bd=2, command=self.cmd_position)
        self.btn_pos.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))

        self.btn_quit = tk.Button(btn_grid2, text="QUIT (%M0303)", font=("Segoe UI", 8, "bold"), bg="#3b4048", fg="#ffffff", activebackground="#4e5560", relief="raised", bd=2, command=self.cmd_quit)
        self.btn_quit.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=3)

        self.btn_emerg = tk.Button(btn_grid2, text="EMERGÊNCIA", font=("Segoe UI", 8, "bold"), bg="#bd1919", fg="#ffffff", activebackground="#e62020", relief="raised", bd=2, command=self.cmd_emergency)
        self.btn_emerg.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(3, 0))

        # 2.3 Simulação de Planta / Injeção de Peças e Falhas
        sim_frame = tk.Frame(right_col, bg="#23232c", bd=1, relief="solid")
        sim_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(sim_frame, text="INTERAÇÃO DE BANCADA & ALIMENTAÇÃO", font=("Segoe UI", 9, "bold"), fg="#d19a66", bg="#23232c").pack(anchor="w", padx=10, pady=(6, 4))
        
        sim_row = tk.Frame(sim_frame, bg="#23232c")
        sim_row.pack(fill=tk.X, padx=10, pady=(0, 6))

        btn_feed = tk.Button(sim_row, text="＋ Inserir Peça na Entrada", font=("Segoe UI", 8, "bold"), bg="#2e4d6d", fg="#ffffff", relief="groove", command=self.cmd_insert_piece)
        btn_feed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))

        self.btn_autofeed = tk.Button(sim_row, text="Auto-Alimentação: OFF", font=("Segoe UI", 8), bg="#3b4048", fg="#dcdfe4", relief="groove", command=self.cmd_toggle_autofeed)
        self.btn_autofeed.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)

        self.btn_fault = tk.Button(sim_row, text="Falha de Furo: OFF", font=("Segoe UI", 8), bg="#3b4048", fg="#dcdfe4", relief="groove", command=self.cmd_toggle_fault)
        self.btn_fault.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(4, 0))

        # 2.4 Monitor de Tags de I/O em tempo real
        io_frame = tk.Frame(right_col, bg="#23232c", bd=1, relief="solid")
        io_frame.pack(fill=tk.X, pady=(0, 8))

        tk.Label(io_frame, text="DIAGNÓSTICO DE I/O (%I e %Q)", font=("Segoe UI", 9, "bold"), fg="#61afef", bg="#23232c").pack(anchor="w", padx=10, pady=(6, 4))

        self.led_canvas = tk.Canvas(io_frame, bg="#1a1a22", height=135, highlightthickness=0)
        self.led_canvas.pack(fill=tk.X, padx=8, pady=(0, 6))

        # 2.5 Log de Eventos e Alarmes
        log_frame = tk.Frame(right_col, bg="#23232c", bd=1, relief="solid")
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="HISTÓRICO DE EVENTOS E ALARMES", font=("Segoe UI", 9, "bold"), fg="#e5c07b", bg="#23232c").pack(anchor="w", padx=10, pady=(6, 2))

        self.log_listbox = tk.Listbox(log_frame, bg="#181820", fg="#abb2bf", font=("Consolas", 8), selectbackground="#2c313a", relief="flat")
        self.log_listbox.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 6))

    def log_event(self, source, msg):
        t_str = time.strftime("%H:%M:%S")
        entry = f"[{t_str}] [{source}] {msg}"
        self.log_messages.append(entry)
        if hasattr(self, 'log_listbox'):
            self.log_listbox.insert(tk.END, entry)
            self.log_listbox.see(tk.END)

    # Comandos dos botões da IHM
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
        # Desliga todos os atuadores imediatamente
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
                self.log_event("MANUAL", "Comando POSITION (%M0302): Iniciando avanço de 90° na mesa.")
            else:
                self.log_event("MANUAL", "Mesa já em movimento.")
        else:
            self.log_event("ALERTA", "Comando POSITION só opera em modo MANUAL.")

    def cmd_quit(self):
        self.plc.I_QUIT = True
        if self.plc.mode == "AUTO_RUNNING":
            # Verificar se não há mais peças
            has_pieces = any(slot is not None for slot in self.plc.table_slots) or self.plc.I_PART_PRESENT
            if not has_pieces:
                self.plc.mode = "STANDBY"
                self.log_event("IHM", "Comando QUIT (%M0303): Modo automático desabilitado (Planta vazia).")
            else:
                self.log_event("IHM", "QUIT solicitado: Sistema finalizará as peças atuais antes de parar.")

    def cmd_emergency(self):
        # Toggle emergência
        self.plc.I_EMERGENCY = not self.plc.I_EMERGENCY
        if not self.plc.I_EMERGENCY:
            self.plc.mode = "EMERGENCY"
            self.plc.Q_DRILL_MOTOR = False
            self.plc.Q_TABLE_MOTOR = False
            self.plc.Q_DRILL_DOWN = False
            self.plc.Q_DRILL_UP = False
            self.plc.Q_TEST_DOWN = False
            self.plc.Q_CLAMP_LOCK = False
            self.btn_emerg.configure(bg="#ff0000", text="EMERGÊNCIA ATIVA!")
            self.log_event("ALARME CRÍTICO", "BOTAO DE EMERGÊNCIA %I0008 ACIONADO!")
        else:
            self.plc.mode = "STANDBY"
            self.btn_emerg.configure(bg="#bd1919", text="EMERGÊNCIA")
            self.log_event("SEGURANÇA", "Emergência desarmada. Pressione RESET/START para reiniciar.")

    def cmd_set_auto(self):
        # Prioridade da chave física manual sobre virtual
        if not self.plc.I_AUTO_MANUAL_PHYS:
            self.log_event("BLOQUEIO", "Comando rejeitado: Chave física local está em MANUAL (prioritária).")
            return
        self.plc.I_AUTO_MANUAL = True
        self.btn_mode_auto.configure(bg="#355c3d")
        self.btn_mode_manual.configure(bg="#414552")
        self.log_event("IHM", "Modo selecionado no Supervisório: AUTOMÁTICO.")

    def cmd_set_manual(self):
        self.plc.I_AUTO_MANUAL = False
        self.plc.mode = "MANUAL"
        self.btn_mode_auto.configure(bg="#414552")
        self.btn_mode_manual.configure(bg="#6e622b")
        # Desliga motores de furação e teste caso estivessem ligados
        self.plc.Q_DRILL_MOTOR = False
        self.plc.Q_DRILL_DOWN = False
        self.plc.Q_TEST_DOWN = False
        self.plc.Q_CLAMP_LOCK = False
        self.log_event("IHM", "Modo selecionado: MANUAL. Apenas rotações por POSITION permitidas.")

    def cmd_insert_piece(self):
        if self.plc.table_slots[0] is None:
            self.plc.table_slots[0] = {
                "drilled": False,
                "tested": False,
                "ok": False,
                "id": len(self.log_messages) + 1
            }
            self.plc.I_PART_PRESENT = True
            self.log_event("ALIMENTAÇÃO", "Peça bruta inserida na estação de ENTRADA.")
        else:
            self.log_event("ALERTA", "Posição de ENTRADA já ocupada!")

    def cmd_toggle_autofeed(self):
        self.plc.auto_feed_enabled = not self.plc.auto_feed_enabled
        if self.plc.auto_feed_enabled:
            self.btn_autofeed.configure(bg="#2e6d44", text="Auto-Alimentação: ON")
            self.log_event("SIMULAÇÃO", "Alimentação contínua de peças ativada.")
        else:
            self.btn_autofeed.configure(bg="#3b4048", text="Auto-Alimentação: OFF")
            self.log_event("SIMULAÇÃO", "Alimentação contínua desativada.")

    def cmd_toggle_fault(self):
        self.plc.fault_drill_blocked = not self.plc.fault_drill_blocked
        if self.plc.fault_drill_blocked:
            self.btn_fault.configure(bg="#8f2d2d", text="Falha de Furo: ON")
            self.log_event("DEFEITO", "Injeção de defeito ATIVA: Próxima furação falhará (peça não furada).")
        else:
            self.btn_fault.configure(bg="#3b4048", text="Falha de Furo: OFF")
            self.log_event("DEFEITO", "Injeção de defeito desativada.")

    # Loop de automação física e controle PLC
    def update_cycle(self):
        if not self.running:
            return

        # 1. Executar lógica do CLP
        self.step_plc_logic()

        # 2. Executar física mecânica da planta
        self.step_physical_plant()

        # 3. Desenhar no Canvas e atualizar indicadores
        self.render_synoptic()
        self.render_io_leds()
        self.update_kpis()

        # Agendar próximo ciclo
        self.after_id = self.root.after(40, self.update_cycle)

    def step_plc_logic(self):
        # Se emergência ou stop ativo, não avança sequências
        if self.plc.mode in ["EMERGENCY", "STOPPED"]:
            return

        # Atualizar sensor de presença na entrada
        self.plc.I_PART_PRESENT = (self.plc.table_slots[0] is not None)

        # Auto-alimentação
        if self.plc.auto_feed_enabled and self.plc.mode == "AUTO_RUNNING":
            if self.plc.table_slots[0] is None and not self.plc.table_moving:
                self.plc.table_slots[0] = {
                    "drilled": False,
                    "tested": False,
                    "ok": False,
                    "id": int(time.time() * 10) % 1000
                }
                self.plc.I_PART_PRESENT = True

        # Máquina de Estados no modo AUTOMÁTICO
        if self.plc.mode == "AUTO_RUNNING":
            # Passo 0: Aguardando condições para iniciar rotação ou processamento
            if self.plc.auto_step == 0:
                # Verifica se há peças na mesa
                has_work = any(slot is not None for slot in self.plc.table_slots)
                
                # Se há peça na entrada ou em trânsito, e mesa parada com atuadores recuados:
                if (has_work or self.plc.I_PART_PRESENT) and not self.plc.table_moving:
                    # Garantir atuadores recuados antes de girar
                    if self.plc.I_DRILL_UP and self.plc.I_TEST_UP and self.plc.I_CLAMP_RELEASED:
                        # Se há peça na posição de Furação que ainda não foi furada, OU
                        # se há peça na posição de Teste que ainda não foi testada:
                        need_drill = (self.plc.table_slots[1] is not None and not self.plc.table_slots[1]["drilled"])
                        need_test = (self.plc.table_slots[2] is not None and not self.plc.table_slots[2]["tested"])

                        if need_drill or need_test:
                            # Executar operações de bancada (podem ser simultâneas!)
                            self.plc.auto_step = 20
                        else:
                            # Pode girar a mesa para a próxima posição
                            # Mas primeiro descarta peça que chegou na saída
                            if self.plc.table_slots[3] is not None:
                                p = self.plc.table_slots[3]
                                self.log_event("SAÍDA", f"Peça #{p['id']} coletada na estação de Saída (Status: {'OK' if p['ok'] else 'REJEITO'}).")
                                self.plc.table_slots[3] = None

                            # Iniciar rotação de 90°
                            self.plc.auto_step = 10
                            self.plc.Q_TABLE_MOTOR = True
                            self.plc.table_moving = True
                            self.plc.target_table_angle = (self.plc.table_angle + 90.0) % 360.0
                            self.log_event("MESA", "Avanço de 90° iniciado pelo ciclo automático.")

            # Passo 10: Aguardando mesa terminar rotação de 90°
            elif self.plc.auto_step == 10:
                if not self.plc.table_moving and self.plc.I_TABLE_IND:
                    self.plc.Q_TABLE_MOTOR = False
                    # Rotacionar array de peças na mesa: slot 3 sai, 2->3, 1->2, 0->1, 0 fica None
                    self.plc.table_slots = [None, self.plc.table_slots[0], self.plc.table_slots[1], self.plc.table_slots[2]]
                    self.log_event("MESA", "Posicionamento 90° concluído (Sensor Indutivo %I0009 atuado).")
                    self.plc.auto_step = 0

            # Passo 20: Executar Furação e/ou Teste (Simultâneos ou Individuais)
            elif self.plc.auto_step == 20:
                # 20.1 Controle da Furadeira
                p_drill = self.plc.table_slots[1]
                if p_drill is not None and not p_drill["drilled"]:
                    # Travar peça se ainda não travou
                    if not self.plc.I_CLAMP_LOCKED:
                        self.plc.Q_CLAMP_LOCK = True
                    else:
                        # Peça travada -> ligar motor da furadeira
                        self.plc.Q_DRILL_MOTOR = True
                        if self.plc.drill_spin_delay < 1.0:
                            self.plc.drill_spin_delay += 0.05
                        else:
                            # Velocidade nominal atingida -> descer furadeira
                            if not self.plc.fault_drill_blocked:
                                self.plc.Q_DRILL_DOWN = True
                                self.plc.Q_DRILL_UP = False
                            else:
                                # Simula broca presa / peça muito dura que não atinge fim de curso
                                self.plc.Q_DRILL_DOWN = True
                                self.plc.Q_DRILL_UP = False

                            # Quando atingir fim de curso inferior
                            if self.plc.I_DRILL_DOWN:
                                p_drill["drilled"] = True
                                self.log_event("FURAÇÃO", f"Furo concluído na peça #{p_drill['id']}. Subindo furadeira.")

                # Se a peça na furação já furou (ou não havia peça), recuar furadeira
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
                                # Concluiu tentativa com falha
                                p_drill["drilled"] = True
                                self.log_event("FURAÇÃO", f"Furadeira abortou descida (Peça #{p_drill['id']} com defeito de dureza).")

                # 20.2 Controle do Testador
                p_test = self.plc.table_slots[2]
                if p_test is not None and not p_test["tested"]:
                    # Descer provador do furo
                    self.plc.Q_TEST_DOWN = True
                    if self.plc.test_timer_start == 0.0:
                        self.plc.test_timer_start = time.time()

                    elapsed = time.time() - self.plc.test_timer_start
                    # Teste 1: Fim de curso inferior atingido?
                    if self.plc.I_TEST_DOWN:
                        p_test["tested"] = True
                        p_test["ok"] = True
                        self.plc.R_DRILLED_COUNT += 1
                        self.log_event("TESTE", f"Peça #{p_test['id']} APROVADA! (Furo verificado com sucesso - %R0100={self.plc.R_DRILLED_COUNT}).")
                        self.plc.Q_TEST_DOWN = False
                        self.plc.test_timer_start = 0.0
                    elif elapsed >= 3.0:
                        # Timeout de 3 segundos atingido sem atingir o sensor inferior -> REJEITADA
                        p_test["tested"] = True
                        p_test["ok"] = False
                        self.plc.R_REJECT_COUNT += 1
                        self.log_event("TESTE", f"Peça #{p_test['id']} REJEITADA! (Timeout 3s sem atingir sensor - %R0104={self.plc.R_REJECT_COUNT}).")
                        self.plc.Q_TEST_DOWN = False
                        self.plc.test_timer_start = 0.0
                else:
                    self.plc.Q_TEST_DOWN = False
                    self.plc.test_timer_start = 0.0

                # 20.3 Verificar se ambas as operações finalizaram
                drill_done = (p_drill is None or (p_drill["drilled"] and self.plc.I_DRILL_UP and self.plc.I_CLAMP_RELEASED))
                test_done = (p_test is None or (p_test["tested"] and self.plc.I_TEST_UP))

                if drill_done and test_done:
                    # Ambas concluíram com segurança! Retorna ao passo 0
                    self.plc.auto_step = 0

    def step_physical_plant(self):
        # 1. Movimento da mesa rotativa
        if self.plc.table_moving:
            diff = (self.plc.target_table_angle - self.plc.table_angle) % 360.0
            if diff > 0.1 and diff <= 95.0:
                self.plc.table_angle = (self.plc.table_angle + 6.0) % 360.0
                self.plc.I_TABLE_IND = False
            else:
                self.plc.table_angle = self.plc.target_table_angle
                self.plc.table_moving = False
                self.plc.Q_TABLE_MOTOR = False
                self.plc.I_TABLE_IND = True

        # 2. Movimento da furadeira
        if self.plc.Q_DRILL_DOWN and not self.plc.Q_DRILL_UP:
            if self.plc.fault_drill_blocked:
                # Trava a descida na metade (não atinge 1.0)
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
        
        # Sensores de fim de curso da furadeira
        self.plc.I_DRILL_UP = (self.plc.drill_pos <= 0.05)
        self.plc.I_DRILL_DOWN = (self.plc.drill_pos >= 0.95)

        # Rotação da broca
        if self.plc.Q_DRILL_MOTOR:
            self.plc.drill_rpm_angle = (self.plc.drill_rpm_angle + 30.0) % 360.0

        # 3. Movimento da trava pneumática
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

        # 4. Movimento do provador de teste
        if self.plc.Q_TEST_DOWN:
            # Se a peça embaixo foi furada com sucesso, a haste desce até o fim (1.0)
            p_test = self.plc.table_slots[2]
            target_depth = 1.0 if (p_test and p_test.get("drilled", False) and not self.plc.fault_drill_blocked) else 0.4
            if self.plc.test_pos < target_depth:
                self.plc.test_pos += 0.06
                if self.plc.test_pos >= target_depth:
                    self.plc.test_pos = target_depth
        else:
            # Retorno por mola
            if self.plc.test_pos > 0.0:
                self.plc.test_pos -= 0.1
                if self.plc.test_pos <= 0.0:
                    self.plc.test_pos = 0.0

        self.plc.I_TEST_UP = (self.plc.test_pos <= 0.05)
        self.plc.I_TEST_DOWN = (self.plc.test_pos >= 0.95)

    # Renderização Gráfica do Sinótico da Planta
    def render_synoptic(self):
        c = self.canvas
        w = c.winfo_width()
        h = c.winfo_height()
        if w < 100 or h < 100:
            return

        c.delete("all")

        # Fundo do sinótico com grade técnica sutil
        c.create_rectangle(0, 0, w, h, fill="#181822", outline="")
        for gx in range(0, w, 40):
            c.create_line(gx, 0, gx, h, fill="#1f1f2e", width=1)
        for gy in range(0, h, 40):
            c.create_line(0, gy, w, gy, fill="#1f1f2e", width=1)

        # Coordenadas centrais da mesa rotativa
        cx = w * 0.48
        cy = h * 0.52
        table_r = min(w, h) * 0.32

        # 1. Base metálica estática da mesa
        c.create_oval(cx - table_r - 18, cy - table_r - 18, cx + table_r + 18, cy + table_r + 18, fill="#2a2b36", outline="#3c3f50", width=3)
        c.create_oval(cx - table_r, cy - table_r, cx + table_r, cy + table_r, fill="#343746", outline="#52576b", width=2)

        # Divisões em 4 quadrantes da mesa com rotação
        rad = math.radians(self.plc.table_angle)
        for i in range(4):
            a = rad + (i * math.pi / 2.0)
            ex = cx + table_r * math.cos(a)
            ey = cy + table_r * math.sin(a)
            c.create_line(cx, cy, ex, ey, fill="#20222b", width=2, dash=(4, 2))

        # Cubo central da mesa
        c.create_oval(cx - 30, cy - 30, cx + 30, cy + 30, fill="#222430", outline="#61afef", width=2)
        c.create_text(cx, cy, text="MESA\nINDEX", font=("Segoe UI", 7, "bold"), fill="#61afef", justify="center")

        # Sensor indutivo na mesa (%I0009)
        c.create_rectangle(cx + table_r + 4, cy - 10, cx + table_r + 26, cy + 10, fill="#3a3d4d", outline="#e5c07b", width=1)
        c.create_oval(cx + table_r + 7, cy - 5, cx + table_r + 17, cy + 5, fill="#98c379" if self.plc.I_TABLE_IND else "#4b5263", outline="")
        c.create_text(cx + table_r + 34, cy, text="%I0009\nIndutivo", font=("Consolas", 7), fill="#e5c07b", anchor="w")

        # 4 Posições da Mesa:
        # Posição 0: Entrada (À esquerda, 180° ou topo esquerdo)
        # Vamos definir as 4 estações ao redor da mesa:
        # 0: Entrada (Oeste / 180°)
        # 1: Furação (Norte / 270°)
        # 2: Teste (Leste / 0°)
        # 3: Saída (Sul / 90°)
        station_angles = [math.pi, 3 * math.pi / 2.0, 0.0, math.pi / 2.0]
        station_names = ["1. ENTRADA", "2. FURAÇÃO", "3. TESTE", "4. SAÍDA"]

        for idx, (s_ang, s_name) in enumerate(zip(station_angles, station_names)):
            sx = cx + (table_r * 0.65) * math.cos(s_ang)
            sy = cy + (table_r * 0.65) * math.sin(s_ang)

            # Marcador de nicho da peça na mesa
            c.create_oval(sx - 24, sy - 24, sx + 24, sy + 24, fill="#22242e", outline="#4b5263", width=2)
            c.create_text(sx, sy, text=f"P{idx+1}", font=("Segoe UI", 8, "bold"), fill="#5c6370")

            # Desenha a peça se houver
            piece = self.plc.table_slots[idx]
            if piece is not None:
                p_color = "#98c379" if piece.get("ok") else ("#d19a66" if piece.get("drilled") else "#61afef")
                c.create_oval(sx - 18, sy - 18, sx + 18, sy + 18, fill=p_color, outline="#ffffff", width=2)
                
                # Furo no meio se furada
                if piece.get("drilled"):
                    c.create_oval(sx - 6, sy - 6, sx + 6, sy + 6, fill="#181822", outline="#282c34", width=1)
                
                c.create_text(sx, sy + 1, text=f"#{piece['id']}", font=("Segoe UI", 7, "bold"), fill="#181822")

        # Rótulos externos das 4 Estações
        # Estação 1: Entrada
        p1_x = cx - table_r - 80
        p1_y = cy
        c.create_rectangle(p1_x - 45, p1_y - 25, p1_x + 45, p1_y + 25, fill="#21252b", outline="#61afef", width=1)
        c.create_text(p1_x, p1_y - 8, text="[ ENTRADA ]", font=("Segoe UI", 8, "bold"), fill="#61afef")
        sensor_ent_color = "#98c379" if self.plc.I_PART_PRESENT else "#4b5263"
        c.create_oval(p1_x - 30, p1_y + 4, p1_x - 18, p1_y + 16, fill=sensor_ent_color, outline="")
        c.create_text(p1_x - 10, p1_y + 10, text="%I0016 Reflex.", font=("Consolas", 7), fill="#abb2bf", anchor="w")

        # Estação 2: Furação (Norte)
        p2_x = cx
        p2_y = cy - table_r - 70
        c.create_rectangle(p2_x - 90, p2_y - 45, p2_x + 90, p2_y + 45, fill="#21252b", outline="#e5c07b", width=1)
        c.create_text(p2_x, p2_y - 30, text="[ ESTAÇÃO DE FURAÇÃO ]", font=("Segoe UI", 8, "bold"), fill="#e5c07b")
        
        # Representação gráfica da Furadeira e Pistão
        drill_col_x = p2_x - 35
        # Cilindro da furadeira
        c.create_rectangle(drill_col_x - 12, p2_y - 18, drill_col_x + 12, p2_y + 20, fill="#3e4451", outline="#5c6370")
        # Haste móvel
        drill_head_y = p2_y - 10 + (self.plc.drill_pos * 30)
        c.create_rectangle(drill_col_x - 4, p2_y - 18, drill_col_x + 4, drill_head_y, fill="#abb2bf", outline="")
        # Broca / Motor
        motor_col = "#98c379" if self.plc.Q_DRILL_MOTOR else "#5c6370"
        c.create_oval(drill_col_x - 10, drill_head_y, drill_col_x + 10, drill_head_y + 14, fill=motor_col, outline="#ffffff" if self.plc.Q_DRILL_MOTOR else "")
        c.create_line(drill_col_x, drill_head_y + 14, drill_col_x, drill_head_y + 26, fill="#abb2bf", width=2)

        # Sensores de fim de curso da furadeira
        c.create_oval(drill_col_x + 16, p2_y - 14, drill_col_x + 24, p2_y - 6, fill="#98c379" if self.plc.I_DRILL_UP else "#4b5263", outline="")
        c.create_text(drill_col_x + 28, p2_y - 10, text="%I0010 (Sup)", font=("Consolas", 7), fill="#abb2bf", anchor="w")
        c.create_oval(drill_col_x + 16, p2_y + 10, drill_col_x + 24, p2_y + 18, fill="#98c379" if self.plc.I_DRILL_DOWN else "#4b5263", outline="")
        c.create_text(drill_col_x + 28, p2_y + 14, text="%I0011 (Inf)", font=("Consolas", 7), fill="#abb2bf", anchor="w")

        # Trava Pneumática da Peça (%Q0006)
        clamp_x = p2_x + 45
        clamp_ext = self.plc.clamp_pos * 14
        c.create_rectangle(clamp_x, p2_y - 4, clamp_x + 28, p2_y + 16, fill="#2c313a", outline="#61afef")
        c.create_rectangle(clamp_x - clamp_ext, p2_y + 1, clamp_x, p2_y + 11, fill="#98c379" if self.plc.I_CLAMP_LOCKED else "#e5c07b", outline="")
        c.create_text(clamp_x + 14, p2_y + 26, text="Trava %Q0006", font=("Consolas", 7), fill="#abb2bf")

        # Estação 3: Teste (Leste)
        p3_x = cx + table_r + 90
        p3_y = cy
        c.create_rectangle(p3_x - 45, p3_y - 50, p3_x + 85, p3_y + 50, fill="#21252b", outline="#98c379", width=1)
        c.create_text(p3_x + 20, p3_y - 36, text="[ TESTE DO FURO ]", font=("Segoe UI", 8, "bold"), fill="#98c379")

        # Cilindro de teste
        test_col_x = p3_x - 15
        c.create_rectangle(test_col_x - 8, p3_y - 20, test_col_x + 8, p3_y + 15, fill="#3e4451", outline="#5c6370")
        test_probe_y = p3_y - 15 + (self.plc.test_pos * 35)
        c.create_line(test_col_x, p3_y - 20, test_col_x, test_probe_y + 20, fill="#61afef", width=3)
        c.create_oval(test_col_x - 3, test_probe_y + 20, test_col_x + 3, test_probe_y + 26, fill="#ffffff", outline="")

        # Sensores de fim de curso do teste
        c.create_oval(test_col_x + 16, p3_y - 18, test_col_x + 24, p3_y - 10, fill="#98c379" if self.plc.I_TEST_UP else "#4b5263", outline="")
        c.create_text(test_col_x + 28, p3_y - 14, text="%I0012 (Sup)", font=("Consolas", 7), fill="#abb2bf", anchor="w")
        c.create_oval(test_col_x + 16, p3_y + 6, test_col_x + 24, p3_y + 14, fill="#98c379" if self.plc.I_TEST_DOWN else "#4b5263", outline="")
        c.create_text(test_col_x + 28, p3_y + 10, text="%I0013 (Inf)", font=("Consolas", 7), fill="#abb2bf", anchor="w")

        # Temporizador de 3s
        if self.plc.test_timer_start > 0:
            elapsed = min(3.0, time.time() - self.plc.test_timer_start)
            c.create_text(p3_x + 20, p3_y + 36, text=f"Tempo: {elapsed:.1f}s / 3.0s", font=("Consolas", 8, "bold"), fill="#e5c07b")

        # Estação 4: Saída (Sul)
        p4_x = cx
        p4_y = cy + table_r + 65
        c.create_rectangle(p4_x - 55, p4_y - 20, p4_x + 55, p4_y + 20, fill="#21252b", outline="#c678dd", width=1)
        c.create_text(p4_x, p4_y, text="[ SAÍDA DE PEÇAS ]", font=("Segoe UI", 8, "bold"), fill="#c678dd")

    # Painel inferior de LEDs de diagnóstico de I/O
    def render_io_leds(self):
        c = self.led_canvas
        w = c.winfo_width()
        if w < 100:
            return
        c.delete("all")

        # Lista de Entradas (%I)
        inputs = [
            ("%I0001", "START", self.plc.I_START),
            ("%I0002", "RESET", self.plc.I_RESET),
            ("%I0003", "POSIT.", self.plc.I_POSITION),
            ("%I0004", "STOP", self.plc.I_STOP),
            ("%I0005", "CHAVE", self.plc.I_AUTO_MANUAL),
            ("%I0008", "EMERG", self.plc.I_EMERGENCY),
            ("%I0009", "MESA", self.plc.I_TABLE_IND),
            ("%I0010", "FUR.S", self.plc.I_DRILL_UP),
            ("%I0011", "FUR.I", self.plc.I_DRILL_DOWN),
            ("%I0012", "TST.S", self.plc.I_TEST_UP),
            ("%I0013", "TST.I", self.plc.I_TEST_DOWN),
            ("%I0015", "TRAVA", self.plc.I_CLAMP_LOCKED),
            ("%I0016", "PRES.", self.plc.I_PART_PRESENT),
        ]

        # Lista de Saídas (%Q)
        outputs = [
            ("%Q0001", "M.FUR", self.plc.Q_DRILL_MOTOR),
            ("%Q0002", "M.MES", self.plc.Q_TABLE_MOTOR),
            ("%Q0003", "S.DEC", self.plc.Q_DRILL_DOWN),
            ("%Q0004", "S.SUB", self.plc.Q_DRILL_UP),
            ("%Q0005", "S.TST", self.plc.Q_TEST_DOWN),
            ("%Q0006", "S.TRV", self.plc.Q_CLAMP_LOCK),
        ]

        # Linha 1: Entradas %I
        c.create_text(10, 18, text="ENTRADAS %I:", font=("Segoe UI", 7, "bold"), fill="#61afef", anchor="w")
        x_start = 85
        col_w = 32
        for i, (addr, name, val) in enumerate(inputs):
            x = x_start + (i * col_w)
            color = "#98c379" if val else "#3b4048"
            c.create_oval(x, 10, x + 12, 22, fill=color, outline="#21252b")
            c.create_text(x + 6, 28, text=name, font=("Segoe UI", 6), fill="#828997")
            c.create_text(x + 6, 37, text=addr[2:], font=("Consolas", 6), fill="#5c6370")

        # Linha 2: Saídas %Q
        c.create_text(10, 68, text="SAÍDAS %Q:", font=("Segoe UI", 7, "bold"), fill="#e5c07b", anchor="w")
        x_start_q = 85
        for i, (addr, name, val) in enumerate(outputs):
            x = x_start_q + (i * 44)
            color = "#e5c07b" if val else "#3b4048"
            c.create_oval(x, 60, x + 12, 72, fill=color, outline="#21252b")
            c.create_text(x + 6, 78, text=name, font=("Segoe UI", 6), fill="#abb2bf")
            c.create_text(x + 6, 87, text=addr, font=("Consolas", 6), fill="#5c6370")

        # Resetar pulsos momentâneos
        self.plc.I_START = False
        self.plc.I_STOP = False
        self.plc.I_RESET = False
        self.plc.I_POSITION = False
        self.plc.I_QUIT = False

    def update_kpis(self):
        # Atualizar contadores
        self.lbl_kpi_ok.configure(text=str(self.plc.R_DRILLED_COUNT))
        self.lbl_kpi_nok.configure(text=str(self.plc.R_REJECT_COUNT))
        total = self.plc.R_DRILLED_COUNT + self.plc.R_REJECT_COUNT
        rate = (self.plc.R_DRILLED_COUNT / total * 100.0) if total > 0 else 100.0
        self.lbl_kpi_rate.configure(text=f"{rate:.1f} %")

        # Atualizar badge de modo
        mode_text = f"MODO: {self.plc.mode}"
        if self.plc.mode == "AUTO_RUNNING":
            bg = "#1b4427"
            fg = "#98c379"
        elif self.plc.mode == "MANUAL":
            bg = "#473b18"
            fg = "#e5c07b"
        elif self.plc.mode == "EMERGENCY":
            bg = "#5c1d1d"
            fg = "#ff6b6b"
        elif self.plc.mode == "STOPPED":
            bg = "#3d2222"
            fg = "#e06c75"
        else:
            bg = "#282c34"
            fg = "#abb2bf"

        self.lbl_mode_badge.configure(text=mode_text, bg=bg, fg=fg)

if __name__ == "__main__":
    root = tk.Tk()
    app = FestoScadaApp(root)
    root.mainloop()
