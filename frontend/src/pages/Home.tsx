import { useEffect, useState } from "react";
import api from "../api/client";
import { useAuth } from "../store/auth";

/**
 * 백엔드 응답 스키마
 * GET /api/v1/currency/latest
 */
type Latest = {
  base: string;           // 기준 통화 (예: USD)
  target: string;         // 대상 통화 (예: KRW)
  current_rate: number;   // 현재 환율
  avg_3y: number;         // 3년 평균 환율
  status: "LOW" | "HIGH"; // 현재가가 평균보다 낮으면 LOW, 높으면 HIGH
  last_updated: string;   // ISO 문자열
  source: string;         // "db-cache" | "live"
};

export default function Home() {
  const [data, setData] = useState<Latest | null>(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState<string | null>(null);
  const { accessToken } = useAuth();

  // 구독/해제
  const subscribe = async () => {
    await api.post("/notifications/subscribe");
    alert("알림이 활성화되었습니다.");
  };
  const unsubscribe = async () => {
    await api.delete("/notifications/unsubscribe");
    alert("알림이 비활성화되었습니다.");
  };

  // 환율 조회
  useEffect(() => {
    const run = async () => {
      setLoading(true);
      try {
        const res = await api.get<Latest>("/currency/latest");
        setData(res.data);
      } catch (e: any) {
        setErr(e?.response?.data?.detail || "환율 정보를 불러오지 못했습니다.");
      } finally {
        setLoading(false);
      }
    };
    run();
  }, []);

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto px-4 py-16 text-center">
        <div className="inline-block animate-spin rounded-full h-12 w-12 border-t-4 border-b-4 border-blue-500"></div>
        <p className="mt-3 text-sm text-gray-500">불러오는 중...</p>
      </div>
    );
  }

  if (err) {
    return (
      <div className="max-w-3xl mx-auto px-4 py-12">
        <div className="bg-white rounded-2xl shadow p-6 text-center">
          <p className="text-red-600">{err}</p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  // 스크린샷처럼: 현재 < 평균일 때 파란색, 현재 > 평균일 때 빨간색
  const isLower = data.current_rate < data.avg_3y;
  const currentColor = isLower ? "text-blue-600" : "text-red-600";
  const currentBg = isLower ? "bg-blue-50" : "bg-red-50";
  const currentTitle = isLower ? "text-blue-700" : "text-red-700";

  return (
    <div className="max-w-4xl mx-auto px-4 py-10">
      {/* 메인 카드 */}
      <div className="bg-white rounded-2xl shadow-md p-6 sm:p-8">
        {/* 타이틀 */}
        <h2 className="text-center text-xl sm:text-2xl font-semibold text-gray-800">
          {data.base}/{data.target} 환율 정보
        </h2>
        <p className="text-center text-xs sm:text-sm text-gray-400 mt-1">
          마지막 업데이트: {new Date(data.last_updated).toLocaleString()}
        </p>

        {/* 값 2단 */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 sm:gap-6 mt-6">
          {/* 3년 평균 */}
          <div className="bg-gray-50 rounded-xl p-5 text-center">
            <p className="text-sm text-gray-500 mb-2">3년 평균 환율</p>
            <p className="text-3xl font-extrabold text-gray-800">
              {data.avg_3y.toFixed(2)} <span className="text-xl font-bold">원</span>
            </p>
          </div>

          {/* 현재 환율 */}
          <div className={`${currentBg} rounded-xl p-5 text-center`}>
            <p className={`text-sm mb-2 ${currentTitle}`}>현재 환율</p>
            <p className={`text-3xl font-extrabold ${currentColor}`}>
              {data.current_rate.toFixed(2)} <span className="text-xl font-bold">원</span>
            </p>
          </div>
        </div>

        {/* 상태 배너 (카드 하단 전체폭) */}
        <div
          className={`mt-6 rounded-lg px-4 py-3 text-center font-semibold ${
            isLower ? "bg-blue-100 text-blue-800" : "bg-red-100 text-red-800"
          }`}
        >
          {isLower
            ? "현재 환율이 3년 평균보다 낮습니다 (매수 기회!)"
            : "현재 환율이 3년 평균보다 높습니다"}
        </div>
      </div>

      {/* 알림 카드 (로그인 시 표시) */}
      {accessToken ? (
        <div className="bg-white rounded-2xl shadow-md p-6 mt-8 text-center">
          <h3 className="text-lg font-bold text-gray-800 mb-1">환율 변동 알림</h3>
          <p className="text-sm text-gray-600 mb-4">
            현재 환율이 3년 평균보다 낮아질 때 이메일로 알려드립니다.
          </p>
          <div className="flex flex-col sm:flex-row gap-3 justify-center">
            <button
              onClick={subscribe}
              className="px-5 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
            >
              알림 구독
            </button>
            <button
              onClick={unsubscribe}
              className="px-5 py-2.5 rounded-lg bg-gray-200 hover:bg-gray-300 text-gray-800 font-semibold"
            >
              알림 해제
            </button>
          </div>
        </div>
      ) : (
        <p className="text-center text-sm text-gray-500 mt-6">
          로그인 시 알림 구독/해제가 가능합니다.
        </p>
      )}

      {/* 푸터 여백 감안 */}
      <div className="h-4" />
    </div>
  );
}
