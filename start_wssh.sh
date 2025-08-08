#!/bin/bash

# WebSocket SSH Server Start Script
# WebSocket SSH 서버 시작 스크립트

# Change to script directory / 스크립트 디렉토리로 이동
cd "$(dirname "$0")"

# Activate virtual environment / 가상환경 활성화
source venv/bin/activate

# Start WebSocket SSH server / WebSocket SSH 서버 시작
echo "Starting WebSocket SSH server on port 8022..."
echo "WebSocket SSH 서버를 포트 8022에서 시작합니다..."

wssh --address=0.0.0.0 --port=8022 --debug 