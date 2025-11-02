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
