import React from "react";

export function useInactivityHint(ws: WebSocket | null, onRequestHint?: () => void) {
  // placeholder hook (GameBoard has inline timer in this scaffold)
  return { suggestions: null, resetTimer: () => {} };
}

export default function SuggestionsPanel({ suggestions, onApplyMove }: { suggestions: any[] | null, onApplyMove: (uci: string) => void }) {
  if (!suggestions || suggestions.length === 0) return null;
  return (
    <div className="absolute right-4 bottom-20 w-72 bg-white dark:bg-gray-800 rounded shadow p-2 z-50">
      <div className="text-sm font-semibold mb-2">Hints</div>
      {suggestions.map((s, i) => (
        <div key={i} className="mb-1 p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700">
          <div className="flex justify-between">
            <div className="text-sm">{s.move}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">
              {s.score ? (s.score.mate ? `M${s.score.mate}` : `${s.score.cp} cp`) : ""}
            </div>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400">{(s.pv || []).slice(0,4).join(" ")}</div>
          <div className="mt-1">
            <button className="text-xs px-2 py-1 mr-2 bg-blue-500 text-white rounded" onClick={()=>onApplyMove(s.move)}>Apply</button>
          </div>
        </div>
      ))}
    </div>
  );
}