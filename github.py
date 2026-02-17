#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
|                    GitHub CLI - Professional Edition                        |
|                         Developed by Krishna (Kgsflink)                     |
|                  GitHub: https://github.com/Kgsflink/GithubTool             |
|                  Instagram: @gopalsahani666                                 |
===============================================================================

A full-featured GitHub CLI that works like Git:
  - One-command sync (github-tool sync -P ./dir)
  - Git-like workflow: init, status, commit, push, pull, clone, remote, log
  - Automatic repository creation if needed
  - Smart URL handling (accepts both 'user/repo' and full GitHub URLs)
  - Multithreaded uploads/downloads with progress bars
"""

import os
import sys
import json
import base64
import hashlib
import argparse
import fnmatch
import logging
import shutil
import time
import re
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Set
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

import requests
from requests.exceptions import RequestException

# -----------------------------------------------------------------------------
# Logging with colours
# -----------------------------------------------------------------------------
class ColouredFormatter(logging.Formatter):
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[38;5;46m"
    cyan = "\x1b[38;5;51m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: cyan + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(levelname)s - %(message)s" + reset,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColouredFormatter())
logger.addHandler(console_handler)

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CONFIG_FILE = Path.home() / ".github_cli_config.json"
LOCAL_STATE_DIR = Path.cwd() / ".github_cli"          # per‑repo state
COMMITS_DIR = LOCAL_STATE_DIR / "commits"
MANIFEST_FILE = LOCAL_STATE_DIR / "manifest.json"     # current commit manifest
REMOTE_FILE = LOCAL_STATE_DIR / "remote.json"         # remote info

# -----------------------------------------------------------------------------
# Utility functions
# -----------------------------------------------------------------------------
def show_banner():
    banner = r"""
    ╔══════════════════════════════════════════════════════════════════════════╗
    ║                                                                          ║
    ║   _____ _ _   _           _       _____           _                      ║
    ║  / ____(_) | | |         | |     |_   _|         | |                     ║
    ║ | |  __ _| |_| |__  _   _| |__     | | ___   ___ | |                     ║
    ║ | | |_ | | __| '_ \| | | | '_ \    | |/ _ \ / _ \| |                     ║
    ║ | |__| | | |_| | | | |_| | |_) |   | | (_) | (_) | |                     ║
    ║  \_____|_|\__|_| |_|\__,_|_.__/    \_/\___/ \___/|_|                     ║
    ║                                                                          ║
    ╠══════════════════════════════════════════════════════════════════════════╣
    ║                                                                          ║
    ║   [+] GitHub CLI Pro                           Version 4.1.0             ║
    ║   [+] Developer: Krishna (Kgsflink)                                      ║
    ║   [+] GitHub: https://github.com/Kgsflink/GithubTool                     ║
    ║   [+] Instagram: @gopalsahani666                                         ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)

def parse_github_url(text: str) -> str:
    """
    Convert various GitHub URL formats to 'owner/repo'.
    Accepts:
      - owner/repo
      - https://github.com/owner/repo
      - https://github.com/owner/repo.git
      - git@github.com:owner/repo.git
    Returns 'owner/repo' or raises ValueError.
    """
    text = text.strip()
    # Already in owner/repo format?
    if re.match(r'^[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+$', text):
        return text
    # Try HTTPS URL
    m = re.search(r'github\.com[:/]([^/]+)/([^/.]+)(\.git)?', text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # Try SSH
    m = re.search(r'git@github\.com:([^/]+)/([^/.]+)(\.git)?', text)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    raise ValueError(f"Unable to parse GitHub repository from '{text}'")

def file_hash(file_path: Path) -> str:
    """Return SHA256 hash of file contents."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def normalize_path(path: Path, base: Path) -> str:
    """Return relative path with forward slashes."""
    return str(path.relative_to(base)).replace(os.sep, "/")

def should_ignore(rel_path: str, ignore_patterns: List[str]) -> bool:
    """Check if a relative path matches any ignore pattern."""
    for pattern in ignore_patterns:
        if pattern.startswith("#") or not pattern.strip():
            continue
        if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
            return True
    return False

def load_gitignore(directory: Path) -> List[str]:
    """Load patterns from .gitignore if it exists."""
    gitignore_path = directory / ".gitignore"
    if gitignore_path.exists():
        with open(gitignore_path) as f:
            return [line.strip() for line in f if line.strip() and not line.startswith("#")]
    return []

def progress_bar(iteration, total, prefix="", suffix="", length=50, fill="█"):
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled = int(length * iteration // total)
    bar = fill * filled + "░" * (length - filled)
    print(f"\r{prefix} |{bar}| {percent}% {suffix}", end="\r")
    if iteration == total:
        print()

# -----------------------------------------------------------------------------
# Core GitHub API client
# -----------------------------------------------------------------------------
class GitHubClient:
    """Handles all GitHub API communication."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or self._load_token()
        if not self.token:
            logger.error("No GitHub token found. Please set GITHUB_TOKEN env var or run with -A <token>")
            sys.exit(1)
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github.v3+json"
        })
        self.username = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0

    def _load_token(self) -> Optional[str]:
        env_token = os.environ.get("GITHUB_TOKEN")
        if env_token:
            return env_token
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE) as f:
                    return json.load(f).get("github_token")
            except Exception:
                pass
        return None

    def save_token(self, token: str):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"github_token": token}, f, indent=2)
        logger.info(f"✓ Token saved to {CONFIG_FILE}")

    def check_rate_limit(self):
        try:
            resp = self.session.get("https://api.github.com/rate_limit")
            resp.raise_for_status()
            data = resp.json()
            self.rate_limit_remaining = data["rate"]["remaining"]
            self.rate_limit_reset = data["rate"]["reset"]
        except RequestException as e:
            logger.warning(f"Could not check rate limit: {e}")

    def wait_for_rate_limit(self, required: int = 1):
        if self.rate_limit_remaining < required:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset)
            wait = (reset_time - datetime.now()).total_seconds()
            if wait > 0:
                logger.warning(f"Rate limit low. Waiting {wait:.0f}s...")
                time.sleep(min(wait, 60))
            self.check_rate_limit()

    def get_username(self) -> str:
        if self.username:
            return self.username
        try:
            resp = self.session.get("https://api.github.com/user")
            resp.raise_for_status()
            self.username = resp.json()["login"]
            logger.info(f"✓ Authenticated as: \x1b[38;5;226m{self.username}\x1b[0m")
            return self.username
        except RequestException as e:
            logger.error(f"✗ Failed to get GitHub username: {e}")
            if hasattr(e, "response") and e.response and e.response.status_code == 401:
                logger.error("  Invalid token.")
            sys.exit(1)

    def repo_exists(self, repo_full_name: str) -> bool:
        url = f"https://api.github.com/repos/{repo_full_name}"
        try:
            resp = self.session.get(url)
            return resp.status_code == 200
        except RequestException:
            return False

    def create_repo(self, name: str, private: bool = False, description: str = "") -> str:
        self.wait_for_rate_limit()
        url = "https://api.github.com/user/repos"
        data = {
            "name": name,
            "private": private,
            "description": description or f"Created by GitHub CLI",
            "auto_init": False,
            "gitignore_template": "Python",
            "license_template": "mit"
        }
        try:
            logger.info(f"Creating repository: {name} (private: {private})")
            resp = self.session.post(url, json=data)
            resp.raise_for_status()
            full_name = resp.json()["full_name"]
            logger.info(f"✓ Repository '{full_name}' created.")
            return full_name
        except RequestException as e:
            logger.error(f"✗ Failed to create repository: {e}")
            if hasattr(e, "response") and e.response:
                logger.error(f"  Response: {e.response.text}")
            sys.exit(1)

    def delete_repo(self, repo_full_name: str, confirm: bool = True):
        if confirm:
            logger.warning("\x1b[38;5;196m⚠️  This action is irreversible!\x1b[0m")
            answer = input(f"Type '{repo_full_name}' to confirm: ").strip()
            if answer != repo_full_name:
                logger.info("Deletion cancelled.")
                return
        self.wait_for_rate_limit(5)
        url = f"https://api.github.com/repos/{repo_full_name}"
        try:
            resp = self.session.delete(url)
            if resp.status_code == 204:
                logger.info(f"✓ Repository '{repo_full_name}' deleted.")
            else:
                logger.error(f"✗ Failed to delete: {resp.status_code}")
                if resp.text:
                    logger.error(f"  {resp.text}")
                sys.exit(1)
        except RequestException as e:
            logger.error(f"✗ Error: {e}")
            sys.exit(1)

    def get_file_sha_and_content(self, repo_full_name: str, path: str) -> Tuple[Optional[str], Optional[bytes]]:
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{path}"
        try:
            self.wait_for_rate_limit()
            resp = self.session.get(url)
            if resp.status_code == 200:
                data = resp.json()
                sha = data["sha"]
                content = base64.b64decode(data["content"])
                return sha, content
            elif resp.status_code == 404:
                return None, None
            else:
                return None, None
        except RequestException:
            return None, None

    def upload_file(self, repo_full_name: str, local_path: Path, remote_path: str,
                    message: str = None) -> Tuple[bool, str]:
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{remote_path}"
        try:
            with open(local_path, "rb") as f:
                content_bytes = f.read()
            content_b64 = base64.b64encode(content_bytes).decode()
        except IOError as e:
            return False, f"Read error: {e}"

        sha, remote_content = self.get_file_sha_and_content(repo_full_name, remote_path)
        if sha and remote_content == content_bytes:
            return True, f"No change: {remote_path}"

        data = {
            "message": message or f"Update {remote_path}",
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha

        try:
            self.wait_for_rate_limit()
            resp = self.session.put(url, json=data)
            if resp.status_code in (200, 201):
                return True, f"Uploaded {remote_path}"
            else:
                return False, f"HTTP {resp.status_code}: {resp.text}"
        except RequestException as e:
            return False, str(e)

    def delete_file(self, repo_full_name: str, remote_path: str, sha: str, message: str = None) -> bool:
        url = f"https://api.github.com/repos/{repo_full_name}/contents/{remote_path}"
        data = {
            "message": message or f"Delete {remote_path}",
            "sha": sha,
            "branch": "main"
        }
        try:
            self.wait_for_rate_limit()
            resp = self.session.delete(url, json=data)
            return resp.status_code in (200, 204)
        except RequestException:
            return False

    def get_repo_tree(self, repo_full_name: str, branch: str = "main") -> Optional[List[Dict]]:
        """Fetch entire file tree of the repository (recursive)."""
        url = f"https://api.github.com/repos/{repo_full_name}/git/trees/{branch}?recursive=1"
        try:
            self.wait_for_rate_limit()
            resp = self.session.get(url)
            resp.raise_for_status()
            return resp.json().get("tree", [])
        except RequestException as e:
            logger.error(f"Failed to get tree: {e}")
            return None

    def download_file(self, repo_full_name: str, path: str) -> Optional[bytes]:
        sha, content = self.get_file_sha_and_content(repo_full_name, path)
        return content

# -----------------------------------------------------------------------------
# Local repository state management
# -----------------------------------------------------------------------------
class LocalRepo:
    """Represents a locally tracked repository (with .github_cli)."""

    def __init__(self, path: Path):
        self.root = path.resolve()
        self.state_dir = self.root / ".github_cli"
        self.manifest_file = self.state_dir / "manifest.json"
        self.remote_file = self.state_dir / "remote.json"
        self.commits_dir = self.state_dir / "commits"
        self.manifest = self._load_manifest()
        self.remote_info = self._load_remote()

    def is_initialized(self) -> bool:
        return self.state_dir.is_dir()

    def init(self, remote_full_name: Optional[str] = None):
        """Create .github_cli directory structure."""
        self.state_dir.mkdir(exist_ok=True)
        self.commits_dir.mkdir(exist_ok=True)
        if remote_full_name:
            self.set_remote(remote_full_name)
        self._save_manifest({})   # empty manifest
        logger.info(f"✓ Initialized empty GitHub CLI repository in {self.root}")

    def set_remote(self, full_name: str):
        """Store remote in owner/repo format."""
        try:
            full_name = parse_github_url(full_name)
        except ValueError as e:
            logger.error(f"Invalid remote: {e}")
            sys.exit(1)
        with open(self.remote_file, "w") as f:
            json.dump({"full_name": full_name}, f, indent=2)
        self.remote_info = {"full_name": full_name}
        logger.info(f"Remote set to {full_name}")

    def get_remote(self) -> Optional[str]:
        return self.remote_info.get("full_name") if self.remote_info else None

    def _load_manifest(self) -> Dict[str, str]:
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file) as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_manifest(self, manifest: Dict[str, str]):
        with open(self.manifest_file, "w") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)
        self.manifest = manifest

    def _load_remote(self) -> Optional[Dict]:
        if self.remote_file.exists():
            try:
                with open(self.remote_file) as f:
                    return json.load(f)
            except Exception:
                return None
        return None

    def get_changed_files(self, ignore_patterns: List[str]) -> Tuple[Set[Path], Set[str], Set[Path]]:
        """
        Scan working directory and compare with manifest.
        Returns: (added_or_modified, deleted_relative_paths, unmodified)
        """
        added_or_modified = set()
        deleted = set()
        unmodified = set()

        # Files currently in working tree
        current_files = set()
        for root, dirs, files in os.walk(self.root):
            # Skip .github_cli and .git
            dirs[:] = [d for d in dirs if d not in (".github_cli", ".git")]
            for file in files:
                full_path = Path(root) / file
                rel_path = normalize_path(full_path, self.root)
                if should_ignore(rel_path, ignore_patterns):
                    continue
                current_files.add(full_path)

                # Compare with manifest
                manifest_hash = self.manifest.get(rel_path)
                if manifest_hash is None:
                    added_or_modified.add(full_path)
                else:
                    current_hash = file_hash(full_path)
                    if current_hash == manifest_hash:
                        unmodified.add(full_path)
                    else:
                        added_or_modified.add(full_path)

        # Files in manifest but not in working tree
        for rel_path in self.manifest.keys():
            full_path = self.root / rel_path
            if not full_path.exists():
                deleted.add(rel_path)

        return added_or_modified, deleted, unmodified

    def commit(self, message: str, author: str = None, ignore_patterns: List[str] = None) -> bool:
        """
        Commit all changes (add/modify/delete) to GitHub.
        Returns True if any change was pushed.
        """
        remote = self.get_remote()
        if not remote:
            logger.error("✗ No remote set. Use 'github-tool remote add <full_name>'")
            return False

        client = GitHubClient()
        # Ensure remote exists, if not, ask to create
        if not client.repo_exists(remote):
            logger.warning(f"Remote repository {remote} does not exist.")
            answer = input("Create it now? (y/n): ").strip().lower()
            if answer.startswith('y'):
                private_choice = input("Create as private? (y/n): ").strip().lower()
                private = private_choice.startswith('y')
                desc = input("Description (optional): ").strip()
                client.create_repo(remote.split('/')[-1], private, desc)
            else:
                logger.error("Cannot commit without a remote repository.")
                return False

        ignore = ignore_patterns or []
        added_mod, deleted_rel, _ = self.get_changed_files(ignore)

        if not added_mod and not deleted_rel:
            logger.info("Nothing to commit, working tree clean.")
            return False

        logger.info(f"Committing: {len(added_mod)} changed files, {len(deleted_rel)} deletions")

        # Prepare upload tasks
        tasks = []
        for file_path in added_mod:
            rel_path = normalize_path(file_path, self.root)
            tasks.append(("upload", file_path, rel_path))

        for rel_path in deleted_rel:
            tasks.append(("delete", None, rel_path))

        # Execute with progress
        total = len(tasks)
        success_uploads = 0
        success_deletes = 0
        failed = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for task_type, local_path, remote_path in tasks:
                if task_type == "upload":
                    future = executor.submit(client.upload_file, remote, local_path, remote_path, message)
                else:
                    # need SHA to delete
                    sha, _ = client.get_file_sha_and_content(remote, remote_path)
                    if sha:
                        future = executor.submit(client.delete_file, remote, remote_path, sha, message)
                    else:
                        logger.warning(f"File {remote_path} not found on remote, skipping delete.")
                        total -= 1
                        continue
                futures[future] = (task_type, remote_path)

            for i, future in enumerate(as_completed(futures), 1):
                task_type, remote_path = futures[future]
                try:
                    if task_type == "upload":
                        ok, msg = future.result()
                        if ok:
                            success_uploads += 1
                        else:
                            failed.append(remote_path)
                            logger.error(f"✗ {msg}")
                    else:
                        ok = future.result()
                        if ok:
                            success_deletes += 1
                        else:
                            failed.append(remote_path)
                            logger.error(f"✗ Failed to delete {remote_path}")
                except Exception as e:
                    failed.append(remote_path)
                    logger.error(f"✗ Error: {e}")
                progress_bar(i, total, prefix="Committing:", suffix=f"{i}/{total}")

        print()
        if failed:
            logger.warning(f"Failed: {len(failed)} files")
        else:
            logger.info("✓ All changes committed successfully.")

        # Update manifest with new hashes
        new_manifest = {}
        for file_path in added_mod:
            rel_path = normalize_path(file_path, self.root)
            new_manifest[rel_path] = file_hash(file_path)
        # Keep files that were unchanged
        for rel_path, h in self.manifest.items():
            if (self.root / rel_path).exists() and rel_path not in new_manifest:
                new_manifest[rel_path] = h
        self._save_manifest(new_manifest)

        # Save commit log
        commit_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_entry = {
            "id": commit_id,
            "message": message,
            "author": author or client.get_username(),
            "timestamp": datetime.now().isoformat(),
            "changes": {
                "added/modified": [normalize_path(p, self.root) for p in added_mod],
                "deleted": list(deleted_rel)
            }
        }
        with open(self.commits_dir / f"{commit_id}.json", "w") as f:
            json.dump(log_entry, f, indent=2)

        return True

    def status(self, ignore_patterns: List[str]):
        """Show working tree status."""
        added_mod, deleted_rel, unchanged = self.get_changed_files(ignore_patterns)
        logger.info("On branch main")
        if not added_mod and not deleted_rel:
            logger.info("Working tree clean.")
            return
        if added_mod:
            logger.info("\nChanges to be committed:")
            for f in sorted(added_mod):
                rel = normalize_path(f, self.root)
                logger.info(f"  (modified/new)  {rel}")
        if deleted_rel:
            logger.info("\nDeleted files:")
            for f in sorted(deleted_rel):
                logger.info(f"  (deleted)  {f}")

    def pull(self, ignore_patterns: List[str] = None):
        """Download all files from remote and update working copy."""
        remote = self.get_remote()
        if not remote:
            logger.error("✗ No remote set.")
            return

        client = GitHubClient()
        tree = client.get_repo_tree(remote)
        if tree is None:
            return

        # Filter only blobs (files)
        files = [item for item in tree if item["type"] == "blob"]
        logger.info(f"Fetching {len(files)} files from {remote}...")

        ignore = ignore_patterns or []
        downloaded = 0
        skipped = 0
        failed = []

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {}
            for item in files:
                path = item["path"]
                if should_ignore(path, ignore):
                    skipped += 1
                    continue
                future = executor.submit(client.download_file, remote, path)
                futures[future] = path

            total = len(futures)
            for i, future in enumerate(as_completed(futures), 1):
                path = futures[future]
                try:
                    content = future.result()
                    if content is None:
                        failed.append(path)
                        continue
                    # Write file
                    full_path = self.root / path
                    full_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(full_path, "wb") as f:
                        f.write(content)
                    downloaded += 1
                except Exception as e:
                    failed.append(path)
                    logger.error(f"✗ Failed to download {path}: {e}")
                progress_bar(i, total, prefix="Pulling:", suffix=f"{i}/{total}")

        print()
        logger.info(f"✓ Downloaded: {downloaded}, skipped (ignored): {skipped}, failed: {len(failed)}")

        # Update manifest to reflect pulled state
        new_manifest = {}
        for item in files:
            path = item["path"]
            full_path = self.root / path
            if full_path.exists() and not should_ignore(path, ignore):
                new_manifest[path] = file_hash(full_path)
        self._save_manifest(new_manifest)

    def clone(self, repo_full_name: str, dest_dir: Path, ignore_patterns: List[str] = None):
        """Clone a remote repository into dest_dir and initialize local state."""
        if dest_dir.exists():
            logger.error(f"✗ Destination '{dest_dir}' already exists.")
            return

        dest_dir.mkdir(parents=True)
        os.chdir(dest_dir)
        self.root = dest_dir
        self.state_dir = self.root / ".github_cli"
        self.manifest_file = self.state_dir / "manifest.json"
        self.remote_file = self.state_dir / "remote.json"
        self.commits_dir = self.state_dir / "commits"

        self.init(remote_full_name=repo_full_name)
        self.pull(ignore_patterns)
        logger.info(f"✓ Cloned {repo_full_name} into {dest_dir}")

# -----------------------------------------------------------------------------
# One-shot sync function
# -----------------------------------------------------------------------------
def sync_directory(args):
    """One‑shot sync of a directory to GitHub."""
    client = GitHubClient(token=args.token)
    client.get_username()

    local_dir = Path(args.path).expanduser().resolve()
    if not local_dir.is_dir():
        logger.error(f"✗ Not a directory: {local_dir}")
        sys.exit(1)

    # Repository name
    repo_name = args.repo
    if not repo_name:
        repo_name = local_dir.name
        logger.info(f"No repository name provided, using directory name: {repo_name}")

    full_name = f"{client.get_username()}/{repo_name}"

    # Check if repo exists, else create
    if client.repo_exists(full_name):
        logger.info(f"✓ Repository '{full_name}' already exists.")
    else:
        logger.info(f"Repository '{full_name}' does not exist.")
        private = args.private
        if private is None:
            answer = input("Create as private repository? (y/n): ").strip().lower()
            private = answer.startswith('y')
        desc = args.description or ""
        full_name = client.create_repo(repo_name, private, desc)

    # Build ignore patterns
    ignore_patterns = args.ignore or []
    if not args.no_gitignore:
        gitignore_patterns = load_gitignore(local_dir)
        if gitignore_patterns:
            ignore_patterns.extend(gitignore_patterns)
            logger.info(f"Loaded {len(gitignore_patterns)} patterns from .gitignore")
    ignore_patterns = list(set(ignore_patterns))

    logger.info(f"🚀 Syncing {local_dir} to {full_name}")
    logger.info(f"🚫 Ignore patterns: {ignore_patterns if ignore_patterns else 'None'}")

    # Collect all files to upload
    files_to_upload = []
    for root, dirs, files in os.walk(local_dir):
        dirs[:] = [d for d in dirs if d not in (".git", ".github_cli")]
        for file in files:
            file_path = Path(root) / file
            rel_path = normalize_path(file_path, local_dir)
            if should_ignore(rel_path, ignore_patterns):
                continue
            files_to_upload.append((file_path, rel_path))

    total = len(files_to_upload)
    if total == 0:
        logger.warning("No files to upload.")
        return

    logger.info(f"📦 Found {total} files to upload")

    successful = 0
    failed = []

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(client.upload_file, full_name, local_path, remote_path, f"Sync {remote_path}"): remote_path
            for local_path, remote_path in files_to_upload
        }
        for i, future in enumerate(as_completed(futures), 1):
            remote_path = futures[future]
            try:
                ok, msg = future.result()
                if ok:
                    successful += 1
                else:
                    failed.append(remote_path)
                    logger.error(f"✗ {msg}")
            except Exception as e:
                failed.append(remote_path)
                logger.error(f"✗ Error uploading {remote_path}: {e}")
            progress_bar(i, total, prefix="Uploading:", suffix=f"{i}/{total}")

    print()
    logger.info(f"\n📊 Sync Summary:")
    logger.info(f"  ✓ Successful: {successful}")
    logger.info(f"  ✗ Failed: {len(failed)}")
    repo_url = f"https://github.com/{full_name}"
    logger.info(f"\n🌐 Repository URL: \x1b[38;5;39m{repo_url}\x1b[0m")

# -----------------------------------------------------------------------------
# Command line interface
# -----------------------------------------------------------------------------
def main():
    show_banner()

    parser = argparse.ArgumentParser(
        description="GitHub CLI - Git-like interface + One-Shot Sync",
        epilog="Use 'github-tool <command> -h' for help on a specific command."
    )
    # Global options
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-A", "--token", help="GitHub personal access token (saved)")

    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="", required=True)

    # ---- sync (one-shot upload) ----
    p_sync = subparsers.add_parser("sync", help="One-shot sync of a directory to GitHub")
    p_sync.add_argument("-P", "--path", required=True, help="Local directory path to upload")
    p_sync.add_argument("--repo", help="Repository name (defaults to directory name)")
    p_sync.add_argument("--desc", "--description", dest="description", default="", help="Repository description")
    p_sync.add_argument("--private", action="store_true", help="Create repository as private (if creating)")
    p_sync.add_argument("-I", "--ignore", nargs="*", help="Ignore patterns (fnmatch style)")
    p_sync.add_argument("--no-gitignore", action="store_true", help="Do not load patterns from .gitignore")
    p_sync.add_argument("--workers", type=int, default=5, help="Number of concurrent upload workers (default: 5)")

    # ---- init ----
    p_init = subparsers.add_parser("init", help="Initialize current directory as a GitHub CLI repo")
    p_init.add_argument("--remote", help="Remote repository (user/repo or full URL)")

    # ---- status ----
    p_status = subparsers.add_parser("status", help="Show working tree status")
    p_status.add_argument("-I", "--ignore", nargs="*", help="Ignore patterns")

    # ---- commit ----
    p_commit = subparsers.add_parser("commit", help="Commit changes to GitHub")
    p_commit.add_argument("-m", "--message", required=True, help="Commit message")
    p_commit.add_argument("--author", help="Author name (defaults to GitHub username)")
    p_commit.add_argument("-I", "--ignore", nargs="*", help="Ignore patterns")

    # ---- push ----
    p_push = subparsers.add_parser("push", help="Push committed changes (same as commit)")

    # ---- pull ----
    p_pull = subparsers.add_parser("pull", help="Pull latest from GitHub")
    p_pull.add_argument("-I", "--ignore", nargs="*", help="Ignore patterns")

    # ---- clone ----
    p_clone = subparsers.add_parser("clone", help="Clone a repository")
    p_clone.add_argument("repo", help="Repository (user/repo or full URL)")
    p_clone.add_argument("directory", nargs="?", help="Destination directory (default: repo name)")
    p_clone.add_argument("-I", "--ignore", nargs="*", help="Ignore patterns")

    # ---- remote ----
    p_remote = subparsers.add_parser("remote", help="Manage remote repository")
    p_remote_sub = p_remote.add_subparsers(dest="remote_command", required=True, metavar="")
    p_remote_add = p_remote_sub.add_parser("add", help="Add a remote")
    p_remote_add.add_argument("name", help="Remote repository (user/repo or full URL)")
    p_remote_remove = p_remote_sub.add_parser("remove", help="Remove current remote")
    p_remote_show = p_remote_sub.add_parser("show", help="Show current remote")

    # ---- create-repo ----
    p_create = subparsers.add_parser("create-repo", help="Create a new repository on GitHub")
    p_create.add_argument("name", help="Repository name")
    p_create.add_argument("--private", action="store_true", help="Private repository")
    p_create.add_argument("--desc", help="Description")

    # ---- delete-repo ----
    p_delete = subparsers.add_parser("delete-repo", help="Delete a repository on GitHub")
    p_delete.add_argument("name", help="Repository full name (user/repo)")
    p_delete.add_argument("--force", action="store_true", help="Skip confirmation")

    # ---- log ----
    p_log = subparsers.add_parser("log", help="Show commit history")

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # For commands that need token (basically all), we create client
    # But token may be None; client will try to load from config/env.
    if args.command == "sync":
        sync_directory(args)
        return

    # All other commands (except sync) may require a local repo or are standalone.
    client = GitHubClient(token=args.token)
    if args.token:
        client.save_token(args.token)
    client.get_username()  # verify token early

    # Commands that don't require a local repo
    if args.command in ("create-repo", "delete-repo", "clone"):
        if args.command == "create-repo":
            client.create_repo(args.name, args.private, args.desc)
        elif args.command == "delete-repo":
            client.delete_repo(args.name, confirm=not args.force)
        elif args.command == "clone":
            try:
                full_name = parse_github_url(args.repo)
            except ValueError as e:
                logger.error(e)
                sys.exit(1)
            dest = Path(args.directory) if args.directory else Path(full_name.split("/")[-1])
            repo = LocalRepo(Path.cwd())
            repo.clone(full_name, dest, args.ignore)
        return

    # All other commands require a local repo (must be inside one)
    try:
        local = LocalRepo(Path.cwd())
        if not local.is_initialized() and args.command not in ("init",):
            logger.error("✗ Not a GitHub CLI repository. Run 'github-tool init' first.")
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Error accessing local repo: {e}")
        sys.exit(1)

    # Execute command
    if args.command == "init":
        if local.is_initialized():
            logger.warning("Repository already initialized.")
        else:
            local.init(args.remote)

    elif args.command == "status":
        local.status(args.ignore or [])

    elif args.command == "commit":
        local.commit(args.message, args.author, args.ignore)

    elif args.command == "push":
        logger.info("Push will commit all changes.")
        local.commit("Push commit", ignore_patterns=args.ignore)

    elif args.command == "pull":
        local.pull(args.ignore)

    elif args.command == "remote":
        if args.remote_command == "add":
            local.set_remote(args.name)
        elif args.remote_command == "remove":
            if local.remote_file.exists():
                local.remote_file.unlink()
                logger.info("Remote removed.")
            else:
                logger.warning("No remote set.")
        elif args.remote_command == "show":
            remote = local.get_remote()
            if remote:
                logger.info(f"Remote: {remote}")
            else:
                logger.info("No remote configured.")

    elif args.command == "log":
        logs = sorted(local.commits_dir.glob("*.json"))
        if not logs:
            logger.info("No commits yet.")
        else:
            for log_file in logs:
                with open(log_file) as f:
                    entry = json.load(f)
                logger.info(f"{entry['id']}  {entry['author']}  {entry['message']}")

    else:
        logger.error(f"Unknown command: {args.command}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⚠️  Interrupted by user.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"✗ Unexpected error: {e}")
        sys.exit(1)
