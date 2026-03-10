const state = {
  apiBaseUrl: "",
  userId: "",
  selectedEmotion: "행복",
  intensity: 5,
  currentHq: 50,
  selectedPeriod: "today",
  emotionScores: {
    행복: 9.0,
    평온: 0.0,
    슬픔: -7.5,
    불안: -6.5,
    분노: -9.0,
  },
};

const elements = {};

document.addEventListener("DOMContentLoaded", () => {
  cacheElements();
  hydrateState();
  wireEvents();
  renderEmotionPicker();
  renderPeriodFilter();
  syncInputsFromState();
  refreshPreview();
  bootstrap();
});

function cacheElements() {
  elements.apiBaseUrlInput = document.querySelector("#api-base-url");
  elements.userIdInput = document.querySelector("#user-id");
  elements.saveSettingsButton = document.querySelector("#save-settings-button");
  elements.refreshButton = document.querySelector("#refresh-button");
  elements.emotionPicker = document.querySelector("#emotion-picker");
  elements.intensityRange = document.querySelector("#intensity-range");
  elements.intensityLabel = document.querySelector("#intensity-label");
  elements.noteInput = document.querySelector("#note-input");
  elements.saveRecordButton = document.querySelector("#save-record-button");
  elements.periodFilter = document.querySelector("#period-filter");

  elements.previewCurrentHq = document.querySelector("#preview-current-hq");
  elements.previewEmotionScore = document.querySelector("#preview-emotion-score");
  elements.previewDeltaHq = document.querySelector("#preview-delta-hq");
  elements.previewNextHq = document.querySelector("#preview-next-hq");

  elements.summaryRecordCount = document.querySelector("#summary-record-count");
  elements.summaryMostEmotion = document.querySelector("#summary-most-emotion");
  elements.summaryAverageHq = document.querySelector("#summary-average-hq");
  elements.summaryCurrentHq = document.querySelector("#summary-current-hq");

  elements.timelineChart = document.querySelector("#timeline-chart");
  elements.hourlyChart = document.querySelector("#hourly-chart");
  elements.weekdayChart = document.querySelector("#weekday-chart");
  elements.recordsList = document.querySelector("#records-list");

  elements.statusDot = document.querySelector("#status-dot");
  elements.healthLabel = document.querySelector("#health-label");
  elements.storageBackendLabel = document.querySelector("#storage-backend-label");
  elements.toast = document.querySelector("#toast");
}

function hydrateState() {
  const config = window.EMOTION_TRACKER_CONFIG || {};
  const storedApiBaseUrl = localStorage.getItem("emotion-tracker-api-base-url");
  const storedUserId = localStorage.getItem("emotion-tracker-user-id");

  state.apiBaseUrl = storedApiBaseUrl || config.API_BASE_URL || window.location.origin;
  state.userId = storedUserId || buildGuestId();
}

function wireEvents() {
  elements.saveSettingsButton.addEventListener("click", () => {
    state.apiBaseUrl = normalizeApiBaseUrl(elements.apiBaseUrlInput.value);
    state.userId = elements.userIdInput.value.trim() || buildGuestId();

    localStorage.setItem("emotion-tracker-api-base-url", state.apiBaseUrl);
    localStorage.setItem("emotion-tracker-user-id", state.userId);

    syncInputsFromState();
    refreshPreview();
    bootstrap();
    showToast("설정을 저장했습니다.");
  });

  elements.refreshButton.addEventListener("click", () => bootstrap());

  elements.intensityRange.addEventListener("input", (event) => {
    state.intensity = Number(event.target.value);
    elements.intensityLabel.textContent = String(state.intensity);
    refreshPreview();
  });

  elements.saveRecordButton.addEventListener("click", async () => {
    try {
      await apiRequest(`/api/v1/users/${encodeURIComponent(state.userId)}/records`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          emotion: state.selectedEmotion,
          intensity: state.intensity,
          note: elements.noteInput.value.trim(),
        }),
      });

      elements.noteInput.value = "";
      showToast("감정 기록을 저장했습니다.");
      await loadCurrentHq();
      await loadAnalytics();
      refreshPreview();
    } catch (error) {
      showToast(error.message, true);
    }
  });
}

async function bootstrap() {
  syncInputsFromState();
  await loadMeta();
  await loadHealth();
  await loadCurrentHq();
  await loadAnalytics();
  refreshPreview();
}

function syncInputsFromState() {
  elements.apiBaseUrlInput.value = state.apiBaseUrl;
  elements.userIdInput.value = state.userId;
  elements.intensityRange.value = String(state.intensity);
  elements.intensityLabel.textContent = String(state.intensity);
}

async function loadMeta() {
  try {
    const payload = await apiRequest("/api/v1/meta");
    state.emotionScores = Object.fromEntries(
      payload.emotions.map((emotion) => [emotion.key, Number(emotion.score)])
    );
    if (!state.emotionScores[state.selectedEmotion]) {
      state.selectedEmotion = payload.emotions[0]?.key || "행복";
    }
    renderEmotionPicker();
    refreshPreview();
  } catch (error) {
    showToast(`메타 데이터를 불러오지 못했습니다: ${error.message}`, true);
  }
}

async function loadHealth() {
  try {
    const [health, storage] = await Promise.all([
      apiRequest("/health"),
      apiRequest("/storage"),
    ]);
    elements.statusDot.className = "status-dot ok";
    elements.healthLabel.textContent = "백엔드 연결 완료";
    elements.storageBackendLabel.textContent = storage.backend || health.storage_backend;
  } catch (error) {
    elements.statusDot.className = "status-dot error";
    elements.healthLabel.textContent = "백엔드 연결 실패";
    elements.storageBackendLabel.textContent = "Unavailable";
    showToast(`백엔드 연결 실패: ${error.message}`, true);
  }
}

async function loadCurrentHq() {
  try {
    const payload = await apiRequest(
      `/api/v1/users/${encodeURIComponent(state.userId)}/hq`
    );
    state.currentHq = Number(payload.current_hq || 50);
  } catch (error) {
    state.currentHq = 50;
    showToast(`현재 HQ를 가져오지 못했습니다: ${error.message}`, true);
  }
}

async function loadAnalytics() {
  try {
    const payload = await apiRequest(
      `/api/v1/users/${encodeURIComponent(state.userId)}/analytics?period=${state.selectedPeriod}`
    );
    renderSummary(payload.summary);
    renderTimelineChart(payload.records);
    renderBarsChart(elements.hourlyChart, payload.hourly, "hour_label");
    renderBarsChart(elements.weekdayChart, payload.weekday, "weekday");
    renderRecords(payload.records);
  } catch (error) {
    showToast(`분석 데이터를 가져오지 못했습니다: ${error.message}`, true);
  }
}

function renderEmotionPicker() {
  const emotions = Object.entries(state.emotionScores);
  elements.emotionPicker.innerHTML = emotions
    .map(([emotion, score]) => {
      const activeClass = state.selectedEmotion === emotion ? "active" : "";
      return `
        <button class="emotion-button ${activeClass}" data-emotion="${emotion}">
          ${emotion} <small>(${formatNumber(score)})</small>
        </button>
      `;
    })
    .join("");

  elements.emotionPicker.querySelectorAll(".emotion-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedEmotion = button.dataset.emotion;
      renderEmotionPicker();
      refreshPreview();
    });
  });
}

function renderPeriodFilter() {
  const periodLabels = {
    today: "오늘",
    week: "이번 주",
    month: "이번 달",
    all: "전체",
  };

  elements.periodFilter.innerHTML = Object.entries(periodLabels)
    .map(([period, label]) => {
      const activeClass = state.selectedPeriod === period ? "active" : "";
      return `<button class="period-button ${activeClass}" data-period="${period}">${label}</button>`;
    })
    .join("");

  elements.periodFilter.querySelectorAll(".period-button").forEach((button) => {
    button.addEventListener("click", async () => {
      state.selectedPeriod = button.dataset.period;
      renderPeriodFilter();
      await loadAnalytics();
    });
  });
}

function refreshPreview() {
  const score = Number(state.emotionScores[state.selectedEmotion] || 0);
  const deltaHq = score * (state.intensity / 15);
  const adjustmentFactor = 1 - Math.abs(state.currentHq - 50) / 100;
  const adjustedDelta = deltaHq * adjustmentFactor;
  const nextHq = clamp(state.currentHq + adjustedDelta, 0, 100);

  elements.previewCurrentHq.textContent = formatFixed(state.currentHq);
  elements.previewEmotionScore.textContent = formatFixed(score);
  elements.previewDeltaHq.textContent = `${adjustedDelta >= 0 ? "+" : ""}${formatFixed(adjustedDelta)}`;
  elements.previewNextHq.textContent = formatFixed(nextHq);
}

function renderSummary(summary) {
  elements.summaryRecordCount.textContent = `${summary.record_count ?? 0}`;
  elements.summaryMostEmotion.textContent = summary.most_common_emotion || "-";
  elements.summaryAverageHq.textContent = summary.average_hq != null ? formatFixed(summary.average_hq) : "-";
  elements.summaryCurrentHq.textContent = summary.current_hq != null ? formatFixed(summary.current_hq) : "-";
}

function renderTimelineChart(records) {
  if (!records || records.length === 0) {
    elements.timelineChart.innerHTML = `<div class="empty-state">아직 표시할 기록이 없습니다.</div>`;
    return;
  }

  const width = 720;
  const height = 240;
  const padding = 24;
  const points = records.map((record, index) => {
    const x = padding + (index / Math.max(records.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - ((Number(record.HQ_current) || 0) / 100) * (height - padding * 2);
    return { x, y };
  });

  const path = points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x},${point.y}`).join(" ");
  const circles = points
    .map(
      (point) => `
        <circle cx="${point.x}" cy="${point.y}" r="4.5" fill="#ef5b3f"></circle>
      `
    )
    .join("");
  const yGuides = [0, 25, 50, 75, 100]
    .map((value) => {
      const y = height - padding - (value / 100) * (height - padding * 2);
      return `
        <line x1="${padding}" x2="${width - padding}" y1="${y}" y2="${y}" stroke="rgba(17,32,25,0.08)" />
        <text x="${padding}" y="${y - 6}" fill="#5f6d65" font-size="11">${value}</text>
      `;
    })
    .join("");

  elements.timelineChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="시간 순 HQ 추이">
      ${yGuides}
      <path d="${path}" fill="none" stroke="#112019" stroke-width="3" stroke-linecap="round"></path>
      ${circles}
    </svg>
  `;
}

function renderBarsChart(container, rows, labelKey) {
  if (!rows || rows.length === 0) {
    container.innerHTML = `<div class="empty-state">아직 표시할 데이터가 없습니다.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="bars-list">
      ${rows
        .map((row) => {
          const value = Number(row.average_hq || 0);
          const width = `${clamp(value, 0, 100)}%`;
          return `
            <div class="bar-row">
              <span class="bar-label">${row[labelKey]}</span>
              <div class="bar-track">
                <div class="bar-fill" style="width:${width}"></div>
              </div>
              <span class="bar-value">${formatFixed(value)}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderRecords(records) {
  if (!records || records.length === 0) {
    elements.recordsList.innerHTML = `<div class="empty-state">기록을 추가하면 여기에 쌓입니다.</div>`;
    return;
  }

  const formatted = [...records].reverse().slice(0, 12);
  elements.recordsList.innerHTML = formatted
    .map((record) => {
      const timestamp = new Date(record.timestamp);
      const note = record.note ? `<p class="record-note">${escapeHtml(record.note)}</p>` : "";
      return `
        <article class="record-item">
          <div class="record-topline">
            <strong class="record-emotion">${record.emotion}</strong>
            <span class="record-timestamp">${timestamp.toLocaleString("ko-KR")}</span>
          </div>
          <div class="record-meta">
            <span>강도 ${record.intensity}</span>
            <span>HQ ${formatFixed(record.HQ_previous)} → ${formatFixed(record.HQ_current)}</span>
            <span>점수 ${formatFixed(record.emotion_score)}</span>
          </div>
          ${note}
        </article>
      `;
    })
    .join("");
}

async function apiRequest(path, options = {}) {
  const response = await fetch(`${normalizeApiBaseUrl(state.apiBaseUrl)}${path}`, options);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `${response.status} ${response.statusText}`);
  }

  return response.json();
}

function normalizeApiBaseUrl(value) {
  return (value || window.location.origin).replace(/\/$/, "");
}

function buildGuestId() {
  return `guest-${Math.random().toString(36).slice(2, 8)}`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function formatFixed(value) {
  return Number(value).toFixed(2);
}

function formatNumber(value) {
  const number = Number(value);
  return `${number >= 0 ? "+" : ""}${number.toFixed(1)}`;
}

function escapeHtml(text) {
  return text
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

let toastTimer = null;
function showToast(message, isError = false) {
  elements.toast.textContent = message;
  elements.toast.style.background = isError ? "#7f1d1d" : "#112019";
  elements.toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 2600);
}
