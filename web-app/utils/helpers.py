# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Helper Functions
EPICS IOC 모니터 헬퍼 함수들
Common utility functions used throughout the application
애플리케이션 전체에서 사용되는 공통 유틸리티 함수들
"""

import time
import pandas as pd
from typing import Any, Optional

def safe_str(val: Any) -> str:
    """
    Safely convert value to string / 값을 안전하게 문자열로 변환
    
    Args:
        val: Value to convert / 변환할 값
        
    Returns:
        str: Safe string representation / 안전한 문자열 표현
    """
    try:
        if pd.isna(val):
            return ""
        return str(val).strip()
    except:
        return ""

def format_uptime(sec: int) -> str:
    """
    Format uptime in seconds to human readable format / 초 단위 업타임을 사람이 읽기 쉬운 형식으로 변환
    
    Args:
        sec: Seconds / 초
        
    Returns:
        str: Formatted uptime string / 포맷된 업타임 문자열
    """
    sec = int(sec)
    d = sec // 86400
    h = (sec % 86400) // 3600
    m = (sec % 3600) // 60
    s = sec % 60
    
    parts = []
    if d: 
        parts.append(f"{d}d")
    if h: 
        parts.append(f"{h}h")
    if len(parts) < 2 and m: 
        parts.append(f"{m}m")
    if len(parts) < 2 and s: 
        parts.append(f"{s}s")
    
    return " ".join(parts[:2])

def parse_hex_value(hex_str: str) -> Optional[int]:
    """
    Parse hexadecimal string to integer / 16진수 문자열을 정수로 파싱
    
    Args:
        hex_str: Hexadecimal string / 16진수 문자열
        
    Returns:
        Optional[int]: Parsed integer or None if failed / 파싱된 정수 또는 실패 시 None
    """
    try:
        if not hex_str or hex_str.lower() == "nan":
            return None
        return int(hex_str.replace("0x", "").replace("0X", ""), 16)
    except (ValueError, TypeError):
        return None

def validate_ioc_name(ioc_name: str) -> bool:
    """
    Validate IOC name format / IOC 이름 형식 검증
    
    Args:
        ioc_name: IOC name to validate / 검증할 IOC 이름
        
    Returns:
        bool: True if valid, False otherwise / 유효하면 True, 아니면 False
    """
    if not ioc_name or not isinstance(ioc_name, str):
        return False
    
    # Basic validation rules / 기본 검증 규칙
    if len(ioc_name) > 100:  # Too long / 너무 길음
        return False
    
    if any(char in ioc_name for char in ['<', '>', '"', "'", '&', '|', ';', '`']):
        return False  # Dangerous characters / 위험한 문자들
    
    return True

def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe file operations / 안전한 파일 작업을 위해 파일명 정리
    
    Args:
        filename: Original filename / 원본 파일명
        
    Returns:
        str: Sanitized filename / 정리된 파일명
    """
    import re
    # Remove or replace dangerous characters / 위험한 문자들 제거 또는 대체
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Limit length / 길이 제한
    if len(sanitized) > 255:
        sanitized = sanitized[:255]
    return sanitized

def get_timestamp() -> str:
    """
    Get current timestamp in standard format / 표준 형식의 현재 타임스탬프 반환
    
    Returns:
        str: Current timestamp / 현재 타임스탬프
    """
    return time.strftime("%Y-%m-%d %H:%M:%S")

def parse_datetime_safe(datetime_str: str) -> Optional[pd.Timestamp]:
    """
    Safely parse datetime string / 안전하게 날짜시간 문자열 파싱
    
    Args:
        datetime_str: Datetime string to parse / 파싱할 날짜시간 문자열
        
    Returns:
        Optional[pd.Timestamp]: Parsed timestamp or None if failed / 파싱된 타임스탬프 또는 실패 시 None
    """
    try:
        return pd.to_datetime(datetime_str, errors="coerce")
    except:
        return None

def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely / 안전하게 백분율 계산
    
    Args:
        part: Part value / 부분 값
        total: Total value / 전체 값
        
    Returns:
        float: Percentage (0-100) / 백분율 (0-100)
    """
    try:
        if total == 0:
            return 0.0
        return (part / total) * 100
    except (TypeError, ValueError, ZeroDivisionError):
        return 0.0

def truncate_string(text: str, max_length: int = 100) -> str:
    """
    Truncate string to specified length / 문자열을 지정된 길이로 자르기
    
    Args:
        text: Text to truncate / 자를 텍스트
        max_length: Maximum length / 최대 길이
        
    Returns:
        str: Truncated text / 잘린 텍스트
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length-3] + "..."

def is_valid_ip(ip: str) -> bool:
    """
    Validate IP address format / IP 주소 형식 검증
    
    Args:
        ip: IP address to validate / 검증할 IP 주소
        
    Returns:
        bool: True if valid, False otherwise / 유효하면 True, 아니면 False
    """
    import re
    pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
    if not re.match(pattern, ip):
        return False
    
    parts = ip.split('.')
    return all(0 <= int(part) <= 255 for part in parts) 