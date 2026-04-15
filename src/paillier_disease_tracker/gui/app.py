from __future__ import annotations

from pathlib import Path
from time import perf_counter
import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk

from ..benchmarking import KeySizeBenchmarkResult, run_crypto_benchmark
from ..client import ClientApplication, DiseaseCountFlow, ValidationReport
from ..config import DEFAULT_DB_PATH, DEFAULT_DISEASES, DEFAULT_KEY_SIZE, DEFAULT_KEYS_PATH
from ..crypto import generate_keypair
from ..keys import load_keypair, save_keypair


class TrackerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Paillier Disease Tracker Control Center")
        self.root.geometry("1380x900")
        self.root.minsize(1200, 760)

        self.app: ClientApplication | None = None
        self.loaded_db_path: Path | None = None
        self.loaded_keys_path: Path | None = None
        self.last_benchmark_results: list[KeySizeBenchmarkResult] = []
        self.diagnosis_vars: dict[str, tk.IntVar] = {}
        self.validation_status_var = tk.StringVar(value="Validation: -")
        self.summary_rows_var = tk.StringVar(value="Rows: -")
        self.summary_encrypted_var = tk.StringVar(value="Encrypted SUM: -")
        self.summary_decrypted_var = tk.StringVar(value="Decrypted SUM: -")
        self.summary_plain_var = tk.StringVar(value="Plain SUM reference: -")
        self.status_var = tk.StringVar(value="Ready")
        self.theme_var = tk.StringVar(value="flatly")

        self.db_path_var = tk.StringVar(value=str(DEFAULT_DB_PATH))
        self.keys_path_var = tk.StringVar(value=str(DEFAULT_KEYS_PATH))
        self.key_size_var = tk.StringVar(value=str(DEFAULT_KEY_SIZE))
        self.patient_name_var = tk.StringVar(value="")
        self.bulk_patients_var = tk.StringVar(value="5000")
        self.bulk_seed_var = tk.StringVar(value="42")
        self.bulk_prefix_var = tk.StringVar(value="bulk_patient")
        self.bulk_batch_size_var = tk.StringVar(value="1000")
        self.selected_disease_var = tk.StringVar(value=DEFAULT_DISEASES[0])
        self.process_plain_var = tk.StringVar(value="dane jawne: -")
        self.process_cipher_var = tk.StringVar(value="szyfrogram: -")
        self.process_homomorphic_var = tk.StringVar(value="wynik homomorficzny: -")
        self.process_decrypted_var = tk.StringVar(value="odszyfrowany wynik: -")
        self.benchmark_key_sizes_var = tk.StringVar(value="256,512,768")
        self.benchmark_encrypt_iterations_var = tk.StringVar(value="200")
        self.benchmark_decrypt_iterations_var = tk.StringVar(value="200")
        self.benchmark_homomorphic_iterations_var = tk.StringVar(value="100")
        self.benchmark_batch_size_var = tk.StringVar(value="64")
        self.benchmark_report_path_var = tk.StringVar(
            value="docs/08_tydzien_6_dane_wydajnosciowe.md"
        )

        self._configure_styles()
        self._build_layout()
        self._configure_styles()
        self._refresh_diagnosis_controls(list(DEFAULT_DISEASES))
        self._log("GUI gotowe. Uzyj Setup new albo Load existing.")

    def _is_dark_theme(self, theme_name: str | None = None) -> bool:
        selected = (theme_name or self.theme_var.get()).strip().lower()
        return selected in {
            "darkly",
            "superhero",
            "solar",
            "cyborg",
            "vapor",
        }

    def _configure_styles(self) -> None:
        selected_theme = self.theme_var.get().strip() or "flatly"
        if not hasattr(self, "style"):
            self.style = ttk.Style(theme=selected_theme)
        else:
            self.style.theme_use(selected_theme)

        is_dark = self._is_dark_theme(selected_theme)
        root_bg = "#0f172a" if is_dark else "#f2f5fb"
        card_bg = "#111827" if is_dark else "#ffffff"
        primary_text = "#e2e8f0" if is_dark else "#0f172a"
        secondary_text = "#cbd5e1" if is_dark else "#334155"
        summary_bg = "#1e293b" if is_dark else "#e8eefc"
        chip_bg = "#1d4ed8" if is_dark else "#dbeafe"
        chip_fg = "#eff6ff" if is_dark else "#1e3a8a"

        self.root.configure(bg=root_bg)
        self.style.configure("App.TFrame", background=root_bg)
        self.style.configure("Card.TLabelframe", background=card_bg)
        self.style.configure("Card.TLabelframe.Label", background=card_bg, foreground=primary_text)
        self.style.configure(
            "Header.TLabel",
            background=root_bg,
            foreground=primary_text,
            font=("Segoe UI Semibold", 22),
        )
        self.style.configure(
            "Subheader.TLabel",
            background=root_bg,
            foreground=secondary_text,
            font=("Segoe UI", 10),
        )
        self.style.configure(
            "Summary.TLabel",
            background=summary_bg,
            foreground=primary_text,
            font=("Segoe UI Semibold", 10),
            padding=8,
        )
        self.style.configure(
            "Chip.TLabel",
            background=chip_bg,
            foreground=chip_fg,
            font=("Segoe UI Semibold", 9),
            padding=(10, 3),
        )
        self.style.configure("Accent.TButton", font=("Segoe UI Semibold", 10))
        self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI Semibold", 10))
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1d4ed8")],
            foreground=[("active", "#ffffff")],
        )

        text_bg = "#0b1220" if is_dark else "#ffffff"
        text_fg = "#e5e7eb" if is_dark else "#1f2937"
        for widget_name in ("log_widget", "pipeline_text", "benchmark_summary_text"):
            if hasattr(self, widget_name):
                widget = getattr(self, widget_name)
                widget.configure(bg=text_bg, fg=text_fg, insertbackground=text_fg)

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=12, style="App.TFrame")
        container.pack(fill=tk.BOTH, expand=True)

        header_frame = ttk.Frame(container, style="App.TFrame")
        header_frame.pack(fill=tk.X)

        ttk.Label(header_frame, text="Paillier Disease Tracker", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header_frame,
            text="Centrum operacyjne: konfiguracja, dane, analityka homomorficzna, walidacja i benchmarki.",
            style="Subheader.TLabel",
        ).pack(anchor=tk.W, pady=(2, 10))

        chips_frame = ttk.Frame(header_frame, style="App.TFrame")
        chips_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(chips_frame, text="Klient-Serwer", style="Chip.TLabel").pack(side=tk.LEFT, padx=(0, 6))
        ttk.Label(chips_frame, text="Paillier Homomorphic", style="Chip.TLabel").pack(
            side=tk.LEFT,
            padx=(0, 6),
        )
        ttk.Label(chips_frame, text="Walidacja End-to-End", style="Chip.TLabel").pack(side=tk.LEFT)

        self.main_notebook = ttk.Notebook(container)
        self.main_notebook.pack(fill=tk.BOTH, expand=True)

        self.project_tab = ttk.Frame(self.main_notebook, style="App.TFrame", padding=8)
        self.patients_tab = ttk.Frame(self.main_notebook, style="App.TFrame", padding=8)
        self.analytics_tab = ttk.Frame(self.main_notebook, style="App.TFrame", padding=8)
        self.performance_tab = ttk.Frame(self.main_notebook, style="App.TFrame", padding=8)
        self.log_tab = ttk.Frame(self.main_notebook, style="App.TFrame", padding=8)

        self.main_notebook.add(self.project_tab, text="Projekt")
        self.main_notebook.add(self.patients_tab, text="Pacjenci i dane")
        self.main_notebook.add(self.analytics_tab, text="Analityka i walidacja")
        self.main_notebook.add(self.performance_tab, text="Benchmarki")
        self.main_notebook.add(self.log_tab, text="Log")

        self._build_project_tab()
        self._build_patients_tab()
        self._build_analytics_tab()
        self._build_performance_tab()
        self._build_log_tab()

        status_bar = ttk.Label(container, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, pady=(8, 0))

    def _build_project_tab(self) -> None:
        config_frame = ttk.Labelframe(
            self.project_tab,
            text="Konfiguracja projektu",
            padding=12,
            style="Card.TLabelframe",
            bootstyle="info",
        )
        config_frame.pack(fill=tk.X)

        ttk.Label(config_frame, text="DB path").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.db_path_var, width=64).grid(
            row=0, column=1, sticky=tk.W, padx=8
        )

        ttk.Label(config_frame, text="Keys path").grid(row=1, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.keys_path_var, width=64).grid(
            row=1, column=1, sticky=tk.W, padx=8
        )

        ttk.Label(config_frame, text="Key size").grid(row=2, column=0, sticky=tk.W)
        ttk.Entry(config_frame, textvariable=self.key_size_var, width=16).grid(
            row=2, column=1, sticky=tk.W, padx=8
        )

        ttk.Button(
            config_frame,
            text="Setup new",
            command=self.on_setup_new,
            style="Accent.TButton",
            bootstyle="primary",
        ).grid(
            row=0, column=2, padx=6
        )
        ttk.Button(
            config_frame,
            text="Load existing",
            command=self.on_load_existing,
            bootstyle="secondary",
        ).grid(
            row=1, column=2, padx=6
        )
        ttk.Button(
            config_frame,
            text="List diseases",
            command=self.on_list_diseases,
            bootstyle="info",
        ).grid(
            row=2, column=2, padx=6
        )

        ttk.Label(config_frame, text="Theme").grid(row=3, column=0, sticky=tk.W, pady=(8, 0))
        self.theme_combobox = ttk.Combobox(
            config_frame,
            textvariable=self.theme_var,
            state="readonly",
            values=sorted(self.style.theme_names()),
            width=20,
        )
        self.theme_combobox.grid(row=3, column=1, sticky=tk.W, padx=8, pady=(8, 0))
        ttk.Button(
            config_frame,
            text="Apply theme",
            command=self.on_apply_theme,
            bootstyle="warning",
        ).grid(row=3, column=2, padx=6, pady=(8, 0))

        mapping_frame = ttk.Labelframe(
            self.project_tab,
            text="Mapowanie chorob",
            padding=10,
            style="Card.TLabelframe",
            bootstyle="primary",
        )
        mapping_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.mapping_tree = ttk.Treeview(
            mapping_frame,
            columns=("code", "name"),
            show="headings",
            height=8,
        )
        self.mapping_tree.heading("code", text="Code")
        self.mapping_tree.heading("name", text="Disease")
        self.mapping_tree.column("code", width=120, anchor=tk.CENTER)
        self.mapping_tree.column("name", width=340, anchor=tk.W)
        self.mapping_tree.pack(fill=tk.BOTH, expand=True)

    def _build_patients_tab(self) -> None:
        patient_frame = ttk.Labelframe(
            self.patients_tab,
            text="Dodawanie pacjenta",
            padding=12,
            style="Card.TLabelframe",
            bootstyle="success",
        )
        patient_frame.pack(fill=tk.X)

        ttk.Label(patient_frame, text="Pseudonym").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(patient_frame, textvariable=self.patient_name_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=8
        )

        self.diagnoses_frame = ttk.Frame(patient_frame)
        self.diagnoses_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(8, 0))

        ttk.Button(
            patient_frame,
            text="Add patient",
            command=self.on_add_patient,
            style="Accent.TButton",
            bootstyle="success",
        ).grid(
            row=0, column=2, padx=6
        )

        seed_frame = ttk.Labelframe(
            self.patients_tab,
            text="Seed danych",
            padding=12,
            style="Card.TLabelframe",
            bootstyle="warning",
        )
        seed_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(seed_frame, text="Seed demo", command=self.on_seed_demo, bootstyle="secondary").grid(
            row=0,
            column=0,
            padx=6,
        )

        ttk.Label(seed_frame, text="Bulk patients").grid(row=0, column=1, sticky=tk.W)
        ttk.Entry(seed_frame, textvariable=self.bulk_patients_var, width=10).grid(
            row=0, column=2, sticky=tk.W, padx=6
        )

        ttk.Label(seed_frame, text="Seed").grid(row=0, column=3, sticky=tk.W)
        ttk.Entry(seed_frame, textvariable=self.bulk_seed_var, width=10).grid(
            row=0, column=4, sticky=tk.W, padx=6
        )

        ttk.Label(seed_frame, text="Prefix").grid(row=0, column=5, sticky=tk.W)
        ttk.Entry(seed_frame, textvariable=self.bulk_prefix_var, width=18).grid(
            row=0, column=6, sticky=tk.W, padx=6
        )

        ttk.Label(seed_frame, text="Batch size").grid(row=0, column=7, sticky=tk.W)
        ttk.Entry(seed_frame, textvariable=self.bulk_batch_size_var, width=10).grid(
            row=0, column=8, sticky=tk.W, padx=6
        )

        ttk.Button(
            seed_frame,
            text="Run seed-bulk",
            command=self.on_seed_bulk,
            style="Accent.TButton",
            bootstyle="warning",
        ).grid(
            row=0,
            column=9,
            padx=6,
        )

    def _build_analytics_tab(self) -> None:
        analytics_frame = ttk.Labelframe(
            self.analytics_tab,
            text="Analityka serwerowa",
            padding=10,
            style="Card.TLabelframe",
            bootstyle="primary",
        )
        analytics_frame.pack(fill=tk.X)

        ttk.Label(analytics_frame, text="Disease").grid(row=0, column=0, sticky=tk.W)
        self.disease_combobox = ttk.Combobox(
            analytics_frame,
            textvariable=self.selected_disease_var,
            state="readonly",
            values=list(DEFAULT_DISEASES),
            width=30,
        )
        self.disease_combobox.grid(row=0, column=1, sticky=tk.W, padx=8)

        ttk.Button(
            analytics_frame,
            text="Count encrypted",
            command=self.on_count_disease,
            style="Accent.TButton",
            bootstyle="primary",
        ).grid(
            row=0, column=2, padx=6
        )
        ttk.Button(
            analytics_frame,
            text="Count + show flow details",
            command=self.on_count_with_rows,
            bootstyle="info",
        ).grid(row=0, column=3, padx=6)
        ttk.Button(
            analytics_frame,
            text="Show encrypted rows",
            command=self.on_show_encrypted_rows,
            bootstyle="secondary",
        ).grid(
            row=0,
            column=4,
            padx=6,
        )
        ttk.Button(
            analytics_frame,
            text="Validate selected",
            command=self.on_validate_selected,
            bootstyle="success",
        ).grid(
            row=0,
            column=5,
            padx=6,
        )
        ttk.Button(
            analytics_frame,
            text="Validate all",
            command=self.on_validate_all,
            style="Accent.TButton",
            bootstyle="success",
        ).grid(
            row=0,
            column=6,
            padx=6,
        )

        summary_frame = ttk.Frame(self.analytics_tab, style="App.TFrame")
        summary_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(summary_frame, textvariable=self.summary_rows_var, style="Summary.TLabel").grid(
            row=0,
            column=0,
            sticky="ew",
            padx=4,
        )
        ttk.Label(summary_frame, textvariable=self.summary_encrypted_var, style="Summary.TLabel").grid(
            row=0,
            column=1,
            sticky="ew",
            padx=4,
        )
        ttk.Label(summary_frame, textvariable=self.summary_decrypted_var, style="Summary.TLabel").grid(
            row=0,
            column=2,
            sticky="ew",
            padx=4,
        )
        ttk.Label(summary_frame, textvariable=self.summary_plain_var, style="Summary.TLabel").grid(
            row=0,
            column=3,
            sticky="ew",
            padx=4,
        )
        ttk.Label(summary_frame, textvariable=self.validation_status_var, style="Summary.TLabel").grid(
            row=0,
            column=4,
            sticky="ew",
            padx=4,
        )

        for index in range(5):
            summary_frame.grid_columnconfigure(index, weight=1)

        self.analytics_notebook = ttk.Notebook(self.analytics_tab)
        self.analytics_notebook.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        flow_tab = ttk.Frame(self.analytics_notebook, padding=8)
        encrypted_tab = ttk.Frame(self.analytics_notebook, padding=8)
        validation_tab = ttk.Frame(self.analytics_notebook, padding=8)
        pipeline_tab = ttk.Frame(self.analytics_notebook, padding=8)

        self.analytics_notebook.add(flow_tab, text="Flow rows")
        self.analytics_notebook.add(encrypted_tab, text="Encrypted rows")
        self.analytics_notebook.add(validation_tab, text="Validation report")
        self.analytics_notebook.add(pipeline_tab, text="Pipeline timeline")

        ttk.Label(flow_tab, textvariable=self.process_plain_var).grid(
            row=0, column=0, sticky=tk.W
        )
        ttk.Label(flow_tab, textvariable=self.process_cipher_var).grid(
            row=1, column=0, sticky=tk.W, pady=(2, 0)
        )
        ttk.Label(flow_tab, textvariable=self.process_homomorphic_var).grid(
            row=2, column=0, sticky=tk.W, pady=(2, 0)
        )
        ttk.Label(flow_tab, textvariable=self.process_decrypted_var).grid(
            row=3, column=0, sticky=tk.W, pady=(2, 8)
        )

        columns = ("pseudonym", "plain", "ciphertext")
        self.process_tree = ttk.Treeview(flow_tab, columns=columns, show="headings", height=14)
        self.process_tree.heading("pseudonym", text="Pseudonym")
        self.process_tree.heading("plain", text="Dane jawne (0/1)")
        self.process_tree.heading("ciphertext", text="Szyfrogram")
        self.process_tree.column("pseudonym", width=240, anchor=tk.W)
        self.process_tree.column("plain", width=140, anchor=tk.CENTER)
        self.process_tree.column("ciphertext", width=780, anchor=tk.W)
        self.process_tree.grid(row=4, column=0, sticky="nsew")

        process_scrollbar = ttk.Scrollbar(
            flow_tab,
            orient=tk.VERTICAL,
            command=self.process_tree.yview,
        )
        process_scrollbar.grid(row=4, column=1, sticky="ns")
        self.process_tree.configure(yscrollcommand=process_scrollbar.set)
        flow_tab.grid_columnconfigure(0, weight=1)
        flow_tab.grid_rowconfigure(4, weight=1)

        self.encrypted_rows_tree = ttk.Treeview(
            encrypted_tab,
            columns=("pseudonym", "ciphertext"),
            show="headings",
            height=16,
        )
        self.encrypted_rows_tree.heading("pseudonym", text="Pseudonym")
        self.encrypted_rows_tree.heading("ciphertext", text="Ciphertext")
        self.encrypted_rows_tree.column("pseudonym", width=240, anchor=tk.W)
        self.encrypted_rows_tree.column("ciphertext", width=920, anchor=tk.W)
        self.encrypted_rows_tree.pack(fill=tk.BOTH, expand=True)

        self.validation_tree = ttk.Treeview(
            validation_tab,
            columns=("disease", "h_sum", "p_sum", "h_count", "p_count", "status"),
            show="headings",
            height=16,
        )
        self.validation_tree.heading("disease", text="Disease")
        self.validation_tree.heading("h_sum", text="Homomorphic SUM")
        self.validation_tree.heading("p_sum", text="Plain SUM")
        self.validation_tree.heading("h_count", text="Homomorphic COUNT")
        self.validation_tree.heading("p_count", text="Plain COUNT")
        self.validation_tree.heading("status", text="Status")
        self.validation_tree.column("disease", width=180, anchor=tk.W)
        self.validation_tree.column("h_sum", width=180, anchor=tk.CENTER)
        self.validation_tree.column("p_sum", width=180, anchor=tk.CENTER)
        self.validation_tree.column("h_count", width=180, anchor=tk.CENTER)
        self.validation_tree.column("p_count", width=180, anchor=tk.CENTER)
        self.validation_tree.column("status", width=140, anchor=tk.CENTER)
        self.validation_tree.pack(fill=tk.BOTH, expand=True)

        self.pipeline_text = tk.Text(pipeline_tab, wrap=tk.WORD, height=14)
        self.pipeline_text.pack(fill=tk.BOTH, expand=True)

    def _build_performance_tab(self) -> None:
        control_frame = ttk.Labelframe(
            self.performance_tab,
            text="Konfiguracja benchmarku",
            padding=12,
            style="Card.TLabelframe",
            bootstyle="danger",
        )
        control_frame.pack(fill=tk.X)

        ttk.Label(control_frame, text="Key sizes").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(control_frame, textvariable=self.benchmark_key_sizes_var, width=24).grid(
            row=0,
            column=1,
            sticky=tk.W,
            padx=6,
        )
        ttk.Label(control_frame, text="Encrypt iterations").grid(row=0, column=2, sticky=tk.W)
        ttk.Entry(
            control_frame,
            textvariable=self.benchmark_encrypt_iterations_var,
            width=10,
        ).grid(row=0, column=3, sticky=tk.W, padx=6)
        ttk.Label(control_frame, text="Decrypt iterations").grid(row=0, column=4, sticky=tk.W)
        ttk.Entry(
            control_frame,
            textvariable=self.benchmark_decrypt_iterations_var,
            width=10,
        ).grid(row=0, column=5, sticky=tk.W, padx=6)
        ttk.Label(control_frame, text="Homomorphic iterations").grid(
            row=0,
            column=6,
            sticky=tk.W,
        )
        ttk.Entry(
            control_frame,
            textvariable=self.benchmark_homomorphic_iterations_var,
            width=10,
        ).grid(row=0, column=7, sticky=tk.W, padx=6)
        ttk.Label(control_frame, text="Batch size").grid(row=0, column=8, sticky=tk.W)
        ttk.Entry(
            control_frame,
            textvariable=self.benchmark_batch_size_var,
            width=10,
        ).grid(row=0, column=9, sticky=tk.W, padx=6)
        ttk.Button(
            control_frame,
            text="Run benchmark",
            command=self.on_run_benchmark,
            style="Accent.TButton",
            bootstyle="danger",
        ).grid(row=0, column=10, padx=6)

        export_frame = ttk.Frame(self.performance_tab, style="App.TFrame")
        export_frame.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(export_frame, text="Report path").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(export_frame, textvariable=self.benchmark_report_path_var, width=70).grid(
            row=0,
            column=1,
            sticky=tk.W,
            padx=6,
        )
        ttk.Button(
            export_frame,
            text="Export report",
            command=self.on_export_benchmark_report,
            bootstyle="info",
        ).grid(row=0, column=2, padx=6)

        result_frame = ttk.Labelframe(
            self.performance_tab,
            text="Wyniki benchmarku",
            padding=10,
            style="Card.TLabelframe",
            bootstyle="secondary",
        )
        result_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.benchmark_tree = ttk.Treeview(
            result_frame,
            columns=("key_size", "keygen_ms", "enc_ms", "dec_ms", "add_ms", "mul_ms"),
            show="headings",
            height=10,
        )
        self.benchmark_tree.heading("key_size", text="Key size")
        self.benchmark_tree.heading("keygen_ms", text="Keygen [ms]")
        self.benchmark_tree.heading("enc_ms", text="Encrypt avg [ms]")
        self.benchmark_tree.heading("dec_ms", text="Decrypt avg [ms]")
        self.benchmark_tree.heading("add_ms", text="Add_many avg [ms]")
        self.benchmark_tree.heading("mul_ms", text="Mul_const avg [ms]")

        self.benchmark_tree.column("key_size", width=120, anchor=tk.CENTER)
        self.benchmark_tree.column("keygen_ms", width=180, anchor=tk.CENTER)
        self.benchmark_tree.column("enc_ms", width=180, anchor=tk.CENTER)
        self.benchmark_tree.column("dec_ms", width=180, anchor=tk.CENTER)
        self.benchmark_tree.column("add_ms", width=180, anchor=tk.CENTER)
        self.benchmark_tree.column("mul_ms", width=180, anchor=tk.CENTER)
        self.benchmark_tree.pack(fill=tk.BOTH, expand=True)

        self.benchmark_summary_text = tk.Text(result_frame, wrap=tk.WORD, height=6)
        self.benchmark_summary_text.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

    def _build_log_tab(self) -> None:
        log_frame = ttk.Labelframe(
            self.log_tab,
            text="Dziennik operacji",
            padding=10,
            style="Card.TLabelframe",
            bootstyle="dark",
        )
        log_frame.pack(fill=tk.BOTH, expand=True)

        self.log_widget = tk.Text(log_frame, height=20, wrap=tk.WORD)
        self.log_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_widget.configure(yscrollcommand=scrollbar.set)

        ttk.Button(self.log_tab, text="Clear log", command=self.on_clear_log, bootstyle="secondary").pack(
            anchor=tk.E,
            pady=(8, 0),
        )

    def _log(self, message: str) -> None:
        self.log_widget.insert(tk.END, f"{message}\n")
        self.log_widget.see(tk.END)

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)
        self.root.update_idletasks()

    def _compact_series(self, values: list[int], max_items: int = 4) -> str:
        if not values:
            return "-"
        if len(values) <= max_items:
            return ", ".join(str(item) for item in values)
        preview = ", ".join(str(item) for item in values[:max_items])
        return f"{preview}, ... (total={len(values)})"

    def _render_flow(self, flow: DiseaseCountFlow) -> None:
        for item_id in self.process_tree.get_children():
            self.process_tree.delete(item_id)

        plain_values = [row.plain_value for row in flow.rows]
        ciphertexts = [row.ciphertext for row in flow.rows]

        self.process_plain_var.set(f"dane jawne: {self._compact_series(plain_values)}")
        self.process_cipher_var.set(f"szyfrogram: {self._compact_series(ciphertexts)}")
        self.process_homomorphic_var.set(
            f"wynik homomorficzny: {flow.encrypted_homomorphic_result}"
        )
        self.process_decrypted_var.set(
            f"odszyfrowany wynik: {flow.decrypted_result} (plain reference={flow.plain_reference})"
        )

        if not flow.rows:
            self.process_tree.insert("", tk.END, values=("<brak rekordow>", "-", "-"))
            return

        for row in flow.rows:
            self.process_tree.insert(
                "",
                tk.END,
                values=(row.pseudonym, row.plain_value, row.ciphertext),
            )

    def _render_encrypted_rows(self, rows: list[tuple[str, int]]) -> None:
        for item_id in self.encrypted_rows_tree.get_children():
            self.encrypted_rows_tree.delete(item_id)

        if not rows:
            self.encrypted_rows_tree.insert("", tk.END, values=("<brak rekordow>", "-"))
            return

        for pseudonym, ciphertext in rows:
            self.encrypted_rows_tree.insert("", tk.END, values=(pseudonym, ciphertext))

    def _render_validation_report(self, report: ValidationReport) -> None:
        for item_id in self.validation_tree.get_children():
            self.validation_tree.delete(item_id)

        if not report.results:
            self.validation_tree.insert("", tk.END, values=("-", "-", "-", "-", "-", "-"))
            return

        for result in report.results:
            self.validation_tree.insert(
                "",
                tk.END,
                values=(
                    result.disease,
                    result.homomorphic_sum,
                    result.plain_sum,
                    result.homomorphic_count,
                    result.plain_count,
                    "PASS" if result.is_valid else "FAIL",
                ),
            )

    def _render_pipeline_timeline(self, disease_name: str, flow: DiseaseCountFlow) -> None:
        lines = [
            "Pipeline (client -> cloud -> client)",
            f"1. Disease selected: {disease_name}",
            "2. Server reads encrypted flags for selected disease from SQLite.",
            "3. Server computes homomorphic aggregate ciphertext using multiplication mod n^2.",
            "4. Client decrypts aggregate result using private key.",
            "5. Client compares decrypted result with SQL plain SUM reference.",
            "",
            f"Rows in flow: {len(flow.rows)}",
            f"Homomorphic ciphertext result: {flow.encrypted_homomorphic_result}",
            f"Decrypted result: {flow.decrypted_result}",
            f"Plain reference: {flow.plain_reference}",
        ]

        self.pipeline_text.delete("1.0", tk.END)
        self.pipeline_text.insert("1.0", "\n".join(lines))

    def _update_summary(
        self,
        row_count: int,
        encrypted_sum: int,
        decrypted_sum: int,
        plain_sum_reference: int,
        is_valid: bool,
    ) -> None:
        self.summary_rows_var.set(f"Rows: {row_count}")
        self.summary_encrypted_var.set(f"Encrypted SUM: {encrypted_sum}")
        self.summary_decrypted_var.set(f"Decrypted SUM: {decrypted_sum}")
        self.summary_plain_var.set(f"Plain SUM reference: {plain_sum_reference}")
        self.validation_status_var.set(f"Validation: {'PASS' if is_valid else 'FAIL'}")

    def _parse_positive_int(self, value: str, field_name: str) -> int:
        parsed = int(value.strip())
        if parsed <= 0:
            raise ValueError(f"{field_name} must be positive")
        return parsed

    def _parse_key_sizes(self, raw: str) -> list[int]:
        values = [item.strip() for item in raw.split(",") if item.strip()]
        if not values:
            raise ValueError("Key sizes cannot be empty")

        key_sizes = [int(item) for item in values]
        for key_size in key_sizes:
            if key_size < 128:
                raise ValueError("Every key size must be at least 128")
        return key_sizes

    def _refresh_diagnosis_controls(self, disease_names: list[str]) -> None:
        for child in self.diagnoses_frame.winfo_children():
            child.destroy()

        self.diagnosis_vars.clear()

        for index, disease_name in enumerate(disease_names):
            value_var = tk.IntVar(value=0)
            self.diagnosis_vars[disease_name] = value_var
            ttk.Checkbutton(
                self.diagnoses_frame,
                text=disease_name,
                variable=value_var,
                onvalue=1,
                offvalue=0,
            ).grid(row=index // 3, column=index % 3, sticky=tk.W, padx=8, pady=2)

        self.disease_combobox.configure(values=disease_names)
        if disease_names:
            self.selected_disease_var.set(disease_names[0])

    def _refresh_mapping_table(self) -> None:
        if self.app is None:
            return

        mapping = self.app.repository.disease_mapping()
        for item_id in self.mapping_tree.get_children():
            self.mapping_tree.delete(item_id)
        for disease_name, numeric_code in mapping.items():
            self.mapping_tree.insert("", tk.END, values=(numeric_code, disease_name))

    def _create_or_load_app(self) -> ClientApplication:
        db_path = Path(self.db_path_var.get().strip()).resolve()
        keys_path = Path(self.keys_path_var.get().strip()).resolve()

        if (
            self.app is not None
            and self.loaded_db_path == db_path
            and self.loaded_keys_path == keys_path
        ):
            return self.app
        return self._load_existing_app()

    def _load_existing_app(self) -> ClientApplication:
        db_path = Path(self.db_path_var.get().strip()).resolve()
        keys_path = Path(self.keys_path_var.get().strip()).resolve()

        public_key, private_key = load_keypair(keys_path)
        app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
        app.initialize_catalog(list(DEFAULT_DISEASES))

        self.app = app
        self.loaded_db_path = db_path
        self.loaded_keys_path = keys_path
        self._refresh_diagnosis_controls(app.list_diseases())
        self._refresh_mapping_table()
        return app

    def on_setup_new(self) -> None:
        try:
            self._set_status("Generating keys and initializing project...")
            db_path = Path(self.db_path_var.get().strip()).resolve()
            keys_path = Path(self.keys_path_var.get().strip()).resolve()
            key_size = int(self.key_size_var.get().strip())

            if key_size < 128:
                raise ValueError("Key size must be at least 128")

            public_key, private_key = generate_keypair(key_size)
            save_keypair(keys_path, public_key, private_key)

            app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
            app.initialize_catalog(list(DEFAULT_DISEASES))
            existing_patients = app.repository.total_patients()
            if existing_patients:
                app.repository.clear_patient_data()

            self.app = app
            self.loaded_db_path = db_path
            self.loaded_keys_path = keys_path
            self._refresh_diagnosis_controls(app.list_diseases())
            self._refresh_mapping_table()
            self._log(
                f"Setup complete. db={db_path}, keys={keys_path}, diseases={', '.join(app.list_diseases())}"
            )
            if existing_patients:
                self._log(f"Existing patient records cleared after key rotation: {existing_patients}")
            self._set_status("Setup complete")
        except Exception as error:
            self._log(f"ERROR setup: {error}")
            messagebox.showerror("Setup error", str(error))
            self._set_status("Setup failed")

    def on_load_existing(self) -> None:
        try:
            self._set_status("Loading existing project...")
            app = self._load_existing_app()
            self._log(
                f"Loaded existing project. db={self.db_path_var.get()}, diseases={', '.join(app.list_diseases())}"
            )
            self._set_status("Project loaded")
        except Exception as error:
            self._log(f"ERROR load: {error}")
            messagebox.showerror("Load error", str(error))
            self._set_status("Load failed")

    def on_apply_theme(self) -> None:
        try:
            selected_theme = self.theme_var.get().strip() or "flatly"
            self.style.theme_use(selected_theme)
            self._configure_styles()
            self._log(f"Theme changed to: {selected_theme}")
            self._set_status(f"Theme applied: {selected_theme}")
        except Exception as error:
            self._log(f"ERROR apply-theme: {error}")
            messagebox.showerror("Theme error", str(error))
            self._set_status("Theme change failed")

    def on_list_diseases(self) -> None:
        try:
            app = self._create_or_load_app()
            self._refresh_mapping_table()
            mapping = app.repository.disease_mapping()
            self._log("Disease mapping refreshed")
            for disease_name, numeric_code in mapping.items():
                self._log(f"  {numeric_code}: {disease_name}")
            self._set_status("Disease mapping refreshed")
        except Exception as error:
            self._log(f"ERROR list-diseases: {error}")
            messagebox.showerror("List diseases error", str(error))
            self._set_status("List diseases failed")

    def on_seed_demo(self) -> None:
        try:
            self._set_status("Seeding demo data...")
            app = self._create_or_load_app()
            inserted = app.seed_demo_data()
            self._log(f"Inserted demo patients: {inserted}")
            self._set_status("Seed demo complete")
        except Exception as error:
            self._log(f"ERROR seed-demo: {error}")
            messagebox.showerror("Seed error", str(error))
            self._set_status("Seed demo failed")

    def on_seed_bulk(self) -> None:
        try:
            self._set_status("Seeding bulk synthetic data...")
            app = self._create_or_load_app()
            patient_count = self._parse_positive_int(self.bulk_patients_var.get(), "Bulk patients")
            seed_value = int(self.bulk_seed_var.get().strip())
            prefix = self.bulk_prefix_var.get().strip() or "bulk_patient"
            batch_size = self._parse_positive_int(self.bulk_batch_size_var.get(), "Batch size")

            started = perf_counter()
            inserted = app.seed_bulk_data(
                patient_count=patient_count,
                seed=seed_value,
                pseudonym_prefix=prefix,
                batch_size=batch_size,
            )
            elapsed = perf_counter() - started

            self._log(
                f"Inserted bulk patients: {inserted} (seed={seed_value}, batch_size={batch_size}, elapsed={elapsed:.3f}s)"
            )
            self._set_status("Seed bulk complete")
        except Exception as error:
            self._log(f"ERROR seed-bulk: {error}")
            messagebox.showerror("Seed bulk error", str(error))
            self._set_status("Seed bulk failed")

    def on_add_patient(self) -> None:
        try:
            self._set_status("Adding patient...")
            app = self._create_or_load_app()
            pseudonym = self.patient_name_var.get().strip()
            if not pseudonym:
                raise ValueError("Pseudonym cannot be empty")

            diagnoses = {name: variable.get() for name, variable in self.diagnosis_vars.items()}
            patient_id = app.add_patient(pseudonym, diagnoses)
            self.patient_name_var.set("")
            self._log(f"Inserted patient id={patient_id}, pseudonym={pseudonym}")
            self._set_status("Patient added")
        except Exception as error:
            self._log(f"ERROR add-patient: {error}")
            messagebox.showerror("Add patient error", str(error))
            self._set_status("Add patient failed")

    def on_count_disease(self) -> None:
        self._count_disease(show_rows=False)

    def on_count_with_rows(self) -> None:
        self._count_disease(show_rows=True)

    def _count_disease(self, show_rows: bool) -> None:
        try:
            self._set_status("Running server-side encrypted count/sum...")
            app = self._create_or_load_app()
            disease_name = self.selected_disease_var.get().strip()
            if not disease_name:
                raise ValueError("Choose disease first")

            result = app.count_and_sum_disease(disease_name)
            flow = app.build_count_flow(disease_name)
            encrypted_rows = app.repository.get_encrypted_rows_for_disease(disease_name)
            self._render_flow(flow)
            self._render_encrypted_rows(encrypted_rows)
            self._render_pipeline_timeline(disease_name, flow)

            is_valid = (
                result.decrypted_count == result.plain_count_reference
                and result.decrypted_sum == result.plain_sum_reference
            )
            self._update_summary(
                row_count=result.row_count,
                encrypted_sum=result.encrypted_sum,
                decrypted_sum=result.decrypted_sum,
                plain_sum_reference=result.plain_sum_reference,
                is_valid=is_valid,
            )

            self._log(
                " | ".join(
                    [
                        f"Disease={result.disease}",
                        f"Rows={result.row_count}",
                        f"Encrypted COUNT={result.encrypted_count}",
                        f"Encrypted SUM={result.encrypted_sum}",
                        f"Decrypted COUNT={result.decrypted_count}",
                        f"Decrypted SUM={result.decrypted_sum}",
                        f"Plain COUNT ref={result.plain_count_reference}",
                        f"Plain SUM ref={result.plain_sum_reference}",
                        f"Validation={is_valid}",
                    ]
                )
            )

            if show_rows:
                self._log(f"Flow rows for {disease_name}: plain -> ciphertext")
                for row in flow.rows:
                    self._log(f"  {row.pseudonym}: {row.plain_value} -> {row.ciphertext}")
            self.analytics_notebook.select(0)
            self._set_status("Count and flow ready")
        except Exception as error:
            self._log(f"ERROR count: {error}")
            messagebox.showerror("Count error", str(error))
            self._set_status("Count failed")

    def on_show_encrypted_rows(self) -> None:
        try:
            app = self._create_or_load_app()
            disease_name = self.selected_disease_var.get().strip()
            if not disease_name:
                raise ValueError("Choose disease first")

            rows = app.repository.get_encrypted_rows_for_disease(disease_name)
            self._render_encrypted_rows(rows)
            self.analytics_notebook.select(1)
            self._log(f"Encrypted rows rendered for disease={disease_name}, rows={len(rows)}")
            self._set_status("Encrypted rows rendered")
        except Exception as error:
            self._log(f"ERROR show-encrypted: {error}")
            messagebox.showerror("Show encrypted rows error", str(error))
            self._set_status("Show encrypted failed")

    def on_validate_selected(self) -> None:
        try:
            self._set_status("Validating selected disease...")
            app = self._create_or_load_app()
            disease_name = self.selected_disease_var.get().strip()
            if not disease_name:
                raise ValueError("Choose disease first")

            validation = app.validate_disease_sum(disease_name)
            report = ValidationReport(
                results=[validation],
                total_diseases=1,
                passed_diseases=1 if validation.is_valid else 0,
                all_valid=validation.is_valid,
            )
            self._render_validation_report(report)
            self.analytics_notebook.select(2)
            self.validation_status_var.set(
                f"Validation: {'PASS' if validation.is_valid else 'FAIL'}"
            )
            self._log(
                " | ".join(
                    [
                        f"Validate disease={validation.disease}",
                        f"homomorphic_sum={validation.homomorphic_sum}",
                        f"plain_sum={validation.plain_sum}",
                        f"status={validation.is_valid}",
                    ]
                )
            )
            self._set_status("Validation for selected disease complete")
        except Exception as error:
            self._log(f"ERROR validate-selected: {error}")
            messagebox.showerror("Validate selected error", str(error))
            self._set_status("Validate selected failed")

    def on_validate_all(self) -> None:
        try:
            self._set_status("Validating all diseases...")
            app = self._create_or_load_app()
            report = app.validate_all_disease_sums()
            self._render_validation_report(report)
            self.analytics_notebook.select(2)
            self.validation_status_var.set(
                f"Validation: {'PASS' if report.all_valid else 'FAIL'} ({report.passed_diseases}/{report.total_diseases})"
            )
            self._log(
                f"Validation summary: passed={report.passed_diseases}/{report.total_diseases}, all_valid={report.all_valid}"
            )
            for result in report.results:
                self._log(
                    f"  disease={result.disease}, homomorphic_sum={result.homomorphic_sum}, plain_sum={result.plain_sum}, status={result.is_valid}"
                )
            self._set_status("Validation for all diseases complete")
        except Exception as error:
            self._log(f"ERROR validate-all: {error}")
            messagebox.showerror("Validate all error", str(error))
            self._set_status("Validate all failed")

    def _render_benchmark_results(self, results: list[KeySizeBenchmarkResult]) -> None:
        for item_id in self.benchmark_tree.get_children():
            self.benchmark_tree.delete(item_id)

        for result in results:
            self.benchmark_tree.insert(
                "",
                tk.END,
                values=(
                    result.key_size,
                    f"{result.keygen_seconds * 1000.0:.3f}",
                    f"{result.encrypt_timing.average_ms:.3f}",
                    f"{result.decrypt_timing.average_ms:.3f}",
                    f"{result.homomorphic_add_timing.average_ms:.3f}",
                    f"{result.homomorphic_mul_timing.average_ms:.3f}",
                ),
            )

        lines: list[str] = []
        for result in results:
            lines.append(
                " | ".join(
                    [
                        f"key={result.key_size}",
                        f"keygen={result.keygen_seconds * 1000.0:.3f}ms",
                        f"enc={result.encrypt_timing.average_ms:.3f}ms",
                        f"dec={result.decrypt_timing.average_ms:.3f}ms",
                        f"add={result.homomorphic_add_timing.average_ms:.3f}ms",
                        f"mul={result.homomorphic_mul_timing.average_ms:.3f}ms",
                    ]
                )
            )

        self.benchmark_summary_text.delete("1.0", tk.END)
        self.benchmark_summary_text.insert("1.0", "\n".join(lines))

    def on_run_benchmark(self) -> None:
        try:
            self._set_status("Running crypto benchmark...")
            key_sizes = self._parse_key_sizes(self.benchmark_key_sizes_var.get())
            encrypt_iterations = self._parse_positive_int(
                self.benchmark_encrypt_iterations_var.get(),
                "Encrypt iterations",
            )
            decrypt_iterations = self._parse_positive_int(
                self.benchmark_decrypt_iterations_var.get(),
                "Decrypt iterations",
            )
            homomorphic_iterations = self._parse_positive_int(
                self.benchmark_homomorphic_iterations_var.get(),
                "Homomorphic iterations",
            )
            batch_size = self._parse_positive_int(
                self.benchmark_batch_size_var.get(),
                "Batch size",
            )

            started = perf_counter()
            results = run_crypto_benchmark(
                key_sizes=key_sizes,
                encrypt_iterations=encrypt_iterations,
                decrypt_iterations=decrypt_iterations,
                homomorphic_iterations=homomorphic_iterations,
                homomorphic_batch_size=batch_size,
            )
            elapsed = perf_counter() - started
            self.last_benchmark_results = results
            self._render_benchmark_results(results)
            self.main_notebook.select(3)
            self._log(
                f"Benchmark complete for key_sizes={key_sizes} in {elapsed:.3f}s"
            )
            self._set_status("Benchmark complete")
        except Exception as error:
            self._log(f"ERROR benchmark: {error}")
            messagebox.showerror("Benchmark error", str(error))
            self._set_status("Benchmark failed")

    def on_export_benchmark_report(self) -> None:
        if not self.last_benchmark_results:
            messagebox.showwarning("No benchmark data", "Run benchmark first.")
            return

        try:
            report_path = Path(self.benchmark_report_path_var.get().strip())
            report_path.parent.mkdir(parents=True, exist_ok=True)

            lines = [
                "# Dane wydajnosciowe (GUI benchmark)",
                "",
                "| Key size | Keygen [ms] | Encrypt avg [ms] | Decrypt avg [ms] | Add_many avg [ms] | Mul_const avg [ms] |",
                "| --- | ---: | ---: | ---: | ---: | ---: |",
            ]

            for result in self.last_benchmark_results:
                lines.append(
                    "| "
                    + f"{result.key_size} | "
                    + f"{result.keygen_seconds * 1000.0:.3f} | "
                    + f"{result.encrypt_timing.average_ms:.3f} | "
                    + f"{result.decrypt_timing.average_ms:.3f} | "
                    + f"{result.homomorphic_add_timing.average_ms:.3f} | "
                    + f"{result.homomorphic_mul_timing.average_ms:.3f} |"
                )

            report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            self._log(f"Benchmark report exported: {report_path}")
            self._set_status("Benchmark report exported")
        except Exception as error:
            self._log(f"ERROR export-benchmark-report: {error}")
            messagebox.showerror("Export benchmark report error", str(error))
            self._set_status("Benchmark export failed")

    def on_clear_log(self) -> None:
        self.log_widget.delete("1.0", tk.END)
        self._set_status("Log cleared")


def main() -> int:
    root = ttk.Window(themename="flatly")
    TrackerGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
