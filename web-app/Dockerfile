# EPICS IOC Monitor Web Application Dockerfile
# EPICS IOC 모니터 웹 애플리케이션 Dockerfile

FROM python:3.11-slim

# Set environment variables / 환경 변수 설정
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV FLASK_APP=app.py
ENV FLASK_ENV=production

# Install system dependencies / 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    curl \
    wget \
    git \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Set work directory / 작업 디렉토리 설정
WORKDIR /app

# Copy requirements and install Python dependencies / requirements 복사 및 Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code / 애플리케이션 코드 복사
COPY . .

# Create necessary directories / 필요한 디렉토리 생성
RUN mkdir -p logs cache config static templates

# Create non-root user / 비루트 사용자 생성
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port / 포트 노출
EXPOSE 5000

# Health check / 헬스 체크
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/api/status || exit 1

# Run application / 애플리케이션 실행
CMD ["python", "app.py"] 