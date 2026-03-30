from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from ..client import ClientApplication
from ..config import DEFAULT_DB_PATH, DEFAULT_DISEASES, DEFAULT_KEY_SIZE, DEFAULT_KEYS_PATH
from ..crypto import generate_keypair
from ..keys import load_keypair, save_keypair


class TrackerGUI:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Paillier Disease Tracker GUI (wstepny)")
        self.root.geometry("980x680")

        self.app: ClientApplication | None = None
        self.diagnosis_vars: dict[str, tk.IntVar] = {}

        self.db_path_var = tk.StringVar(value=str(DEFAULT_DB_PATH))
        self.keys_path_var = tk.StringVar(value=str(DEFAULT_KEYS_PATH))
        self.key_size_var = tk.StringVar(value=str(DEFAULT_KEY_SIZE))
        self.patient_name_var = tk.StringVar(value="")
        self.selected_disease_var = tk.StringVar(value=DEFAULT_DISEASES[0])

        self._build_layout()
        self._refresh_diagnosis_controls(list(DEFAULT_DISEASES))
        self._log("GUI gotowe. Uzyj Setup new albo Load existing.")

    def _build_layout(self) -> None:
        container = ttk.Frame(self.root, padding=12)
        container.pack(fill=tk.BOTH, expand=True)

        config_frame = ttk.LabelFrame(container, text="Konfiguracja", padding=10)
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

        ttk.Button(config_frame, text="Setup new", command=self.on_setup_new).grid(
            row=0, column=2, padx=6
        )
        ttk.Button(config_frame, text="Load existing", command=self.on_load_existing).grid(
            row=1, column=2, padx=6
        )
        ttk.Button(config_frame, text="Seed demo", command=self.on_seed_demo).grid(
            row=2, column=2, padx=6
        )

        patient_frame = ttk.LabelFrame(container, text="Dodawanie pacjenta", padding=10)
        patient_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(patient_frame, text="Pseudonym").grid(row=0, column=0, sticky=tk.W)
        ttk.Entry(patient_frame, textvariable=self.patient_name_var, width=40).grid(
            row=0, column=1, sticky=tk.W, padx=8
        )

        self.diagnoses_frame = ttk.Frame(patient_frame)
        self.diagnoses_frame.grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=(8, 0))

        ttk.Button(patient_frame, text="Add patient", command=self.on_add_patient).grid(
            row=0, column=2, padx=6
        )

        analytics_frame = ttk.LabelFrame(container, text="Analityka serwerowa", padding=10)
        analytics_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Label(analytics_frame, text="Disease").grid(row=0, column=0, sticky=tk.W)
        self.disease_combobox = ttk.Combobox(
            analytics_frame,
            textvariable=self.selected_disease_var,
            state="readonly",
            values=list(DEFAULT_DISEASES),
            width=30,
        )
        self.disease_combobox.grid(row=0, column=1, sticky=tk.W, padx=8)

        ttk.Button(analytics_frame, text="Count encrypted", command=self.on_count_disease).grid(
            row=0, column=2, padx=6
        )
        ttk.Button(
            analytics_frame,
            text="Count + show ciphertexts",
            command=self.on_count_with_rows,
        ).grid(row=0, column=3, padx=6)

        log_frame = ttk.LabelFrame(container, text="Log", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))

        self.log_widget = tk.Text(log_frame, height=16, wrap=tk.WORD)
        self.log_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_widget.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_widget.configure(yscrollcommand=scrollbar.set)

    def _log(self, message: str) -> None:
        self.log_widget.insert(tk.END, f"{message}\n")
        self.log_widget.see(tk.END)

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

    def _create_or_load_app(self) -> ClientApplication:
        if self.app is not None:
            return self.app
        return self._load_existing_app()

    def _load_existing_app(self) -> ClientApplication:
        db_path = Path(self.db_path_var.get().strip())
        keys_path = Path(self.keys_path_var.get().strip())

        public_key, private_key = load_keypair(keys_path)
        app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
        app.initialize_catalog(list(DEFAULT_DISEASES))

        self.app = app
        self._refresh_diagnosis_controls(app.list_diseases())
        return app

    def on_setup_new(self) -> None:
        try:
            db_path = Path(self.db_path_var.get().strip())
            keys_path = Path(self.keys_path_var.get().strip())
            key_size = int(self.key_size_var.get().strip())

            if key_size < 128:
                raise ValueError("Key size must be at least 128")

            public_key, private_key = generate_keypair(key_size)
            save_keypair(keys_path, public_key, private_key)

            app = ClientApplication(db_path=db_path, public_key=public_key, private_key=private_key)
            app.initialize_catalog(list(DEFAULT_DISEASES))

            self.app = app
            self._refresh_diagnosis_controls(app.list_diseases())
            self._log(
                f"Setup complete. db={db_path}, keys={keys_path}, diseases={', '.join(app.list_diseases())}"
            )
        except Exception as error:
            self._log(f"ERROR setup: {error}")
            messagebox.showerror("Setup error", str(error))

    def on_load_existing(self) -> None:
        try:
            app = self._load_existing_app()
            self._log(
                f"Loaded existing project. db={self.db_path_var.get()}, diseases={', '.join(app.list_diseases())}"
            )
        except Exception as error:
            self._log(f"ERROR load: {error}")
            messagebox.showerror("Load error", str(error))

    def on_seed_demo(self) -> None:
        try:
            app = self._create_or_load_app()
            inserted = app.seed_demo_data()
            self._log(f"Inserted demo patients: {inserted}")
        except Exception as error:
            self._log(f"ERROR seed-demo: {error}")
            messagebox.showerror("Seed error", str(error))

    def on_add_patient(self) -> None:
        try:
            app = self._create_or_load_app()
            pseudonym = self.patient_name_var.get().strip()
            if not pseudonym:
                raise ValueError("Pseudonym cannot be empty")

            diagnoses = {name: variable.get() for name, variable in self.diagnosis_vars.items()}
            patient_id = app.add_patient(pseudonym, diagnoses)
            self.patient_name_var.set("")
            self._log(f"Inserted patient id={patient_id}, pseudonym={pseudonym}")
        except Exception as error:
            self._log(f"ERROR add-patient: {error}")
            messagebox.showerror("Add patient error", str(error))

    def on_count_disease(self) -> None:
        self._count_disease(show_rows=False)

    def on_count_with_rows(self) -> None:
        self._count_disease(show_rows=True)

    def _count_disease(self, show_rows: bool) -> None:
        try:
            app = self._create_or_load_app()
            disease_name = self.selected_disease_var.get().strip()
            if not disease_name:
                raise ValueError("Choose disease first")

            result = app.count_disease(disease_name)
            self._log(
                " | ".join(
                    [
                        f"Disease={result.disease}",
                        f"Encrypted aggregate={result.encrypted_result}",
                        f"Decrypted result={result.decrypted_result}",
                        f"Plain reference={result.plain_reference}",
                        f"Validation={result.decrypted_result == result.plain_reference}",
                    ]
                )
            )

            if show_rows:
                rows = app.repository.get_encrypted_rows_for_disease(disease_name)
                self._log(f"Ciphertexts for {disease_name}:")
                for pseudonym, ciphertext in rows:
                    self._log(f"  {pseudonym}: {ciphertext}")
        except Exception as error:
            self._log(f"ERROR count: {error}")
            messagebox.showerror("Count error", str(error))


def main() -> int:
    root = tk.Tk()
    TrackerGUI(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
