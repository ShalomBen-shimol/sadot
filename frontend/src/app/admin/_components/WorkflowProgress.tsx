"use client";

import { useCallback, useEffect, useState } from "react";
import {
  getTransferWorkflow,
  advanceTransferWorkflow,
  type WorkflowStatus,
} from "@/lib/api";
import { ActionButton, Badge, ErrorBox } from "./ui";

// Live view of a transfer's walk through its configurable workflow: which step
// it's on, what's blocking, and the buttons to advance / fire a manual action.
export default function WorkflowProgress({
  token,
  transferId,
  onChanged,
}: {
  token: string;
  transferId: number;
  onChanged?: () => void;
}) {
  const [status, setStatus] = useState<WorkflowStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      setStatus(await getTransferWorkflow(token, transferId));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "שגיאה בטעינת התהליך");
    }
  }, [token, transferId]);

  useEffect(() => {
    load();
  }, [load]);

  async function advance(runAction: boolean) {
    setError(null);
    try {
      setStatus(await advanceTransferWorkflow(token, transferId, runAction));
      onChanged?.();
    } catch (e) {
      setError(e instanceof Error ? e.message : "הפעולה נכשלה");
    }
  }

  const currentTitle = (s: WorkflowStatus): string =>
    s.current?.title || s.current?.type || "";

  return (
    <div className="card space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-brand-dark">תהליך אוטומציה</h2>
        {status &&
          (status.done ? (
            <Badge tone="green">הושלם</Badge>
          ) : (
            <Badge tone="gray">
              שלב {Math.min(status.step_index + 1, status.total)} מתוך {status.total}
            </Badge>
          ))}
      </div>

      {error && <ErrorBox message={error} />}

      {status && (
        <>
          {/* Step rail */}
          <ol className="space-y-1.5 text-sm">
            {status.steps.map((step, i) => {
              const done = i < status.step_index;
              const current = i === status.step_index && !status.done;
              return (
                <li key={i} className="flex items-center gap-3">
                  <span
                    className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[11px] ${
                      done
                        ? "bg-green-100 text-green-700"
                        : current
                          ? "bg-brand text-white"
                          : "bg-gray-100 text-gray-400"
                    }`}
                  >
                    {done ? "✓" : i + 1}
                  </span>
                  <span className={current ? "font-medium text-gray-900" : "text-gray-600"}>
                    {step.title || step.type}
                  </span>
                </li>
              );
            })}
          </ol>

          {/* Current-state banner + actions */}
          {status.done ? (
            <p className="text-sm text-green-700">כל שלבי התהליך הושלמו.</p>
          ) : (
            <div className="space-y-2 border-t border-gray-100 pt-3">
              {status.blocking && (
                <p className="text-sm text-amber-700">
                  ממתין: {status.blocking} — <span className="font-medium">{currentTitle(status)}</span>
                </p>
              )}
              {status.awaiting_action && (
                <p className="text-sm text-gray-600">
                  השלב הבא דורש הפעלה ידנית: <span className="font-medium">{currentTitle(status)}</span>
                </p>
              )}
              <div className="flex flex-wrap gap-2">
                <ActionButton variant="outline" onClick={() => advance(false)}>
                  בדיקה וקידום
                </ActionButton>
                {status.awaiting_action && (
                  <ActionButton onClick={() => advance(true)}>
                    הפעלה: {currentTitle(status)}
                  </ActionButton>
                )}
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}
