#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Configuration Generator
EPICS IOC 모니터 설정 생성기
Generates configuration files for the IOC Monitor
IOC 모니터를 위한 설정 파일들을 생성합니다
"""

import os
import sys
import json
from pathlib import Path

def create_monitoring_config():
    """Create monitoring configuration file / 모니터링 설정 파일 생성"""
    
    config = {
        "monitoring_pvs": {
            "System_Status": {
                "address": "SYSTEM:STATUS",
                "description": "System status PV",
                "enabled": True
            },
            "Machine_Mode": {
                "address": "MACHINE:MODE", 
                "description": "Machine mode PV",
                "enabled": True
            },
            "Beam_Status": {
                "address": "BEAM:STATUS",
                "description": "Beam status PV", 
                "enabled": True
            },
            "IOC_Ready": {
                "address": "IOC:READY",
                "description": "IOC ready status PV",
                "enabled": True
            }
        },
        "control_pvs": {
            "IOC_Ready": {
                "address": "IOC:READY",
                "description": "IOC ready control PV",
                "enabled": True,
                "conditions": {
                    "faulted_ioc_count": {
                        "operator": "==",
                        "value": 0,
                        "set_value": "1",
                        "description": "Set IOC_Ready to 1 when no faulted IOCs"
                    }
                }
            },
            "System_Alert": {
                "address": "SYSTEM:ALERT",
                "description": "System alert control PV", 
                "enabled": False,
                "conditions": {
                    "faulted_ioc_count": {
                        "operator": ">",
                        "value": 5,
                        "set_value": "1",
                        "description": "Set alert when more than 5 IOCs are faulted"
                    }
                }
            }
        },
        "intervals": {
            "cache_update": 5,
            "control_update": 1,
            "faulted_monitor": 5,
            "pv_cache_update": 30
        },
        "features": {
            "control_pv_enabled": True,
            "faulted_monitoring_enabled": True,
            "pv_cache_enabled": True,
            "logging_enabled": True
        }
    }
    
    config_file = Path("web-app/config/monitoring_config.json")
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print(f"Monitoring configuration created: {config_file}")
    return config

def create_env_template():
    """Create .env template file / .env 템플릿 파일 생성"""
    
    env_template = """# EPICS IOC Monitor Web Application Environment
# EPICS IOC 모니터 웹 애플리케이션 환경

# Flask settings / Flask 설정
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security / 보안
SECRET_KEY=your-secret-key-here

# Logging / 로깅
LOG_LEVEL=INFO

# EPICS environment / EPICS 환경
EPICS_BASE=/opt/epics
EPICS_HOST_ARCH=linux-x86_64

# Monitoring PVs - Configure your monitoring PVs here / 모니터링 PV들 - 여기서 모니터링할 PV들을 설정하세요
# Format: MONITORING_PV_<number>_NAME="Display Name"
# Format: MONITORING_PV_<number>_ADDRESS="PV:ADDRESS"
# Example / 예시:
MONITORING_PV_1_NAME="System Status"
MONITORING_PV_1_ADDRESS="SYSTEM:STATUS"
MONITORING_PV_2_NAME="Machine Mode"
MONITORING_PV_2_ADDRESS="MACHINE:MODE"
MONITORING_PV_3_NAME="Beam Status"
MONITORING_PV_3_ADDRESS="BEAM:STATUS"
MONITORING_PV_4_NAME="IOC Ready"
MONITORING_PV_4_ADDRESS="IOC:READY"

# Control PVs - PVs that will be set based on monitoring PV changes / 제어 PV들 - 모니터링 PV 변화에 따라 설정될 PV들
# Format: CONTROL_PV_<number>_NAME="Display Name"
# Format: CONTROL_PV_<number>_ADDRESS="PV:ADDRESS"
# Format: CONTROL_PV_<number>_ENABLED=true/false
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_TYPE="condition_type"
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_OPERATOR="==" or "!=" or ">" or "<" or ">=" or "<="
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_VALUE="condition_value"
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_SET_VALUE="value_to_set"
# Example / 예시:
CONTROL_PV_1_NAME="IOC Ready"
CONTROL_PV_1_ADDRESS="IOC:READY"
CONTROL_PV_1_ENABLED=true
CONTROL_PV_1_CONDITION_1_TYPE="faulted_ioc_count"
CONTROL_PV_1_CONDITION_1_OPERATOR="=="
CONTROL_PV_1_CONDITION_1_VALUE="0"
CONTROL_PV_1_CONDITION_1_SET_VALUE="1"

# Monitoring intervals (seconds) / 모니터링 간격 (초)
CACHE_UPDATE_INTERVAL=5
IOC_READY_UPDATE_INTERVAL=1
FAULTED_MONITOR_INTERVAL=5
PV_CACHE_UPDATE_INTERVAL=30

# Performance settings / 성능 설정
MAX_WORKERS=4
REQUEST_TIMEOUT=30
"""
    
    env_file = Path("web-app/.env.template")
    env_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(env_template)
    
    print(f"Environment template created: {env_file}")
    return env_file

def create_readme():
    """Create configuration README / 설정 README 생성"""
    
    readme_content = """# EPICS IOC Monitor Configuration Guide
# EPICS IOC 모니터 설정 가이드

## 개요 / Overview

이 문서는 EPICS IOC Monitor의 설정 방법을 설명합니다.

## 설정 파일 / Configuration Files

### 1. .env 파일

웹 애플리케이션의 환경 변수를 설정합니다.

#### 모니터링 PV 설정 / Monitoring PV Configuration

```bash
# 모니터링할 PV들을 설정하세요
MONITORING_PV_1_NAME="System Status"
MONITORING_PV_1_ADDRESS="SYSTEM:STATUS"
MONITORING_PV_2_NAME="Machine Mode"
MONITORING_PV_2_ADDRESS="MACHINE:MODE"
```

#### 제어 PV 설정 / Control PV Configuration

```bash
# 모니터링 조건에 따라 자동으로 설정될 PV들을 설정하세요
CONTROL_PV_1_NAME="IOC Ready"
CONTROL_PV_1_ADDRESS="IOC:READY"
CONTROL_PV_1_ENABLED=true
CONTROL_PV_1_CONDITION_1_TYPE="faulted_ioc_count"
CONTROL_PV_1_CONDITION_1_OPERATOR="=="
CONTROL_PV_1_CONDITION_1_VALUE="0"
CONTROL_PV_1_CONDITION_1_SET_VALUE="1"
```

### 2. monitoring_config.json

JSON 형식의 모니터링 설정 파일입니다.

## 조건 타입 / Condition Types

### faulted_ioc_count
- 장애 IOC 개수
- 정수 값으로 비교

### monitoring_pv_name
- 모니터링 PV의 이름
- 해당 PV의 현재 값과 비교

## 연산자 / Operators

- `==`: 같음
- `!=`: 다름  
- `>`: 큼
- `<`: 작음
- `>=`: 크거나 같음
- `<=`: 작거나 같음

## 예제 / Examples

### 예제 1: 장애 IOC가 없을 때 IOC Ready를 1로 설정

```bash
CONTROL_PV_1_NAME="IOC Ready"
CONTROL_PV_1_ADDRESS="IOC:READY"
CONTROL_PV_1_ENABLED=true
CONTROL_PV_1_CONDITION_1_TYPE="faulted_ioc_count"
CONTROL_PV_1_CONDITION_1_OPERATOR="=="
CONTROL_PV_1_CONDITION_1_VALUE="0"
CONTROL_PV_1_CONDITION_1_SET_VALUE="1"
```

### 예제 2: Machine Mode가 2일 때 System Alert를 1로 설정

```bash
CONTROL_PV_2_NAME="System Alert"
CONTROL_PV_2_ADDRESS="SYSTEM:ALERT"
CONTROL_PV_2_ENABLED=true
CONTROL_PV_2_CONDITION_1_TYPE="Machine_Mode"
CONTROL_PV_2_CONDITION_1_OPERATOR="=="
CONTROL_PV_2_CONDITION_1_VALUE="2"
CONTROL_PV_2_CONDITION_1_SET_VALUE="1"
```

## 설정 적용 / Applying Configuration

1. .env 파일을 편집하여 원하는 PV들을 설정
2. 웹 애플리케이션 재시작
3. API를 통해 설정 확인: `GET /api/control_states`

## 문제 해결 / Troubleshooting

### PV 연결 실패
- PV 주소가 올바른지 확인
- EPICS 환경이 설정되었는지 확인
- 네트워크 연결 확인

### 제어 PV 설정 실패
- PV에 쓰기 권한이 있는지 확인
- 조건 설정이 올바른지 확인
- 로그 파일에서 오류 메시지 확인
"""
    
    readme_file = Path("web-app/config/README.md")
    readme_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(readme_file, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"Configuration README created: {readme_file}")
    return readme_file

def main():
    """Main function / 메인 함수"""
    print("EPICS IOC Monitor Configuration Generator")
    print("EPICS IOC 모니터 설정 생성기")
    print("=" * 50)
    
    try:
        # Create monitoring configuration / 모니터링 설정 생성
        config = create_monitoring_config()
        
        # Create .env template / .env 템플릿 생성
        env_file = create_env_template()
        
        # Create README / README 생성
        readme_file = create_readme()
        
        print("\n" + "=" * 50)
        print("Configuration files created successfully!")
        print("설정 파일들이 성공적으로 생성되었습니다!")
        print("\nNext steps / 다음 단계:")
        print("1. Edit web-app/.env.template and save as web-app/.env")
        print("   web-app/.env.template을 편집하여 web-app/.env로 저장하세요")
        print("2. Configure your monitoring and control PVs")
        print("   모니터링 및 제어 PV들을 설정하세요")
        print("3. Run the deployment script")
        print("   배포 스크립트를 실행하세요")
        
    except Exception as e:
        print(f"Error creating configuration files: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 