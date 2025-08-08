# -*- coding: utf-8 -*-
"""
EPICS PV Service
EPICS PV 서비스
PV management and caching functionality
PV 관리 및 캐싱 기능
"""

import time
import subprocess
import threading
from typing import Dict, List, Optional
from datetime import datetime

# EPICS Channel Access 라이브러리 import
try:
    import epics
    from epics import PV
    EPICS_AVAILABLE = True
except ImportError:
    EPICS_AVAILABLE = False
    print("Warning: epics library not found. Install with: pip install pyepics")

class PVService:
    """EPICS PV service / EPICS PV 서비스"""
    
    def __init__(self):
        """Initialize PV service / PV 서비스 초기화"""
        self.pv_cache = {}  # Global cache: PV name → info
        
        # Load configuration
        from config import Config
        self.config = Config()
        
        # IOC Monitor Ready Control PVs
        self.threshold_pv_name = "TEST-CTRL:SYS-MACHINE:MODE"
        self.control_pv_name = "TEST-CTRL:SYS-IOCM:READY"
        
        # EPICS PV connections
        self.threshold_pv = None
        self.control_pv = None
        self.pv_connections_ready = False
        
        # Control logic state
        self.last_control_check = 0
        self.control_check_interval = 1  # 1초마다 체크
        self.last_inactive_ioc_check = False
        
        # Initialize EPICS connections if available
        if EPICS_AVAILABLE:
            self._setup_epics_connections()
    
    def _setup_epics_connections(self):
        """Setup EPICS PV connections / EPICS PV 연결 설정"""
        try:
            # Threshold PV (BPC 임계값)
            self.threshold_pv = PV(self.threshold_pv_name, auto_monitor=True)
            
            # Control PV (제어할 대상)
            self.control_pv = PV(self.control_pv_name, auto_monitor=True)
            
            # 연결 대기
            time.sleep(1)
            
            if self.threshold_pv.connected and self.control_pv.connected:
                self.pv_connections_ready = True
                print(f"[PV SERVICE] EPICS PV connections established")
                print(f"[PV SERVICE] Threshold PV: {self.threshold_pv_name}")
                print(f"[PV SERVICE] Control PV: {self.control_pv_name}")
            else:
                print(f"[PV SERVICE] Failed to connect to EPICS PVs")
                if not self.threshold_pv.connected:
                    print(f"[PV SERVICE] Threshold PV not connected: {self.threshold_pv_name}")
                if not self.control_pv.connected:
                    print(f"[PV SERVICE] Control PV not connected: {self.control_pv_name}")
                    
        except Exception as e:
            print(f"[PV SERVICE] Error setting up EPICS connections: {e}")
    
    def get_threshold_value(self) -> Optional[float]:
        """Get threshold PV value / 임계값 PV 값 조회"""
        if self.threshold_pv and self.threshold_pv.connected:
            try:
                return self.threshold_pv.get()
            except Exception as e:
                print(f"[PV SERVICE] Error getting threshold value: {e}")
                return None
        return None
    
    def get_control_value(self) -> Optional[float]:
        """Get control PV value / 제어 PV 값 조회"""
        if self.control_pv and self.control_pv.connected:
            try:
                return self.control_pv.get()
            except Exception as e:
                print(f"[PV SERVICE] Error getting control value: {e}")
                return None
        return None
    
    def set_control_value(self, value: float) -> bool:
        """Set control PV value / 제어 PV 값 설정"""
        if self.control_pv and self.control_pv.connected:
            try:
                self.control_pv.put(value)
                print(f"[PV SERVICE] Set control PV to {value}")
                return True
            except Exception as e:
                print(f"[PV SERVICE] Error setting control value: {e}")
                return False
        return False
    
    def check_inactive_iocs(self) -> bool:
        """Check if there are inactive IOCs / 비활성화된 IOC가 있는지 확인"""
        try:
            from services.alive_service import AliveService
            alive_service = AliveService()
            ioc_details = alive_service.get_ioc_details()
            
            inactive_count = sum(1 for info in ioc_details.values() if info.get("status") == "OFFLINE")
            return inactive_count > 0
            
        except Exception as e:
            print(f"[PV SERVICE] Error checking IOC status: {e}")
            return False
    
    def parse_bpc_value(self, bpc_str) -> int:
        """Parse BPC value from various formats / 다양한 형식의 BPC 값을 숫자로 변환"""
        if bpc_str is None:
            return 0
        
        # 문자열로 변환
        bpc_str = str(bpc_str).strip()
        
        try:
            # 16진수 형식 (0x00, 0x01 등)
            if bpc_str.startswith('0x') or bpc_str.startswith('0X'):
                return int(bpc_str, 16)
            
            # 2진수 형식 (0b1, 0b0 등)
            elif bpc_str.startswith('0b') or bpc_str.startswith('0B'):
                return int(bpc_str, 2)
            
            # 8진수 형식 (0o1, 0o0 등)
            elif bpc_str.startswith('0o') or bpc_str.startswith('0O'):
                return int(bpc_str, 8)
            
            # 일반 10진수
            else:
                return int(bpc_str)
                
        except (ValueError, TypeError):
            print(f"[PV SERVICE] Failed to parse BPC value: {bpc_str}, using 0")
            return 0
    
    def check_low_bpc_inactive_iocs(self) -> bool:
        """Check if there are inactive IOCs with BPC < threshold / BPC가 임계값보다 낮은 비활성화된 IOC가 있는지 확인"""
        try:
            print(f"[PV SERVICE] Starting check_low_bpc_inactive_iocs...")
            
            # API에서 IOC 데이터 가져오기
            import requests
            
            try:
                response = requests.get("http://localhost:5001/api/alive/ioc_details", timeout=5)
                if response.status_code != 200:
                    print(f"[PV SERVICE] Failed to get IOC details: {response.status_code}")
                    return False
                
                ioc_details = response.json()
                print(f"[PV SERVICE] Got {len(ioc_details)} IOCs from API")
                
            except Exception as e:
                print(f"[PV SERVICE] Error getting IOC details from API: {e}")
                return False
            
            # 임계값 가져오기 (기본값: 1)
            threshold = self.get_threshold_value()
            if threshold is None:
                threshold = 1.0
            
            print(f"[PV SERVICE] Threshold value: {threshold}")
            print(f"[PV SERVICE] Checking {len(ioc_details)} IOCs for BPC >= {threshold} inactive ones...")
            
            # 꺼진 IOC들 중에서 BPC ≤ 임계값인 것 확인
            for ioc_name, info in ioc_details.items():
                bpc_raw = info.get("BPC", info.get("bpc", 0))
                bpc_value = self.parse_bpc_value(bpc_raw)
                status = info.get("status", "UNKNOWN")
                
                print(f"[PV SERVICE] IOC {ioc_name}: BPC={bpc_value}, status={status}")
                
                # IOC가 꺼져있고 BPC ≤ 임계값인 경우
                # overall_status를 직접 사용하여 상태 판단
                overall_status = info.get("overall_status", "U")
                last_seen_str = info.get("last_seen", "")
                
                # overall_status가 "DO" (Down)이거나 "D" (Disconnected)인 경우 꺼진 것으로 판단
                is_offline = overall_status in ["DO", "D", "DOWN"]
                
                # last_seen이 1분 이상 과거인지 확인 (백업 조건)
                is_old_last_seen = False
                if last_seen_str:
                    try:
                        from datetime import datetime
                        last_seen_time = datetime.strptime(last_seen_str, "%Y-%m-%d %H:%M:%S")
                        current_time = datetime.now()
                        time_diff = (current_time - last_seen_time).total_seconds()
                        is_old_last_seen = time_diff > 60  # 1분 = 60초
                        print(f"[PV SERVICE] IOC {ioc_name}: overall_status={overall_status}, last_seen={last_seen_str}, time_diff={time_diff:.0f}s, is_old={is_old_last_seen}")
                    except Exception as e:
                        print(f"[PV SERVICE] Error parsing last_seen for {ioc_name}: {e}")
                
                if (is_offline or is_old_last_seen) and bpc_value >= threshold:
                    print(f"[PV SERVICE] Found inactive IOC with BPC >= {threshold}: {ioc_name} (BPC={bpc_value}, overall_status={overall_status}, old_last_seen={is_old_last_seen})")
                    return True
            
            print(f"[PV SERVICE] No inactive IOCs with BPC >= {threshold} found")
            return False
            
        except Exception as e:
            print(f"[PV SERVICE] Error checking low BPC inactive IOCs: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def evaluate_control_logic(self) -> float:
        """Evaluate control logic and return target value / 제어 로직 평가 및 목표값 반환"""
        # BPC ≤ 임계값인 비활성화된 IOC가 있는지 확인
        has_low_bpc_inactive_iocs = self.check_low_bpc_inactive_iocs()
        
        # 제어 로직: BPC ≤ 임계값인 IOC가 꺼져있으면 0 (NOT READY), 아니면 1 (READY)
        if has_low_bpc_inactive_iocs:
            print(f"[PV SERVICE] Low BPC inactive IOCs found, setting control PV to 0 (NOT READY)")
            return 0
        else:
            print(f"[PV SERVICE] No low BPC inactive IOCs, setting control PV to 1 (READY)")
            return 1
    
    def apply_control_logic(self):
        """Apply control logic / 제어 로직 적용"""
        if not self.pv_connections_ready:
            return
        
        current_time = time.time()
        
        # 1초마다 체크
        if current_time - self.last_control_check >= self.control_check_interval:
            self.last_control_check = current_time
            
            # BPC < 임계값인 비활성화된 IOC가 있는지 확인
            has_low_bpc_inactive_iocs = self.check_low_bpc_inactive_iocs()
            
            # 매번 제어 로직 실행 (더 빠른 반응을 위해)
            print(f"[PV SERVICE] Checking low BPC inactive IOCs: {has_low_bpc_inactive_iocs}")
            
            target_value = self.evaluate_control_logic()
            current_value = self.get_control_value()
            
            if current_value != target_value:
                success = self.set_control_value(target_value)
                if success:
                    print(f"[PV SERVICE] Control logic applied: {current_value} → {target_value}")
                else:
                    print(f"[PV SERVICE] Failed to apply control logic")
            else:
                print(f"[PV SERVICE] Control value unchanged: {current_value}")
            
            self.last_inactive_ioc_check = has_low_bpc_inactive_iocs
    
    def get_ioc_monitor_ready_status(self) -> Dict:
        """Get IOC Monitor Ready status / IOC Monitor Ready 상태 조회"""
        status = {
            "enabled": EPICS_AVAILABLE and self.pv_connections_ready,
            "threshold_pv": self.threshold_pv_name,
            "threshold_value": self.get_threshold_value(),
            "threshold_connected": self.threshold_pv.connected if self.threshold_pv else False,
            "control_pv": self.control_pv_name,
            "control_value": self.get_control_value(),
            "control_connected": self.control_pv.connected if self.control_pv else False,
            "last_check": datetime.fromtimestamp(self.last_control_check).strftime("%Y-%m-%d %H:%M:%S") if self.last_control_check > 0 else "Never",
            "low_bpc_inactive_iocs_found": self.check_low_bpc_inactive_iocs(),
            "recommended_value": self.evaluate_control_logic()
        }
        
        return status
    
    def update_pv_cache(self):
        """Update PV cache periodically / 주기적으로 PV 캐시 업데이트"""
        while True:
            try:
                # Check if PV cache is enabled / PV 캐시가 활성화되었는지 확인
                if not self.config.FEATURE_PV_CACHE:
                    time.sleep(self.config.PV_CACHE_UPDATE_INTERVAL)
                    continue
                
                # Get IOC list from cache data
                from app import cache_data
                ioc_list = [(ioc["ioc"], ioc["ipaddress"]) for ioc in cache_data if ioc.get("ipaddress")]
                
                new_cache = {}
                for ioc_name, ip in ioc_list:
                    try:
                        output = subprocess.check_output(["pvlist", ip], encoding="utf-8", timeout=5)
                        pvs = [line.strip() for line in output.splitlines() if line.strip()]
                        for pv in pvs:
                            new_cache[pv] = {
                                "ioc": ioc_name,
                                "ip": ip
                            }
                    except Exception as e:
                        print(f"[WARN] {ioc_name}({ip}) PV collection failed: {e}")
                
                self.pv_cache = new_cache
                print(f"[PV CACHE UPDATED] {len(self.pv_cache)} PVs collected")
                
            except Exception as e:
                print(f"[ERROR] PV cache update failed: {e}")
            
            time.sleep(self.config.PV_CACHE_UPDATE_INTERVAL)
    
    def search_pvs(self, query: str) -> Dict[str, Dict]:
        """
        Search PVs by query / 쿼리로 PV 검색
        
        Args:
            query: Search query / 검색 쿼리
            
        Returns:
            Dict[str, Dict]: Matching PVs / 일치하는 PV들
        """
        q = query.lower()
        results = {
            pv: info for pv, info in self.pv_cache.items()
            if q in pv.lower()
        }
        return results
    
    def get_pv_details(self, pvname: str) -> Dict:
        """
        Get PV details / PV 상세 정보 조회
        
        Args:
            pvname: PV name / PV 이름
            
        Returns:
            Dict: PV details / PV 상세 정보
        """
        return self.pv_cache.get(pvname, {})
    
    def get_pv_autocomplete(self, query: str, limit: int = 10) -> List[str]:
        """
        Get PV autocomplete suggestions / PV 자동완성 제안 조회
        
        Args:
            query: Autocomplete query / 자동완성 쿼리
            limit: Maximum number of suggestions / 최대 제안 수
            
        Returns:
            List[str]: Matching PV names / 일치하는 PV 이름들
        """
        q = query.lower()
        matches = [pv for pv in self.pv_cache if q in pv.lower()]
        return matches[:limit]
    
    def get_pv_value(self, pvname: str) -> str:
        """
        Get current PV value / 현재 PV 값 조회
        
        Args:
            pvname: PV name / PV 이름
            
        Returns:
            str: PV value / PV 값
        """
        try:
            result = subprocess.check_output(['caget', '-t', pvname], encoding='utf-8', timeout=5)
            return result.strip()
        except subprocess.CalledProcessError:
            return "ERROR"
        except subprocess.TimeoutExpired:
            return "TIMEOUT"
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def set_pv_value(self, pvname: str, value: str) -> bool:
        """
        Set PV value / PV 값 설정
        
        Args:
            pvname: PV name / PV 이름
            value: Value to set / 설정할 값
            
        Returns:
            bool: True if successful, False otherwise / 성공하면 True, 아니면 False
        """
        try:
            subprocess.run(['caput', pvname, value], check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return False
        except Exception:
            return False
    
    def get_pv_info(self, pvname: str) -> Dict:
        """
        Get detailed PV information / 상세 PV 정보 조회
        
        Args:
            pvname: PV name / PV 이름
            
        Returns:
            Dict: PV information / PV 정보
        """
        try:
            # Get PV value
            value = self.get_pv_value(pvname)
            
            # Get PV info from cache
            cache_info = self.pv_cache.get(pvname, {})
            
            # Try to get additional info using cainfo
            try:
                info_output = subprocess.check_output(['cainfo', pvname], encoding='utf-8', timeout=5)
                info_lines = info_output.strip().split('\n')
                info_dict = {}
                
                for line in info_lines:
                    if ':' in line:
                        key, val = line.split(':', 1)
                        info_dict[key.strip()] = val.strip()
                
                return {
                    "name": pvname,
                    "value": value,
                    "ioc": cache_info.get("ioc", "Unknown"),
                    "ip": cache_info.get("ip", "Unknown"),
                    "info": info_dict
                }
            except:
                return {
                    "name": pvname,
                    "value": value,
                    "ioc": cache_info.get("ioc", "Unknown"),
                    "ip": cache_info.get("ip", "Unknown"),
                    "info": {}
                }
                
        except Exception as e:
            return {
                "name": pvname,
                "value": f"ERROR: {str(e)}",
                "ioc": "Unknown",
                "ip": "Unknown",
                "info": {}
            }
    
    def monitor_pv(self, pvname: str, duration: int = 60) -> List[Dict]:
        """
        Monitor PV for a specified duration / 지정된 시간 동안 PV 모니터링
        
        Args:
            pvname: PV name to monitor / 모니터링할 PV 이름
            duration: Monitoring duration in seconds / 모니터링 시간 (초)
            
        Returns:
            List[Dict]: Monitoring data / 모니터링 데이터
        """
        import time
        from datetime import datetime
        
        data = []
        start_time = time.time()
        
        while time.time() - start_time < duration:
            try:
                value = self.get_pv_value(pvname)
                timestamp = datetime.now().isoformat()
                
                data.append({
                    "timestamp": timestamp,
                    "value": value
                })
                
                time.sleep(1)  # Sample every second
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[ERROR] PV monitoring failed: {e}")
                break
        
        return data 