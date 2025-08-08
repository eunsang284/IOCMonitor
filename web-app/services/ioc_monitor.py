# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Service
EPICS IOC 모니터 서비스
Core IOC monitoring functionality
핵심 IOC 모니터링 기능
"""

import os
import time
import subprocess
import pandas as pd
from typing import List, Dict, Any, Set
from datetime import datetime

from utils.helpers import safe_str, format_uptime, parse_hex_value, get_timestamp

class IOCMonitor:
    """IOC monitoring service / IOC 모니터링 서비스"""
    
    def __init__(self):
        """Initialize IOC monitor / IOC 모니터 초기화"""
        self.cache_data = []
        self.previous_faulted_iocs = set()
        self.previous_ioc_down_status = {}
        self.prev_ready_val = None
        self.masked_iocs = set()
        
        # Load configuration
        from config import Config
        self.config = Config()
        
        # Ensure directories exist
        os.makedirs(self.config.LOG_DIR, exist_ok=True)
        os.makedirs(self.config.CACHE_DIR, exist_ok=True)
    
    def check_running(self, name: str) -> bool:
        """
        Check if process is running / 프로세스 실행 여부 확인
        
        Args:
            name: Process name to check / 확인할 프로세스 이름
            
        Returns:
            bool: True if running, False otherwise / 실행 중이면 True, 아니면 False
        """
        try:
            result = subprocess.run(["pgrep", "-f", name], 
                                  stdout=subprocess.DEVNULL, 
                                  stderr=subprocess.DEVNULL)
            return result.returncode == 0
        except Exception:
            return False
    
    def get_daily_log_path(self) -> str:
        """
        Get daily log file path / 일일 로그 파일 경로 반환
        
        Returns:
            str: Log file path / 로그 파일 경로
        """
        today = time.strftime("%Y-%m-%d")
        log_dir = self.config.LOG_DIR
        os.makedirs(log_dir, exist_ok=True)
        return os.path.join(log_dir, f"faulted_ioc_{today}.log")
    
    def load_ioc_cache(self, cache_path: str) -> Dict[str, Dict[str, str]]:
        """
        Load IOC cache from file / 파일에서 IOC 캐시 로드
        
        Args:
            cache_path: Path to cache file / 캐시 파일 경로
            
        Returns:
            Dict[str, Dict[str, str]]: IOC cache data / IOC 캐시 데이터
        """
        ioc_cache = {}
        try:
            with open(cache_path, "r") as f:
                lines = f.readlines()
            
            for line in lines:
                if line.startswith("IOC이름") or line.strip() == "" or line.startswith("캐싱된 시간"):
                    continue
                
                parts = line.strip().split("\t")
                if len(parts) >= 6:
                    ioc_name = parts[0]
                    ioc_cache[ioc_name] = {
                        "MEM_USED": parts[1],
                        "MEM_MAX": parts[2],
                        "MEM_PER": parts[3],
                        "SYS_CPU_LOAD": parts[4],
                        "NETWORK_USED": parts[5],
                    }
        except Exception as e:
            print(f"[ERROR] Cache loading failed: {e}")
        
        return ioc_cache
    
    def load_and_cache_data(self):
        """Load and cache IOC data periodically / 주기적으로 IOC 데이터 로드 및 캐싱"""
        while True:
            try:
                # Check if CSV loading is enabled / CSV 로딩이 활성화되었는지 확인
                if not self.config.FEATURE_CSV_LOADING:
                    # Try to load data from Alive server instead / 대신 Alive 서버에서 데이터 로드 시도
                    if self.config.FEATURE_ALIVE_SERVER:
                        try:
                            # Get IOC list from alivectl
                            result = subprocess.run(
                                ['../build/alive-server/alivectl', '-l'],
                                capture_output=True, text=True, timeout=10
                            )
                            
                            if result.returncode == 0 and result.stdout.strip():
                                ioc_list = result.stdout.strip().split('\n')
                                self.cache_data = []
                                
                                for ioc_name in ioc_list:
                                    if ioc_name.strip():
                                        # Get detailed IOC info
                                        try:
                                            info_result = subprocess.run(
                                                ['../build/alive-server/alivectl', '-i', ioc_name.strip()],
                                                capture_output=True, text=True, timeout=5
                                            )
                                            
                                            ioc_data = {
                                                "ioc": ioc_name.strip(),
                                                "ipaddress": "N/A",  # Will be updated if available
                                                "STATUS_TIME": {"isDown": False},  # Default status
                                                "info": info_result.stdout if info_result.returncode == 0 else "No info available"
                                            }
                                            
                                            # Try to get IP address from info
                                            if info_result.returncode == 0:
                                                for line in info_result.stdout.split('\n'):
                                                    if 'IP:' in line or 'Address:' in line:
                                                        ip_match = re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', line)
                                                        if ip_match:
                                                            ioc_data["ipaddress"] = ip_match.group()
                                                            break
                                            
                                            self.cache_data.append(ioc_data)
                                            
                                        except Exception as e:
                                            print(f"[WARNING] Failed to get info for IOC {ioc_name}: {e}")
                                            self.cache_data.append({
                                                "ioc": ioc_name.strip(),
                                                "ipaddress": "N/A",
                                                "STATUS_TIME": {"isDown": False},
                                                "info": "Error getting info"
                                            })
                                
                                print(f"[INFO] Loaded {len(self.cache_data)} IOCs from Alive server")
                            else:
                                print("[INFO] No IOCs found in Alive server")
                                self.cache_data = []
                                
                        except Exception as e:
                            print(f"[WARNING] Failed to load data from Alive server: {e}")
                            self.cache_data = []
                    else:
                        print("[INFO] CSV loading and Alive server both disabled. Using empty data.")
                        self.cache_data = []
                    
                    time.sleep(self.config.CACHE_UPDATE_INTERVAL)
                    continue
                
                # Load CSV files (original code)
                df_main = pd.read_csv(self.config.CSV_MAIN, sep=";", engine="python", header=1)
                df_env_raw = pd.read_csv(self.config.CSV_ENV, sep=";", engine="python", comment="#")
                df_linux = pd.read_csv(self.config.CSV_LINUX, sep=";", engine="python", comment="#")
                
                # Convert entry columns to string
                df_main["entry"] = df_main["entry"].astype(str)
                df_env_raw["entry"] = df_env_raw["entry"].astype(str)
                df_linux["entry"] = df_linux["entry"].astype(str)
                
                # Pivot environment data
                df_env = df_env_raw.pivot(index="entry", columns="variable", values="value").reset_index()
                
                # Merge dataframes
                df_merged = df_main.merge(df_env, on="entry", how="left") \
                                   .merge(df_linux, on="entry", how="left")
                
                # Apply PV cache
                ioc_cache = self.load_ioc_cache(self.config.CACHE_FILE)
                
                def apply_cache(row):
                    ioc_name = row["ioc"]
                    cache = ioc_cache.get(ioc_name, {})
                    row["MEM_USED"] = cache.get("MEM_USED", "N/A")
                    row["MEM_MAX"] = cache.get("MEM_MAX", "N/A")
                    row["MEM_PER"] = cache.get("MEM_PER", "N/A")
                    row["SYS_CPU_LOAD"] = cache.get("SYS_CPU_LOAD", "N/A")
                    raw_network = cache.get("NETWORK_USED", "N/A")
                    if isinstance(raw_network, str) and "byte" in raw_network:
                        raw_network = raw_network.replace("bytes", "").strip()
                    row["NETWORK_USED"] = raw_network
                    return row
                
                df_merged = df_merged.apply(apply_cache, axis=1)
                
                # Add status fields
                now = time.time()
                
                def apply_status(row):
                    st = str(row.get("status", "")).strip().lower()
                    boot = pd.to_datetime(row.get("boottime"), errors="coerce")
                    inc = pd.to_datetime(row.get("incarnation"), errors="coerce")
                    is_down = False
                    delta = 0
                    text = ""
                    
                    if st == "down" and pd.notna(inc):
                        delta = max(0, now - inc.timestamp())
                        text = f"↓ {format_uptime(delta)}"
                        is_down = True
                    elif st == "up" and pd.notna(boot):
                        delta = now - boot.timestamp()
                        text = f"↑ {format_uptime(delta)}"
                    else:
                        text = f"{'↓' if st == 'down' else '↑'} N/A"
                    
                    row["STATUS_TIME"] = {
                        "text": text,
                        "seconds": int(delta),
                        "isDown": is_down
                    }
                    return row
                
                df_merged = df_merged.apply(apply_status, axis=1)
                df_merged["MSG"] = df_merged["usermsg"] if "usermsg" in df_merged.columns else "N/A"
                
                # Update cache
                self.cache_data.clear()
                self.cache_data.extend(df_merged.to_dict(orient="records"))
                print(f"[CACHE UPDATED] {get_timestamp()}")
                
            except Exception as e:
                print(f"[ERROR] Cache loading failed: {e}")
            
            time.sleep(self.config.CACHE_UPDATE_INTERVAL)
    
    def get_faulted_iocs(self, cache_data: List[Dict], masked_iocs: Set[str]) -> List[Dict]:
        """
        Get faulted IOCs / 장애 IOC 조회
        
        Args:
            cache_data: IOC cache data / IOC 캐시 데이터
            masked_iocs: Set of masked IOC names / 마스크된 IOC 이름 집합
            
        Returns:
            List[Dict]: List of faulted IOCs / 장애 IOC 목록
        """
        # Check if faulted monitoring is enabled / 장애 모니터링이 활성화되었는지 확인
        if not self.config.FEATURE_FAULTED_MONITORING:
            return []
        
        faulted = []
        for ioc in cache_data:
            ioc_name = ioc.get("ioc", "N/A")
            status_info = ioc.get("STATUS_TIME", {})
            is_down = isinstance(status_info, dict) and status_info.get("isDown", False)
            
            # Simple fault detection: IOC is down
            if is_down:
                faulted.append(ioc)
        
        # Filter out masked IOCs
        filtered = [ioc for ioc in faulted if ioc.get("ioc") not in masked_iocs]
        return filtered
    
    def monitor_faulted_iocs(self):
        """Monitor faulted IOCs and log changes / 장애 IOC 모니터링 및 변경 로그"""
        # Check if faulted monitoring is enabled / 장애 모니터링이 활성화되었는지 확인
        if not self.config.FEATURE_FAULTED_MONITORING:
            print("[INFO] Faulted IOC monitoring disabled.")
            return
        
        # Initialize previous states
        for ioc in self.cache_data:
            ioc_name = ioc.get("ioc", "N/A")
            status_info = ioc.get("STATUS_TIME", {})
            is_down = isinstance(status_info, dict) and status_info.get("isDown", False)
            self.previous_ioc_down_status[ioc_name] = is_down
        
        while True:
            try:
                faulted = []
                current_down_iocs = set()
                up_to_down = []
                down_to_up = []
                
                for ioc in self.cache_data:
                    ioc_name = ioc.get("ioc", "N/A")
                    status_info = ioc.get("STATUS_TIME", {})
                    is_down = isinstance(status_info, dict) and status_info.get("isDown", False)
                    prev_down = self.previous_ioc_down_status.get(ioc_name, False)
                    
                    # State transition detection
                    if prev_down != is_down:
                        if is_down:
                            up_to_down.append(ioc_name)
                        else:
                            down_to_up.append(ioc_name)
                    
                    self.previous_ioc_down_status[ioc_name] = is_down
                    
                    # Simple fault detection: IOC is down
                    if is_down:
                        current_down_iocs.add(ioc_name)
                        faulted.append(ioc)
                
                # Log state transitions
                timestamp = get_timestamp()
                with open(self.get_daily_log_path(), "a") as log:
                    if up_to_down:
                        masked = [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in up_to_down]
                        joined = ", ".join(masked)
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] State transition detected (up → down), targets: {joined}\n")
                    if down_to_up:
                        masked = [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in down_to_up]
                        joined = ", ".join(masked)
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] State transition detected (down → up), targets: {joined}\n")
                
                current_faulted_names = set(ioc.get("ioc", "N/A") for ioc in faulted)
                
                # Log faulted list changes
                if current_faulted_names != self.previous_faulted_iocs:
                    timestamp = get_timestamp()
                    
                    def _annotate(names):
                        return [f"{n}{' [masked]' if n in self.masked_iocs else ''}" for n in sorted(names)]
                    
                    prev_list = _annotate(self.previous_faulted_iocs)
                    curr_list = _annotate(current_faulted_names)
                    
                    with open(self.get_daily_log_path(), "a") as log:
                        log.write(f"[{timestamp}] IOCMonitor : [LOG] Faulted IOC List change detected,")
                        log.write(f"    Unmasked Faulted IOC count: {len(curr_list)} ")
                        log.write(f"    Previous: {prev_list}")
                        log.write(f"    Current: {curr_list}\n")
                    
                    self.previous_faulted_iocs = current_faulted_names
                
            except Exception as e:
                print(f"[ERROR] Faulted IOC monitoring failed: {e}")
            
            time.sleep(self.config.FAULTED_MONITOR_INTERVAL)
    
    def update_control_pvs_periodically(self):
        """Update control PVs based on monitoring conditions / 모니터링 조건에 따라 제어 PV 업데이트"""
        while True:
            try:
                # Check if control PVs are enabled / 제어 PV가 활성화되었는지 확인
                if not self.config.FEATURE_CONTROL_PVS:
                    time.sleep(self.config.IOC_READY_UPDATE_INTERVAL)
                    continue
                
                # Get current monitoring data / 현재 모니터링 데이터 가져오기
                monitoring_data = self.get_monitoring_data()
                
                # Process each control PV / 각 제어 PV 처리
                for control_pv_name, control_pv_config in self.config.CONTROL_PVS.items():
                    if not control_pv_config.get("enabled", False):
                        continue
                    
                    pv_address = control_pv_config["pv_address"]
                    conditions = control_pv_config.get("conditions", {})
                    
                    # Check conditions and determine new value / 조건 확인하고 새 값 결정
                    new_value = self.evaluate_control_conditions(conditions, monitoring_data)
                    
                    if new_value is not None:
                        # Set the control PV / 제어 PV 설정
                        try:
                            subprocess.run(
                                ["caput", pv_address, str(new_value)],
                                check=True,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE
                            )
                            print(f"[SET] {control_pv_name} ({pv_address}) ← {new_value}")
                            
                            # Log the change / 변경 사항 로그
                            timestamp = get_timestamp()
                            log_line = f"[{timestamp}] IOCMonitor : [CONTROL] {control_pv_name} set to {new_value}"
                            with open(self.get_daily_log_path(), "a") as log:
                                log.write(log_line + "\n")
                                
                        except subprocess.CalledProcessError as e:
                            print(f"[ERROR] {control_pv_name} setting failed: {e.stderr.decode().strip()}")
                
            except Exception as e:
                print(f"[ERROR] Control PV update failed: {e}")
            
            time.sleep(self.config.IOC_READY_UPDATE_INTERVAL)
    
    def get_monitoring_data(self):
        """Get current monitoring data / 현재 모니터링 데이터 가져오기"""
        data = {}
        
        # Get faulted IOC count / 장애 IOC 개수 가져오기
        faulted_count = len(self.get_faulted_iocs(self.cache_data, set()))
        data["faulted_ioc_count"] = faulted_count
        
        # Check if PV monitoring is enabled / PV 모니터링이 활성화되었는지 확인
        if not self.config.FEATURE_PV_MONITORING:
            print("[INFO] PV monitoring disabled. Skipping PV reads.")
            return data
        
        # Get monitoring PV values / 모니터링 PV 값들 가져오기
        for pv_name, pv_address in self.config.EPICS_PVS.items():
            try:
                value = subprocess.check_output(['caget', '-t', pv_address], encoding='utf-8', timeout=5).strip()
                data[pv_name] = value
            except Exception as e:
                print(f"[WARNING] Failed to read PV {pv_name} ({pv_address}): {e}")
                data[pv_name] = "ERROR"
        
        return data
    
    def evaluate_control_conditions(self, conditions, monitoring_data):
        """Evaluate control conditions and return new value / 제어 조건 평가하고 새 값 반환"""
        for condition_type, condition_config in conditions.items():
            operator = condition_config["operator"]
            expected_value = condition_config["value"]
            set_value = condition_config["set_value"]
            
            current_value = monitoring_data.get(condition_type, "0")
            
            # Convert to appropriate type for comparison / 비교를 위해 적절한 타입으로 변환
            try:
                if "." in str(expected_value):
                    current_value = float(current_value)
                    expected_value = float(expected_value)
                else:
                    current_value = int(current_value)
                    expected_value = int(expected_value)
            except:
                current_value = str(current_value)
                expected_value = str(expected_value)
            
            # Evaluate condition / 조건 평가
            condition_met = False
            if operator == "==":
                condition_met = current_value == expected_value
            elif operator == "!=":
                condition_met = current_value != expected_value
            elif operator == ">":
                condition_met = current_value > expected_value
            elif operator == "<":
                condition_met = current_value < expected_value
            elif operator == ">=":
                condition_met = current_value >= expected_value
            elif operator == "<=":
                condition_met = current_value <= expected_value
            
            if condition_met:
                return set_value
        
        return None
    
    def delete_ioc(self, ioc_name: str) -> str:
        """
        Delete IOC from alive server / alive 서버에서 IOC 삭제
        
        Args:
            ioc_name: IOC name to delete / 삭제할 IOC 이름
            
        Returns:
            str: Command output / 명령 출력
        """
        cmd = [
            "sudo",
            self.config.ALIVECTL_EXEC,
            "-d",
            ioc_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return result.stdout.strip() 