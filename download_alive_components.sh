#!/bin/bash

# EPICS Alive Components Download Script
# EPICS Alive 컴포넌트 다운로드 스크립트
# Downloads EPICS Alive components for IOC Monitor implementation
# IOC Monitor 구현을 위한 EPICS Alive 컴포넌트들을 다운로드합니다

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

# Check if git is installed / Git 설치 여부 확인
check_git() {
    if ! command -v git &> /dev/null; then
        print_error "Git is not installed. Please install git first."
        print_error "Git이 설치되어 있지 않습니다. Git을 먼저 설치하세요."
        exit 1
    fi
    print_success "Git is available."
}

# Function to clone repository / 저장소 클론 함수
clone_repo() {
    local repo_url=$1
    local folder_name=$2
    local description=$3
    
    print_status "Downloading $description..."
    
    if [ -d "$folder_name" ]; then
        print_warning "Directory $folder_name already exists. Removing it..."
        rm -rf "$folder_name"
    fi
    
    if git clone "$repo_url" "$folder_name"; then
        print_success "Successfully downloaded $description to $folder_name/"
    else
        print_error "Failed to download $description"
        return 1
    fi
}

# Main execution / 메인 실행
main() {
    print_status "Starting EPICS Alive components download..."
    print_status "Target directory: $(pwd)"
    
    # Check git availability / Git 가용성 확인
    check_git
    
    # Create directories and clone repositories / 디렉토리 생성 및 저장소 클론
    print_status "Creating directories and downloading components..."
    
    # Clone alive-server (alived) / alive-server (alived) 클론
    clone_repo "https://github.com/epics-alive-server/alived.git" "alive-server" "Alive Database Server"
    
    # Clone alive-client (client-tools) / alive-client (client-tools) 클론
    clone_repo "https://github.com/epics-alive-server/client-tools.git" "alive-client" "Alive Client Tools"
    
    # Clone alive-web (web-client) / alive-web (web-client) 클론
    clone_repo "https://github.com/epics-alive-server/web-client.git" "alive-web" "Alive Web Client"
    
    print_status "Download completed!"
    print_status "Directory structure:"
    echo "  ├── alive-server/     (Database server that interfaces with EPICS alive records)"
    echo "  ├── alive-client/     (API library and clients for the EPICS Alive database server)"
    echo "  └── alive-web/        (Web client for EPICS Alive system)"
    
    print_success "All EPICS Alive components have been successfully downloaded!"
    print_status "You can now proceed with your IOC Monitor implementation."
}

# Execute script / 스크립트 실행
main "$@" 