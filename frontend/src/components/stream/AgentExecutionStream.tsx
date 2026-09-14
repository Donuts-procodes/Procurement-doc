import { useState, useRef, useEffect } from "react";
import type { StreamEvent } from "../../types";

interface AgentExecutionStreamProps {
  events: StreamEvent[];
  isStreaming: boolean;
  onClear?: () => void;
}

export function AgentExecutionStream({ events, isStreaming, onClear }: AgentExecutionStreamProps) {
  const [expandedTools, setExpandedTools] = useState<Record<number, boolean>>({});
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  const toggleToolExpand = (index: number) => {
    setExpandedTools((prev) => ({ ...prev, [index]: !prev[index] }));
  };

  const agentSteps = events.filter((e) => e.type === "agent_thought") as Extract<
    StreamEvent,
    { type: "agent_thought" }
  >[];

  const currentStep = agentSteps.find((s) => s.status === "running")?.step || (isStreaming ? "Processing graph..." : "Idle");

  return (
    <div
      className="agent-execution-stream"
      style={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        backgroundColor: "#0f172a",
        color: "#f8fafc",
        borderRight: "1px solid #1e293b",
        fontFamily: "Inter, system-ui, sans-serif",
      }}
    >
      {/* Stream Header */}
      <div
        style={{
          padding: "12px 16px",
          borderBottom: "1px solid #1e293b",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          backgroundColor: "#1e293b",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <span style={{ fontSize: "16px" }}>⚡</span>
          <span style={{ fontWeight: 700, fontSize: "13px", letterSpacing: "0.5px", color: "#38bdf8" }}>
            AGENT EXECUTION STREAM
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          {isStreaming ? (
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                fontSize: "11px",
                fontWeight: 600,
                color: "#4ade80",
                backgroundColor: "rgba(74, 222, 128, 0.1)",
                padding: "2px 8px",
                borderRadius: "12px",
                border: "1px solid rgba(74, 222, 128, 0.3)",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  backgroundColor: "#4ade80",
                  animation: "pulse 1.5s infinite",
                }}
              />
              LIVE
            </span>
          ) : (
            <span
              style={{
                fontSize: "11px",
                fontWeight: 600,
                color: "#94a3b8",
                backgroundColor: "rgba(148, 163, 184, 0.1)",
                padding: "2px 8px",
                borderRadius: "12px",
              }}
            >
              IDLE
            </span>
          )}
          {onClear && events.length > 0 && (
            <button
              onClick={onClear}
              style={{
                background: "transparent",
                border: "none",
                color: "#64748b",
                cursor: "pointer",
                fontSize: "11px",
                padding: "2px 4px",
              }}
              title="Clear event stream"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Active Status Chip Banner */}
      <div
        style={{
          padding: "8px 16px",
          backgroundColor: isStreaming ? "rgba(56, 189, 248, 0.1)" : "rgba(30, 41, 59, 0.5)",
          borderBottom: "1px solid #1e293b",
          fontSize: "12px",
          display: "flex",
          alignItems: "center",
          gap: "8px",
        }}
      >
        <span style={{ color: "#94a3b8" }}>Current Phase:</span>
        <span
          style={{
            color: isStreaming ? "#38bdf8" : "#cbd5e1",
            fontWeight: 600,
            textTransform: "capitalize",
            overflow: "hidden",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
          }}
        >
          {currentStep.replace(/_/g, " ")}
        </span>
      </div>

      {/* Timeline Event Feed */}
      <div
        style={{
          flex: 1,
          overflowY: "auto",
          padding: "12px 16px",
          display: "flex",
          flexDirection: "column",
          gap: "10px",
        }}
      >
        {events.length === 0 && (
          <div style={{ textAlign: "center", color: "#64748b", marginTop: "40px", fontSize: "12px" }}>
            <p>No agent events recorded yet.</p>
            <p style={{ fontSize: "11px", marginTop: "4px" }}>
              Trigger a document generation or inline AI edit to watch subagents execute in real time.
            </p>
          </div>
        )}

        {events.map((evt, idx) => {
          if (evt.type === "agent_thought") {
            const isCompleted = evt.status === "completed";
            return (
              <div
                key={idx}
                style={{
                  display: "flex",
                  alignItems: "flex-start",
                  gap: "10px",
                  padding: "8px 12px",
                  borderRadius: "6px",
                  backgroundColor: isCompleted ? "rgba(30, 41, 59, 0.6)" : "rgba(56, 189, 248, 0.12)",
                  border: isCompleted ? "1px solid #334155" : "1px solid #0284c7",
                }}
              >
                <span style={{ fontSize: "14px", marginTop: "1px" }}>
                  {isCompleted ? "✅" : "🧠"}
                </span>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: isCompleted ? "#cbd5e1" : "#38bdf8" }}>
                      {evt.step.replace(/_/g, " ")}
                    </span>
                    <span
                      style={{
                        fontSize: "10px",
                        fontWeight: 700,
                        textTransform: "uppercase",
                        color: isCompleted ? "#4ade80" : "#f59e0b",
                      }}
                    >
                      {evt.status}
                    </span>
                  </div>
                </div>
              </div>
            );
          }

          if (evt.type === "tool_execution") {
            const isExpanded = !!expandedTools[idx];
            return (
              <div
                key={idx}
                style={{
                  borderRadius: "6px",
                  backgroundColor: "#1e293b",
                  border: "1px solid #334155",
                  overflow: "hidden",
                }}
              >
                <div
                  onClick={() => toggleToolExpand(idx)}
                  style={{
                    padding: "8px 12px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    cursor: "pointer",
                    backgroundColor: "#1e293b",
                  }}
                >
                  <div style={{ display: "flex", alignItems: "center", gap: "6px", minWidth: 0 }}>
                    <span style={{ fontSize: "13px" }}>🛠️</span>
                    <span style={{ fontSize: "12px", fontWeight: 600, color: "#f1f5f9" }}>
                      {evt.tool_name}
                    </span>
                  </div>
                  <span style={{ fontSize: "10px", color: "#94a3b8" }}>
                    {isExpanded ? "▲ Hide" : "▼ Details"}
                  </span>
                </div>

                {isExpanded && (
                  <div
                    style={{
                      padding: "8px 12px",
                      borderTop: "1px solid #334155",
                      backgroundColor: "#0f172a",
                      fontSize: "11px",
                      fontFamily: "monospace",
                    }}
                  >
                    <div style={{ color: "#94a3b8", marginBottom: "4px" }}>Input:</div>
                    <pre
                      style={{
                        background: "#1e293b",
                        padding: "6px",
                        borderRadius: "4px",
                        overflowX: "auto",
                        color: "#e2e8f0",
                        margin: 0,
                      }}
                    >
                      {JSON.stringify(evt.input, null, 2)}
                    </pre>

                    {evt.output && (
                      <>
                        <div style={{ color: "#94a3b8", marginTop: "6px", marginBottom: "4px" }}>Output:</div>
                        <pre
                          style={{
                            background: "#1e293b",
                            padding: "6px",
                            borderRadius: "4px",
                            overflowX: "auto",
                            color: "#38bdf8",
                            margin: 0,
                            maxHeight: "120px",
                          }}
                        >
                          {evt.output}
                        </pre>
                      </>
                    )}
                  </div>
                )}
              </div>
            );
          }

          if (evt.type === "canvas_patch") {
            return (
              <div
                key={idx}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  backgroundColor: "rgba(168, 85, 247, 0.1)",
                  border: "1px solid rgba(168, 85, 247, 0.3)",
                  fontSize: "11px",
                  color: "#d8b4fe",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>🎨</span>
                <span>
                  Canvas Patch: <strong>{evt.operation}</strong>
                  {evt.target_id ? ` (${evt.target_id})` : ""}
                </span>
              </div>
            );
          }

          if (evt.type === "checkpoint") {
            return (
              <div
                key={idx}
                style={{
                  padding: "6px 10px",
                  borderRadius: "6px",
                  backgroundColor: "rgba(34, 197, 94, 0.1)",
                  border: "1px solid rgba(34, 197, 94, 0.3)",
                  fontSize: "11px",
                  color: "#86efac",
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                }}
              >
                <span>💾</span>
                <span>
                  Checkpoint Saved: <strong>{evt.version_id}</strong>
                </span>
              </div>
            );
          }

          return null;
        })}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
