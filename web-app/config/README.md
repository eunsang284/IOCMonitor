# EPICS IOC Monitor Configuration Guide
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
