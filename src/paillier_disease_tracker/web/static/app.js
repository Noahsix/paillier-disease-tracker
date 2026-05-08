const ui = {
  dbPath: document.getElementById("dbPath"),
  keysPath: document.getElementById("keysPath"),
  keySize: document.getElementById("keySize"),
  setupBtn: document.getElementById("setupBtn"),
  loadBtn: document.getElementById("loadBtn"),
  listDiseasesBtn: document.getElementById("listDiseasesBtn"),
  mappingTable: document.getElementById("mappingTable"),
  newDiseaseName: document.getElementById("newDiseaseName"),
  addDiseaseBtn: document.getElementById("addDiseaseBtn"),
  patientName: document.getElementById("patientName"),
  diagnosesContainer: document.getElementById("diagnosesContainer"),
  addPatientBtn: document.getElementById("addPatientBtn"),
  seedDemoBtn: document.getElementById("seedDemoBtn"),
  seedBulkBtn: document.getElementById("seedBulkBtn"),
  bulkPatients: document.getElementById("bulkPatients"),
  bulkSeed: document.getElementById("bulkSeed"),
  bulkPrefix: document.getElementById("bulkPrefix"),
  bulkBatchSize: document.getElementById("bulkBatchSize"),
  diseaseSelect: document.getElementById("diseaseSelect"),
  countBtn: document.getElementById("countBtn"),
  countFlowBtn: document.getElementById("countFlowBtn"),
  encryptedRowsBtn: document.getElementById("encryptedRowsBtn"),
  summaryRows: document.getElementById("summaryRows"),
  summaryEncrypted: document.getElementById("summaryEncrypted"),
  summaryDecrypted: document.getElementById("summaryDecrypted"),
  summaryPlain: document.getElementById("summaryPlain"),
  summaryValidation: document.getElementById("summaryValidation"),
  flowTable: document.getElementById("flowTable"),
  encryptedRowsTable: document.getElementById("encryptedRowsTable"),
  pipelineText: document.getElementById("pipelineText"),
  validateSelectedBtn: document.getElementById("validateSelectedBtn"),
  validateAllBtn: document.getElementById("validateAllBtn"),
  validationTable: document.getElementById("validationTable"),
  dbPreviewLimit: document.getElementById("dbPreviewLimit"),
  dbPreviewBtn: document.getElementById("dbPreviewBtn"),
  dbPreviewHead: document.getElementById("dbPreviewHead"),
  dbPreviewTable: document.getElementById("dbPreviewTable"),
  dbPreviewTotalPatients: document.getElementById("dbPreviewTotalPatients"),
  dbPreviewTotalDiagnoses: document.getElementById("dbPreviewTotalDiagnoses"),
  dbPreviewTotalDiseases: document.getElementById("dbPreviewTotalDiseases"),
  logOutput: document.getElementById("logOutput"),
  clearLogBtn: document.getElementById("clearLogBtn"),
  statusText: document.getElementById("statusText"),
  statusDb: document.getElementById("statusDb"),
  statusKeys: document.getElementById("statusKeys"),
  statusLastAction: document.getElementById("statusLastAction"),
  busyOverlay: document.getElementById("busyOverlay"),
  busyTitle: document.getElementById("busyTitle"),
  busyDetail: document.getElementById("busyDetail"),
  busyTimer: document.getElementById("busyTimer"),
};

const appState = {
  diseases: [],
};

const busyState = {
  count: 0,
  startedAt: 0,
  intervalId: null,
  label: "",
  detail: "",
};

const actionButtons = Array.from(document.querySelectorAll("button"));

function log(message) {
  const stamp = new Date().toLocaleTimeString();
  ui.logOutput.textContent += `[${stamp}] ${message}\n`;
  ui.logOutput.scrollTop = ui.logOutput.scrollHeight;
}

function setStatus(message) {
  ui.statusText.textContent = message;
}

function setLastAction(label, durationSeconds, success) {
  if (!label) {
    ui.statusLastAction.textContent = "-";
    return;
  }
  const status = success ? "done" : "failed";
  ui.statusLastAction.textContent = `${label} · ${durationSeconds.toFixed(1)}s · ${status}`;
}

function setProjectStatus(dbPath, keysPath) {
  ui.statusDb.textContent = dbPath || "-";
  ui.statusKeys.textContent = keysPath || "-";
}

function setButtonsDisabled(disabled) {
  actionButtons.forEach(button => {
    button.disabled = disabled;
  });
}

function beginBusy(label, detail) {
  busyState.count += 1;
  busyState.label = label || "Working";
  busyState.detail = detail || "Processing request...";

  if (busyState.count > 1) {
    return;
  }

  busyState.startedAt = performance.now();
  if (busyState.intervalId) {
    window.clearInterval(busyState.intervalId);
  }

  setStatus(`${busyState.label} in progress...`);
  ui.busyTitle.textContent = busyState.label;
  ui.busyDetail.textContent = busyState.detail;
  ui.busyTimer.textContent = "0.0s";
  ui.busyOverlay.setAttribute("aria-hidden", "false");
  document.body.classList.add("is-busy");
  setButtonsDisabled(true);

  busyState.intervalId = window.setInterval(() => {
    const elapsed = (performance.now() - busyState.startedAt) / 1000;
    ui.busyTimer.textContent = `${elapsed.toFixed(1)}s`;
    if (elapsed > 3 && !ui.busyDetail.textContent.includes("Still working")) {
      ui.busyDetail.textContent = `${busyState.detail} Still working...`;
    }
  }, 120);
}

function endBusy(label, success) {
  if (busyState.count === 0) {
    return;
  }
  busyState.count -= 1;
  if (busyState.count > 0) {
    return;
  }

  const duration = (performance.now() - busyState.startedAt) / 1000;
  if (busyState.intervalId) {
    window.clearInterval(busyState.intervalId);
    busyState.intervalId = null;
  }

  document.body.classList.remove("is-busy");
  ui.busyOverlay.setAttribute("aria-hidden", "true");
  setButtonsDisabled(false);
  setLastAction(label || busyState.label, duration, success);
}

async function apiRequest(url, options) {
  const response = await fetch(url, options);
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const payload = await response.json();
      detail = payload.detail || JSON.stringify(payload);
    } catch (error) {
      // ignore parse errors
    }
    throw new Error(detail);
  }
  return response.json();
}

function apiGet(url) {
  return apiRequest(url, { method: "GET" });
}

function apiPost(url, payload) {
  return apiRequest(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload || {}),
  });
}

function clearTable(table) {
  table.innerHTML = "";
}

function renderMapping(mapping) {
  clearTable(ui.mappingTable);
  Object.entries(mapping || {}).forEach(([name, code]) => {
    const row = document.createElement("tr");
    row.innerHTML = `<td>${code}</td><td>${name}</td>`;
    ui.mappingTable.appendChild(row);
  });
}

function renderDiseases(diseases) {
  const currentSelection = ui.diseaseSelect.value;
  appState.diseases = diseases || [];
  ui.diseaseSelect.innerHTML = "";
  ui.diagnosesContainer.innerHTML = "";

  appState.diseases.forEach(name => {
    const option = document.createElement("option");
    option.value = name;
    option.textContent = name;
    ui.diseaseSelect.appendChild(option);

    const label = document.createElement("label");
    label.className = "chip";
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.dataset.disease = name;
    label.appendChild(checkbox);
    label.appendChild(document.createTextNode(name));
    ui.diagnosesContainer.appendChild(label);
  });

  if (appState.diseases.length === 0) {
    return;
  }
  if (appState.diseases.includes(currentSelection)) {
    ui.diseaseSelect.value = currentSelection;
  } else {
    ui.diseaseSelect.value = appState.diseases[0];
  }
}

function readDiagnoses() {
  const values = {};
  ui.diagnosesContainer.querySelectorAll("input[type='checkbox']").forEach(input => {
    values[input.dataset.disease] = input.checked ? 1 : 0;
  });
  return values;
}

function updateSummary(result) {
  ui.summaryRows.textContent = String(result.row_count ?? "-");
  ui.summaryEncrypted.textContent = String(result.encrypted_sum ?? "-");
  ui.summaryDecrypted.textContent = String(result.decrypted_sum ?? "-");
  ui.summaryPlain.textContent = String(result.plain_sum_reference ?? "-");
  ui.summaryValidation.textContent = result.is_valid ? "PASS" : "FAIL";
}

function renderFlow(flow) {
  clearTable(ui.flowTable);
  if (!flow || !flow.rows || flow.rows.length === 0) {
    ui.flowTable.innerHTML = "<tr><td>-</td><td>-</td><td>-</td></tr>";
    return;
  }
  flow.rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.pseudonym}</td><td>${row.plain_value}</td><td>${row.ciphertext}</td>`;
    ui.flowTable.appendChild(tr);
  });
}

function renderEncryptedRows(rows) {
  clearTable(ui.encryptedRowsTable);
  if (!rows || rows.length === 0) {
    ui.encryptedRowsTable.innerHTML = "<tr><td>-</td><td>-</td></tr>";
    return;
  }
  rows.forEach(row => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${row.pseudonym}</td><td>${row.ciphertext}</td>`;
    ui.encryptedRowsTable.appendChild(tr);
  });
}

function renderPipeline(disease, flow, summary) {
  if (!flow) {
    ui.pipelineText.textContent = "-";
    return;
  }
  const lines = [
    "Pipeline (client -> cloud -> client)",
    `1. Disease selected: ${disease}`,
    "2. Server reads encrypted flags for selected disease from SQLite.",
    "3. Server computes homomorphic aggregate ciphertext using multiplication mod n^2.",
    "4. Client decrypts aggregate result using private key.",
    "5. Client compares decrypted result with SQL plain SUM reference.",
    "",
    `Rows in flow: ${flow.rows.length}`,
    `Homomorphic ciphertext result: ${flow.encrypted_homomorphic_result}`,
    `Decrypted result: ${flow.decrypted_result}`,
    `Plain reference: ${flow.plain_reference}`,
  ];
  ui.pipelineText.textContent = lines.join("\n");
}

function renderValidationTable(report) {
  clearTable(ui.validationTable);
  const rows = report.results || [];
  if (rows.length === 0) {
    ui.validationTable.innerHTML = "<tr><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td><td>-</td></tr>";
    return;
  }
  rows.forEach(result => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${result.disease}</td><td>${result.homomorphic_sum}</td><td>${result.plain_sum}</td><td>${result.homomorphic_count}</td><td>${result.plain_count}</td><td>${result.is_valid ? "PASS" : "FAIL"}</td>`;
    ui.validationTable.appendChild(tr);
  });
}

function renderDbPreview(preview) {
  ui.dbPreviewHead.innerHTML = "";
  clearTable(ui.dbPreviewTable);

  ui.dbPreviewTotalPatients.textContent = String(preview.total_patients ?? "-");
  ui.dbPreviewTotalDiagnoses.textContent = String(preview.total_diagnoses ?? "-");
  ui.dbPreviewTotalDiseases.textContent = String(preview.diseases?.length ?? "-");

  const headerRow = document.createElement("tr");
  const headings = ["Pseudonym", ...(preview.diseases || [])];
  headings.forEach(title => {
    const th = document.createElement("th");
    th.textContent = title;
    headerRow.appendChild(th);
  });
  ui.dbPreviewHead.appendChild(headerRow);

  const rows = preview.rows || [];
  if (rows.length === 0) {
    const emptyRow = document.createElement("tr");
    emptyRow.innerHTML = `<td colspan="${headings.length}">-</td>`;
    ui.dbPreviewTable.appendChild(emptyRow);
    return;
  }

  rows.forEach(row => {
    const tr = document.createElement("tr");
    const values = [row.pseudonym, ...(preview.diseases || []).map(name => row.diagnoses?.[name] ?? 0)];
    values.forEach(value => {
      const td = document.createElement("td");
      td.textContent = String(value);
      tr.appendChild(td);
    });
    ui.dbPreviewTable.appendChild(tr);
  });
}

function revealSections() {
  const items = document.querySelectorAll("[data-reveal]");
  items.forEach((item, index) => {
    setTimeout(() => item.classList.add("is-visible"), 120 + index * 80);
  });
}

async function loadConfig() {
  const config = await apiGet("/api/config");
  ui.dbPath.value = config.db_path;
  ui.keysPath.value = config.keys_path;
  ui.keySize.value = config.key_size;
  ui.bulkPatients.value = 5000;
  ui.bulkSeed.value = 42;
  ui.bulkPrefix.value = "bulk_patient";
  ui.bulkBatchSize.value = 1000;
  renderDiseases(config.diseases);
  setLastAction("", 0, true);
}

async function setupProject() {
  setStatus("Setting up project...");
  const payload = {
    db_path: ui.dbPath.value,
    keys_path: ui.keysPath.value,
    key_size: Number(ui.keySize.value),
  };
  const response = await apiPost("/api/project/setup", payload);
  renderDiseases(response.diseases);
  renderMapping(response.mapping);
  setProjectStatus(response.db_path, response.keys_path);
  log(`Setup complete. Diseases: ${response.diseases.join(", ")}`);
  setStatus("Setup complete");
}

async function loadProject() {
  setStatus("Loading project...");
  const response = await apiPost("/api/project/load", {
    db_path: ui.dbPath.value,
    keys_path: ui.keysPath.value,
  });
  renderDiseases(response.diseases);
  renderMapping(response.mapping);
  setProjectStatus(response.db_path, response.keys_path);
  log(`Project loaded. Diseases: ${response.diseases.join(", ")}`);
  setStatus("Project loaded");
}

async function listDiseases() {
  setStatus("Listing diseases...");
  const response = await apiGet("/api/diseases");
  renderDiseases(response.diseases);
  renderMapping(response.mapping);
  log("Disease mapping refreshed");
  setStatus("Diseases refreshed");
}

async function addDisease() {
  const name = ui.newDiseaseName.value.trim();
  if (!name) {
    throw new Error("Provide a disease name");
  }
  setStatus("Adding new disease...");
  const response = await apiPost("/api/diseases/add", { name });
  renderDiseases(response.diseases);
  renderMapping(response.mapping);
  ui.newDiseaseName.value = "";
  log(`Added disease: ${name}`);
  setStatus("Disease added");
}

async function loadDbPreview() {
  const limitValue = Number(ui.dbPreviewLimit.value);
  const limit = Number.isFinite(limitValue) && limitValue > 0 ? limitValue : 50;
  setStatus("Loading database preview...");
  const response = await apiGet(`/api/db/preview?limit=${limit}`);
  renderDbPreview(response);
  log(`Database preview loaded (limit=${limit})`);
  setStatus("Database preview ready");
}

async function addPatient() {
  setStatus("Adding patient...");
  const payload = {
    pseudonym: ui.patientName.value,
    diagnoses: readDiagnoses(),
  };
  const response = await apiPost("/api/patients/add", payload);
  ui.patientName.value = "";
  log(`Added patient id=${response.patient_id}, pseudonym=${response.pseudonym}`);
  setStatus("Patient added");
}

async function seedDemo() {
  setStatus("Seeding demo data...");
  const response = await apiPost("/api/patients/seed-demo");
  log(`Inserted demo patients: ${response.inserted}`);
  setStatus("Seed demo complete");
}

async function seedBulk() {
  setStatus("Seeding bulk data...");
  const payload = {
    patients: Number(ui.bulkPatients.value),
    seed: Number(ui.bulkSeed.value),
    prefix: ui.bulkPrefix.value,
    batch_size: Number(ui.bulkBatchSize.value),
  };
  const response = await apiPost("/api/patients/seed-bulk", payload);
  log(`Inserted bulk patients: ${response.inserted} (total=${response.total_patients})`);
  setStatus("Seed bulk complete");
}

async function countDisease(includeFlow) {
  setStatus("Counting encrypted data...");
  const payload = {
    disease: ui.diseaseSelect.value,
    include_flow: includeFlow,
  };
  const response = await apiPost("/api/analytics/count", payload);
  updateSummary(response);
  if (response.flow) {
    renderFlow(response.flow);
    renderPipeline(response.disease, response.flow, response);
  }
  log(`Counted disease ${response.disease}, rows=${response.row_count}, valid=${response.is_valid}`);
  setStatus("Count complete");
}

async function showEncryptedRows() {
  setStatus("Loading encrypted rows...");
  const response = await apiPost("/api/analytics/encrypted-rows", {
    disease: ui.diseaseSelect.value,
  });
  renderEncryptedRows(response.rows);
  log(`Encrypted rows loaded for ${response.disease}, rows=${response.rows.length}`);
  setStatus("Encrypted rows ready");
}

async function validateSelected() {
  setStatus("Validating selected disease...");
  const response = await apiPost("/api/validation/selected", {
    disease: ui.diseaseSelect.value,
  });
  renderValidationTable({ results: [response] });
  log(`Validation for ${response.disease}: ${response.is_valid}`);
  setStatus("Validation complete");
}

async function validateAll() {
  setStatus("Validating all diseases...");
  const response = await apiPost("/api/validation/all");
  renderValidationTable(response);
  log(`Validation summary: ${response.passed_diseases}/${response.total_diseases}`);
  setStatus("Validation complete");
}

function attachEvents() {
  ui.setupBtn.addEventListener("click", () =>
    runAction("Setup new", setupProject, "Generating Paillier keys. This can take a few seconds.")
  );
  ui.loadBtn.addEventListener("click", () =>
    runAction("Load project", loadProject, "Loading keys and catalog from disk.")
  );
  ui.listDiseasesBtn.addEventListener("click", () =>
    runAction("List diseases", listDiseases, "Refreshing disease catalog.")
  );
  ui.addDiseaseBtn.addEventListener("click", () =>
    runAction(
      "Add disease",
      addDisease,
      "Adding new disease and backfilling existing patients with 0 values."
    )
  );
  ui.addPatientBtn.addEventListener("click", () =>
    runAction("Add patient", addPatient, "Encrypting diagnoses and writing to database.")
  );
  ui.seedDemoBtn.addEventListener("click", () =>
    runAction("Seed demo", seedDemo, "Adding demo patients.")
  );
  ui.seedBulkBtn.addEventListener("click", () =>
    runAction("Seed bulk", seedBulk, "Inserting many encrypted records. This can take a while.")
  );
  ui.countBtn.addEventListener("click", () =>
    runAction("Count encrypted", () => countDisease(false), "Computing encrypted count and sum.")
  );
  ui.countFlowBtn.addEventListener("click", () =>
    runAction("Count + flow", () => countDisease(true), "Computing encrypted count and loading flow rows.")
  );
  ui.encryptedRowsBtn.addEventListener("click", () =>
    runAction("Show encrypted rows", showEncryptedRows, "Loading ciphertext rows from database.")
  );
  ui.validateSelectedBtn.addEventListener("click", () =>
    runAction("Validate selected", validateSelected, "Validating encrypted vs plain result.")
  );
  ui.validateAllBtn.addEventListener("click", () =>
    runAction("Validate all", validateAll, "Validating all diseases. This can take a while.")
  );
  ui.dbPreviewBtn.addEventListener("click", () =>
    runAction("Database preview", loadDbPreview, "Loading patient rows from the database.")
  );
  ui.clearLogBtn.addEventListener("click", () => (ui.logOutput.textContent = ""));
}

async function runAction(label, action, detail) {
  beginBusy(label, detail);
  let success = false;
  try {
    await action();
    success = true;
  } catch (error) {
    log(`ERROR: ${error.message}`);
    setStatus(`Error: ${error.message}`);
  } finally {
    endBusy(label, success);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await loadConfig();
    attachEvents();
    revealSections();
    log("Web console ready");
  } catch (error) {
    log(`Failed to load config: ${error.message}`);
  }
});
