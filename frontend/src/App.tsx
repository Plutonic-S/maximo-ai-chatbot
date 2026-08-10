import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  type ChatModelAdapter,
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  AuiIf,
} from "@assistant-ui/react";
import "@assistant-ui/react-markdown/styles/dot.css";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";

const maximoAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const lastUserMessage = messages[messages.length - 1];
    let userText = "";
    if (lastUserMessage && lastUserMessage.content) {
      userText = lastUserMessage.content
        .filter((c) => c.type === "text")
        .map((c: any) => c.text)
        .join("\n");
    }

    const apiBaseUrl = import.meta.env.VITE_API_BASE_URL || "https://1esbcsi8mf.execute-api.eu-central-1.amazonaws.com/api/chat";
    const response = await fetch(apiBaseUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: userText }),
      signal: abortSignal,
    });

    if (!response.ok) {
      throw new Error(`Backend API error (${response.status}): ${response.statusText}`);
    }

    const data = await response.json();
    return {
      content: [{ type: "text", text: data.reply }],
    };
  },
};

function ChatUI() {
  return (
    <ThreadPrimitive.Root className="chat-container">
      {/* Top Header Bar */}
      <header className="chat-header">
        <div className="chat-header-title">
          <span>Maximo AI Assistant</span>
          <span className="model-pill">Gemini 3.5 Flash Lite</span>
        </div>
        <div className="status-badge">
          <span className="status-dot"></span>
          <span>AWS Lambda API Gateway Connected</span>
        </div>
      </header>

      {/* Main Messages Viewport */}
      <ThreadPrimitive.Viewport className="chat-viewport">
        <ThreadPrimitive.Empty>
          <div className="empty-state">
            <div className="empty-state-icon">🛠️</div>
            <div className="empty-state-title">Maximo Asset & Ticket Copilot</div>
            <div className="empty-state-desc">
              Ask questions about service requests, locations, work orders, or classifications across your IBM Maximo environment.
            </div>
          </div>
        </ThreadPrimitive.Empty>

        {/* Message Item Rendering */}
        <ThreadPrimitive.Messages>
          {({ message }) => (
            <MessagePrimitive.Root
              className={message.role === "user" ? "user-message-root" : "assistant-message-root"}
            >
              <MessagePrimitive.Parts>
                {({ part }) => {
                  switch (part.type) {
                    case "text":
                      return <MarkdownTextPrimitive remarkPlugins={[remarkGfm]} />;
                    default:
                      return null;
                  }
                }}
              </MessagePrimitive.Parts>
            </MessagePrimitive.Root>
          )}
        </ThreadPrimitive.Messages>

        {/* Loading Indicator */}
        <AuiIf condition={({ thread }) => thread.isRunning}>
          <div className="loading-indicator">
            <div className="spinner"></div>
            <span>Querying Maximo OSLC REST API...</span>
          </div>
        </AuiIf>
      </ThreadPrimitive.Viewport>

      {/* Input Composer */}
      <ComposerPrimitive.Root className="chat-composer">
        <ComposerPrimitive.Input
          className="composer-input"
          placeholder="Ask Maximo AI (e.g. 'Show tickets for location AIR101 and 764750')..."
        />
        <ComposerPrimitive.Send className="composer-send">
          Send
        </ComposerPrimitive.Send>
      </ComposerPrimitive.Root>
    </ThreadPrimitive.Root>
  );
}

export default function App() {
  const runtime = useLocalRuntime(maximoAdapter);

  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <ChatUI />
    </AssistantRuntimeProvider>
  );
}
