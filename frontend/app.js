const CATEGORIES = [
  { code: "COD", name: "Coding" },
  { code: "DSA", name: "Data Structures & Algorithms" },
  { code: "OOD", name: "Object-Oriented Design" },
  { code: "APTI", name: "Aptitude" },
  { code: "COMM", name: "Communication" },
  { code: "AI", name: "Artificial Intelligence" },
  { code: "CLOUD", name: "Cloud Computing" },
  { code: "SQL", name: "Database" },
  { code: "SWE", name: "Software Engineering" },
  { code: "SYSD", name: "System Design" },
  { code: "NETW", name: "Networking" },
  { code: "OS", name: "Operating Systems" },
];

const JOB_FIELDS = [
  ["department", "Department"],
  ["employment_type", "Employment type"],
  ["location", "Location"],
  ["experience", "Experience"],
  ["education", "Education"],
];

let selectedFile = null;
let lastResult = null;
let currentMode = "file";

const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("file-input");
const fileChip = document.getElementById("file-chip");
const fileChipName = document.getElementById("file-chip-name");
const fileChipRemove = document.getElementById("file-chip-remove");
const modeButtons = document.querySelectorAll(".mode-btn");
const textEntry = document.getElementById("text-entry");
const jdTextInput = document.getElementById("jd-text-input");
const scanBtn = document.getElementById("scan-btn");
const statusLine = document.getElementById("status-line");
const emptyState = document.getElementById("empty-state");
const results = document.getElementById("results");
const jobCard = document.getElementById("job-card");
const categoryGrid = document.getElementById("category-grid");
const skillsList = document.getElementById("skills-list");
const rawJson = document.getElementById("raw-json");
const downloadBtn = document.getElementById("download-json-btn");
const toggleRawBtn = document.getElementById("toggle-raw-btn");

// ---- File selection ----
dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => { e.preventDefault(); dropzone.classList.add("dragover"); });
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("dragover"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("dragover");
  if (e.dataTransfer.files.length) setFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) setFile(fileInput.files[0]);
});
fileChipRemove.addEventListener("click", (e) => {
  e.stopPropagation();
  clearFile();
});

modeButtons.forEach((button) => {
  button.addEventListener("click", () => setMode(button.dataset.mode));
});

jdTextInput.addEventListener("input", () => {
  if (currentMode === "text") {
    scanBtn.disabled = jdTextInput.value.trim().length < 30;
  }
});

function setMode(mode) {
  currentMode = mode;
  const isTextMode = mode === "text";

  modeButtons.forEach((button) => {
    const active = button.dataset.mode === mode;
    button.classList.toggle("active", active);
  });

  dropzone.classList.toggle("hidden", isTextMode);
  textEntry.classList.toggle("hidden", !isTextMode);

  if (isTextMode) {
    scanBtn.disabled = jdTextInput.value.trim().length < 30;
    setStatus("Paste a full job description to analyze.");
  } else {
    scanBtn.disabled = !selectedFile;
    setStatus(selectedFile ? "Ready to scan selected file." : "");
  }
}

function setFile(file) {
  const okType = /\.(pdf|docx)$/i.test(file.name);
  if (!okType) {
    setStatus("Only .pdf or .docx files are supported.", true);
    return;
  }
  if (file.size > 10 * 1024 * 1024) {
    setStatus("File exceeds 10MB limit.", true);
    return;
  }
  selectedFile = file;
  fileChipName.textContent = file.name;
  fileChip.classList.remove("hidden");
  scanBtn.disabled = false;
  setStatus("");
}

function clearFile() {
  selectedFile = null;
  fileInput.value = "";
  fileChip.classList.add("hidden");
  scanBtn.disabled = true;
}

function setStatus(msg, isError = false) {
  statusLine.textContent = msg;
  statusLine.classList.toggle("error", isError);
}

// ---- Scan ----
scanBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  scanBtn.disabled = true;
  scanBtn.classList.add("scanning");
  scanBtn.querySelector(".scan-btn-label").textContent = "Scanning…";
  setStatus("Reading document and resolving RADIX signals…");

  const formData = new FormData();
  formData.append("file", selectedFile);

  try {
    const res = await fetch("/api/analyze", { method: "POST", body: formData });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Analysis failed.");
    }

    lastResult = data;
    renderResults(data);
    setStatus(`Scan complete · ${data.skills.length} skills mapped.`);
  } catch (err) {
    setStatus(err.message || "Something went wrong.", true);
  } finally {
    scanBtn.disabled = false;
    scanBtn.classList.remove("scanning");
    scanBtn.querySelector(".scan-btn-label").textContent = "Scan document";
  }
});

// ---- Render ----
function renderResults(data) {
  emptyState.classList.add("hidden");
  results.classList.remove("hidden");

  renderJobCard(data);
  renderCategoryGrid(data.skills);
  renderSkillsList(data.skills);
  rawJson.textContent = JSON.stringify(data, null, 2);
  rawJson.classList.add("hidden");
  toggleRawBtn.textContent = "View raw JSON";
}

function field(v) {
  return v && String(v).trim() ? String(v) : null;
}

function renderJobCard(data) {
  const role = field(data.role) || "Role not specified";
  const company = field(data.company);

  let html = `<div class="job-role">${escapeHtml(role)}${company ? ` <span style="color:var(--slate); font-size:15px; font-weight:400;">@ ${escapeHtml(company)}</span>` : ""}</div>`;

  for (const [key, label] of JOB_FIELDS) {
    const v = field(data[key]);
    html += `
      <div class="job-field">
        <span class="k">${label}</span>
        <span class="v ${v ? "" : "empty"}">${v ? escapeHtml(v) : "not specified"}</span>
      </div>`;
  }

  jobCard.innerHTML = html;
}

function renderCategoryGrid(skills) {
  const counts = {};
  for (const c of CATEGORIES) counts[c.code] = 0;
  for (const s of skills) {
    if (counts.hasOwnProperty(s.category_code)) counts[s.category_code]++;
  }

  categoryGrid.innerHTML = CATEGORIES.map((c) => {
    const count = counts[c.code];
    return `
      <div class="cat-tile ${count > 0 ? "active" : ""}">
        <div class="cat-code">${c.code}</div>
        <div class="cat-count">${count}</div>
        <div class="cat-name">${c.name}</div>
      </div>`;
  }).join("");
}

function renderSkillsList(skills) {
  if (!skills.length) {
    skillsList.innerHTML = `<p style="color:var(--slate-dim); font-family:var(--font-mono); font-size:13px;">No skills extracted.</p>`;
    return;
  }

  const byCategory = {};
  for (const c of CATEGORIES) byCategory[c.code] = [];
  for (const s of skills) {
    if (byCategory.hasOwnProperty(s.category_code)) byCategory[s.category_code].push(s);
  }

  let html = "";
  for (const c of CATEGORIES) {
    const group = byCategory[c.code];
    if (!group.length) continue;
    html += `<div class="skill-group-label">${c.code} · ${c.name}</div>`;
    for (const s of group) {
      const conf = (s.confidence || "Low").toLowerCase();
      html += `
        <div class="skill-row">
          <span class="skill-name">${escapeHtml(s.skill_name)}</span>
          <span class="confidence-badge ${conf}">${escapeHtml(s.confidence || "Low")}</span>
        </div>`;
    }
  }
  skillsList.innerHTML = html;
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

// ---- Actions ----
downloadBtn.addEventListener("click", () => {
  if (!lastResult) return;
  const blob = new Blob([JSON.stringify(lastResult, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${(lastResult.company || "jd").replace(/\s+/g, "_").toLowerCase()}_radix.json`;
  a.click();
  URL.revokeObjectURL(url);
});

toggleRawBtn.addEventListener("click", () => {
  const hidden = rawJson.classList.toggle("hidden");
  toggleRawBtn.textContent = hidden ? "View raw JSON" : "Hide raw JSON";
});
