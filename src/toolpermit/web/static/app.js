"use strict";

let csrfToken = "";
const approvalsNode = document.querySelector("#approvals");
const runsNode = document.querySelector("#runs");
const eventsNode = document.querySelector("#events");
const runFilter = document.querySelector("#run-filter");
const statusNode = document.querySelector("#status");

function textElement(tag, className, value) {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = String(value);
  return node;
}

function clear(node) {
  while (node.firstChild) node.removeChild(node.firstChild);
}

function empty(node, message) {
  node.append(textElement("p", "empty", message));
}

function detail(label, value) {
  const row = document.createElement("div");
  row.className = "detail";
  row.append(textElement("dt", "detail-label", label));
  row.append(textElement("dd", "detail-value", value));
  return row;
}

async function jsonRequest(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) throw new Error(`Request failed (${response.status})`);
  return response.json();
}

async function decide(id, action) {
  await jsonRequest(`/api/approvals/${encodeURIComponent(id)}/${action}`, {
    method: "POST",
    headers: {"X-CSRF-Token": csrfToken},
  });
  statusNode.textContent = `Approval ${action}d.`;
  await refresh();
}

function renderApprovals(items) {
  clear(approvalsNode);
  if (items.length === 0) {
    empty(approvalsNode, "No pending approvals.");
    return;
  }
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "card pending";
    card.append(textElement("p", "state", "PENDING — action required"));
    card.append(textElement("h3", "tool", item.event.tool_name));
    const values = document.createElement("dl");
    values.append(detail("Rule", item.event.rule_id));
    values.append(detail("Session", item.event.connection_id));
    values.append(detail("Arguments (redacted)", JSON.stringify(item.event.arguments, null, 2)));
    card.append(values);
    const actions = document.createElement("div");
    actions.className = "actions";
    const approve = textElement("button", "approve", "Approve once");
    approve.type = "button";
    approve.setAttribute("aria-label", `Approve ${item.event.tool_name} once`);
    approve.addEventListener("click", () => decide(item.id, "approve"));
    const reject = textElement("button", "reject", "Reject");
    reject.type = "button";
    reject.setAttribute("aria-label", `Reject ${item.event.tool_name}`);
    reject.addEventListener("click", () => decide(item.id, "reject"));
    actions.append(approve, reject);
    card.append(actions);
    approvalsNode.append(card);
  }
}

function renderRuns(items) {
  clear(runsNode);
  clear(runFilter);
  if (items.length === 0) {
    empty(runsNode, "No recorded runs yet.");
    empty(eventsNode, "Select a run to inspect events.");
    return;
  }
  for (const item of items.slice(0, 20)) {
    const option = document.createElement("option");
    option.value = item.id;
    option.textContent = `${item.id} — ${item.mode}`;
    runFilter.append(option);
    const card = document.createElement("article");
    card.className = "card";
    card.append(textElement("p", "state", `${item.mode.toUpperCase()} MODE`));
    card.append(textElement("h3", "run", item.id));
    card.append(textElement("p", "command", item.upstream_command.join(" ")));
    card.append(textElement("p", "timestamp", new Date(item.started_at * 1000).toLocaleString()));
    runsNode.append(card);
  }
}

function renderEvents(items) {
  clear(eventsNode);
  if (items.length === 0) {
    empty(eventsNode, "No events match these filters.");
    return;
  }
  for (const item of items) {
    const card = document.createElement("article");
    card.className = "card";
    card.append(textElement("p", "state", `${item.decision.toUpperCase()} — ${item.lifecycle}`));
    card.append(textElement("h3", "tool", item.tool_name));
    const values = document.createElement("dl");
    values.append(detail("Rule", item.rule_id));
    values.append(detail("Session", item.connection_id));
    values.append(detail("Arguments (redacted)", JSON.stringify(item.arguments, null, 2)));
    card.append(values);
    eventsNode.append(card);
  }
}

async function loadEvents() {
  if (!runFilter.value) return;
  const parameters = new URLSearchParams();
  for (const name of ["decision", "tool", "session", "rule"]) {
    const value = document.querySelector(`#${name}-filter`).value.trim();
    if (value) parameters.set(name, value);
  }
  const suffix = parameters.size ? `?${parameters.toString()}` : "";
  const result = await jsonRequest(`/api/runs/${encodeURIComponent(runFilter.value)}${suffix}`);
  renderEvents(result.events);
}

async function refresh() {
  try {
    statusNode.textContent = "Refreshing local state…";
    const [approvals, runs] = await Promise.all([
      jsonRequest("/api/approvals"),
      jsonRequest("/api/runs"),
    ]);
    renderApprovals(approvals.approvals);
    renderRuns(runs.runs);
    await loadEvents();
    statusNode.textContent = `Updated. ${approvals.approvals.length} approval(s) pending.`;
  } catch (error) {
    statusNode.textContent = `Unable to load local state: ${error.message}`;
  }
}

async function start() {
  const session = await jsonRequest("/api/session");
  csrfToken = session.csrf_token;
  await refresh();
}

document.querySelector("#refresh").addEventListener("click", refresh);
document.querySelector("#filters").addEventListener("submit", (event) => {
  event.preventDefault();
  loadEvents().catch((error) => { statusNode.textContent = `Filtering failed: ${error.message}`; });
});
start().catch((error) => { statusNode.textContent = `Startup failed: ${error.message}`; });
