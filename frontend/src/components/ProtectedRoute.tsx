import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../store/auth";
import { useEffect } from "react";

export default function ProtectedRoute() {
  const { accessToken, hydrate } = useAuth();
  useEffect(() => { hydrate(); }, [hydrate]);
  if (!accessToken) return <Navigate to="/login" replace />;
  return <Outlet />;
}
