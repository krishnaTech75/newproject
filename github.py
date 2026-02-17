#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
===============================================================================
|                                                                             |
|   ██████╗ ██╗████████╗██╗  ██╗██╗   ██╗██████╗ ████████╗ ██████╗  ██████╗  |
|  ██╔════╝ ██║╚══██╔══╝██║  ██║██║   ██║██╔══██╗╚══██╔══╝██╔═══██╗██╔═══██╗ |
|  ██║  ███╗██║   ██║   ███████║██║   ██║██████╔╝   ██║   ██║   ██║██║   ██║ |
|  ██║   ██║██║   ██║   ██╔══██║██║   ██║██╔══██╗   ██║   ██║   ██║██║   ██║ |
|  ╚██████╔╝██║   ██║   ██║  ██║╚██████╔╝██████╔╝   ██║   ╚██████╔╝╚██████╔╝ |
|   ╚═════╝ ╚═╝   ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝  |
|                                                                             |
|                    ████████╗ ██████╗  ██████╗ ██╗                         |
|                    ╚══██╔══╝██╔═══██╗██╔═══██╗██║                         |
|                       ██║   ██║   ██║██║   ██║██║                         |
|                       ██║   ██║   ██║██║   ██║██║                         |
|                       ██║   ╚██████╔╝╚██████╔╝███████╗                    |
|                       ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝                    |
|                                                                             |
===============================================================================
|                          GITHUB TOOL - Professional CLI                     |
|                         Developed by Krishna (Kgsflink)                     |
|                  GitHub: https://github.com/Kgsflink                        |
|                  Instagram: @gopalsahani666                                 |
===============================================================================

Enhanced Features:
- Auto mode: Smart repository management with interactive prompts
- Clone repositories to local machine
- Create repositories with auto-initialization
- Upload directories with intelligent file filtering
- Delete repositories with confirmation
- Multi-threaded operations for speed
- Gitignore pattern support
- Progress tracking and detailed logging
- Rate limit management
- Config file support
"""

import os
import sys
import json
import base64
import argparse
import fnmatch
import logging
import threading
import time
import subprocess
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from getpass import getpass
from functools import wraps
import re

import requests
from requests.exceptions import RequestException

# Configure logging with colors for better readability
class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    green = "\x1b[38;5;46m"
    cyan = "\x1b[38;5;51m"
    magenta = "\x1b[38;5;201m"
    reset = "\x1b[0m"

    FORMATS = {
        logging.DEBUG: grey + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.INFO: cyan + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.WARNING: yellow + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.ERROR: red + "%(asctime)s - %(levelname)s - %(message)s" + reset,
        logging.CRITICAL: bold_red + "%(asctime)s - %(levelname)s - %(message)s" + reset
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt, datefmt='%Y-%m-%d %H:%M:%S')
        return formatter.format(record)

# Set up logging with colors
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(ColoredFormatter())
logger.addHandler(console_handler)

CONFIG_FILE = Path.home() / '.github_cli_config.json'
PROGRESS_FILE = Path.home() / '.github_cli_progress.json'
CACHE_FILE = Path.home() / '.github_cli_cache.json'

def show_banner():
    """Display a professional clean ASCII banner."""
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
    ║   [+] Status: System Ready                   Version: 3.0.0-Pro          ║
    ║   [+] Developer: Krishna (Kgsflink)                                      ║
    ║   [+] GitHub: https://github.com/Kgsflink/GithubTool                     ║
    ║   [+] Instagram: @gopalsahani666                                         ║
    ║                                                                          ║
    ║   ⚡ New Features: Auto Mode, Clone, Smart Sync, Batch Ops               ║
    ║                                                                          ║
    ╚══════════════════════════════════════════════════════════════════════════╝
    >>> Ready to execute commands...
    """
    print(banner)

def progress_bar(iteration, total, prefix='', suffix='', length=50, fill='█'):
    """Display a progress bar in the console."""
    percent = f"{100 * (iteration / float(total)):.1f}"
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '░' * (length - filled_length)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end='\r')
    if iteration == total:
        print()

def validate_repo_name(name: str) -> bool:
    """Validate repository name according to GitHub rules."""
    pattern = r'^[a-zA-Z0-9_.-]+$'
    return bool(re.match(pattern, name)) and len(name) <= 100

class GitHubCLI:
    """Main class for GitHub CLI operations with enhanced features."""

    def __init__(self, token: Optional[str] = None, max_workers: int = 5):
        self.token = token or self._load_token()
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'token {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        })
        self.username = None
        self.rate_limit_remaining = 5000
        self.rate_limit_reset = 0
        self.cache = self._load_cache()

    def _load_token(self) -> Optional[str]:
        """Load token from config file or environment variable."""
        env_token = os.environ.get('GITHUB_TOKEN')
        if env_token:
            return env_token

        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
                    return config.get('github_token')
            except (json.JSONDecodeError, KeyError, IOError) as e:
                logger.warning(f"Could not read config file: {e}")
        return None

    def _load_cache(self) -> Dict:
        """Load cached data."""
        if CACHE_FILE.exists():
            try:
                with open(CACHE_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        """Save cache data."""
        try:
            with open(CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except IOError:
            pass

    def save_token(self, token: str) -> None:
        """Save token to config file."""
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump({'github_token': token}, f, indent=2)
            logger.info(f"✓ Token saved to {CONFIG_FILE}")
        except IOError as e:
            logger.error(f"✗ Failed to save token: {e}")
            sys.exit(1)

    def check_rate_limit(self) -> Dict:
        """Check current GitHub API rate limit."""
        try:
            resp = self.session.get('https://api.github.com/rate_limit')
            resp.raise_for_status()
            data = resp.json()
            self.rate_limit_remaining = data['rate']['remaining']
            self.rate_limit_reset = data['rate']['reset']
            return data
        except RequestException as e:
            logger.warning(f"Could not check rate limit: {e}")
            return {}

    def wait_for_rate_limit(self, required: int = 1) -> None:
        """Wait if rate limit is low."""
        if self.rate_limit_remaining < required:
            reset_time = datetime.fromtimestamp(self.rate_limit_reset)
            wait_seconds = (reset_time - datetime.now()).total_seconds()
            if wait_seconds > 0:
                logger.warning(f"Rate limit low. Waiting {wait_seconds:.0f} seconds...")
                time.sleep(min(wait_seconds, 60))
            self.check_rate_limit()

    def get_username(self) -> str:
        """Fetch the authenticated user's username."""
        if self.username:
            return self.username
        try:
            resp = self.session.get('https://api.github.com/user')
            resp.raise_for_status()
            self.username = resp.json()['login']
            logger.info(f"✓ Authenticated as: \x1b[38;5;226m{self.username}\x1b[0m")
            return self.username
        except RequestException as e:
            logger.error(f"✗ Failed to get GitHub username: {e}")
            if hasattr(e, 'response') and e.response and e.response.status_code == 401:
                logger.error("  Invalid token. Please check your GitHub token.")
            sys.exit(1)

    def repo_exists(self, repo_name: str) -> bool:
        """Check if a repository exists under the authenticated user."""
        username = self.get_username()
        url = f'https://api.github.com/repos/{username}/{repo_name}'
        try:
            resp = self.session.get(url)
            exists = resp.status_code == 200
            if exists:
                # Cache repo info
                cache_key = f"{username}/{repo_name}"
                self.cache[cache_key] = {
                    'name': repo_name,
                    'full_name': f"{username}/{repo_name}",
                    'last_checked': datetime.now().isoformat()
                }
                self._save_cache()
            return exists
        except RequestException:
            return False

    def list_repos(self, per_page: int = 100) -> List[Dict]:
        """List all repositories for the authenticated user."""
        self.wait_for_rate_limit()
        username = self.get_username()
        repos = []
        page = 1
        
        logger.info(f"📋 Fetching repositories for {username}...")
        
        while True:
            url = f'https://api.github.com/user/repos?per_page={per_page}&page={page}'
            try:
                resp = self.session.get(url)
                resp.raise_for_status()
                page_repos = resp.json()
                
                if not page_repos:
                    break
                    
                repos.extend(page_repos)
                page += 1
                
                progress_bar(page, page + 1, prefix='Fetching:', suffix=f'Page {page-1}')
                
            except RequestException as e:
                logger.error(f"✗ Failed to list repositories: {e}")
                break
        
        print()
        logger.info(f"✓ Found {len(repos)} repositories")
        return repos

    def create_repo(self, repo_name: str, private: bool = False, 
                   description: str = "", auto_init: bool = True) -> str:
        """Create a new repository. Returns full name (username/repo)."""
        if not validate_repo_name(repo_name):
            logger.error(f"✗ Invalid repository name: {repo_name}")
            logger.error("  Repository names can only contain letters, numbers, ., -, and _")
            sys.exit(1)

        self.wait_for_rate_limit()
        url = 'https://api.github.com/user/repos'
        data = {
            'name': repo_name,
            'private': private,
            'auto_init': auto_init,
            'description': description or f'Repository created by GitHub Tool - Krishna',
            'gitignore_template': 'Python',
            'license_template': 'mit'
        }
        
        try:
            logger.info(f"📦 Creating repository: {repo_name} (private: {private})")
            resp = self.session.post(url, json=data)
            resp.raise_for_status()
            full_name = resp.json()['full_name']
            logger.info(f"✓ Repository '{full_name}' created successfully.")
            
            # Cache the new repo
            self.cache[full_name] = {
                'name': repo_name,
                'full_name': full_name,
                'created': datetime.now().isoformat(),
                'private': private
            }
            self._save_cache()
            
            return full_name
        except RequestException as e:
            logger.error(f"✗ Failed to create repository: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"  Response: {e.response.text}")
            sys.exit(1)

    def delete_repo(self, repo_full_name: str, confirm: bool = True) -> None:
        """Delete a repository by its full name (username/repo)."""
        if confirm:
            logger.warning("\x1b[38;5;196m⚠️  WARNING: This action is irreversible!\x1b[0m")
            logger.warning("  All code, issues, PRs, and wiki pages will be permanently deleted.")
            response = input(f"Type the repository name '{repo_full_name}' to confirm deletion: ").strip()
            if response != repo_full_name:
                logger.info("Deletion cancelled.")
                return

        self.wait_for_rate_limit(5)
        url = f'https://api.github.com/repos/{repo_full_name}'
        try:
            resp = self.session.delete(url)
            if resp.status_code == 204:
                logger.info(f"✓ Repository '{repo_full_name}' deleted successfully.")
                # Remove from cache
                if repo_full_name in self.cache:
                    del self.cache[repo_full_name]
                    self._save_cache()
            else:
                logger.error(f"✗ Failed to delete repository: {resp.status_code}")
                if resp.text:
                    logger.error(f"  Response: {resp.text}")
                sys.exit(1)
        except RequestException as e:
            logger.error(f"✗ Error deleting repository: {e}")
            sys.exit(1)

    def clone_repo(self, repo_full_name: str, target_dir: Optional[Path] = None, 
                   depth: int = 0, use_ssh: bool = False) -> Path:
        """Clone a repository to local machine."""
        username = self.get_username()
        
        if not target_dir:
            target_dir = Path.cwd() / repo_full_name.split('/')[-1]
        
        target_dir = target_dir.expanduser().resolve()
        
        if target_dir.exists():
            logger.error(f"✗ Target directory already exists: {target_dir}")
            response = input("Overwrite? (y/N): ").strip().lower()
            if response != 'y':
                logger.info("Clone cancelled.")
                sys.exit(1)
            import shutil
            shutil.rmtree(target_dir)

        # Determine clone URL
        if use_ssh:
            clone_url = f"git@github.com:{repo_full_name}.git"
        else:
            clone_url = f"https://github.com/{repo_full_name}.git"

        logger.info(f"📦 Cloning {repo_full_name} to {target_dir}")
        logger.info(f"🔗 URL: {clone_url}")

        # Build git command
        cmd = ['git', 'clone']
        if depth > 0:
            cmd.extend(['--depth', str(depth)])
        cmd.extend([clone_url, str(target_dir)])

        try:
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"✓ Repository cloned successfully to {target_dir}")
            
            # Show clone info
            if process.stdout:
                logger.debug(process.stdout)
            
            # Get repository info
            os.chdir(target_dir)
            size = subprocess.run(['git', 'count-objects', '-vH'], 
                                 capture_output=True, text=True)
            logger.info(f"📊 Repository size: {self._parse_git_size(size.stdout)}")
            
            return target_dir
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Failed to clone repository: {e}")
            if e.stderr:
                logger.error(f"  Error: {e.stderr}")
            sys.exit(1)
        except Exception as e:
            logger.error(f"✗ Unexpected error during clone: {e}")
            sys.exit(1)

    def _parse_git_size(self, output: str) -> str:
        """Parse git count-objects output to get human-readable size."""
        for line in output.split('\n'):
            if 'size:' in line:
                size = line.split(':')[1].strip()
                return f"{size} KB"
        return "Unknown"

    def get_file_sha(self, repo_full_name: str, file_path: str) -> Tuple[Optional[str], Optional[bytes]]:
        """Get SHA and content of a file in the repository."""
        url = f'https://api.github.com/repos/{repo_full_name}/contents/{file_path}'
        try:
            self.wait_for_rate_limit()
            resp = self.session.get(url)
            if resp.status_code == 200:
                data = resp.json()
                sha = data['sha']
                content = base64.b64decode(data['content'])
                return sha, content
            elif resp.status_code == 404:
                return None, None
            else:
                return None, None
        except RequestException:
            return None, None

    def upload_file(self, repo_full_name: str, local_path: Path, remote_path: str) -> Tuple[bool, str]:
        """Upload a single file to the repository, updating if changed."""
        url = f'https://api.github.com/repos/{repo_full_name}/contents/{remote_path}'

        # Read local file
        try:
            with open(local_path, 'rb') as f:
                content_bytes = f.read()
            content_b64 = base64.b64encode(content_bytes).decode('utf-8')
        except IOError as e:
            return False, f"Could not read {local_path}: {e}"

        # Check remote file
        sha, remote_content = self.get_file_sha(repo_full_name, remote_path)
        if sha and remote_content == content_bytes:
            return True, f"No changes in {remote_path}. Skipping."

        # Prepare payload
        data = {
            'message': f'Upload/update {remote_path}',
            'content': content_b64,
            'branch': 'main'
        }
        if sha:
            data['sha'] = sha

        try:
            self.wait_for_rate_limit()
            resp = self.session.put(url, json=data)
            if resp.status_code in (200, 201):
                return True, f"Successfully uploaded {remote_path}"
            else:
                return False, f"Failed to upload {remote_path}: {resp.status_code}"
        except RequestException as e:
            return False, f"Error uploading {remote_path}: {e}"

    def should_ignore(self, path: Path, base_dir: Path, ignore_patterns: List[str]) -> bool:
        """Check if a file should be ignored based on patterns (fnmatch)."""
        rel_path = str(path.relative_to(base_dir)).replace('\\', '/')
        
        # Common patterns to always ignore
        always_ignore = [
            '.git/', '.github/', '__pycache__/', '*.pyc', '*.pyo',
            '*.so', '*.dll', '*.exe', '*.class', '*.log', '*.tmp',
            '.DS_Store', 'Thumbs.db', '*.swp', '*.swo', '*~'
        ]
        
        all_patterns = always_ignore + ignore_patterns
        
        for pattern in all_patterns:
            if pattern.startswith('#'):
                continue
            pattern = pattern.strip()
            if not pattern:
                continue
            if fnmatch.fnmatch(rel_path, pattern) or fnmatch.fnmatch(os.path.basename(rel_path), pattern):
                return True
        return False

    def upload_directory(self, repo_full_name: str, local_dir: Path, 
                        ignore_patterns: List[str], sync: bool = False) -> None:
        """Recursively upload a directory, respecting ignore patterns."""
        if not local_dir.is_dir():
            logger.error(f"✗ Not a directory: {local_dir}")
            return

        # Collect all files to upload
        files_to_upload = []
        for root, dirs, files in os.walk(local_dir):
            # Skip .git directory
            if '.git' in dirs:
                dirs.remove('.git')
            
            root_path = Path(root)
            for file in files:
                file_path = root_path / file
                if self.should_ignore(file_path, local_dir, ignore_patterns):
                    logger.debug(f"Ignoring {file_path}")
                    continue

                remote_path = str(file_path.relative_to(local_dir)).replace('\\', '/')
                files_to_upload.append((file_path, remote_path))

        total_files = len(files_to_upload)
        if total_files == 0:
            logger.warning("No files to upload.")
            return

        logger.info(f"📦 Found {total_files} files to process")
        
        # Upload files with progress bar
        successful = 0
        failed = 0
        skipped = 0
        results = []

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {
                executor.submit(self.upload_file, repo_full_name, file_path, remote_path): (file_path, remote_path)
                for file_path, remote_path in files_to_upload
            }

            for i, future in enumerate(as_completed(future_to_file), 1):
                file_path, remote_path = future_to_file[future]
                try:
                    success, message = future.result()
                    if success:
                        if "No changes" in message:
                            skipped += 1
                        else:
                            successful += 1
                        results.append(f"✓ {remote_path}")
                    else:
                        failed += 1
                        results.append(f"✗ {remote_path} - {message}")
                        logger.error(message)
                    
                    progress_bar(i, total_files, prefix='Uploading:', 
                               suffix=f'Complete ({i}/{total_files})')
                    
                except Exception as e:
                    failed += 1
                    logger.error(f"✗ Error processing {remote_path}: {e}")
                    progress_bar(i, total_files, prefix='Uploading:', 
                               suffix=f'Complete ({i}/{total_files})')

        print()
        logger.info(f"\n📊 Upload Summary:")
        logger.info(f"  ✓ Uploaded: {successful}")
        logger.info(f"  ⏭️  Skipped (unchanged): {skipped}")
        logger.info(f"  ✗ Failed: {failed}")
        
        # Save progress
        self.save_progress(repo_full_name, results)

    def save_progress(self, repo_name: str, results: List[str]) -> None:
        """Save upload progress to a file."""
        try:
            progress_data = {
                'repo': repo_name,
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress_data, f, indent=2)
            logger.info(f"📝 Progress saved to {PROGRESS_FILE}")
        except IOError as e:
            logger.warning(f"Could not save progress: {e}")

    def auto_mode(self, path: Path) -> None:
        """Interactive auto mode for repository management."""
        logger.info("\n🔧 Entering AUTO MODE")
        logger.info("=" * 50)
        
        # Check if path exists
        if not path.exists():
            logger.error(f"✗ Path does not exist: {path}")
            return
        
        # Get repository name
        default_name = path.name
        logger.info(f"📁 Directory: {path}")
        repo_name = input(f"Repository name [{default_name}]: ").strip()
        if not repo_name:
            repo_name = default_name
        
        # Check if repo exists
        exists = self.repo_exists(repo_name)
        
        if exists:
            logger.info(f"✓ Repository '{repo_name}' exists")
            action = input("What would you like to do? [U]pload files, [D]elete repo, [C]ancel: ").strip().upper()
            
            if action.startswith('U'):
                username = self.get_username()
                full_name = f"{username}/{repo_name}"
                self._handle_upload(full_name, path)
            elif action.startswith('D'):
                username = self.get_username()
                full_name = f"{username}/{repo_name}"
                self.delete_repo(full_name)
            else:
                logger.info("Operation cancelled.")
        else:
            logger.info(f"📦 Repository '{repo_name}' does not exist")
            create = input("Create new repository? (y/N): ").strip().lower()
            
            if create == 'y':
                # Get repository settings
                private_input = input("Make repository private? (y/N): ").strip().lower()
                private = private_input == 'y'
                
                description = input("Repository description (optional): ").strip()
                
                auto_init = True
                if path.iterdir():
                    auto_init_input = input("Directory not empty. Auto-initialize with README? (Y/n): ").strip().lower()
                    auto_init = auto_init_input != 'n'
                
                # Create repository
                username = self.get_username()
                full_name = self.create_repo(repo_name, private, description, auto_init)
                
                # Upload files if directory not empty
                if any(path.iterdir()):
                    upload = input("Upload directory contents? (Y/n): ").strip().lower()
                    if upload != 'n':
                        self._handle_upload(full_name, path)
                else:
                    logger.info("✓ Empty repository created successfully")
                
                # Show URL
                repo_url = f"https://github.com/{full_name}"
                logger.info(f"\n🌐 Repository URL: \x1b[38;5;39m{repo_url}\x1b[0m")
            else:
                logger.info("Operation cancelled.")

    def _handle_upload(self, full_name: str, path: Path):
        """Handle file upload with ignore patterns."""
        # Load ignore patterns
        ignore_patterns = []
        
        # Check for .gitignore
        gitignore_path = path / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r') as f:
                gitignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
            ignore_patterns.extend(gitignore_patterns)
            logger.info(f"Loaded {len(gitignore_patterns)} patterns from .gitignore")
        
        # Additional patterns
        custom_patterns = input("Additional ignore patterns (comma-separated, optional): ").strip()
        if custom_patterns:
            ignore_patterns.extend([p.strip() for p in custom_patterns.split(',')])
        
        # Remove duplicates
        ignore_patterns = list(set(ignore_patterns))
        
        logger.info(f"🚀 Starting upload to {full_name}")
        logger.info(f"📁 Local directory: {path}")
        logger.info(f"🚫 Ignore patterns: {len(ignore_patterns)} patterns loaded")
        
        self.upload_directory(full_name, path, ignore_patterns, sync=True)

    def run(self, args: argparse.Namespace) -> None:
        """Main orchestration method."""
        # Save token if provided
        if args.token:
            self.save_token(args.token)
            self.token = args.token
            self.session.headers.update({'Authorization': f'token {self.token}'})

        # Verify token works
        try:
            self.get_username()
            self.check_rate_limit()
            logger.info(f"⚡ Rate limit remaining: {self.rate_limit_remaining}")
        except SystemExit:
            logger.error("✗ Invalid or missing GitHub token. Please provide a valid token with -A/--token.")
            sys.exit(1)

        # Handle list repositories
        if args.list:
            repos = self.list_repos()
            if repos:
                print("\n📋 Your Repositories:")
                print("-" * 80)
                for repo in repos:
                    private = "🔒 Private" if repo['private'] else "🌐 Public"
                    stars = f"★ {repo['stargazers_count']}" if repo['stargazers_count'] > 0 else ""
                    print(f"  {repo['name']:<30} {private:<10} {stars}")
                print("-" * 80)
            return

        # Handle clone operation
        if args.clone:
            if not args.repo:
                logger.error("✗ Repository name required for cloning. Use --repo.")
                sys.exit(1)
            username = self.get_username()
            full_name = f"{username}/{args.repo}" if '/' not in args.repo else args.repo
            self.clone_repo(full_name, args.output, args.depth, args.ssh)
            return

        # Handle delete operation
        if args.delete:
            if not args.repo:
                logger.error("✗ Repository name required for deletion. Use --repo.")
                sys.exit(1)
            username = self.get_username()
            full_name = f"{username}/{args.repo}" if '/' not in args.repo else args.repo
            self.delete_repo(full_name, confirm=not args.force)
            return

        # Handle auto mode
        if args.auto:
            if not args.path:
                logger.error("✗ Local directory path required for auto mode. Use -P/--path.")
                sys.exit(1)
            local_dir = Path(args.path).expanduser().resolve()
            self.auto_mode(local_dir)
            return

        # Legacy mode (upload/create)
        if args.path:
            local_dir = Path(args.path).expanduser().resolve()
            if not local_dir.is_dir():
                logger.error(f"✗ Invalid directory: {local_dir}")
                sys.exit(1)

            # Get repository name
            repo_name = args.repo
            if not repo_name:
                repo_name = local_dir.name
                logger.info(f"Using directory name as repository name: {repo_name}")

            # Determine private flag
            private = args.private if args.private is not None else False

            # Check if repo exists
            if self.repo_exists(repo_name):
                username = self.get_username()
                full_name = f"{username}/{repo_name}"
                logger.info(f"✓ Repository '{full_name}' already exists.")
            else:
                logger.info(f"Repository '{repo_name}' does not exist. Creating...")
                full_name = self.create_repo(repo_name, private, args.description, args.no_init)

            # Upload files
            ignore_patterns = args.ignore or []
            
            # Load .gitignore if present and not disabled
            gitignore_path = local_dir / '.gitignore'
            if gitignore_path.exists() and not args.no_gitignore:
                with open(gitignore_path, 'r') as f:
                    gitignore_patterns = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                ignore_patterns.extend(gitignore_patterns)
                logger.info(f"Loaded {len(gitignore_patterns)} patterns from .gitignore")

            # Remove duplicates
            ignore_patterns = list(set(ignore_patterns))
            
            logger.info(f"🚀 Starting upload to {full_name}")
            logger.info(f"📁 Local directory: {local_dir}")
            logger.info(f"🚫 Ignore patterns: {ignore_patterns if ignore_patterns else 'None'}")

            self.upload_directory(full_name, local_dir, ignore_patterns, args.sync)
            
            # Show repository URL
            repo_url = f"https://github.com/{full_name}"
            logger.info(f"\n🌐 Repository URL: \x1b[38;5;39m{repo_url}\x1b[0m")
            logger.info("✨ Upload process completed successfully!")
        else:
            # No path provided, show help
            logger.error("✗ No action specified. Use --auto, --clone, --delete, --list, or provide -P/--path.")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description='GitHub Tool - Professional CLI for GitHub Repository Management',
        epilog='\x1b[38;5;226mExamples:\x1b[0m\n'
               '  Auto Mode:    github-tool --auto -P ./myproject\n'
               '  Clone Repo:   github-tool --clone --repo username/repo -O ./destination\n'
               '  List Repos:   github-tool --list\n'
               '  Upload:       github-tool -P ./myproject --repo myrepo --private\n'
               '  Delete:       github-tool --delete --repo myrepo\n'
               '  Smart Sync:   github-tool -P ./myproject --sync\n'
               '  SSH Clone:    github-tool --clone --repo myrepo --ssh\n'
               '  Shallow:      github-tool --clone --repo myrepo --depth 1',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Main arguments
    parser.add_argument('-A', '--token', help='GitHub personal access token (saved for future use)')
    parser.add_argument('-P', '--path', help='Local directory path to upload')
    parser.add_argument('--repo', help='Repository name (defaults to directory name)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    parser.add_argument('--version', action='version', version='GitHub Tool 3.0 - Developed by Krishna (Kgsflink)')

    # Operation modes
    mode_group = parser.add_argument_group('Operation Modes')
    mode_group.add_argument('--auto', action='store_true', 
                          help='Auto mode: Interactive smart repository management')
    mode_group.add_argument('--clone', action='store_true', 
                          help='Clone a repository to local machine')
    mode_group.add_argument('--list', action='store_true', 
                          help='List all your repositories')
    mode_group.add_argument('--delete', action='store_true', 
                          help='Delete the specified repository')

    # Repository options
    repo_group = parser.add_argument_group('Repository Options')
    repo_group.add_argument('--desc', '--description', dest='description', default='', 
                          help='Repository description')
    repo_group.add_argument('--private', action='store_true', 
                          help='Create repository as private (if creating)')
    repo_group.add_argument('--no-init', action='store_true', 
                          help='Do not auto-initialize with README')

    # Upload options
    upload_group = parser.add_argument_group('Upload Options')
    upload_group.add_argument('-I', '--ignore', nargs='*', 
                            help='Ignore patterns (fnmatch style, e.g., "*.pyc" "temp/*")')
    upload_group.add_argument('--no-gitignore', action='store_true', 
                            help='Do not load patterns from .gitignore')
    upload_group.add_argument('--sync', action='store_true', 
                            help='Sync mode: Only upload changed files')
    upload_group.add_argument('--workers', type=int, default=5, 
                            help='Number of concurrent upload workers (default: 5)')

    # Clone options
    clone_group = parser.add_argument_group('Clone Options')
    clone_group.add_argument('-O', '--output', help='Output directory for clone')
    clone_group.add_argument('--depth', type=int, default=0, 
                           help='Create a shallow clone with history truncated to specified number of commits')
    clone_group.add_argument('--ssh', action='store_true', 
                           help='Use SSH instead of HTTPS for cloning')

    # Delete options
    delete_group = parser.add_argument_group('Delete Options')
    delete_group.add_argument('--force', action='store_true', 
                            help='Force delete without confirmation')

    args = parser.parse_args()

    # Show banner
    show_banner()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # If no arguments, show help
    if len(sys.argv) == 1:
        parser.print_help()
        print("\n\x1b[38;5;226m✨ Try 'github-tool --auto -P ./your-project' for interactive mode!\x1b[0m")
        sys.exit(0)

    # Initialize CLI
    cli = GitHubCLI(token=args.token, max_workers=args.workers)
    
    # Run main logic
    try:
        cli.run(args)
    except KeyboardInterrupt:
        logger.info("\n⚠️  Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"✗ Unexpected error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
