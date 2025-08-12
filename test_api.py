#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IOC Monitor API Test Script
API가 정상적으로 작동하는지 테스트하는 스크립트
"""

import requests
import json
import sys
from datetime import datetime


def test_api_endpoint(base_url: str, endpoint: str, method: str = "GET", data: dict = None) -> bool:
    """API 엔드포인트 테스트"""
    url = f"{base_url}{endpoint}"
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=10)
        else:
            print(f"❌ 지원하지 않는 HTTP 메소드: {method}")
            return False
        
        if response.status_code == 200:
            print(f"✅ {method} {endpoint} - 성공")
            try:
                result = response.json()
                if isinstance(result, dict) and len(result) > 0:
                    print(f"   응답 데이터: {len(result)} 개의 키")
                else:
                    print(f"   응답: {result}")
            except:
                print(f"   응답: {response.text[:100]}...")
            return True
        else:
            print(f"❌ {method} {endpoint} - 실패 (HTTP {response.status_code})")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ {method} {endpoint} - 연결 실패: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ {method} {endpoint} - 오류: {str(e)}")
        return False


def main():
    """메인 테스트 함수"""
    base_url = "http://192.168.70.235:5001"
    
    print("=== IOC Monitor API 테스트 ===\n")
    print(f"Base URL: {base_url}")
    print(f"테스트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 테스트할 API 엔드포인트들
    test_endpoints = [
        # 시스템 상태 관련
        ("/api/status", "GET"),
        ("/api/ioc_count", "GET"),
        
        # IOC 관리 관련
        ("/api/alive/ioc_list", "GET"),
        ("/api/alive/ioc_details", "GET"),
        ("/api/alive/status", "GET"),
        ("/api/alive/faulted", "GET"),
        ("/api/data", "GET"),
        ("/api/ip_list", "GET"),
        ("/api/faulted_iocs", "GET"),
        
        # 제어 및 모니터링 관련
        ("/api/control_states", "GET"),
        ("/api/ioc_monitor_ready/status", "GET"),
        
        # 로그 및 이벤트 관련
        ("/api/events", "GET"),
        ("/api/server_log_dates", "GET"),
        
        # EPICS PV 관련 (기본적인 것들)
        ("/api/pv/search", "GET"),
        
        # API 문서 관련
        ("/api/list", "GET"),
    ]
    
    success_count = 0
    total_count = len(test_endpoints)
    
    print("1. 기본 API 엔드포인트 테스트:")
    print("-" * 50)
    
    for endpoint, method in test_endpoints:
        if test_api_endpoint(base_url, endpoint, method):
            success_count += 1
        print()
    
    print("2. 테스트 결과 요약:")
    print("-" * 50)
    print(f"성공: {success_count}/{total_count}")
    print(f"실패: {total_count - success_count}/{total_count}")
    print(f"성공률: {(success_count/total_count)*100:.1f}%")
    
    if success_count == total_count:
        print("\n🎉 모든 API 테스트가 성공했습니다!")
        return 0
    else:
        print(f"\n⚠️  {total_count - success_count}개의 API 테스트가 실패했습니다.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
