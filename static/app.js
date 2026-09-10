/**
 * Voter List Search Web Application Frontend Logic
 */

document.addEventListener("DOMContentLoaded", () => {
  // DOM Elements
  const searchForm = document.getElementById("searchForm");
  const voterNameInput = document.getElementById("voterNameInput");
  const relationNameInput = document.getElementById("relationNameInput");
  const partSelect = document.getElementById("partSelect");
  const btnClearName = document.getElementById("btnClearName");
  const btnClearRel = document.getElementById("btnClearRel");
  const btnReset = document.getElementById("btnReset");
  const btnSearch = document.getElementById("btnSearch");
  
  const statsBadge = document.getElementById("statsBadge");
  const statsText = document.getElementById("statsText");
  const statusBanner = document.getElementById("statusBanner");
  const bannerTitle = document.getElementById("bannerTitle");
  const bannerDesc = document.getElementById("bannerDesc");
  const bannerIcon = document.getElementById("bannerIcon");
  
  const loadingIndicator = document.getElementById("loadingIndicator");
  const resultsSection = document.getElementById("resultsSection");
  const initialPlaceholder = document.getElementById("initialPlaceholder");
  const resultsCountHeading = document.getElementById("resultsCountHeading");
  const resultsTimingBadge = document.getElementById("resultsTimingBadge");
  const resultsTableBody = document.getElementById("resultsTableBody");
  const btnExportCsv = document.getElementById("btnExportCsv");

  // Modal Elements
  const btnOpenUpload = document.getElementById("btnOpenUpload");
  const uploadModal = document.getElementById("uploadModal");
  const btnCloseModal = document.getElementById("btnCloseModal");
  const btnCancelUpload = document.getElementById("btnCancelUpload");
  const dropZone = document.getElementById("dropZone");
  const pdfFileInput = document.getElementById("pdfFileInput");
  const selectedFileInfo = document.getElementById("selectedFileInfo");
  const selectedFileName = document.getElementById("selectedFileName");
  const selectedFileSize = document.getElementById("selectedFileSize");
  const btnRemoveFile = document.getElementById("btnRemoveFile");
  const btnStartUpload = document.getElementById("btnStartUpload");
  const uploadProgress = document.getElementById("uploadProgress");
  const progressBar = document.getElementById("progressBar");
  const uploadStatusText = document.getElementById("uploadStatusText");
  const uploadResultAlert = document.getElementById("uploadResultAlert");

  let currentSearchResults = [];
  let selectedFile = null;

  // Initialize
  fetchStats();

  // Input Clear Buttons visibility
  voterNameInput.addEventListener("input", () => {
    btnClearName.style.display = voterNameInput.value ? "block" : "none";
  });
  relationNameInput.addEventListener("input", () => {
    btnClearRel.style.display = relationNameInput.value ? "block" : "none";
  });

  btnClearName.addEventListener("click", () => {
    voterNameInput.value = "";
    btnClearName.style.display = "none";
    voterNameInput.focus();
  });

  btnClearRel.addEventListener("click", () => {
    relationNameInput.value = "";
    btnClearRel.style.display = "none";
    relationNameInput.focus();
  });

  btnReset.addEventListener("click", () => {
    voterNameInput.value = "";
    relationNameInput.value = "";
    partSelect.value = "all";
    btnClearName.style.display = "none";
    btnClearRel.style.display = "none";
    resultsSection.style.display = "none";
    statusBanner.style.display = "none";
    initialPlaceholder.style.display = "block";
    currentSearchResults = [];
    voterNameInput.focus();
  });

  // Quick Chips
  document.querySelectorAll(".chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      voterNameInput.value = chip.dataset.name || "";
      relationNameInput.value = chip.dataset.rel || "";
      btnClearName.style.display = voterNameInput.value ? "block" : "none";
      btnClearRel.style.display = relationNameInput.value ? "block" : "none";
      executeSearch();
    });
  });

  // Search Submission
  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    executeSearch();
  });

  async function executeSearch() {
    const name = voterNameInput.value.trim();
    const relation = relationNameInput.value.trim();
    const part = partSelect.value;

    if (!name) {
      voterNameInput.focus();
      return;
    }

    // UI Loading state
    loadingIndicator.style.display = "flex";
    resultsSection.style.display = "none";
    initialPlaceholder.style.display = "none";
    statusBanner.style.display = "none";
    btnSearch.disabled = true;

    const params = new URLSearchParams({ name });
    if (relation) params.append("relation", relation);
    if (part && part !== "all") params.append("bhag", part);

    try {
      const resp = await fetch(`/api/search?${params.toString()}`);
      if (!resp.ok) {
        throw new Error(`Search error: ${resp.statusText}`);
      }
      const data = await resp.json();
      renderSearchResults(data);
    } catch (err) {
      console.error(err);
      showBanner("error", "Search Failed", "Could not connect to the search server. Please try again.");
      initialPlaceholder.style.display = "block";
    } finally {
      loadingIndicator.style.display = "none";
      btnSearch.disabled = false;
    }
  }

  function renderSearchResults(data) {
    currentSearchResults = data.results || [];
    resultsTableBody.innerHTML = "";

    // Check Fallback state
    if (data.is_fallback) {
      showBanner(
        "fallback",
        "No exact match found",
        "Showing the top closest matching voter names instead."
      );
    } else {
      statusBanner.style.display = "none";
    }

    if (currentSearchResults.length === 0) {
      showBanner("info", "No Results", "No matching voters found. Try searching with a different spelling or relation name.");
      initialPlaceholder.style.display = "block";
      resultsSection.style.display = "none";
      return;
    }

    // Header info
    resultsCountHeading.textContent = `Found ${currentSearchResults.length} Voter${currentSearchResults.length > 1 ? "s" : ""}`;
    resultsTimingBadge.textContent = `⚡ ${data.elapsed_ms} ms`;

    // Render Table Rows
    currentSearchResults.forEach((v) => {
      const tr = document.createElement("tr");

      // Score class
      const score = v.match_score || 100;
      let scoreClass = "match-high";
      if (score < 75) scoreClass = "match-low";
      else if (score < 90) scoreClass = "match-med";

      // Age & Gender
      const genderText = v.gender ? v.gender : "-";
      const ageText = v.age ? `${v.age} yrs` : "-";

      tr.innerHTML = `
        <td class="col-kram">
          <span class="kram-badge" title="Kram Sankhya (Serial Number)">${v.kram_sankhya}</span>
        </td>
        <td class="col-bhag">
          <span class="bhag-badge" title="Bhag Sankhya (Part Number)">Part ${v.bhag_sankhya}</span>
        </td>
        <td class="col-name">
          <div class="name-cell">
            <span class="name-hindi">${escapeHtml(v.name_hindi || "-")}</span>
            <span class="name-english">${escapeHtml(v.name_english || "-")}</span>
            ${v.is_deleted ? '<span class="tag-deleted">Shifted / Deleted</span>' : ""}
          </div>
        </td>
        <td class="col-relation">
          <div class="rel-cell">
            <span class="rel-type-tag">${escapeHtml(v.relation_type || "Father")}</span>
            <span class="rel-hindi">${escapeHtml(v.relation_name_hindi || "-")}</span>
            <span class="rel-english">${escapeHtml(v.relation_name_english || "-")}</span>
          </div>
        </td>
        <td class="col-age">
          <span style="font-weight:600; color:#fff;">${ageText}</span>
          <span style="color:var(--text-dim); font-size:0.75rem; display:block;">${genderText}</span>
        </td>
        <td class="col-house">
          <span style="font-weight:500;">${escapeHtml(v.house_number || "-")}</span>
        </td>
        <td class="col-epic">
          <span class="epic-code">${escapeHtml(v.epic || "-")}</span>
        </td>
        <td class="col-match">
          <span class="match-pill ${scoreClass}">
            ${v.match_label ? v.match_label : `${score}%`}
          </span>
        </td>
      `;
      resultsTableBody.appendChild(tr);
    });

    resultsSection.style.display = "flex";
    initialPlaceholder.style.display = "none";
  }

  function showBanner(type, title, desc) {
    statusBanner.className = `status-banner ${type}`;
    bannerTitle.textContent = title;
    bannerDesc.textContent = desc;
    statusBanner.style.display = "flex";
  }

  // Export CSV
  btnExportCsv.addEventListener("click", () => {
    if (!currentSearchResults.length) return;
    const headers = ["Kram Sankhya", "Bhag Sankhya", "Voter Name Hindi", "Voter Name English", "Relation Type", "Relation Name Hindi", "Relation Name English", "Age", "Gender", "House Number", "EPIC", "Match Score"];
    const rows = currentSearchResults.map((v) => [
      v.kram_sankhya,
      v.bhag_sankhya,
      `"${(v.name_hindi || "").replace(/"/g, '""')}"`,
      `"${(v.name_english || "").replace(/"/g, '""')}"`,
      v.relation_type || "Father",
      `"${(v.relation_name_hindi || "").replace(/"/g, '""')}"`,
      `"${(v.relation_name_english || "").replace(/"/g, '""')}"`,
      v.age || "",
      v.gender || "",
      `"${(v.house_number || "").replace(/"/g, '""')}"`,
      v.epic || "",
      v.match_score || "",
    ]);

    const csvContent = "data:text/csv;charset=utf-8," + [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `voter_search_results_${Date.now()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  });

  // Fetch Database Stats
  async function fetchStats() {
    try {
      const resp = await fetch("/api/stats");
      if (resp.ok) {
        const stats = await resp.json();
        statsText.textContent = `${stats.total_voters.toLocaleString()} Voters • ${stats.parts.length} Part Lists`;
        
        // Populate parts dropdown
        const currentVal = partSelect.value;
        partSelect.innerHTML = '<option value="all">All Parts (सभी भाग)</option>';
        stats.parts.forEach((p) => {
          const opt = document.createElement("option");
          opt.value = p;
          opt.textContent = `Bhag ${p} (भाग संख्या ${p})`;
          partSelect.appendChild(opt);
        });
        partSelect.value = currentVal || "all";
      }
    } catch (e) {
      statsText.textContent = "Offline";
    }
  }

  // Upload Modal Handlers
  btnOpenUpload.addEventListener("click", () => {
    resetUploadModal();
    uploadModal.style.display = "flex";
  });

  btnCloseModal.addEventListener("click", () => {
    uploadModal.style.display = "none";
  });

  btnCancelUpload.addEventListener("click", () => {
    uploadModal.style.display = "none";
  });

  uploadModal.addEventListener("click", (e) => {
    if (e.target === uploadModal) {
      uploadModal.style.display = "none";
    }
  });

  // Drag and Drop
  dropZone.addEventListener("click", () => pdfFileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover");
    if (e.dataTransfer.files.length) {
      handleFileSelected(e.dataTransfer.files[0]);
    }
  });

  pdfFileInput.addEventListener("change", () => {
    if (pdfFileInput.files.length) {
      handleFileSelected(pdfFileInput.files[0]);
    }
  });

  function handleFileSelected(file) {
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      showUploadAlert("error", "Please select a valid PDF file.");
      return;
    }
    selectedFile = file;
    selectedFileName.textContent = file.name;
    selectedFileSize.textContent = formatBytes(file.size);
    selectedFileInfo.style.display = "flex";
    dropZone.style.display = "none";
    btnStartUpload.disabled = false;
    uploadResultAlert.style.display = "none";
  }

  btnRemoveFile.addEventListener("click", () => {
    selectedFile = null;
    pdfFileInput.value = "";
    selectedFileInfo.style.display = "none";
    dropZone.style.display = "block";
    btnStartUpload.disabled = true;
  });

  function resetUploadModal() {
    selectedFile = null;
    pdfFileInput.value = "";
    selectedFileInfo.style.display = "none";
    dropZone.style.display = "block";
    btnStartUpload.disabled = true;
    uploadProgress.style.display = "none";
    uploadResultAlert.style.display = "none";
    progressBar.style.width = "0%";
  }

  function showUploadAlert(type, message) {
    uploadResultAlert.className = `alert-box ${type}`;
    uploadResultAlert.textContent = message;
    uploadResultAlert.style.display = "block";
  }

  // Start Upload
  btnStartUpload.addEventListener("click", async () => {
    if (!selectedFile) return;

    btnStartUpload.disabled = true;
    btnCancelUpload.disabled = true;
    uploadProgress.style.display = "flex";
    progressBar.style.width = "40%";
    uploadStatusText.textContent = "Uploading & extracting voter records...";

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const resp = await fetch("/api/upload", {
        method: "POST",
        body: formData,
      });

      progressBar.style.width = "90%";

      if (!resp.ok) {
        const errData = await resp.json().catch(() => ({}));
        throw new Error(errData.detail || "Upload failed");
      }

      const res = await resp.json();
      progressBar.style.width = "100%";
      uploadStatusText.textContent = "Done!";

      showUploadAlert("success", `Success! Ingested ${res.total_voters} voters into Bhag (Part) ${res.bhag_sankhya} in ${res.elapsed_seconds}s.`);

      // Refresh stats
      fetchStats();

      // Close modal after delay
      setTimeout(() => {
        uploadModal.style.display = "none";
        resetUploadModal();
        btnStartUpload.disabled = false;
        btnCancelUpload.disabled = false;
      }, 1800);
    } catch (err) {
      console.error(err);
      progressBar.style.width = "0%";
      uploadProgress.style.display = "none";
      showUploadAlert("error", `Error: ${err.message}`);
      btnStartUpload.disabled = false;
      btnCancelUpload.disabled = false;
    }
  });

  function formatBytes(bytes) {
    if (bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  }

  function escapeHtml(str) {
    if (!str) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
});
