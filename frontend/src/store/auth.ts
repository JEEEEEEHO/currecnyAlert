import { create } from "zustand";

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  email: string | null;
  login: (payload: { accessToken: string; refreshToken: string; email: string }) => void;
  logout: () => void;
  hydrate: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  email: null,
  login: ({ accessToken, refreshToken, email }) => {
    localStorage.setItem("auth", JSON.stringify({ accessToken, refreshToken, email }));
    set({ accessToken, refreshToken, email });
  },
  logout: () => {
    localStorage.removeItem("auth");
    set({ accessToken: null, refreshToken: null, email: null });
  },
  hydrate: () => {
    const raw = localStorage.getItem("auth");
    if (raw) {
      try {
        const { accessToken, refreshToken, email } = JSON.parse(raw);
        set({ accessToken, refreshToken, email });
      } catch {}
    }
  },
}));
