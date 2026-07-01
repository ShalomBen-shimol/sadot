"use client";

import { useEffect, useRef, useState } from "react";
import { sendChatMessage } from "@/lib/api";

type Turn = { role: "user" | "bot"; text: string };

const WELCOME =
  "שלום 🐾 אני העוזר/ת של פנסיון בשדות. אני כאן כדי ללוות אותך בעדינות אם את/ה שוקל/ת למסור כלב. אפשר לספר לי מה מביא אותך לכאן?";

export default function PublicChatPage() {
  const [turns, setTurns] = useState<Turn[]>([{ role: "bot", text: WELCOME }]);
  const [input, setInput] = useState("");
  const [conversationId, setConversationId] = useState<number | undefined>();
  const [sending, setSending] = useState(false);
  const [done, setDone] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns, sending]);

  async function send() {
    const text = input.trim();
    if (!text || sending) return;
    setInput("");
    setTurns((t) => [...t, { role: "user", text }]);
    setSending(true);
    try {
      const r = await sendChatMessage(text, conversationId);
      setConversationId(r.conversation_id);
      setTurns((t) => [...t, { role: "bot", text: r.reply }]);
      if (r.status === "lead_created" || r.status === "escalated") setDone(true);
    } catch {
      setTurns((t) => [...t, { role: "bot", text: "מצטערים, קרתה תקלה. נסו שוב בעוד רגע." }]);
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="mx-auto flex h-[85vh] max-w-2xl flex-col p-4">
      <div className="mb-3 text-center">
        <h1 className="text-xl font-bold text-brand-dark">שיחה עם פנסיון בשדות</h1>
        <p className="text-xs text-gray-500">שיחה דיסקרטית ולא מחייבת</p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto rounded-2xl bg-gray-50 p-4">
        {turns.map((t, i) => (
          <div key={i} className={`flex ${t.role === "user" ? "justify-start" : "justify-end"}`}>
            <div
              className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-4 py-2 text-sm ${
                t.role === "user"
                  ? "bg-brand text-white"
                  : "border border-gray-200 bg-white text-gray-800"
              }`}
            >
              {t.text}
            </div>
          </div>
        ))}
        {sending && (
          <div className="flex justify-end">
            <div className="rounded-2xl border border-gray-200 bg-white px-4 py-2 text-sm text-gray-400">
              מקליד/ה…
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>

      {done ? (
        <div className="mt-3 rounded-xl bg-green-50 p-3 text-center text-sm text-green-700">
          תודה! צוות הפנסיון יחזור אליך בהקדם.
        </div>
      ) : (
        <div className="mt-3 flex items-end gap-2">
          <textarea
            className="input min-h-[48px] flex-1 resize-none"
            placeholder="כתוב/כתבי הודעה…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
          />
          <button className="btn-primary px-6 py-3" onClick={send} disabled={sending || !input.trim()}>
            שליחה
          </button>
        </div>
      )}
    </div>
  );
}
