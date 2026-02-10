"""
SORTER ANALYZER - Production Version
Simplified light-mode only application with CSV export
"""

import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import font as tkfont
import pandas as pd
from typing import List, Tuple, Optional
from datetime import datetime

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from config import load_settings, save_settings, DEFAULT_FOLDER, DEFAULT_NR_LIST, DEFAULT_MONITOR_INTERVAL_SEC
from files_io import list_alarmlog_files, find_today_alarmlog


# ==================== HELPER FUNCTIONS ====================
def parse_duration_to_seconds(duration_str: str) -> float:
    """Konwertuje HH:MM:SS na sekundy"""
    try:
        h, m, s = duration_str.split(':')
        return int(h) * 3600 + int(m) * 60 + float(s)
    except:
        return 0.0


def format_seconds_to_duration(seconds: float) -> str:
    """Formatuje sekundy na HH:MM:SS"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def calculate_shift(time_str: str) -> Optional[int]:
    """Oblicza zmianę (1 lub 2)"""
    if pd.isna(time_str):
        return None
    if '06:07:00' <= time_str <= '14:15:00':
        return 1
    elif '14:20:00' <= time_str <= '22:30:00':
        return 2
    return None


def analyze_data(file_path: str, nr_list: List[int], query_mode: str) -> Tuple[List[str], List[tuple]]:
    """Główna analiza danych z Pandas"""
    df = pd.read_csv(
        file_path,
        sep=';',
        names=['start', 'status', 'nr', 'alarm', 'duration'],
        encoding='utf-8'
    )
    
    df['nr'] = pd.to_numeric(df['nr'], errors='coerce')
    
    # Filtrowanie
    filtered = df[
        (df['status'] == 'OK') &
        (df['nr'].isin(nr_list))
    ].copy()
    
    filtered['shift'] = filtered['start'].apply(calculate_shift)
    filtered = filtered[filtered['shift'].notna()]
    filtered['dur_sec'] = filtered['duration'].apply(parse_duration_to_seconds)
    filtered['alarm_first'] = filtered['alarm'].str.split().str[0].fillna('-')
    
    if query_mode == 'total':
        filtered['shift'] = 'total'
        grouped = filtered.groupby(['shift', 'status', 'nr'], as_index=False).agg({
            'alarm_first': 'first',
            'dur_sec': 'sum',
            'alarm': 'count'
        })
        grouped.columns = ['shift', 'status', 'nr', 'alarm', 'dur_sec', 'cnt']
        grouped = grouped[['shift', 'status', 'nr', 'alarm', 'cnt', 'dur_sec']]
        grouped = grouped.sort_values('cnt', ascending=False)
    else:
        grouped = filtered.groupby(['shift', 'status', 'nr'], as_index=False).agg({
            'alarm_first': 'first',
            'dur_sec': 'sum',
            'alarm': 'count'
        })
        grouped.columns = ['shift', 'status', 'nr', 'alarm', 'dur_sec', 'cnt']
        grouped = grouped[['shift', 'status', 'nr', 'alarm', 'cnt', 'dur_sec']]
        grouped['shift'] = grouped['shift'].astype(int)
        grouped = grouped.sort_values('shift')
    
    grouped['duration_fixed'] = grouped['dur_sec'].apply(format_seconds_to_duration)
    grouped = grouped.drop('dur_sec', axis=1)
    
    columns = list(grouped.columns)
    rows = [tuple(row) for row in grouped.values]
    
    return columns, rows


# ==================== MAIN APP ====================
class SorterApp(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("SORTER ANALYZER")
        self.geometry("1400x850")
        self.configure(bg='#f0f2f5')
        
        # Colors - Light mode
        self.bg = '#f0f2f5'
        self.bg_secondary = '#ffffff'
        self.bg_card = '#ffffff'
        self.accent = '#0066ff'
        self.accent_secondary = '#ff3366'
        self.text = '#1a1a1a'
        self.text_secondary = '#666666'
        self.success = '#00cc66'
        self.warning = '#ff9900'
        self.error = '#ff3366'
        self.border = '#dddddd'
        
        # Settings
        folder, nr_list, monitor_interval = load_settings()
        self.folder_path = tk.StringVar(value=folder)
        self.nr_list_var = tk.StringVar(value=",".join(str(n) for n in nr_list))
        self.monitor_interval_var = tk.StringVar(value=str(monitor_interval))
        self.mode_var = tk.StringVar(value="single")
        self.query_mode_var = tk.StringVar(value="shifts")
        
        # State
        self.monitoring = False
        self.current_nr_list = nr_list
        self.monitor_interval_sec = monitor_interval
        self.last_columns = None
        self.last_rows = None
        self.view_mode = 'table'
        
        # Fonts
        self.font_title = tkfont.Font(family="Segoe UI", size=24, weight="bold")
        self.font_header = tkfont.Font(family="Segoe UI", size=12, weight="bold")
        self.font_normal = tkfont.Font(family="Segoe UI", size=10)
        self.font_small = tkfont.Font(family="Segoe UI", size=9)
        
        self._build_ui()
        self.refresh_file_list()
        self.update_mode_state()
    
    # ==================== UI CONSTRUCTION ====================
    def _build_ui(self):
        """Buduje interfejs"""
        
        # HEADER
        self.header = tk.Frame(self, height=70, bg=self.bg_secondary)
        self.header.pack(fill='x', padx=0, pady=0)
        self.header.pack_propagate(False)
        
        title_frame = tk.Frame(self.header, bg=self.bg_secondary)
        title_frame.pack(side='left', padx=30, pady=20)
        
        self.title_label = tk.Label(
            title_frame,
            text="SORTER ANALYZER",
            font=self.font_title,
            bg=self.bg_secondary,
            fg=self.accent
        )
        self.title_label.pack(side='left')
        
        # MAIN CONTAINER
        self.main_container = tk.Frame(self, bg=self.bg)
        self.main_container.pack(fill='both', expand=True, padx=20, pady=10)
        
        # LEFT PANEL - Controls (with scrollbar)
        left_outer = tk.Frame(self.main_container, bg=self.bg)
        left_outer.pack(side='left', fill='both', padx=(0, 10))
        
        self.left_canvas = tk.Canvas(left_outer, bg=self.bg, width=400, highlightthickness=0)
        left_scrollbar = ttk.Scrollbar(left_outer, orient='vertical', command=self.left_canvas.yview)
        
        self.left_panel = tk.Frame(self.left_canvas, bg=self.bg)
        
        self.left_canvas.configure(yscrollcommand=left_scrollbar.set)
        
        left_scrollbar.pack(side='right', fill='y')
        self.left_canvas.pack(side='left', fill='both', expand=True)
        
        self.canvas_frame = self.left_canvas.create_window((0, 0), window=self.left_panel, anchor='nw')
        
        self.left_panel.bind('<Configure>', lambda e: self.left_canvas.configure(scrollregion=self.left_canvas.bbox('all')))
        
        def _on_mousewheel(event):
            self.left_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.left_canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        self._build_controls()
        
        # RIGHT PANEL - Data view
        self.right_panel = tk.Frame(self.main_container, bg=self.bg_card)
        self.right_panel.pack(side='right', fill='both', expand=True)
        
        self._build_data_view()
        
        # FOOTER - Status bar
        self.footer = tk.Frame(self, height=40, bg=self.bg_secondary)
        self.footer.pack(fill='x', side='bottom')
        self.footer.pack_propagate(False)
        
        self.status_label = tk.Label(
            self.footer,
            text="Gotowy do analizy",
            font=self.font_small,
            bg=self.bg_secondary,
            fg=self.text_secondary,
            anchor='w'
        )
        self.status_label.pack(side='left', padx=20, pady=10)
        
        self.time_label = tk.Label(
            self.footer,
            text="",
            font=self.font_small,
            bg=self.bg_secondary,
            fg=self.text_secondary,
            anchor='e'
        )
        self.time_label.pack(side='right', padx=20, pady=10)
        self.update_time()
    
    def _build_controls(self):
        """Panel kontrolny po lewej"""
        
        # CARD 1: Folder selection
        card1 = self._create_card(self.left_panel, "Folder z danymi")
        card1.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            card1,
            text="Folder:",
            font=self.font_small,
            bg=self.bg_card,
            fg=self.text_secondary
        ).pack(anchor='w', padx=15, pady=(10, 5))
        
        folder_frame = tk.Frame(card1, bg=self.bg_card)
        folder_frame.pack(fill='x', padx=15, pady=(0, 10))
        
        self.folder_entry = tk.Entry(
            folder_frame,
            textvariable=self.folder_path,
            font=self.font_small,
            bg='#f8f9fa',
            fg=self.text,
            insertbackground=self.accent,
            relief='solid',
            bd=1
        )
        self.folder_entry.pack(side='left', fill='x', expand=True, ipady=6, padx=(0, 5))
        
        self._create_button(folder_frame, "...", self.browse_folder, width=3).pack(side='right')
        
        # CARD 2: Mode selection
        card2 = self._create_card(self.left_panel, "Tryb pracy")
        card2.pack(fill='x', pady=(0, 15))
        
        mode_frame = tk.Frame(card2, bg=self.bg_card)
        mode_frame.pack(fill='x', padx=15, pady=10)
        
        self.radio_single = tk.Radiobutton(
            mode_frame,
            text="Analiza wstecz",
            variable=self.mode_var,
            value="single",
            font=self.font_normal,
            bg=self.bg_card,
            fg=self.text,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_card,
            activeforeground=self.accent,
            indicatoron=1,
            command=self.update_mode_state
        )
        self.radio_single.pack(anchor='w', pady=3)
        
        self.radio_live = tk.Radiobutton(
            mode_frame,
            text="Monitoring LIVE",
            variable=self.mode_var,
            value="live",
            font=self.font_normal,
            bg=self.bg_card,
            fg=self.text,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_card,
            activeforeground=self.accent,
            indicatoron=1,
            command=self.update_mode_state
        )
        self.radio_live.pack(anchor='w', pady=3)
        
        file_frame = tk.Frame(card2, bg=self.bg_card)
        file_frame.pack(fill='x', padx=15, pady=(5, 10))
        
        tk.Label(
            file_frame,
            text="Plik:",
            font=self.font_small,
            bg=self.bg_card,
            fg=self.text_secondary
        ).pack(side='left', padx=(0, 5))
        
        style = ttk.Style()
        style.theme_use('clam')
        
        self.file_combo = ttk.Combobox(
            file_frame,
            state="readonly",
            font=self.font_small,
            width=25
        )
        self.file_combo.pack(side='left', fill='x', expand=True)
        
        # CARD 3: Query settings
        card3 = self._create_card(self.left_panel, "Parametry zapytania")
        card3.pack(fill='x', pady=(0, 15))
        
        query_frame = tk.Frame(card3, bg=self.bg_card)
        query_frame.pack(fill='x', padx=15, pady=10)
        
        self.radio_shifts = tk.Radiobutton(
            query_frame,
            text="Zmiany (1/2)",
            variable=self.query_mode_var,
            value="shifts",
            font=self.font_normal,
            bg=self.bg_card,
            fg=self.text,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_card,
            indicatoron=1
        )
        self.radio_shifts.pack(anchor='w', pady=3)
        
        self.radio_total = tk.Radiobutton(
            query_frame,
            text="Total (suma)",
            variable=self.query_mode_var,
            value="total",
            font=self.font_normal,
            bg=self.bg_card,
            fg=self.text,
            selectcolor=self.bg_secondary,
            activebackground=self.bg_card,
            indicatoron=1
        )
        self.radio_total.pack(anchor='w', pady=3)
        
        tk.Label(
            card3,
            text="Numery błędów:",
            font=self.font_small,
            bg=self.bg_card,
            fg=self.text_secondary
        ).pack(anchor='w', padx=15, pady=(10, 5))
        
        self.nr_entry = tk.Entry(
            card3,
            textvariable=self.nr_list_var,
            font=self.font_small,
            bg='#f8f9fa',
            fg=self.text,
            insertbackground=self.accent,
            relief='solid',
            bd=1
        )
        self.nr_entry.pack(fill='x', padx=15, pady=(0, 10), ipady=6)
        
        tk.Label(
            card3,
            text="Interwał monitoringu (s):",
            font=self.font_small,
            bg=self.bg_card,
            fg=self.text_secondary
        ).pack(anchor='w', padx=15, pady=(5, 5))
        
        self.interval_entry = tk.Entry(
            card3,
            textvariable=self.monitor_interval_var,
            font=self.font_small,
            bg='#f8f9fa',
            fg=self.text,
            insertbackground=self.accent,
            relief='solid',
            bd=1,
            width=10
        )
        self.interval_entry.pack(anchor='w', padx=15, pady=(0, 15), ipady=6)
        
        # CARD 4: Actions
        card4 = self._create_card(self.left_panel, "Akcje")
        card4.pack(fill='x', pady=(0, 15))
        
        actions_frame = tk.Frame(card4, bg=self.bg_card)
        actions_frame.pack(fill='x', padx=15, pady=15)
        
        self.analyze_btn = self._create_button(
            actions_frame,
            "ANALIZUJ TERAZ",
            self.run_now,
            bg=self.accent,
            fg='white'
        )
        self.analyze_btn.pack(fill='x', pady=5)
        
        self.monitor_btn = self._create_button(
            actions_frame,
            f"START MONITORINGU ({self.monitor_interval_sec}s)",
            self.toggle_monitoring,
            bg=self.success,
            fg='white'
        )
        self.monitor_btn.pack(fill='x', pady=5)
        
        self._create_button(
            actions_frame,
            "Zapisz ustawienia",
            self.on_save_settings,
            bg=self.bg_secondary
        ).pack(fill='x', pady=5)
        
        self._create_button(
            actions_frame,
            "Odśwież listę plików",
            self.refresh_file_list,
            bg=self.bg_secondary
        ).pack(fill='x', pady=5)
        
        # Export CSV button
        self.export_btn = self._create_button(
            actions_frame,
            "Eksportuj do CSV",
            self.export_to_csv,
            bg=self.accent_secondary,
            fg='white'
        )
        self.export_btn.pack(fill='x', pady=5)
        self.export_btn.config(state='disabled')
    
    def _build_data_view(self):
        """Panel danych po prawej"""
        
        view_header = tk.Frame(self.right_panel, bg=self.bg_card, height=60)
        view_header.pack(fill='x', pady=(0, 1))
        view_header.pack_propagate(False)
        
        tk.Label(
            view_header,
            text="Wyniki analizy",
            font=self.font_header,
            bg=self.bg_card,
            fg=self.text
        ).pack(side='left', padx=20, pady=15)
        
        toggle_frame = tk.Frame(view_header, bg=self.bg_card)
        toggle_frame.pack(side='right', padx=20, pady=15)
        
        self.btn_table = self._create_button(
            toggle_frame,
            "Tabela",
            lambda: self.switch_view('table'),
            bg=self.accent,
            fg='white',
            width=12
        )
        self.btn_table.pack(side='left', padx=3)
        
        self.btn_charts = self._create_button(
            toggle_frame,
            "Wykresy",
            lambda: self.switch_view('charts'),
            bg=self.bg_secondary,
            width=12
        )
        self.btn_charts.pack(side='left', padx=3)
        
        self.content_container = tk.Frame(self.right_panel, bg=self.bg_card)
        self.content_container.pack(fill='both', expand=True)
        
        self.table_frame = tk.Frame(self.content_container, bg=self.bg_card)
        self.charts_frame = tk.Frame(self.content_container, bg=self.bg_card)
        
        self.table_frame.pack(fill='both', expand=True)
    
    def _create_card(self, parent, title):
        """Tworzy kartę z tytułem"""
        card = tk.Frame(parent, bg=self.bg_card, relief='solid', bd=1)
        
        header = tk.Label(
            card,
            text=title,
            font=self.font_header,
            bg=self.bg_card,
            fg=self.text,
            anchor='w'
        )
        header.pack(fill='x', padx=15, pady=(15, 5))
        
        separator = tk.Frame(card, bg=self.accent, height=2)
        separator.pack(fill='x', padx=15, pady=(0, 5))
        
        return card
    
    def _create_button(self, parent, text, command, bg=None, fg=None, width=None):
        """Tworzy styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.font_normal,
            bg=bg or self.bg_secondary,
            fg=fg or self.text,
            activebackground=self.accent,
            activeforeground='white',
            relief='flat',
            bd=0,
            cursor='hand2',
            width=width
        )
        
        original_bg = bg or self.bg_secondary
        original_fg = fg or self.text
        
        def on_enter(e):
            if btn['state'] != 'disabled':
                btn['bg'] = self.accent
                btn['fg'] = 'white'
        
        def on_leave(e):
            if btn['state'] != 'disabled':
                btn['bg'] = original_bg
                btn['fg'] = original_fg
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        
        return btn
    
    def switch_view(self, mode):
        """Przełącza między tabelą a wykresami"""
        self.view_mode = mode
        
        if mode == 'table':
            self.btn_table['bg'] = self.accent
            self.btn_table['fg'] = 'white'
            self.btn_charts['bg'] = self.bg_secondary
            self.btn_charts['fg'] = self.text
        else:
            self.btn_charts['bg'] = self.accent
            self.btn_charts['fg'] = 'white'
            self.btn_table['bg'] = self.bg_secondary
            self.btn_table['fg'] = self.text
        
        if mode == 'table':
            self.charts_frame.pack_forget()
            self.table_frame.pack(fill='both', expand=True)
            if self.last_rows:
                self.show_table(self.last_columns, self.last_rows)
        else:
            self.table_frame.pack_forget()
            self.charts_frame.pack(fill='both', expand=True)
            if self.last_rows:
                self.show_charts(self.last_columns, self.last_rows)
    
    def show_table(self, columns, rows):
        """Wyświetla tabelę wyników"""
        for widget in self.table_frame.winfo_children():
            widget.destroy()
        
        if not rows:
            tk.Label(
                self.table_frame,
                text="Brak danych do wyświetlenia",
                font=self.font_header,
                bg=self.bg_card,
                fg=self.text_secondary
            ).pack(expand=True)
            return
        
        # Stats cards
        stats_frame = tk.Frame(self.table_frame, bg=self.bg_card)
        stats_frame.pack(fill='x', padx=20, pady=15)
        
        df = pd.DataFrame(rows, columns=columns)
        
        total_alarms = df['cnt'].sum() if 'cnt' in df.columns else len(rows)
        unique_types = df['alarm'].nunique() if 'alarm' in df.columns else 0
        
        self._create_stat_card(stats_frame, "Wszystkie alarmy", str(total_alarms)).pack(side='left', padx=10)
        self._create_stat_card(stats_frame, "Unikalne typy", str(unique_types)).pack(side='left', padx=10)
        self._create_stat_card(stats_frame, "Wierszy danych", str(len(rows))).pack(side='left', padx=10)
        
        # Table
        table_container = tk.Frame(self.table_frame, bg=self.bg_card)
        table_container.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            "Treeview",
            background='white',
            foreground=self.text,
            fieldbackground='white',
            borderwidth=1
        )
        style.configure("Treeview.Heading", background=self.bg_secondary, foreground=self.accent, font=self.font_header, borderwidth=1)
        style.map('Treeview', background=[('selected', self.accent)])
        
        tree = ttk.Treeview(table_container, columns=columns, show='headings', style="Treeview")
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120, anchor='center')
        
        for row in rows:
            tree.insert('', 'end', values=row)
        
        scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=tree.yview)
        tree.configure(yscroll=scrollbar.set)
        
        tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
    
    def show_charts(self, columns, rows):
        """Wyświetla wykresy"""
        for widget in self.charts_frame.winfo_children():
            widget.destroy()
        
        if not rows:
            tk.Label(
                self.charts_frame,
                text="Brak danych do wizualizacji",
                font=self.font_header,
                bg=self.bg_card,
                fg=self.text_secondary
            ).pack(expand=True)
            return
        
        df = pd.DataFrame(rows, columns=columns)
        
        plt.style.use('default')
        
        fig = Figure(figsize=(12, 6), dpi=100, facecolor='white')
        
        if 'shift' in df.columns and 'cnt' in df.columns and 'alarm' in df.columns:
            if df['shift'].dtype in ['int64', 'int32']:
                ax = fig.add_subplot(111)
                
                shift1 = df[df['shift'] == 1]
                shift2 = df[df['shift'] == 2]
                
                x = range(len(df['alarm'].unique()))
                width = 0.35
                
                if not shift1.empty:
                    ax.bar([i - width/2 for i in x[:len(shift1)]], shift1['cnt'], width, 
                           label='Zmiana 1', color=self.accent, alpha=0.8)
                if not shift2.empty:
                    ax.bar([i + width/2 for i in x[:len(shift2)]], shift2['cnt'], width,
                           label='Zmiana 2', color=self.accent_secondary, alpha=0.8)
                
                ax.set_xlabel('Typ alarmu', fontsize=12)
                ax.set_ylabel('Liczba wystąpień', fontsize=12)
                ax.set_title('Rozkład alarmów według zmian', fontsize=16, fontweight='bold', pad=20)
                ax.set_xticks(x)
                ax.set_xticklabels(df['alarm'].unique(), rotation=45, ha='right')
                ax.legend()
                ax.grid(alpha=0.3)
                ax.set_facecolor('white')
                
            else:
                ax = fig.add_subplot(111)
                ax.barh(df['alarm'], df['cnt'], color=self.accent, alpha=0.8)
                ax.set_xlabel('Liczba wystąpień', fontsize=12)
                ax.set_ylabel('Typ alarmu', fontsize=12)
                ax.set_title('Najczęstsze alarmy', fontsize=16, fontweight='bold', pad=20)
                ax.grid(alpha=0.3, axis='x')
                ax.set_facecolor('white')
        
        fig.tight_layout(pad=2)
        
        canvas = FigureCanvasTkAgg(fig, master=self.charts_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill='both', expand=True, padx=20, pady=20)
    
    def _create_stat_card(self, parent, title, value):
        """Tworzy kartę statystyczną"""
        card = tk.Frame(parent, bg='white', relief='solid', bd=1)
        
        text_frame = tk.Frame(card, bg='white')
        text_frame.pack(padx=20, pady=15)
        
        tk.Label(
            text_frame,
            text=value,
            font=('Segoe UI', 20, 'bold'),
            bg='white',
            fg=self.text
        ).pack(anchor='w')
        
        tk.Label(
            text_frame,
            text=title,
            font=self.font_small,
            bg='white',
            fg=self.text_secondary
        ).pack(anchor='w')
        
        return card
    
    def get_nr_list_from_ui(self, show_error=True):
        """Walidacja listy numerów"""
        text = self.nr_list_var.get()
        parts = text.replace(";", ",").split(",")
        nr_list = []
        for part in parts:
            part = part.strip()
            if not part:
                continue
            try:
                nr_list.append(int(part))
            except ValueError:
                if show_error:
                    messagebox.showerror("Błąd", f"Nieprawidłowa wartość: '{part}'")
                return None
        
        if not nr_list:
            if show_error:
                messagebox.showerror("Błąd", "Lista numerów jest pusta")
            return None
        
        self.current_nr_list = nr_list
        return nr_list
    
    def browse_folder(self):
        """Wybór folderu"""
        folder = filedialog.askdirectory(initialdir=self.folder_path.get())
        if folder:
            self.folder_path.set(folder)
            save_settings(folder, self.current_nr_list or DEFAULT_NR_LIST, self.monitor_interval_sec or DEFAULT_MONITOR_INTERVAL_SEC)
            self.refresh_file_list()
    
    def refresh_file_list(self):
        """Odświeża listę plików"""
        files = list_alarmlog_files(self.folder_path.get().strip())
        self.file_combo['values'] = files
        if files:
            self.file_combo.current(0)
        else:
            self.file_combo.set("")
        self.status_label.config(text=f"Znaleziono {len(files)} plików")
    
    def update_mode_state(self):
        """Aktualizuje stan kontrolek"""
        if self.mode_var.get() == "single":
            if self.monitoring:
                self.monitoring = False
                self.monitor_btn.config(text=f"START MONITORINGU ({self.monitor_interval_sec}s)")
            self.monitor_btn.config(state="disabled")
            self.file_combo.config(state="readonly")
        else:
            self.file_combo.config(state="disabled")
            self.monitor_btn.config(state="normal")
    
    def run_now(self):
        """Uruchamia analizę"""
        folder = self.folder_path.get().strip()
        if not os.path.isdir(folder):
            messagebox.showerror("Błąd", "Folder nie istnieje")
            return
        
        nr_list = self.get_nr_list_from_ui(show_error=True)
        if nr_list is None:
            return
        
        try:
            if self.mode_var.get() == "single":
                filename = self.file_combo.get()
                if not filename:
                    messagebox.showerror("Błąd", "Nie wybrano pliku")
                    return
                path = os.path.join(folder, filename)
            else:
                path = find_today_alarmlog(folder)
                if not path:
                    raise FileNotFoundError("Brak dzisiejszego pliku")
            
            self.status_label.config(text="Analizuję dane...")
            self.update()
            
            columns, rows = analyze_data(path, nr_list, self.query_mode_var.get())
            
            self.last_columns = columns
            self.last_rows = rows
            
            if self.view_mode == 'table':
                self.show_table(columns, rows)
            else:
                self.show_charts(columns, rows)
            
            self.export_btn.config(state='normal')
            self.status_label.config(text=f"Analiza zakończona - {len(rows)} wyników")
            
        except Exception as e:
            messagebox.showerror("Błąd", str(e))
            self.status_label.config(text=f"Błąd: {e}")
    
    def toggle_monitoring(self):
        """Przełącza monitoring"""
        if self.mode_var.get() != "live":
            messagebox.showerror("Błąd", "Wybierz tryb 'Monitoring LIVE'")
            return
        
        if not self.monitoring:
            nr_list = self.get_nr_list_from_ui(show_error=True)
            if nr_list is None:
                return
            
            self.monitoring = True
            self.monitor_btn.config(
                text=f"STOP MONITORINGU ({self.monitor_interval_sec}s)",
                bg=self.error
            )
            self.status_label.config(text=f"Monitoring aktywny (odświeżanie co {self.monitor_interval_sec}s)")
            self.monitor_step()
        else:
            self.monitoring = False
            self.monitor_btn.config(
                text=f"START MONITORINGU ({self.monitor_interval_sec}s)",
                bg=self.success
            )
            self.status_label.config(text="Monitoring zatrzymany")
    
    def monitor_step(self):
        """Krok monitoringu"""
        if not self.monitoring:
            return
        
        try:
            folder = self.folder_path.get().strip()
            path = find_today_alarmlog(folder)
            if not path:
                raise FileNotFoundError("Brak dzisiejszego pliku")
            
            columns, rows = analyze_data(path, self.current_nr_list or DEFAULT_NR_LIST, self.query_mode_var.get())
            
            self.last_columns = columns
            self.last_rows = rows
            
            if self.view_mode == 'table':
                self.show_table(columns, rows)
            else:
                self.show_charts(columns, rows)
            
            self.export_btn.config(state='normal')
            self.status_label.config(text=f"LIVE - ostatnia aktualizacja: {datetime.now().strftime('%H:%M:%S')}")
            
        except Exception as e:
            self.status_label.config(text=f"Monitoring: {e}")
        
        self.after(self.monitor_interval_sec * 1000, self.monitor_step)
    
    def on_save_settings(self):
        """Zapisuje ustawienia"""
        folder = self.folder_path.get().strip() or DEFAULT_FOLDER
        nr_list = self.get_nr_list_from_ui(show_error=True) or DEFAULT_NR_LIST
        
        try:
            interval = int(self.monitor_interval_var.get().strip())
            if interval <= 0:
                raise ValueError
        except:
            interval = DEFAULT_MONITOR_INTERVAL_SEC
        
        self.monitor_interval_sec = interval
        save_settings(folder, nr_list, interval)
        self.status_label.config(text="Ustawienia zapisane")
    
    def export_to_csv(self):
        """Eksportuje dane do CSV"""
        if not self.last_rows or not self.last_columns:
            messagebox.showwarning("Uwaga", "Brak danych do eksportu. Wykonaj najpierw analizę.")
            return
        
        # Ask for save location
        default_filename = f"sorter_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=default_filename
        )
        
        if not filepath:
            return
        
        try:
            df = pd.DataFrame(self.last_rows, columns=self.last_columns)
            df.to_csv(filepath, index=False, encoding='utf-8-sig', sep=';')
            messagebox.showinfo("Sukces", f"Dane wyeksportowane do:\n{filepath}")
            self.status_label.config(text=f"Eksport zakończony: {os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się wyeksportować danych:\n{e}")
    
    def update_time(self):
        """Aktualizuje czas w footerze"""
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.after(1000, self.update_time)


if __name__ == "__main__":
    app = SorterApp()
    app.mainloop()
