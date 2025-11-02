"""Main application entry point for FireKey."""

from __future__ import annotations

import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk
from typing import Dict, List, Optional

from .openai_client import OpenAIClient
from .profiles import Profile, ProfileManager


class FireKeyApp:
    """Tkinter based desktop application for FireKey."""

    def __init__(self, root: Optional[tk.Tk] = None, profiles_dir: Optional[Path] = None):
        self.root = root or tk.Tk()
        self.root.title("FireKey")
        self.root.geometry("700x600")

        self.profiles_dir = profiles_dir or Path(__file__).resolve().parent.parent / "profiles"
        self.profile_manager = ProfileManager(self.profiles_dir)
        self.profiles: List[Profile] = self.profile_manager.load_profiles()
        self.profile_map: Dict[str, Profile] = {profile.name: profile for profile in self.profiles}

        self.client = OpenAIClient()

        self._manage_dialog: Optional[ProfilesDialog] = None

        self._build_ui()
        self._refresh_profiles()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Context profile selection row
        profile_row = ttk.Frame(main_frame)
        profile_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(profile_row, text="Context Profile:").pack(side=tk.LEFT)
        self.selected_profile = tk.StringVar()
        self.profile_combobox = ttk.Combobox(
            profile_row,
            textvariable=self.selected_profile,
            state="readonly",
            width=40,
        )
        self.profile_combobox.pack(side=tk.LEFT, padx=(10, 10))

        manage_button = ttk.Button(profile_row, text="Manage Profiles", command=self._open_manage_dialog)
        manage_button.pack(side=tk.LEFT)

        # User context input
        ttk.Label(main_frame, text="User Context:").pack(anchor=tk.W)
        self.context_text = tk.Text(main_frame, height=10, wrap=tk.WORD)
        self.context_text.pack(fill=tk.BOTH, expand=True, pady=(5, 15))

        # Process button
        process_button = ttk.Button(main_frame, text="Process", command=self._on_process_clicked)
        process_button.pack(anchor=tk.E, pady=(0, 15))

        # Output area
        ttk.Label(main_frame, text="FireKey Response:").pack(anchor=tk.W)
        self.output_text = tk.Text(main_frame, height=12, wrap=tk.WORD, state=tk.DISABLED)
        self.output_text.pack(fill=tk.BOTH, expand=True)

        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)

    # ------------------------------------------------------------------
    # Profile management helpers
    # ------------------------------------------------------------------
    def _refresh_profiles(self) -> None:
        self.profiles = self.profile_manager.load_profiles()
        self.profile_map = {profile.name: profile for profile in self.profiles}
        names = [profile.name for profile in self.profiles]
        self.profile_combobox["values"] = names
        if names:
            current = self.selected_profile.get()
            if current not in names:
                self.selected_profile.set(names[0])
        else:
            self.selected_profile.set("")

    def _open_manage_dialog(self) -> None:
        if self._manage_dialog and self._manage_dialog.winfo_exists():
            self._manage_dialog.lift()
            return

        self._manage_dialog = ProfilesDialog(
            self.root,
            manager=self.profile_manager,
            on_profiles_changed=self._handle_profiles_changed,
            on_close=self._handle_dialog_closed,
        )

    def _handle_profiles_changed(self) -> None:
        self._refresh_profiles()

    def _handle_dialog_closed(self) -> None:
        self._manage_dialog = None
        self._refresh_profiles()

    # ------------------------------------------------------------------
    # Processing logic
    # ------------------------------------------------------------------
    def _on_process_clicked(self) -> None:
        user_text = self.context_text.get("1.0", tk.END).strip()
        profile = self.profile_map.get(self.selected_profile.get())
        merged = self._merge_contexts(user_text, profile)
        self._set_status("Submitting request to OpenAI…")
        threading.Thread(target=self._process_prompt, args=(merged,), daemon=True).start()

    def _merge_contexts(self, user_text: str, profile: Optional[Profile]) -> str:
        segments = []
        if profile and profile.context.strip():
            segments.append(profile.context.strip())
        if user_text:
            segments.append(user_text)
        return "\n\n".join(segments)

    def _process_prompt(self, prompt: str) -> None:
        response = self.client.generate_response(prompt)
        self.root.after(0, lambda: self._show_response(response))

    def _show_response(self, response: str) -> None:
        self.output_text.configure(state=tk.NORMAL)
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, response)
        self.output_text.configure(state=tk.DISABLED)
        self._set_status("Ready")

    def _set_status(self, message: str) -> None:
        self.status_var.set(message)

    def run(self) -> None:
        self.root.mainloop()


class ProfilesDialog(tk.Toplevel):
    """Dialog that lets users add, edit, or delete profiles."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        manager: ProfileManager,
        on_profiles_changed: callable,
        on_close: callable,
    ) -> None:
        super().__init__(master)
        self.title("Manage Profiles")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self.manager = manager
        self.on_profiles_changed = on_profiles_changed
        self._on_close = on_close

        self._profiles: List[Profile] = []

        container = ttk.Frame(self, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(container, width=40, height=10)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        self.listbox.configure(yscrollcommand=scrollbar.set)

        buttons = ttk.Frame(container)
        buttons.pack(side=tk.LEFT, padx=(10, 0), fill=tk.Y)

        ttk.Button(buttons, text="Add", command=self._add_profile).pack(fill=tk.X)
        ttk.Button(buttons, text="Edit", command=self._edit_profile).pack(fill=tk.X, pady=5)
        ttk.Button(buttons, text="Delete", command=self._delete_profile).pack(fill=tk.X)

        close_btn = ttk.Button(self, text="Close", command=self._close)
        close_btn.pack(pady=(10, 0))

        self.protocol("WM_DELETE_WINDOW", self._close)

        self._refresh()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _refresh(self) -> None:
        self._profiles = self.manager.load_profiles()
        self.listbox.delete(0, tk.END)
        for profile in self._profiles:
            self.listbox.insert(tk.END, profile.name)
        self.on_profiles_changed()

    def _selected_profile(self) -> Optional[Profile]:
        try:
            index = self.listbox.curselection()[0]
        except IndexError:
            return None
        return self._profiles[index]

    def _add_profile(self) -> None:
        ProfileEditorDialog(
            self,
            title="Add Profile",
            on_save=self._handle_add,
        )

    def _edit_profile(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            messagebox.showinfo("Select a profile", "Please select a profile to edit.")
            return
        ProfileEditorDialog(
            self,
            title="Edit Profile",
            on_save=lambda updated: self._handle_edit(profile, updated),
            profile=profile,
        )

    def _delete_profile(self) -> None:
        profile = self._selected_profile()
        if profile is None:
            messagebox.showinfo("Select a profile", "Please select a profile to delete.")
            return
        if messagebox.askyesno("Delete Profile", f"Delete '{profile.name}'?"):
            self.manager.delete_profile(profile)
            self._refresh()

    def _handle_add(self, profile: Profile) -> None:
        self.manager.save_profile(profile)
        self._refresh()

    def _handle_edit(self, original: Profile, updated: Profile) -> None:
        self.manager.save_profile(updated, original_path=original.path)
        self._refresh()

    def _close(self) -> None:
        self.grab_release()
        self.destroy()
        self._on_close()


class ProfileEditorDialog(tk.Toplevel):
    """Modal dialog used to create or edit a profile."""

    def __init__(
        self,
        master: tk.Misc,
        *,
        title: str,
        on_save: callable,
        profile: Optional[Profile] = None,
    ) -> None:
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        self._on_save = on_save
        self._original_profile = profile

        container = ttk.Frame(self, padding=15)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="Name:").grid(row=0, column=0, sticky=tk.W)
        self.name_var = tk.StringVar(value=profile.name if profile else "")
        name_entry = ttk.Entry(container, textvariable=self.name_var, width=40)
        name_entry.grid(row=1, column=0, sticky=tk.W)

        ttk.Label(container, text="Context:").grid(row=2, column=0, sticky=tk.W, pady=(10, 0))
        self.context_text = tk.Text(container, width=50, height=10, wrap=tk.WORD)
        self.context_text.grid(row=3, column=0, pady=(5, 10))
        if profile:
            self.context_text.insert(tk.END, profile.context)

        button_row = ttk.Frame(container)
        button_row.grid(row=4, column=0, sticky=tk.E)

        ttk.Button(button_row, text="Cancel", command=self._cancel).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(button_row, text="Save", command=self._save).pack(side=tk.RIGHT)

        self.protocol("WM_DELETE_WINDOW", self._cancel)
        name_entry.focus_set()

    def _save(self) -> None:
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Invalid name", "Profile name cannot be empty.")
            return
        context = self.context_text.get("1.0", tk.END).strip()
        original_path = self._original_profile.path if self._original_profile else None
        updated = Profile(name=name, context=context, path=original_path)
        self._on_save(updated)
        self._finish()

    def _cancel(self) -> None:
        self._finish()

    def _finish(self) -> None:
        self.grab_release()
        self.destroy()


def main() -> None:
    """Entry point used by ``python -m firekey`` or ``python main.py``."""

    app = FireKeyApp()
    app.run()


if __name__ == "__main__":
    main()
