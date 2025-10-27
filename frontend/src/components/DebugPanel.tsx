import { useState } from "react";
import { InfoCircledIcon, Cross2Icon } from "@radix-ui/react-icons";
import { Button } from "./ui/button";

interface DebugInfo {
  stage: string;
  model: string;
  elapsed_ms: number;
  pipeline_time_ms: number;
  tokens: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
    communication?: {
      model: string;
      system_prompt: string;
      messages: Array<{ role: string; content: string }>;
      response: any;
      temperature: number;
    };
  };
}

interface DebugPanelProps {
  debugInfo: DebugInfo[];
}

export function DebugPanel({ debugInfo }: DebugPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedStage, setSelectedStage] = useState<number>(0);

  if (!debugInfo || debugInfo.length === 0) return null;

  const currentStage = debugInfo[selectedStage];
  const communication = currentStage?.tokens?.communication;
  const pipelineTimeMs = currentStage?.pipeline_time_ms || 0;

  return (
    <>
      {/* Debug Icon Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="inline-flex items-center gap-1 px-2 py-1 text-xs text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded transition-colors"
        title="Show debug information"
      >
        <InfoCircledIcon className="h-3 w-3" />
        <span>Debug</span>
      </button>

      {/* Debug Panel Modal */}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
          <div className="bg-white rounded-lg shadow-2xl w-[90vw] h-[90vh] flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b bg-gradient-to-r from-purple-50 to-blue-50">
              <div>
                <h2 className="text-lg font-bold text-gray-900">
                  🔍 LLM Debug Information
                </h2>
                <p className="text-xs text-gray-600 mt-1">
                  Pipeline: {pipelineTimeMs}ms | {debugInfo.length} stages
                </p>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsOpen(false)}
                className="h-8 w-8 p-0"
              >
                <Cross2Icon className="h-4 w-4" />
              </Button>
            </div>

            {/* Content */}
            <div className="flex-1 overflow-hidden flex">
              {/* Sidebar - Stages */}
              <div className="w-64 border-r bg-gray-50 overflow-y-auto">
                <div className="p-4 space-y-2">
                  {debugInfo.map((info, idx) => (
                    <button
                      key={idx}
                      onClick={() => setSelectedStage(idx)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedStage === idx
                          ? "bg-white border-purple-300 shadow-sm"
                          : "bg-white/50 border-gray-200 hover:bg-white"
                      }`}
                    >
                      <div className="font-semibold text-sm text-gray-900">
                        {info.stage.charAt(0).toUpperCase() + info.stage.slice(1)}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {info.model}
                      </div>
                      <div className="flex items-center gap-2 mt-2 text-xs">
                        <span className="text-blue-600 font-mono">
                          {info.elapsed_ms}ms
                        </span>
                        <span className="text-gray-400">•</span>
                        <span className="text-purple-600 font-mono">
                          {info.tokens.total_tokens} tokens
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Main Content - Communication Details */}
              <div className="flex-1 overflow-y-auto p-6">
                {communication ? (
                  <div className="space-y-6">
                    {/* Metadata */}
                    <div className="bg-gray-50 rounded-lg p-4 border">
                      <h3 className="font-semibold text-sm text-gray-900 mb-3">
                        Metadata
                      </h3>
                      <div className="grid grid-cols-2 gap-4 text-sm">
                        <div>
                          <span className="text-gray-600">Model:</span>
                          <div className="font-mono text-purple-600 mt-1">
                            {communication.model}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Temperature:</span>
                          <div className="font-mono text-purple-600 mt-1">
                            {communication.temperature}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Input Tokens:</span>
                          <div className="font-mono text-blue-600 mt-1">
                            {currentStage.tokens.input_tokens}
                          </div>
                        </div>
                        <div>
                          <span className="text-gray-600">Output Tokens:</span>
                          <div className="font-mono text-blue-600 mt-1">
                            {currentStage.tokens.output_tokens}
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* System Prompt */}
                    <div>
                      <h3 className="font-semibold text-sm text-gray-900 mb-2">
                        System Prompt
                      </h3>
                      <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-xs overflow-x-auto border">
                        {communication.system_prompt}
                      </pre>
                    </div>

                    {/* User Messages */}
                    <div>
                      <h3 className="font-semibold text-sm text-gray-900 mb-2">
                        User Message
                      </h3>
                      {communication.messages.map((msg, idx) => (
                        <div key={idx} className="mb-2">
                          <div className="text-xs text-gray-600 mb-1 font-semibold">
                            {msg.role.toUpperCase()}
                          </div>
                          <pre className="bg-blue-50 text-gray-900 p-4 rounded-lg text-xs overflow-x-auto border border-blue-200">
                            {msg.content}
                          </pre>
                        </div>
                      ))}
                    </div>

                    {/* LLM Response */}
                    <div>
                      <h3 className="font-semibold text-sm text-gray-900 mb-2">
                        LLM Response (Structured Output)
                      </h3>
                      <pre className="bg-green-50 text-gray-900 p-4 rounded-lg text-xs overflow-x-auto border border-green-200">
                        {JSON.stringify(communication.response, null, 2)}
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="text-center text-gray-500 mt-12">
                    No communication details available for this stage
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </>
  );
}
