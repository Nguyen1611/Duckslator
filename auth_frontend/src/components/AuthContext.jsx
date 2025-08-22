import { createContext, useCallback, useContext, useEffect, useState } from 'react';

const AuthContext = createContext({
  isLoggedIn: false,
  user: null,
  loading: true,
  refresh: async () => {},
  setAuthenticated: (user) => {},
  setLoggedOut: () => {},
});

export function AuthProvider({ children }) {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const BASE_URL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8001';

  const refresh = useCallback(async () => {
    try {
      setLoading(true);
      // Get token from localStorage (for normal login) or cookie (for Google OAuth)
      const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
      const headers = new Headers();
      
      // If we have a token in localStorage, use it
      if (token) {
        headers.set('Authorization', `Bearer ${token}`);
      }
      // Otherwise, rely on the cookie (for Google OAuth)
      
      const resp = await fetch(`${BASE_URL}/auth/me`, {
        credentials: 'include',
        headers,
      });
      if (!resp.ok) throw new Error('unauth');
      const data = await resp.json();
      setIsLoggedIn(true);
      setUser(data);
    } catch {
      setIsLoggedIn(false);
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, [BASE_URL]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const setAuthenticated = (u) => {
    setIsLoggedIn(true);
    setUser(u || user);
  };

  const setLoggedOut = () => {
    setIsLoggedIn(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ isLoggedIn, user, loading, refresh, setAuthenticated, setLoggedOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}


