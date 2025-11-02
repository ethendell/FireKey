"""Tkinter-based GUI for exporting FireKey metadata."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tkinter import (  # type: ignore
    BOTH,
    END,
    LEFT,
    Button,
    Checkbutton,
    Entry,
    Frame,
    Label,
    Listbox,
    OptionMenu,
    StringVar,
    Tk,
    messagebox,
)
from tkinter import filedialog
from typing import List, Optional

from .data import load_sample_metadata
from .exporter import ExportResult, ExportSummary, Exporter, SUPPORTED_FORMATS


@dataclass
class AppState:
    records: List[dict]
    model: StringVar
    tokens: StringVar
    cost: StringVar
    format_var: StringVar
    include_posters: StringVar


class FireKeyApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("FireKey Export Manager")
        self.exporter = Exporter()

        records = load_sample_metadata()
        self.state = AppState(
            records=records,
            model=StringVar(value="gpt-4.1"),
            tokens=StringVar(value="1820"),
            cost=StringVar(value="3.12"),
            format_var=StringVar(value="CSV"),
            include_posters=StringVar(value="1"),
        )

        self.last_export: Optional[ExportResult] = None

        self._build_header()
        self._build_record_list()
        self._build_controls()

    # ------------------------------------------------------------------
    def _build_header(self) -> None:
        header = Frame(self.root)
        header.pack(fill=BOTH, padx=10, pady=(10, 0))

        Label(header, text="Model").pack(side=LEFT)
        Entry(header, textvariable=self.state.model, width=12).pack(side=LEFT, padx=(4, 12))

        Label(header, text="Tokens").pack(side=LEFT)
        Entry(header, textvariable=self.state.tokens, width=8).pack(side=LEFT, padx=(4, 12))

        Label(header, text="Cost ($)").pack(side=LEFT)
        Entry(header, textvariable=self.state.cost, width=8).pack(side=LEFT, padx=(4, 12))

        Label(header, text="Format").pack(side=LEFT)
        OptionMenu(header, self.state.format_var, *SUPPORTED_FORMATS).pack(side=LEFT)

        Checkbutton(
            header,
            text="Include poster frames",
            variable=self.state.include_posters,
            onvalue="1",
            offvalue="0",
        ).pack(side=LEFT, padx=(12, 0))

    def _build_record_list(self) -> None:
        wrapper = Frame(self.root)
        wrapper.pack(fill=BOTH, expand=True, padx=10, pady=10)
        Label(wrapper, text="Metadata Preview").pack(anchor="w")
        self.record_list = Listbox(wrapper, width=80, height=8)
        self.record_list.pack(fill=BOTH, expand=True, pady=(4, 0))
        for record in self.state.records:
            display = f"{record.get('filename')} - {record.get('title')}"
            self.record_list.insert(END, display)

    def _build_controls(self) -> None:
        controls = Frame(self.root)
        controls.pack(fill=BOTH, padx=10, pady=10)

        Button(controls, text="Export", command=self._handle_export).pack(side=LEFT)
        Button(controls, text="Open Export Folder", command=self._open_folder).pack(side=LEFT, padx=6)
        Button(controls, text="Copy CSV Path", command=self._copy_csv_path).pack(side=LEFT, padx=6)

    # Actions -----------------------------------------------------------
    def _handle_export(self) -> None:
        try:
            summary = self._build_summary()
        except ValueError as exc:
            messagebox.showerror("Export error", str(exc))
            return

        fmt = self.state.format_var.get().upper()
        include_posters = fmt == "CSV" and self.state.include_posters.get() == "1"
        destination_path = None
        if fmt != "CSV":
            filetypes = [(f"{fmt} file", f"*.{fmt.lower()}")]
            destination = filedialog.asksaveasfilename(defaultextension=f".{fmt.lower()}", filetypes=filetypes)
            if not destination:
                return
            destination_path = Path(destination)

        try:
            self.last_export = self.exporter.export(
                self.state.records,
                fmt,
                summary,
                include_poster_frames=include_posters,
                output_path=destination_path,
            )
        except Exception as exc:  # pragma: no cover - user feedback path
            messagebox.showerror("Export failed", str(exc))
            return

        if not self.last_export.metadata_path:
            messagebox.showinfo("Export complete", "Export finished but no metadata file was produced.")
            return

        message = [f"Metadata saved to: {self.last_export.metadata_path}"]
        if self.last_export.summary_path:
            message.append(f"Summary saved to: {self.last_export.summary_path}")
        if self.last_export.poster_frame_paths:
            message.append(f"Poster frames copied: {len(self.last_export.poster_frame_paths)}")
        messagebox.showinfo("Export complete", "\n".join(message))

    def _build_summary(self) -> ExportSummary:
        try:
            tokens = int(self.state.tokens.get())
        except ValueError as exc:
            raise ValueError("Tokens must be a whole number") from exc
        try:
            cost = float(self.state.cost.get())
        except ValueError as exc:
            raise ValueError("Cost must be numeric") from exc

        return ExportSummary(
            model=self.state.model.get() or "Unknown",
            tokens=tokens,
            cost=round(cost, 2),
        )

    def _open_folder(self) -> None:
        if not self.last_export or not self.last_export.folder:
            messagebox.showinfo("No export", "Run a CSV export before opening the folder.")
            return
        folder = self.last_export.folder
        try:
            from .exporter import open_folder

            open_folder(folder)
        except Exception as exc:  # pragma: no cover - user feedback
            messagebox.showerror("Unable to open folder", str(exc))

    def _copy_csv_path(self) -> None:
        if not self.last_export or not self.last_export.metadata_path:
            messagebox.showinfo("No CSV", "Run an export before copying the path.")
            return
        path = self.last_export.metadata_path
        self.root.clipboard_clear()
        self.root.clipboard_append(str(path))
        self.root.update()
        messagebox.showinfo("Copied", "CSV path copied to clipboard.")


def launch() -> None:
    root = Tk()
    app = FireKeyApp(root)
    root.mainloop()


if __name__ == "__main__":  # pragma: no cover - GUI entry point
    launch()
"""Tkinter-based GUI for FireKEY."""
from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from .config import AppConfig
from .prompt_loader import PromptRepository


class FireKeyApp:
    """Main application window."""

    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("FireKEY")
        self.repo = PromptRepository()
        self.config = AppConfig.load()
        self.templates = self.repo.list_templates()
        self.display_to_file: Dict[str, str] = {}

        self.template_var = tk.StringVar()
        self.type_var = tk.StringVar(value="photo")

        self._build_ui()
        self._load_templates_into_dropdown()

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        padding = {"padx": 12, "pady": 6}

        main_frame = ttk.Frame(self.root, padding=padding)
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)

        # Prompt template dropdown
        ttk.Label(main_frame, text="Prompt Template:").grid(row=0, column=0, sticky="w", **padding)
        self.template_combo = ttk.Combobox(main_frame, textvariable=self.template_var, state="readonly")
        self.template_combo.grid(row=0, column=1, sticky="ew", **padding)
        self.template_combo.bind("<<ComboboxSelected>>", self._on_template_change)

        # Type selection
        ttk.Label(main_frame, text="Content Type:").grid(row=1, column=0, sticky="w", **padding)
        self.type_combo = ttk.Combobox(main_frame, textvariable=self.type_var, values=["photo", "video"], state="readonly")
        self.type_combo.grid(row=1, column=1, sticky="ew", **padding)

        # Context input
        ttk.Label(main_frame, text="Context:").grid(row=2, column=0, sticky="nw", **padding)
        self.context_text = tk.Text(main_frame, width=60, height=6)
        self.context_text.grid(row=2, column=1, sticky="ew", **padding)

        # Process button
        process_button = ttk.Button(main_frame, text="Process", command=self._process)
        process_button.grid(row=3, column=1, sticky="e", **padding)

        # Output area
        ttk.Label(main_frame, text="System Prompt:").grid(row=4, column=0, sticky="nw", **padding)
        self.system_output = tk.Text(main_frame, width=60, height=5, state="disabled")
        self.system_output.grid(row=4, column=1, sticky="ew", **padding)

        ttk.Label(main_frame, text="User Prompt:").grid(row=5, column=0, sticky="nw", **padding)
        self.user_output = tk.Text(main_frame, width=60, height=5, state="disabled")
        self.user_output.grid(row=5, column=1, sticky="ew", **padding)

    def _load_templates_into_dropdown(self) -> None:
        self.templates = self.repo.list_templates()
        self.display_to_file.clear()
        options: List[str] = []
        for template in self.templates:
            display_name = f"{template.name} ({template.file_name})"
            self.display_to_file[display_name] = template.file_name
            options.append(display_name)
        self.template_combo["values"] = options

        default_display = None
        if self.config.last_template:
            default_display = self._display_for_file(self.config.last_template)
        if default_display is None and options:
            default_display = options[0]
        if default_display:
            self.template_var.set(default_display)
        else:
            self.template_var.set("")

    # ---------------------------------------------------------------- events
    def _display_for_file(self, file_name: str) -> Optional[str]:
        for display, stored_file in self.display_to_file.items():
            if stored_file == file_name:
                return display
        return None

    def _on_template_change(self, _event=None) -> None:  # type: ignore[override]
        file_name = self._selected_file_name()
        if not file_name:
            return
        self.config.last_template = file_name
        self.config.save()

    def _selected_file_name(self) -> Optional[str]:
        display = self.template_var.get()
        return self.display_to_file.get(display)

    def _process(self) -> None:
        file_name = self._selected_file_name()
        if not file_name:
            messagebox.showerror("No Template", "Please choose a prompt template before processing.")
            return
        template = self.repo.get(file_name)
        if template is None:
            messagebox.showerror("Missing Template", "The selected template could not be loaded.")
            return
        content_type = self.type_var.get() or "photo"
        context = self.context_text.get("1.0", tk.END).strip()
        rendered = template.render(type_value=content_type, context=context)
        self._set_text(self.system_output, rendered["system_prompt"])
        self._set_text(self.user_output, rendered["user_prompt"])
        self.config.last_template = file_name
        self.config.save()

    def _set_text(self, widget: tk.Text, value: str) -> None:
        widget.configure(state="normal")
        widget.delete("1.0", tk.END)
        widget.insert("1.0", value)
        widget.configure(state="disabled")

    def run(self) -> None:
        self.root.mainloop()


def run_app() -> None:
    app = FireKeyApp()
    if not app.templates:
        messagebox.showwarning(
            "No Templates Found",
            "No prompt templates were discovered. Add .txt templates to the prompts directory to begin.",
        )
    app.run()


__all__ = ["FireKeyApp", "run_app"]
