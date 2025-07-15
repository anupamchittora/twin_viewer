import React from 'react';

interface ChatMessage {
  type: 'user' | 'bot';
  content: string;
}

interface ChatLayoutProps {
  messages: ChatMessage[];
  kql: string;
  onReset: () => void;
  isLoading: boolean;
}

const ChatLayout: React.FC<ChatLayoutProps> = ({ messages, kql, onReset, isLoading }) => {
  return (
    <div className="max-w-3xl mx-auto p-6 text-white">
      <h1 className="text-3xl font-bold mb-2 text-white">
        🎙️ Azure Voice → KQL → ADX → TTS Chatbot
      </h1>
      <p className="text-gray-400 mb-6">
        Speak your query and get smart KQL-generated summaries from Azure Data Explorer, in a chat-like interface.
      </p>

      <button
        onClick={onReset}
        className="mb-6 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md shadow"
      >
        🔁 Reset Session
      </button>

      {/* Chat Messages */}
      <div className="flex flex-col gap-4 mb-8">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`rounded-2xl px-5 py-3 shadow-md max-w-[80%] ${
              msg.type === 'user'
                ? 'self-end bg-blue-600 text-white text-right'
                : 'self-start bg-gray-200 text-black text-left'
            }`}
          >
            {msg.content}
          </div>
        ))}
      </div>

      {/* Loading Spinner */}
      {isLoading && (
        <div className="mt-4 flex items-center space-x-2 text-lg font-semibold text-gray-300 animate-pulse">
          <div className="w-5 h-5 border-2 border-blue-500 border-dashed rounded-full animate-spin" />
          <span>🤖 Thinking...</span>
        </div>
      )}

      {/* KQL Display */}
      {kql && (
        <div className="bg-gray-900 rounded-xl p-4 mt-6">
          <h3 className="text-lg font-semibold text-yellow-400 mb-2">📜 Generated KQL</h3>
          <pre className="overflow-x-auto text-sm text-green-200 whitespace-pre-wrap">{kql}</pre>
        </div>
      )}
    </div>
  );
};

export default ChatLayout;
