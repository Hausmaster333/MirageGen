import { useState } from 'react';
import { Scene } from './components/Scene';
import { Chat } from './components/Chat';
import type { StreamFrame } from './types';

export default function App() {
  const [streamData, setStreamData] = useState<StreamFrame | null>(null);
  const [isThinking, setIsThinking] = useState(false);

  const handleStreamFrame = (frame: StreamFrame) => {
    setStreamData({ ...frame });
  };

  return (
    <div className="flex flex-col h-screen w-screen bg-gray-900 overflow-hidden">
      <Scene streamData={streamData} isThinking={isThinking} />

      <Chat onStreamFrame={handleStreamFrame} onLoading={setIsThinking} />
    </div>
  );
}
