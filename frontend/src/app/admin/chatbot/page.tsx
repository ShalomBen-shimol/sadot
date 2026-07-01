"use client";

import { useEffect, useState } from "react";
import { getBotConfig, updateBotConfig, previewBotConfig, type BotConfig } from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  ActionButton,
} from "../_components/ui";

type SandboxTurn = { role: "user" | "assistant"; content: string };

export default function ChatbotConsolePage() {
  const token = useAdminToken();
  const [cfg, setCfg] = useState<BotConfig | null>(null);
  const [persona, setPersona] = useState("");
  const [knowledgebase, setKnowledgebase] = useState("");
  const [model, setModel] = useState("claude-opus-4-8");
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);

  // Test sandbox
  const [turns, setTurns] = useState<SandboxTurn[]>([]);
  const [sandboxInput, setSandboxInput] = useState("");
  const [testing, setTesting] = useState(false);

  useEffect(() => {
    if (!token) return;
    getBotConfig(token)
      .then((c) => {
        setCfg(c);
        setPersona(c.persona);
        setKnowledgebase(c.knowledgebase);
        setModel(c.model);
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  async function save() {
    setError(null);
    setSavedMsg(null);
    try {
      const updated = await updateBotConfig(token!, { persona, knowledgebase, model });
      setCfg(updated);
      setSavedMsg(`נשמר (גרסה ${updated.version})`);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function runTest() {
    const message = sandboxInput.trim();
    if (!message || testing) return;
    setSandboxInput("");
    const history = turns;
    setTurns((t) => [...t, { role: "user", content: message }]);
    setTesting(true);
    try {
      // Tests the CURRENT (unsaved) edits — nothing is persisted, no lead created.
      const r = await previewBotConfig(token!, { persona, knowledgebase, model, message, history });
      setTurns((t) => [...t, { role: "assistant", content: r.reply }]);
    } catch (e) {
      setTurns((t) => [...t, { role: "assistant", content: "שגיאה: " + errorMessage(e) }]);
    } finally {
      setTesting(false);
    }
  }

  if (token === undefined || (cfg === null && !error)) return <Spinner />;

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="ניהול הבוט"
        subtitle="הגדרת אישיות ומאגר הידע של הצ'אט בוט. כללי הבטיחות מוגדרים במערכת ואינם ניתנים לשינוי."
        action={
          cfg && (
            <div className="flex items-center gap-2">
              <Badge tone={cfg.provider === "claude" ? "green" : "gray"}>
                {cfg.provider === "claude" ? "Claude Opus 4.8" : "מצב הדגמה (Mock)"}
              </Badge>
              <span className="text-xs text-gray-400">גרסה {cfg.version}</span>
            </div>
          )
        }
      />
      {error && <ErrorBox message={error} />}

      {cfg?.provider === "mock" && (
        <div className="card bg-amber-50 text-sm text-amber-900">
          הבוט פועל כרגע במצב הדגמה (ללא מפתח Claude). כדי להפעיל את Claude Opus 4.8 האמיתי, יש
          להגדיר את <span className="font-mono" dir="ltr">ANTHROPIC_API_KEY</span> בשרת.
        </div>
      )}

      {/* Editor */}
      <div className="card space-y-4">
        <h2 className="font-semibold text-brand-dark">אישיות ומדיניות</h2>
        <label className="block text-sm">
          <span className="text-gray-600">טון וסגנון (persona)</span>
          <textarea
            className="input mt-1 min-h-[120px]"
            value={persona}
            onChange={(e) => setPersona(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600">מאגר ידע (עובדות, מחירים, נהלים)</span>
          <textarea
            className="input mt-1 min-h-[120px]"
            value={knowledgebase}
            onChange={(e) => setKnowledgebase(e.target.value)}
          />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600">מודל</span>
          <input className="input mt-1" dir="ltr" value={model} onChange={(e) => setModel(e.target.value)} />
        </label>
        <div className="flex items-center gap-3">
          <ActionButton onClick={save}>שמירה כגרסה חדשה</ActionButton>
          {savedMsg && <span className="text-sm text-green-600">{savedMsg}</span>}
        </div>
      </div>

      {/* Test sandbox */}
      <div className="card space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-brand-dark">ארגז חול לבדיקה</h2>
          <button className="text-xs text-gray-500 hover:underline" onClick={() => setTurns([])}>
            ניקוי
          </button>
        </div>
        <p className="text-xs text-gray-400">
          בודק את השינויים הנוכחיים (לפני שמירה). לא נשמר דבר ולא נוצר ליד.
        </p>
        <div className="min-h-[100px] space-y-2 rounded-xl bg-gray-50 p-3">
          {turns.length === 0 && <p className="text-sm text-gray-400">שלח/י הודעת בדיקה כדי לראות תשובה.</p>}
          {turns.map((t, i) => (
            <div key={i} className={`flex ${t.role === "user" ? "justify-start" : "justify-end"}`}>
              <div
                className={`max-w-[80%] whitespace-pre-wrap rounded-2xl px-3 py-1.5 text-sm ${
                  t.role === "user" ? "bg-brand text-white" : "border border-gray-200 bg-white text-gray-800"
                }`}
              >
                {t.content}
              </div>
            </div>
          ))}
          {testing && <p className="text-left text-xs text-gray-400">מקליד/ה…</p>}
        </div>
        <div className="flex items-end gap-2">
          <input
            className="input flex-1"
            placeholder="הודעת בדיקה…"
            value={sandboxInput}
            onChange={(e) => setSandboxInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && runTest()}
          />
          <ActionButton onClick={runTest} variant="outline">
            בדיקה
          </ActionButton>
        </div>
      </div>
    </div>
  );
}
