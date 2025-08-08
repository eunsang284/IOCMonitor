# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Log Service
EPICS IOC 모니터 로그 서비스
Log management and retrieval functionality
로그 관리 및 조회 기능
"""

import os
import time
from typing import List, Dict, Optional
from datetime import datetime
import subprocess

class LogService:
    """Log management service / 로그 관리 서비스"""
    
    def __init__(self):
        """Initialize log service / 로그 서비스 초기화"""
        # Load configuration
        from config import Config
        self.config = Config()
        
        # Ensure log directory exists
        os.makedirs(self.config.LOG_DIR, exist_ok=True)
    
    def get_daily_log_path(self) -> str:
        """
        Get daily log file path / 일일 로그 파일 경로 반환
        
        Returns:
            str: Log file path / 로그 파일 경로
        """
        today = time.strftime("%Y-%m-%d")
        return os.path.join(self.config.LOG_DIR, f"faulted_ioc_{today}.log")
    
    def log_startup(self, timestamp: str):
        """
        Log application startup / 애플리케이션 시작 로그
        
        Args:
            timestamp: Startup timestamp / 시작 타임스탬프
        """
        try:
            with open(self.get_daily_log_path(), "a") as log:
                log.write(f"[{timestamp}] IOCMonitor : [STARTUP] Server started\n")
        except Exception as e:
            print(f"[ERROR] Startup logging failed: {e}")
    
    def get_ioc_logs(self, iocname: str) -> List[Dict]:
        """
        Get IOC event logs / IOC 이벤트 로그 조회
        
        Args:
            iocname: IOC name / IOC 이름
            
        Returns:
            List[Dict]: IOC logs / IOC 로그들
        """
        logs = []
        
        try:
            with open(self.config.ALIVE_EVENTS_LOG, "r") as f:
                for line in f:
                    if iocname in line:
                        parts = line.strip().split()
                        # Log format: [date] [time] [IOCname] [event] [IP] [MSG]
                        if len(parts) >= 6:
                            logs.append({
                                "time": parts[0] + " " + parts[1],  # ex. 2025-05-16 19:04:06
                                "event": parts[3],                  # ex. MESSAGE, BOOT, FAIL
                                "ip": parts[4],                     # ex. 192.168.60.14
                                "code": parts[5]                    # ex. 0, 1, 10001 (MSG)
                            })
                        else:
                            print(f"[SKIP] Log format error: {line.strip()}")
                            
        except FileNotFoundError:
            print(f"[ERROR] Log file not found: {self.config.ALIVE_EVENTS_LOG}")
        except Exception as e:
            print(f"[ERROR] Log file read failed: {e}")
        
        # Return in reverse chronological order
        return logs[::-1]
    
    def get_log_dates(self) -> List[str]:
        """
        Get available log dates / 사용 가능한 로그 날짜들 조회
        
        Returns:
            List[str]: Available log dates / 사용 가능한 로그 날짜들
        """
        try:
            files = os.listdir(self.config.LOG_DIR)
            log_dates = sorted([
                f[len("faulted_ioc_"):-len(".log")]
                for f in files if f.startswith("faulted_ioc_") and f.endswith(".log")
            ], reverse=True)
            return log_dates
        except Exception as e:
            print(f"[ERROR] Log directory read failed: {e}")
            return []
    
    def get_log_by_date(self, date: str) -> str:
        """
        Get log content by date / 날짜별 로그 내용 조회
        
        Args:
            date: Log date / 로그 날짜
            
        Returns:
            str: Log content / 로그 내용
        """
        try:
            log_path = os.path.join(self.config.LOG_DIR, f"faulted_ioc_{date}.log")
            with open(log_path, "r") as f:
                lines = f.readlines()
            lines = lines[::-1]  # Latest logs first
            return "".join(lines)
        except Exception as e:
            return f"Log file read failed: {e}"
    
    def write_log(self, message: str, level: str = "INFO"):
        """
        Write log message / 로그 메시지 작성
        
        Args:
            message: Log message / 로그 메시지
            level: Log level / 로그 레벨
        """
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] IOCMonitor : [{level}] {message}\n"
            
            with open(self.get_daily_log_path(), "a") as log:
                log.write(log_entry)
                
        except Exception as e:
            print(f"[ERROR] Log writing failed: {e}")
    
    def get_system_logs(self, lines: int = 100) -> List[str]:
        """
        Get system logs / 시스템 로그 조회
        
        Args:
            lines: Number of lines to retrieve / 조회할 라인 수
            
        Returns:
            List[str]: System log lines / 시스템 로그 라인들
        """
        try:
            # Get recent system logs using journalctl
            result = subprocess.run(
                ['journalctl', '-n', str(lines), '--no-pager'],
                capture_output=True, text=True, timeout=30
            )
            
            if result.returncode == 0:
                return result.stdout.splitlines()
            else:
                return [f"Failed to retrieve system logs: {result.stderr}"]
                
        except subprocess.TimeoutExpired:
            return ["System log retrieval timed out"]
        except Exception as e:
            return [f"System log retrieval failed: {e}"]
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Clean up old log files / 오래된 로그 파일 정리
        
        Args:
            days: Days to keep / 보관할 일수
        """
        try:
            import glob
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.now() - timedelta(days=days)
            
            log_pattern = os.path.join(self.config.LOG_DIR, "faulted_ioc_*.log")
            log_files = glob.glob(log_pattern)
            
            for log_file in log_files:
                try:
                    # Extract date from filename
                    filename = os.path.basename(log_file)
                    date_str = filename.replace("faulted_ioc_", "").replace(".log", "")
                    file_date = datetime.strptime(date_str, "%Y-%m-%d")
                    
                    if file_date < cutoff_date:
                        os.remove(log_file)
                        print(f"Removed old log file: {log_file}")
                        
                except Exception as e:
                    print(f"Failed to process log file {log_file}: {e}")
                    
        except Exception as e:
            print(f"[ERROR] Log cleanup failed: {e}") 