"""FireKey Tkinter GUI application.

This module defines a Tkinter-based graphical user interface that offers
media preview, processing controls, options, and logging functionality.
"""

from __future__ import annotations

import queue
import threading
import time
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from PIL import Image, ImageDraw, ImageOps, ImageTk
except ImportError as exc:  # pragma: no cover - Pillow is required for GUI
    raise RuntimeError("Pillow is required to run this application") from exc

# Supported file extensions
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".gif", ".tiff", ".webp"}
VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".mpeg", ".mpg"}


class FireKeyApp:
    """Main application class encapsulating the FireKey GUI."""

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("FireKey Media Processor")
        self.root.geometry("1024x720")

        # Media state
        self.selected_media: Optional[Path] = None
        self.media_type: Optional[str] = None  # "image" or "video"
        self.preview_photo: Optional[ImageTk.PhotoImage] = None
        self.poster_frame_image: Optional[Image.Image] = None

        # Tkinter variables
        self.frame_count_var = tk.IntVar(value=10)
        self.fidelity_var = tk.StringVar(value="HiFi")
        self.include_gps_var = tk.BooleanVar(value=False)
        self.use_poster_frame_var = tk.BooleanVar(value=True)
        self.progress_var = tk.DoubleVar(value=0.0)
        self.token_estimate_var = tk.StringVar(value="Tokens: 0")
        self.elapsed_time_var = tk.StringVar(value="Elapsed: 00:00")

        # Processing state
        self.processing_thread: Optional[threading.Thread] = None
        self.stop_event = threading.Event()
        self.event_queue: queue.Queue[tuple] = queue.Queue()
        self.processing_start_time: Optional[float] = None

        self._build_ui()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        """Construct all GUI widgets."""

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main_frame = ttk.Frame(self.root, padding=12)
        main_frame.grid(row=0, column=0, sticky="nsew")
        main_frame.columnconfigure(0, weight=3)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)

        # Preview Pane --------------------------------------------------
        preview_frame = ttk.LabelFrame(main_frame, text="Preview", padding=8)
        preview_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12))
        preview_frame.columnconfigure(0, weight=1)
        preview_frame.rowconfigure(0, weight=1)

        self.preview_label = ttk.Label(preview_frame, anchor="center")
        self.preview_label.grid(row=0, column=0, sticky="nsew")
        self._show_placeholder("No media loaded")

        # Right-hand side container for options and controls ------------
        rhs_container = ttk.Frame(main_frame)
        rhs_container.grid(row=0, column=1, sticky="nsew")
        rhs_container.columnconfigure(0, weight=1)

        # Options panel -------------------------------------------------
        options_frame = ttk.LabelFrame(rhs_container, text="Options", padding=12)
        options_frame.grid(row=0, column=0, sticky="nsew")
        for i in range(4):
            options_frame.rowconfigure(i, weight=1)
        options_frame.columnconfigure(1, weight=1)

        ttk.Label(options_frame, text="Frame Count:").grid(row=0, column=0, sticky="w", pady=4)
        self.frame_count_spinbox = ttk.Spinbox(
            options_frame,
            from_=1,
            to=1000,
            textvariable=self.frame_count_var,
            width=8,
        )
        self.frame_count_spinbox.grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(options_frame, text="Fidelity:").grid(row=1, column=0, sticky="w", pady=4)
        fidelity_combo = ttk.Combobox(
            options_frame,
            textvariable=self.fidelity_var,
            values=("LoFi", "HiFi"),
            state="readonly",
        )
        fidelity_combo.grid(row=1, column=1, sticky="ew", pady=4)

        include_gps_check = ttk.Checkbutton(
            options_frame,
            text="Include GPS metadata",
            variable=self.include_gps_var,
        )
        include_gps_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=4)

        use_poster_check = ttk.Checkbutton(
            options_frame,
            text="Use Poster Frame",
            variable=self.use_poster_frame_var,
            command=self.refresh_preview,
        )
        use_poster_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        # Control buttons -----------------------------------------------
        controls_frame = ttk.Frame(rhs_container)
        controls_frame.grid(row=1, column=0, sticky="ew", pady=12)
        controls_frame.columnconfigure((0, 1, 2), weight=1)

        open_button = ttk.Button(controls_frame, text="Open Media", command=self.open_media)
        open_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))

        self.process_button = ttk.Button(
            controls_frame,
            text="Start Processing",
            command=self.start_processing,
        )
        self.process_button.grid(row=0, column=1, sticky="ew", padx=6)

        self.stop_button = ttk.Button(
            controls_frame,
            text="Stop",
            command=self.request_stop,
            state="disabled",
        )
        self.stop_button.grid(row=0, column=2, sticky="ew", padx=(6, 0))

        # Progress section ----------------------------------------------
        progress_frame = ttk.LabelFrame(rhs_container, text="Progress", padding=12)
        progress_frame.grid(row=2, column=0, sticky="ew")
        progress_frame.columnconfigure(0, weight=1)

        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
        )
        self.progress_bar.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        self.token_label = ttk.Label(progress_frame, textvariable=self.token_estimate_var)
        self.token_label.grid(row=1, column=0, sticky="w")

        self.elapsed_label = ttk.Label(progress_frame, textvariable=self.elapsed_time_var)
        self.elapsed_label.grid(row=2, column=0, sticky="w", pady=(4, 0))

        # Log area ------------------------------------------------------
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding=8)
        log_frame.grid(row=1, column=1, sticky="nsew", pady=(12, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = ScrolledText(log_frame, height=12, wrap="word", state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")

        self._log("Ready.")

    # ------------------------------------------------------------------
    # Media management
    # ------------------------------------------------------------------
    def open_media(self) -> None:
        """Open a media file and update the preview pane."""
        filetypes = (
            ("Media files", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp *.mp4 *.mov *.avi *.mkv *.wmv *.flv *.mpeg *.mpg"),
            ("Images", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
            ("Videos", "*.mp4 *.mov *.avi *.mkv *.wmv *.flv *.mpeg *.mpg"),
            ("All files", "*.*"),
        )
        path = filedialog.askopenfilename(title="Select media file", filetypes=filetypes)
        if not path:
            return

        self.selected_media = Path(path)
        self.media_type = self._determine_media_type(self.selected_media)

        if self.media_type == "image":
            try:
                image = self._load_image(self.selected_media)
            except Exception as exc:  # pragma: no cover - GUI message
                messagebox.showerror("Error", f"Failed to load image: {exc}")
                self._log(f"Error loading image: {exc}")
                return
            self.poster_frame_image = image
            self._display_image(image)
            self._log(f"Loaded image: {self.selected_media.name}")
        elif self.media_type == "video":
            try:
                poster = self._extract_poster_frame(self.selected_media)
            except Exception as exc:  # pragma: no cover - GUI message
                messagebox.showerror("Error", f"Failed to read video: {exc}")
                self._log(f"Error loading video: {exc}")
                self.poster_frame_image = None
                self._show_placeholder("Unable to load poster frame")
                return
            self.poster_frame_image = poster
            if self.use_poster_frame_var.get() and poster is not None:
                self._display_image(poster)
            else:
                self._show_placeholder("Poster frame disabled")
            self._log(f"Loaded video: {self.selected_media.name}")
        else:
            messagebox.showwarning("Unsupported", "The selected file type is not supported.")
            self._log(f"Unsupported media type: {self.selected_media.suffix}")
            self._show_placeholder("Unsupported media")
            return

    def refresh_preview(self) -> None:
        """Refresh the preview based on current settings."""
        if self.media_type == "video":
            if self.use_poster_frame_var.get() and self.poster_frame_image is not None:
                self._display_image(self.poster_frame_image)
            else:
                self._show_placeholder("Poster frame disabled")
        elif self.media_type == "image" and self.poster_frame_image is not None:
            self._display_image(self.poster_frame_image)
        else:
            self._show_placeholder("No media loaded")

    def _determine_media_type(self, path: Path) -> Optional[str]:
        suffix = path.suffix.lower()
        if suffix in IMAGE_EXTENSIONS:
            return "image"
        if suffix in VIDEO_EXTENSIONS:
            return "video"
        return None

    def _load_image(self, path: Path) -> Image.Image:
        image = Image.open(path)
        return image.convert("RGB")

    def _extract_poster_frame(self, path: Path) -> Optional[Image.Image]:
        """Extract the first frame of a video as a PIL Image."""
        # Try OpenCV first, then imageio as a fallback.
        try:
            import cv2  # type: ignore

            capture = cv2.VideoCapture(str(path))
            success, frame = capture.read()
            capture.release()
            if not success:
                raise RuntimeError("Could not read video frame")
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            return Image.fromarray(frame_rgb)
        except Exception:
            try:
                import imageio.v2 as imageio  # type: ignore

                with imageio.get_reader(str(path)) as reader:
                    frame = reader.get_data(0)
                return Image.fromarray(frame)
            except Exception as exc:
                raise RuntimeError("Unable to extract poster frame") from exc

    # ------------------------------------------------------------------
    # Processing logic
    # ------------------------------------------------------------------
    def start_processing(self) -> None:
        """Start the media processing thread."""
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showinfo("Processing", "Processing is already running.")
            return
        if not self.selected_media:
            messagebox.showwarning("No media", "Please select a media file before processing.")
            return

        self.stop_event.clear()
        self.progress_var.set(0)
        self.token_estimate_var.set("Tokens: 0")
        self.processing_start_time = time.time()
        self._log("Starting processing...")
        self._update_elapsed_time()

        self.processing_thread = threading.Thread(target=self._process_media, daemon=True)
        self.processing_thread.start()

        self.process_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.root.after(100, self._drain_event_queue)

    def request_stop(self) -> None:
        """Signal the processing thread to stop."""
        if self.processing_thread and self.processing_thread.is_alive():
            self._log("Stop requested. Attempting to cancel processing...")
            self.stop_event.set()
        else:
            self._log("No active processing to stop.")

    def _process_media(self) -> None:
        """Simulated processing loop to demonstrate progress handling."""
        media_type = self.media_type or "media"
        total_steps = max(self.frame_count_var.get(), 1) if media_type == "video" else 10
        time_per_step = 0.3 if self.fidelity_var.get() == "LoFi" else 0.5

        for step in range(total_steps):
            if self.stop_event.is_set():
                self.event_queue.put(("stopped",))
                return
            time.sleep(time_per_step)
            progress = int(((step + 1) / total_steps) * 100)
            tokens = self._estimate_tokens(step + 1, total_steps)
            self.event_queue.put(("progress", progress))
            self.event_queue.put(("tokens", tokens))
            self.event_queue.put(("log", f"Processed step {step + 1} of {total_steps}"))

        self.event_queue.put(("complete", "Processing complete."))

    def _estimate_tokens(self, processed_steps: int, total_steps: int) -> int:
        base_tokens = 500 if self.fidelity_var.get() == "HiFi" else 250
        gps_bonus = 100 if self.include_gps_var.get() else 0
        media_multiplier = 2 if (self.media_type == "video" and self.use_poster_frame_var.get()) else 1
        progress_ratio = max(processed_steps / max(total_steps, 1), 0)
        return int((base_tokens + gps_bonus) * media_multiplier * progress_ratio)

    def _drain_event_queue(self) -> None:
        """Handle queued events from the processing thread."""
        try:
            while True:
                event = self.event_queue.get_nowait()
                self._handle_event(event)
        except queue.Empty:
            pass

        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(100, self._drain_event_queue)
        else:
            self.process_button.configure(state="normal")
            self.stop_button.configure(state="disabled")
            self.processing_thread = None
            self.stop_event.clear()
            self.processing_start_time = None
            self.elapsed_time_var.set("Elapsed: 00:00")

    def _handle_event(self, event: tuple) -> None:
        """Interpret events emitted by the processing thread."""
        if not event:
            return

        action = event[0]
        if action == "progress":
            progress_value = float(event[1])
            self.progress_var.set(progress_value)
        elif action == "tokens":
            estimate = int(event[1])
            self.token_estimate_var.set(f"Tokens: {estimate}")
        elif action == "log":
            message = str(event[1])
            self._log(message)
        elif action == "complete":
            message = str(event[1]) if len(event) > 1 else "Processing finished."
            self.progress_var.set(100)
            self._log(message)
        elif action == "stopped":
            self._log("Processing stopped by user.")
            messagebox.showinfo("Stopped", "Processing was cancelled.")
            self.progress_var.set(0)

    def _update_elapsed_time(self) -> None:
        if self.processing_start_time is None:
            return
        elapsed = time.time() - self.processing_start_time
        minutes, seconds = divmod(int(elapsed), 60)
        self.elapsed_time_var.set(f"Elapsed: {minutes:02d}:{seconds:02d}")
        if self.processing_thread and self.processing_thread.is_alive():
            self.root.after(500, self._update_elapsed_time)

    # ------------------------------------------------------------------
    # Preview helpers
    # ------------------------------------------------------------------
    def _display_image(self, image: Image.Image) -> None:
        resized = self._prepare_image_for_preview(image)
        self.preview_photo = ImageTk.PhotoImage(resized)
        self.preview_label.configure(image=self.preview_photo, text="")

    def _show_placeholder(self, message: str) -> None:
        placeholder = self._create_placeholder_image(message)
        self.preview_photo = ImageTk.PhotoImage(placeholder)
        self.preview_label.configure(image=self.preview_photo)

    def _prepare_image_for_preview(self, image: Image.Image) -> Image.Image:
        max_width, max_height = 640, 480
        resized = ImageOps.contain(image, (max_width, max_height))
        return resized

    def _create_placeholder_image(self, message: str) -> Image.Image:
        width, height = 640, 480
        placeholder = Image.new("RGB", (width, height), color="#2f3542")
        draw = ImageDraw.Draw(placeholder)
        text = message
        text_width, text_height = draw.textsize(text)
        position = ((width - text_width) / 2, (height - text_height) / 2)
        draw.text(position, text, fill="#f1f2f6")
        return placeholder

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------
    def _log(self, message: str) -> None:
        timestamp = time.strftime("%H:%M:%S")
        entry = f"[{timestamp}] {message}\n"
        self.log_text.configure(state="normal")
        self.log_text.insert("end", entry)
        self.log_text.configure(state="disabled")
        self.log_text.see("end")


def main() -> None:
    root = tk.Tk()
    app = FireKeyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
