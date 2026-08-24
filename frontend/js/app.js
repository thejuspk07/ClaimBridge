/**
 * ClaimBridge v2 — Pure JavaScript Frontend Client
 * Connects directly to the FastAPI Medical Claim Processing Engine.
 * Includes: dedup-aware UX, sortable table, micro-interactions,
 * skeleton loaders, confidence count-up, toast slide-in, recent uploads.
 */

// ============================================================================
// Application State
// ============================================================================

let appState = {
  mode: 'live', // 'live' | 'demo'
  selectedFiles: [],
  claims: [],
  currentClaim: null,
  currentFilter: 'all',
  searchQuery: '',
  zoomLevel: 1.0,
  pendingCorrections: {},
  recentUploads: [],   // {filename, status, claimId}
  sortColumn: null,
  sortDirection: 'desc',
  previousClaimIds: new Set(),
};

// ============================================================================
// DOM References
// ============================================================================

const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const fileQueueContainer = document.getElementById('file-queue-container');
const fileQueueList = document.getElementById('file-queue-list');
const selectedFileCount = document.getElementById('selected-file-count');
const processBtn = document.getElementById('process-btn');
const progressCard = document.getElementById('progress-card');
const claimsTbody = document.getElementById('claims-tbody');

// ============================================================================
// Initialization
// ============================================================================

document.addEventListener('DOMContentLoaded', () => {
  setupEventListeners();
  checkHealth();
  fetchClaims();
});

function setupEventListeners() {
  // Drag & Drop with animated feedback
  dropzone.addEventListener('click', () => fileInput.click());
  
  dropzone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone.addEventListener('dragleave', () => {
    dropzone.classList.remove('dragover');
  });

  dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFilesSelected(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
      handleFilesSelected(e.target.files);
    }
  });
}

// ============================================================================
// Health Check
// ============================================================================

async function checkHealth() {
  try {
    const res = await fetch('/api/health');
    if (res.ok) {
      const data = await res.json();
      document.getElementById('engine-status-text').textContent = `${data.engine} Active`;
    }
  } catch (err) {
    document.getElementById('engine-status-text').textContent = 'Backend Offline';
    showToast('Backend offline. Please start FastAPI server.', 'error');
  }
}

// ============================================================================
// File Selection
// ============================================================================

function handleFilesSelected(files) {
  for (let i = 0; i < files.length; i++) {
    const file = files[i];
    if (!appState.selectedFiles.some(f => f.name === file.name)) {
      appState.selectedFiles.push(file);
    }
  }
  updateFileQueueUI();
}

function updateFileQueueUI() {
  if (appState.selectedFiles.length === 0) {
    fileQueueContainer.style.display = 'none';
    processBtn.disabled = true;
    selectedFileCount.textContent = '0';
    fileQueueList.innerHTML = '';
    return;
  }

  fileQueueContainer.style.display = 'block';
  processBtn.disabled = false;
  selectedFileCount.textContent = appState.selectedFiles.length;
  
  fileQueueList.innerHTML = appState.selectedFiles.map((file, idx) => `
    <div class="file-queue-item">
      <span class="file-queue-name" title="${file.name}">📄 ${file.name}</span>
      <span style="color: var(--text-muted); font-size: 0.75rem;">${(file.size / 1024).toFixed(0)} KB</span>
      <button class="remove-file-btn" onclick="removeSelectedFile(${idx})">&times;</button>
    </div>
  `).join('');
}

function removeSelectedFile(index) {
  appState.selectedFiles.splice(index, 1);
  updateFileQueueUI();
}

function clearSelectedFiles() {
  appState.selectedFiles = [];
  fileInput.value = '';
  updateFileQueueUI();
}

// ============================================================================
// Processing Pipeline (Live OCR & Extraction)
// ============================================================================

async function startProcessing() {
  if (appState.selectedFiles.length === 0) return;

  processBtn.disabled = true;
  progressCard.style.display = 'flex';
  resetProgressStages();
  
  const filesToProcess = [...appState.selectedFiles];
  const total = filesToProcess.length;

  for (let i = 0; i < total; i++) {
    const file = filesToProcess[i];
    updateProgressUI(i, total, file.name);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      // Stage progression with animation
      setProgressStage('upload');
      await sleep(150);

      setProgressStage('render');
      await sleep(150);

      setProgressStage('ocr');
      const response = await fetch('/api/claims/process', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `Server error: ${response.status}`);
      }

      setProgressStage('extract');
      await sleep(100);

      setProgressStage('validate');
      const processedClaim = await response.json();
      await sleep(100);

      // Mark all stages completed
      completeAllStages();

      addRecentUpload(file.name, 'success', processedClaim.claim_id);
      showToast(`Processed: ${file.name} (Conf: ${processedClaim.confidence_score}%)`, 'success');

    } catch (err) {
      console.error('Error processing claim:', err);
      addRecentUpload(file.name, 'error', null);
      showToast(`Failed ${file.name}: ${err.message}`, 'error');
    }
  }

  // Finished batch
  progressCard.style.display = 'none';
  clearSelectedFiles();
  processBtn.disabled = false;
  await fetchClaims();
}

function updateProgressUI(currentIndex, totalCount, filename) {
  const pct = Math.round(((currentIndex) / totalCount) * 100);
  document.getElementById('progress-pct-label').textContent = `${pct}%`;
  document.getElementById('progress-status-label').textContent = `Processing ${filename} (${currentIndex + 1}/${totalCount})`;
  document.getElementById('progress-bar-fill').style.width = `${pct}%`;
}

function resetProgressStages() {
  const stages = ['upload', 'render', 'ocr', 'extract', 'validate'];
  stages.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    if (el) {
      el.classList.remove('active', 'completed');
    }
  });
}

function setProgressStage(stageId) {
  const stages = ['upload', 'render', 'ocr', 'extract', 'validate'];
  const targetIdx = stages.indexOf(stageId);
  
  stages.forEach((s, idx) => {
    const el = document.getElementById(`stage-${s}`);
    if (!el) return;
    
    if (idx < targetIdx) {
      el.classList.remove('active');
      el.classList.add('completed');
    } else if (idx === targetIdx) {
      el.classList.add('active');
      el.classList.remove('completed');
    } else {
      el.classList.remove('active', 'completed');
    }
  });
}

function completeAllStages() {
  const stages = ['upload', 'render', 'ocr', 'extract', 'validate'];
  stages.forEach(s => {
    const el = document.getElementById(`stage-${s}`);
    if (el) {
      el.classList.remove('active');
      el.classList.add('completed');
    }
  });
}

// ============================================================================
// Recent Uploads
// ============================================================================

function addRecentUpload(filename, status, claimId) {
  appState.recentUploads.unshift({ filename, status, claimId });
  if (appState.recentUploads.length > 5) {
    appState.recentUploads = appState.recentUploads.slice(0, 5);
  }
  renderRecentUploads();
}

function renderRecentUploads() {
  const panel = document.getElementById('recent-uploads-panel');
  const list = document.getElementById('recent-uploads-list');
  
  if (appState.recentUploads.length === 0) {
    panel.style.display = 'none';
    return;
  }

  panel.style.display = 'flex';
  list.innerHTML = appState.recentUploads.map(item => {
    const icon = item.status === 'success' ? '✓' : item.status === 'error' ? '✕' : '⚠';
    const iconColor = item.status === 'success' ? 'var(--success)' : item.status === 'error' ? 'var(--danger)' : 'var(--warning)';
    const onclick = item.claimId ? `onclick="openClaimDetail('${item.claimId}')"` : '';
    
    return `
      <div class="recent-upload-item" ${onclick}>
        <span class="recent-upload-icon" style="color: ${iconColor};">${icon}</span>
        <span class="recent-upload-name">${item.filename}</span>
        <span class="recent-upload-status" style="color: ${iconColor};">${item.status === 'success' ? 'Done' : 'Failed'}</span>
      </div>
    `;
  }).join('');
}

// ============================================================================
// Fetch Claims List
// ============================================================================

async function fetchClaims() {
  // Show skeleton loaders while fetching
  showSkeletonRows();

  try {
    const params = new URLSearchParams();
    if (appState.currentFilter !== 'all') {
      params.append('status', appState.currentFilter);
    }
    if (appState.searchQuery) {
      params.append('search', appState.searchQuery);
    }

    const res = await fetch(`/api/claims?${params.toString()}`);
    if (res.ok) {
      appState.claims = await res.json();
      sortAndRenderClaims();
      updateMetrics();
    }
  } catch (err) {
    console.error('Error fetching claims:', err);
    claimsTbody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3rem;">
          Unable to fetch claims. Check backend connection.
        </td>
      </tr>
    `;
  }
}

function showSkeletonRows() {
  const skeletonCount = 4;
  const skeletons = [];
  for (let i = 0; i < skeletonCount; i++) {
    skeletons.push(`
      <tr class="skeleton-row">
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar medium"></div></td>
        <td><div class="skeleton-bar medium"></div></td>
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar short"></div></td>
        <td><div class="skeleton-bar short"></div></td>
      </tr>
    `);
  }
  claimsTbody.innerHTML = skeletons.join('');
}

// ============================================================================
// Sorting
// ============================================================================

function getStatusPriority(status) {
  // Successful first, review middle, failed last
  const priorities = {
    'approved': 0,
    'auto_approved': 0,
    'processed': 1,
    'needs_review': 2,
    'review': 2,
    'rejected': 3,
    'flagged': 3,
    'failed': 4,
  };
  return priorities[status?.toLowerCase()] ?? 3;
}

function sortAndRenderClaims() {
  let sorted = [...appState.claims];

  // Apply column sort if active
  if (appState.sortColumn) {
    sorted.sort((a, b) => {
      let valA = a[appState.sortColumn];
      let valB = b[appState.sortColumn];
      if (valA == null) valA = -Infinity;
      if (valB == null) valB = -Infinity;
      const cmp = valA > valB ? 1 : valA < valB ? -1 : 0;
      return appState.sortDirection === 'asc' ? cmp : -cmp;
    });
  } else {
    // Default sort: successful first, failed/0% last, then by uploaded_at desc within group
    sorted.sort((a, b) => {
      const pa = getStatusPriority(a.status);
      const pb = getStatusPriority(b.status);
      if (pa !== pb) return pa - pb;
      // Within same priority, newest first
      return (b.uploaded_at || '').localeCompare(a.uploaded_at || '');
    });
  }

  // Update sort header indicators
  document.querySelectorAll('.claims-table th.sortable').forEach(th => {
    const col = th.dataset.sort;
    th.classList.toggle('sort-active', col === appState.sortColumn);
    const indicator = th.querySelector('.sort-indicator');
    if (indicator) {
      if (col === appState.sortColumn) {
        indicator.textContent = appState.sortDirection === 'asc' ? '↑' : '↓';
      } else {
        indicator.textContent = '↕';
      }
    }
  });

  renderClaimsTable(sorted);
}

function toggleSort(column) {
  if (appState.sortColumn === column) {
    if (appState.sortDirection === 'desc') {
      appState.sortDirection = 'asc';
    } else {
      // Third click: reset to default sort
      appState.sortColumn = null;
      appState.sortDirection = 'desc';
      sortAndRenderClaims();
      return;
    }
  } else {
    appState.sortColumn = column;
    appState.sortDirection = 'desc';
  }
  sortAndRenderClaims();
}

// ============================================================================
// Render Claims Table
// ============================================================================

function renderClaimsTable(sortedClaims) {
  const claims = sortedClaims || appState.claims;

  // Update row count
  const totalCount = appState.claims.length;
  const displayCount = claims.length;
  const rowCountEl = document.getElementById('table-row-count');
  if (rowCountEl) {
    rowCountEl.textContent = totalCount > 0
      ? `Showing ${displayCount} of ${totalCount} claim${totalCount !== 1 ? 's' : ''}`
      : '';
  }

  if (claims.length === 0) {
    claimsTbody.innerHTML = `
      <tr>
        <td colspan="9" style="text-align: center; color: var(--text-muted); padding: 3rem;">
          No claims found matching the current filter.
        </td>
      </tr>
    `;
    return;
  }

  // Track which claim IDs are new for animation
  const currentIds = new Set(claims.map(c => c.claim_id));
  const newIds = new Set();
  currentIds.forEach(id => {
    if (!appState.previousClaimIds.has(id)) newIds.add(id);
  });

  claimsTbody.innerHTML = claims.map(claim => {
    const confClass = claim.confidence_score >= 95 ? 'conf-high' : claim.confidence_score >= 85 ? 'conf-med' : 'conf-low';
    const statusBadgeClass = `badge-${claim.status.toLowerCase()}`;
    const statusLabel = claim.status.replace('_', ' ');
    const isNew = newIds.has(claim.claim_id);

    // Patient column: show extraction-failed tag for blank/low-confidence
    let patientCell;
    if (!claim.patient_name && claim.confidence_score < 10) {
      patientCell = '<span class="extraction-failed-tag">⚠ Extraction Failed</span>';
    } else {
      patientCell = claim.patient_name || '<span style="color: var(--text-muted);">&mdash;</span>';
    }

    return `
      <tr class="${isNew ? 'claim-row-enter' : ''}" onclick="openClaimDetail('${claim.claim_id}')">
        <td><span class="claim-id-badge">${claim.claim_id}</span></td>
        <td style="font-weight: 500;">${claim.filename}</td>
        <td>${patientCell}</td>
        <td style="font-family: var(--font-mono);">${claim.insured_id || '<span style="color: var(--text-muted);">&mdash;</span>'}</td>
        <td style="font-weight: 600;">${claim.total_charge !== null && claim.total_charge !== undefined ? `$${claim.total_charge.toFixed(2)}` : '&mdash;'}</td>
        <td>
          <span class="confidence-chip ${confClass}" data-conf="${claim.confidence_score.toFixed(1)}">0.0%</span>
        </td>
        <td><span class="badge ${statusBadgeClass}">${statusLabel}</span></td>
        <td>
          ${claim.error_count > 0 ? `<span style="color: var(--danger); font-weight: 600; font-size: 0.75rem;">${claim.error_count} ERR</span> ` : ''}
          ${claim.warning_count > 0 ? `<span style="color: var(--warning); font-weight: 600; font-size: 0.75rem;">${claim.warning_count} WARN</span>` : ''}
          ${claim.error_count === 0 && claim.warning_count === 0 ? `<span style="color: var(--success); font-size: 0.75rem;">✓ Valid</span>` : ''}
        </td>
        <td>
          <button class="btn-secondary" style="padding: 0.25rem 0.6rem; font-size: 0.75rem;" onclick="event.stopPropagation(); openClaimDetail('${claim.claim_id}')">Inspect</button>
        </td>
      </tr>
    `;
  }).join('');

  // Update previous IDs for next render
  appState.previousClaimIds = currentIds;

  // Animate confidence count-up
  requestAnimationFrame(() => {
    animateConfidenceChips();
  });
}

// ============================================================================
// Confidence Count-Up Animation
// ============================================================================

function animateConfidenceChips() {
  const chips = document.querySelectorAll('.confidence-chip[data-conf]');
  chips.forEach(chip => {
    const targetVal = parseFloat(chip.dataset.conf);
    if (isNaN(targetVal)) return;
    
    const duration = 500;
    const startTime = performance.now();
    
    function tick(now) {
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      // Ease-out
      const eased = 1 - Math.pow(1 - progress, 3);
      const current = (eased * targetVal).toFixed(1);
      chip.textContent = `${current}%`;
      
      if (progress < 1) {
        requestAnimationFrame(tick);
      }
    }
    
    requestAnimationFrame(tick);
  });
}

// ============================================================================
// Update KPI Cards
// ============================================================================

function updateMetrics() {
  const total = appState.claims.length;
  const autoApproved = appState.claims.filter(c => c.status === 'approved' || c.status === 'auto_approved' || (c.error_count === 0 && c.warning_count === 0)).length;
  const needsReview = appState.claims.filter(c => c.status === 'needs_review' || c.warning_count > 0 || c.error_count > 0).length;
  
  const avgConf = total > 0
    ? (appState.claims.reduce((acc, c) => acc + c.confidence_score, 0) / total).toFixed(1)
    : '0.0';

  document.getElementById('kpi-total-claims').textContent = total;
  document.getElementById('kpi-auto-approved').textContent = autoApproved;
  document.getElementById('kpi-needs-review').textContent = needsReview;
  document.getElementById('kpi-avg-confidence').textContent = `${avgConf}%`;
}

// ============================================================================
// Search and Filter
// ============================================================================

function filterClaims(status) {
  appState.currentFilter = status;
  document.querySelectorAll('.filter-tab').forEach(tab => {
    tab.classList.toggle('active', tab.dataset.filter === status);
  });
  fetchClaims();
}

function handleSearch(query) {
  appState.searchQuery = query;
  fetchClaims();
}

// ============================================================================
// Open Claim Detail Workspace
// ============================================================================

async function openClaimDetail(claimId) {
  try {
    const res = await fetch(`/api/claims/${claimId}`);
    if (!res.ok) throw new Error('Could not load claim details.');
    
    const claim = await res.json();
    appState.currentClaim = claim;
    appState.pendingCorrections = {};

    // Switch Views
    document.getElementById('queue-view').style.display = 'none';
    const detailView = document.getElementById('detail-view');
    detailView.classList.add('active');

    // Populate UI
    document.getElementById('detail-claim-id-badge').textContent = claim.claim_id;
    document.getElementById('detail-claim-image').src = claim.image_url;
    resetZoom();

    // Patient Fields
    document.getElementById('field-patient-name').value = claim.patient.name || '';
    document.getElementById('field-patient-dob').value = claim.patient.dob || '';
    document.getElementById('field-patient-street').value = claim.patient.address?.street || '';
    document.getElementById('field-patient-city-state-zip').value = [
      claim.patient.address?.city,
      claim.patient.address?.state,
      claim.patient.address?.zip
    ].filter(Boolean).join(', ');
    document.getElementById('field-patient-phone').value = claim.patient.address?.phone || '';

    // Insurance Fields
    document.getElementById('field-insured-id').value = claim.insurance.insured_id || '';
    document.getElementById('field-insured-name').value = claim.insurance.insured_name || '';
    document.getElementById('field-policy-group').value = claim.insurance.policy_group || '';
    document.getElementById('field-plan-name').value = claim.insurance.plan_name || '';

    // Diagnoses & Context
    document.getElementById('field-diagnosis-codes').value = (claim.diagnosis_codes || []).join(', ');
    document.getElementById('field-illness-date').value = claim.additional_claim_info || '';

    // Service Lines
    renderServiceLines(claim.service_lines || []);

    // Billing & Provider
    document.getElementById('field-tax-id').value = claim.federal_tax_id || '';
    document.getElementById('field-account-no').value = claim.patient_account_number || '';
    document.getElementById('field-total-charge').value = claim.total_charge !== null ? claim.total_charge.toFixed(2) : '';
    document.getElementById('field-billing-provider').value = claim.providers?.billing_provider || '';
    document.getElementById('field-billing-npi').value = claim.providers?.billing_npi || '';

    // Right Review Panel — confidence gauge count-up
    const gaugeEl = document.getElementById('detail-confidence-score');
    animateCountUp(gaugeEl, 0, claim.confidence_score, 600);

    const statusClass = `badge-${(claim.review_status || claim.status).toLowerCase()}`;
    document.getElementById('detail-status-badge').innerHTML = `
      <span class="badge ${statusClass}">${(claim.review_status || claim.status).replace('_', ' ')}</span>
    `;

    // Field Confidence List
    renderFieldConfidences(claim.field_confidences || {});

    // Validation Messages
    renderValidationMessages(claim.validation?.messages || []);

  } catch (err) {
    showToast(`Error opening claim: ${err.message}`, 'error');
  }
}

function closeDetailView() {
  document.getElementById('detail-view').classList.remove('active');
  document.getElementById('queue-view').style.display = 'grid';
  appState.currentClaim = null;
  fetchClaims();
}

// ============================================================================
// Animated Count-Up Helper
// ============================================================================

function animateCountUp(el, from, to, durationMs) {
  const startTime = performance.now();
  function tick(now) {
    const elapsed = now - startTime;
    const progress = Math.min(elapsed / durationMs, 1);
    const eased = 1 - Math.pow(1 - progress, 3);
    const current = from + (to - from) * eased;
    el.textContent = `${current.toFixed(1)}%`;
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ============================================================================
// Render Sub-Components
// ============================================================================

function renderServiceLines(lines) {
  const tbody = document.getElementById('services-tbody');
  tbody.innerHTML = lines.map((line, idx) => `
    <tr>
      <td style="font-weight: 700; text-align: center;">${line.line_number}</td>
      <td><input type="text" value="${line.date_of_service || ''}" onchange="markServiceLineEdited(${idx}, 'date_of_service', this.value)"></td>
      <td><input type="text" value="${line.place_of_service || ''}" style="width: 40px;" onchange="markServiceLineEdited(${idx}, 'place_of_service', this.value)"></td>
      <td><input type="text" value="${line.procedure_code || ''}" style="font-family: var(--font-mono);" onchange="markServiceLineEdited(${idx}, 'procedure_code', this.value)"></td>
      <td><input type="text" value="${line.diagnosis_pointer || ''}" style="width: 35px; text-align: center;" onchange="markServiceLineEdited(${idx}, 'diagnosis_pointer', this.value)"></td>
      <td><input type="text" value="${line.charges !== null && line.charges !== undefined ? line.charges.toFixed(2) : ''}" style="font-weight: 600;" onchange="markServiceLineEdited(${idx}, 'charges', parseFloat(this.value))"></td>
      <td><input type="text" value="${line.units !== null && line.units !== undefined ? line.units : ''}" style="width: 35px; text-align: center;" onchange="markServiceLineEdited(${idx}, 'units', parseInt(this.value))"></td>
      <td><input type="text" value="${line.provider_npi || ''}" style="font-family: var(--font-mono);" onchange="markServiceLineEdited(${idx}, 'provider_npi', this.value)"></td>
    </tr>
  `).join('');
}

function renderFieldConfidences(confMap) {
  const container = document.getElementById('field-confidences-list');
  const entries = Object.entries(confMap);
  if (entries.length === 0) {
    container.innerHTML = `<span style="color: var(--text-muted);">No field confidence scores available.</span>`;
    return;
  }

  container.innerHTML = entries.map(([field, score]) => {
    const pct = (score * 100).toFixed(1);
    const color = score >= 0.95 ? 'var(--success)' : score >= 0.85 ? 'var(--warning)' : 'var(--danger)';
    const label = field.replace('_', ' ');
    return `
      <div style="display: flex; justify-content: space-between; align-items: center;">
        <span style="text-transform: capitalize;">${label}</span>
        <span style="font-weight: 700; color: ${color}; font-family: var(--font-mono);">${pct}%</span>
      </div>
    `;
  }).join('');
}

function renderValidationMessages(messages) {
  const container = document.getElementById('validation-messages-container');
  if (messages.length === 0) {
    container.innerHTML = `
      <div class="val-msg info">
        <span class="val-msg-code">ALL CHECKS PASSED</span>
        <span>No clinical or billing consistency errors detected.</span>
      </div>
    `;
    return;
  }

  container.innerHTML = messages.map(msg => `
    <div class="val-msg ${msg.level}">
      <span class="val-msg-code">${msg.code}</span>
      <span>${msg.message}</span>
    </div>
  `).join('');
}

// ============================================================================
// Field Editing
// ============================================================================

function markFieldEdited(fieldPath, value) {
  appState.pendingCorrections[fieldPath] = value;
  showToast(`Field modified: ${fieldPath}`, 'info');
}

function markDiagnosesEdited(rawString) {
  const codes = rawString.split(',').map(c => c.trim().toUpperCase()).filter(Boolean);
  appState.pendingCorrections['diagnosis_codes'] = codes;
}

function markServiceLineEdited(lineIdx, key, value) {
  const path = `service_lines[${lineIdx}].${key}`;
  appState.pendingCorrections[path] = value;
}

// ============================================================================
// Human Review Actions
// ============================================================================

async function approveCurrentClaim() {
  if (!appState.currentClaim) return;
  try {
    const res = await fetch(`/api/claims/${appState.currentClaim.claim_id}/approve`, {
      method: 'POST'
    });
    if (res.ok) {
      showToast('Claim approved successfully!', 'success');
      await openClaimDetail(appState.currentClaim.claim_id);
    }
  } catch (err) {
    showToast(`Error approving claim: ${err.message}`, 'error');
  }
}

async function saveCurrentCorrections() {
  if (!appState.currentClaim) return;
  try {
    const res = await fetch(`/api/claims/${appState.currentClaim.claim_id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'review',
        reviewer: 'Human Auditor',
        corrections: appState.pendingCorrections,
        notes: 'Manual field updates applied via ClaimBridge UI.'
      })
    });
    if (res.ok) {
      showToast('Corrections and audit trail saved!', 'success');
      await openClaimDetail(appState.currentClaim.claim_id);
    }
  } catch (err) {
    showToast(`Error saving corrections: ${err.message}`, 'error');
  }
}

async function rejectCurrentClaim() {
  if (!appState.currentClaim) return;
  try {
    const res = await fetch(`/api/claims/${appState.currentClaim.claim_id}/review`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action: 'reject',
        reviewer: 'Human Auditor',
        notes: 'Claim flagged for manual investigation.'
      })
    });
    if (res.ok) {
      showToast('Claim flagged/rejected for investigation.', 'warning');
      await openClaimDetail(appState.currentClaim.claim_id);
    }
  } catch (err) {
    showToast(`Error updating status: ${err.message}`, 'error');
  }
}

// ============================================================================
// Export Utilities
// ============================================================================

function exportCurrentJson() {
  if (!appState.currentClaim) return;
  window.open(`/api/claims/${appState.currentClaim.claim_id}/export`, '_blank');
  showToast('Downloading claim JSON...', 'info');
}

function exportCsv() {
  window.open('/api/claims/export/csv', '_blank');
  showToast('Exporting CSV summary...', 'info');
}

// ============================================================================
// Demo Mode vs Live Mode Toggle
// ============================================================================

async function setAppMode(mode) {
  appState.mode = mode;
  document.getElementById('mode-live-btn').classList.toggle('active', mode === 'live');
  document.getElementById('mode-demo-btn').classList.toggle('active', mode === 'demo');

  if (mode === 'demo') {
    showToast('Loading pre-verified 10-claim demo dataset...', 'info');
    try {
      const res = await fetch('/api/demo/load', { method: 'POST' });
      if (res.ok) {
        showToast('Demo dataset loaded successfully.', 'success');
        await fetchClaims();
      }
    } catch (err) {
      showToast(`Error loading demo data: ${err.message}`, 'error');
    }
  } else {
    showToast('Switched to Live Backend Mode. Ready for PDF uploads.', 'info');
  }
}

// ============================================================================
// Document Zoom Controls
// ============================================================================

function zoomDoc(delta) {
  appState.zoomLevel = Math.max(0.5, Math.min(2.5, appState.zoomLevel + delta));
  const img = document.getElementById('detail-claim-image');
  if (img) img.style.transform = `scale(${appState.zoomLevel})`;
}

function resetZoom() {
  appState.zoomLevel = 1.0;
  const img = document.getElementById('detail-claim-image');
  if (img) img.style.transform = 'scale(1.0)';
}

// ============================================================================
// Toast Notifications — with slide-in/out animation
// ============================================================================

function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : type === 'warning' ? '⚠' : 'ℹ';
  toast.innerHTML = `<span style="font-weight: bold;">${icon}</span> <span>${message}</span>`;
  
  container.appendChild(toast);
  
  // Auto-dismiss after 3 seconds with slide-out
  setTimeout(() => {
    toast.classList.add('toast-exit');
    toast.addEventListener('animationend', () => toast.remove(), { once: true });
    // Fallback removal
    setTimeout(() => { if (toast.parentNode) toast.remove(); }, 300);
  }, 3000);
}

// ============================================================================
// Utilities
// ============================================================================

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}
