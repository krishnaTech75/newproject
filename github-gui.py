import os
import json
import base64
import threading
import fnmatch
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
import requests

# --- GITHUB DARK THEME COLORS ---
GH_BG = "#0d1117"
GH_SIDEBAR = "#161b22"
GH_TEXT = "#c9d1d9"
GH_GREEN = "#238636"
GH_BLUE = "#1f6feb"
GH_BORDER = "#30363d"
GH_RED = "#da3633"

CONFIG_FILE = Path.home() / '.github_cli_config.json'

class GitHubGodMode(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("GitHub Tool Pro - GODMODE")
        self.geometry("1200x850")
        self.configure(fg_color=GH_BG)

        # App State
        self.token = self._load_token()
        self.username = None
        self.all_repos = []
        
        # Grid Configuration
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main_content()
        self._build_log_area()

        if self.token:
            self.verify_auth()
        else:
            self.show_frame("settings")

    def _load_token(self):
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    return json.load(f).get('github_token')
            except: return None
        return None

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=GH_SIDEBAR, border_color=GH_BORDER, border_width=1)
        self.sidebar.grid(row=0, column=0, rowspan=2, sticky="nsew")
        
        logo = ctk.CTkLabel(self.sidebar, text="GIT-TOOL PRO", font=ctk.CTkFont(size=22, weight="bold"))
        logo.pack(pady=30, padx=20)

        self.btn_list = self._sidebar_btn("📁 My Repositories", "list")
        self.btn_create = self._sidebar_btn("📤 New Upload", "upload")
        self.btn_clone = self._sidebar_btn("📥 Clone Repo", "clone")
        self.btn_settings = self._sidebar_btn("⚙️ Settings", "settings")

        self.status_lbl = ctk.CTkLabel(self.sidebar, text="Not Connected", text_color="gray")
        self.status_lbl.pack(side="bottom", pady=20)

    def _sidebar_btn(self, text, frame_name):
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color="transparent", anchor="w", 
                            hover_color=GH_BORDER, height=45, text_color=GH_TEXT,
                            command=lambda: self.show_frame(frame_name))
        btn.pack(fill="x", padx=10, pady=5)
        return btn

    def _build_main_content(self):
        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.grid(row=0, column=1, sticky="nsew", padx=30, pady=30)
        self.frames = {}

        # --- REPO LIST FRAME ---
        f_list = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(f_list, text="Repository Browser", font=("Arial", 28, "bold")).pack(pady=(0,10), anchor="w")
        
        search_row = ctk.CTkFrame(f_list, fg_color="transparent")
        search_row.pack(fill="x", pady=10)
        self.search_entry = ctk.CTkEntry(search_row, placeholder_text="Search repositories...", width=400)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.filter_repos)
        
        ctk.CTkButton(search_row, text="Refresh", fg_color=GH_BLUE, width=100, command=self.fetch_repos).pack(side="right")

        self.repo_scroll = ctk.CTkScrollableFrame(f_list, fg_color=GH_SIDEBAR, height=500, border_color=GH_BORDER, border_width=1)
        self.repo_scroll.pack(fill="both", expand=True)
        self.frames["list"] = f_list

        # --- UPLOAD FRAME ---
        f_up = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(f_up, text="Upload Project", font=("Arial", 28, "bold")).pack(pady=10)
        self.up_path = ctk.CTkEntry(f_up, placeholder_text="Select local folder...", width=500)
        self.up_path.pack(pady=5)
        ctk.CTkButton(f_up, text="Browse Folder", fg_color=GH_BORDER, command=lambda: self.browse_folder(self.up_path)).pack(pady=5)
        self.up_name = ctk.CTkEntry(f_up, placeholder_text="Repository Name", width=500)
        self.up_name.pack(pady=5)
        self.up_private = ctk.CTkCheckBox(f_up, text="Private Repository")
        self.up_private.pack(pady=5)
        self.progress = ctk.CTkProgressBar(f_up, width=500)
        self.progress.set(0)
        self.progress.pack(pady=20)
        ctk.CTkButton(f_up, text="🚀 START UPLOAD", fg_color=GH_GREEN, height=50, command=self.start_new_upload).pack(pady=10)
        self.frames["upload"] = f_up

        # --- CLONE FRAME ---
        f_cl = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(f_cl, text="Clone", font=("Arial", 28, "bold")).pack(pady=10)
        self.cl_name = ctk.CTkEntry(f_cl, placeholder_text="username/repo", width=500)
        self.cl_name.pack(pady=10)
        self.cl_dest = ctk.CTkEntry(f_cl, placeholder_text="Destination Path", width=500)
        self.cl_dest.pack(pady=5)
        ctk.CTkButton(f_cl, text="Browse", fg_color=GH_BORDER, command=lambda: self.browse_folder(self.cl_dest)).pack(pady=5)
        ctk.CTkButton(f_cl, text="Start Cloning", fg_color=GH_BLUE, command=self.clone_repo).pack(pady=10)
        self.frames["clone"] = f_cl

        # --- SETTINGS FRAME ---
        f_set = ctk.CTkFrame(self.container, fg_color="transparent")
        ctk.CTkLabel(f_set, text="Settings", font=("Arial", 28, "bold")).pack(pady=20)
        self.token_entry = ctk.CTkEntry(f_set, placeholder_text="GitHub Token (PAT)", width=500, show="*")
        self.token_entry.pack(pady=10)
        if self.token: self.token_entry.insert(0, self.token)
        ctk.CTkButton(f_set, text="Update Token", fg_color=GH_BLUE, command=self.save_token).pack(pady=10)
        self.frames["settings"] = f_set

    def _build_log_area(self):
        self.log_box = ctk.CTkTextbox(self, height=180, fg_color="#010409", text_color="#7ee787", font=("Consolas", 12))
        self.log_box.grid(row=1, column=1, sticky="nsew", padx=30, pady=(0, 30))

    def log(self, msg):
        self.log_box.insert("end", f">>> {msg}\n")
        self.log_box.see("end")

    def show_frame(self, name):
        for f in self.frames.values(): f.pack_forget()
        self.frames[name].pack(fill="both", expand=True)

    # --- CORE LOGIC ---

    def verify_auth(self):
        headers = {'Authorization': f'token {self.token}'}
        def task():
            try:
                r = requests.get('https://api.github.com/user', headers=headers)
                if r.status_code == 200:
                    self.username = r.json()['login']
                    self.after(0, lambda: self.status_lbl.configure(text=f"Logged as: {self.username}", text_color=GH_BLUE))
                    self.fetch_repos()
                    self.after(0, lambda: self.show_frame("list"))
                else:
                    self.log("✗ Auth Failed: Invalid Token")
            except: self.log("✗ Connection Error")
        threading.Thread(target=task, daemon=True).start()

    def fetch_repos(self):
        self.log("Fetching repositories...")
        headers = {'Authorization': f'token {self.token}'}
        def task():
            try:
                r = requests.get(f'https://api.github.com/user/repos?per_page=100&sort=updated', headers=headers)
                self.all_repos = r.json()
                self.render_repo_list(self.all_repos)
                self.log(f"Found {len(self.all_repos)} repositories.")
            except: self.log("✗ Failed to load repositories.")
        threading.Thread(target=task, daemon=True).start()

    def filter_repos(self, event=None):
        query = self.search_entry.get().lower()
        filtered = [r for r in self.all_repos if query in r['name'].lower()]
        self.render_repo_list(filtered)

    def render_repo_list(self, repos):
        for w in self.repo_scroll.winfo_children(): w.destroy()
        for repo in repos:
            frame = ctk.CTkFrame(self.repo_scroll, fg_color=GH_BORDER, height=50)
            frame.pack(fill="x", pady=4, padx=5)
            
            icon = "🔒" if repo['private'] else "🌐"
            ctk.CTkLabel(frame, text=f"{icon} {repo['name']}", font=("Arial", 14, "bold"), width=300, anchor="w").pack(side="left", padx=15)
            
            # Actions Row
            ctk.CTkButton(frame, text="Delete", fg_color=GH_RED, width=70, height=28, 
                          command=lambda n=repo['name']: self.delete_repo(n)).pack(side="right", padx=10)
            
            ctk.CTkButton(frame, text="Sync/Update", fg_color=GH_GREEN, width=100, height=28, 
                          command=lambda n=repo['name']: self.sync_existing_repo(n)).pack(side="right", padx=5)

    def delete_repo(self, name):
        if messagebox.askyesno("Confirm Delete", f"Delete {name} forever?"):
            headers = {'Authorization': f'token {self.token}'}
            def task():
                r = requests.delete(f'https://api.github.com/repos/{self.username}/{name}', headers=headers)
                if r.status_code == 204:
                    self.log(f"✓ Deleted {name}")
                    self.fetch_repos()
            threading.Thread(target=task, daemon=True).start()

    def browse_folder(self, entry_widget):
        p = filedialog.askdirectory()
        if p:
            entry_widget.delete(0, "end")
            entry_widget.insert(0, p)

    # --- GODMODE SYNC ENGINE ---

    def sync_existing_repo(self, repo_name):
        local_path = filedialog.askdirectory(title=f"Select folder to sync with {repo_name}")
        if not local_path: return
        threading.Thread(target=self.engine_upload, args=(repo_name, local_path, False), daemon=True).start()

    def start_new_upload(self):
        repo_name = self.up_name.get()
        local_path = self.up_path.get()
        private = self.up_private.get()
        if not repo_name or not local_path: return
        threading.Thread(target=self.engine_upload, args=(repo_name, local_path, True, private), daemon=True).start()

    def engine_upload(self, repo_name, local_dir, create_new=False, private=False):
        headers = {'Authorization': f'token {self.token}'}
        root = Path(local_dir)
        
        if create_new:
            self.log(f"Creating repo {repo_name}...")
            requests.post('https://api.github.com/user/repos', headers=headers, json={'name': repo_name, 'private': private, 'auto_init': True})

        # Get existing files SHAs to skip unchanged files
        self.log("Analyzing repository tree...")
        existing_shas = {}
        tree_res = requests.get(f'https://api.github.com/repos/{self.username}/{repo_name}/git/trees/main?recursive=1', headers=headers)
        if tree_res.status_code == 200:
            for item in tree_res.json().get('tree', []):
                if item['type'] == 'blob': existing_shas[item['path']] = item['sha']

        # Collect local files (obeying gitignore)
        ignore = ['.git', '__pycache__', 'node_modules', '.DS_Store', '.env']
        files_to_process = []
        for f in root.rglob('*'):
            if f.is_file() and not any(x in f.parts for x in ignore):
                files_to_process.append(f)

        total = len(files_to_process)
        self.log(f"Found {total} files. Starting multi-threaded sync...")

        def process_file(file_path):
            rel_path = file_path.relative_to(root).as_posix()
            with open(file_path, 'rb') as f: content = f.read()
            encoded = base64.b64encode(content).decode()
            
            data = {"message": "Godmode Sync", "content": encoded}
            if rel_path in existing_shas:
                data["sha"] = existing_shas[rel_path]
            
            url = f'https://api.github.com/repos/{self.username}/{repo_name}/contents/{rel_path}'
            res = requests.put(url, headers=headers, json=data)
            return res.status_code

        count = 0
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(process_file, f): f for f in files_to_process}
            for future in as_completed(futures):
                count += 1
                self.progress.set(count / total)
                if count % 10 == 0: self.log(f"Progress: {count}/{total}")

        self.log(f"✅ Sync Complete: {repo_name} is updated.")
        self.fetch_repos()

    def clone_repo(self):
        repo = self.cl_name.get()
        dest = self.cl_dest.get()
        def task():
            url = f"https://github.com/{repo}.git" if "/" in repo else f"https://github.com/{self.username}/{repo}.git"
            self.log(f"Cloning {url}...")
            res = subprocess.run(['git', 'clone', url, dest], capture_output=True, text=True)
            if res.returncode == 0: self.log("✓ Clone Successful")
            else: self.log(f"✗ Error: {res.stderr}")
        threading.Thread(target=task, daemon=True).start()

    def save_token(self):
        t = self.token_entry.get()
        if t:
            with open(CONFIG_FILE, 'w') as f: json.dump({'github_token': t}, f)
            self.token = t
            self.verify_auth()

if __name__ == "__main__":
    app = GitHubGodMode()
    app.mainloop()