import { FormEvent, useState } from "react";
import api from "../api/client";
import { Link, useNavigate } from "react-router-dom";

export default function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await api.post("/auth/register", { email, password });
      alert("회원가입 성공! 로그인 페이지로 이동합니다.");
      navigate("/login");
    } catch (e: any) {
      setError(e.response?.data?.detail || "회원가입 실패");
    }
  };

  return (
    <div className="max-w-md mx-auto px-4 py-8">
      <h1 className="text-2xl font-bold mb-4">회원가입</h1>
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
        <button className="w-full py-2 rounded-lg bg-gray-900 text-white">가입하기</button>
        <p className="text-sm text-gray-500">
          이미 계정이 있나요? <Link to="/login" className="text-blue-600">로그인</Link>
        </p>
      </form>
    </div>
  );
}
