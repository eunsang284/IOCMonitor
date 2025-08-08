#!/bin/bash

# EPICS Alive Daemon Installation Script v1.2.0
# EPICS Alive Daemon 설치 스크립트 v1.2.0
# Builds and configures EPICS Alive Daemon within IOC Monitor directory
# IOC Monitor 디렉토리 내에서 EPICS Alive Daemon을 빌드하고 설정합니다

set -e  # Exit on any error / 오류 발생 시 종료

# Set environment variables directly / 환경 변수 직접 설정
export BASE_DIR="$(pwd)"
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

# Color definitions / 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color / 색상 초기화

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

# Check current directory / 현재 디렉토리 확인
check_directory() {
    if [ ! -d "$ALIVE_SERVER_DIR" ]; then
        print_error "alive-server directory not found: $ALIVE_SERVER_DIR"
        print_error "Please run download_alive_components.sh first to download components."
        print_error "먼저 download_alive_components.sh를 실행하여 컴포넌트를 다운로드하세요."
        exit 1
    fi
    
    if [ ! -d "$ALIVE_CLIENT_DIR" ]; then
        print_error "alive-client directory not found: $ALIVE_CLIENT_DIR"
        print_error "Please run download_alive_components.sh first to download components."
        print_error "먼저 download_alive_components.sh를 실행하여 컴포넌트를 다운로드하세요."
        exit 1
    fi
    
    if [ ! -d "$ALIVE_WEB_DIR" ]; then
        print_error "alive-web directory not found: $ALIVE_WEB_DIR"
        print_error "Please run download_alive_components.sh first to download components."
        print_error "먼저 download_alive_components.sh를 실행하여 컴포넌트를 다운로드하세요."
        exit 1
    fi
    
    print_success "All EPICS Alive components verified."
}

# Check required tools / 필요한 도구 확인
check_tools() {
    if ! command -v gcc &> /dev/null; then
        print_error "gcc is not installed. Please install gcc."
        print_error "gcc가 설치되어 있지 않습니다. gcc를 설치하세요."
        exit 1
    fi
    
    if ! command -v make &> /dev/null; then
        print_error "make is not installed. Please install make."
        print_error "make가 설치되어 있지 않습니다. make를 설치하세요."
        exit 1
    fi
    
    print_success "Required build tools verified."
}

# Create directories / 디렉토리 생성
create_directories() {
    print_status "Creating required directories..."
    
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$BUILD_DIR"
    mkdir -p "$BUILD_SERVER_DIR"
    mkdir -p "$EVENT_DIR"
    mkdir -p "$STATE_DIR"
    
    print_success "Directory creation completed."
}

# Copy and modify configuration file / 설정 파일 복사 및 수정
setup_config() {
    print_status "Setting up configuration file..."
    
    # Copy configuration file / 설정 파일 복사
    if [ -f "$ALIVED_CONFIG_TEMPLATE" ]; then
        cp "$ALIVED_CONFIG_TEMPLATE" "$ALIVED_CONFIG_FILE"
        print_success "Configuration file copied: $ALIVED_CONFIG_FILE"
    else
        print_error "Configuration template not found: $ALIVED_CONFIG_TEMPLATE"
        exit 1
    fi
    
    # Modify configuration file paths / 설정 파일 경로 수정
    sed -i "s|log_file.*|log_file         \"$LOG_FILE\"|" "$ALIVED_CONFIG_FILE"
    sed -i "s|event_file.*|event_file       \"$EVENT_FILE\"|" "$ALIVED_CONFIG_FILE"
    sed -i "s|info_file.*|info_file        \"$INFO_FILE\"|" "$ALIVED_CONFIG_FILE"
    sed -i "s|control_socket.*|control_socket   \"$CONTROL_SOCKET\"|" "$ALIVED_CONFIG_FILE"
    sed -i "s|event_dir.*|event_dir        \"$EVENT_DIR\"|" "$ALIVED_CONFIG_FILE"
    sed -i "s|state_dir.*|state_dir        \"$STATE_DIR\"|" "$ALIVED_CONFIG_FILE"
    
    print_success "Configuration file modified for IOC_Monitor directory."
}

# Build / 빌드
build_alive_server() {
    print_status "Building EPICS Alive Server..."
    print_status "Build directory: $BUILD_SERVER_DIR"
    
    # Move to build directory and build / 빌드 디렉토리로 이동하여 빌드
    cd "$BUILD_SERVER_DIR"
    
    # Use build Makefile / 빌드 Makefile 사용
    if make -f ../../scripts/build.mk BUILD_DIR=. Cfg_File="$ALIVED_CONFIG_FILE"; then
        print_success "Build completed successfully."
    else
        print_error "Build failed."
        exit 1
    fi
    
    cd "$BASE_DIR"
}

# Verify executables / 실행 파일 확인
verify_executables() {
    print_status "Verifying executable files..."
    
    if [ -f "$ALIVED_EXEC" ]; then
        print_success "alived executable created: $ALIVED_EXEC"
    else
        print_error "alived executable not found: $ALIVED_EXEC"
        exit 1
    fi
    
    if [ -f "$ALIVECTL_EXEC" ]; then
        print_success "alivectl executable created: $ALIVECTL_EXEC"
    else
        print_error "alivectl executable not found: $ALIVECTL_EXEC"
        exit 1
    fi
    
    if [ -f "$EVENT_DUMP_EXEC" ]; then
        print_success "event_dump executable created: $EVENT_DUMP_EXEC"
    else
        print_error "event_dump executable not found: $EVENT_DUMP_EXEC"
    fi
}

# Test installation / 테스트
test_installation() {
    print_status "Testing installation..."
    
    # Test alived help / alived 도움말 테스트
    if "$ALIVED_EXEC" -h &> /dev/null; then
        print_success "alived executable working correctly: $ALIVED_EXEC"
    else
        print_warning "alived executable test failed."
    fi
    
    # Test alivectl help (with environment variable) / alivectl 도움말 테스트 (환경 변수 설정)
    export Cfg_File="$ALIVED_CONFIG_FILE"
    if "$ALIVECTL_EXEC" -h &> /dev/null; then
        print_success "alivectl executable working correctly: $ALIVECTL_EXEC"
    else
        print_warning "alivectl executable test failed."
        print_warning "For actual use, set environment variable Cfg_File or specify config file in command line."
        print_warning "실제 사용 시에는 환경 변수 Cfg_File을 설정하거나 명령행에서 설정 파일을 지정하세요."
    fi
}

# Show completion information / 설치 완료 정보 출력
show_completion_info() {
    print_success "EPICS Alive Daemon installation completed!"
    echo ""
    print_status "Installed files:"
    echo "  ├── $ALIVED_EXEC          # Alive server (daemon)"
    echo "  ├── $ALIVECTL_EXEC        # Daemon control tool"
    echo "  ├── $EVENT_DUMP_EXEC      # Event dump tool"
    echo "  ├── $CONFIG_DIR/          # Configuration directory"
    echo "  ├── $BUILD_DIR/           # Build directory"
    echo "  └── $LOGS_DIR/            # Log directory"
    echo ""
    print_status "Usage:"
    echo "  # Load configuration"
    echo "  source load_config.sh"
    echo ""
    echo "  # Start daemon (terminal mode)"
    echo "  $ALIVED_EXEC -t"
    echo ""
    echo "  # Control daemon"
    echo "  $ALIVECTL_EXEC -p       # Check daemon status"
    echo "  $ALIVECTL_EXEC -s       # Show current status"
    echo "  $ALIVECTL_EXEC -l       # List IOCs"
    echo "  $ALIVECTL_EXEC -q       # Stop daemon"
    echo ""
    print_status "Configuration file: $ALIVED_CONFIG_FILE"
    print_status "Build directory: $BUILD_DIR"
    print_status "Log directory: $LOGS_DIR"
    echo ""
    print_status "Git deployment structure:"
    echo "  - Source code maintained in alive-server/, alive-client/, alive-web/ directories"
    echo "  - Build files generated in build/ directory (excluded from Git)"
    echo "  - Configuration files in config/ directory"
    echo "  - Log files in logs/ directory (excluded from Git)"
}

# Main execution function / 메인 실행 함수
main() {
    # Display version information / 버전 정보 표시
    VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")
    print_status "EPICS IOC Monitor v${VERSION}"
    print_status "EPICS IOC 모니터 v${VERSION}"
    print_status "Starting EPICS Alive Daemon installation..."
    print_status "Working directory: $BASE_DIR"
    
    # 1. Check directory / 디렉토리 확인
    check_directory
    
    # 2. Check tools / 도구 확인
    check_tools
    
    # 3. Create directories / 디렉토리 생성
    create_directories
    
    # 4. Setup configuration file / 설정 파일 설정
    setup_config
    
    # 5. Build / 빌드
    build_alive_server
    
    # 6. Verify executables / 실행 파일 확인
    verify_executables
    
    # 7. Test installation / 테스트
    test_installation
    
    # 8. Show completion information / 완료 정보 출력
    show_completion_info
}

# Execute script / 스크립트 실행
main "$@" 