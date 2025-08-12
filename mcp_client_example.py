#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IOC Monitor MCP Client Example
MCP에서 IOC Monitor API를 사용하기 위한 Python 클라이언트 예시
"""

import requests
import json
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class IOCInfo:
    """IOC 정보를 담는 데이터 클래스"""
    name: str
    status: str
    ip_address: str
    uptime: str
    last_seen: str
    masked: bool = False


class IOCMonitorClient:
    """IOC Monitor API 클라이언트"""
    
    def __init__(self, base_url: str = "http://192.168.70.235:5001", timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = requests.Session()
        
    def _make_request(self, method: str, endpoint: str, **kwargs) -> Dict[str, Any]:
        """HTTP 요청을 수행하고 응답을 반환"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = self.session.request(
                method, 
                url, 
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}", "success": False}
        except json.JSONDecodeError:
            return {"error": "Invalid JSON response", "success": False}
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 조회"""
        return self._make_request("GET", "/api/status")
    
    def get_ioc_count(self) -> Dict[str, Any]:
        """IOC 개수 조회"""
        return self._make_request("GET", "/api/ioc_count")
    
    def get_ioc_list(self) -> Dict[str, Any]:
        """IOC 목록 조회"""
        return self._make_request("GET", "/api/alive/ioc_list")
    
    def get_ioc_details(self) -> Dict[str, Any]:
        """모든 IOC 상세 정보 조회"""
        return self._make_request("GET", "/api/alive/ioc_details")
    
    def get_ioc_detail(self, ioc_name: str) -> Dict[str, Any]:
        """특정 IOC 상세 정보 조회"""
        return self._make_request("GET", f"/api/alive/ioc/{ioc_name}")
    
    def get_ioc_status_summary(self) -> Dict[str, Any]:
        """IOC 상태 요약 정보"""
        return self._make_request("GET", "/api/alive/status")
    
    def get_faulted_iocs(self) -> Dict[str, Any]:
        """장애 IOC 정보"""
        return self._make_request("GET", "/api/alive/faulted")
    
    def get_all_ioc_data(self) -> Dict[str, Any]:
        """모든 IOC 데이터 (마스크 상태 포함)"""
        return self._make_request("GET", "/api/data")
    
    def get_ip_list(self) -> Dict[str, Any]:
        """IOC IP 주소 목록"""
        return self._make_request("GET", "/api/ip_list")
    
    def get_faulted_iocs_detailed(self) -> Dict[str, Any]:
        """장애 IOC 상세 정보 (마스크 제외)"""
        return self._make_request("GET", "/api/faulted_iocs")
    
    def get_control_states(self) -> Dict[str, Any]:
        """제어 상태 및 모니터링 데이터"""
        return self._make_request("GET", "/api/control_states")
    
    def get_ioc_logs(self, ioc_name: str) -> Dict[str, Any]:
        """특정 IOC의 이벤트 로그"""
        return self._make_request("GET", f"/api/ioc_logs/{ioc_name}")
    
    def get_all_events(self) -> Dict[str, Any]:
        """모든 이벤트 캐시"""
        return self._make_request("GET", "/api/events")
    
    def read_pv(self, pv_name: str) -> Dict[str, Any]:
        """PV 값 읽기"""
        return self._make_request("GET", f"/api/pv/caget/{pv_name}")
    
    def write_pv(self, pv_name: str, value: Any) -> Dict[str, Any]:
        """PV 값 설정"""
        data = {"value": value}
        return self._make_request("POST", f"/api/pv/caput/{pv_name}", json=data)
    
    def search_pv(self, query: str) -> Dict[str, Any]:
        """PV 검색"""
        params = {"query": query}
        return self._make_request("GET", "/api/pv/search", params=params)
    
    def get_pv_detail(self, pv_name: str) -> Dict[str, Any]:
        """PV 상세 정보"""
        return self._make_request("GET", f"/api/pv/{pv_name}")
    
    def get_pv_autocomplete(self, query: str) -> Dict[str, Any]:
        """PV 자동완성 제안"""
        params = {"q": query}
        return self._make_request("GET", "/api/pv/autocomplete", params=params)
    
    def get_server_log_dates(self) -> Dict[str, Any]:
        """서버 로그 날짜 목록"""
        return self._make_request("GET", "/api/server_log_dates")
    
    def get_server_log_by_date(self, date: str) -> str:
        """특정 날짜의 서버 로그"""
        url = f"{self.base_url}/server_log/{date}"
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            return f"Failed to get server log: {str(e)}"
    
    def get_ioc_monitor_ready_status(self) -> Dict[str, Any]:
        """IOC Monitor Ready 상태 조회"""
        return self._make_request("GET", "/api/ioc_monitor_ready/status")
    
    def set_ioc_monitor_ready(self, value: float = 1.0) -> Dict[str, Any]:
        """IOC Monitor Ready 값 설정"""
        data = {"value": value}
        return self._make_request("POST", "/api/ioc_monitor_ready/set", json=data)
    
    def get_api_list(self) -> Dict[str, Any]:
        """사용 가능한 모든 API 목록"""
        return self._make_request("GET", "/api/list")


class IOCMonitorMCP:
    """MCP에서 사용할 수 있는 IOC Monitor 래퍼 클래스"""
    
    def __init__(self, client: IOCMonitorClient):
        self.client = client
    
    def get_system_overview(self) -> Dict[str, Any]:
        """시스템 전체 개요 정보"""
        try:
            status = self.client.get_system_status()
            ioc_count = self.client.get_ioc_count()
            faulted = self.client.get_faulted_iocs()
            
            return {
                "system_status": status,
                "ioc_count": ioc_count,
                "faulted_iocs": faulted,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get system overview: {str(e)}"}
    
    def monitor_ioc_status(self, ioc_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """IOC 상태 모니터링"""
        try:
            if ioc_names:
                # 특정 IOC들만 모니터링
                results = {}
                for name in ioc_names:
                    results[name] = self.client.get_ioc_detail(name)
                return results
            else:
                # 모든 IOC 모니터링
                return self.client.get_ioc_details()
        except Exception as e:
            return {"error": f"Failed to monitor IOC status: {str(e)}"}
    
    def get_faulted_iocs_summary(self) -> Dict[str, Any]:
        """장애 IOC 요약 정보"""
        try:
            faulted = self.client.get_faulted_iocs()
            detailed = self.client.get_faulted_iocs_detailed()
            
            return {
                "faulted_summary": faulted,
                "faulted_detailed": detailed,
                "total_faulted": len(detailed.get("data", [])),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {"error": f"Failed to get faulted IOCs summary: {str(e)}"}
    
    def read_multiple_pvs(self, pv_names: List[str]) -> Dict[str, Any]:
        """여러 PV 값 동시 읽기"""
        try:
            results = {}
            for pv_name in pv_names:
                results[pv_name] = self.client.read_pv(pv_name)
            return results
        except Exception as e:
            return {"error": f"Failed to read multiple PVs: {str(e)}"}
    
    def write_multiple_pvs(self, pv_values: Dict[str, Any]) -> Dict[str, Any]:
        """여러 PV 값 동시 설정"""
        try:
            results = {}
            for pv_name, value in pv_values.items():
                results[pv_name] = self.client.write_pv(pv_name, value)
            return results
        except Exception as e:
            return {"error": f"Failed to write multiple PVs: {str(e)}"}
    
    def get_ioc_logs_summary(self, ioc_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """IOC 로그 요약 정보"""
        try:
            if ioc_names:
                results = {}
                for name in ioc_names:
                    results[name] = self.client.get_ioc_logs(name)
                return results
            else:
                # 모든 이벤트 가져오기
                return self.client.get_all_events()
        except Exception as e:
            return {"error": f"Failed to get IOC logs summary: {str(e)}"}


def main():
    """사용 예시"""
    # 클라이언트 생성
    client = IOCMonitorClient()
    mcp = IOCMonitorMCP(client)
    
    print("=== IOC Monitor MCP Client Example ===\n")
    
    # 1. 시스템 상태 확인
    print("1. 시스템 상태 확인:")
    status = mcp.get_system_overview()
    print(json.dumps(status, indent=2, ensure_ascii=False))
    print()
    
    # 2. IOC 개수 확인
    print("2. IOC 개수 확인:")
    ioc_count = client.get_ioc_count()
    print(json.dumps(ioc_count, indent=2, ensure_ascii=False))
    print()
    
    # 3. 장애 IOC 확인
    print("3. 장애 IOC 확인:")
    faulted = mcp.get_faulted_iocs_summary()
    print(json.dumps(faulted, indent=2, ensure_ascii=False))
    print()
    
    # 4. 사용 가능한 API 목록
    print("4. 사용 가능한 API 목록:")
    api_list = client.get_api_list()
    print(f"총 {api_list.get('total_apis', 0)}개의 API가 사용 가능합니다.")
    print(f"Base URL: {api_list.get('base_url', 'N/A')}")
    print()


if __name__ == "__main__":
    main()
