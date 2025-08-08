#!/bin/bash

# IOC Monitor Configuration Loader
# IOC Monitor 설정 로더
# Loads configuration file and sets environment variables for EPICS Alive system
# EPICS Alive 시스템을 위한 설정 파일을 로드하고 환경 변수를 설정합니다

# Color definitions / 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Color output functions / 색상 출력 함수
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Load config.env file / config.env 파일 로드
load_config() {
    local config_file="config.env"
    
    if [ ! -f "$config_file" ]; then
        print_error "config.env file not found."
        print_error "config.env 파일을 찾을 수 없습니다."
        print_error "Current directory: $(pwd)"
        return 1
    fi
    
    print_status "Loading config.env file..."
    
    # Set BASE_DIR to current directory / BASE_DIR을 현재 디렉토리로 설정
    export BASE_DIR="$(pwd)"
    
    # Load config.env file as source / config.env 파일을 소스로 로드
    source "$config_file"
    
    # Set BASE_DIR again if not set / BASE_DIR이 설정되지 않았다면 다시 설정
    if [ -z "$BASE_DIR" ]; then
        export BASE_DIR="$(pwd)"
    fi
    
    # Set other variables based on BASE_DIR / BASE_DIR을 기반으로 다른 변수들 설정
    export ALIVE_SERVER_DIR="${BASE_DIR}/alive-server"
    export ALIVE_CLIENT_DIR="${BASE_DIR}/alive-client"
    export ALIVE_WEB_DIR="${BASE_DIR}/alive-web"
    export BUILD_DIR="${BASE_DIR}/build"
    export BUILD_SERVER_DIR="${BUILD_DIR}/alive-server"
    export BUILD_CLIENT_DIR="${BUILD_DIR}/alive-client"
    export BUILD_WEB_DIR="${BUILD_DIR}/alive-web"
    export CONFIG_DIR="${BASE_DIR}/config"
    export LOGS_DIR="${BASE_DIR}/logs"
    export EVENT_DIR="${LOGS_DIR}/event"
    export STATE_DIR="${LOGS_DIR}/state"
    export ALIVED_CONFIG_FILE="${CONFIG_DIR}/alived_config.txt"
    export ALIVED_CONFIG_TEMPLATE="${ALIVE_SERVER_DIR}/init/alived_config.txt"
    export ALIVED_EXEC="${BUILD_SERVER_DIR}/alived"
    export ALIVECTL_EXEC="${BUILD_SERVER_DIR}/alivectl"
    export EVENT_DUMP_EXEC="${BUILD_SERVER_DIR}/event_dump"
    export ALIVED_SRC_DIR="${ALIVE_SERVER_DIR}/src"
    export ALIVED_MAKEFILE="${ALIVE_SERVER_DIR}/Makefile"
    export LOG_FILE="${LOGS_DIR}/log.txt"
    export EVENT_FILE="${LOGS_DIR}/events.txt"
    export INFO_FILE="${LOGS_DIR}/info.txt"
    export CONTROL_SOCKET="${LOGS_DIR}/control_socket"
    export Cfg_File="${ALIVED_CONFIG_FILE}"
    export ALIVE_BASE_DIR="${BASE_DIR}"
    export ALIVE_CONFIG_DIR="${CONFIG_DIR}"
    export ALIVE_LOGS_DIR="${LOGS_DIR}"
    export DOWNLOAD_SCRIPT="${BASE_DIR}/download_alive_components.sh"
    export INSTALL_SCRIPT="${BASE_DIR}/install_alive.sh"
    export MAKEFILE_BACKUP="${ALIVE_SERVER_DIR}/Makefile.backup"
    
    # Verify environment variables / 환경 변수 확인
    if [ -z "$BASE_DIR" ]; then
        print_error "BASE_DIR environment variable not set."
        print_error "BASE_DIR 환경 변수가 설정되지 않았습니다."
        return 1
    fi
    
    print_success "Configuration loaded successfully."
    print_status "Base directory: $BASE_DIR"
    
    return 0
}

# Display environment variables / 환경 변수 출력
show_config() {
    echo ""
    print_status "Current configuration:"
    echo "  BASE_DIR: $BASE_DIR"
    echo "  CONFIG_DIR: $CONFIG_DIR"
    echo "  LOGS_DIR: $LOGS_DIR"
    echo "  BUILD_DIR: $BUILD_DIR"
    echo "  ALIVED_CONFIG_FILE: $ALIVED_CONFIG_FILE"
    echo "  Cfg_File: $Cfg_File"
    echo ""
}

# Main execution / 메인 실행
main() {
    if load_config; then
        show_config
        return 0
    else
        return 1
    fi
}

# Execute main function only when script is run directly / 스크립트가 직접 실행된 경우에만 main 함수 호출
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi 