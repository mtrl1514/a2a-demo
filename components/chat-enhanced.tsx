"use client";

/**
 * Enhanced Chat Component with Direct Orchestrator A2A Visualization.
 * Provides the same A2A message flow UI for both middleware and direct approaches.
 */

import React, { useEffect } from "react";
import { CopilotKit, useCopilotChat, useCopilotAction } from "@copilotkit/react-core";
import { CopilotChat } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";
import { MessageToA2A } from "./a2a/MessageToA2A";
import { MessageFromA2A } from "./a2a/MessageFromA2A";

type ResearchData = {
  topic: string;
  summary: string;
  findings: Array<{ title: string; description: string }>;
  sources: string;
};

type AnalysisData = {
  topic: string;
  overview: string;
  insights: Array<{ title: string; description: string; importance: string }>;
  conclusion: string;
};

type ChatProps = {
  onResearchUpdate: (data: ResearchData | null) => void;
  onAnalysisUpdate: (data: AnalysisData | null) => void;
};

const ChatInner = ({ onResearchUpdate, onAnalysisUpdate }: ChatProps) => {
  const { visibleMessages } = useCopilotChat();

  // Extract structured JSON from both A2A middleware and Direct Orchestrator responses
  useEffect(() => {
    const extractDataFromMessages = () => {
      for (const message of visibleMessages) {
        const msg = message as any;

        // Handle A2A Middleware responses
        if (msg.type === "ResultMessage" && msg.actionName === "send_message_to_a2a_agent") {
          try {
            const result = msg.result;
            let parsed;

            if (typeof result === "string") {
              let cleanResult = result;
              if (result.startsWith("A2A Agent Response: ")) {
                cleanResult = result.substring("A2A Agent Response: ".length);
              }
              try {
                parsed = JSON.parse(cleanResult);
              } catch {
                continue;
              }
            } else if (typeof result === "object") {
              parsed = result;
            } else {
              continue;
            }

            if (parsed.findings && Array.isArray(parsed.findings)) {
              onResearchUpdate(parsed as ResearchData);
            } else if (parsed.insights && Array.isArray(parsed.insights)) {
              onAnalysisUpdate(parsed as AnalysisData);
            }
          } catch (e) {
            console.error("Failed to extract data from message:", e);
          }
        }

        // Handle Direct Orchestrator responses - extract from marked JSON data
        if (msg.type === "ResponseMessage" && msg.role === "assistant") {
          try {
            const content = msg.content;
            if (typeof content === "string") {
              // Look for marked research data
              const researchMatch = content.match(/RESEARCH_DATA_START:\s*(\{[\s\S]*?\})\s*:RESEARCH_DATA_END/);
              if (researchMatch) {
                try {
                  const researchData = JSON.parse(researchMatch[1]);
                  if (researchData.findings && Array.isArray(researchData.findings)) {
                    onResearchUpdate(researchData as ResearchData);
                  }
                } catch (e) {
                  console.error("Failed to parse research data:", e);
                }
              }

              // Look for marked analysis data
              const analysisMatch = content.match(/ANALYSIS_DATA_START:\s*(\{[\s\S]*?\})\s*:ANALYSIS_DATA_END/);
              if (analysisMatch) {
                try {
                  const analysisData = JSON.parse(analysisMatch[1]);
                  if (analysisData.insights && Array.isArray(analysisData.insights)) {
                    onAnalysisUpdate(analysisData as AnalysisData);
                  }
                } catch (e) {
                  console.error("Failed to parse analysis data:", e);
                }
              }
            }
          } catch (e) {
            console.error("Failed to extract data from Direct Orchestrator response:", e);
          }
        }
      }
    };

    extractDataFromMessages();
  }, [visibleMessages, onResearchUpdate, onAnalysisUpdate]);

  // Register A2A Middleware action (original)
  useCopilotAction({
    name: "send_message_to_a2a_agent",
    description: "Sends a message to an A2A agent via middleware",
    available: "frontend",
    parameters: [
      {
        name: "agentName",
        type: "string",
        description: "The name of the A2A agent to send the message to",
      },
      {
        name: "task",
        type: "string",
        description: "The message to send to the A2A agent",
      },
    ],
    render: (actionRenderProps) => {
      return (
        <>
          <MessageToA2A {...actionRenderProps} />
          <MessageFromA2A {...actionRenderProps} />
        </>
      );
    },
  });

  // Register Direct Orchestrator Research Agent action
  useCopilotAction({
    name: "call_research_agent",
    description: "Calls Research Agent directly via HTTP",
    available: "frontend",
    parameters: [
      {
        name: "query",
        type: "string",
        description: "The research query to send to the agent",
      },
      {
        name: "instruction",
        type: "string",
        description: "Detailed instruction for what the agent should research",
        required: true,
      },
    ],
    render: (actionRenderProps) => {
      // Transform props to match A2A format
      // Use the AI's detailed instruction if available, fallback to query
      const task = actionRenderProps.args.instruction || actionRenderProps.args.query;

      const a2aProps = {
        ...actionRenderProps,
        args: {
          agentName: "Research Agent",
          task: task,
        },
      };

      return (
        <>
          <MessageToA2A {...a2aProps} />
          <MessageFromA2A {...a2aProps} />
        </>
      );
    },
  });

  // Register Direct Orchestrator Analysis Agent action
  useCopilotAction({
    name: "call_analysis_agent",
    description: "Calls Analysis Agent directly via HTTP",
    available: "frontend",
    parameters: [
      {
        name: "research_data",
        type: "string",
        description: "The research data to analyze",
      },
      {
        name: "instruction",
        type: "string",
        description: "Detailed instruction for what analysis to perform",
        required: true,
      },
    ],
    handler: async ({ research_data, instruction }) => {
      // This handler ensures the action is always called
      // console.log("Analysis Agent action triggered with data:", research_data?.substring(0, 100));
      // console.log("Analysis instruction:", instruction);
      return "Analysis started";
    },
    render: (actionRenderProps) => {
      // Transform props to match A2A format
      // Use the AI's detailed instruction if available, otherwise show research excerpt
      let task;
      if (actionRenderProps.args.instruction) {
        task = actionRenderProps.args.instruction;
      } else {
        // Fallback to showing research excerpt if no instruction provided
        const researchData = actionRenderProps.args.research_data || "";
        task = researchData.length > 100
          ? `Analyzing: ${researchData.substring(0, 100)}...`
          : `Analyzing: ${researchData}`;
      }

      const a2aProps = {
        ...actionRenderProps,
        args: {
          agentName: "Analysis Agent",
          task: task || "Analyzing research findings...",
        },
      };

      return (
        <>
          <MessageToA2A {...a2aProps} />
          <MessageFromA2A {...a2aProps} />
        </>
      );
    },
  });

  return (
    <CopilotChat
      labels={{
        title: "Research Assistant",
        initial: "👋 Hi! I'm your research assistant. I can help you research any topic.\n\nFor example, try:\n- \"Research quantum computing\"\n- \"Tell me about artificial intelligence\"\n- \"Research renewable energy\"\n\nI'll coordinate with specialized agents to gather information and provide insights!",
      }}
      className="h-full"
    />
  );
};

export default function ChatEnhanced({ onResearchUpdate, onAnalysisUpdate }: ChatProps) {
  return (
    <CopilotKit
      runtimeUrl="/api/copilotkit"
      agent="a2a_chat"
    >
      <ChatInner
        onResearchUpdate={onResearchUpdate}
        onAnalysisUpdate={onAnalysisUpdate}
      />
    </CopilotKit>
  );
}