# IOC Monitor API Documentation for MCP

## 개요
이 문서는 IOC Monitor의 API를 MCP(Model Context Protocol)에서 사용하기 위한 가이드입니다.

## Base URL
```
http://192.168.70.235:5001
```

## API 목록

### 1. 시스템 상태 관련 API

#### 시스템 상태 조회
- **Endpoint:** `/api/status`
- **Method:** GET
- **Description:** 시스템 전반적인 상태 조회 (IOC Monitor, SSH Server, Cache Server 등)
- **MCP 사용법:** 시스템 모니터링 및 상태 확인
- **Response:** JSON

#### IOC 개수 조회
- **Endpoint:** `/api/ioc_count`
- **Method:** GET
- **Description:** 전체 IOC 개수 조회
- **MCP 사용법:** IOC 총 개수 파악
- **Response:** JSON

### 2. IOC 관리 관련 API

#### IOC 목록 조회
- **Endpoint:** `/api/alive/ioc_list`
- **Method:** GET
- **Description:** Alive 서버에서 IOC 목록 조회
- **MCP 사용법:** 모든 IOC 이름 목록 가져오기
- **Response:** JSON

#### IOC 상세 정보 조회
- **Endpoint:** `/api/alive/ioc_details`
- **Method:** GET
- **Description:** 모든 IOC의 상세 정보 조회
- **MCP 사용법:** IOC 상태, IP, 업타임 등 상세 정보
- **Response:** JSON

#### 특정 IOC 상세 정보
- **Endpoint:** `/api/alive/ioc/<ioc_name>`
- **Method:** GET
- **Description:** 특정 IOC의 상세 정보 조회
- **MCP 사용법:** 특정 IOC의 상태 및 정보 확인
- **Response:** JSON

#### IOC 상태 요약
- **Endpoint:** `/api/alive/status`
- **Method:** GET
- **Description:** IOC 상태 요약 정보
- **MCP 사용법:** IOC 상태 통계 및 요약
- **Response:** JSON

#### 장애 IOC 정보
- **Endpoint:** `/api/alive/faulted`
- **Method:** GET
- **Description:** 현재 장애 상태인 IOC 정보
- **MCP 사용법:** 장애 IOC 모니터링 및 알림
- **Response:** JSON

#### 모든 IOC 데이터
- **Endpoint:** `/api/data`
- **Method:** GET
- **Description:** 모든 IOC 데이터 (마스크 상태 포함)
- **MCP 사용법:** 전체 IOC 데이터 및 마스크 상태
- **Response:** JSON

#### IP 주소 목록
- **Endpoint:** `/api/ip_list`
- **Method:** GET
- **Description:** IOC IP 주소 목록
- **MCP 사용법:** IOC IP 주소 목록 조회
- **Response:** JSON

#### 장애 IOC 상세 정보
- **Endpoint:** `/api/faulted_iocs`
- **Method:** GET
- **Description:** 장애 IOC 상세 정보 (마스크 제외)
- **MCP 사용법:** 장애 IOC 상세 분석
- **Response:** JSON

### 3. EPICS PV 관련 API

#### PV 값 읽기
- **Endpoint:** `/api/pv/caget/<pvname>`
- **Method:** GET
- **Description:** PV 값 읽기 (caget 사용)
- **MCP 사용법:** EPICS PV 값 읽기
- **Response:** JSON

#### PV 값 설정
- **Endpoint:** `/api/pv/caput/<pvname>`
- **Method:** POST
- **Description:** PV 값 설정 (caput 사용)
- **MCP 사용법:** EPICS PV 값 설정
- **Response:** JSON

#### PV 검색
- **Endpoint:** `/api/pv/search`
- **Method:** GET
- **Description:** PV 검색
- **MCP 사용법:** EPICS PV 검색
- **Response:** JSON

#### PV 상세 정보
- **Endpoint:** `/api/pv/<pvname>`
- **Method:** GET
- **Description:** PV 상세 정보
- **MCP 사용법:** PV 상세 정보 조회
- **Response:** JSON

#### PV 자동완성
- **Endpoint:** `/api/pv/autocomplete`
- **Method:** GET
- **Description:** PV 자동완성 제안
- **MCP 사용법:** PV 이름 자동완성
- **Response:** JSON

### 4. 로그 및 이벤트 관련 API

#### IOC 이벤트 로그
- **Endpoint:** `/api/ioc_logs/<iocname>`
- **Method:** GET
- **Description:** 특정 IOC의 이벤트 로그
- **MCP 사용법:** IOC 이벤트 로그 분석
- **Response:** JSON

#### 모든 이벤트
- **Endpoint:** `/api/events`
- **Method:** GET
- **Description:** 모든 이벤트 캐시
- **MCP 사용법:** 전체 이벤트 데이터
- **Response:** JSON

#### 서버 로그 날짜 목록
- **Endpoint:** `/api/server_log_dates`
- **Method:** GET
- **Description:** 서버 로그 날짜 목록
- **MCP 사용법:** 로그 파일 날짜 목록
- **Response:** JSON

#### 날짜별 서버 로그
- **Endpoint:** `/server_log/<date>`
- **Method:** GET
- **Description:** 특정 날짜의 서버 로그
- **MCP 사용법:** 날짜별 서버 로그 조회
- **Response:** Text

### 5. 제어 및 모니터링 관련 API

#### IOC Monitor Ready 상태
- **Endpoint:** `/api/ioc_monitor_ready/status`
- **Method:** GET
- **Description:** IOC Monitor Ready 상태 조회
- **MCP 사용법:** IOC Monitor 제어 상태 확인
- **Response:** JSON

#### IOC Monitor Ready 설정
- **Endpoint:** `/api/ioc_monitor_ready/set`
- **Method:** POST
- **Description:** IOC Monitor Ready 값 설정
- **MCP 사용법:** IOC Monitor 제어 값 설정
- **Response:** JSON

#### 제어 상태
- **Endpoint:** `/api/control_states`
- **Method:** GET
- **Description:** 제어 상태 및 모니터링 데이터
- **MCP 사용법:** IOC 모니터링 상태 확인
- **Response:** JSON

## MCP에서의 사용 예시

### Python 예시
```python
import requests
import json

# Base URL
base_url = "http://192.168.70.235:5001"

# 시스템 상태 조회
def get_system_status():
    response = requests.get(f"{base_url}/api/status")
    return response.json()

# IOC 목록 조회
def get_ioc_list():
    response = requests.get(f"{base_url}/api/alive/ioc_list")
    return response.json()

# 특정 IOC 상태 확인
def get_ioc_status(ioc_name):
    response = requests.get(f"{base_url}/api/alive/ioc/{ioc_name}")
    return response.json()

# PV 값 읽기
def read_pv(pv_name):
    response = requests.get(f"{base_url}/api/pv/caget/{pv_name}")
    return response.json()

# PV 값 설정
def write_pv(pv_name, value):
    data = {"value": value}
    response = requests.post(f"{base_url}/api/pv/caput/{pv_name}", json=data)
    return response.json()
```

### JavaScript 예시
```javascript
// Base URL
const baseUrl = "http://192.168.70.235:5001";

// 시스템 상태 조회
async function getSystemStatus() {
    const response = await fetch(`${baseUrl}/api/status`);
    return await response.json();
}

// IOC 목록 조회
async function getIocList() {
    const response = await fetch(`${baseUrl}/api/alive/ioc_list`);
    return await response.json();
}

// 특정 IOC 상태 확인
async function getIocStatus(iocName) {
    const response = await fetch(`${baseUrl}/api/alive/ioc/${iocName}`);
    return await response.json();
}

// PV 값 읽기
async function readPv(pvName) {
    const response = await fetch(`${baseUrl}/api/pv/caget/${pvName}`);
    return await response.json();
}

// PV 값 설정
async function writePv(pvName, value) {
    const response = await fetch(`${baseUrl}/api/pv/caput/${pvName}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({value: value})
    });
    return await response.json();
}
```

### cURL 예시
```bash
# 시스템 상태 조회
curl http://192.168.70.235:5001/api/status

# IOC 목록 조회
curl http://192.168.70.235:5001/api/alive/ioc_list

# 특정 IOC 상태 확인
curl http://192.168.70.235:5001/api/alive/ioc/IOC_NAME

# PV 값 읽기
curl http://192.168.70.235:5001/api/pv/caget/PV_NAME

# PV 값 설정
curl -X POST http://192.168.70.235:5001/api/pv/caput/PV_NAME \
  -H "Content-Type: application/json" \
  -d '{"value": 123.45}'
```

## 응답 형식

### 성공 응답 예시
```json
{
    "success": true,
    "data": {...},
    "message": "요청이 성공적으로 처리되었습니다."
}
```

### 오류 응답 예시
```json
{
    "success": false,
    "error": "오류 메시지",
    "status_code": 500
}
```

## 인증

- **읽기 전용 API:** 대부분의 조회 API는 인증이 필요하지 않습니다.
- **제어 API:** 일부 제어 기능은 관리자 로그인이 필요할 수 있습니다.

## 주의사항

1. **Rate Limiting:** API 호출 빈도에 제한이 있을 수 있습니다.
2. **데이터 크기:** 대량의 데이터를 요청할 때는 페이지네이션을 고려하세요.
3. **에러 처리:** 항상 응답 상태 코드와 에러 메시지를 확인하세요.
4. **네트워크:** 네트워크 지연이나 연결 문제를 고려한 타임아웃을 설정하세요.

## 추가 정보

- **API 문서 페이지:** http://192.168.70.235:5001/api/docs
- **API 목록:** http://192.168.70.235:5001/api/list
- **웹 대시보드:** http://192.168.70.235:5001/

## 지원

API 사용에 문제가 있거나 추가 기능이 필요한 경우, 시스템 관리자에게 문의하세요.
