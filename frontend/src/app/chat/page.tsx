'use client';

import { useState, FormEvent } from 'react';

type Source = {
  page_content: string;
  metadata: Record<string, unknown>;
};

type Message = {
  text: string;
  sender: 'user' | 'bot';
  sources?: Source[];
};

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { text: input, sender: 'user' };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: input }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.statusText}`);
      }

      const data = await response.json();
      const botMessage: Message = {
        text: data.answer,
        sender: 'bot',
        sources: data.sources,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (error) {
      const errorMessage: Message = {
        text: `Sorry, something went wrong. ${error instanceof Error ? error.message : ''}`,
        sender: 'bot',
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-screen max-w-2xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4 text-center">RAG Chat</h1>
      <div className="flex-grow overflow-y-auto bg-gray-100 p-4 rounded-lg mb-4">
        {messages.map((msg, index) => (
          <div key={index} className={`chat ${msg.sender === 'user' ? 'chat-end' : 'chat-start'}`}>
            <div className="chat-bubble">
              <p>{msg.text}</p>
              {msg.sender === 'bot' && msg.sources && (
                <div className="mt-2 text-xs text-gray-500">
                  <h4 className="font-bold">Sources:</h4>
                  {msg.sources.map((source, i) => (
                    <div key={i} className="mt-1 p-2 bg-gray-200 rounded">
                      <p className="truncate">{source.page_content}</p>
                      <pre className="text-xs mt-1 bg-gray-300 p-1 rounded">{JSON.stringify(source.metadata, null, 2)}</pre>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="chat chat-start">
            <div className="chat-bubble">Typing...</div>
          </div>
        )}
      </div>
      <form onSubmit={handleSubmit} className="flex">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          className="input input-bordered flex-grow"
          placeholder="Ask anything..."
          disabled={isLoading}
        />
        <button type="submit" className="btn btn-primary ml-2" disabled={isLoading}>
          Send
        </button>
      </form>
    </div>
  );
}
