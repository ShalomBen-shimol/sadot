"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import {
  assignLocality,
  listLocalities,
  listMunicipalities,
  resolveLocality,
  updateMunicipality,
  type Locality,
  type LocalityResolveResponse,
  type Municipality,
} from "../../../lib/api";
import {
  ActionButton,
  Badge,
  ErrorBox,
  PageHeader,
  Spinner,
  errorMessage,
  useAdminToken,
} from "../_components/ui";

type Tab = "authorities" | "localities" | "review";

export default function AuthoritiesPage() {
  const token = useAdminToken();
  const [tab, setTab] = useState<Tab>("authorities");
  const [munis, setMunis] = useState<Municipality[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMunis = useCallback(async () => {
    if (!token) return;
    try {
      setMunis(await listMunicipalities(token));
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token]);

  useEffect(() => {
    loadMunis();
  }, [loadMunis]);

  const muniById = useMemo(() => {
    const m = new Map<number, Municipality>();
    (munis ?? []).forEach((x) => m.set(x.id, x));
    return m;
  }, [munis]);

  if (token === undefined || munis === null) return <Spinner />;

  return (
    <div className="space-y-6">
      <PageHeader
        title="רשויות וטרינריות"
        subtitle={`${munis.length} רשויות · שיוך יישובים לרשות הווטרינרית המתאימה`}
      />
      {error && <ErrorBox message={error} />}

      <div className="flex gap-2 border-b border-gray-200">
        {([
          ["authorities", "רשויות"],
          ["localities", "יישובים וחיפוש"],
          ["review", "ממתינים לשיוך"],
        ] as [Tab, string][]).map(([key, label]) => (
          <button
            key={key}
            onClick={() => setTab(key)}
            className={`-mb-px border-b-2 px-4 py-2 text-sm font-medium transition ${
              tab === key
                ? "border-brand text-brand-dark"
                : "border-transparent text-gray-500 hover:text-brand-dark"
            }`}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "authorities" && <AuthoritiesTab token={token} munis={munis} onSaved={loadMunis} />}
      {tab === "localities" && <LocalitiesTab token={token} muniById={muniById} />}
      {tab === "review" && <ReviewTab token={token} munis={munis} muniById={muniById} />}
    </div>
  );
}

/* ----------------------------- Authorities tab ----------------------------- */
function AuthoritiesTab({
  token,
  munis,
  onSaved,
}: {
  token: string;
  munis: Municipality[];
  onSaved: () => Promise<void>;
}) {
  const [q, setQ] = useState("");
  const [editing, setEditing] = useState<Municipality | null>(null);

  const filtered = useMemo(() => {
    const s = q.trim();
    if (!s) return munis;
    return munis.filter((m) =>
      [m.city_name, m.authority_name, m.vet_name, m.district, m.email].some(
        (v) => v && v.includes(s)
      )
    );
  }, [q, munis]);

  const missing = munis.filter((m) => !m.email).length;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <input
          className="input max-w-xs"
          placeholder="חיפוש רשות / וטרינר / לשכה…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
        <span className="text-sm text-gray-500">{filtered.length} תוצאות</span>
        {missing > 0 && <Badge tone="amber">{missing} רשויות ללא מייל</Badge>}
      </div>

      <div className="card overflow-x-auto p-0">
        <table className="min-w-full text-right text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2 font-medium">רשות</th>
              <th className="px-3 py-2 font-medium">לשכה</th>
              <th className="px-3 py-2 font-medium">וטרינר</th>
              <th className="px-3 py-2 font-medium">מייל</th>
              <th className="px-3 py-2 font-medium">טלפון</th>
              <th className="px-3 py-2 font-medium"></th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filtered.slice(0, 300).map((m) => (
              <tr key={m.id} className="hover:bg-gray-50">
                <td className="px-3 py-2 font-medium text-gray-900">{m.city_name}</td>
                <td className="px-3 py-2 text-gray-600">{m.district ?? "—"}</td>
                <td className="px-3 py-2 text-gray-600">{m.vet_name ?? "—"}</td>
                <td className="px-3 py-2 text-gray-600">
                  {m.email ?? <Badge tone="amber">חסר</Badge>}
                </td>
                <td className="px-3 py-2 text-gray-600">{m.phone ?? "—"}</td>
                <td className="px-3 py-2">
                  <button className="text-xs text-brand-dark hover:underline" onClick={() => setEditing(m)}>
                    עריכה
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {editing && (
        <EditAuthorityModal
          token={token}
          authority={editing}
          onClose={() => setEditing(null)}
          onSaved={async () => {
            setEditing(null);
            await onSaved();
          }}
        />
      )}
    </div>
  );
}

function EditAuthorityModal({
  token,
  authority,
  onClose,
  onSaved,
}: {
  token: string;
  authority: Municipality;
  onClose: () => void;
  onSaved: () => Promise<void>;
}) {
  const [vetName, setVetName] = useState(authority.vet_name ?? "");
  const [email, setEmail] = useState(authority.email ?? "");
  const [phone, setPhone] = useState(authority.phone ?? "");
  const [err, setErr] = useState<string | null>(null);

  async function save() {
    setErr(null);
    try {
      await updateMunicipality(token, authority.id, {
        vet_name: vetName || null,
        email: email || null,
        phone: phone || null,
      });
      await onSaved();
    } catch (e) {
      setErr(errorMessage(e));
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4" onClick={onClose}>
      <div className="card w-full max-w-md space-y-4" onClick={(e) => e.stopPropagation()}>
        <h2 className="text-lg font-bold text-brand-dark">{authority.city_name}</h2>
        <p className="text-xs text-gray-500">{authority.authority_name}</p>
        {err && <ErrorBox message={err} />}
        <label className="block text-sm">
          <span className="text-gray-600">שם הווטרינר</span>
          <input className="input mt-1" value={vetName} onChange={(e) => setVetName(e.target.value)} />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600">מייל</span>
          <input className="input mt-1" value={email} onChange={(e) => setEmail(e.target.value)} />
        </label>
        <label className="block text-sm">
          <span className="text-gray-600">טלפון</span>
          <input className="input mt-1" value={phone} onChange={(e) => setPhone(e.target.value)} />
        </label>
        <div className="flex justify-end gap-2">
          <button className="btn-outline text-sm" onClick={onClose}>ביטול</button>
          <ActionButton onClick={save}>שמירה</ActionButton>
        </div>
      </div>
    </div>
  );
}

/* ------------------------- Localities + resolver tab ------------------------ */
function LocalitiesTab({
  token,
  muniById,
}: {
  token: string;
  muniById: Map<number, Municipality>;
}) {
  const [resolveQ, setResolveQ] = useState("");
  const [resolved, setResolved] = useState<LocalityResolveResponse | null>(null);
  const [resolveErr, setResolveErr] = useState<string | null>(null);

  const [search, setSearch] = useState("");
  const [items, setItems] = useState<Locality[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);

  async function doResolve() {
    setResolveErr(null);
    setResolved(null);
    if (!resolveQ.trim()) return;
    try {
      setResolved(await resolveLocality(token, resolveQ.trim()));
    } catch (e) {
      setResolveErr(errorMessage(e));
    }
  }

  useEffect(() => {
    let active = true;
    const t = setTimeout(async () => {
      if (!search.trim()) {
        setItems([]);
        setTotal(0);
        return;
      }
      setLoading(true);
      try {
        const res = await listLocalities(token, { search: search.trim(), limit: 100 });
        if (active) {
          setItems(res.items);
          setTotal(res.total);
        }
      } finally {
        if (active) setLoading(false);
      }
    }, 250);
    return () => {
      active = false;
      clearTimeout(t);
    };
  }, [search, token]);

  return (
    <div className="space-y-6">
      {/* Resolver */}
      <div className="card space-y-3">
        <h3 className="font-semibold text-brand-dark">איתור רשות לפי יישוב</h3>
        <div className="flex flex-wrap gap-2">
          <input
            className="input max-w-xs"
            placeholder="הקלד שם יישוב…"
            value={resolveQ}
            onChange={(e) => setResolveQ(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && doResolve()}
          />
          <ActionButton onClick={doResolve}>איתור</ActionButton>
        </div>
        {resolveErr && <ErrorBox message={resolveErr} />}
        {resolved && !resolved.resolved && (
          <div className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
            לא נמצאה רשות וטרינרית עבור «{resolved.query}». ניתן לשייך ידנית בלשונית «ממתינים לשיוך».
          </div>
        )}
        {resolved && resolved.resolved && resolved.authority && (
          <div className="rounded-lg bg-green-50 p-4 text-sm">
            <div className="font-semibold text-green-900">{resolved.authority.city_name}</div>
            <div className="mt-1 grid grid-cols-2 gap-x-6 gap-y-1 text-green-800">
              <span>גוף: {resolved.authority.authority_name ?? "—"}</span>
              <span>לשכה: {resolved.authority.district ?? "—"}</span>
              <span>וטרינר: {resolved.authority.vet_name ?? "—"}</span>
              <span>רישיון: {resolved.authority.license_number ?? "—"}</span>
              <span>מייל: {resolved.authority.email ?? "—"}</span>
              <span>טלפון: {resolved.authority.phone ?? "—"}</span>
            </div>
          </div>
        )}
      </div>

      {/* Locality search */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-3">
          <input
            className="input max-w-xs"
            placeholder="חיפוש יישוב…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          {loading ? (
            <span className="text-sm text-gray-400">טוען…</span>
          ) : (
            search && <span className="text-sm text-gray-500">{total} תוצאות</span>
          )}
        </div>
        {items.length > 0 && (
          <div className="card overflow-x-auto p-0">
            <table className="min-w-full text-right text-sm">
              <thead className="bg-gray-50 text-xs text-gray-500">
                <tr>
                  <th className="px-3 py-2 font-medium">יישוב</th>
                  <th className="px-3 py-2 font-medium">נפה</th>
                  <th className="px-3 py-2 font-medium">רשות וטרינרית</th>
                  <th className="px-3 py-2 font-medium">סטטוס</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((l) => {
                  const muni = l.municipality_id ? muniById.get(l.municipality_id) : null;
                  return (
                    <tr key={l.id} className="hover:bg-gray-50">
                      <td className="px-3 py-2 font-medium text-gray-900">{l.name}</td>
                      <td className="px-3 py-2 text-gray-600">{l.subdistrict ?? "—"}</td>
                      <td className="px-3 py-2 text-gray-600">{muni?.city_name ?? "—"}</td>
                      <td className="px-3 py-2">
                        {l.needs_review ? (
                          <Badge tone="amber">ממתין לשיוך</Badge>
                        ) : (
                          <Badge tone="green">משויך</Badge>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ------------------------------- Review tab -------------------------------- */
function ReviewTab({
  token,
  munis,
  muniById,
}: {
  token: string;
  munis: Municipality[];
  muniById: Map<number, Municipality>;
}) {
  const [items, setItems] = useState<Locality[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const res = await listLocalities(token, { needs_review: true, limit: 1000 });
      setItems(res.items);
    } catch (e) {
      setError(errorMessage(e));
    }
  }, [token]);

  useEffect(() => {
    load();
  }, [load]);

  if (items === null) return <Spinner />;

  return (
    <div className="space-y-4">
      {error && <ErrorBox message={error} />}
      <p className="text-sm text-gray-500">
        {items.length} יישובים ללא רשות וטרינרית משויכת (בעיקר יישובי יו״ש, פזורה בדואית ויישובים שאינם
        ברשימת הרשויות). בחר רשות ושייך.
      </p>
      <div className="card overflow-x-auto p-0">
        <table className="min-w-full text-right text-sm">
          <thead className="bg-gray-50 text-xs text-gray-500">
            <tr>
              <th className="px-3 py-2 font-medium">יישוב</th>
              <th className="px-3 py-2 font-medium">נפה</th>
              <th className="px-3 py-2 font-medium">שיוך לרשות</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((l) => (
              <ReviewRow key={l.id} token={token} locality={l} munis={munis} onAssigned={load} />
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ReviewRow({
  token,
  locality,
  munis,
  onAssigned,
}: {
  token: string;
  locality: Locality;
  munis: Municipality[];
  onAssigned: () => Promise<void>;
}) {
  const [selected, setSelected] = useState<string>("");

  async function assign() {
    if (!selected) return;
    await assignLocality(token, locality.id, { municipality_id: Number(selected) });
    await onAssigned();
  }

  return (
    <tr className="hover:bg-gray-50">
      <td className="px-3 py-2 font-medium text-gray-900">{locality.name}</td>
      <td className="px-3 py-2 text-gray-600">{locality.subdistrict ?? "—"}</td>
      <td className="px-3 py-2">
        <div className="flex items-center gap-2">
          <select
            className="input max-w-xs"
            value={selected}
            onChange={(e) => setSelected(e.target.value)}
          >
            <option value="">בחר רשות…</option>
            {munis.map((m) => (
              <option key={m.id} value={m.id}>
                {m.city_name}
              </option>
            ))}
          </select>
          <ActionButton onClick={assign} disabled={!selected}>
            שייך
          </ActionButton>
        </div>
      </td>
    </tr>
  );
}
