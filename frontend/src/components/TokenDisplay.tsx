import { useState, useEffect } from "react";
import { api, TokenUsage } from "@/lib/api";

interface TokenDisplayProps {
  threadId: string | null;
}

export function TokenDisplay({ threadId }: TokenDisplayProps) {
  const [usage, setUsage] = useState<TokenUsage | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (!threadId) {
      setUsage(null);
      return;
    }

    const fetchUsage = async () => {
      setIsLoading(true);
      try {
        const data = await api.getTokenUsage(threadId);
        setUsage(data);
      } catch (error) {
        console.error("Failed to fetch token usage:", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchUsage();

    // Poll every 2 seconds when thread is active
    const interval = setInterval(fetchUsage, 2000);

    return () => clearInterval(interval);
  }, [threadId]);

  if (!threadId || !usage) return null;

  return (
    <div className="flex items-center gap-4 text-xs text-gray-600">
      <div className="flex items-center gap-1">
        <span className="font-medium">Tokens:</span>
        <span className="font-mono">{usage.total_tokens.toLocaleString()}</span>
      </div>
      <div className="flex items-center gap-1 text-gray-500">
        <span>In:</span>
        <span className="font-mono">{usage.input_tokens.toLocaleString()}</span>
      </div>
      <div className="flex items-center gap-1 text-gray-500">
        <span>Out:</span>
        <span className="font-mono">{usage.output_tokens.toLocaleString()}</span>
      </div>
      <div className="flex items-center gap-1 text-gray-500">
        <span>Calls:</span>
        <span className="font-mono">{usage.calls}</span>
      </div>
    </div>
  );
}
