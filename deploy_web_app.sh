#!/bin/bash

# EPICS IOC Monitor Web Application Deployment Script v1.0.1
# EPICS IOC 모니터 웹 애플리케이션 배포 스크립트 v1.0.1
# Deploys the Flask web application for IOC monitoring
# IOC 모니터링을 위한 Flask 웹 애플리케이션을 배포합니다

set -e  # Exit on any error / 오류 발생 시 종료

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

# Configuration / 설정
WEB_APP_DIR="web-app"
VENV_DIR="venv"
DEPLOYMENT_MODE="${1:-development}"  # development, production, docker

# Check if running from IOC_Monitor directory / IOC_Monitor 디렉토리에서 실행되는지 확인
check_directory() {
    if [ ! -d "$WEB_APP_DIR" ]; then
        print_error "web-app directory not found: $WEB_APP_DIR"
        print_error "Please run this script from the IOC_Monitor directory."
        print_error "IOC_Monitor 디렉토리에서 이 스크립트를 실행하세요."
        exit 1
    fi
    
    print_success "Directory structure verified."
}

# Check Python dependencies / Python 의존성 확인
check_python_dependencies() {
    print_status "Checking Python dependencies..."
    
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed. Please install Python 3.8+."
        print_error "Python 3이 설치되어 있지 않습니다. Python 3.8+를 설치하세요."
        exit 1
    fi
    
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is not installed. Please install pip3."
        print_error "pip3이 설치되어 있지 않습니다. pip3를 설치하세요."
        exit 1
    fi
    
    # Check for venv module / venv 모듈 확인
    if ! python3 -c "import venv" &> /dev/null; then
        print_error "Python venv module is not available. Please install python3-venv."
        print_error "Python venv 모듈을 사용할 수 없습니다. python3-venv를 설치하세요."
        exit 1
    fi
    
    print_success "Python environment verified."
}

# Create and activate virtual environment / 가상환경 생성 및 활성화
setup_virtual_environment() {
    print_status "Setting up virtual environment..."
    
    if [ ! -d "$VENV_DIR" ]; then
        print_status "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
        print_success "Virtual environment created: $VENV_DIR"
    else
        print_status "Virtual environment already exists: $VENV_DIR"
    fi
    
    # Activate virtual environment / 가상환경 활성화
    print_status "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip / pip 업그레이드
    print_status "Upgrading pip..."
    pip install --upgrade pip
    
    print_success "Virtual environment setup completed."
}

# Install Python dependencies / Python 의존성 설치
install_dependencies() {
    print_status "Installing Python dependencies in virtual environment..."
    
    # Ensure virtual environment is activated / 가상환경이 활성화되었는지 확인
    if [ -z "$VIRTUAL_ENV" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    cd "$WEB_APP_DIR"
    
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
        print_success "Python dependencies installed from requirements.txt"
    else
        print_warning "requirements.txt not found. Installing basic dependencies..."
        pip install Flask Flask-CORS pandas numpy requests python-dotenv
        print_success "Basic dependencies installed."
    fi
    
    cd ..
}

# Setup environment variables / 환경 변수 설정
setup_environment() {
    print_status "Setting up environment variables..."
    
    # Create .env file if it doesn't exist / .env 파일이 없으면 생성
    if [ ! -f "$WEB_APP_DIR/.env" ]; then
        cat > "$WEB_APP_DIR/.env" << EOF
# EPICS IOC Monitor Web Application Environment
# EPICS IOC 모니터 웹 애플리케이션 환경

# Flask settings / Flask 설정
FLASK_ENV=development
FLASK_DEBUG=true
FLASK_HOST=0.0.0.0
FLASK_PORT=5000

# Security / 보안
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Logging / 로깅
LOG_LEVEL=INFO

# EPICS environment / EPICS 환경
EPICS_BASE=/opt/epics
EPICS_HOST_ARCH=linux-x86_64

# Monitoring PVs - Configure your monitoring PVs here / 모니터링 PV들 - 여기서 모니터링할 PV들을 설정하세요
# Format: MONITORING_PV_<number>_NAME="Display Name"
# Format: MONITORING_PV_<number>_ADDRESS="PV:ADDRESS"
# Example / 예시:
# MONITORING_PV_1_NAME="System Status"
# MONITORING_PV_1_ADDRESS="SYSTEM:STATUS"
# MONITORING_PV_2_NAME="Machine Mode"
# MONITORING_PV_2_ADDRESS="MACHINE:MODE"
# MONITORING_PV_3_NAME="Beam Status"
# MONITORING_PV_3_ADDRESS="BEAM:STATUS"
# MONITORING_PV_4_NAME="IOC Ready"
# MONITORING_PV_4_ADDRESS="IOC:READY"

# Control PVs - PVs that will be set based on monitoring PV changes / 제어 PV들 - 모니터링 PV 변화에 따라 설정될 PV들
# Format: CONTROL_PV_<number>_NAME="Display Name"
# Format: CONTROL_PV_<number>_ADDRESS="PV:ADDRESS"
# Format: CONTROL_PV_<number>_ENABLED=true/false
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_TYPE="condition_type"
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_OPERATOR="==" or "!=" or ">" or "<" or ">=" or "<="
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_VALUE="condition_value"
# Format: CONTROL_PV_<number>_CONDITION_<condition_number>_SET_VALUE="value_to_set"
# Example / 예시:
# CONTROL_PV_1_NAME="IOC Ready"
# CONTROL_PV_1_ADDRESS="IOC:READY"
# CONTROL_PV_1_ENABLED=true
# CONTROL_PV_1_CONDITION_1_TYPE="faulted_ioc_count"
# CONTROL_PV_1_CONDITION_1_OPERATOR="=="
# CONTROL_PV_1_CONDITION_1_VALUE="0"
# CONTROL_PV_1_CONDITION_1_SET_VALUE="1"

# Default monitoring PVs (if not specified above) / 기본 모니터링 PV들 (위에서 지정하지 않은 경우)
# These will be used if no custom PVs are defined / 사용자 정의 PV가 정의되지 않은 경우 사용됩니다

# Monitoring intervals (seconds) / 모니터링 간격 (초)
CACHE_UPDATE_INTERVAL=5
IOC_READY_UPDATE_INTERVAL=1
FAULTED_MONITOR_INTERVAL=5
PV_CACHE_UPDATE_INTERVAL=30

# Feature flags - Enable/disable features / 기능 플래그 - 기능 활성화/비활성화
FEATURE_ALIVE_SERVER=true
FEATURE_CSV_LOADING=false
FEATURE_PV_MONITORING=true
FEATURE_CONTROL_PVS=true
FEATURE_FAULTED_MONITORING=true
FEATURE_PV_CACHE=false

# Performance settings / 성능 설정
MAX_WORKERS=4
REQUEST_TIMEOUT=30
EOF
        print_success "Environment file created: $WEB_APP_DIR/.env"
        print_warning "Please edit $WEB_APP_DIR/.env to configure your monitoring PVs."
        print_warning "$WEB_APP_DIR/.env를 편집하여 모니터링할 PV들을 설정하세요."
    else
        print_status "Environment file already exists."
    fi
}

# Create necessary directories / 필요한 디렉토리 생성
create_directories() {
    print_status "Creating necessary directories..."
    print_status "필요한 디렉토리를 생성합니다..."
    
    mkdir -p "$WEB_APP_DIR/logs"
    mkdir -p "$WEB_APP_DIR/cache"
    mkdir -p "$WEB_APP_DIR/config"
    mkdir -p "$WEB_APP_DIR/static"
    mkdir -p "$WEB_APP_DIR/static/vendor/bootstrap/css"
    mkdir -p "$WEB_APP_DIR/static/vendor/bootstrap/js"
    mkdir -p "$WEB_APP_DIR/static/vendor/xterm/css"
    mkdir -p "$WEB_APP_DIR/static/vendor/xterm/js"
    mkdir -p "$WEB_APP_DIR/templates"
    
    print_success "Directories created."
    print_success "디렉토리 생성 완료."
}

# Download frontend vendor assets for offline use / 오프라인 사용을 위한 프론트엔드 라이브러리 다운로드
download_vendor_assets() {
    print_status "Downloading frontend assets (Bootstrap, xterm.js)..."
    print_status "프론트엔드 자산(부트스트랩, xterm.js)을 다운로드합니다..."

    # Check downloader availability / 다운로드 도구 확인
    DOWNLOADER=""
    if command -v curl >/dev/null 2>&1; then
        DOWNLOADER="curl -fsSL -o"
    elif command -v wget >/dev/null 2>&1; then
        DOWNLOADER="wget -qO"
    else
        print_warning "Neither curl nor wget is installed. Skipping asset download."
        print_warning "curl 또는 wget이 설치되어 있지 않습니다. 자산 다운로드를 건너뜁니다."
        return
    fi
    
    # Bootstrap 5.3.0
    if [ ! -f "$WEB_APP_DIR/static/vendor/bootstrap/css/bootstrap.min.css" ]; then
        $DOWNLOADER "$WEB_APP_DIR/static/vendor/bootstrap/css/bootstrap.min.css" \
            https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css || true
    fi
    if [ ! -f "$WEB_APP_DIR/static/vendor/bootstrap/js/bootstrap.bundle.min.js" ]; then
        $DOWNLOADER "$WEB_APP_DIR/static/vendor/bootstrap/js/bootstrap.bundle.min.js" \
            https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js || true
    fi
    
    # xterm.js 5.3.0 and fit addon 0.8.0
    if [ ! -f "$WEB_APP_DIR/static/vendor/xterm/css/xterm.min.css" ]; then
        $DOWNLOADER "$WEB_APP_DIR/static/vendor/xterm/css/xterm.min.css" \
            https://cdn.jsdelivr.net/npm/xterm@5.3.0/css/xterm.min.css || true
    fi
    if [ ! -f "$WEB_APP_DIR/static/vendor/xterm/js/xterm.min.js" ]; then
        $DOWNLOADER "$WEB_APP_DIR/static/vendor/xterm/js/xterm.min.js" \
            https://cdn.jsdelivr.net/npm/xterm@5.3.0/lib/xterm.min.js || true
    fi
    if [ ! -f "$WEB_APP_DIR/static/vendor/xterm/js/xterm-addon-fit.min.js" ]; then
        $DOWNLOADER "$WEB_APP_DIR/static/vendor/xterm/js/xterm-addon-fit.min.js" \
            https://cdn.jsdelivr.net/npm/xterm-addon-fit@0.8.0/lib/xterm-addon-fit.min.js || true
    fi
    
    print_success "Frontend assets are ready for offline use."
    print_success "오프라인 실행을 위한 프론트엔드 자산 준비 완료."
}

# Deploy in development mode / 개발 모드로 배포
deploy_development() {
    print_status "Deploying in development mode..."
    
    # Ensure virtual environment is activated / 가상환경이 활성화되었는지 확인
    if [ -z "$VIRTUAL_ENV" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Start WebSocket SSH server in background / WebSocket SSH 서버를 백그라운드에서 시작
    print_status "Starting WebSocket SSH server in background..."
    print_status "WebSocket SSH 서버를 백그라운드에서 시작합니다..."
    
    # Check if websockets is installed / websockets 설치 확인
    if ! python -c "import websockets" &> /dev/null; then
        print_status "Installing websockets..."
        pip install websockets
        print_success "websockets installed."
    fi
    
    # Kill existing WebSocket SSH process if running / 실행 중인 WebSocket SSH 프로세스 종료
    if [ -f "websocket_ssh.pid" ]; then
        OLD_PID=$(cat websocket_ssh.pid)
        if kill -0 $OLD_PID 2>/dev/null; then
            print_status "Stopping existing WebSocket SSH server (PID: $OLD_PID)..."
            kill $OLD_PID
            sleep 2
        fi
        rm -f websocket_ssh.pid
    fi
    
    # Start WebSocket SSH server in background / WebSocket SSH 서버를 백그라운드에서 시작
    nohup python websocket_ssh_server.py > websocket_ssh.log 2>&1 &
    WSSH_PID=$!
    echo $WSSH_PID > websocket_ssh.pid
    print_success "WebSocket SSH server started with PID: $WSSH_PID"
    print_status "WebSocket SSH server logs: tail -f websocket_ssh.log"
    
    cd "$WEB_APP_DIR"
    
    # Set environment variables / 환경 변수 설정
    export FLASK_ENV=development
    export FLASK_DEBUG=true
    export FLASK_HOST=0.0.0.0
    export FLASK_PORT=5001
    
    print_status "Starting Flask development server..."
    print_status "Access the application at: http://localhost:5001"
    print_status "WebSocket SSH server at: ws://localhost:8022"
    print_status "API documentation at: http://localhost:5001/api"
    print_status "Virtual environment: $VIRTUAL_ENV"
    
    python app.py
}

# Deploy in production mode / 프로덕션 모드로 배포
deploy_production() {
    print_status "Deploying in production mode..."
    
    # Ensure virtual environment is activated / 가상환경이 활성화되었는지 확인
    if [ -z "$VIRTUAL_ENV" ]; then
        source "$VENV_DIR/bin/activate"
    fi
    
    # Start WebSocket SSH server in background / WebSocket SSH 서버를 백그라운드에서 시작
    print_status "Starting WebSocket SSH server in background..."
    print_status "WebSocket SSH 서버를 백그라운드에서 시작합니다..."
    
    # Check if websockets is installed / websockets 설치 확인
    if ! python -c "import websockets" &> /dev/null; then
        print_status "Installing websockets..."
        pip install websockets
        print_success "websockets installed."
    fi
    
    # Kill existing WebSocket SSH process if running / 실행 중인 WebSocket SSH 프로세스 종료
    if [ -f "websocket_ssh.pid" ]; then
        OLD_PID=$(cat websocket_ssh.pid)
        if kill -0 $OLD_PID 2>/dev/null; then
            print_status "Stopping existing WebSocket SSH server (PID: $OLD_PID)..."
            kill $OLD_PID
            sleep 2
        fi
        rm -f websocket_ssh.pid
    fi
    
    # Start WebSocket SSH server in background / WebSocket SSH 서버를 백그라운드에서 시작
    nohup python websocket_ssh_server.py > websocket_ssh.log 2>&1 &
    WSSH_PID=$!
    echo $WSSH_PID > websocket_ssh.pid
    print_success "WebSocket SSH server started with PID: $WSSH_PID"
    print_status "WebSocket SSH server logs: tail -f websocket_ssh.log"
    
    # Check if gunicorn is available / gunicorn 가용성 확인
    if ! command -v gunicorn &> /dev/null; then
        print_warning "Gunicorn not found. Installing..."
        pip install gunicorn
    fi
    
    cd "$WEB_APP_DIR"
    
    # Set environment variables / 환경 변수 설정
    export FLASK_ENV=production
    export FLASK_DEBUG=false
    export FLASK_HOST=0.0.0.0
    export FLASK_PORT=5000
    
    print_status "Starting Gunicorn production server..."
    print_status "Access the application at: http://localhost:5000"
    print_status "WebSocket SSH server at: ws://localhost:8022"
    print_status "Virtual environment: $VIRTUAL_ENV"
    
    gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 app:app
}

# Deploy using Docker / Docker를 사용하여 배포
deploy_docker() {
    print_status "Deploying using Docker..."
    
    # Check if Docker is available / Docker 가용성 확인
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        print_error "Docker가 설치되어 있지 않습니다. 먼저 Docker를 설치하세요."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        print_error "Docker Compose가 설치되어 있지 않습니다. 먼저 Docker Compose를 설치하세요."
        exit 1
    fi
    
    cd "$WEB_APP_DIR"
    
    print_status "Building Docker image..."
    docker-compose build
    
    print_status "Starting Docker services..."
    docker-compose up -d
    
    print_success "Docker deployment completed."
    print_status "Access the application at: http://localhost:5000"
    print_status "Check logs with: docker-compose logs -f"
}

# Create systemd service / systemd 서비스 생성
create_systemd_service() {
    print_status "Creating systemd service..."
    
    SERVICE_NAME="ioc-monitor-web"
    SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
    
    if [ "$EUID" -ne 0 ]; then
        print_warning "This operation requires root privileges."
        print_warning "Please run with sudo to create systemd service."
        return
    fi
    
    # Get absolute paths / 절대 경로 가져오기
    BASE_DIR=$(pwd)
    VENV_PATH="$BASE_DIR/$VENV_DIR"
    WEB_APP_PATH="$BASE_DIR/$WEB_APP_DIR"
    
    cat > "$SERVICE_FILE" << EOF
[Unit]
Description=EPICS IOC Monitor Web Application
After=network.target

[Service]
Type=simple
User=ctrluser
WorkingDirectory=$WEB_APP_PATH
Environment=PATH=$VENV_PATH/bin:/usr/local/bin:/usr/bin:/bin
Environment=VIRTUAL_ENV=$VENV_PATH
Environment=FLASK_ENV=production
Environment=FLASK_DEBUG=false
Environment=FLASK_HOST=0.0.0.0
Environment=FLASK_PORT=5000
ExecStart=$VENV_PATH/bin/python app.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable "$SERVICE_NAME"
    
    print_success "Systemd service created: $SERVICE_NAME"
    print_status "Start service with: sudo systemctl start $SERVICE_NAME"
    print_status "Check status with: sudo systemctl status $SERVICE_NAME"
}

# Show deployment information / 배포 정보 표시
show_deployment_info() {
    print_success "EPICS IOC Monitor Web Application deployment completed!"
    echo ""
    print_status "Deployment Information:"
    echo "  ├── Mode: $DEPLOYMENT_MODE"
    echo "  ├── Directory: $(pwd)/$WEB_APP_DIR"
    echo "  ├── Virtual Environment: $(pwd)/$VENV_DIR"
    echo "  ├── Port: 5000"
    echo "  ├── URL: http://localhost:5000"
    echo "  └── API: http://localhost:5000/api"
    echo ""
    print_status "API Documentation:"
    echo "  └── $WEB_APP_DIR/API_DOCUMENTATION.md"
    echo ""
    print_status "Configuration:"
    echo "  ├── Environment: $WEB_APP_DIR/.env"
    echo "  ├── Logs: $WEB_APP_DIR/logs/"
    echo "  └── Cache: $WEB_APP_DIR/cache/"
    echo ""
    
    if [ "$DEPLOYMENT_MODE" = "docker" ]; then
        print_status "Docker Commands:"
        echo "  ├── View logs: docker-compose logs -f"
        echo "  ├── Stop: docker-compose down"
        echo "  └── Restart: docker-compose restart"
    elif [ "$DEPLOYMENT_MODE" = "production" ]; then
        print_status "Production Commands:"
        echo "  ├── Check status: ps aux | grep gunicorn"
        echo "  ├── Stop: pkill gunicorn"
        echo "  └── Restart: $0 production"
    fi
    
    echo ""
    print_status "Virtual Environment Commands:"
    echo "  ├── Activate: source $VENV_DIR/bin/activate"
    echo "  ├── Deactivate: deactivate"
    echo "  └── Install package: pip install <package_name>"
}

# Clean virtual environment / 가상환경 정리
clean_virtual_environment() {
    print_status "Cleaning virtual environment..."
    
    if [ -d "$VENV_DIR" ]; then
        rm -rf "$VENV_DIR"
        print_success "Virtual environment removed: $VENV_DIR"
    else
        print_status "Virtual environment does not exist."
    fi
}

# Start WebSocket SSH server / WebSocket SSH 서버 시작
start_wssh_server() {
    print_status "Starting WebSocket SSH server..."
    
    # Check if websockets is installed / websockets 설치 확인
    if ! source "$VENV_DIR/bin/activate" && python -c "import websockets" &> /dev/null; then
        print_status "Installing websockets..."
        source "$VENV_DIR/bin/activate"
        pip install websockets
        print_success "websockets installed."
    fi
    
    # Kill existing WebSocket SSH process if running / 실행 중인 WebSocket SSH 프로세스 종료
    if [ -f "websocket_ssh.pid" ]; then
        OLD_PID=$(cat websocket_ssh.pid)
        if kill -0 $OLD_PID 2>/dev/null; then
            print_status "Stopping existing WebSocket SSH server (PID: $OLD_PID)..."
            kill $OLD_PID
            sleep 2
        fi
        rm -f websocket_ssh.pid
    fi
    
    # Start WebSocket SSH server / WebSocket SSH 서버 시작
    print_status "Starting WebSocket SSH server on port 8022..."
    print_status "WebSocket SSH 서버를 포트 8022에서 시작합니다..."
    
    source "$VENV_DIR/bin/activate"
    nohup python websocket_ssh_server.py > websocket_ssh.log 2>&1 &
    WSSH_PID=$!
    echo $WSSH_PID > websocket_ssh.pid
    print_success "WebSocket SSH server started with PID: $WSSH_PID"
    print_status "WebSocket SSH server logs: tail -f websocket_ssh.log"
}

# Stop WebSocket SSH server / WebSocket SSH 서버 중지
stop_wssh_server() {
    print_status "Stopping WebSocket SSH server..."
    
    if [ -f "websocket_ssh.pid" ]; then
        WSSH_PID=$(cat websocket_ssh.pid)
        if kill -0 $WSSH_PID 2>/dev/null; then
            print_status "Stopping WebSocket SSH server (PID: $WSSH_PID)..."
            kill $WSSH_PID
            rm -f websocket_ssh.pid
            print_success "WebSocket SSH server stopped."
        else
            print_warning "WebSocket SSH server is not running."
            rm -f websocket_ssh.pid
        fi
    else
        print_warning "No WebSocket SSH server PID file found."
    fi
}

# Main deployment function / 메인 배포 함수
main() {
    # Display version information / 버전 정보 표시
    VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")
    print_status "EPICS IOC Monitor v${VERSION}"
    print_status "EPICS IOC 모니터 v${VERSION}"
    print_status "Starting EPICS IOC Monitor Web Application deployment..."
    print_status "Deployment mode: $DEPLOYMENT_MODE"
    
    # 1. Check directory / 디렉토리 확인
    check_directory
    
    # 2. Check Python dependencies / Python 의존성 확인
    check_python_dependencies
    
    # 3. Setup virtual environment / 가상환경 설정
    setup_virtual_environment
    
    # 4. Install dependencies / 의존성 설치
    install_dependencies
    
    # 5. Setup environment / 환경 설정
    setup_environment
    
    # 6. Create directories / 디렉토리 생성
    create_directories
    
    # 6.1 Download vendor assets / 라이브러리 다운로드
    download_vendor_assets
    
    # 7. Deploy based on mode / 모드에 따른 배포
    case "$DEPLOYMENT_MODE" in
        "development")
            deploy_development
            ;;
        "production")
            deploy_production
            ;;
        "docker")
            deploy_docker
            ;;
        "systemd")
            create_systemd_service
            show_deployment_info
            ;;
        "wssh")
            start_wssh_server
            ;;
        "stop-wssh")
            stop_wssh_server
            ;;
        "clean")
            clean_virtual_environment
            print_success "Virtual environment cleaned."
            ;;
        *)
            print_error "Invalid deployment mode: $DEPLOYMENT_MODE"
            print_error "Valid modes: development, production, docker, systemd, wssh, stop-wssh, clean"
            exit 1
            ;;
    esac
    
    # 8. Show deployment information / 배포 정보 표시
    if [ "$DEPLOYMENT_MODE" != "development" ] && [ "$DEPLOYMENT_MODE" != "clean" ]; then
        show_deployment_info
    fi
}

# Show usage / 사용법 표시
show_usage() {
    VERSION=$(cat VERSION 2>/dev/null || echo "1.0.0")
    echo "EPICS IOC Monitor Web Application Deployment Script v1.0.1${VERSION}"
    echo "EPICS IOC 모니터 웹 애플리케이션 배포 스크립트 v1.0.1${VERSION}"
    echo ""
    echo "Usage: $0 [deployment_mode]"
    echo ""
    echo "Deployment modes:"
    echo "  development  - Run in development mode with Flask debug server (includes SSH)"
    echo "  production   - Run in production mode with Gunicorn (includes SSH)"
    echo "  docker       - Deploy using Docker and Docker Compose"
    echo "  systemd      - Create systemd service (requires sudo)"
    echo "  wssh         - Start WebSocket SSH server only"
    echo "  stop-wssh    - Stop WebSocket SSH server"
    echo "  clean        - Remove virtual environment"
    echo ""
    echo "Examples:"
    echo "  $0 development   # Start development server (with SSH)"
    echo "  $0 production    # Start production server (with SSH)"
    echo "  $0 docker        # Deploy with Docker"
    echo "  sudo $0 systemd  # Create systemd service"
    echo "  $0 wssh          # Start WebSocket SSH server only"
    echo "  $0 stop-wssh     # Stop WebSocket SSH server"
    echo "  $0 clean         # Remove virtual environment"
    echo ""
    echo "Virtual Environment:"
    echo "  The script automatically creates and manages a virtual environment."
    echo "  스크립트가 자동으로 가상환경을 생성하고 관리합니다."
}

# Check command line arguments / 명령행 인수 확인
if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
    show_usage
    exit 0
fi

# Execute main function / 메인 함수 실행
main "$@" 