import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText


class FireKeyApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FireKey")
        self.selected_folder: str | None = None

        self._configure_grid()
        self._create_widgets()

    def _configure_grid(self) -> None:
        self.root.columnconfigure(0, weight=3, minsize=400)
        self.root.columnconfigure(1, weight=2, minsize=300)
        self.root.rowconfigure(0, weight=1)

    def _create_widgets(self) -> None:
        self.preview_label = tk.Label(
            self.root,
            text="Image Preview",
            anchor="center",
            bg="lightgray",
            fg="black",
            relief=tk.SUNKEN,
        )
        self.preview_label.grid(column=0, row=0, sticky="nsew", padx=(10, 5), pady=10)

        controls_frame = ttk.Frame(self.root, padding=10)
        controls_frame.grid(column=1, row=0, sticky="nsew")
        controls_frame.columnconfigure(0, weight=1)

        folder_button = ttk.Button(
            controls_frame,
            text="Select Folder",
            command=self.select_folder,
        )
        folder_button.grid(column=0, row=0, sticky="ew", pady=(0, 10))

        model_label = ttk.Label(controls_frame, text="Model")
        model_label.grid(column=0, row=1, sticky="w")

        self.model_var = tk.StringVar(value="gpt-4o-mini")
        model_dropdown = ttk.Combobox(
            controls_frame,
            textvariable=self.model_var,
            values=("gpt-4o-mini", "gpt-4o"),
            state="readonly",
        )
        model_dropdown.grid(column=0, row=2, sticky="ew", pady=(0, 10))

        creativity_label = ttk.Label(controls_frame, text="Creativity")
        creativity_label.grid(column=0, row=3, sticky="w")

        self.creativity_var = tk.DoubleVar(value=0.5)
        self.creativity_display = ttk.Label(controls_frame, text="0.50")
        self.creativity_display.grid(column=0, row=4, sticky="e", pady=(0, 2))

        self.creativity_scale = ttk.Scale(
            controls_frame,
            from_=0.1,
            to=1.0,
            orient="horizontal",
            variable=self.creativity_var,
            command=self._update_creativity_display,
        )
        self.creativity_scale.grid(column=0, row=5, sticky="ew", pady=(0, 10))

        context_label = ttk.Label(controls_frame, text="Context")
        context_label.grid(column=0, row=6, sticky="w")

        self.context_text = ScrolledText(controls_frame, height=6, wrap=tk.WORD)
        self.context_text.grid(column=0, row=7, sticky="nsew", pady=(0, 10))
        controls_frame.rowconfigure(7, weight=1)

        process_button = ttk.Button(
            controls_frame,
            text="Process",
            command=self.process_folder,
        )
        process_button.grid(column=0, row=8, sticky="ew", pady=(0, 10))

        log_label = ttk.Label(controls_frame, text="Log Output")
        log_label.grid(column=0, row=9, sticky="w")

        self.log_output = ScrolledText(
            controls_frame,
            height=10,
            state="disabled",
            wrap=tk.WORD,
        )
        self.log_output.grid(column=0, row=10, sticky="nsew")
        controls_frame.rowconfigure(10, weight=1)

    def _update_creativity_display(self, _event: str | None = None) -> None:
        value = self.creativity_var.get()
        self.creativity_display.configure(text=f"{value:.2f}")

    def select_folder(self) -> None:
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder = folder
            self._append_log(f"Selected folder: {folder}")

    def process_folder(self) -> None:
        if not self.selected_folder:
            self._append_log("Please select a folder before processing.")
            return

        model = self.model_var.get()
        creativity = self.creativity_var.get()
        context = self.context_text.get("1.0", tk.END).strip()

        self._append_log(
            "Processing folder with settings: "
            f"model={model}, creativity={creativity:.2f}, context length={len(context)}"
        )
        # Placeholder for actual processing logic
        self._append_log("process_folder() called.")

    def _append_log(self, message: str) -> None:
        self.log_output.configure(state="normal")
        self.log_output.insert(tk.END, message + "\n")
        self.log_output.see(tk.END)
        self.log_output.configure(state="disabled")


def main() -> None:
    root = tk.Tk()
    app = FireKeyApp(root)
    root.geometry("1000x600")
    root.minsize(800, 500)
    root.mainloop()


if __name__ == "__main__":
    main()
