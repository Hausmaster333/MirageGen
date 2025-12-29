import { useState } from 'react';
import { type Emotion } from './types';
import { Scene } from './components/Scene';
import { Chat } from './components/Chat';

export default function App() {
  const [emotion, setEmotion] = useState<Emotion>('idle');
  return (
    <div className="flex flex-col h-screen w-screen bg-gray-900 overflow-hidden">
      <Scene emotion={emotion} />
      <Chat />
      <div className="mt-4 flex justify-center gap-2 opacity-50 hover:opacity-100 transition-opacity pb-2">
        {(['thinking', 'happy', 'sad'] as Emotion[]).map(emo => (
          <button
            key={emo}
            onClick={() => setEmotion(emo)}
            className="px-3 py-1 bg-gray-800 text-white text-xs rounded-full border border-gray-600 hover:bg-gray-700 capitalize"
          >
            {emo}
          </button>
        ))}
      </div>
    </div>
  );
}
