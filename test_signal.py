#!/usr/bin/env python3
import signal
import sys
import time
from datetime import datetime

def log_shutdown():
    """Log shutdown message"""
    try:
        log_file = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shutdown_message = f"{timestamp} TEST-SIGNAL-HANDLER SHUTDOWN 192.168.70.235 0\n"
        
        with open(log_file, "a") as f:
            f.write(shutdown_message)
        
        print(f"[INFO] Shutdown logged: {shutdown_message.strip()}")
    except Exception as e:
        print(f"[ERROR] Failed to log shutdown: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\n[INFO] Received signal {signum}, shutting down...")
    log_shutdown()
    print("[INFO] Shutdown complete.")
    sys.exit(0)

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Log startup
    try:
        log_file = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        startup_message = f"{timestamp} TEST-SIGNAL-HANDLER STARTUP 192.168.70.235 0\n"
        
        with open(log_file, "a") as f:
            f.write(startup_message)
        
        print(f"[INFO] Startup logged: {startup_message.strip()}")
    except Exception as e:
        print(f"[ERROR] Failed to log startup: {e}")
    
    print("Test signal handler running... Press Ctrl+C to test shutdown logging")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[INFO] KeyboardInterrupt received")
        signal_handler(signal.SIGINT, None) 