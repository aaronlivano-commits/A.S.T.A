import { useRef, useState } from "react";
import { Card, CardHeader } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useTypewriter } from "@/animations/gsapHooks";
import { api } from "@/lib/api";

// Grounded interactive chatbot. Streams tokens over SSE from
//   POST /api/v1/chat/stream
// which returns the framework's expected { topic_id, messages } shape.
export default function ChatWindow() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [sources, setSources] = useState([]);
  const typewriter = useTypewriter();
  const messagesRef = useRef(messages);

  // Keep a ref so the SSE callback always sees the latest message list.
  messagesRef.current = messages;

  async function handleSend(e) {
    e.preventDefault();
    const text = input.trim();
    if (!text || streaming) return;

    const userMsg = { role: "user", text };
    const history = messagesRef.current
      .filter((m) => !m.streaming)
      .map((m) => ({ role: m.role, content: m.text }));

    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setStreaming(true);
    setSources([]);
    typewriter.reset();

    const assistantMsg = { role: "assistant", streaming: true, text: "" };
    setMessages((prev) => [...prev, assistantMsg]);

    const stop = await api
      .streamSse(
        "/chat/stream",
        {
          topic_id: null,
          messages: [...history, { role: "user", content: text }],
        },
        {
          sources: (payload) => setSources(Array.isArray(payload) ? payload : []),
          token: (payload) => {
            const tokenText =
              typeof payload === "string" ? payload : payload?.text ?? "";
            if (!tokenText) return;
            typewriter.append(tokenText);
            setMessages((prev) =>
              prev.map((m, i) =>
                i === prev.length - 1 && m.streaming
                  ? { ...m, text: m.text + tokenText }
                  : m
              )
            );
          },
          error: (payload) => {
            const detail =
              typeof payload === "string"
                ? payload
                : payload?.detail ?? "Streaming failed";
            setMessages((prev) =>
              prev.map((m, i) =>
                i === prev.length - 1 && m.streaming
                  ? { ...m, text: `Backend error: ${detail}`, streaming: false }
                  : m
              )
            );
          },
          done: () => {
            setMessages((prev) =>
              prev.map((m, i) =>
                i === prev.length - 1 && m.streaming ? { ...m, streaming: false } : m
              )
            );
          },
        }
      )
      .catch((err) => {
        const detail =
          err.status === 401
            ? "Sign in with Google to chat — the backend requires a verified Firebase ID token."
            : `Backend not reachable yet — ${err.message}`;
        setMessages((prev) =>
          prev.map((m, i) =>
            i === prev.length - 1 && m.streaming
              ? { ...m, text: detail, streaming: false }
              : m
          )
        );
      });

    // Stop button hook (cleanly cancel the underlying reader).
    stopRef.current = stop;
  }

  const stopRef = useRef(null);

  return (
    <Card>
      <CardHeader designation="UNIT-03" title="Grounded Interactive Chatbot" />
      <p className="text-asta-whiteDim max-w-[74ch] mb-6">
        Answers are scoped to the current topic's uploaded material — no open-ended
        recall. Responses stream in as they're generated.
      </p>

      <div className="bg-asta-void border border-asta-line p-5 h-72 overflow-y-auto flex flex-col gap-4 mb-4">
        {messages.length === 0 && (
          <p className="font-mono text-xs text-asta-whiteDim">
            ASK SOMETHING ABOUT YOUR UPLOADED MATERIAL.
          </p>
        )}
        {messages.map((m, i) => {
          const isLastStreaming = m.streaming && i === messages.length - 1;
          return (
            <div
              key={i}
              className={`max-w-[85%] px-4 py-3 text-sm ${
                m.role === "user"
                  ? "self-end bg-asta-blueDeep text-asta-white"
                  : "self-start bg-asta-panelAlt text-asta-white"
              }`}
            >
              {isLastStreaming ? <span ref={typewriter.ref} /> : m.text}
            </div>
          );
        })}
      </div>

      {sources.length > 0 && (
        <div className="mb-4 font-mono text-xs text-asta-whiteDim">
          <span className="text-asta-yellow">SOURCES:</span>{" "}
          {sources.map((s, i) => (
            <span key={i} className="mr-3">
              [Source {i + 1}]
            </span>
          ))}
        </div>
      )}

      <form onSubmit={handleSend} className="flex gap-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="TRANSMIT QUERY…"
          className="flex-1 bg-asta-void border border-asta-line text-asta-white placeholder:text-asta-whiteDim px-4 py-3 font-mono text-sm focus:outline-none focus:border-asta-blueBright"
        />
        {streaming ? (
          <Button
            type="button"
            variant="danger"
            onClick={() => stopRef.current?.()}
          >
            STOP
          </Button>
        ) : (
          <Button type="submit" variant="primary">
            SEND
          </Button>
        )}
      </form>
    </Card>
  );
}
