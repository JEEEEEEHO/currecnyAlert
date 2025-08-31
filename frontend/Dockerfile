# 빌드 스테이지
FROM node:20-alpine AS builder
WORKDIR /app
COPY package.json /app/package.json
COPY package-lock.json /app/package-lock.json 2>/dev/null || true
RUN npm i
COPY . /app
RUN npm run build

# 배포 스테이지 (nginx로 정적 파일 제공)
FROM nginx:1.27-alpine
COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
