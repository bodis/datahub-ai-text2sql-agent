import { useState, useEffect, useRef } from "react";
import { Message } from "@/lib/api";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { PaperPlaneIcon, ReloadIcon } from "@radix-ui/react-icons";
import { DataSourceBadges } from "./DataSourceBadges";
import { TokenDisplay } from "./TokenDisplay";
import { DebugPanel } from "./DebugPanel";

interface ChatInterfaceProps {
  threadId: string;
  messages: Message[];
  onSendMessage: (content: string) => Promise<void>;
  isLoading?: boolean;
}

export function ChatInterface({ threadId, messages, onSendMessage, isLoading = false }: ChatInterfaceProps) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      const message = input;
      setInput("");
      await onSendMessage(message);
    }
  };

  return (
    <div className="flex-1 flex flex-col h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <div className="border-b bg-white/70 backdrop-blur-sm px-6 py-4">
        <div className="flex items-center justify-between gap-4 mb-3">
          <h1 className="text-xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
            💬 Chat Interface
          </h1>
          <DataSourceBadges />
        </div>
        <TokenDisplay threadId={threadId} />
      </div>
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <p className="text-lg font-semibold text-gray-700 mb-2">
                Start a Conversation
              </p>
              <p className="text-sm text-gray-500">
                Send a message to begin chatting!
              </p>
            </div>
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={`flex ${
                message.sender === "user" ? "justify-end" : "justify-start"
              }`}
            >
              <div
                className={`max-w-[70%] rounded-2xl px-4 py-3 shadow-sm ${
                  message.sender === "user"
                    ? "bg-gradient-to-br from-purple-500 to-purple-600 text-white"
                    : "bg-gradient-to-br from-blue-50 to-blue-100 text-gray-900 border border-blue-200"
                }`}
              >
                <p className="text-xs font-semibold mb-2 opacity-80">
                  {message.sender === "user" ? "You" : "🤖 Server"}
                </p>
                <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>
                <div className="flex items-center justify-between mt-2">
                  <p className="text-xs opacity-60">
                    {new Date(message.created_at).toLocaleTimeString()}
                  </p>
                  {message.debug_info && message.debug_info.length > 0 && (
                    <DebugPanel debugInfo={message.debug_info} />
                  )}
                </div>
              </div>
            </div>
          ))
        )}
        {isLoading && (
          <div className="flex justify-start">
            <div className="max-w-[70%] rounded-2xl px-4 py-3 shadow-sm bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200">
              <p className="text-xs font-semibold mb-2 opacity-80 text-gray-900">🤖 Server</p>
              <div className="flex items-center gap-2">
                <ReloadIcon className="h-4 w-4 animate-spin text-blue-600" />
                <p className="text-sm text-gray-900">Typing...</p>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <div className="border-t p-4 bg-white/70 backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="flex gap-3 max-w-4xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            className="flex-1 border-2 border-purple-200 focus:border-purple-400 rounded-xl shadow-sm"
            disabled={isLoading}
          />
          <Button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 shadow-md px-6 rounded-xl"
          >
            {isLoading ? (
              <ReloadIcon className="h-4 w-4 animate-spin" />
            ) : (
              <PaperPlaneIcon className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
