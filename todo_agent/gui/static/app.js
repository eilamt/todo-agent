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
      if (!btn.dataset.view) return; // skip non-view buttons (collapse-all)
      currentView = btn.dataset.view;
      document.querySelectorAll(".filter-btn[data-view]").forEach(b =>
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

  // Global collapse/expand
  const collapseBtn = document.getElementById("collapse-all-btn");
  if (collapseBtn) {
    collapseBtn.addEventListener("click", () => {
      const bodies = document.querySelectorAll(".card-body");
      const anyVisible = [...bodies].some(b => !b.classList.contains("hidden"));
      bodies.forEach(b => b.classList.toggle("hidden", anyVisible));
      // Update all collapse toggles
      document.querySelectorAll(".collapse-toggle").forEach(t => {
        t.textContent = anyVisible ? "▶" : "▼";
      });
      collapseBtn.textContent = anyVisible ? "Expand all" : "Collapse all";
    });
  }

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
    // Reset collapse button label after re-render (cards default to expanded)
    const collapseBtn = document.getElementById("collapse-all-btn");
    if (collapseBtn) collapseBtn.textContent = "Collapse all";
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

  // Project title — click to edit inline
  const titleEl = el("span", "project-title");
  titleEl.textContent = project.name;
  makeInlineEdit(
    titleEl,
    "input",
    project.name,
    v => v.trim().length > 0,
    async v => {
      const r = await apiPatch(`/api/projects/${project.id}`, { name: v.trim() });
      if (!r.ok) throw new Error((await r.json()).error || "Save failed");
    }
  );
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

  // Meta: percent + importance (importance is editable)
  const meta = el("span", "project-meta");
  const pct = project.percent_complete !== null && project.percent_complete !== undefined
    ? `${project.percent_complete}%`
    : "—";
  meta.appendChild(document.createTextNode(`  ${pct}  ·  imp `));
  const impSpan = el("span", "project-importance-val");
  impSpan.textContent = project.importance;
  makeInlineEdit(
    impSpan,
    "input",
    String(project.importance),
    v => Number.isInteger(+v) && +v >= 0 && +v <= 100,
    async v => {
      const r = await apiPatch(`/api/projects/${project.id}`, { importance: +v });
      if (!r.ok) throw new Error((await r.json()).error || "Save failed");
    },
    "number"
  );
  meta.appendChild(impSpan);
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
    if (e.target.tagName === "SELECT" || e.target.tagName === "BUTTON" || e.target.tagName === "INPUT") return;
    collapsed = !collapsed;
    body.classList.toggle("hidden", collapsed);
  });

  return section;
}

function buildItemCard(lane, project, item) {
  const imp = item.importance ?? 50;
  const card = el("div", "item-card");
  card.dataset.status = item.status;
  card.dataset.importance = imp;
  if (imp > 80) card.classList.add("item-high-importance");

  // Title row: title + collapse toggle + delete
  const titleRow = el("div", "item-title-row");

  const titleSpan = el("span", "item-title-text");
  titleSpan.textContent = item.title;
  makeInlineEdit(
    titleSpan,
    "input",
    item.title,
    v => v.trim().length > 0,
    async v => {
      const r = await apiPatch(`/api/items/${item.id}`, { title: v.trim() });
      if (!r.ok) throw new Error((await r.json()).error || "Save failed");
    }
  );
  titleRow.appendChild(titleSpan);

  // Collapse toggle
  const collapseToggle = el("button", "collapse-toggle");
  collapseToggle.textContent = "▼";
  collapseToggle.title = "Collapse/expand";
  titleRow.appendChild(collapseToggle);

  // Delete button stays in title row so it's always visible
  const delBtn = el("button", "btn-delete");
  delBtn.textContent = "✕";
  delBtn.title = "Delete item";
  delBtn.addEventListener("click", () => confirmDeleteItem(item));
  titleRow.appendChild(delBtn);

  card.appendChild(titleRow);

  // Card body — everything below the title row, collapsible
  const cardBody = el("div", "card-body");

  // Description
  if (item.description) {
    const descEl = el("p", "item-description");
    descEl.textContent = item.description;
    makeInlineEdit(
      descEl,
      "textarea",
      item.description,
      () => true,
      async v => {
        const r = await apiPatch(`/api/items/${item.id}`, { description: v.trim() || null });
        if (!r.ok) throw new Error((await r.json()).error || "Save failed");
      }
    );
    const clearDescBtn = el("button", "btn-clear-desc");
    clearDescBtn.textContent = "✕";
    clearDescBtn.title = "Clear description";
    clearDescBtn.addEventListener("click", async () => {
      await apiPatch(`/api/items/${item.id}`, { description: null });
      await poll();
    });
    const descWrap = el("div", "desc-wrap");
    descWrap.appendChild(descEl);
    descWrap.appendChild(clearDescBtn);
    cardBody.appendChild(descWrap);
  } else {
    const addDescLink = el("span", "add-desc-link");
    addDescLink.textContent = "+ add description";
    addDescLink.addEventListener("click", () => {
      const ta = document.createElement("textarea");
      ta.className = "inline-edit-input";
      ta.rows = 2;
      ta.placeholder = "Add description…";
      addDescLink.replaceWith(ta);
      ta.focus();
      const save = async () => {
        const val = ta.value.trim();
        if (val) {
          await apiPatch(`/api/items/${item.id}`, { description: val });
          await poll();
        } else {
          ta.replaceWith(addDescLink);
        }
      };
      ta.addEventListener("blur", save);
      ta.addEventListener("keydown", e => {
        if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); save(); }
        if (e.key === "Escape") ta.replaceWith(addDescLink);
      });
    });
    cardBody.appendChild(addDescLink);
  }

  // Controls row
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

  // Today checkbox
  const todayLabel = el("label", "flag-label badge badge-today");
  const todayCb = el("input");
  todayCb.type = "checkbox";
  todayCb.className = "flag-cb";
  todayCb.checked = !!item.today;
  todayCb.addEventListener("change", async () => {
    await apiPatch(`/api/items/${item.id}`, { today: todayCb.checked });
    await poll();
  });
  todayLabel.appendChild(todayCb);
  todayLabel.appendChild(document.createTextNode(" today"));
  controls.appendChild(todayLabel);

  // This-week checkbox
  const weekLabel = el("label", "flag-label badge badge-week");
  const weekCb = el("input");
  weekCb.type = "checkbox";
  weekCb.className = "flag-cb";
  weekCb.checked = !!item.this_week;
  weekCb.addEventListener("change", async () => {
    await apiPatch(`/api/items/${item.id}`, { this_week: weekCb.checked });
    await poll();
  });
  weekLabel.appendChild(weekCb);
  weekLabel.appendChild(document.createTextNode(" this-week"));
  controls.appendChild(weekLabel);

  // Deadline date input + clear
  const deadlineWrap = el("span", "deadline-wrap");
  const deadlineInput = el("input");
  deadlineInput.type = "date";
  deadlineInput.className = "deadline-input";
  deadlineInput.value = item.deadline || "";
  deadlineInput.addEventListener("change", async () => {
    await apiPatch(`/api/items/${item.id}`, { deadline: deadlineInput.value || null });
    await poll();
  });
  deadlineWrap.appendChild(deadlineInput);
  if (item.deadline) {
    const clrDeadline = el("button", "btn-clear-deadline");
    clrDeadline.textContent = "✕";
    clrDeadline.title = "Clear deadline";
    clrDeadline.addEventListener("click", async () => {
      await apiPatch(`/api/items/${item.id}`, { deadline: null });
      await poll();
    });
    deadlineWrap.appendChild(clrDeadline);
  }
  controls.appendChild(deadlineWrap);

  // Importance badge — click to edit
  const impBadge = el("span", "badge badge-importance");
  impBadge.textContent = imp;
  makeInlineEdit(
    impBadge,
    "input",
    String(imp),
    v => Number.isInteger(+v) && +v >= 0 && +v <= 100,
    async v => {
      const r = await apiPatch(`/api/items/${item.id}`, { importance: +v });
      if (!r.ok) throw new Error((await r.json()).error || "Save failed");
    },
    "number"
  );
  controls.appendChild(impBadge);

  cardBody.appendChild(controls);
  card.appendChild(cardBody);

  // Wire collapse toggle
  collapseToggle.addEventListener("click", e => {
    e.stopPropagation();
    const hidden = cardBody.classList.toggle("hidden");
    collapseToggle.textContent = hidden ? "▶" : "▼";
  });

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

// ---- Inline edit factory --------------------------------------------------

/**
 * makeInlineEdit — attach click-to-edit behaviour to a display element.
 *
 * @param {HTMLElement} displayEl  Element showing the current value.
 * @param {string}      inputTag   "input" or "textarea".
 * @param {string}      currentVal Initial value for the input.
 * @param {Function}    validate   (string) => boolean — client-side guard.
 * @param {Function}    onSave     async (string) => void — throws on failure.
 * @param {string}      inputType  For <input>, the type attribute (default "text").
 */
function makeInlineEdit(displayEl, inputTag, currentVal, validate, onSave, inputType = "text") {
  displayEl.classList.add("editable");
  displayEl.style.cursor = "pointer";

  displayEl.addEventListener("click", e => {
    e.stopPropagation();
    const input = document.createElement(inputTag);
    input.className = "inline-edit-input";
    if (inputTag === "input") {
      input.type = inputType;
      if (inputType === "number") { input.min = "0"; input.max = "100"; }
    }
    input.value = currentVal;

    const restore = () => {
      if (input.parentNode) input.replaceWith(displayEl);
    };

    const commit = async () => {
      const val = input.value;
      if (!validate(val)) { restore(); return; }
      try {
        await onSave(val);
        await poll();
      } catch (_) {
        restore();
      }
    };

    displayEl.replaceWith(input);
    input.focus();
    if (inputTag === "input") input.select();

    input.addEventListener("blur", commit);
    input.addEventListener("keydown", e => {
      if (e.key === "Enter") { e.preventDefault(); input.removeEventListener("blur", commit); commit(); }
      if (e.key === "Escape") { input.removeEventListener("blur", commit); restore(); }
    });
  });
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
