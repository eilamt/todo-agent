/* todo-agent browser GUI
 * Polling every 5 s with If-Modified-Since / 304 to stay in sync with CLI changes.
 */

"use strict";

let lastModified = null;
let currentView = "all";   // "all" | "today" | "this-week"
let storeData = null;      // full data snapshot from /api/data

// ---- Initialisation -------------------------------------------------------

document.addEventListener("DOMContentLoaded", () => {
  // Read initial view from URL ?view=...
  const params = new URLSearchParams(window.location.search);
  const viewParam = params.get("view");
  if (["all", "today", "this-week"].includes(viewParam)) {
    currentView = viewParam;
  }

  // Activate correct filter button
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.classList.toggle("active", btn.dataset.view === currentView);
    btn.addEventListener("click", () => {
      currentView = btn.dataset.view;
      document.querySelectorAll(".filter-btn").forEach(b =>
        b.classList.toggle("active", b === btn)
      );
      if (storeData) render(storeData, currentView);
    });
  });

  // Add-lane toggle
  document.getElementById("show-add-lane").addEventListener("click", () => {
    document.getElementById("add-lane-form").classList.remove("hidden");
    document.getElementById("new-lane-name").focus();
  });
  document.getElementById("cancel-add-lane").addEventListener("click", () => {
    document.getElementById("add-lane-form").classList.add("hidden");
  });
  document.getElementById("add-lane-form").addEventListener("submit", async e => {
    e.preventDefault();
    const name = document.getElementById("new-lane-name").value.trim();
    if (!name) return;
    await apiPost("/api/lanes", { name });
    document.getElementById("new-lane-name").value = "";
    document.getElementById("add-lane-form").classList.add("hidden");
    await poll();
  });

  poll();
  setInterval(poll, 5000);
});

// ---- Polling --------------------------------------------------------------

async function poll() {
  const headers = {};
  if (lastModified) headers["If-Modified-Since"] = lastModified;
  try {
    const res = await fetch("/api/data", { headers });
    if (res.status === 304) return;       // unchanged
    if (!res.ok) return;
    lastModified = res.headers.get("Last-Modified");
    storeData = await res.json();
    render(storeData, currentView);
  } catch (_) { /* ignore network errors */ }
}

// ---- Render ---------------------------------------------------------------

function render(data, view) {
  const board = document.getElementById("board");
  board.innerHTML = "";

  if (!data.lanes || data.lanes.length === 0) {
    board.innerHTML = '<p class="empty-state">No lanes yet. Add one above.</p>';
    return;
  }

  data.lanes.forEach(lane => {
    board.appendChild(buildLaneCol(lane, view));
  });
}

function buildLaneCol(lane, view) {
  const col = el("div", "lane-col");

  // Header
  const header = el("div", "lane-header");
  const title = el("span", "lane-title");
  title.textContent = lane.name;
  header.appendChild(title);

  const delBtn = el("button", "btn-delete");
  delBtn.textContent = "✕";
  delBtn.title = "Delete lane";
  delBtn.addEventListener("click", () => confirmDeleteLane(lane));
  header.appendChild(delBtn);
  col.appendChild(header);

  // Projects
  lane.projects.forEach(project => {
    const visibleItems = filteredItems(project.items, view);
    if (view !== "all" && visibleItems.length === 0) return;
    col.appendChild(buildProjectSection(lane, project, visibleItems));
  });

  // Add project form
  col.appendChild(buildAddProjectForm(lane));

  return col;
}

function buildProjectSection(lane, project, visibleItems) {
  const section = el("div", "project-section");

  // Header (clickable to collapse)
  const header = el("div", "project-header");
  header.title = "Click to expand/collapse";
  const titleEl = el("span", "project-title");
  titleEl.textContent = project.name;
  header.appendChild(titleEl);

  const statusSel = buildStatusSelect(
    ["not-started", "scheduled", "in-progress", "completed"],
    project.status,
    async val => {
      await apiPatch(`/api/projects/${project.id}`, { status: val });
      await poll();
    }
  );
  header.appendChild(statusSel);

  const meta = el("span", "project-meta");
  const pct = project.percent_complete !== null && project.percent_complete !== undefined
    ? `${project.percent_complete}%`
    : "—";
  meta.textContent = `  ${pct}  ·  imp ${project.importance}`;
  header.appendChild(meta);

  const delBtn = el("button", "btn-delete");
  delBtn.textContent = "✕";
  delBtn.title = "Delete project";
  delBtn.addEventListener("click", e => { e.stopPropagation(); confirmDeleteProject(project); });
  header.appendChild(delBtn);

  section.appendChild(header);

  // Body
  const body = el("div", "project-body");
  if (visibleItems.length === 0) {
    body.innerHTML = '<p class="empty-state">No items.</p>';
  } else {
    visibleItems.forEach(item => body.appendChild(buildItemCard(lane, project, item)));
  }
  body.appendChild(buildAddItemForm(lane, project));
  section.appendChild(body);

  // Collapse toggle
  let collapsed = false;
  header.addEventListener("click", e => {
    if (e.target.tagName === "SELECT" || e.target.tagName === "BUTTON") return;
    collapsed = !collapsed;
    body.classList.toggle("hidden", collapsed);
  });

  return section;
}

function buildItemCard(lane, project, item) {
  const card = el("div", "item-card");
  card.dataset.status = item.status;

  const titleEl = el("div", "item-title");
  titleEl.textContent = item.title;
  card.appendChild(titleEl);

  const controls = el("div", "item-controls");

  // Status select
  const statusSel = buildStatusSelect(
    ["not-started", "in-progress", "completed"],
    item.status,
    async val => {
      await apiPatch(`/api/items/${item.id}`, { status: val });
      await poll();
    }
  );
  controls.appendChild(statusSel);

  // Flags
  if (item.today) {
    const b = el("span", "badge badge-today");
    b.textContent = "today";
    controls.appendChild(b);
  }
  if (item.this_week) {
    const b = el("span", "badge badge-week");
    b.textContent = "this-week";
    controls.appendChild(b);
  }
  if (item.deadline) {
    const b = el("span", "badge badge-deadline");
    b.textContent = item.deadline;
    controls.appendChild(b);
  }

  // Delete
  const delBtn = el("button", "btn-delete");
  delBtn.textContent = "✕";
  delBtn.title = "Delete item";
  delBtn.addEventListener("click", () => confirmDeleteItem(item));
  controls.appendChild(delBtn);

  card.appendChild(controls);
  return card;
}

function buildAddProjectForm(lane) {
  const wrap = el("div", "inline-form");
  const input = el("input");
  input.type = "text";
  input.placeholder = "New project…";
  const addBtn = el("button");
  addBtn.textContent = "Add";
  addBtn.type = "button";
  addBtn.addEventListener("click", async () => {
    const name = input.value.trim();
    if (!name) return;
    await apiPost(`/api/lanes/${lane.id}/projects`, { name });
    input.value = "";
    await poll();
  });
  wrap.appendChild(input);
  wrap.appendChild(addBtn);
  return wrap;
}

function buildAddItemForm(lane, project) {
  const wrap = el("div", "inline-form");
  const input = el("input");
  input.type = "text";
  input.placeholder = "New item…";
  const addBtn = el("button");
  addBtn.textContent = "Add";
  addBtn.type = "button";
  addBtn.addEventListener("click", async () => {
    const title = input.value.trim();
    if (!title) return;
    await apiPost(`/api/projects/${project.id}/items`, { title });
    input.value = "";
    await poll();
  });
  wrap.appendChild(input);
  wrap.appendChild(addBtn);
  return wrap;
}

// ---- Status select --------------------------------------------------------

function buildStatusSelect(options, current, onChange) {
  const sel = el("select");
  options.forEach(opt => {
    const o = document.createElement("option");
    o.value = opt;
    o.textContent = opt;
    if (opt === current) o.selected = true;
    sel.appendChild(o);
  });
  sel.addEventListener("change", () => onChange(sel.value));
  return sel;
}

// ---- Confirmation modal ---------------------------------------------------

function showModal(message, onConfirm) {
  const modal = document.getElementById("modal");
  document.getElementById("modal-message").textContent = message;
  modal.classList.remove("hidden");

  const confirmBtn = document.getElementById("modal-confirm");
  const cancelBtn = document.getElementById("modal-cancel");

  function cleanup() {
    modal.classList.add("hidden");
    confirmBtn.replaceWith(confirmBtn.cloneNode(true));
    cancelBtn.replaceWith(cancelBtn.cloneNode(true));
  }

  document.getElementById("modal-confirm").addEventListener("click", async () => {
    cleanup();
    await onConfirm();
    await poll();
  });
  document.getElementById("modal-cancel").addEventListener("click", cleanup);
}

function confirmDeleteLane(lane) {
  const projCount = lane.projects.length;
  const itemCount = lane.projects.reduce((s, p) => s + p.items.length, 0);
  showModal(
    `Delete lane "${lane.name}"? This will also remove ${projCount} project(s) and ${itemCount} item(s).`,
    () => apiDelete(`/api/lanes/${lane.id}`)
  );
}

function confirmDeleteProject(project) {
  const itemCount = project.items.length;
  showModal(
    `Delete project "${project.name}"? This will also remove ${itemCount} item(s).`,
    () => apiDelete(`/api/projects/${project.id}`)
  );
}

function confirmDeleteItem(item) {
  showModal(
    `Delete item "${item.title}"?`,
    () => apiDelete(`/api/items/${item.id}`)
  );
}

// ---- API helpers ----------------------------------------------------------

async function apiPost(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function apiPatch(url, body) {
  return fetch(url, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function apiDelete(url) {
  return fetch(url, { method: "DELETE" });
}

// ---- DOM helper -----------------------------------------------------------

function el(tag, className) {
  const e = document.createElement(tag);
  if (className) e.className = className;
  return e;
}

// ---- Filter helper --------------------------------------------------------

function filteredItems(items, view) {
  if (view === "all") return items;
  if (view === "today") return items.filter(i => i.today === true);
  if (view === "this-week") return items.filter(i => i.this_week === true);
  return items;
}
