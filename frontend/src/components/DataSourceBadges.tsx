import { useState, useEffect } from "react";
import { api, DataSource } from "@/lib/api";

export function DataSourceBadges() {
  const [dataSources, setDataSources] = useState<DataSource[]>([]);
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

  if (dataSources.length === 0) return null;

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-gray-500 font-medium">Data Sources:</span>
      {dataSources.map((source) => (
        <div
          key={source.id}
          className="relative"
          onMouseEnter={() => setHoveredId(source.id)}
          onMouseLeave={() => setHoveredId(null)}
        >
          <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-gradient-to-r from-purple-100 to-blue-100 text-purple-700 border border-purple-200 cursor-help hover:shadow-sm transition-all">
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
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
