import { useState, useEffect } from "react";
import { api, DataSource } from "@/lib/api";

interface DataSourceBadgesProps {
  threadId?: string;
  messageCount?: number; // Add this to trigger refresh when messages change
}

export function DataSourceBadges({ threadId, messageCount }: DataSourceBadgesProps) {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
  const [usedDatabases, setUsedDatabases] = useState<string[]>([]);
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  useEffect(() => {
    const fetchDataSources = async () => {
      try {
        const sources = await api.getDataSources();
        setDataSources(sources);
      } catch (error) {
        console.error("Failed to fetch data sources:", error);
      }
    };

    fetchDataSources();
  }, []);

  useEffect(() => {
    const fetchUsedDatabases = async () => {
      if (!threadId) {
        setUsedDatabases([]);
        return;
      }

      try {
        const databases = await api.getUsedDatabases(threadId);
        setUsedDatabases(databases);
      } catch (error) {
        console.error("Failed to fetch used databases:", error);
        setUsedDatabases([]);
      }
    };

    fetchUsedDatabases();
  }, [threadId, messageCount]); // Also depend on messageCount to refresh after messages

  if (dataSources.length === 0) return null;

  const isUsed = (sourceId: string) => usedDatabases.includes(sourceId);
  const hasAnyMessages = (messageCount ?? 0) > 0;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-gray-500 font-medium">Data Sources:</span>
      {dataSources.map((source) => {
        const used = isUsed(source.id);
        // Dim if: no messages yet OR (has messages but this one not used)
        const shouldDim = !hasAnyMessages || (hasAnyMessages && !used);

        return (
          <div
            key={source.id}
            className="relative"
            onMouseEnter={() => setHoveredId(source.id)}
            onMouseLeave={() => setHoveredId(null)}
          >
            <span
              className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium border cursor-help hover:shadow-sm transition-all ${
                shouldDim
                  ? "opacity-30 bg-gray-100 text-gray-500 border-gray-200"
                  : "bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 border-purple-200"
              }`}
            >
              {source.name}
            </span>

            {hoveredId === source.id && (
              <div className="absolute z-50 top-full mt-2 left-0 w-64 p-3 bg-white rounded-lg shadow-lg border border-gray-200">
                <div className="font-semibold text-sm text-gray-900 mb-1">
                  {source.name}
                </div>
                <div className="text-xs text-gray-600 leading-relaxed">
                  {source.description}
                </div>
                {used && (
                  <div className="mt-2 text-xs text-purple-600 font-medium">
                    ✓ Used in this thread
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
