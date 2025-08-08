# EPICS IOC Monitor API Documentation
# EPICS IOC 모니터 API 문서

## Overview / 개요

The EPICS IOC Monitor provides a RESTful API for monitoring and managing EPICS IOCs.
EPICS IOC 모니터는 EPICS IOC를 모니터링하고 관리하기 위한 RESTful API를 제공합니다.

## Base URL / 기본 URL

```
http://localhost:5000/api
```

## Authentication / 인증

Most endpoints are public, but some require admin authentication.
대부분의 엔드포인트는 공개이지만, 일부는 관리자 인증이 필요합니다.

### Admin Authentication / 관리자 인증

For protected endpoints, use session-based authentication:
보호된 엔드포인트의 경우 세션 기반 인증을 사용하세요:

1. Login: `POST /admin/login`
2. Use session cookie for subsequent requests
3. Logout: `GET /admin/logout`

## API Endpoints / API 엔드포인트

### System Status / 시스템 상태

#### GET /api/status
Get system component status / 시스템 컴포넌트 상태 조회

**Response:**
```json
{
  "IOC Monitor Control IOC": "🟢 RUNNING",
  "SSH Server": "🟢 RUNNING", 
  "IOC Info Cache Server": "🟢 RUNNING",
  "IOC Monitor Web Server": "🟢 RUNNING",
  "Alive Server": "🟢 RUNNING"
}
```

### IOC Data / IOC 데이터

#### GET /api/data
Get all IOC data / 모든 IOC 데이터 조회

**Response:**
```json
[
  {
    "ioc": "TEST-SYS:MCP-EXP001",
    "ipaddress": "192.168.70.235",
    "status": "up",
    "boottime": "2025-08-06 22:09:27",
    "incarnation": "2025-08-06 22:09:27",
    "STATUS_TIME": {
      "text": "↑ 2h 30m",
      "seconds": 9000,
      "isDown": false
    },
    "MEM_USED": "512MB",
    "MEM_MAX": "1GB", 
    "MEM_PER": "50%",
    "SYS_CPU_LOAD": "25%",
    "NETWORK_USED": "1024",
    "masked": false
  }
]
```

#### GET /api/ioc_count
Get total IOC count / 총 IOC 개수 조회

**Response:**
```json
{
  "ioc_count": 150
}
```

#### GET /api/ip_list
Get list of IOC IP addresses / IOC IP 주소 목록 조회

**Response:**
```json
[
  "192.168.70.235",
  "192.168.70.236",
  "192.168.70.237"
]
```

### Faulted IOCs / 장애 IOC

#### GET /api/faulted_iocs
Get faulted IOCs / 장애 IOC 조회

**Response:**
```json
{
  "count": 3,
  "data": [
    {
      "ioc": "TEST-SYS:FAULTED-IOC",
      "ipaddress": "192.168.70.240",
      "status": "down",
      "STATUS_TIME": {
        "text": "↓ 1h 15m",
        "seconds": 4500,
        "isDown": true
      },
      "BPC": "0x01",
      "MSG": "10001"
    }
  ]
}
```

### Control System States / 제어 시스템 상태

#### GET /api/control_states
Get EPICS control system states / EPICS 제어 시스템 상태 조회

**Response:**
```json
{
  "Source Mode": "1",
  "Machine Mode": "2", 
  "Beam Mode": "3",
  "BPS Source Mode": "1",
  "BPS Machine Mode": "2",
  "BPS Beam Mode": "3",
  "IOC Monitor Machine Mode": "0x01",
  "IOC Monitor Status": "1"
}
```

### IOC Logs / IOC 로그

#### GET /api/ioc_logs/{iocname}
Get IOC event logs / IOC 이벤트 로그 조회

**Parameters:**
- `iocname`: IOC name / IOC 이름

**Response:**
```json
{
  "logs": [
    {
      "time": "2025-08-06 22:09:27",
      "event": "BOOT",
      "ip": "192.168.70.235", 
      "code": "0"
    },
    {
      "time": "2025-08-06 22:10:15",
      "event": "MESSAGE",
      "ip": "192.168.70.235",
      "code": "10001"
    }
  ]
}
```

### PV Management / PV 관리

#### GET /api/pv/search?query={query}
Search PVs / PV 검색

**Parameters:**
- `query`: Search query / 검색 쿼리

**Response:**
```json
{
  "TEST-SYS:PV1": {
    "ioc": "TEST-SYS:MCP-EXP001",
    "ip": "192.168.70.235"
  },
  "TEST-SYS:PV2": {
    "ioc": "TEST-SYS:MCP-EXP001", 
    "ip": "192.168.70.235"
  }
}
```

#### GET /api/pv/{pvname}
Get PV details / PV 상세 정보 조회

**Response:**
```json
{
  "ioc": "TEST-SYS:MCP-EXP001",
  "ip": "192.168.70.235"
}
```

#### GET /api/pv/autocomplete?q={query}
Get PV autocomplete suggestions / PV 자동완성 제안 조회

**Response:**
```json
[
  "TEST-SYS:PV1",
  "TEST-SYS:PV2",
  "TEST-SYS:PV3"
]
```

### Admin Operations (Authentication Required) / 관리자 작업 (인증 필요)

#### DELETE /api/delete?ioc={iocname}
Delete IOC from alive server / alive 서버에서 IOC 삭제

**Parameters:**
- `ioc`: IOC name to delete / 삭제할 IOC 이름

**Response:**
```json
{
  "status": "ok",
  "output": "IOC deleted successfully"
}
```

#### POST /api/toggle_mask
Toggle IOC mask status / IOC 마스크 상태 토글

**Request Body:**
```json
{
  "ioc": "TEST-SYS:MCP-EXP001"
}
```

**Response:**
```json
{
  "status": "ok",
  "action": "masked"
}
```

#### POST /api/unmask_all
Unmask all IOCs / 모든 IOC 마스크 해제

**Response:**
```json
{
  "status": "ok"
}
```

## Error Responses / 오류 응답

### 400 Bad Request / 잘못된 요청
```json
{
  "error": "Missing required parameter: ioc"
}
```

### 403 Forbidden / 접근 금지
```json
{
  "error": "Permission denied"
}
```

### 404 Not Found / 찾을 수 없음
```json
{
  "error": "IOC not found: TEST-SYS:INVALID-IOC"
}
```

### 500 Internal Server Error / 내부 서버 오류
```json
{
  "error": "Database connection failed"
}
```

## Rate Limiting / 속도 제한

- Public endpoints: 100 requests per minute / 공개 엔드포인트: 분당 100 요청
- Admin endpoints: 10 requests per minute / 관리자 엔드포인트: 분당 10 요청

## CORS / CORS

The API supports CORS for the following origins:
API는 다음 출처에 대해 CORS를 지원합니다:

- `http://192.168.60.150`
- `http://192.168.60.61:3000`
- `http://localhost:3000`
- `http://127.0.0.1:3000`

## Data Sources / 데이터 소스

### IOC Status Data / IOC 상태 데이터
- Source: EPICS Alive Server (alivectl) / 출처: EPICS Alive 서버 (alivectl)
- Format: CSV files (SAVE.csv, SAVE_envvars.csv, SAVE_linux.csv) / 형식: CSV 파일
- Update frequency: Every 5 seconds / 업데이트 빈도: 5초마다

### Performance Data / 성능 데이터
- Source: Direct EPICS PV queries (caget) / 출처: 직접 EPICS PV 쿼리 (caget)
- Format: Real-time values / 형식: 실시간 값
- Update frequency: Every 5 seconds / 업데이트 빈도: 5초마다
- Note: Only for running IOCs / 참고: 실행 중인 IOC만

### Event Logs / 이벤트 로그
- Source: EPICS Alive Server event files / 출처: EPICS Alive 서버 이벤트 파일
- Format: Text logs / 형식: 텍스트 로그
- Update frequency: Real-time / 업데이트 빈도: 실시간

## Examples / 예제

### Python Client Example / Python 클라이언트 예제

```python
import requests

# Get all IOC data
response = requests.get('http://localhost:5000/api/data')
iocs = response.json()

# Get faulted IOCs
response = requests.get('http://localhost:5000/api/faulted_iocs')
faulted = response.json()

# Search PVs
response = requests.get('http://localhost:5000/api/pv/search?query=TEST-SYS')
pvs = response.json()
```

### JavaScript Client Example / JavaScript 클라이언트 예제

```javascript
// Get all IOC data
fetch('/api/data')
  .then(response => response.json())
  .then(data => console.log(data));

// Get faulted IOCs
fetch('/api/faulted_iocs')
  .then(response => response.json())
  .then(data => console.log(data.count, data.data));

// Search PVs
fetch('/api/pv/search?query=TEST-SYS')
  .then(response => response.json())
  .then(data => console.log(data));
```

### cURL Examples / cURL 예제

```bash
# Get system status
curl http://localhost:5000/api/status

# Get all IOC data
curl http://localhost:5000/api/data

# Get faulted IOCs
curl http://localhost:5000/api/faulted_iocs

# Search PVs
curl "http://localhost:5000/api/pv/search?query=TEST-SYS"

# Delete IOC (requires authentication)
curl -X DELETE "http://localhost:5000/api/delete?ioc=TEST-SYS:MCP-EXP001" \
  -H "Cookie: session=your-session-cookie"
``` 