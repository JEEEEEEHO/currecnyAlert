// axios 인스턴스: 인증 토큰을 자동으로 헤더에 첨부
import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1",
});

api.interceptors.request.use((config) => {
  const raw = localStorage.getItem("auth");
  if (raw) {
    try {
      const { accessToken } = JSON.parse(raw);
      if (accessToken) config.headers["Authorization"] = `Bearer ${accessToken}`;
    } catch {}
  }
  return config;
});

export default api;
