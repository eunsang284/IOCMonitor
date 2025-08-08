#!/bin/bash

# EPICS IOC Monitor Version Manager
# EPICS IOC 모니터 버전 관리 스크립트
# Centralized version management for all project files
# 모든 프로젝트 파일의 중앙화된 버전 관리
#
# Development Workflow Examples / 개발 워크플로우 예시
# ===================================================
# 1. Bug Fix (버그 수정 후):
#    ./version_manager.sh bump-patch
#    git add . && git commit -m "Fix bug: version 1.0.1" && git tag v1.0.1
#
# 2. New Feature (새 기능 추가 후):
#    ./version_manager.sh bump-minor  
#    git add . && git commit -m "Add new feature: version 1.1.0" && git tag v1.1.0
#
# 3. Major Changes (주요 변경사항 후):
#    ./version_manager.sh bump-major
#    git add . && git commit -m "Major update: version 2.0.0" && git tag v2.0.0
#
# 4. Specific Version (특정 버전으로 설정):
#    ./version_manager.sh update 1.2.3
#    git add . && git commit -m "Release version 1.2.3" && git tag v1.2.3

set -e

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

# Get current version / 현재 버전 가져오기
get_current_version() {
    if [ -f "VERSION" ]; then
        cat VERSION
    else
        echo "1.0.0"
    fi
}

# Update version in all files / 모든 파일에서 버전 업데이트
update_version() {
    local new_version="$1"
    local current_version=$(get_current_version)
    
    print_status "Updating version from ${current_version} to ${new_version}"
    print_status "버전을 ${current_version}에서 ${new_version}로 업데이트합니다"
    
    # Update VERSION file / VERSION 파일 업데이트
    echo "$new_version" > VERSION
    print_success "Updated VERSION file"
    
    # Update package.json / package.json 업데이트
    if [ -f "package.json" ]; then
        sed -i "s/\"version\": \"[^\"]*\"/\"version\": \"$new_version\"/" package.json
        print_success "Updated package.json"
    fi
    
    # Update CHANGELOG.md / CHANGELOG.md 업데이트
    if [ -f "CHANGELOG.md" ]; then
        # Add new version entry if it doesn't exist
        if ! grep -q "## \[$new_version\]" CHANGELOG.md; then
            current_date=$(date +%Y-%m-%d)
            sed -i "5i\\\n## [$new_version] - $current_date\n\n### Added\n- Version $new_version release\n\n" CHANGELOG.md
            print_success "Added new version entry to CHANGELOG.md"
        fi
    fi
    
    # Update script headers / 스크립트 헤더 업데이트
    update_script_headers "$new_version"
    
    print_success "Version update completed successfully!"
    print_success "버전 업데이트가 성공적으로 완료되었습니다!"
}

# Update script headers with version / 스크립트 헤더에 버전 업데이트
update_script_headers() {
    local version="$1"
    
    # Update deploy_web_app.sh / deploy_web_app.sh 업데이트
    if [ -f "deploy_web_app.sh" ]; then
        sed -i "s/EPICS IOC Monitor Web Application Deployment Script v[0-9.]*/EPICS IOC Monitor Web Application Deployment Script v$version/" deploy_web_app.sh
        sed -i "s/EPICS IOC 모니터 웹 애플리케이션 배포 스크립트 v[0-9.]*/EPICS IOC 모니터 웹 애플리케이션 배포 스크립트 v$version/" deploy_web_app.sh
    fi
    
    # Update install_alive.sh / install_alive.sh 업데이트
    if [ -f "install_alive.sh" ]; then
        sed -i "s/EPICS Alive Daemon Installation Script v[0-9.]*/EPICS Alive Daemon Installation Script v$version/" install_alive.sh
        sed -i "s/EPICS Alive Daemon 설치 스크립트 v[0-9.]*/EPICS Alive Daemon 설치 스크립트 v$version/" install_alive.sh
    fi
    
    # Update websocket_ssh_server.py / websocket_ssh_server.py 업데이트
    if [ -f "websocket_ssh_server.py" ]; then
        sed -i "s/WebSocket SSH Server with Paramiko v[0-9.]*/WebSocket SSH Server with Paramiko v$version/" websocket_ssh_server.py
        sed -i "s/Paramiko를 사용한 WebSocket SSH 서버 v[0-9.]*/Paramiko를 사용한 WebSocket SSH 서버 v$version/" websocket_ssh_server.py
    fi
    
    print_success "Updated script headers"
}

# Show current version / 현재 버전 표시
show_version() {
    local version=$(get_current_version)
    echo "EPICS IOC Monitor v$version"
    echo "EPICS IOC 모니터 v$version"
}

# Show version in all files / 모든 파일에서 버전 표시
show_all_versions() {
    print_status "Current versions in all files:"
    print_status "모든 파일의 현재 버전:"
    echo ""
    
    # VERSION file
    if [ -f "VERSION" ]; then
        echo "VERSION: $(cat VERSION)"
    fi
    
    # package.json
    if [ -f "package.json" ]; then
        local pkg_version=$(grep '"version"' package.json | sed 's/.*"version": "\([^"]*\)".*/\1/')
        echo "package.json: $pkg_version"
    fi
    
    # Script headers
    if [ -f "deploy_web_app.sh" ]; then
        local script_version=$(grep "Deployment Script v" deploy_web_app.sh | sed 's/.*v\([0-9.]*\).*/\1/')
        echo "deploy_web_app.sh: $script_version"
    fi
    
    if [ -f "install_alive.sh" ]; then
        local install_version=$(grep "Installation Script v" install_alive.sh | sed 's/.*v\([0-9.]*\).*/\1/')
        echo "install_alive.sh: $install_version"
    fi
    
    if [ -f "websocket_ssh_server.py" ]; then
        local ssh_version=$(grep "Paramiko v" websocket_ssh_server.py | sed 's/.*v\([0-9.]*\).*/\1/')
        echo "websocket_ssh_server.py: $ssh_version"
    fi
}

# Validate version format / 버전 형식 검증
validate_version() {
    local version="$1"
    if [[ $version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        return 0
    else
        print_error "Invalid version format. Use format: X.Y.Z (e.g., 1.0.0)"
        print_error "잘못된 버전 형식입니다. 형식을 사용하세요: X.Y.Z (예: 1.0.0)"
        return 1
    fi
}

# Show usage / 사용법 표시
show_usage() {
    echo "EPICS IOC Monitor Version Manager"
    echo "EPICS IOC 모니터 버전 관리 스크립트"
    echo ""
    echo "Usage: $0 [command] [version]"
    echo ""
    echo "Commands:"
    echo "  show                    - Show current version"
    echo "  show-all                - Show versions in all files"
    echo "  update <version>        - Update version in all files"
    echo "  bump-patch              - Increment patch version (1.0.0 -> 1.0.1)"
    echo "  bump-minor              - Increment minor version (1.0.0 -> 1.1.0)"
    echo "  bump-major              - Increment major version (1.0.0 -> 2.0.0)"
    echo ""
    echo "Examples:"
    echo "  $0 show                 # Show current version"
    echo "  $0 update 1.1.0         # Update to version 1.1.0"
    echo "  $0 bump-patch           # Increment patch version"
    echo "  $0 bump-minor           # Increment minor version"
}

# Bump version / 버전 증가
bump_version() {
    local bump_type="$1"
    local current_version=$(get_current_version)
    local major minor patch
    
    IFS='.' read -r major minor patch <<< "$current_version"
    
    case "$bump_type" in
        "patch")
            patch=$((patch + 1))
            ;;
        "minor")
            minor=$((minor + 1))
            patch=0
            ;;
        "major")
            major=$((major + 1))
            minor=0
            patch=0
            ;;
        *)
            print_error "Invalid bump type. Use: patch, minor, or major"
            return 1
            ;;
    esac
    
    local new_version="$major.$minor.$patch"
    update_version "$new_version"
}

# Main execution / 메인 실행
main() {
    case "$1" in
        "show")
            show_version
            ;;
        "show-all")
            show_all_versions
            ;;
        "update")
            if [ -z "$2" ]; then
                print_error "Version number required for update command"
                print_error "업데이트 명령에는 버전 번호가 필요합니다"
                exit 1
            fi
            if validate_version "$2"; then
                update_version "$2"
            else
                exit 1
            fi
            ;;
        "bump-patch")
            bump_version "patch"
            ;;
        "bump-minor")
            bump_version "minor"
            ;;
        "bump-major")
            bump_version "major"
            ;;
        "-h"|"--help"|"")
            show_usage
            ;;
        *)
            print_error "Unknown command: $1"
            print_error "알 수 없는 명령: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function / 메인 함수 실행
main "$@" 