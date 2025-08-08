# Changelog

All notable changes to this project will be documented in this file.


## [1.2.0] - 2025-08-08

### Added
- Version 1.2.0 release



## [1.1.0] - 2025-08-08

### Added
- Version 1.1.0 release



## [1.0.1] - 2025-08-08

### Added
- Version 1.0.1 release


The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-XX

### Added
- Webbased EPICS IOC Monitoring System
- EPICS Alive 기반 IOC 모니터링 시스템
- Flask 웹 애플리케이션 (포트 5001)
- 실시간 IOC 상태 모니터링 및 테이블 표시
- IOC 상세 정보 페이지 (엔지니어, 위치, 목적, BPC, ENV1-ENV16 등)
- 이벤트 로그 시스템 (일별 로그 분리)
- 서버 로그 페이지 (IOCMonitor Logs)
- 관리자 로그인 시스템 (raon/raon)
- WebSocket SSH 터미널 (포트 8022)
- IOC 마스크/언마스크 기능
- 오프라인 IOC 삭제 기능
- 백그라운드 모니터링 및 캐싱 시스템
- 오프라인 실행 지원 (부트스트랩, xterm.js 로컬 캐시)
- 한국어/영어 이중 언어 지원
- 자동 배포 스크립트 (development/production 모드)
- EPICS Alive Daemon 자동 설치 스크립트

### Technical Features
- Python 3.8+ 호환
- Flask 2.3.3 기반 웹 프레임워크
- WebSocket SSH (websockets + paramiko)
- Bootstrap 5.3.0 UI 프레임워크
- xterm.js 5.3.0 웹 터미널
- 실시간 데이터 캐싱 및 백그라운드 업데이트
- RESTful API 엔드포인트
- 환경 변수 기반 설정 관리
- 로그 로테이션 및 일별 분리
- Graceful shutdown 및 시그널 핸들링

### Deployment
- 개발 모드: Flask 내장 서버
- 프로덕션 모드: Gunicorn WSGI 서버
- 자동 정적 자산 다운로드 및 캐싱
- 오프라인 환경 지원
- systemd 서비스 지원 (선택사항)

### Security
- 관리자 인증 시스템
- SSH 연결 보안
- 세션 관리
- CORS 설정

### Monitoring
- 실시간 IOC 상태 추적
- 성능 메트릭 수집
- 이벤트 로깅
- 장애 IOC 감지 및 알림
- 서버 상태 모니터링 