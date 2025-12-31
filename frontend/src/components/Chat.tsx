import { useState, type KeyboardEvent } from 'react';
import type { Message, ChatResponse } from '../types';

interface ChatProps {
  onResponse: (response: ChatResponse) => void;
  onLoading: (isLoading: boolean) => void;
}

export const Chat = ({ onResponse, onLoading }: ChatProps) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const API_URL = import.meta.env.VITE_API_URL;
  const handleSendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userText = inputValue;
    setMessages(prev => [...prev, { text: userText, sender: 'user' }]);
    setInputValue('');

    setIsLoading(true);
    onLoading(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userText }),
      });

      if (!res.ok) throw new Error('API Error');

      const data: ChatResponse = await res.json();

      setMessages(prev => [...prev, { text: data.full_text, sender: 'bot' }]);
      onResponse(data);
    } catch (error) {
      console.error(error);
      setMessages(prev => [
        ...prev,
        { text: 'Ошибка связи с сервером :(', sender: 'bot' },
      ]);
    } finally {
      setIsLoading(false);
      onLoading(false);
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') handleSendMessage();
  };
  return (
    <div className="w-full max-w-2xl mx-auto p-6 z-10 mb-8">
      <div className="bg-gray-800/40 backdrop-blur-xl rounded-2xl shadow-2xl overflow-hidden border border-white/10 ring-1 ring-white/5">
        <div className="p-4 flex gap-3 items-center">
          <input
            disabled={isLoading}
            type="text"
            value={inputValue}
            onChange={e => setInputValue(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Спроси аватара..."
            className="
            flex-1
            bg-gray-900/60
            text-gray-100
            placeholder-gray-400
            border border-gray-700/50
            rounded-xl
            px-5 py-3
            text-base
            focus:outline-none
            focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50
            transition-all duration-200
            shadow-inner
          "
          />

          <button
            onClick={handleSendMessage}
            className="
            bg-linear-to-r from-purple-600 to-indigo-600
            hover:from-purple-500 hover:to-indigo-500
            active:scale-95
            text-white
            shadow-lg shadow-purple-500/20
            rounded-xl
            p-3
            transition-all duration-200
            flex items-center justify-center
            group
          "
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              viewBox="0 0 24 24"
              fill="currentColor"
              className="w-6 h-6 transform group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-transform"
            >
              <path d="M3.478 2.405a.75.75 0 00-.926.94l2.432 7.905H13.5a.75.75 0 010 1.5H4.984l-2.432 7.905a.75.75 0 00.926.94 60.519 60.519 0 0018.445-8.986.75.75 0 000-1.218A60.517 60.517 0 003.478 2.405z" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
};
