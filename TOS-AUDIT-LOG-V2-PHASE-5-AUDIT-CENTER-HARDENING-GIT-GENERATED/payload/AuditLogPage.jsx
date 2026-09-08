import { useEffect, useMemo, useState } from "react";
import { Database, Download, RefreshCw, Search, ShieldCheck, Trash2 } from "lucide-react";
import { api } from "../lib/api";
import { getErrorMessage } from "../lib/errors";
import { Notice } from "../components/ui/Primitives";
import { usePreferences } from "../contexts/PreferencesContext";

function formatDate(value, isEnglish = false) {
  if (!value) return "—";
  return new Date(value).toLocaleString(isEnglish ? "en-GB" : "ar-EG", { dateStyle: "medium", timeStyle: "short" });
}

function actorLabel(actor) {
  return actor?.name || actor?.email || actor?.id || "System";
}

function badgeClass(severity) {
  const value = String(severity || "INFO").toUpperCase();
  if (value === "CRITICAL") return "bg-red-50 text-red-700 dark:bg-red-500/10 dark:text-red-200";
  if (value === "ERROR") return "bg-rose-50 text-rose-700 dark:bg-rose-500/10 dark:text-rose-200";
  if (value === "WARN") return "bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-200";
  return "bg-emerald-50 text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200";
}

function saveBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename || "tos-audit-v2.csv";
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 3000);
}

const EMPTY_FILTERS = {
  q: "",
  action: "",
  category: "",
  severity: "",
  outcome: "",
  source: "",
  from: "",
  to: "",
  page: 1,
};

export function AuditLogPage({ activeProjectId = "" }) {
  const { lang } = usePreferences();
  const isEnglish = lang === "en";
  const ui = (ar, en) => isEnglish ? en : ar;

  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const [projectOnly, setProjectOnly] = useState(Boolean(activeProjectId));
  const [entries, setEntries] = useState([]);
  const [filterOptions, setFilterOptions] = useState({ actions: [], categories: [], severities: [], outcomes: [], sources: [] });
  const [retention, setRetention] = useState(null);
  const [userRole, setUserRole] = useState("");
  const [pageInfo, setPageInfo] = useState({ page: 1, totalPages: 1, total: 0 });
  const [selectedId, setSelectedId] = useState("");
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [purging, setPurging] = useState(false);
  const [error, setError] = useState("");

  const query = useMemo(() => ({
    ...filters,
    ...(filters.from ? { from: `${filters.from}T00:00:00.000` } : {}),
    ...(filters.to ? { to: `${filters.to}T23:59:59.999` } : {}),
    ...(projectOnly && activeProjectId ? { projectId: activeProjectId } : {}),
    limit: 50,
  }), [filters, projectOnly, activeProjectId]);

  async function loadAuditLog() {
    try {
      setLoading(true);
      setError("");
      const response = await api.auditLog.v2(query);
      setEntries(response?.entries || []);
      setPageInfo({ page: response?.page || 1, totalPages: response?.totalPages || 1, total: response?.total || 0 });
    } catch (err) {
      setError(getErrorMessage(err, ui("تعذر تحميل Audit Center V2.", "Could not load Audit Center V2.")));
      setEntries([]);
    } finally {
      setLoading(false);
    }
  }

  async function loadGovernance() {
    const results = await Promise.allSettled([
      api.auditLog.v2Filters(),
      api.auditLog.retention(),
      api.me(),
    ]);
    if (results[0].status === "fulfilled") setFilterOptions(results[0].value || {});
    if (results[1].status === "fulfilled") setRetention(results[1].value || null);
    if (results[2].status === "fulfilled") setUserRole(results[2].value?.role || "");
  }

  useEffect(() => { loadGovernance(); }, []);
  useEffect(() => { loadAuditLog(); }, [query]);

  function updateFilter(key, value) {
    setFilters((current) => ({ ...current, [key]: value, page: key === "page" ? value : 1 }));
  }

  async function exportCsv() {
    try {
      setExporting(true);
      setError("");
      const result = await api.auditLog.exportV2({ ...query, page: undefined, exportLimit: 5000 });
      saveBlob(result.blob, result.filename);
    } catch (err) {
      setError(getErrorMessage(err, ui("تعذر تصدير السجل.", "Could not export the audit log.")));
    } finally {
      setExporting(false);
    }
  }

  async function runRetention() {
    if (!window.confirm(ui("سيتم حذف أحداث Audit V2 الأقدم من سياسة الاحتفاظ فقط. هل تريد المتابعة؟", "Only Audit V2 events older than the retention policy will be removed. Continue?"))) return;
    try {
      setPurging(true);
      setError("");
      await api.auditLog.runRetention({ days: retention?.days || 365 });
      await Promise.all([loadAuditLog(), loadGovernance()]);
    } catch (err) {
      setError(getErrorMessage(err, ui("تعذر تشغيل سياسة الاحتفاظ.", "Could not run retention.")));
    } finally {
      setPurging(false);
    }
  }

  return (
    <section dir={isEnglish ? "ltr" : "rtl"} className="p-4 sm:p-6">
      <div className="rounded-[30px] border border-zinc-100 bg-white p-5 shadow-sm dark:border-white/10 dark:bg-zinc-950">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="grid h-12 w-12 place-items-center rounded-2xl bg-amber-50 text-amber-700 dark:bg-amber-500/10 dark:text-amber-100">
              <ShieldCheck size={22} />
            </div>
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-black text-zinc-950 dark:text-white">{ui("Audit Center V2", "Audit Center V2")}</h2>
                <span className="rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-black text-emerald-700 dark:bg-emerald-500/10 dark:text-emerald-200">APPEND-ONLY</span>
              </div>
              <p className="mt-1 text-xs text-zinc-400">{ui("سجل مركزي للأمان والعمليات الحساسة مع فلترة وتصدير وسياسة احتفاظ محكومة.", "Central security and sensitive-operations history with filtering, export, and controlled retention.")}</p>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={exportCsv} disabled={exporting} className="inline-flex items-center gap-2 rounded-2xl border border-zinc-200 px-4 py-2 text-xs font-black text-zinc-700 disabled:opacity-50 dark:border-white/10 dark:text-zinc-200">
              <Download size={15} /> {exporting ? ui("جاري التصدير", "Exporting") : "CSV"}
            </button>
            <button type="button" onClick={loadAuditLog} disabled={loading} className="inline-flex items-center gap-2 rounded-2xl bg-zinc-950 px-4 py-2 text-xs font-black text-white disabled:opacity-50 dark:bg-white dark:text-zinc-950">
              <RefreshCw size={15} /> {ui("تحديث", "Refresh")}
            </button>
          </div>
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
          <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="text-[11px] font-bold text-zinc-400">{ui("إجمالي الأحداث", "Total events")}</div>
            <div className="mt-1 text-2xl font-black text-zinc-950 dark:text-white">{pageInfo.total.toLocaleString()}</div>
          </div>
          <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="text-[11px] font-bold text-zinc-400">{ui("سياسة الاحتفاظ", "Retention")}</div>
            <div className="mt-1 text-lg font-black text-zinc-950 dark:text-white">{retention ? `${retention.days} ${ui("يوم", "days")}` : "—"}</div>
          </div>
          <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="text-[11px] font-bold text-zinc-400">{ui("مؤهل للحذف بالسياسة", "Expired by policy")}</div>
            <div className="mt-1 text-lg font-black text-zinc-950 dark:text-white">{retention?.expired ?? "—"}</div>
          </div>
          <div className="rounded-2xl border border-zinc-100 bg-zinc-50 p-4 dark:border-white/10 dark:bg-white/5">
            <div className="text-[11px] font-bold text-zinc-400">{ui("الحماية", "Protection")}</div>
            <div className="mt-1 flex items-center gap-2 text-sm font-black text-emerald-700 dark:text-emerald-200"><Database size={15} /> DB Guard</div>
          </div>
        </div>

        <div className="mt-5 grid gap-3 lg:grid-cols-4">
          <label className="lg:col-span-2">
            <span className="text-[11px] font-black text-zinc-500">{ui("بحث", "Search")}</span>
            <div className="mt-1 flex items-center gap-2 rounded-2xl border border-zinc-100 bg-zinc-50 px-3 dark:border-white/10 dark:bg-white/5">
              <Search size={15} className="text-zinc-400" />
              <input value={filters.q} onChange={(e) => updateFilter("q", e.target.value)} placeholder={ui("Action، مستخدم، كيان، Route، Request ID...", "Action, actor, entity, route, request ID...")} className="w-full bg-transparent py-3 text-sm outline-none dark:text-white" />
            </div>
          </label>
          {[
            ["severity", ui("الخطورة", "Severity"), filterOptions.severities || []],
            ["outcome", ui("النتيجة", "Outcome"), filterOptions.outcomes || []],
            ["category", ui("الفئة", "Category"), filterOptions.categories || []],
            ["action", "Action", filterOptions.actions || []],
            ["source", ui("المصدر", "Source"), filterOptions.sources || []],
          ].map(([key, label, values]) => (
            <label key={key}>
              <span className="text-[11px] font-black text-zinc-500">{label}</span>
              <select value={filters[key]} onChange={(e) => updateFilter(key, e.target.value)} className="mt-1 w-full rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-zinc-900 dark:text-white">
                <option value="">{ui("الكل", "All")}</option>
                {values.map((value) => <option key={value} value={value}>{value}</option>)}
              </select>
            </label>
          ))}
          <label>
            <span className="text-[11px] font-black text-zinc-500">{ui("من", "From")}</span>
            <input type="date" value={filters.from} onChange={(e) => updateFilter("from", e.target.value)} className="mt-1 w-full rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
          </label>
          <label>
            <span className="text-[11px] font-black text-zinc-500">{ui("إلى", "To")}</span>
            <input type="date" value={filters.to} onChange={(e) => updateFilter("to", e.target.value)} className="mt-1 w-full rounded-2xl border border-zinc-100 bg-zinc-50 px-3 py-3 text-sm outline-none dark:border-white/10 dark:bg-zinc-900 dark:text-white" />
          </label>
        </div>

        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <label className="flex items-center gap-2 text-xs font-bold text-zinc-500 dark:text-zinc-300">
            <input type="checkbox" checked={projectOnly} disabled={!activeProjectId} onChange={(e) => { setProjectOnly(e.target.checked); updateFilter("page", 1); }} />
            {ui("المشروع الحالي فقط", "Current project only")}
          </label>
          <div className="flex gap-2">
            <button type="button" onClick={() => setFilters(EMPTY_FILTERS)} className="rounded-xl px-3 py-2 text-xs font-black text-zinc-500 hover:bg-zinc-100 dark:hover:bg-white/10">{ui("مسح الفلاتر", "Clear filters")}</button>
            {userRole === "SUPER_ADMIN" && retention && (
              <button type="button" onClick={runRetention} disabled={purging || !retention.expired} className="inline-flex items-center gap-2 rounded-xl border border-red-100 px-3 py-2 text-xs font-black text-red-600 disabled:opacity-40 dark:border-red-500/20 dark:text-red-300">
                <Trash2 size={14} /> {purging ? ui("جاري التنفيذ", "Running") : ui("تشغيل Retention", "Run retention")}
              </button>
            )}
          </div>
        </div>

        {error && <Notice type="error" className="mt-4">{error}</Notice>}

        <div className="mt-5 overflow-hidden rounded-3xl border border-zinc-100 dark:border-white/10">
          {loading ? (
            <div className="p-8 text-center text-sm font-bold text-zinc-400">{ui("جاري تحميل السجل...", "Loading audit events...")}</div>
          ) : entries.length === 0 ? (
            <div className="grid place-items-center gap-2 p-10 text-center text-sm text-zinc-400"><Search size={26} /> {ui("لا توجد أحداث مطابقة.", "No matching events.")}</div>
          ) : (
            <div className="divide-y divide-zinc-100 dark:divide-white/10">
              {entries.map((entry) => {
                const expanded = selectedId === entry.id;
                return (
                  <article key={entry.id} className="bg-white px-4 py-3 dark:bg-zinc-950">
                    <button type="button" onClick={() => setSelectedId(expanded ? "" : entry.id)} className="grid w-full gap-3 text-start md:grid-cols-[135px_1fr_175px]">
                      <div className="flex flex-wrap gap-1.5">
                        <span className={`rounded-full px-2.5 py-1 text-[10px] font-black ${badgeClass(entry.severity)}`}>{entry.severity || "INFO"}</span>
                        <span className="rounded-full bg-zinc-100 px-2.5 py-1 text-[10px] font-black text-zinc-600 dark:bg-white/10 dark:text-zinc-200">{entry.category || "GENERAL"}</span>
                      </div>
                      <div className="min-w-0">
                        <div className="truncate font-black text-zinc-950 dark:text-white">{entry.action}</div>
                        <div className="mt-1 truncate text-xs text-zinc-500 dark:text-zinc-400">{actorLabel(entry.actor)} · {entry.entityType || "—"}{entry.entityId ? `:${entry.entityId}` : ""} · {entry.outcome}</div>
                        {entry.route && <div className="mt-1 truncate font-mono text-[10px] text-zinc-400">{entry.httpMethod || ""} {entry.route}</div>}
                      </div>
                      <div className="text-xs font-bold text-zinc-400 md:text-left">{formatDate(entry.occurredAt || entry.createdAt, isEnglish)}</div>
                    </button>
                    {expanded && (
                      <div className="mt-3 grid gap-3 rounded-2xl bg-zinc-50 p-4 text-xs dark:bg-white/5 md:grid-cols-2">
                        <div><b>Request ID:</b> <span className="font-mono text-zinc-500">{entry.requestId || "—"}</span></div>
                        <div><b>IP:</b> <span className="font-mono text-zinc-500">{entry.ipAddress || "—"}</span></div>
                        {entry.errorCode && <div className="text-red-600"><b>Error:</b> {entry.errorCode}</div>}
                        <pre className="max-h-52 overflow-auto whitespace-pre-wrap rounded-xl bg-white p-3 text-[11px] text-zinc-600 dark:bg-zinc-950 dark:text-zinc-300 md:col-span-2">{JSON.stringify(entry.metadata || {}, null, 2)}</pre>
                      </div>
                    )}
                  </article>
                );
              })}
            </div>
          )}
        </div>

        <div className="mt-4 flex items-center justify-between text-xs font-bold text-zinc-500">
          <span>{ui("صفحة", "Page")} {pageInfo.page} / {pageInfo.totalPages}</span>
          <div className="flex gap-2">
            <button type="button" disabled={pageInfo.page <= 1} onClick={() => updateFilter("page", pageInfo.page - 1)} className="rounded-xl border border-zinc-100 px-3 py-2 disabled:opacity-40 dark:border-white/10">{ui("السابق", "Previous")}</button>
            <button type="button" disabled={pageInfo.page >= pageInfo.totalPages} onClick={() => updateFilter("page", pageInfo.page + 1)} className="rounded-xl border border-zinc-100 px-3 py-2 disabled:opacity-40 dark:border-white/10">{ui("التالي", "Next")}</button>
          </div>
        </div>
      </div>
    </section>
  );
}
