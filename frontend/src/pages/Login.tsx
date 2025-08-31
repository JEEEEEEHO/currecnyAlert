import { FormEvent, useState, useEffect } from "react";
import api from "../api/client";
import { useAuth } from "../store/auth";
import { Link, useNavigate } from "react-router-dom";

export default function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const loginStore = useAuth((s) => s.login);
  const hydrate = useAuth((s) => s.hydrate);
  const navigate = useNavigate();

  useEffect(() => { hydrate(); }, [hydrate]);

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      const res = await api.post("/auth/login", { email, password });
      loginStore({ accessToken: res.data.access_token, refreshToken: res.data.refresh_token, email });
      navigate("/");
    } catch (e: any) {
      setError(e.response?.data?.detail || "로그인 실패");
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">로그인</h1>
      <form onSubmit={onSubmit} className="bg-white p-6 rounded-2xl shadow space-y-4">
        <div>
          <label className="block text-sm text-gray-600 mb-1">이메일</label>
          <input className="w-full border rounded-lg px-3 py-2" value={email} onChange={(e)=>setEmail(e.target.value)} />
        </div>
        <div>
          <label className="block text-sm text-gray-600 mb-1">비밀번호</label>
          <input type="password" className="w-full border rounded-lg px-3 py-2" value={password} onChange={(e)=>setPassword(e.target.value)} />
        </div>
        {error && <p className="text-red-600 text-sm">{error}</p>}
        <button className="w-full py-2 rounded-lg bg-blue-600 text-white">로그인</button>
        <p className="text-sm text-gray-500">
          아직 계정이 없나요? <Link to="/register" className="text-blue-600">회원가입</Link>
        </p>
      </form>
    </div>
  );
}
