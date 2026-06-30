"use client";

import { useEffect, useState } from "react";
import {
  getEmailSettings,
  updateEmailSettings,
  sendTestEmail,
  type EmailSettings,
} from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  ActionButton,
} from "../_components/ui";

export default function SettingsPage() {
  const token = useAdminToken();
  const [settings, setSettings] = useState<EmailSettings | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Editable fields. Password is write-only: blank means "leave unchanged".
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [fromName, setFromName] = useState("");
  const [fromEmail, setFromEmail] = useState("");
  const [host, setHost] = useState("smtp.gmail.com");
  const [port, setPort] = useState(587);
  const [enabled, setEnabled] = useState(false);

  const [saveMsg, setSaveMsg] = useState<string | null>(null);
  const [testTo, setTestTo] = useState("");
  const [testMsg, setTestMsg] = useState<{ ok: boolean; text: string } | null>(null);

  function hydrate(s: EmailSettings) {
    setSettings(s);
    setUsername(s.username ?? "");
    setFromName(s.from_name ?? "");
    setFromEmail(s.from_email ?? "");
    setHost(s.host);
    setPort(s.port);
    setEnabled(s.enabled);
    setPassword("");
  }

  useEffect(() => {
    if (!token) return;
    getEmailSettings(token)
      .then(hydrate)
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  async function save() {
    setSaveMsg(null);
    setError(null);
    try {
      const updated = await updateEmailSettings(token!, {
        username: username || null,
        // Only send the password when the field was filled — blank keeps it.
        ...(password ? { password } : {}),
        from_name: fromName || null,
        from_email: fromEmail || null,
        host,
        port,
        enabled,
      });
      hydrate(updated);
      setSaveMsg("נשמר");
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  async function test() {
    setTestMsg(null);
    if (!testTo.trim()) return;
    try {
      const r = await sendTestEmail(token!, testTo.trim());
      setTestMsg({ ok: r.status === "sent", text: r.detail });
    } catch (e) {
      setTestMsg({ ok: false, text: errorMessage(e) });
    }
  }

  if (token === undefined || settings === null) return <Spinner />;

  return (
    <div className="max-w-2xl space-y-6">
      <PageHeader
        title="הגדרות דוא״ל"
        subtitle="חיבור חשבון Gmail לשליחת מיילים אוטומטית לרשויות הווטרינריות"
      />
      {error && <ErrorBox message={error} />}

      {/* How-to */}
      <div className="card space-y-2 bg-amber-50 text-sm text-amber-900">
        <p className="font-semibold">איך מחברים חשבון Gmail (שיטת App Password)</p>
        <ol className="list-inside list-decimal space-y-1">
          <li>הפעילו אימות דו-שלבי (2FA) בחשבון ה-Gmail.</li>
          <li>
            צרו «סיסמת אפליקציה» בכתובת{" "}
            <span className="font-mono" dir="ltr">myaccount.google.com/apppasswords</span>.
          </li>
          <li>הזינו את כתובת ה-Gmail ואת סיסמת האפליקציה (16 תווים) כאן, שמרו, ושלחו מייל בדיקה.</li>
        </ol>
        <p className="text-xs text-amber-700">
          שיטה זו אינה תלויה בכתובת האתר — לא צריך לעדכן דבר ב-Google גם לאחר מעבר לדומיין הסופי.
        </p>
      </div>

      {/* Account form */}
      <div className="card space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="font-semibold text-brand-dark">חשבון השליחה</h2>
          <span className="text-xs text-gray-400">
            {settings.password_set ? "סיסמה שמורה ✓" : "לא הוגדרה סיסמה"}
          </span>
        </div>

        <label className="block text-sm">
          <span className="text-gray-600">כתובת Gmail (שם משתמש)</span>
          <input
            className="input mt-1"
            dir="ltr"
            placeholder="basadot@gmail.com"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
        </label>

        <label className="block text-sm">
          <span className="text-gray-600">סיסמת אפליקציה</span>
          <input
            className="input mt-1"
            dir="ltr"
            type="password"
            placeholder={settings.password_set ? "•••••••• (השאירו ריק כדי לא לשנות)" : "16 תווים"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </label>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="text-gray-600">שם השולח (תצוגה)</span>
            <input
              className="input mt-1"
              placeholder="פנסיון בשדות"
              value={fromName}
              onChange={(e) => setFromName(e.target.value)}
            />
          </label>
          <label className="block text-sm">
            <span className="text-gray-600">כתובת השולח (ברירת מחדל: שם המשתמש)</span>
            <input
              className="input mt-1"
              dir="ltr"
              value={fromEmail}
              onChange={(e) => setFromEmail(e.target.value)}
            />
          </label>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <label className="block text-sm">
            <span className="text-gray-600">שרת SMTP</span>
            <input className="input mt-1" dir="ltr" value={host} onChange={(e) => setHost(e.target.value)} />
          </label>
          <label className="block text-sm">
            <span className="text-gray-600">פורט</span>
            <input
              className="input mt-1"
              dir="ltr"
              type="number"
              value={port}
              onChange={(e) => setPort(Number(e.target.value))}
            />
          </label>
        </div>

        <label className="flex items-center gap-2 text-sm text-gray-700">
          <input type="checkbox" checked={enabled} onChange={(e) => setEnabled(e.target.checked)} />
          הפעל שליחת מיילים אמיתית (כשמכובה — המערכת רק מתעדת ולא שולחת)
        </label>

        <div className="flex items-center gap-3">
          <ActionButton onClick={save}>שמירה</ActionButton>
          {saveMsg && <span className="text-sm text-green-600">{saveMsg}</span>}
        </div>
      </div>

      {/* Test */}
      <div className="card space-y-3">
        <h2 className="font-semibold text-brand-dark">שליחת מייל בדיקה</h2>
        <div className="flex flex-wrap items-center gap-2">
          <input
            className="input max-w-xs"
            dir="ltr"
            placeholder="dest@example.com"
            value={testTo}
            onChange={(e) => setTestTo(e.target.value)}
          />
          <ActionButton onClick={test} variant="outline">
            שלח בדיקה
          </ActionButton>
        </div>
        <p className="text-xs text-gray-400">
          הבדיקה משתמשת בסיסמה השמורה — שמרו תחילה אם שיניתם אותה.
        </p>
        {testMsg && (
          <div className={`text-sm ${testMsg.ok ? "text-green-600" : "text-red-600"}`}>
            {testMsg.ok ? "נשלח בהצלחה: " : "נכשל: "}
            {testMsg.text}
          </div>
        )}
      </div>
    </div>
  );
}
