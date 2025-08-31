import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../store/auth";

export default function Header() {
  const { accessToken, email, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <header className="bg-white border-b sticky top-0 z-10">
      <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between">
        <Link to="/" className="font-bold text-lg">환율 알림</Link>
        <nav className="flex items-center gap-3">
          {accessToken ? (
            <>
              <span className="text-sm text-gray-600">{email}</span>
              <button onClick={handleLogout} className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm">
                로그아웃
              </button>
            </>
          ) : (
            <div className="flex items-center gap-2">
              <Link to="/login" className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-sm">로그인</Link>
              <Link to="/register" className="px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 text-sm">회원가입</Link>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}
