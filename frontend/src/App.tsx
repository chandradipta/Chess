import React, { useState, useEffect } from "react";
import CreateAIGame from "./components/CreateAIGame";
import GameBoard from "./components/GameBoard";

export default function App() {
  const [game, setGame] = useState<{ game_id?: number } | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = localStorage.getItem("token");
    if (t) setToken(t);
  }, []);

  const anonToken = token ?? null;

  return (
    <div className="min-h-screen bg-gray-100 dark:bg-gray-900 text-gray-900 dark:text-gray-100">
      <header className="p-4 flex justify-between items-center">
        <h1 className="text-xl font-bold">Chess App Prototype</h1>
        <div className="flex items-center space-x-3">
          <AuthControls token={token} setToken={setToken} />
          <ThemeToggle />
        </div>
      </header>
      <main className="p-4">
        {!game && (
          <CreateAIGame
            onCreate={async (opts) => {
              const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/games`, {
                method: "POST",
                headers: { "Content-Type": "application/json", ...(token ? { Authorization: `Bearer ${token}` } : {}) },
                body: JSON.stringify(opts)
              });
              const data = await res.json();
              setGame({ game_id: data.game_id });
            }}
          />
        )}
        {game?.game_id && (
          <GameBoard gameId={game.game_id} token={anonToken} />
        )}
      </main>
    </div>
  );
}

function ThemeToggle() {
  const [dark, setDark] = useState(document.documentElement.classList.contains("dark"));
  const toggle = () => {
    document.documentElement.classList.toggle("dark");
    setDark(document.documentElement.classList.contains("dark"));
  };
  return (
    <button onClick={toggle} className="px-3 py-1 border rounded">
      {dark ? "Light" : "Dark"} mode
    </button>
  );
}

function AuthControls({ token, setToken }: { token: string | null, setToken: (t: string | null) => void }) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const signup = async () => {
    const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/auth/signup`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
    }
  };
  const login = async () => {
    const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8000"}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();
    if (data.access_token) {
      localStorage.setItem("token", data.access_token);
      setToken(data.access_token);
    }
  };
  const logout = () => {
    localStorage.removeItem("token");
    setToken(null);
  };

  if (token) {
    return <button onClick={logout} className="px-3 py-1 border rounded">Logout</button>;
  }
  return (
    <div className="flex space-x-2 items-center">
      <input placeholder="username" value={username} onChange={e=>setUsername(e.target.value)} className="px-2 py-1 rounded" />
      <input placeholder="email" value={email} onChange={e=>setEmail(e.target.value)} className="px-2 py-1 rounded" />
      <input placeholder="password" type="password" value={password} onChange={e=>setPassword(e.target.value)} className="px-2 py-1 rounded" />
      <button onClick={signup} className="px-2 py-1 bg-green-600 text-white rounded">Signup</button>
      <button onClick={login} className="px-2 py-1 bg-blue-600 text-white rounded">Login</button>
    </div>
  );
}