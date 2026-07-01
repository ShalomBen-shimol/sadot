"use client";

import { useEffect, useMemo, useState } from "react";
import {
  getWorkflowStepTypes,
  getWorkflow,
  updateWorkflow,
  type WorkflowStep,
  type WorkflowStepType,
  type WorkflowVocabulary,
  type WorkflowFieldSpec,
  type TransferType,
} from "@/lib/api";
import {
  useAdminToken,
  errorMessage,
  ErrorBox,
  Spinner,
  PageHeader,
  Badge,
  ActionButton,
} from "../_components/ui";
import {
  transferTypeLabels,
  documentTypeLabels,
  signatureTypeLabels,
  dogStatusLabels,
} from "../_components/labels";

// Hebrew labels for the closed option lists the backend hands us as raw strings.
const OPTION_LABELS: Record<string, string> = {
  authority_to: "רשות מקבלת",
  authority_from: "רשות מוסרת",
  from_person: "מוסר",
  to_person: "מקבל / בעלים חדש",
  none: "ללא בעלים",
  low: "נמוכה",
  normal: "רגילה",
  high: "גבוהה",
  urgent: "דחופה",
};

function optionLabel(value: string): string {
  return (
    OPTION_LABELS[value] ??
    (documentTypeLabels as Record<string, string>)[value] ??
    (signatureTypeLabels as Record<string, string>)[value] ??
    (dogStatusLabels as Record<string, string>)[value] ??
    value
  );
}

const TRANSFER_ORDER: TransferType[] = [
  "surrender_to_facility",
  "facility_to_adopter",
  "direct_surrenderer_to_adopter",
];

export default function WorkflowBuilderPage() {
  const token = useAdminToken();
  const [vocab, setVocab] = useState<WorkflowVocabulary | null>(null);
  const [transferType, setTransferType] = useState<TransferType>("surrender_to_facility");
  const [version, setVersion] = useState<number>(0);
  const [steps, setSteps] = useState<WorkflowStep[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [savedMsg, setSavedMsg] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [addType, setAddType] = useState<string>("");

  const stepTypeMap = useMemo(() => {
    const m: Record<string, WorkflowStepType> = {};
    (vocab?.step_types ?? []).forEach((s) => (m[s.type] = s));
    return m;
  }, [vocab]);

  useEffect(() => {
    if (!token) return;
    getWorkflowStepTypes(token)
      .then((v) => {
        setVocab(v);
        setAddType(v.step_types[0]?.type ?? "");
      })
      .catch((e) => setError(errorMessage(e)));
  }, [token]);

  useEffect(() => {
    if (!token) return;
    setLoading(true);
    setSavedMsg(null);
    getWorkflow(token, transferType)
      .then((wf) => {
        setSteps(wf.steps ?? []);
        setVersion(wf.version);
        setError(null);
      })
      .catch((e) => setError(errorMessage(e)))
      .finally(() => setLoading(false));
  }, [token, transferType]);

  function mutateStep(i: number, patch: Partial<WorkflowStep>) {
    setSteps((prev) => prev.map((s, idx) => (idx === i ? { ...s, ...patch } : s)));
  }

  function setConfig(i: number, key: string, value: unknown) {
    setSteps((prev) =>
      prev.map((s, idx) =>
        idx === i ? { ...s, config: { ...(s.config ?? {}), [key]: value } } : s
      )
    );
  }

  function move(i: number, dir: -1 | 1) {
    setSteps((prev) => {
      const j = i + dir;
      if (j < 0 || j >= prev.length) return prev;
      const next = [...prev];
      [next[i], next[j]] = [next[j], next[i]];
      return next;
    });
  }

  function remove(i: number) {
    setSteps((prev) => prev.filter((_, idx) => idx !== i));
  }

  function addStep() {
    const st = stepTypeMap[addType];
    if (!st) return;
    setSteps((prev) => [
      ...prev,
      {
        type: st.type,
        title: st.label,
        ...(st.kind === "action" && st.manual_default ? { manual: true } : {}),
        config: {},
      },
    ]);
  }

  async function save() {
    if (!token) return;
    setError(null);
    setSavedMsg(null);
    try {
      const wf = await updateWorkflow(token, transferType, steps);
      setVersion(wf.version);
      setSteps(wf.steps ?? []);
      setSavedMsg(`נשמר (גרסה ${wf.version})`);
    } catch (e) {
      setError(errorMessage(e));
    }
  }

  if (token === undefined || (vocab === null && !error)) return <Spinner />;

  return (
    <div className="max-w-3xl space-y-6">
      <PageHeader
        title="מנוע האוטומציה"
        subtitle="בניית תהליך העברת הבעלות — שערים חוסמים (מסמכים/חתימות/אישור) ופעולות (מייל/משימה/עדכון) לפי סדר."
        action={<span className="text-xs text-gray-400">גרסה פעילה {version}</span>}
      />
      {error && <ErrorBox message={error} />}

      {/* Transfer-type selector */}
      <div className="card flex flex-wrap gap-2">
        {TRANSFER_ORDER.map((tt) => (
          <button
            key={tt}
            onClick={() => setTransferType(tt)}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition ${
              transferType === tt
                ? "bg-brand text-white"
                : "text-gray-700 hover:bg-brand-light hover:text-brand-dark"
            }`}
          >
            {transferTypeLabels[tt]}
          </button>
        ))}
      </div>

      {loading ? (
        <Spinner />
      ) : (
        <>
          {/* Step list */}
          <div className="space-y-3">
            {steps.length === 0 && (
              <div className="card text-sm text-gray-500">אין שלבים. הוסיפו שלב ראשון למטה.</div>
            )}
            {steps.map((step, i) => {
              const st = stepTypeMap[step.type];
              return (
                <div key={i} className="card space-y-3">
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-brand-light text-xs font-semibold text-brand-dark">
                      {i + 1}
                    </span>
                    <input
                      className="input flex-1"
                      value={step.title ?? ""}
                      placeholder={st?.label ?? step.type}
                      onChange={(e) => mutateStep(i, { title: e.target.value })}
                    />
                    <Badge tone={st?.kind === "gate" ? "amber" : "green"}>
                      {st?.kind === "gate" ? "שער" : "פעולה"}
                    </Badge>
                    <div className="flex gap-1">
                      <button
                        onClick={() => move(i, -1)}
                        disabled={i === 0}
                        className="rounded px-1.5 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        title="למעלה"
                      >
                        ↑
                      </button>
                      <button
                        onClick={() => move(i, 1)}
                        disabled={i === steps.length - 1}
                        className="rounded px-1.5 text-gray-500 hover:bg-gray-100 disabled:opacity-30"
                        title="למטה"
                      >
                        ↓
                      </button>
                      <button
                        onClick={() => remove(i)}
                        className="rounded px-1.5 text-red-500 hover:bg-red-50"
                        title="מחיקה"
                      >
                        ✕
                      </button>
                    </div>
                  </div>

                  <p className="text-xs text-gray-400">{st?.label ?? step.type}</p>

                  {/* Manual toggle for action steps */}
                  {st?.kind === "action" && (
                    <label className="flex items-center gap-2 text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={!!step.manual}
                        onChange={(e) => mutateStep(i, { manual: e.target.checked })}
                      />
                      דורש הפעלה ידנית של הצוות (לא אוטומטי)
                    </label>
                  )}

                  {/* Config field editors */}
                  {(st?.fields ?? []).map((field) => (
                    <FieldEditor
                      key={field.name}
                      field={field}
                      value={step.config?.[field.name]}
                      vocab={vocab!}
                      onChange={(v) => setConfig(i, field.name, v)}
                    />
                  ))}
                </div>
              );
            })}
          </div>

          {/* Add step + save */}
          <div className="card flex flex-wrap items-center gap-2">
            <select
              className="input max-w-xs"
              value={addType}
              onChange={(e) => setAddType(e.target.value)}
            >
              {(vocab?.step_types ?? []).map((s) => (
                <option key={s.type} value={s.type}>
                  {s.label} ({s.kind === "gate" ? "שער" : "פעולה"})
                </option>
              ))}
            </select>
            <button className="btn-outline text-sm" onClick={addStep}>
              הוספת שלב
            </button>
            <div className="ml-auto flex items-center gap-3">
              {savedMsg && <span className="text-sm text-green-600">{savedMsg}</span>}
              <ActionButton onClick={save}>שמירה כגרסה חדשה</ActionButton>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

// ---- Per-field editor, driven by the field spec from the backend vocabulary ----
function FieldEditor({
  field,
  value,
  vocab,
  onChange,
}: {
  field: WorkflowFieldSpec;
  value: unknown;
  vocab: WorkflowVocabulary;
  onChange: (v: unknown) => void;
}) {
  if (field.type === "documenttypes" || field.type === "signaturetypes") {
    const options =
      field.type === "documenttypes" ? vocab.document_types : vocab.signature_types;
    const selected = Array.isArray(value) ? (value as string[]) : [];
    function toggle(opt: string) {
      onChange(selected.includes(opt) ? selected.filter((s) => s !== opt) : [...selected, opt]);
    }
    return (
      <div>
        <p className="mb-1 text-xs font-medium text-gray-500">{field.label}</p>
        <div className="flex flex-wrap gap-2">
          {options.map((opt) => (
            <label
              key={opt}
              className={`flex cursor-pointer items-center gap-1.5 rounded-lg border px-2.5 py-1 text-sm ${
                selected.includes(opt)
                  ? "border-brand bg-brand-light text-brand-dark"
                  : "border-gray-200 text-gray-600"
              }`}
            >
              <input
                type="checkbox"
                className="sr-only"
                checked={selected.includes(opt)}
                onChange={() => toggle(opt)}
              />
              {optionLabel(opt)}
            </label>
          ))}
        </div>
      </div>
    );
  }

  if (field.type === "select") {
    return (
      <label className="block text-sm">
        <span className="text-gray-600">{field.label}</span>
        <select
          className="input mt-1"
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
        >
          <option value="">—</option>
          {(field.options ?? []).map((opt) => (
            <option key={opt} value={opt}>
              {optionLabel(opt)}
            </option>
          ))}
        </select>
      </label>
    );
  }

  if (field.type === "textarea") {
    return (
      <label className="block text-sm">
        <span className="text-gray-600">{field.label}</span>
        <textarea
          className="input mt-1 min-h-[80px]"
          value={(value as string) ?? ""}
          onChange={(e) => onChange(e.target.value)}
        />
      </label>
    );
  }

  if (field.type === "number") {
    return (
      <label className="block text-sm">
        <span className="text-gray-600">{field.label}</span>
        <input
          type="number"
          className="input mt-1 max-w-[140px]"
          value={value === undefined || value === null ? "" : (value as number)}
          onChange={(e) => onChange(e.target.value === "" ? null : Number(e.target.value))}
        />
      </label>
    );
  }

  // text
  return (
    <label className="block text-sm">
      <span className="text-gray-600">{field.label}</span>
      <input
        className="input mt-1"
        value={(value as string) ?? ""}
        onChange={(e) => onChange(e.target.value)}
      />
    </label>
  );
}
