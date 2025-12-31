import { useState } from 'react';
import { Scene } from './components/Scene';
import { Chat } from './components/Chat';
import { type ChatResponse } from './types';

export default function App() {
  // Храним последний ответ от API для проигрывания
  const [lastResponse, setLastResponse] = useState<ChatResponse | null>(null);

  // Флаг, говорит аватару "думать" (пока идет запрос)
  const [isThinking, setIsThinking] = useState(false);

  return (
    <div className="flex flex-col h-screen w-screen bg-gray-900 overflow-hidden">
      {/* Передаем данные в сцену */}
      <Scene
        lastResponse={lastResponse}
        isThinking={isThinking}
        onAnimationEnd={() => setLastResponse(null)} // Сброс после окончания
      />

      {/* Чат обновляет эти данные */}
      <Chat
        onResponse={resp => setLastResponse(resp)}
        onLoading={loading => setIsThinking(loading)}
      />
    </div>
  );
}
