import { useEffect, useState } from "react";
import {
  AssistantRuntimeProvider,
  useLocalRuntime,
  useAui,
  type ChatModelAdapter,
  ThreadPrimitive,
  MessagePrimitive,
  ComposerPrimitive,
  AuiIf,
} from "@assistant-ui/react";
import "@assistant-ui/react-markdown/styles/dot.css";
import { MarkdownTextPrimitive } from "@assistant-ui/react-markdown";
import remarkGfm from "remark-gfm";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://1esbcsi8mf.execute-api.eu-central-1.amazonaws.com/api/chat";

const MODEL_LABEL = "gpt-oss:120b-cloud";

const STARTER_QUERIES = [
  "How many open service requests are there?",
  "Show locations at site BEDFORD",
  "Classifications available for service requests",
  "Tickets for location AIR101 or 764750",
];

const maximoAdapter: ChatModelAdapter = {
  async run({ messages, abortSignal }) {
    const lastUserMessage = messages[messages.length - 1];
    let userText = "";
    if (lastUserMessage && lastUserMessage.content) {
      userText = lastUserMessage.content
        .filter((c): c is { type: "text"; text: string } => c.type === "text")
        .map((c) => c.text)
        .join("\n");
    }

    const response = await fetch(API_BASE_URL, {
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

function GaugeMark({ size = 18 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <circle cx="16" cy="16" r="13" fill="none" stroke="currentColor" strokeWidth="2.4" />
      <path d="M16 16 L16 8.5" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <path d="M16 16 L21 19.2" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" />
      <circle cx="16" cy="16" r="1.8" fill="currentColor" />
    </svg>
  );
}

type Theme = "light" | "dark";

function useThemeToggle() {
  const [theme, setTheme] = useState<Theme | null>(() => {
    const stored = window.localStorage.getItem("maximo-copilot-theme");
    return stored === "light" || stored === "dark" ? stored : null;
  });

  useEffect(() => {
    if (theme) {
      document.documentElement.setAttribute("data-theme", theme);
      window.localStorage.setItem("maximo-copilot-theme", theme);
    } else {
      document.documentElement.removeAttribute("data-theme");
    }
  }, [theme]);

  const systemPrefersDark =
    typeof window !== "undefined" &&
    window.matchMedia?.("(prefers-color-scheme: dark)").matches;

  const resolved = theme ?? (systemPrefersDark ? "dark" : "light");

  return {
    resolved,
    toggle: () => setTheme(resolved === "dark" ? "light" : "dark"),
  };
}

function ConsoleHeader() {
  const { resolved, toggle } = useThemeToggle();
  return (
    <header className="console-header">
      <div className="console-brand">
        <span className="brand-mark">
          <GaugeMark />
        </span>
        <div className="brand-text">
          <span className="brand-name">Maximo Copilot</span>
          <span className="brand-subtitle">Asset &amp; service request assistant</span>
        </div>
      </div>
      <div className="console-telemetry">
        <span className="model-tag">{MODEL_LABEL}</span>
        <span className="status-pill">
          <span className="status-dot" />
          Connected
        </span>
        <button
          type="button"
          className="theme-toggle"
          onClick={toggle}
          aria-label={resolved === "dark" ? "Switch to light theme" : "Switch to dark theme"}
        >
          {resolved === "dark" ? "Light" : "Dark"}
        </button>
      </div>
    </header>
  );
}

function EmptyState() {
  const aui = useAui();

  const runSuggestion = (text: string) => {
    const composer = aui.thread.composer();
    composer.setText(text);
    composer.send();
  };

  return (
    <div className="console-empty">
      <span className="empty-mark">
        <GaugeMark size={26} />
      </span>
      <h2 className="empty-title">Ask about your Maximo environment</h2>
      <p className="empty-desc">
        Query service requests, locations, and classifications in plain language. Counts, filters,
        and lookups run live against your Maximo OSLC API.
      </p>
      <div className="starter-grid">
        {STARTER_QUERIES.map((q) => (
          <button key={q} type="button" className="starter-chip" onClick={() => runSuggestion(q)}>
            {q}
          </button>
        ))}
      </div>
    </div>
  );
}

function ChatUI() {
  return (
    <ThreadPrimitive.Root className="app-shell">
      <ConsoleHeader />

      <ThreadPrimitive.Viewport className="console-viewport">
        <ThreadPrimitive.Empty>
          <EmptyState />
        </ThreadPrimitive.Empty>

        <ThreadPrimitive.Messages>
          {({ message }) => (
            <MessagePrimitive.Root
              className={message.role === "user" ? "record record-user" : "record record-assistant"}
            >
              {message.role !== "user" && <div className="record-label">Response</div>}
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

        <AuiIf condition={({ thread }) => thread.isRunning}>
          <div className="loading-indicator">
            <span className="loading-bars" aria-hidden="true">
              <span />
              <span />
              <span />
            </span>
            Querying Maximo OSLC API
          </div>
        </AuiIf>
      </ThreadPrimitive.Viewport>

      <ComposerPrimitive.Root className="console-composer">
        <span className="composer-prompt" aria-hidden="true">
          &gt;
        </span>
        <ComposerPrimitive.Input
          className="composer-input"
          placeholder="Ask about tickets, locations, or classifications…"
        />
        <ComposerPrimitive.Send className="composer-send">Send</ComposerPrimitive.Send>
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
