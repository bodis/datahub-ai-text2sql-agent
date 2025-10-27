import { useState, useEffect } from "react";
import { api, Thread, Message } from "./lib/api";
import { ThreadList } from "./components/ThreadList";
import { ChatInterface } from "./components/ChatInterface";

function App() {
  const [threads, setThreads] = useState<Thread[]>([]);
  const [selectedThreadId, setSelectedThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [sendingMessage, setSendingMessage] = useState(false);

  useEffect(() => {
    loadThreads();
  }, []);

  useEffect(() => {
    if (selectedThreadId) {
      loadMessages(selectedThreadId);
    }
  }, [selectedThreadId]);

  const loadThreads = async () => {
    try {
      const fetchedThreads = await api.getThreads();
      setThreads(fetchedThreads);
    } catch (error) {
      console.error("Failed to load threads:", error);
    } finally {
      setLoading(false);
    }
  };

  const loadMessages = async (threadId: string) => {
    try {
      const fetchedMessages = await api.getMessages(threadId);
      setMessages(fetchedMessages);
    } catch (error) {
      console.error("Failed to load messages:", error);
    }
  };

  const handleCreateThread = async () => {
    try {
      const newThread = await api.createThread();
      setThreads([newThread, ...threads]);
      setSelectedThreadId(newThread.id);
      setMessages([]);
    } catch (error) {
      console.error("Failed to create thread:", error);
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!selectedThreadId) return;

    try {
      setSendingMessage(true);
      const result = await api.sendMessage(selectedThreadId, content);
      setMessages([...messages, result.user_message, result.server_message]);
    } catch (error) {
      console.error("Failed to send message:", error);
    } finally {
      setSendingMessage(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <p className="text-muted-foreground">Loading...</p>
      </div>
    );
  }

  return (
    <div className="flex h-screen">
      <ThreadList
        threads={threads}
        selectedThreadId={selectedThreadId}
        onSelectThread={setSelectedThreadId}
        onCreateThread={handleCreateThread}
      />
      {selectedThreadId ? (
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={sendingMessage}
        />
      ) : (
        <div className="flex-1 flex items-center justify-center bg-gradient-to-br from-purple-50 via-white to-blue-50">
          <div className="text-center">
            <div className="text-8xl mb-6">💬</div>
            <h2 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3">
              Welcome to Chat App
            </h2>
            <p className="text-gray-600 mb-6">
              Select a thread or create a new one to start chatting
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
