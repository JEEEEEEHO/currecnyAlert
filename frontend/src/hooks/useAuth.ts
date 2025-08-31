import { useEffect } from "react";
import { useAuth } from "../store/auth";

export function useAuthHydrate() {
  const hydrate = useAuth((s) => s.hydrate);
  useEffect(() => { hydrate(); }, [hydrate]);
}
