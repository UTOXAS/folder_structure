import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import git

EMPTY_CHECKBOX_CHAR = "⬜"
CHECKED_CHAR = "✔"


class FileSelectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Selector")
        self.root.geometry("700x550")
        self.root.resizable(True, True)

        self.file_states = {}
        self.selection_mode = tk.BooleanVar(value=True)
        self.git_mode = tk.BooleanVar(value=False)
        self.current_dir = os.getcwd()
        self.git_repo = None

        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        self._setup_controls()
        self._setup_display()
        self._setup_initial_directory()
        self._bind_events()

    def _setup_controls(self):
        control_frame = ttk.Frame(self.main_frame)
        control_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Button(
            control_frame, text="Load Directory", command=self.load_directory, width=15
        ).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            control_frame, text="Combine Files", command=self.combine_files, width=15
        ).pack(side=tk.LEFT, padx=5)

        ttk.Button(
            control_frame,
            text="Export Tree",
            command=self.export_selected_tree,
            width=15,
        ).pack(side=tk.RIGHT, padx=5)

        ttk.Checkbutton(
            control_frame, text="Auto-select children", variable=self.selection_mode
        ).pack(side=tk.LEFT, padx=(10, 5))
        ttk.Checkbutton(
            control_frame,
            text="Git Mode",
            variable=self.git_mode,
            command=self.toggle_git_mode,
        ).pack(side=tk.LEFT)

    def _setup_display(self):
        """Setup the file display area"""

        self.display_frame = ttk.Frame(self.main_frame)
        self.display_frame.pack(fill=tk.BOTH, expand=True)

        self.tree = ttk.Treeview(
            self.display_frame,
            columns=("Checked", "FullPath"),
            show="tree headings",
            selectmode="none",
        )
        self.tree.heading("#0", text="Name")
        self.tree.heading("Checked", text=CHECKED_CHAR, anchor="center")
        self.tree.column("Checked", width=40, anchor="center")
        self.tree.column("FullPath", width=0, stretch=False)

        self.listbox = tk.Listbox(
            self.display_frame, selectmode="multiple", font=("Courier", 10)
        )

        self.y_scroll = ttk.Scrollbar(self.display_frame, orient="vertical")
        self.x_scroll = ttk.Scrollbar(self.display_frame, orient="horizontal")

        self.tree.pack(fill=tk.BOTH, expand=True)
        self._configure_scrollbars(self.tree)

    def _configure_scrollbars(self, widget):
        """Configure scrollbars for the given widget"""
        self.y_scroll.config(command=widget.yview)
        self.x_scroll.config(command=widget.xview)
        widget.config(
            yscrollcommand=self.y_scroll.set, xscrollcommand=self.x_scroll.set
        )
        self.y_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.x_scroll.pack(side=tk.BOTTOM, fill=tk.X)

    def _setup_initial_directory(self):
        """Initialize with current directory"""
        try:
            self.git_repo = git.Repo(self.current_dir, search_parent_directories=True)
        except git.InvalidGitRepositoryError:
            self.git_repo = None
        self._refresh_display()

    def _bind_events(self):
        """Bind UI events"""
        self.tree.bind("<ButtonRelease-1>", self._handle_tree_click)
        self.listbox.bind("<<ListboxSelect>>", self._handle_list_selection)

    def toggle_git_mode(self):
        """Switch between tree and git list mode"""
        self.tree.pack_forget()
        self.listbox.pack_forget()
        self.y_scroll.pack_forget()
        self.x_scroll.pack_forget()

        self.file_states.clear()
        self._refresh_display()

        display_widget = self.listbox if self.git_mode.get() else self.tree
        display_widget.pack(fill=tk.BOTH, expand=True)
        self._configure_scrollbars(display_widget)

    def _refresh_display(self):
        """Refresh the current display based on mode"""
        if self.git_mode.get():
            self._populate_git_list()
        else:
            self.tree.delete(*self.tree.get_children())
            self._populate_tree(self.current_dir, "")

    def _populate_tree(self, parent_dir, parent_node):
        """Populate tree view with directory contents"""
        if not os.path.isdir(parent_dir):
            return

        for item in sorted(os.listdir(parent_dir)):
            path = os.path.join(parent_dir, item)
            node = self.tree.insert(
                parent_node, "end", text=item, values=(EMPTY_CHECKBOX_CHAR, path)
            )
            self.file_states[node] = False

            if os.path.isdir(path):
                self._populate_tree(path, node)

    def _populate_git_list(self):
        """Populate listbox with git-tracked files"""
        self.listbox.delete(0, tk.END)
        if not self.git_repo:
            return

        repo_root = self.git_repo.working_tree_dir
        for file_path in self.git_repo.git.ls_files().splitlines():
            full_path = os.path.join(repo_root, file_path)
            if os.path.exists(full_path):
                self.listbox.insert(tk.END, file_path)
                self.file_states[file_path] = False

    def _handle_tree_click(self, event):
        """Handle tree item clicks"""
        item = self.tree.identify_row(event.y)
        if not item or self.tree.identify_column(event.x) != "#1":
            return
        self._toggle_tree_selection(item)

    def _toggle_tree_selection(self, item):
        """Toggle selection state in tree view"""
        state = not self.file_states[item]
        self.file_states[item] = state
        full_path = self.tree.item(item, "values")[1]
        self.tree.item(
            item, values=(CHECKED_CHAR if state else EMPTY_CHECKBOX_CHAR, full_path)
        )

        if self.selection_mode.get():
            self._toggle_tree_children(item, state)

    def _toggle_tree_children(self, parent, state):
        """Recursively toggle children in tree view"""
        for child in self.tree.get_children(parent):
            self.file_states[child] = state
            full_path = self.tree.item(child, "values")[1]
            self.tree.item(
                child,
                values=(CHECKED_CHAR if state else EMPTY_CHECKBOX_CHAR, full_path),
            )
            self._toggle_tree_children(child, state)

    def _handle_list_selection(self, event):
        """Handle listbox selection changes"""
        selected_indices = self.listbox.curselection()
        for i in range(self.listbox.size()):
            path = self.listbox.size(i)
            self.file_states[path] = i in selected_indices

    def load_directory(self):
        """Load a new directory"""
        folder = filedialog.askdirectory()
        if folder:
            self.current_dir = folder
            self._setup_initial_directory()

    def get_selected_files(self):
        """Get list of selected file paths"""
        if self.git_mode.get():
            repo_root = (
                self.git_repo.working_tree_dir if self.git_repo else self.current_dir
            )
            return [
                os.path.join(repo_root, path)
                for path, selected in self.file_states.items()
                if selected and os.path.isfile(os.path.join(repo_root, path))
            ]

        return [
            self.tree.item(item, "values")[1]
            for item, selected in self.file_states.items()
            if selected and os.path.isfile(self.tree.item(item, "values")[1])
        ]

    def combine_files(self):
        """Combine selected files into one"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "Please select files to combine")
            return

        output_file_name = "combined_code.txt"
        with open(output_file_name, "w", encoding="utf-8") as outfile:
            for file_path in files:

                outfile.write(f"--- {file_path} ---\n")
                with open(file_path, "r", encoding="utf-8") as infile:
                    outfile.write(infile.read() + "\n\n")

        messagebox.showinfo("Success", f"Files combined into {output_file_name}")

    def export_selected_tree(self):
        """Export selected items as tree structure"""
        files = self.get_selected_files()
        if not files:
            messagebox.showwarning("No Selection", "Please select items to export")
            return

        root_path = (
            self.git_repo.working_tree_dir
            if self.git_mode.get() and self.git_repo
            else self.current_dir
        )
        outout_file_name = "directory_tree.txt"
        with open(outout_file_name, "w", encoding="utf-8") as file:
            file.write(self._generate_tree_string(root_path, files))
        messagebox.showinfo("Success", f"Tree exported to {outout_file_name}")

    def _generate_tree_string(self, root_path, selected_paths):
        """Generate tree string for selected paths"""
        tree_dict = {}
        for path in selected_paths:
            rel_path = os.path.relpath(path, root_path)
            parts = rel_path.split(os.sep)
            current = tree_dict
            for part in parts:
                current = current.setdefault(part, {})

        def format_tree(d, prefix=""):

            lines = []
            items = sorted(d.keys())
            for i, item in enumerate(items):
                is_last = i == len(items) - 1
                branch = "└── " if is_last else "├── "

                lines.append(f"{prefix}{branch}{item}")
                if d[item]:
                    new_prefix = prefix + ("    " if is_last else "│   ")
                    lines.extend(format_tree(d[item], new_prefix))
            return "\n".join(lines)

        return f"{os.path.basename(root_path)}/\n" + format_tree(tree_dict)


if __name__ == "__main__":
    root = tk.Tk()
    root.style = ttk.Style()
    root.style.theme_use("clam")
    app = FileSelectorApp(root)
    root.mainloop()
