import subprocess
import json
import time
import threading
import re
import os
from typing import Dict, List, Optional
from datetime import datetime

class AliveService:
    """Alive 서버와 통신하는 서비스 / Service for communicating with Alive server"""
    
    def __init__(self, alivectl_path: str = "../build/alive-server/alivectl"):
        self.alivectl_path = alivectl_path
        self.ioc_list = []
        self.ioc_details = {}
        self.last_update = None
        self.update_interval = 5  # seconds
        self._running = False
        self._lock = threading.Lock()
        
        # Cache system
        self._cache = {
            "status_summary": None,
            "faulted_iocs_info": None,
            "all_events": None,
            "last_cache_update": None
        }
        self.cache_interval = 5  # seconds
        
        # 로그 관련 변수
        self.previous_faulted_iocs = set()
        self.previous_ioc_down_status = {}
        self.masked_iocs = set()
        
        # 로그 디렉토리 생성
        self.log_dir = "/home/ctrluser/Apps/IOC_Monitor/logs"
        os.makedirs(self.log_dir, exist_ok=True)
        
    def start_monitoring(self):
        """Start IOC monitoring thread / IOC 모니터링 스레드 시작"""
        if not self._running:
            self._running = True
            threading.Thread(target=self._monitor_loop, daemon=True).start()
            threading.Thread(target=self._monitor_faulted_iocs, daemon=True).start()
            
            # Log server startup
            self._log_server_event("STARTUP", "Server started")
            print("[INFO] Alive service monitoring started")
    
    def _log_server_event(self, event_type: str, message: str):
        """Log server events to daily log / 서버 이벤트를 일일 로그에 기록"""
        try:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"[{timestamp}] IOCMonitor : [{event_type}] {message}\n"
            
            with open(self.get_daily_log_path(), "a") as log:
                log.write(log_entry)
        except Exception as e:
            print(f"[ERROR] Failed to log server event: {e}")
    
    def log_server_shutdown(self):
        """Log server shutdown event / 서버 종료 이벤트 로그"""
        self._log_server_event("SHUTDOWN", "Server stopped")
    
    def stop_monitoring(self):
        """Stop IOC monitoring / IOC 모니터링 중지"""
        self._running = False
        print("[INFO] Alive service monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop / 메인 모니터링 루프"""
        print("[INFO] Starting main monitoring loop...")
        while self._running:
            try:
                self._update_ioc_list()
                self._update_ioc_details()
                self.last_update = datetime.now()
                
                # Update cache
                self._update_cache()
                
                # Log monitoring status
                if self.last_update:
                    print(f"[INFO] Monitoring update: {len(self.ioc_list)} IOCs, {self.last_update.strftime('%H:%M:%S')}")
            except Exception as e:
                print(f"[ERROR] Alive monitoring failed: {e}")
            
            time.sleep(self.update_interval)
    
    def _update_cache(self):
        """Update cache with latest data / 최신 데이터로 캐시 업데이트"""
        try:
            with self._lock:
                # Update status summary cache
                self._cache["status_summary"] = self._get_status_summary_internal()
                
                # Update faulted IOCs cache
                self._cache["faulted_iocs_info"] = self._get_faulted_iocs_info_internal()
                
                # Update events cache
                self._cache["all_events"] = self._get_all_events_internal()
                
                self._cache["last_cache_update"] = datetime.now()
        except Exception as e:
            print(f"[ERROR] Cache update failed: {e}")
    
    def _get_status_summary_internal(self) -> Dict:
        """Internal method to get status summary / 상태 요약 내부 메서드"""
        total_count = len(self.ioc_list)
        online_count = sum(1 for info in self.ioc_details.values() 
                         if info.get("status") == "ONLINE")
        offline_count = sum(1 for info in self.ioc_details.values() 
                          if info.get("status") == "OFFLINE")
        error_count = sum(1 for info in self.ioc_details.values() 
                        if info.get("status") in ["ERROR", "UNKNOWN"])
        
        return {
            "total_iocs": total_count,
            "online_iocs": online_count,
            "error_iocs": offline_count + error_count,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }
    
    def _get_faulted_iocs_info_internal(self) -> Dict:
        """Internal method to get faulted IOCs info / 장애 IOC 정보 내부 메서드"""
        faulted_iocs = []
        for ioc_name, info in self.ioc_details.items():
            if info.get("status") == "OFFLINE":
                faulted_iocs.append({
                    "name": ioc_name,
                    "status": info.get("status", "OFFLINE"),
                    "ip_address": info.get("ip_address", "N/A"),
                    "last_seen": info.get("last_seen", "N/A"),
                    "message": info.get("message", "N/A"),
                    "masked": ioc_name in self.masked_iocs
                })
        
        return {
            "faulted_count": len(faulted_iocs),
            "faulted_iocs": faulted_iocs,
            "timestamp": datetime.now().isoformat()
        }
    
    def _get_all_events_internal(self) -> List[Dict]:
        """Internal method to get all events / 모든 이벤트 내부 메서드"""
        try:
            log_file = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
            events = []
            
            with open(log_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    parts = line.split()
                    if len(parts) >= 5:
                        events.append({
                            "time": parts[0] + " " + parts[1],
                            "event": parts[3],
                            "ip": parts[4],
                            "code": parts[5] if len(parts) > 5 else "0"
                        })
            
            return events
        except Exception as e:
            print(f"[ERROR] Failed to read events: {e}")
            return []
    
    def _monitor_faulted_iocs(self):
        """Monitor faulted IOCs and log changes / 장애 IOC 모니터링 및 변경 로그"""
        # 초기 데이터 로드 대기
        time.sleep(10)  # 첫 번째 데이터 로드 대기
        
        # 초기 상태 저장
        with self._lock:
            for ioc_name in self.ioc_list:
                info = self.ioc_details.get(ioc_name, {})
                is_down = info.get("status") == "OFFLINE"
                self.previous_ioc_down_status[ioc_name] = is_down

        while self._running:
            try:
                faulted = []
                current_down_iocs = set()
                up_to_down = []
                down_to_up = []

                for ioc_name in self.ioc_list:
                    info = self.ioc_details.get(ioc_name, {})
                    is_down = info.get("status") == "OFFLINE"
                    prev_down = self.previous_ioc_down_status.get(ioc_name, False)

                    # 상태 전이 판별
                    if prev_down != is_down:
                        if is_down:
                            up_to_down.append(ioc_name)
                        else:
                            down_to_up.append(ioc_name)

                    self.previous_ioc_down_status[ioc_name] = is_down

                    if is_down:
                        current_down_iocs.add(ioc_name)
                        faulted.append(info)

                # 상태 전이 로그 출력
                timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                with open(self.get_daily_log_path(), "a") as log:
                    if up_to_down:
                        masked = [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in up_to_down]
                        joined = ", ".join(masked)
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] 상태 전이 감지 (up → down), 대상: {joined}\n")
                    if down_to_up:
                        masked = [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in down_to_up]
                        joined = ", ".join(masked)
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] 상태 전이 감지 (down → up), 대상: {joined}\n")

                current_faulted_names = set(ioc.get("name", "N/A") for ioc in faulted)

                # Faulted 목록 변경 로그
                if current_faulted_names != self.previous_faulted_iocs:
                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

                    def _annotate(names):
                        return [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in sorted(names)]

                    prev_list = _annotate(self.previous_faulted_iocs)
                    curr_list = _annotate(current_faulted_names)

                    with open(self.get_daily_log_path(), "a") as log:
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] Faulted IOC List 변경 감지,")
                        log.write(f"    Unmasked Faulted IOC 수: {len(curr_list)}개 ")
                        log.write(f"    이전: {prev_list}")
                        log.write(f"    현재: {curr_list}\n")

                    self.previous_faulted_iocs = current_faulted_names

            except Exception as e:
                print(f"[ERROR] Faulted IOC monitoring failed: {e}")

            time.sleep(5)
    
    def get_daily_log_path(self):
        """Get daily log file path / 일일 로그 파일 경로 가져오기"""
        today = time.strftime("%Y-%m-%d")
        return os.path.join(self.log_dir, f"faulted_ioc_{today}.log")
    
    def _update_ioc_list(self):
        """Update IOC list from alivectl -l / alivectl -l로 IOC 목록 업데이트"""
        try:
            result = subprocess.run(
                [self.alivectl_path, '-l'],
                capture_output=True, text=True, timeout=10
            )
            
            if result.returncode == 0:
                ioc_names = [name.strip() for name in result.stdout.strip().split('\n') if name.strip()]
                
                with self._lock:
                    self.ioc_list = ioc_names
                    
                print(f"[INFO] Updated IOC list: {len(ioc_names)} IOCs")
            else:
                print(f"[WARNING] Failed to get IOC list: {result.stderr}")
                
        except Exception as e:
            print(f"[ERROR] IOC list update failed: {e}")
    
    def _update_ioc_details(self):
        """Update detailed IOC information / 상세 IOC 정보 업데이트"""
        with self._lock:
            current_iocs = self.ioc_list.copy()
        
        new_details = {}
        
        for ioc_name in current_iocs:
            try:
                result = subprocess.run(
                    [self.alivectl_path, '-i', ioc_name],
                    capture_output=True, text=True, timeout=5
                )
                
                if result.returncode == 0:
                    info = self._parse_ioc_info(result.stdout, ioc_name)
                    new_details[ioc_name] = info
                else:
                    new_details[ioc_name] = {
                        "name": ioc_name,
                        "status": "ERROR",
                        "error": result.stderr.strip()
                    }
                    
            except Exception as e:
                new_details[ioc_name] = {
                    "name": ioc_name,
                    "status": "ERROR",
                    "error": str(e)
                }
        
        with self._lock:
            self.ioc_details = new_details
            
        print(f"[INFO] Loaded {len(new_details)} IOCs from Alive server")
    
    def _parse_ioc_info(self, info_text: str, ioc_name: str) -> Dict:
        """Parse IOC information from alivectl output / alivectl 출력에서 IOC 정보 파싱"""
        info = {
            "name": ioc_name,
            "status": "UNKNOWN",
            "ip_address": "N/A",
            "incarnation": "N/A",
            "last_seen": "N/A",
            "uptime": "N/A",
            "message": "N/A",
            "heartbeat": 0,
            "ping_time": 0,
            "overall_status": "UNKNOWN",
            "raw_info": info_text,
            # 기존 환경 변수들 추가
            "ARCH": "N/A",
            "TOP": "N/A",
            "EPICS_BASE": "N/A",
            "SUPPORT": "N/A",
            "ENGINEER": "N/A",
            "GROUP": "N/A",
            "LOCATION": "N/A",
            "DBLIST": "N/A",
            "PURPOSE": "N/A",
            "BPC": "N/A",
            # ENV1-ENV16 추가
            "ENV1": "N/A",
            "ENV2": "N/A",
            "ENV3": "N/A",
            "ENV4": "N/A",
            "ENV5": "N/A",
            "ENV6": "N/A",
            "ENV7": "N/A",
            "ENV8": "N/A",
            "ENV9": "N/A",
            "ENV10": "N/A",
            "ENV11": "N/A",
            "ENV12": "N/A",
            "ENV13": "N/A",
            "ENV14": "N/A",
            "ENV15": "N/A",
            "ENV16": "N/A",
            "user": "N/A",
            "group": "N/A",
            "host": "N/A"
        }
        
        lines = info_text.split('\n')
        in_env_vars = False
        in_linux_info = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Parse different fields based on actual alivectl output format
            if 'IP address =' in line:
                ip_match = line.split('IP address =')[1].strip()
                info["ip_address"] = ip_match
            elif 'incarnation =' in line:
                inc_match = line.split('incarnation =')[1].strip()
                # Extract timestamp from incarnation
                if '[' in inc_match:
                    inc_match = inc_match.split('[')[1].split(']')[0]
                info["incarnation"] = inc_match
            elif 'ping time =' in line:
                ping_match = line.split('ping time =')[1].strip()
                # Extract timestamp from ping time
                if '[' in ping_match:
                    ping_match = ping_match.split('[')[1].split(']')[0]
                info["last_seen"] = ping_match
                # Extract numeric ping time for status calculation
                try:
                    ping_numeric = int(ping_match.split('[')[0].strip())
                    info["ping_time"] = ping_numeric
                except Exception as e:
                    # Try to extract from the original line
                    try:
                        original_ping = line.split('ping time =')[1].strip()
                        ping_numeric = int(original_ping.split('[')[0].strip())
                        info["ping_time"] = ping_numeric
                    except Exception as e2:
                        pass
            elif 'boot time =' in line:
                boot_match = line.split('boot time =')[1].strip()
                # Extract timestamp from boot time
                if '[' in boot_match:
                    boot_match = boot_match.split('[')[1].split(']')[0]
                info["uptime"] = boot_match
            elif 'user message =' in line:
                msg_match = line.split('user message =')[1].strip()
                info["message"] = msg_match
            elif 'heartbeat =' in line:
                try:
                    heartbeat = int(line.split('heartbeat =')[1].strip())
                    info["heartbeat"] = heartbeat
                except:
                    pass
            elif 'overall status =' in line:
                status_match = line.split('overall status =')[1].strip()
                info["overall_status"] = status_match
                # Convert status codes to readable format
                if status_match == 'U':
                    info["status"] = "UP"
                elif status_match == 'D':
                    info["status"] = "DOWN"
                elif status_match == 'E':
                    info["status"] = "ERROR"
                else:
                    info["status"] = status_match
            elif 'environment variables =' in line:
                in_env_vars = True
                in_linux_info = False
                continue
            elif 'IOC type =' in line:
                in_env_vars = False
                in_linux_info = True
                continue
            elif in_env_vars and '=' in line:
                # 환경 변수 파싱
                parts = line.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip()
                    if var_name in info:
                        info[var_name] = var_value
            elif in_linux_info and '=' in line:
                # Linux 정보 파싱
                parts = line.split('=', 1)
                if len(parts) == 2:
                    var_name = parts[0].strip()
                    var_value = parts[1].strip()
                    if var_name in info:
                        info[var_name] = var_value
        
        # Determine actual online/offline status based on overall status and heartbeat
        info["status"] = self._determine_actual_status(info)
        
        return info
    
    def _determine_actual_status(self, info: Dict) -> str:
        """Determine actual IOC status based on overall status and heartbeat / overall status와 heartbeat를 기반으로 실제 IOC 상태 판단"""
        overall_status = info.get("overall_status", "UNKNOWN")
        heartbeat = info.get("heartbeat", 0)
        ping_time = info.get("ping_time", 0)
        
        # 기존 로직: overall status가 주요 지표
        if overall_status == 'U':
            return "ONLINE"
        elif overall_status == 'D':
            return "OFFLINE"
        elif overall_status == 'E':
            return "ERROR"
        
        # 백업 로직: heartbeat와 ping time 기반
        current_time = int(time.time())
        
        # If heartbeat > 0, IOC is responding and should be considered online
        if heartbeat > 0:
            return "ONLINE"
        
        # If ping time is 0, IOC is offline
        if ping_time == 0:
            return "OFFLINE"
        
        # Calculate time difference between current time and last ping
        time_diff = current_time - ping_time
        
        # If last ping was more than 300 seconds (5 minutes) ago, consider IOC offline
        if time_diff > 300:
            return "OFFLINE"
        
        # If heartbeat is 0 but recent ping exists, IOC might be having issues
        if heartbeat == 0:
            return "UNKNOWN"
        
        # Default to online if we have recent ping
        return "ONLINE"
    
    def get_ioc_list(self) -> List[str]:
        """Get current IOC list / 현재 IOC 목록 가져오기"""
        with self._lock:
            return self.ioc_list.copy()
    
    def get_ioc_details(self) -> Dict:
        """Get detailed IOC information / 상세 IOC 정보 가져오기"""
        with self._lock:
            return self.ioc_details.copy()
    
    def get_ioc_detail(self, ioc_name: str) -> Optional[Dict]:
        """Get specific IOC detail / 특정 IOC 상세 정보 가져오기"""
        with self._lock:
            return self.ioc_details.get(ioc_name)
    
    def get_status_summary(self) -> Dict:
        """Get IOC status summary / IOC 상태 요약 가져오기"""
        with self._lock:
            if self._cache["status_summary"] is not None:
                return self._cache["status_summary"]
            else:
                return self._get_status_summary_internal()
    
    def get_faulted_iocs_info(self) -> Dict:
        """Get current faulted IOCs information / 현재 장애 IOC 정보 가져오기"""
        with self._lock:
            if self._cache["faulted_iocs_info"] is not None:
                return self._cache["faulted_iocs_info"]
            else:
                return self._get_faulted_iocs_info_internal()
    
    def get_ioc_logs(self, ioc_name: str) -> List[Dict]:
        """Get IOC event logs / IOC 이벤트 로그 가져오기"""
        logfile = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
        logs = []

        try:
            with open(logfile, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # events.txt 형식: 2025-08-07 00:39:12 TEST-SYS:MCP-EXP001 FAIL 192.168.70.235 0
                    if ioc_name in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            logs.append({
                                "time": parts[0] + " " + parts[1],  # ex. 2025-08-07 00:39:12
                                "event": parts[3],                  # ex. BOOT, FAIL
                                "ip": parts[4],                     # ex. 192.168.70.235
                                "code": parts[5] if len(parts) > 5 else "0"  # ex. 0
                            })
        except FileNotFoundError:
            print(f"[WARNING] Log file not found: {logfile}")
        except Exception as e:
            print(f"[ERROR] Failed to read log file: {e}")

        # 최신 순서로 역정렬
        return logs[::-1]
    
    def get_server_log_dates(self) -> List[str]:
        """Get available server log dates / 사용 가능한 서버 로그 날짜 가져오기"""
        try:
            files = os.listdir(self.log_dir)
            dates = []
            for f in files:
                if f.startswith("faulted_ioc_") and f.endswith(".log"):
                    date_part = f[len("faulted_ioc_"):-len(".log")]
                    dates.append(date_part)
            dates.sort()
            return dates
        except Exception as e:
            print(f"[ERROR] Failed to get log dates: {e}")
            return []
    
    def get_server_log_by_date(self, date: str) -> str:
        """Get server log content by date / 날짜별 서버 로그 내용 가져오기"""
        try:
            log_path = os.path.join(self.log_dir, f"faulted_ioc_{date}.log")
            with open(log_path, "r") as f:
                content = f.read()
            return content
        except Exception as e:
            print(f"[ERROR] Failed to read log for date {date}: {e}")
            return f"로그 파일 읽기 실패: {e}"
    
    def ping_alive_server(self) -> bool:
        """Ping alive server to check if it's running / Alive 서버가 실행 중인지 확인"""
        try:
            result = subprocess.run(
                [self.alivectl_path, '-p'],
                capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except Exception as e:
            print(f"[ERROR] Alive server ping failed: {e}")
            return False 