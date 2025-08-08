# EPICS IOC Monitor

**Webbased EPICS IOC Monitoring System**

EPICS IOC 모니터링 시스템으로, EPICS Alive 서버를 기반으로 IOC 상태를 실시간으로 모니터링하고 관리합니다.

## 개요 / Overview

이 프로젝트는 EPICS (Experimental Physics and Industrial Control System) IOC (Input/Output Controller)들을 모니터링하기 위한 통합 시스템입니다. EPICS Alive 서버를 기반으로 하여 IOC의 상태, 성능, 이벤트를 실시간으로 추적하고 웹 인터페이스를 통해 관리할 수 있습니다.

## 주요 기능 / Key Features

- **실시간 IOC 모니터링**: EPICS Alive 서버를 통한 IOC 상태 실시간 추적
- **성능 모니터링**: 메모리, CPU, 네트워크 사용량 모니터링
- **이벤트 로깅**: IOC 부팅, 장애, 복구 이벤트 자동 로깅
- **웹 인터페이스**: Flask 기반 웹 애플리케이션
- **RESTful API**: 외부 시스템과의 통합을 위한 API 제공
- **다중 배포 옵션**: 개발, 프로덕션, Docker 배포 지원

## 시스템 요구사항 / System Requirements

- Linux (Ubuntu/Debian 계열 권장)
- Python 3.8+
- EPICS Base 7.0+ (caget/caput 포함, 없을 경우 관련 기능 제한)
- Git, GCC, Make
- curl 또는 wget (정적 자산 캐시용)

## 설치 및 설정 / Installation and Setup

### 1단계: EPICS Alive 컴포넌트 다운로드

```bash
# IOC_Monitor 디렉토리로 이동
cd ~/Apps/IOC_Monitor

# EPICS Alive 컴포넌트 다운로드
./download_alive_components.sh
```

### 2단계: EPICS Alive Daemon 설치

```bash
# EPICS Alive Daemon 빌드 및 설치
./install_alive.sh
```

### 3단계: 설정 로드

```bash
# 환경 설정 로드
./load_config.sh
```

### 4단계: 웹 애플리케이션 배포 (오프라인 자산 자동 캐시)

```bash
# 개발 모드로 배포 (부트스트랩/xterm.js 자산을 로컬로 다운로드 후 사용)
./deploy_web_app.sh development

# 프로덕션 모드로 배포 (부트스트랩/xterm.js 자산을 로컬로 다운로드 후 사용)
./deploy_web_app.sh production

# Docker를 사용한 배포
./deploy_web_app.sh docker

# systemd 서비스 생성 (sudo 필요)
sudo ./deploy_web_app.sh systemd
```

## 디렉토리 구조 / Directory Structure

```
IOC_Monitor/
├── alive-server/          # EPICS Alive 서버 소스
├── alive-client/          # EPICS Alive 클라이언트 도구
├── alive-web/             # 기존 웹 클라이언트 (사용하지 않음)
├── web-app/               # 새로운 Flask 웹 애플리케이션
│   ├── app.py             # 메인 Flask 애플리케이션
│   ├── config.py          # 설정 파일
│   ├── services/          # 서비스 모듈들
│   ├── utils/             # 유틸리티 함수들
│   ├── static/            # 정적 파일들
│   │   └── vendor/        # 부트스트랩, xterm.js 등 로컬 캐시된 라이브러리
│   ├── templates/         # HTML 템플릿들
│   ├── logs/              # 로그 파일들
│   ├── cache/             # 캐시 파일들
│   ├── requirements.txt   # Python 의존성
│   ├── Dockerfile         # Docker 설정
│   └── docker-compose.yml # Docker Compose 설정
├── build/                 # 빌드된 실행 파일들
│   └── alive-server/
│       ├── alived         # Alive 서버 데몬
│       ├── alivectl       # Alive 제어 도구
│       └── event_dump     # 이벤트 덤프 도구
├── config/                # 설정 파일들
│   └── alived_config.txt  # Alive 서버 설정
├── logs/                  # 로그 파일들
│   ├── log.txt           # 메인 로그
│   ├── events.txt        # 이벤트 로그
│   ├── info.txt          # 정보 로그
│   ├── event/            # 이벤트 디렉토리
│   └── state/            # 상태 디렉토리
├── scripts/               # 빌드 스크립트들
│   └── build.mk          # 빌드 Makefile
├── src/                   # 데이터 소스 파일들
│   ├── SAVE.csv          # 메인 IOC 데이터
│   ├── SAVE_envvars.csv  # 환경 변수 데이터
│   ├── SAVE_linux.csv    # Linux 시스템 데이터
│   └── ioc_cache.txt     # IOC 캐시 데이터
├── download_alive_components.sh  # 컴포넌트 다운로드 스크립트
├── install_alive.sh              # Alive 서버 설치 스크립트
├── load_config.sh                # 설정 로드 스크립트
├── deploy_web_app.sh             # 웹 애플리케이션 배포 스크립트
├── config.env                    # 환경 설정 파일
└── README_한국어.md              # 이 파일
```

## 설정 관리 / Configuration Management

### config.env 파일

모든 경로와 설정이 `config.env` 파일에 중앙화되어 있습니다:

```bash
# 기본 디렉토리
BASE_DIR=/home/ctrluser/Apps/IOC_Monitor

# EPICS Alive 컴포넌트 디렉토리
ALIVE_SERVER_DIR=${BASE_DIR}/alive-server
ALIVE_CLIENT_DIR=${BASE_DIR}/alive-client
ALIVE_WEB_DIR=${BASE_DIR}/alive-web

# 빌드 및 출력 디렉토리
BUILD_DIR=${BASE_DIR}/build
BUILD_SERVER_DIR=${BUILD_DIR}/alive-server

# 실행 파일들 (빌드 디렉토리에 위치)
ALIVED_EXEC=${BUILD_SERVER_DIR}/alived
ALIVECTL_EXEC=${BUILD_SERVER_DIR}/alivectl
EVENT_DUMP_EXEC=${BUILD_SERVER_DIR}/event_dump

# 설정 및 로그 디렉토리
CONFIG_DIR=${BASE_DIR}/config
LOGS_DIR=${BASE_DIR}/logs
```

### 웹 애플리케이션 설정

웹 애플리케이션의 설정은 `web-app/config.py`에서 관리됩니다:

```python
class Config:
    # Flask 설정
    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(24)
    DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    HOST = os.environ.get("FLASK_HOST", "0.0.0.0")
    PORT = int(os.environ.get("FLASK_PORT", 5000))
    
    # EPICS PV 설정
    EPICS_PVS = {
        "IOCM_MACHINE_MODE": "SCL-Ctrl:OP-Env:IOCMMachineMode",
        "IOCM_READY": "SCL-Ctrl:OP-Env:IOCMReady",
        # ... 기타 PV들
    }
```

## 사용법 / Usage

### EPICS Alive Daemon 사용법

```bash
# 설정 로드
source load_config.sh

# 데몬 시작 (터미널 모드)
$ALIVED_EXEC -t

# 데몬 상태 확인
$ALIVECTL_EXEC -p

# 현재 상태 출력
$ALIVECTL_EXEC -s

# IOC 목록 출력
$ALIVECTL_EXEC -l

# 데몬 중지
$ALIVECTL_EXEC -q
```

### 웹 애플리케이션 사용법

#### 개발 모드
```bash
./deploy_web_app.sh development
```

#### 프로덕션 모드
```bash
./deploy_web_app.sh production
```

## 오프라인 실행 / Offline Execution
- 최초 배포 시 스크립트가 다음 자산을 `web-app/static/vendor` 하위에 자동 다운로드하여 캐시합니다.
  - Bootstrap 5.3.0 (CSS/JS)
  - xterm.js 5.3.0, xterm-addon-fit 0.8.0 (CSS/JS)
- 이후 템플릿은 CDN이 아닌 로컬 자산을 참조하므로 인터넷 연결이 없어도 웹 UI가 정상 동작합니다.

> 주의: curl 또는 wget이 없는 환경에서는 자산 다운로드가 건너뛰어집니다. 이 경우 해당 파일들을 수동으로 같은 경로에 배치하세요.

#### Docker 모드
```bash
./deploy_web_app.sh docker
```

#### systemd 서비스
```bash
# 서비스 생성
sudo ./deploy_web_app.sh systemd

# 서비스 시작
sudo systemctl start ioc-monitor-web

# 서비스 상태 확인
sudo systemctl status ioc-monitor-web

# 서비스 중지
sudo systemctl stop ioc-monitor-web
```

### API 사용법

웹 애플리케이션은 RESTful API를 제공합니다:

```bash
# 시스템 상태 조회
curl http://localhost:5000/api/status

# 모든 IOC 데이터 조회
curl http://localhost:5000/api/data

# 장애 IOC 조회
curl http://localhost:5000/api/faulted_iocs

# 제어 시스템 상태 조회
curl http://localhost:5000/api/control_states
```

자세한 API 문서는 `web-app/API_DOCUMENTATION.md`를 참조하세요.

## 데이터 수집 방식 / Data Collection Methods

### 1. IOC 상태 데이터
- **소스**: EPICS Alive 서버 (alivectl)
- **형식**: CSV 파일 (SAVE.csv, SAVE_envvars.csv, SAVE_linux.csv)
- **업데이트 빈도**: 5초마다

### 2. 성능 데이터
- **소스**: 직접 EPICS PV 쿼리 (caget)
- **형식**: 실시간 값
- **업데이트 빈도**: 5초마다
- **참고**: 실행 중인 IOC만 (꺼진 IOC는 수행하지 않음)

### 3. 이벤트 로그
- **소스**: EPICS Alive 서버 이벤트 파일
- **형식**: 텍스트 로그
- **업데이트 빈도**: 실시간

## 배포 옵션 / Deployment Options

### 1. 개발 모드 (Development)
- Flask 내장 서버 사용
- 디버그 모드 활성화
- 실시간 코드 리로드
- 로컬 개발용

### 2. 프로덕션 모드 (Production)
- Gunicorn WSGI 서버 사용
- 다중 워커 프로세스
- 성능 최적화
- 실제 운영 환경용

### 3. Docker 모드 (Docker)
- 컨테이너화된 배포
- Redis 캐시 포함
- Nginx 리버스 프록시
- 확장 가능한 아키텍처

### 4. systemd 서비스 (Systemd)
- 시스템 서비스로 등록
- 자동 시작/재시작
- 로그 관리
- 서버 운영용

## 문제 해결 / Troubleshooting

### 일반적인 문제들

1. **EPICS 환경 설정 문제**
   ```bash
   # EPICS 환경 확인
   echo $EPICS_BASE
   echo $EPICS_HOST_ARCH
   
   # EPICS 환경 설정
   source /opt/epics/setEpicsEnv.sh
   ```

2. **권한 문제**
   ```bash
   # 실행 권한 부여
   chmod +x *.sh
   chmod +x build/alive-server/*
   ```

3. **포트 충돌**
   ```bash
   # 포트 사용 확인
   netstat -tlnp | grep :5000
   
   # 다른 포트 사용
   export FLASK_PORT=5001
   ```

4. **의존성 문제**
   ```bash
   # Python 의존성 재설치
   pip3 install -r web-app/requirements.txt --force-reinstall
   ```

### 로그 확인

```bash
# Alive 서버 로그
tail -f logs/log.txt

# 웹 애플리케이션 로그
tail -f web-app/logs/app.log

# 시스템 로그
journalctl -u ioc-monitor-web -f
```

## 개발 가이드 / Development Guide

### 코드 구조

- **app.py**: 메인 Flask 애플리케이션
- **services/**: 비즈니스 로직 서비스들
  - `ioc_monitor.py`: IOC 모니터링 서비스
  - `pv_service.py`: PV 관리 서비스
  - `log_service.py`: 로그 관리 서비스
- **utils/**: 유틸리티 함수들
  - `helpers.py`: 공통 헬퍼 함수들
- **config.py**: 설정 관리

### 새로운 기능 추가

1. 서비스 레이어에 기능 추가
2. API 엔드포인트 정의
3. 프론트엔드 템플릿 업데이트
4. 테스트 작성

### 테스트

```bash
# 단위 테스트 실행
python3 -m pytest web-app/tests/

# 통합 테스트 실행
python3 web-app/tests/test_integration.py
```

## 라이선스 / License

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여 / Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 연락처 / Contact

프로젝트 관련 문의사항이 있으시면 이슈를 생성해 주세요.

---

**참고**: 이 시스템은 EPICS Alive 서버를 기반으로 하며, EPICS 환경이 올바르게 설정되어 있어야 합니다. 