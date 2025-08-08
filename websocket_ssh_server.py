#!/usr/bin/env python3
"""
WebSocket SSH Server with Paramiko v1.0.1
Paramiko를 사용한 WebSocket SSH 서버 v1.0.1
"""

import asyncio
import websockets
import json
import logging
import os
import signal
import sys
from datetime import datetime
import paramiko
import threading
import base64

# Configure logging / 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('websocket_ssh.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SSHClient:
    def __init__(self, websocket, host, username, password):
        self.websocket = websocket
        self.host = host
        self.username = username
        self.password = password
        self.ssh = paramiko.SSHClient()
        self.ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.chan = None
        self.running = False

    async def connect(self):
        """SSH 연결 설정"""
        try:
            self.ssh.connect(
                self.host,
                username=self.username,
                password=self.password,
                timeout=10
            )
            self.chan = self.ssh.invoke_shell(term='xterm')
            self.chan.settimeout(0)
            self.running = True
            
            # 읽기/쓰기 스레드 시작
            threading.Thread(target=self._read_ssh, daemon=True).start()
            
            return True
        except paramiko.AuthenticationException:
            logger.error(f"SSH authentication failed for user {self.username}")
            await self.websocket.send(json.dumps({
                "type": "error",
                "message": "비밀번호가 틀렸습니다. / Password is incorrect."
            }))
            return False
        except paramiko.SSHException as e:
            logger.error(f"SSH connection error: {e}")
            await self.websocket.send(json.dumps({
                "type": "error",
                "message": f"SSH 연결 오류: {str(e)}"
            }))
            return False
        except Exception as e:
            logger.error(f"SSH connection error: {e}")
            await self.websocket.send(json.dumps({
                "type": "error",
                "message": f"SSH 연결 실패: {str(e)}"
            }))
            return False

    def _read_ssh(self):
        """SSH 출력 읽기"""
        import time
        import queue
        
        # 메시지 큐 생성
        message_queue = queue.Queue()
        
        # 메시지 전송 함수
        def send_message():
            try:
                while self.running:
                    try:
                        message = message_queue.get(timeout=0.1)
                        # 새 이벤트 루프 생성하여 메시지 전송
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            loop.run_until_complete(self.websocket.send(message))
                        finally:
                            loop.close()
                    except queue.Empty:
                        continue
                    except Exception as e:
                        logger.error(f"Failed to send message: {e}")
                        break
            except Exception as e:
                logger.error(f"Message sender error: {e}")
        
        # 메시지 전송 스레드 시작
        import threading
        sender_thread = threading.Thread(target=send_message, daemon=True)
        sender_thread.start()
        
        try:
            while self.running and self.chan:
                if self.chan.recv_ready():
                    data = self.chan.recv(1024)
                    if len(data) == 0:
                        break
                    
                    # 메시지를 큐에 추가
                    message = data.decode('utf-8', errors='ignore')
                    message_queue.put(message)
                else:
                    time.sleep(0.1)
        except Exception as e:
            logger.error(f"SSH read error: {e}")
        finally:
            self.running = False
            self.close()

    def write(self, data):
        """SSH로 데이터 쓰기"""
        if self.chan and self.running:
            try:
                self.chan.send(data)
            except Exception as e:
                logger.error(f"SSH write error: {e}")
                self.close()

    def resize(self, cols, rows):
        """터미널 크기 조정"""
        if self.chan and self.running:
            try:
                self.chan.resize_pty(width=cols, height=rows)
            except Exception as e:
                logger.error(f"SSH resize error: {e}")

    def close(self):
        """SSH 연결 종료"""
        self.running = False
        if self.chan:
            self.chan.close()
        self.ssh.close()

class WebSocketSSHServer:
    def __init__(self, host='0.0.0.0', port=8022):
        self.host = host
        self.port = port
        self.clients = {}
        self.running = False
        
    async def handle_connection(self, websocket, path):
        """WebSocket 연결 처리"""
        client_id = id(websocket)
        self.clients[client_id] = websocket
        ssh_client = None
        
        try:
            logger.info(f"Client {client_id} connected from {websocket.remote_address} on path {path}")
            
            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get("type", "")
                    
                    if msg_type == "auth":
                        # SSH 연결 시작
                        username = data.get("username")
                        password = data.get("password")
                        host = data.get("host")
                        
                        if not host:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": "Host 정보가 필요합니다."
                            }))
                            continue
                        
                        logger.info(f"Starting SSH connection to {host} for user {username}")
                        ssh_client = SSHClient(websocket, host, username, password)
                        if await ssh_client.connect():
                            logger.info(f"SSH connection established for client {client_id} to {host}")
                        else:
                            ssh_client = None
                            
                    elif msg_type == "input" and ssh_client:
                        # 키 입력 처리
                        ssh_client.write(data.get("data", ""))
                        
                    elif msg_type == "resize" and ssh_client:
                        # 터미널 크기 조정
                        cols = data.get("cols", 80)
                        rows = data.get("rows", 24)
                        ssh_client.resize(cols, rows)
                        
                except json.JSONDecodeError:
                    logger.error("Invalid JSON message")
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON format"
                    }))
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client {client_id} disconnected")
        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}")
        finally:
            if ssh_client:
                ssh_client.close()
            del self.clients[client_id]
    
    async def start_server(self):
        """WebSocket 서버 시작"""
        self.running = True
        
        # PID 파일 작성
        with open('websocket_ssh.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"Starting WebSocket SSH server on {self.host}:{self.port}")
        
        try:
            # websockets 라이브러리 버전에 따른 호환성 처리
            import websockets.server as ws_server
            
            async def handler(websocket, path):
                await self.handle_connection(websocket, path)
            
            server = await ws_server.serve(handler, self.host, self.port)
            logger.info(f"WebSocket SSH server is running on ws://{self.host}:{self.port}")
            
            while self.running:
                await asyncio.sleep(1)
            
            server.close()
            await server.wait_closed()
                    
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """리소스 정리"""
        self.running = False
        
        # 모든 클라이언트 연결 종료
        for client_id, websocket in self.clients.items():
            try:
                asyncio.run_coroutine_threadsafe(
                    websocket.close(),
                    asyncio.get_event_loop()
                )
            except:
                pass
        
        # PID 파일 제거
        try:
            os.remove('websocket_ssh.pid')
        except FileNotFoundError:
            pass
        
        logger.info("WebSocket SSH server stopped")

def signal_handler(signum, frame):
    """종료 시그널 처리"""
    logger.info(f"Received signal {signum}, shutting down...")
    sys.exit(0)

async def main():
    """메인 함수"""
    # Display version information / 버전 정보 표시
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
    except:
        version = "1.0.0"
    
    print(f"EPICS IOC Monitor WebSocket SSH Server v{version}")
    print(f"EPICS IOC 모니터 WebSocket SSH 서버 v{version}")
    print(f"Starting WebSocket SSH server on 0.0.0.0:8022")
    print(f"WebSocket SSH 서버를 0.0.0.0:8022에서 시작합니다")
    
    # 시그널 핸들러 등록
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # 서버 생성 및 시작
    server = WebSocketSSHServer()
    await server.start_server()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1) 