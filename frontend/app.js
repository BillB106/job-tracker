// ---------- tiny API helper ----------
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (res.status === 401) { showLogin(); throw new Error("unauthorized"); }
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || res.statusText);
  return res.status === 204 ? null : res.json();
}

const $ = (id) => document.getElementById(id);
let gridApi = null;
let META = { prio_values: [], status_values: [] };

// ---------- auth ----------
function showLogin() { $("login").classList.remove("hidden"); $("app").classList.add("hidden"); }
function showApp() { $("login").classList.add("hidden"); $("app").classList.remove("hidden"); }

$("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  $("login-error").textContent = "";
  try {
    await api("/api/login", { method: "POST", body: JSON.stringify({ password: $("password").value }) });
    await boot();
  } catch (err) {
    $("login-error").textContent = "Wrong password.";
  }
});

$("logout-btn").addEventListener("click", async () => {
  await api("/api/logout", { method: "POST" });
  location.reload();
});

// ---------- grid ----------
// Renders the job title as a link to its posting (still editable on double-click).
function titleRenderer(p) {
  const url = p.data && p.data.source_url;
  if (url) {
    const a = document.createElement("a");
    a.href = url; a.target = "_blank"; a.rel = "noopener";
    a.textContent = p.value || "(no title)";
    a.style.color = "#0563C1";
    return a;
  }
  return p.value || "";
}

function buildColumns() {
  const editableText = { editable: true, cellEditor: "agTextCellEditor" };
  return [
    { field: "job_portal", headerName: "Job Portal", width: 130, ...editableText },
    { field: "prio", headerName: "Prio", width: 150, editable: true,
      cellEditor: "agSelectCellEditor", cellEditorParams: { values: META.prio_values } },
    { field: "status", headerName: "Status", width: 110, editable: true,
      cellEditor: "agSelectCellEditor", cellEditorParams: { values: META.status_values } },
    { field: "title", headerName: "Job Title", width: 340, editable: true,
      cellEditor: "agTextCellEditor", cellRenderer: titleRenderer },
    { field: "company", headerName: "Company", width: 170, ...editableText },
    { field: "location", headerName: "Location", width: 200, ...editableText },
    { field: "work_type", headerName: "Work Type", width: 110, ...editableText },
    { field: "posted_date", headerName: "Posted (approx)", width: 140 },
    { field: "posted", headerName: "Posted", width: 150 },
    { field: "applicants", headerName: "Applicants / Clicks", width: 160 },
    { field: "apply_method", headerName: "Apply Method", width: 130 },
    { field: "notes", headerName: "Notes", width: 240, editable: true,
      cellEditor: "agLargeTextCellEditor", cellEditorPopup: true },
    { headerName: "", width: 60, filter: false, sortable: false, editable: false,
      cellRenderer: (p) => {
        const b = document.createElement("button");
        b.textContent = "✕"; b.title = "Delete";
        b.style.cssText = "border:0;background:transparent;color:#c0392b;cursor:pointer;font-size:14px;";
        b.addEventListener("click", () => deleteRow(p.data));
        return b;
      } },
  ];
}

async function deleteRow(row) {
  if (!confirm(`Delete "${row.title}"?`)) return;
  await api(`/api/jobs/${row.id}`, { method: "DELETE" });
  gridApi.applyTransaction({ remove: [row] });
  updateCount();
}

async function onCellValueChanged(e) {
  const field = e.colDef.field;
  const patch = { [field]: e.newValue };
  try {
    const updated = await api(`/api/jobs/${e.data.id}`, { method: "PATCH", body: JSON.stringify(patch) });
    e.node.setData(updated);
    if (field === "prio" || field === "status") gridApi.redrawRows({ rowNodes: [e.node] }); // re-apply row styling

  } catch (err) {
    alert("Update failed: " + err.message);
    e.node.setDataValue(field, e.oldValue); // revert
  }
}

function updateCount() {
  const total = gridApi.getDisplayedRowCount();
  $("count").textContent = `${total} jobs shown`;
}

async function initGrid() {
  const jobs = await api("/api/jobs");
  const gridOptions = {
    theme: agGrid.themeQuartz,
    columnDefs: buildColumns(),
    rowData: jobs,
    defaultColDef: {
      sortable: true,
      filter: "agTextColumnFilter",
      floatingFilter: true,   // per-column filter box under each header
      resizable: true,
      minWidth: 70,
    },
    rowHeight: 36,
    rowClassRules: {
      "prio-tackle": (p) => p.data && p.data.prio === "Tackle now",
      "prio-eye": (p) => p.data && p.data.prio === "Keep an eye on",
      "prio-applied": (p) => p.data && p.data.prio === "Applied / in progress",
      "prio-discard": (p) => p.data && p.data.prio === "Discard / not interested",
      "status-offline": (p) => p.data && p.data.status === "Offline",
    },
    onCellValueChanged,
    onModelUpdated: updateCount,
    stopEditingWhenCellsLoseFocus: true,
  };
  gridApi = agGrid.createGrid($("grid"), gridOptions);
  updateCount();
}

$("add-btn").addEventListener("click", async () => {
  const job = await api("/api/jobs", {
    method: "POST",
    body: JSON.stringify({ title: "New job", job_portal: "LinkedIn" }),
  });
  gridApi.applyTransaction({ add: [job], addIndex: 0 });
  updateCount();
});

$("export-btn").addEventListener("click", async () => {
  const btn = $("export-btn");
  const orig = btn.textContent;
  btn.disabled = true; btn.textContent = "Exporting…";
  try {
    const res = await fetch("/api/export.xlsx");
    if (res.status === 401) { showLogin(); return; }
    if (!res.ok) throw new Error(res.statusText);
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url; a.download = "job_tracker_export.xlsx";
    document.body.appendChild(a); a.click(); a.remove();
    URL.revokeObjectURL(url);
  } catch (e) {
    alert("Export failed: " + e.message);
  } finally {
    btn.disabled = false; btn.textContent = orig;
  }
});

$("clear-filters-btn").addEventListener("click", () => {
  gridApi.setFilterModel(null);
});

// ---------- boot ----------
async function boot() {
  META = await api("/api/meta");
  showApp();
  if (gridApi) { gridApi.setGridOption("rowData", await api("/api/jobs")); }
  else { await initGrid(); }
}

(async function start() {
  const me = await fetch("/api/me").then((r) => r.json());
  if (me.authenticated) await boot();
  else showLogin();
})();
