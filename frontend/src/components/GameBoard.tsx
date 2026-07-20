import React, { useEffect, useRef, useState } from "react";
import { Chess } from "chess.js";
import { Chessboard } from "react-chessboard";
import SuggestionsPanel from "./HintLayer";

export default function GameBoard({ gameId, token }: { gameId: number, token: string | null }) {
  const [game, setGame] = useState(new Chess());
  const wsRef = useRef<WebSocket | null>(null);
  const [suggestions, setSuggestions] = useState<any[] | null>(null);

  useEffect(() => {
    const base = (import.meta.env.VITE_API_URL || "http://localhost:8000");
    const wsProtocol = base.startsWith("https") ? "wss" : "ws";
    const host = base.replace(/^https?:\/\//, "");
    const tokenParam = token ? `?token=${token}` : "";
    const url = `${wsProtocol}://${host}/ws/games/${gameId}${tokenParam ? `?token=${token}` : ""}`;
    const ws = new WebSocket(url);
    ws.onopen = () => {
      ws.send(JSON.stringify({ type: "join", color: "random" }));
    };
    ws.onmessage = (ev) => {
      const msg = JSON.parse(ev.data);
      if (msg.type === "sync") {
        const c = new Chess();
        c.load(msg.fen);
        setGame(c);
      } else if (msg.type === "move") {
        const c = new Chess(game.fen());
        // convert UCI to from/to/promotion
        const u = msg.uci;
        const from = u.slice(0,2);
        const to = u.slice(2,4);
        const promotion = u.length > 4 ? u.slice(4) : undefined;
        try {
          c.move({ from, to, promotion });
          setGame(new Chess(c.fen()));
        } catch (e) {
          // force reload
          const d = new Chess(msg.fen);
          setGame(d);
        }
      } else if (msg.type === "suggestions") {
        setSuggestions(msg.suggestions || null);
      }
    };
    wsRef.current = ws;
    return () => ws.close();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameId]);

  const onDrop = (source: string, target: string, piece: string) => {
    const move = { from: source, to: target, promotion: "q" as any };
    const c = new Chess(game.fen());
    const res = c.move(move);
    if (res) {
      const uci = `${move.from}${move.to}${move.promotion ? move.promotion : ""}`;
      wsRef.current?.send(JSON.stringify({ type: "move", uci }));
      setGame(new Chess(c.fen()));
      return true;
    }
    return false;
  };

  const applySuggestion = (uci: string) => {
    wsRef.current?.send(JSON.stringify({ type: "move", uci }));
  };

  useEffect(() => {
    let timer: any = null;
    const reset = () => {
      if (timer) clearTimeout(timer);
      timer = setTimeout(()=> {
        wsRef.current?.send(JSON.stringify({ type: "request_suggestions" }));
      }, 90000);
    };
    const events = ["click","mousemove","keydown","touchstart"];
    events.forEach(e=>window.addEventListener(e, reset));
    reset();
    return () => {
      events.forEach(e=>window.removeEventListener(e, reset));
      if (timer) clearTimeout(timer);
    };
  }, []);

  return (
    <div className="relative">
      <div className="max-w-md">
        <Chessboard position={game.fen()} onPieceDrop={(from, to, piece)=>onDrop(from as string, to as string, piece as string)} />
      </div>
      <SuggestionsPanel suggestions={suggestions} onApplyMove={applySuggestion} />
    </div>
  );
}