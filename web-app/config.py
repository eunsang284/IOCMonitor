# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Configuration
EPICS IOC 모니터 설정
Configuration settings for the Flask application
Flask 애플리케이션을 위한 설정
"""

import os
from datetime import timedelta

class Config:
    """Base configuration / 기본 설정"""
    
    # Flask settings / Flask 설정
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", 5000))
    
    # Admin credentials / 관리자 인증 정보
    ADMIN_CREDENTIALS = {
        "admin": "admin123",  # Change this in production / 프로덕션에서 변경하세요
        "operator": "op123"
    }
    
    # File paths / 파일 경로
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    LOG_DIR = os.path.join(BASE_DIR, "logs")
    CACHE_DIR = os.path.join(BASE_DIR, "cache")
    
    # Alive server paths / Alive 서버 경로
    ALIVED_EXEC = os.path.join(BASE_DIR, "build", "alive-server", "alived")
    ALIVECTL_EXEC = os.path.join(BASE_DIR, "build", "alive-server", "alivectl")
    ALIVED_CONFIG = os.path.join(BASE_DIR, "config", "alived_config.txt")
    
    # Data file paths / 데이터 파일 경로
    CSV_MAIN = os.path.join(BASE_DIR, "src", "SAVE.csv")
    CSV_ENV = os.path.join(BASE_DIR, "src", "SAVE_envvars.csv")
    CSV_LINUX = os.path.join(BASE_DIR, "src", "SAVE_linux.csv")
    CACHE_FILE = os.path.join(BASE_DIR, "src", "ioc_cache.txt")
    
    # Log file paths / 로그 파일 경로
    FAULTED_LOG = os.path.join(LOG_DIR, "faulted_ioc.log")
    ALIVE_EVENTS_LOG = os.path.join(BASE_DIR, "logs", "events.txt")
    
    # EPICS PVs - Configurable from environment / EPICS PV들 - 환경에서 설정 가능
    # Default monitoring PVs / 기본 모니터링 PV들 (비활성화됨)
    DEFAULT_MONITORING_PVS = {
        # 실제 환경에 맞는 PV로 설정하세요 / Configure with actual PVs for your environment
        # "System_Status": "SYSTEM:STATUS",
        # "Machine_Mode": "MACHINE:MODE",
        # "Beam_Status": "BEAM:STATUS",
        # "IOC_Ready": "IOC:READY"
    }
    
    # Default control PVs (PVs that will be set based on monitoring PV changes) / 기본 제어 PV들 (모니터링 PV 변화에 따라 설정될 PV들) (비활성화됨)
    DEFAULT_CONTROL_PVS = {
        # 실제 환경에 맞는 PV로 설정하세요 / Configure with actual PVs for your environment
        # "IOC_Ready": {
        #     "pv_address": "IOC:READY",
        #     "enabled": True,
        #     "conditions": {
        #         "faulted_ioc_count": {
        #             "operator": "==",
        #             "value": 0,
        #             "set_value": "1"
        #         }
        #     }
        # }
    }
    
    # Get monitoring PVs from environment or use defaults / 환경에서 모니터링 PV 가져오기 또는 기본값 사용
    def get_monitoring_pvs(self):
        """Get monitoring PVs from environment / 환경에서 모니터링 PV 가져오기"""
        pvs = {}
        
        # Try to get PVs from environment variables / 환경 변수에서 PV 가져오기 시도
        for i in range(1, 11):  # Support up to 10 PVs / 최대 10개 PV 지원
            pv_name = os.environ.get(f"MONITORING_PV_{i}_NAME")
            pv_address = os.environ.get(f"MONITORING_PV_{i}_ADDRESS")
            
            if pv_name and pv_address:
                pvs[pv_name] = pv_address
        
        # If no PVs defined in environment, use defaults / 환경에 PV가 정의되지 않으면 기본값 사용
        if not pvs:
            pvs = self.DEFAULT_MONITORING_PVS.copy()
        
        return pvs
    
    def get_control_pvs(self):
        """Get control PVs from environment / 환경에서 제어 PV 가져오기"""
        control_pvs = {}
        
        # Try to get control PVs from environment variables / 환경 변수에서 제어 PV 가져오기 시도
        for i in range(1, 6):  # Support up to 5 control PVs / 최대 5개 제어 PV 지원
            pv_name = os.environ.get(f"CONTROL_PV_{i}_NAME")
            pv_address = os.environ.get(f"CONTROL_PV_{i}_ADDRESS")
            enabled = os.environ.get(f"CONTROL_PV_{i}_ENABLED", "false").lower() == "true"
            
            if pv_name and pv_address:
                control_pvs[pv_name] = {
                    "pv_address": pv_address,
                    "enabled": enabled,
                    "conditions": {}
                }
                
                # Get conditions for this control PV / 이 제어 PV의 조건들 가져오기
                for j in range(1, 6):  # Support up to 5 conditions per PV / PV당 최대 5개 조건 지원
                    condition_type = os.environ.get(f"CONTROL_PV_{i}_CONDITION_{j}_TYPE")
                    condition_operator = os.environ.get(f"CONTROL_PV_{i}_CONDITION_{j}_OPERATOR")
                    condition_value = os.environ.get(f"CONTROL_PV_{i}_CONDITION_{j}_VALUE")
                    set_value = os.environ.get(f"CONTROL_PV_{i}_CONDITION_{j}_SET_VALUE")
                    
                    if condition_type and condition_operator and condition_value and set_value:
                        control_pvs[pv_name]["conditions"][condition_type] = {
                            "operator": condition_operator,
                            "value": condition_value,
                            "set_value": set_value
                        }
        
        # If no control PVs defined in environment, use defaults / 환경에 제어 PV가 정의되지 않으면 기본값 사용
        if not control_pvs:
            control_pvs = self.DEFAULT_CONTROL_PVS.copy()
        
        return control_pvs
    
    @property
    def EPICS_PVS(self):
        """Get EPICS PVs for monitoring / 모니터링용 EPICS PV 가져오기"""
        return self.get_monitoring_pvs()
    
    @property
    def CONTROL_PVS(self):
        """Get EPICS PVs for control / 제어용 EPICS PV 가져오기"""
        return self.get_control_pvs()
    
    # Feature flags - Enable/disable features / 기능 플래그 - 기능 활성화/비활성화
    FEATURE_ALIVE_SERVER = os.environ.get("FEATURE_ALIVE_SERVER", "true").lower() == "true"
    FEATURE_CSV_LOADING = os.environ.get("FEATURE_CSV_LOADING", "false").lower() == "true"
    FEATURE_PV_MONITORING = os.environ.get("FEATURE_PV_MONITORING", "true").lower() == "true"
    FEATURE_CONTROL_PVS = os.environ.get("FEATURE_CONTROL_PVS", "true").lower() == "true"
    FEATURE_FAULTED_MONITORING = os.environ.get("FEATURE_FAULTED_MONITORING", "true").lower() == "true"
    FEATURE_PV_CACHE = os.environ.get("FEATURE_PV_CACHE", "false").lower() == "true"
    
    # Monitoring settings / 모니터링 설정
    CACHE_UPDATE_INTERVAL = int(os.environ.get("CACHE_UPDATE_INTERVAL", "5"))  # seconds
    IOC_READY_UPDATE_INTERVAL = int(os.environ.get("IOC_READY_UPDATE_INTERVAL", "1"))  # seconds
    FAULTED_MONITOR_INTERVAL = int(os.environ.get("FAULTED_MONITOR_INTERVAL", "5"))  # seconds
    PV_CACHE_UPDATE_INTERVAL = int(os.environ.get("PV_CACHE_UPDATE_INTERVAL", "30"))  # seconds
    
    # CORS settings / CORS 설정
    CORS_ORIGINS = [
        "http://192.168.60.150",
        "http://192.168.60.61:3000",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ]
    
    # Session settings / 세션 설정
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    
    # Logging settings / 로깅 설정
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Performance settings / 성능 설정
    MAX_WORKERS = int(os.environ.get("MAX_WORKERS", "4"))
    REQUEST_TIMEOUT = int(os.environ.get("REQUEST_TIMEOUT", "30"))  # seconds
    
    # Security settings / 보안 설정
    SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

class DevelopmentConfig(Config):
    """Development configuration / 개발 환경 설정"""
    DEBUG = True
    LOG_LEVEL = "DEBUG"

class ProductionConfig(Config):
    """Production configuration / 프로덕션 환경 설정"""
    DEBUG = False
    LOG_LEVEL = "WARNING"
    SESSION_COOKIE_SECURE = True  # Requires HTTPS

class TestingConfig(Config):
    """Testing configuration / 테스트 환경 설정"""
    TESTING = True
    DEBUG = True
    WTF_CSRF_ENABLED = False

# Configuration mapping / 설정 매핑
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
} 