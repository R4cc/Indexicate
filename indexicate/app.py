"""Graphical file browser with basic file operations."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

FILE_GROUPS = {
    "Media": {".mp3", ".wav", ".mp4", ".avi", ".mkv", ".flac"},
    "Images": {".jpg", ".jpeg", ".png", ".gif", ".bmp"},
    "Documents": {
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".txt",
        ".md",
    },
    "Archives": {".zip", ".rar", ".tar", ".gz", ".7z"},
}

DEFAULT_GROUP = "Other"
ICON_MAP = {
    "Folder": "\U0001f4c1",  # 📁
    "Media": "\U0001f3ac",  # 🎬
    "Images": "\U0001f5bc",  # 🖼️
    "Documents": "\U0001f4c4",  # 📄
    "Archives": "\U0001f5c3",  # 🗃️
    DEFAULT_GROUP: "\U0001f4e6",  # 📦
}


def group_for_extension(ext: str) -> str:
    ext = ext.lower()
    for group, exts in FILE_GROUPS.items():
        if ext in exts:
            return group
    return DEFAULT_GROUP


def open_path(path: str) -> None:
    """Open a file or directory with the default application."""
    if sys.platform.startswith("darwin"):
        subprocess.call(("open", path))
    elif os.name == "nt":
        os.startfile(path)  # type: ignore[attr-defined]
    else:
        subprocess.call(("xdg-open", path))


class IndexicateApp(tk.Frame):
    """Main application widget."""

    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master)
        self.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self, columns=("path", "group"), show="tree")
        self.tree.heading("#0", text="Name")
        self.tree.pack(fill="both", expand=True)

        self.tree.bind("<Double-1>", self.on_open)
        self.tree.bind("<Button-3>", self.popup_menu)

        self.menu = tk.Menu(self, tearoff=0)
        self.menu.add_command(label="Open", command=self.open_selected)
        self.menu.add_command(label="Open folder location", command=self.open_location)
        self.menu.add_command(label="Move…", command=self.move_selected)
        self.menu.add_command(label="Delete", command=self.delete_selected)

        menubar = tk.Menu(master)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Choose folder…", command=self.choose_folder)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=master.destroy)
        menubar.add_cascade(label="File", menu=file_menu)
        master.config(menu=menubar)

    def choose_folder(self) -> None:
        directory = filedialog.askdirectory()
        if directory:
            self.populate(directory)

    def populate(self, path: str) -> None:
        self.tree.delete(*self.tree.get_children())
        self.insert_item("", path)

    def insert_item(self, parent: str, path: str) -> None:
        name = os.path.basename(path) or path
        if os.path.isdir(path):
            node = self.tree.insert(
                parent,
                "end",
                text=f"{ICON_MAP['Folder']} {name}",
                open=False,
                values=(path, "Folder"),
            )
            try:
                for child in sorted(os.listdir(path), key=str.lower):
                    self.insert_item(node, os.path.join(path, child))
            except PermissionError:
                pass
        else:
            group = group_for_extension(os.path.splitext(name)[1])
            icon = ICON_MAP.get(group, ICON_MAP[DEFAULT_GROUP])
            self.tree.insert(
                parent, "end", text=f"{icon} {name}", values=(path, group), tags=(group,)
            )

    def popup_menu(self, event: tk.Event) -> None:
        selected = self.tree.identify_row(event.y)
        if selected:
            self.tree.selection_set(selected)
            self.menu.tk_popup(event.x_root, event.y_root)

    def get_selected_path(self) -> str | None:
        selection = self.tree.selection()
        if not selection:
            return None
        return self.tree.set(selection[0], "path")

    def on_open(self, _event: tk.Event) -> None:
        path = self.get_selected_path()
        if not path:
            return
        if os.path.isdir(path):
            item = self.tree.selection()[0]
            self.tree.item(item, open=not self.tree.item(item, "open"))
        else:
            open_path(path)

    def open_selected(self) -> None:
        path = self.get_selected_path()
        if path:
            open_path(path)

    def open_location(self) -> None:
        path = self.get_selected_path()
        if path:
            open_path(os.path.dirname(path))

    def delete_selected(self) -> None:
        path = self.get_selected_path()
        if not path:
            return
        if messagebox.askyesno("Delete", f"Delete '{os.path.basename(path)}'?"):
            try:
                os.remove(path)
                self.populate(os.path.dirname(path))
            except OSError as exc:
                messagebox.showerror("Error", str(exc))

    def move_selected(self) -> None:
        path = self.get_selected_path()
        if not path:
            return
        dest_dir = filedialog.askdirectory(title="Move to…")
        if dest_dir:
            try:
                shutil.move(path, dest_dir)
                self.populate(os.path.dirname(path))
            except OSError as exc:
                messagebox.showerror("Error", str(exc))


def main() -> None:
    root = tk.Tk()
    root.title("Indexicate")
    app = IndexicateApp(root)
    app.pack(fill="both", expand=True)
    root.geometry("600x400")
    app.mainloop()


if __name__ == "__main__":
    main()
