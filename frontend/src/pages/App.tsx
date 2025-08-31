import { Route, Routes } from "react-router-dom";
import Header from "../components/Header";
import Home from "./Home";
import Login from "./Login";
import Register from "./Register";
import ProtectedRoute from "../components/ProtectedRoute";

export default function App() {
  return (
    <div className="min-h-screen flex flex-col">
      <Header />
      <main className="flex-1">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          {/* 보호 라우트 예시 (마이페이지 등 필요 시 확장) */}
          <Route element={<ProtectedRoute />}>
            {/* <Route path="/mypage" element={<MyPage />} /> */}
          </Route>
        </Routes>
      </main>
      <footer className="text-center text-xs text-gray-500 py-6">© 2025 FX Alert</footer>
    </div>
  );
}
