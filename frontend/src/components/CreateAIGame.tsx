import React, { useState } from "react";

export default function CreateAIGame({ onCreate }: { onCreate: (opts: any) => void }) {
  const [timeControl, setTimeControl] = useState("5+0");
  const [difficulty, setDifficulty] = useState<"easy"|"medium"|"hard">("medium");
  const [color, setColor] = useState<"random"|"white"|"black">("random");

  return (
    <div className="p-4 bg-white dark:bg-gray-800 rounded shadow max-w-md">
      <div className="mb-2">
        <label className="block text-sm">Time Control</label>
        <select className="w-full" value={timeControl} onChange={e=>setTimeControl(e.target.value)}>
          <option value="5+0">5|0</option>
          <option value="3+2">3|2</option>
        </select>
      </div>
      <div className="mb-2">
        <label className="block text-sm">Difficulty</label>
        <select className="w-full" value={difficulty} onChange={e=>setDifficulty(e.target.value as any)}>
          <option value="easy">Easy</option>
          <option value="medium">Medium</option>
          <option value="hard">Hard</option>
        </select>
      </div>
      <div className="mb-2">
        <label className="block text-sm">Color</label>
        <select className="w-full" value={color} onChange={e=>setColor(e.target.value as any)}>
          <option value="random">Random</option>
          <option value="white">Play White</option>
          <option value="black">Play Black</option>
        </select>
      </div>
      <button className="mt-2 px-4 py-2 bg-blue-600 text-white rounded" onClick={()=>onCreate({ ai: true, ai_difficulty: difficulty, color, time_control: timeControl })}>Create AI Game</button>
    </div>
  );
}