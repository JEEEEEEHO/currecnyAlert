# 환율 3년 평균-현재 비교 알림 서비스
#### 💸 https://fx-alert-frontend.vercel.app/
모노레포(backend/ + frontend/)로 구성된 FastAPI + React(TS) 프로젝트입니다.  
**Docker Compose**로 로컬에서 한 번에 실행할 수 있으며, **Celery/Redis**로 평일 09:00/12:00(KST) 스케줄에
환율을 수집/계산하고, **3년 평균보다 현재 환율이 낮으면 이메일 알림**을 보냅니다.

## 빠른 시작 (로컬)

```bash
# 1) 레포 클론 후
cp backend/.env.example backend/.env  # 필요 시 값 수정
docker-compose up --build
```

- 백엔드 API: http://localhost:8000
- 프론트엔드: http://localhost:5173

## 주요 API

- `POST /api/v1/auth/register` : 회원가입 `{ email, password }`
- `POST /api/v1/auth/login` : 로그인 -> `{ access_token, refresh_token }`
- `GET /api/v1/currency/latest` : 현재 환율 + 3년 평균 + 상태(LOW/HIGH)
- `POST /api/v1/notifications/subscribe` : (인증 필요) 구독
- `DELETE /api/v1/notifications/unsubscribe` : (인증 필요) 해제

## 테스트

```bash
# 백엔드
cd backend
pytest -q

# 프론트엔드
cd frontend
npm i
npm test
```

## 배포 (샘플)
- **Frontend**: Vercel (Secrets: `VERCEL_TOKEN`, `VERCEL_ORG_ID`, `VERCEL_PROJECT_ID`)
- **Backend**: Render.com (Secrets: `RENDER_API_KEY`, `RENDER_SERVICE_ID`)
