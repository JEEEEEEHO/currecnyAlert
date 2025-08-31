# 베이스 이미지로 슬림한 Python 3.11 사용
FROM python:3.11-slim

# 시스템 의존성 설치 (예: 빌드 도구, curl 등)
RUN apt-get update && apt-get install -y build-essential curl && rm -rf /var/lib/apt/lists/*

# 워킹 디렉토리
WORKDIR /app

# 파이썬 의존성 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 앱 코드 복사
COPY app /app/app
COPY .env.example /app/.env.example

# Uvicorn으로 FastAPI 실행 (환경파일은 docker-compose가 주입)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
