# -*- coding: utf-8 -*-
"""
EPICS PV Service
EPICS PV 서비스
PV management and caching functionality
PV 관리 및 캐싱 기능
"""

import time
import subprocess
from typing import Dict, List

class PVService:
    """EPICS PV service / EPICS PV 서비스"""
    
    def __init__(self):
        """Initialize PV service / PV 서비스 초기화"""
        self.pv_cache = {}  # Global cache: PV name → info
        
        # Load configuration
        from config import Config
        self.config = Config()
    
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