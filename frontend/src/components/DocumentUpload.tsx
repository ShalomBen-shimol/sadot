"use client";

import { useRef, useState } from "react";
import type { DocumentType } from "@/lib/api";

// Reusable document picker for the public QR intake forms.
//
// IMPORTANT: the public lead endpoints (app/api/v1/public.py) do NOT expose a
// public document-upload route — uploadDocument() requires an admin Bearer
// token. So by default this component runs in "deferred" mode: the user may
// pick a file (local preview only) and we explain that the document itself will
// be collected after we make contact. If a real public upload is enabled later,
// pass `uploadFn` + `publicUploadEnabled` and it will perform the upload.

type DocumentUploadProps = {
  label: string;
  documentType: DocumentType;
  hint?: string;
  accept?: string;
  publicUploadEnabled?: boolean;
  // Optional real uploader (e.g. wired to a future public endpoint).
  uploadFn?: (file: File, documentType: DocumentType) => Promise<void>;
};

export default function DocumentUpload({
  label,
  documentType,
  hint,
  accept = "image/*",
  publicUploadEnabled = false,
  uploadFn,
}: DocumentUploadProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [fileName, setFileName] = useState<string | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [status, setStatus] = useState<"idle" | "uploading" | "done" | "error">(
    "idle"
  );

  const canUpload = publicUploadEnabled && !!uploadFn;

  async function onChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0] ?? null;
    if (!file) {
      setFileName(null);
      setPreviewUrl(null);
      return;
    }
    setFileName(file.name);
    setPreviewUrl(file.type.startsWith("image/") ? URL.createObjectURL(file) : null);

    if (canUpload) {
      setStatus("uploading");
      try {
        await uploadFn!(file, documentType);
        setStatus("done");
      } catch {
        setStatus("error");
      }
    }
  }

  return (
    <div className="rounded-lg border border-dashed border-gray-300 p-4">
      <p className="font-medium text-gray-800">{label}</p>
      {hint && <p className="mt-1 text-xs text-gray-500">{hint}</p>}

      {!canUpload && (
        <p className="mt-2 rounded-md bg-amber-50 px-3 py-2 text-xs text-amber-800">
          אין צורך להעלות עכשיו — נבקש מכם את המסמך הזה לאחר שניצור איתכם קשר.
          תוכלו כבר עכשיו לצלם/לבחור אותו כדי שיהיה מוכן.
        </p>
      )}

      <button
        type="button"
        onClick={() => inputRef.current?.click()}
        className="btn-outline mt-3 w-full py-3 text-base"
      >
        {fileName ? "בחירת קובץ אחר" : "צילום / בחירת קובץ"}
      </button>
      <input
        ref={inputRef}
        type="file"
        accept={accept}
        className="hidden"
        onChange={onChange}
      />

      {fileName && (
        <div className="mt-3 flex items-center gap-3 text-sm text-gray-700">
          {previewUrl && (
            // eslint-disable-next-line @next/next/no-img-element
            <img
              src={previewUrl}
              alt={label}
              className="h-16 w-16 rounded-md object-cover"
            />
          )}
          <span className="break-all">{fileName}</span>
        </div>
      )}

      {status === "uploading" && (
        <p className="mt-2 text-xs text-gray-500">מעלה…</p>
      )}
      {status === "done" && (
        <p className="mt-2 text-xs text-green-700">הקובץ הועלה בהצלחה.</p>
      )}
      {status === "error" && (
        <p className="mt-2 text-xs text-red-600">העלאת הקובץ נכשלה, נסו שוב.</p>
      )}
    </div>
  );
}
