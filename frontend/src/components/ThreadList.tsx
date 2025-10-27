import { Thread } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { PlusIcon } from "@radix-ui/react-icons";

interface ThreadListProps {
  threads: Thread[];
  selectedThreadId: string | null;
  onSelectThread: (threadId: string) => void;
  onCreateThread: () => void;
}

export function ThreadList({
  threads,
  selectedThreadId,
  onSelectThread,
  onCreateThread,
}: ThreadListProps) {
  return (
    <div className="w-80 border-r bg-gradient-to-b from-purple-50 to-blue-50 flex flex-col h-screen">
      <div className="p-4 border-b bg-white/50 backdrop-blur-sm">
        <h2 className="text-lg font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent mb-3">
          💬 Chat Threads
        </h2>
        <Button onClick={onCreateThread} className="w-full bg-gradient-to-r from-purple-500 to-purple-600 hover:from-purple-600 hover:to-purple-700 shadow-md">
          <PlusIcon className="mr-2 h-4 w-4" />
          New Thread
        </Button>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-2">
        {threads.length === 0 ? (
          <p className="text-sm text-gray-500 text-center py-8">
            No threads yet. Create one to get started! ✨
          </p>
        ) : (
          threads.map((thread) => (
            <Card
              key={thread.id}
              className={`p-3 cursor-pointer transition-all duration-200 border-2 ${
                selectedThreadId === thread.id
                  ? "bg-gradient-to-r from-purple-100 to-blue-100 border-purple-300 shadow-md scale-105"
                  : "hover:bg-white hover:shadow-md hover:border-purple-200 border-transparent"
              }`}
              onClick={() => onSelectThread(thread.id)}
            >
              <h3 className="font-semibold text-sm truncate text-gray-800">{thread.name}</h3>
              <p className="text-xs text-gray-500 mt-1">
                {new Date(thread.created_at).toLocaleString()}
              </p>
            </Card>
          ))
        )}
      </div>
    </div>
  );
}
