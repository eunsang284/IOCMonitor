#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EPICS IOC Monitor Web Application
EPICS IOC 모니터 웹 애플리케이션
Production-ready Flask application for IOC monitoring
IOC 모니터링을 위한 프로덕션 준비된 Flask 애플리케이션
"""

import os
import sys
import time
import threading
import subprocess
import pandas as pd
import signal
import atexit
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from flask import Flask, jsonify, render_template, request, flash, url_for, session, redirect, make_response
from flask_cors import CORS

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import configuration
from config import Config

app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Enable CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://192.168.60.150",
            "http://192.168.60.61:3000",
            "http://localhost:3000",
            "http://127.0.0.1:3000"
        ]
    }
})

# Global variables
cache_data = []
masked_iocs = set()
previous_faulted_iocs = set()
previous_ioc_down_status = {}
prev_ready_val = None
pv_cache = {}

# Admin credentials
ADMIN_CREDENTIALS = {
    "raon": "raon"
}

# Import utilities and services
from services.ioc_monitor import IOCMonitor
from services.pv_service import PVService
from services.log_service import LogService
from services.alive_service import AliveService
from utils.helpers import safe_str, format_uptime



# Initialize services
ioc_monitor = IOCMonitor()
pv_service = PVService()
log_service = LogService()
alive_service = AliveService()

@app.route("/")
def index():
    """Main dashboard page / 메인 대시보드 페이지"""
    return render_template("ioc_dashboard.html")

@app.route("/dashboard")
def dashboard():
    """IOC dashboard page / IOC 대시보드 페이지"""
    return render_template("ioc_dashboard.html")

@app.route("/view/status")
def view_status_page():
    """System status page / 시스템 상태 페이지"""
    return render_template("status.html")

@app.route("/api/status")
def api_status():
    """Get system status / 시스템 상태 조회"""
    alive_running = alive_service.ping_alive_server()
    status = {
        "IOC Monitor Control IOC": "🟢 RUNNING" if ioc_monitor.check_running("./st.cmd") else "🔴 STOPPED",
        "SSH Server": "🟢 RUNNING" if check_ssh_server_status() else "🔴 STOPPED",
        "IOC Info Cache Server": "🟢 RUNNING" if ioc_monitor.check_running("pv_cache.py") else "🔴 STOPPED",
        "IOC Monitor Web Server": "🟢 RUNNING" if ioc_monitor.check_running("app.py") else "🔴 STOPPED",
        "Alive Server": "🟢 RUNNING" if alive_running else "🔴 STOPPED"
    }
    return jsonify(status)

@app.route("/api/ioc_count")
def api_ioc_count():
    """Get IOC count / IOC 개수 조회"""
    ioc_list = alive_service.get_ioc_list()
    return jsonify({"ioc_count": len(ioc_list)})

@app.route("/api/alive/ioc_list")
def api_alive_ioc_list():
    """Get IOC list from Alive server / Alive 서버에서 IOC 목록 조회"""
    ioc_list = alive_service.get_ioc_list()
    return jsonify({"iocs": ioc_list})

@app.route("/api/alive/ioc_details")
def api_alive_ioc_details():
    """Get detailed IOC information from Alive server / Alive 서버에서 상세 IOC 정보 조회"""
    ioc_details = alive_service.get_ioc_details()
    return jsonify(ioc_details)

@app.route("/api/alive/ioc/<ioc_name>")
def api_alive_ioc_detail(ioc_name):
    """Get specific IOC detail from Alive server / Alive 서버에서 특정 IOC 상세 정보 조회"""
    ioc_detail = alive_service.get_ioc_detail(ioc_name)
    if ioc_detail:
        return jsonify(ioc_detail)
    else:
        return jsonify({"error": f"IOC {ioc_name} not found"}), 404

@app.route("/api/alive/status")
def api_alive_status():
    """Get IOC status summary from Alive server / Alive 서버에서 IOC 상태 요약 조회"""
    return jsonify(alive_service.get_status_summary())

@app.route("/api/alive/faulted")
def api_alive_faulted():
    """Get current faulted IOCs information / 현재 장애 IOC 정보"""
    return jsonify(alive_service.get_faulted_iocs_info())

@app.route("/api/ioc_monitor_ready/status")
def api_ioc_monitor_ready_status():
    """Get IOC Monitor Ready status / IOC Monitor Ready 상태 조회"""
    try:
        # Check if PV Control feature is enabled
        if not app.config.get('FEATURE_PV_CONTROL', False):
            return jsonify({
                "enabled": False,
                "message": "PV Control feature is not enabled. Set IOC_MONITOR_PV_CONTROL_ENABLED=true to enable."
            })
        
        status = pv_service.get_ioc_monitor_ready_status()
        return jsonify(status)
        
    except Exception as e:
        return jsonify({
            "enabled": False, 
            "error": f"Failed to get IOC Monitor Ready status: {str(e)}"
        })

@app.route("/api/ioc_monitor_ready/set", methods=["POST"])
def api_ioc_monitor_ready_set():
    """Set IOC Monitor Ready value / IOC Monitor Ready 값 설정"""
    try:
        data = request.get_json()
        value = data.get("value", 1)
        
        success = pv_service.set_control_value(float(value))
        
        if success:
            return jsonify({"success": True, "message": f"Control PV set to {value}"})
        else:
            return jsonify({"success": False, "error": "Failed to set control PV"}), 500
            
    except Exception as e:
        return jsonify({
            "success": False, 
            "error": f"Failed to set IOC Monitor Ready value: {str(e)}"
        }), 500

@app.route("/api/pv/caget/<pvname>")
def api_pv_caget(pvname):
    """Get PV value using caget / caget을 사용하여 PV 값 읽기"""
    try:
        import subprocess
        result = subprocess.run(['caget', pvname], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            # caget 출력 파싱: "PV_NAME value"
            output = result.stdout.strip()
            if ' ' in output:
                pv_name, value = output.split(' ', 1)
                return jsonify({
                    "success": True,
                    "pv": pvname,
                    "value": value,
                    "raw_output": output
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Unexpected caget output format: {output}"
                }), 500
        else:
            return jsonify({
                "success": False,
                "error": f"caget failed: {result.stderr}"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "caget timeout"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get PV value: {str(e)}"
        }), 500

@app.route("/api/pv/caput/<pvname>", methods=["POST"])
def api_pv_caput(pvname):
    """Set PV value using caput / caput을 사용하여 PV 값 설정"""
    try:
        data = request.get_json()
        value = data.get("value")
        
        if value is None:
            return jsonify({
                "success": False,
                "error": "Value is required"
            }), 400
        
        import subprocess
        result = subprocess.run(['caput', pvname, str(value)], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            return jsonify({
                "success": True,
                "pv": pvname,
                "value": value,
                "message": f"PV {pvname} set to {value}",
                "raw_output": result.stdout.strip()
            })
        else:
            return jsonify({
                "success": False,
                "error": f"caput failed: {result.stderr}"
            }), 500
            
    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "error": "caput timeout"
        }), 500
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to set PV value: {str(e)}"
        }), 500

@app.route("/api/data")
def api_data():
    """Get all IOC data / 모든 IOC 데이터 조회"""
    ioc_details = alive_service.get_ioc_details()
    records = []
    
    for ioc_name, info in ioc_details.items():
        record = info.copy()
        record["masked"] = ioc_name in alive_service.masked_iocs
        records.append(record)
    
    return jsonify(records)

@app.route("/api/ip_list")
def api_ip_list():
    """Get IP list from IOC data / IOC 데이터에서 IP 목록 조회"""
    ioc_details = alive_service.get_ioc_details()
    ip_list = sorted({
        info.get("ip_address", "N/A") 
        for info in ioc_details.values() 
        if info.get("ip_address") and info.get("ip_address") != "N/A"
    })
    return jsonify(ip_list)

@app.route("/api/faulted_iocs")
def get_faulted_iocs():
    """Get faulted IOCs / 장애 IOC 조회"""
    try:
        ioc_details = alive_service.get_ioc_details()
        faulted = []
        
        for ioc_name, info in ioc_details.items():
            if info.get("status") == "OFFLINE":
                faulted.append(info)
        
        # 마스크된 IOC 제외
        filtered = [ioc for ioc in faulted if ioc.get("name") not in alive_service.masked_iocs]
        
        return jsonify({
            "count": len(filtered),
            "data": filtered
        })
        
    except Exception as e:
        print(f"[ERROR] /api/faulted_iocs: {e}")
        return jsonify({"error": f"Faulted IOC 분석 실패: {str(e)}"}), 500

@app.route("/api/control_states")
def get_control_states():
    """Get control states / 제어 상태 조회"""
    # 간단한 모니터링 데이터 반환
    ioc_details = alive_service.get_ioc_details()
    online_count = sum(1 for info in ioc_details.values() if info.get("status") == "ONLINE")
    offline_count = sum(1 for info in ioc_details.values() if info.get("status") == "OFFLINE")
    
    monitoring_data = {
        "Online IOCs": online_count,
        "Offline IOCs": offline_count,
        "Total IOCs": len(ioc_details)
    }
    
    return jsonify({
        "monitoring_data": monitoring_data,
        "control_pvs": {}  # 기존 제어 PV 기능은 비활성화
    })

@app.route("/api/ioc_logs/<path:iocname>")
def api_ioc_logs(iocname):
    """Get IOC event logs / IOC 이벤트 로그 조회"""
    logs = alive_service.get_ioc_logs(iocname)
    return jsonify({"logs": logs})

@app.route("/log/<path:iocname>")
def show_log(iocname):
    """Show IOC log page / IOC 로그 페이지 표시"""
    logs = alive_service.get_ioc_logs(iocname)
    info = alive_service.get_ioc_detail(iocname)
    return render_template("log_view.html", ioc_name=iocname, logs=logs, info=info)

@app.route("/view/critical")
def view_critical():
    """View critical IOCs page / 중요 IOC 페이지 표시"""
    ioc_details = alive_service.get_ioc_details()
    faulted = [info for info in ioc_details.values() if info.get("status") == "OFFLINE"]
    return render_template("view_critical.html", iocs=faulted, count=len(faulted))

@app.route("/view/server_log")
def view_server_log():
    """View server log page / 서버 로그 페이지 표시"""
    return render_template("server_log.html")

@app.route("/api/docs")
def api_docs():
    """API documentation page / API 문서 페이지"""
    return render_template("api_docs.html")

@app.route("/api/list")
def api_list():
    """Get all available APIs for MCP / MCP용 모든 사용 가능한 API 목록"""
    apis = {
        "system_status": {
            "endpoint": "/api/status",
            "method": "GET",
            "description": "시스템 상태 조회 (IOC Monitor, SSH Server, Cache Server 등)",
            "response": "JSON",
            "mcp_usage": "시스템 전반적인 상태 모니터링"
        },
        "ioc_count": {
            "endpoint": "/api/ioc_count",
            "method": "GET", 
            "description": "전체 IOC 개수 조회",
            "response": "JSON",
            "mcp_usage": "IOC 총 개수 파악"
        },
        "ioc_list": {
            "endpoint": "/api/alive/ioc_list",
            "method": "GET",
            "description": "Alive 서버에서 IOC 목록 조회",
            "response": "JSON",
            "mcp_usage": "모든 IOC 이름 목록 가져오기"
        },
        "ioc_details": {
            "endpoint": "/api/alive/ioc_details",
            "method": "GET",
            "description": "모든 IOC의 상세 정보 조회",
            "response": "JSON",
            "mcp_usage": "IOC 상태, IP, 업타임 등 상세 정보"
        },
        "ioc_detail": {
            "endpoint": "/api/alive/ioc/<ioc_name>",
            "method": "GET",
            "description": "특정 IOC의 상세 정보 조회",
            "response": "JSON",
            "mcp_usage": "특정 IOC의 상태 및 정보 확인"
        },
        "ioc_status_summary": {
            "endpoint": "/api/alive/status",
            "method": "GET",
            "description": "IOC 상태 요약 정보",
            "response": "JSON",
            "mcp_usage": "IOC 상태 통계 및 요약"
        },
        "faulted_iocs": {
            "endpoint": "/api/alive/faulted",
            "method": "GET",
            "description": "현재 장애 상태인 IOC 정보",
            "response": "JSON",
            "mcp_usage": "장애 IOC 모니터링 및 알림"
        },
        "ioc_monitor_ready_status": {
            "endpoint": "/api/ioc_monitor_ready/status",
            "method": "GET",
            "description": "IOC Monitor Ready 상태 조회",
            "response": "JSON",
            "mcp_usage": "IOC Monitor 제어 상태 확인"
        },
        "ioc_monitor_ready_set": {
            "endpoint": "/api/ioc_monitor_ready/set",
            "method": "POST",
            "description": "IOC Monitor Ready 값 설정",
            "response": "JSON",
            "mcp_usage": "IOC Monitor 제어 값 설정"
        },
        "pv_caget": {
            "endpoint": "/api/pv/caget/<pvname>",
            "method": "GET",
            "description": "PV 값 읽기 (caget 사용)",
            "response": "JSON",
            "mcp_usage": "EPICS PV 값 읽기"
        },
        "pv_caput": {
            "endpoint": "/api/pv/caput/<pvname>",
            "method": "POST",
            "description": "PV 값 설정 (caput 사용)",
            "response": "JSON",
            "mcp_usage": "EPICS PV 값 설정"
        },
        "all_ioc_data": {
            "endpoint": "/api/data",
            "method": "GET",
            "description": "모든 IOC 데이터 (마스크 상태 포함)",
            "response": "JSON",
            "mcp_usage": "전체 IOC 데이터 및 마스크 상태"
        },
        "ip_list": {
            "endpoint": "/api/ip_list",
            "method": "GET",
            "description": "IOC IP 주소 목록",
            "response": "JSON",
            "mcp_usage": "IOC IP 주소 목록 조회"
        },
        "faulted_iocs_detailed": {
            "endpoint": "/api/faulted_iocs",
            "method": "GET",
            "description": "장애 IOC 상세 정보 (마스크 제외)",
            "response": "JSON",
            "mcp_usage": "장애 IOC 상세 분석"
        },
        "control_states": {
            "endpoint": "/api/control_states",
            "method": "GET",
            "description": "제어 상태 및 모니터링 데이터",
            "response": "JSON",
            "mcp_usage": "IOC 모니터링 상태 확인"
        },
        "ioc_logs": {
            "endpoint": "/api/ioc_logs/<iocname>",
            "method": "GET",
            "description": "특정 IOC의 이벤트 로그",
            "response": "JSON",
            "mcp_usage": "IOC 이벤트 로그 분석"
        },
        "all_events": {
            "endpoint": "/api/events",
            "method": "GET",
            "description": "모든 이벤트 캐시",
            "response": "JSON",
            "mcp_usage": "전체 이벤트 데이터"
        },
        "pv_search": {
            "endpoint": "/api/pv/search",
            "method": "GET",
            "description": "PV 검색",
            "response": "JSON",
            "mcp_usage": "EPICS PV 검색"
        },
        "pv_detail": {
            "endpoint": "/api/pv/<pvname>",
            "method": "GET",
            "description": "PV 상세 정보",
            "response": "JSON",
            "mcp_usage": "PV 상세 정보 조회"
        },
        "pv_autocomplete": {
            "endpoint": "/api/pv/autocomplete",
            "method": "GET",
            "description": "PV 자동완성 제안",
            "response": "JSON",
            "mcp_usage": "PV 이름 자동완성"
        },
        "server_log_dates": {
            "endpoint": "/api/server_log_dates",
            "method": "GET",
            "description": "서버 로그 날짜 목록",
            "response": "JSON",
            "mcp_usage": "로그 파일 날짜 목록"
        },
        "server_log_by_date": {
            "endpoint": "/server_log/<date>",
            "method": "GET",
            "description": "특정 날짜의 서버 로그",
            "response": "Text",
            "mcp_usage": "날짜별 서버 로그 조회"
        }
    }
    
    return jsonify({
        "total_apis": len(apis),
        "base_url": "http://192.168.70.235:5001",
        "apis": apis,
        "mcp_integration": {
            "description": "이 API들은 MCP(Model Context Protocol)에서 사용할 수 있습니다.",
            "usage_example": "MCP 클라이언트에서 HTTP 요청을 통해 IOC 모니터 데이터에 접근할 수 있습니다.",
            "authentication": "대부분의 API는 인증이 필요하지 않지만, 일부 관리 기능은 로그인이 필요합니다."
        }
    })

@app.route("/server_log/<date>")
def server_log_by_date(date):
    """Get server log by date / 날짜별 서버 로그 조회"""
    content = alive_service.get_server_log_by_date(date)
    return content, 200, {"Content-Type": "text/plain; charset=utf-8"}

@app.route("/server_log_dates")
def server_log_dates():
    """Get server log dates / 서버 로그 날짜 조회"""
    dates = alive_service.get_server_log_dates()
    return jsonify(dates)

@app.route("/api/events")
def api_events():
    """Get all events from cache / 캐시에서 모든 이벤트 조회"""
    with alive_service._lock:
        if alive_service._cache["all_events"] is not None:
            return jsonify(alive_service._cache["all_events"])
        else:
            return jsonify([])

@app.route("/api/pv/search")
def api_pv_search():
    """Search PVs / PV 검색"""
    q = request.args.get("query", "").lower()
    # 간단한 PV 검색 구현 (실제로는 pvlist 명령어 사용)
    return jsonify({})

@app.route("/api/pv/<pvname>")
def api_pv_detail(pvname):
    """Get PV detail / PV 상세 정보 조회"""
    # 간단한 PV 상세 정보 구현
    return jsonify({"pv": pvname, "ioc": "N/A", "ip": "N/A"})

@app.route("/api/pv/autocomplete")
def api_pv_autocomplete():
    """Get PV autocomplete suggestions / PV 자동완성 제안"""
    q = request.args.get("q", "").lower()
    # 간단한 자동완성 구현
    return jsonify([])

@app.route("/view/pv_search")
def pv_search_view():
    """PV search page / PV 검색 페이지"""
    return render_template("search.html")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    """Admin login / 관리자 로그인"""
    if request.method == "POST":
        uid = request.form.get("username")
        pw = request.form.get("password")
        if ADMIN_CREDENTIALS.get(uid) == pw:
            session["logged_in"] = True
            flash("로그인 성공", "success")
            return redirect(url_for("index"))
        else:
            flash("아이디·비밀번호가 잘못되었습니다.", "danger")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    """Admin logout / 관리자 로그아웃"""
    session.pop("logged_in", None)
    flash("로그아웃 되었습니다.", "info")
    return redirect(url_for("index"))

@app.route("/api/delete", methods=["DELETE"])
def api_delete():
    """Delete IOC / IOC 삭제"""
    if not session.get("logged_in"):
        return jsonify(status="error", message="권한이 없습니다."), 403

    ioc = request.args.get("ioc")
    if not ioc:
        return jsonify(status="error", message="ioc 파라미터가 없습니다."), 400

    try:
        # IOC가 꺼져있는지 확인
        ioc_info = alive_service.get_ioc_detail(ioc)
        if ioc_info and ioc_info.get("status") == "ONLINE":
            return jsonify(status="error", message="IOC가 실행 중입니다. 먼저 중지해주세요."), 400
        
        result = subprocess.run(
            [alive_service.alivectl_path, "-d", ioc],
            capture_output=True, text=True, check=True
        )
        
        # 삭제 성공 시 로그 기록
        alive_service._log_server_event("DELETE", f"IOC {ioc} deleted from Alive server")
        
        return jsonify(status="ok", output=result.stdout.strip())
    except subprocess.CalledProcessError as e:
        return jsonify(status="error", message=e.stderr.strip()), 500

@app.route("/api/toggle_mask", methods=["POST"])
def api_toggle_mask():
    """Toggle IOC mask / IOC 마스크 토글"""
    if not session.get("logged_in"):
        return jsonify(status="error", message="권한이 없습니다."), 403
    
    data = request.get_json() or {}
    ioc = data.get("ioc")
    if not ioc:
        return jsonify(status="error", message="ioc 파라미터가 없습니다."), 400
    
    if ioc in alive_service.masked_iocs:
        alive_service.masked_iocs.remove(ioc)
        action = "unmasked"
        alive_service._log_server_event("UNMASK", f"IOC {ioc} unmasked")
    else:
        alive_service.masked_iocs.add(ioc)
        action = "masked"
        alive_service._log_server_event("MASK", f"IOC {ioc} masked")
    
    return jsonify(status="ok", action=action)

@app.route("/api/unmask_all", methods=["POST"])
def api_unmask_all():
    """Unmask all IOCs / 모든 IOC 마스크 해제"""
    if not session.get("logged_in"):
        return jsonify(status="error", message="권한이 없습니다."), 403
    
    alive_service.masked_iocs.clear()
    return jsonify(status="ok")

@app.route("/api/ssh/<ioc_name>")
def api_ssh_connect(ioc_name):
    """SSH connection to IOC / IOC에 SSH 접속"""
    if not session.get("logged_in"):
        return jsonify(status="error", message="권한이 없습니다."), 403
    
    try:
        # IOC 정보 가져오기
        ioc_info = alive_service.get_ioc_detail(ioc_name)
        if not ioc_info:
            return jsonify(status="error", message="IOC를 찾을 수 없습니다."), 404
        
        ip_address = ioc_info.get("ip_address", "")
        if not ip_address or ip_address == "N/A":
            return jsonify(status="error", message="IP 주소를 찾을 수 없습니다."), 400
        
        # WebSocket SSH URL 생성 / Generate WebSocket SSH URL
        ws_ssh_url = f"ws://192.168.70.235:8022/ssh/{ip_address}"
        
        return jsonify({
            "status": "ok",
            "ws_ssh_url": ws_ssh_url,
            "ip_address": ip_address,
            "message": f"WebSocket SSH 연결: {ws_ssh_url}"
        })
        
    except Exception as e:
        return jsonify(status="error", message=f"SSH 연결 실패: {str(e)}"), 500

@app.route("/terminal/<ioc_name>")
def ssh_terminal(ioc_name):
    """Render SSH terminal page / SSH 터미널 페이지 렌더링"""
    if not session.get("logged_in"):
        return redirect(url_for("admin_login"))
    
    try:
        ioc_info = alive_service.get_ioc_detail(ioc_name)
        if not ioc_info:
            abort(404)
        
        ip_address = ioc_info.get("ip_address", "")
        if not ip_address or ip_address == "N/A":
            abort(400, description="IP 주소를 찾을 수 없습니다.")
        
        return render_template(
            "ssh/terminal.html",
            ioc_name=ioc_name,
            ip_address=ip_address,
            ws_url=f"ws://192.168.70.235:8022/ssh/{ip_address}"
        )
    except Exception as e:
        app.logger.error(f"Error rendering SSH terminal: {e}")
        abort(500)

@app.errorhandler(404)
def not_found_error(error):
    """404 error handler / 404 오류 처리"""
    return render_template("errors/404.html"), 404

@app.errorhandler(500)
def internal_error(error):
    """500 error handler / 500 오류 처리"""
    return render_template("errors/500.html"), 500

def check_ssh_server_status():
    """Check if SSH server is running / SSH 서버 실행 상태 확인"""
    try:
        pid_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "websocket_ssh.pid")
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())
            # Check if process is running / 프로세스가 실행 중인지 확인
            os.kill(pid, 0)  # This will raise OSError if process doesn't exist
            return True
    except (OSError, ValueError, FileNotFoundError):
        pass
    return False

def log_server_shutdown():
    """Log server shutdown message / 서버 종료 메시지 로그"""
    try:
        log_file = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        shutdown_message = f"{timestamp} IOC-MONITOR-SERVER SHUTDOWN 192.168.70.235 0\n"
        
        with open(log_file, "a") as f:
            f.write(shutdown_message)
        
        print(f"[INFO] Server shutdown logged: {shutdown_message.strip()}")
    except Exception as e:
        print(f"[ERROR] Failed to log server shutdown: {e}")

def signal_handler(signum, frame):
    """Handle shutdown signals / 종료 시그널 처리"""
    print(f"\n[INFO] Received signal {signum}, shutting down gracefully...")
    print("[INFO] Stopping Alive service monitoring...")
    alive_service.log_server_shutdown()
    alive_service.stop_monitoring()
    log_server_shutdown()
    print("[INFO] Server shutdown complete.")
    sys.exit(0)

def start_background_threads():
    """Start background monitoring threads / 백그라운드 모니터링 스레드 시작"""
    print("Starting Alive service monitoring...")
    alive_service.start_monitoring()
    
    # Start IOC Monitor Ready control logic thread only if PV Control is enabled
    if app.config.get('FEATURE_PV_CONTROL', False):
        def run_control_logic():
            while True:
                try:
                    pv_service.apply_control_logic()
                    time.sleep(0.1)  # 100ms 간격으로 체크
                except Exception as e:
                    print(f"[ERROR] Control logic error: {e}")
                    time.sleep(1)
        
        control_thread = threading.Thread(target=run_control_logic, daemon=True)
        control_thread.start()
        print("Started IOC Monitor Ready control logic thread")
    else:
        print("PV Control feature is disabled. Set IOC_MONITOR_PV_CONTROL_ENABLED=true to enable.")

if __name__ == "__main__":
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    # Register atexit handler as backup
    atexit.register(log_server_shutdown)
    
    # Log server startup
    try:
        log_file = "/home/ctrluser/Apps/IOC_Monitor/logs/events.txt"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        startup_message = f"{timestamp} IOC-MONITOR-SERVER STARTUP 192.168.70.235 0\n"
        
        with open(log_file, "a") as f:
            f.write(startup_message)
        
        print(f"[INFO] Server startup logged: {startup_message.strip()}")
    except Exception as e:
        print(f"[ERROR] Failed to log server startup: {e}")
    
    # Display version information / 버전 정보 표시
    try:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'VERSION'), 'r') as f:
            version = f.read().strip()
    except:
        version = "1.0.0"
    
    print(f"EPICS IOC Monitor v{version}")
    print(f"EPICS IOC 모니터 v{version}")
    print(f"Starting server on 0.0.0.0:5001")
    print(f"서버를 0.0.0.0:5001에서 시작합니다")
    
    start_background_threads()
    app.run(debug=True, host="0.0.0.0", port=5001, use_reloader=False) 