import { initializeApp } from "https://www.gstatic.com/firebasejs/12.7.0/firebase-app.js";
import {
  GoogleAuthProvider,
  browserLocalPersistence,
  browserPopupRedirectResolver,
  browserSessionPersistence,
  indexedDBLocalPersistence,
  getRedirectResult,
  initializeAuth,
  linkWithPopup,
  linkWithRedirect,
  onAuthStateChanged,
  signInAnonymously,
  signInWithPopup,
  signInWithRedirect,
  signOut,
} from "https://www.gstatic.com/firebasejs/12.7.0/firebase-auth.js";
import {
  Timestamp,
  collection,
  doc,
  getDoc,
  getFirestore,
  increment,
  onSnapshot,
  orderBy,
  query,
  runTransaction,
  serverTimestamp,
  setDoc,
  where,
} from "https://www.gstatic.com/firebasejs/12.7.0/firebase-firestore.js";

const EMOTION_OPTIONS = [
  { key: "행복", score: 9.0, icon: "sunny" },
  { key: "평온", score: 0.0, icon: "spa" },
  { key: "슬픔", score: -7.5, icon: "cloud" },
  { key: "불안", score: -6.5, icon: "routine" },
  { key: "분노", score: -9.0, icon: "bolt" },
];

const PERIOD_LABELS = {
  today: "오늘",
  week: "이번 주",
  month: "이번 달",
  all: "전체",
};

const WEEKDAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"];
const DEFAULT_HQ = 50;

const state = {
  app: null,
  db: null,
  auth: null,
  collectionName: "emotion_records",
  user: null,
  projectId: "-",
  nickname: "",
  selectedEmotion: "행복",
  intensity: 5,
  currentHq: DEFAULT_HQ,
  lifetimeRecordCount: 0,
  selectedPeriod: "week",
  records: [],
  unsubscribeSummary: null,
  unsubscribeRecords: null,
  isConfigured: false,
};

const elements = {};
const googleProvider = new GoogleAuthProvider();
googleProvider.setCustomParameters({ prompt: "select_account" });

document.addEventListener("DOMContentLoaded", async () => {
  cacheElements();
  hydrateLocalState();
  wireEvents();
  renderEmotionPicker();
  renderPeriodFilter();
  syncInputsFromState();
  renderIdentity();
  refreshPreview();
  await bootstrapFirebase();
});

function cacheElements() {
  elements.setupBanner = document.querySelector("#setup-banner");
  elements.nicknameInput = document.querySelector("#nickname-input");
  elements.nicknameBadge = document.querySelector("#nickname-badge");
  elements.authHelpText = document.querySelector("#auth-help-text");
  elements.saveNicknameButton = document.querySelector("#save-nickname-button");
  elements.refreshButton = document.querySelector("#refresh-button");
  elements.googleLoginButton = document.querySelector("#google-login-button");
  elements.anonymousLoginButton = document.querySelector("#anonymous-login-button");
  elements.signOutButton = document.querySelector("#sign-out-button");
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
  elements.connectionLabel = document.querySelector("#connection-label");
  elements.authStatusLabel = document.querySelector("#auth-status-label");
  elements.projectIdLabel = document.querySelector("#project-id-label");
  elements.userKeyLabel = document.querySelector("#user-key-label");
  elements.heroCurrentHq = document.querySelector("#hero-current-hq");
  elements.lifetimeRecordCount = document.querySelector("#lifetime-record-count");
  elements.toast = document.querySelector("#toast");
}

function hydrateLocalState() {
  state.nickname = localStorage.getItem("emotion-tracker-nickname") || "";
}

function wireEvents() {
  elements.saveNicknameButton.addEventListener("click", () => {
    state.nickname = elements.nicknameInput.value.trim();
    localStorage.setItem("emotion-tracker-nickname", state.nickname);
    renderIdentity();
    showToast("닉네임 저장");
  });

  elements.refreshButton.addEventListener("click", () => {
    if (!state.isConfigured || !state.user) {
      showToast("연결이 아직 준비되지 않았습니다", true);
      return;
    }

    subscribeSummary();
    subscribeRecords();
    showToast("동기화 새로고침");
  });

  elements.googleLoginButton.addEventListener("click", async () => {
    if (!state.auth) {
      showToast("Firebase 초기화가 끝난 뒤 다시 시도해주세요", true);
      return;
    }

    if (isEmbeddedBrowser()) {
      showToast("카카오톡·앱 내 브라우저 대신 Chrome 또는 Safari에서 열어주세요", true);
      return;
    }

    elements.googleLoginButton.disabled = true;

    try {
      if (shouldUseRedirectAuth()) {
        if (state.user?.isAnonymous) {
          await linkWithRedirect(state.user, googleProvider);
        } else {
          await signInWithRedirect(state.auth, googleProvider);
        }
        return;
      }

      if (state.user?.isAnonymous) {
        try {
          await linkWithPopup(state.user, googleProvider);
          showToast("Google 계정으로 연결했습니다");
          return;
        } catch (error) {
          if (error?.code !== "auth/credential-already-in-use") {
            throw error;
          }
        }
      }

      await signInWithPopup(state.auth, googleProvider);
      showToast("Google 로그인 완료");
    } catch (error) {
      showToast(readableError(error), true);
    } finally {
      elements.googleLoginButton.disabled = false;
    }
  });

  elements.anonymousLoginButton.addEventListener("click", async () => {
    if (!state.auth) {
      showToast("Firebase 초기화가 끝난 뒤 다시 시도해주세요", true);
      return;
    }

    elements.anonymousLoginButton.disabled = true;
    try {
      await signInAnonymously(state.auth);
      showToast("익명으로 시작했습니다");
    } catch (error) {
      showToast(readableError(error), true);
    } finally {
      elements.anonymousLoginButton.disabled = false;
    }
  });

  elements.signOutButton.addEventListener("click", async () => {
    if (!state.auth || !state.user) {
      return;
    }

    elements.signOutButton.disabled = true;
    try {
      await signOut(state.auth);
      showToast("로그아웃했습니다");
    } catch (error) {
      showToast(readableError(error), true);
    } finally {
      elements.signOutButton.disabled = false;
    }
  });

  elements.intensityRange.addEventListener("input", (event) => {
    state.intensity = Number(event.target.value);
    elements.intensityLabel.textContent = String(state.intensity);
    refreshPreview();
  });

  elements.saveRecordButton.addEventListener("click", async () => {
    if (!state.db || !state.user) {
      showToast("먼저 Firebase 연결을 확인해주세요", true);
      return;
    }

    const note = elements.noteInput.value.trim();
    elements.saveRecordButton.disabled = true;

    try {
      const record = await persistEmotionRecord(note);
      state.currentHq = record.hqCurrent;
      elements.noteInput.value = "";
      refreshPreview();
      showToast("감정 저장 완료");
    } catch (error) {
      showToast(readableError(error), true);
    } finally {
      elements.saveRecordButton.disabled = false;
    }
  });
}

async function bootstrapFirebase() {
  const clientConfig = getClientConfig();
  state.collectionName = clientConfig.collectionName;
  state.projectId = clientConfig.firebase.projectId || "-";
  renderIdentity();

  if (!clientConfig.isValid) {
    setConnectionState("설정 필요", "warn");
    elements.authStatusLabel.textContent = "설정 대기";
    elements.setupBanner.hidden = false;
    elements.saveRecordButton.disabled = true;
    return;
  }

  try {
    state.app = initializeApp(clientConfig.firebase);
    state.db = getFirestore(state.app);
    state.auth = initializeAuth(state.app, {
      persistence: [
        indexedDBLocalPersistence,
        browserLocalPersistence,
        browserSessionPersistence,
      ],
      popupRedirectResolver: browserPopupRedirectResolver,
    });
    try {
      const redirectResult = await getRedirectResult(state.auth);
      if (redirectResult?.user) {
        showToast("Google 로그인 완료");
      }
    } catch (error) {
      showToast(readableError(error), true);
    }
    state.isConfigured = true;
    elements.setupBanner.hidden = true;
    setConnectionState("연결 준비됨", "warn");

    onAuthStateChanged(state.auth, async (user) => {
      if (!user) {
        state.user = null;
        state.currentHq = DEFAULT_HQ;
        state.lifetimeRecordCount = 0;
        state.records = [];
        disposeSubscription("unsubscribeSummary");
        disposeSubscription("unsubscribeRecords");
        elements.authStatusLabel.textContent = "로그인 전";
        elements.saveRecordButton.disabled = true;
        setConnectionState("로그인 필요", "warn");
        renderIdentity();
        renderAnalytics();
        renderRecords();
        refreshPreview();
        return;
      }

      state.user = user;
      elements.authStatusLabel.textContent = user.isAnonymous ? "익명 사용자" : "Google 로그인";
      renderIdentity();

      await ensureUserSummaryDoc();
      subscribeSummary();
      subscribeRecords();
      setConnectionState("실시간 연결 중", "ok");
      elements.saveRecordButton.disabled = false;
    });
  } catch (error) {
    setConnectionState("초기화 실패", "error");
    showToast(readableError(error), true);
  }
}

async function ensureUserSummaryDoc() {
  const userRef = getUserDocRef();
  const snapshot = await getDoc(userRef);
  if (snapshot.exists()) {
    return;
  }

  await setDoc(
    userRef,
    {
      currentHq: DEFAULT_HQ,
      recordCount: 0,
      createdAt: serverTimestamp(),
      updatedAt: serverTimestamp(),
    },
    { merge: true }
  );
}

async function persistEmotionRecord(note) {
  const userRef = getUserDocRef();
  const recordsRef = collection(userRef, state.collectionName);
  let savedRecord = null;

  await runTransaction(state.db, async (transaction) => {
    const summarySnapshot = await transaction.get(userRef);
    const summaryData = summarySnapshot.exists() ? summarySnapshot.data() : {};
    const previousHq = Number(summaryData.currentHq ?? DEFAULT_HQ);
    const calculation = calculateHq(previousHq, state.selectedEmotion, state.intensity);
    const recordedAt = Timestamp.now();
    const recordRef = doc(recordsRef);

    transaction.set(recordRef, {
      emotion: calculation.emotion,
      emotionScore: calculation.emotionScore,
      intensity: calculation.intensity,
      note,
      hqPrevious: calculation.hqPrevious,
      hqCurrent: calculation.hqCurrent,
      deltaHq: calculation.deltaHq,
      adjustmentFactor: calculation.adjustmentFactor,
      recordedAt,
      createdAt: serverTimestamp(),
    });

    const summaryUpdate = {
      currentHq: calculation.hqCurrent,
      lastEmotion: calculation.emotion,
      lastRecordedAt: recordedAt,
      recordCount: increment(1),
      updatedAt: serverTimestamp(),
    };

    if (!summarySnapshot.exists()) {
      summaryUpdate.createdAt = serverTimestamp();
    }

    transaction.set(userRef, summaryUpdate, { merge: true });

    savedRecord = {
      id: recordRef.id,
      ...calculation,
      note,
      recordedAt: recordedAt.toDate(),
    };
  });

  return savedRecord;
}

function subscribeSummary() {
  disposeSubscription("unsubscribeSummary");

  state.unsubscribeSummary = onSnapshot(
    getUserDocRef(),
    (snapshot) => {
      const data = snapshot.exists() ? snapshot.data() : {};
      state.currentHq = Number(data.currentHq ?? DEFAULT_HQ);
      state.lifetimeRecordCount = Number(data.recordCount ?? 0);
      elements.heroCurrentHq.textContent = formatFixed(state.currentHq);
      elements.lifetimeRecordCount.textContent = `${state.lifetimeRecordCount}`;
      refreshPreview();
    },
    (error) => {
      setConnectionState("요약 오류", "error");
      showToast(readableError(error), true);
    }
  );
}

function subscribeRecords() {
  disposeSubscription("unsubscribeRecords");

  const constraints = [];
  const startDate = getPeriodStart(state.selectedPeriod);
  if (startDate) {
    constraints.push(where("recordedAt", ">=", Timestamp.fromDate(startDate)));
  }
  constraints.push(orderBy("recordedAt", "asc"));

  const recordsQuery = query(
    collection(getUserDocRef(), state.collectionName),
    ...constraints
  );

  state.unsubscribeRecords = onSnapshot(
    recordsQuery,
    (snapshot) => {
      state.records = snapshot.docs.map((recordDoc) => normalizeRecord(recordDoc.id, recordDoc.data()));
      renderAnalytics();
      renderRecords();
    },
    (error) => {
      setConnectionState("기록 오류", "error");
      showToast(readableError(error), true);
    }
  );
}

function renderEmotionPicker() {
  elements.emotionPicker.innerHTML = EMOTION_OPTIONS.map((emotion) => {
    const activeClass = emotion.key === state.selectedEmotion ? "active" : "";
    return `
      <button class="emotion-button ${activeClass}" data-emotion="${emotion.key}" type="button">
        <span class="material-symbols-outlined">${emotion.icon}</span>
        <strong>${emotion.key}</strong>
      </button>
    `;
  }).join("");

  elements.emotionPicker.querySelectorAll(".emotion-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedEmotion = button.dataset.emotion;
      renderEmotionPicker();
      refreshPreview();
    });
  });
}

function renderPeriodFilter() {
  elements.periodFilter.innerHTML = Object.entries(PERIOD_LABELS)
    .map(([period, label]) => {
      const activeClass = period === state.selectedPeriod ? "active" : "";
      return `<button class="period-button ${activeClass}" data-period="${period}" type="button">${label}</button>`;
    })
    .join("");

  elements.periodFilter.querySelectorAll(".period-button").forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedPeriod = button.dataset.period;
      renderPeriodFilter();
      if (state.user) {
        subscribeRecords();
      }
    });
  });
}

function renderAnalytics() {
  const summary = buildSummary(state.records, state.currentHq);
  const hourly = calculateHourlyHqChange(state.records);
  const weekday = calculateWeekdayHqChange(state.records);

  elements.summaryRecordCount.textContent = `${summary.recordCount}`;
  elements.summaryMostEmotion.textContent = summary.mostCommonEmotion || "-";
  elements.summaryAverageHq.textContent = summary.averageHq == null ? "-" : formatFixed(summary.averageHq);
  elements.summaryCurrentHq.textContent = formatFixed(summary.currentHq);

  renderTimelineChart(state.records);
  renderBarsChart(elements.hourlyChart, hourly, "hourLabel");
  renderBarsChart(elements.weekdayChart, weekday, "weekday");
}

function renderRecords() {
  if (!state.records.length) {
    elements.recordsList.innerHTML = `<div class="empty-state">아직 남겨둔 기록이 없습니다.</div>`;
    return;
  }

  const latest = [...state.records].reverse().slice(0, 10);
  elements.recordsList.innerHTML = latest
    .map((record) => {
      const meta = getEmotionMeta(record.emotion);
      const note = record.note ? `<p class="record-note">${escapeHtml(record.note)}</p>` : "";
      return `
        <article class="record-item">
          <div class="record-icon">
            <span class="material-symbols-outlined">${meta.icon}</span>
          </div>
          <div class="record-copy">
            <strong class="record-title">${record.emotion}의 순간</strong>
            <div class="record-date">${formatDateTime(record.recordedAt)}</div>
            <div class="record-meta">강도 ${record.intensity} · HQ ${formatFixed(record.hqPrevious)} -> ${formatFixed(record.hqCurrent)}</div>
            ${note}
          </div>
        </article>
      `;
    })
    .join("");
}

function renderTimelineChart(records) {
  if (!records.length) {
    elements.timelineChart.innerHTML = `<div class="empty-state">흐름을 그릴 기록이 아직 없습니다.</div>`;
    return;
  }

  const width = 720;
  const height = 210;
  const padding = 20;
  const points = records.map((record, index) => {
    const x = padding + (index / Math.max(records.length - 1, 1)) * (width - padding * 2);
    const y = height - padding - (Number(record.hqCurrent) / 100) * (height - padding * 2);
    return { x, y };
  });

  const path = points.map((point, index) => `${index === 0 ? "M" : "L"}${point.x},${point.y}`).join(" ");
  const circles = points
    .map((point) => `<circle cx="${point.x}" cy="${point.y}" r="4" fill="#11d4c4"></circle>`)
    .join("");
  const guides = [0, 25, 50, 75, 100]
    .map((value) => {
      const y = height - padding - (value / 100) * (height - padding * 2);
      return `
        <line x1="${padding}" x2="${width - padding}" y1="${y}" y2="${y}" stroke="rgba(255,255,255,0.1)"></line>
        <text x="${padding}" y="${y - 6}" font-size="11">${value}</text>
      `;
    })
    .join("");

  elements.timelineChart.innerHTML = `
    <svg viewBox="0 0 ${width} ${height}" role="img" aria-label="HQ 흐름 차트">
      ${guides}
      <path d="${path}" fill="none" stroke="#ffffff" stroke-width="3" stroke-linecap="round"></path>
      ${circles}
    </svg>
  `;
}

function renderBarsChart(container, rows, labelKey) {
  if (!rows.length) {
    container.innerHTML = `<div class="empty-state">아직 보여줄 데이터가 없습니다.</div>`;
    return;
  }

  container.innerHTML = `
    <div class="bars-list">
      ${rows
        .map((row) => {
          const value = Number(row.averageHq || 0);
          return `
            <div class="bar-row">
              <span class="bar-label">${row[labelKey]}</span>
              <div class="bar-track">
                <div class="bar-fill" style="width:${clamp(value, 0, 100)}%"></div>
              </div>
              <span class="bar-value">${formatFixed(value)}</span>
            </div>
          `;
        })
        .join("")}
    </div>
  `;
}

function renderIdentity() {
  const fallbackName = state.user?.displayName?.trim() || (state.user?.isAnonymous ? "익명 방문자" : "마음 사용자");
  const nickname = state.nickname || fallbackName;
  elements.nicknameInput.value = state.nickname;
  elements.nicknameBadge.textContent = nickname;
  elements.projectIdLabel.textContent = state.projectId === "-" ? "프로젝트 -" : `프로젝트 ${state.projectId}`;
  elements.userKeyLabel.textContent = state.user ? `UID ${shortenUid(state.user.uid)}` : "UID -";
  elements.heroCurrentHq.textContent = formatFixed(state.currentHq);
  elements.lifetimeRecordCount.textContent = `${state.lifetimeRecordCount}`;
  elements.googleLoginButton.hidden = Boolean(state.user && !state.user.isAnonymous);
  elements.anonymousLoginButton.hidden = Boolean(state.user);
  elements.signOutButton.hidden = !state.user;

  if (!state.user) {
    elements.authHelpText.textContent = "Google로 로그인하면 어떤 기기에서 접속해도 같은 기록을 이어서 볼 수 있습니다.";
  } else if (state.user.isAnonymous) {
    elements.authHelpText.textContent = "익명 기록은 이 브라우저 안에서만 이어집니다. 기기 간 동기화가 필요하면 Google 로그인을 사용하세요.";
  } else {
    elements.authHelpText.textContent = "지금은 Google 계정 기준으로 기록이 묶여 있습니다. 다른 기기에서도 같은 계정으로 이어집니다.";
  }
}

function syncInputsFromState() {
  elements.intensityRange.value = String(state.intensity);
  elements.intensityLabel.textContent = String(state.intensity);
}

function refreshPreview() {
  const calculation = calculateHq(state.currentHq, state.selectedEmotion, state.intensity);
  elements.previewCurrentHq.textContent = formatFixed(state.currentHq);
  elements.previewEmotionScore.textContent = formatFixed(calculation.emotionScore);
  elements.previewDeltaHq.textContent = formatSigned(calculation.deltaHq);
  elements.previewNextHq.textContent = formatFixed(calculation.hqCurrent);
  elements.summaryCurrentHq.textContent = formatFixed(state.currentHq);
}

function calculateHq(previousHq, emotion, intensity) {
  const emotionScore = getEmotionScore(emotion);
  const normalizedPrevious = clamp(Number(previousHq) || DEFAULT_HQ, 0, 100);
  const intensityValue = clamp(Number(intensity) || 1, 1, 10);
  const deltaHq = emotionScore * (intensityValue / 15);
  const adjustmentFactor = 1 - Math.abs(normalizedPrevious - 50) / 100;
  const adjustedDelta = deltaHq * adjustmentFactor;
  const currentHq = clamp(normalizedPrevious + adjustedDelta, 0, 100);

  return {
    emotion,
    emotionScore: round2(emotionScore),
    intensity: intensityValue,
    hqPrevious: round2(normalizedPrevious),
    hqCurrent: round2(currentHq),
    deltaHq: round2(adjustedDelta),
    adjustmentFactor: round4(adjustmentFactor),
  };
}

function buildSummary(records, currentHq) {
  if (!records.length) {
    return {
      recordCount: 0,
      mostCommonEmotion: null,
      averageHq: null,
      currentHq,
    };
  }

  const averageHq =
    records.reduce((total, record) => total + Number(record.hqCurrent || 0), 0) / records.length;

  return {
    recordCount: records.length,
    mostCommonEmotion: calculateMostCommonEmotion(records),
    averageHq: round2(averageHq),
    currentHq,
  };
}

function calculateMostCommonEmotion(records) {
  const counts = new Map();
  records.forEach((record) => {
    counts.set(record.emotion, (counts.get(record.emotion) || 0) + 1);
  });

  let winner = null;
  let maxCount = -1;
  counts.forEach((count, emotion) => {
    if (count > maxCount) {
      winner = emotion;
      maxCount = count;
    }
  });
  return winner;
}

function calculateHourlyHqChange(records) {
  const grouped = new Map();
  records.forEach((record) => {
    const date = record.recordedAt;
    const hour = date.getHours();
    const hourLabel = `${String(hour).padStart(2, "0")}:00`;
    const current = grouped.get(hour) || { hour, hourLabel, total: 0, count: 0 };
    current.total += Number(record.hqCurrent || 0);
    current.count += 1;
    grouped.set(hour, current);
  });

  return [...grouped.values()]
    .sort((a, b) => a.hour - b.hour)
    .map((row) => ({
      hour: row.hour,
      hourLabel: row.hourLabel,
      averageHq: round2(row.total / row.count),
      recordCount: row.count,
    }));
}

function calculateWeekdayHqChange(records) {
  const grouped = new Map();
  records.forEach((record) => {
    const weekdayIndex = (record.recordedAt.getDay() + 6) % 7;
    const weekday = WEEKDAY_LABELS[weekdayIndex];
    const current = grouped.get(weekdayIndex) || { weekdayIndex, weekday, total: 0, count: 0 };
    current.total += Number(record.hqCurrent || 0);
    current.count += 1;
    grouped.set(weekdayIndex, current);
  });

  return [...grouped.values()]
    .sort((a, b) => a.weekdayIndex - b.weekdayIndex)
    .map((row) => ({
      weekdayIndex: row.weekdayIndex,
      weekday: row.weekday,
      averageHq: round2(row.total / row.count),
      recordCount: row.count,
    }));
}

function normalizeRecord(id, data) {
  return {
    id,
    emotion: data.emotion,
    emotionScore: Number(data.emotionScore || 0),
    intensity: Number(data.intensity || 0),
    note: data.note || "",
    hqPrevious: Number(data.hqPrevious ?? DEFAULT_HQ),
    hqCurrent: Number(data.hqCurrent ?? DEFAULT_HQ),
    deltaHq: Number(data.deltaHq ?? 0),
    adjustmentFactor: Number(data.adjustmentFactor ?? 1),
    recordedAt: toDate(data.recordedAt) || new Date(),
  };
}

function getClientConfig() {
  const config = window.EMOTION_TRACKER_CONFIG || {};
  const firebase = config.firebase || {};
  const requiredKeys = ["apiKey", "authDomain", "projectId", "appId"];
  const missingKeys = requiredKeys.filter((key) => !String(firebase[key] || "").trim());

  return {
    firebase,
    collectionName: config.app?.collectionName || "emotion_records",
    isValid: missingKeys.length === 0,
    missingKeys,
  };
}

function getUserDocRef() {
  return doc(state.db, "users", state.user.uid);
}

function getEmotionScore(emotion) {
  return getEmotionMeta(emotion).score;
}

function getEmotionMeta(emotion) {
  return EMOTION_OPTIONS.find((item) => item.key === emotion) || EMOTION_OPTIONS[0];
}

function getPeriodStart(period) {
  const now = new Date();
  const start = new Date(now);
  start.setHours(0, 0, 0, 0);

  if (period === "today") {
    return start;
  }
  if (period === "week") {
    const weekday = (start.getDay() + 6) % 7;
    start.setDate(start.getDate() - weekday);
    return start;
  }
  if (period === "month") {
    start.setDate(1);
    return start;
  }
  return null;
}

function shouldUseRedirectAuth() {
  return /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
}

function isEmbeddedBrowser() {
  const ua = navigator.userAgent || "";
  return /KAKAOTALK|FBAN|FBAV|Instagram|NAVER|Line|wv|TikTok|Twitter/i.test(ua);
}

function setConnectionState(message, level) {
  elements.connectionLabel.textContent = message;
  elements.statusDot.className = `status-dot ${level}`;
}

function disposeSubscription(key) {
  if (typeof state[key] === "function") {
    state[key]();
    state[key] = null;
  }
}

function toDate(value) {
  if (!value) {
    return null;
  }
  if (value instanceof Date) {
    return value;
  }
  if (typeof value.toDate === "function") {
    return value.toDate();
  }
  return new Date(value);
}

function shortenUid(uid) {
  return uid.length <= 10 ? uid : `${uid.slice(0, 4)}-${uid.slice(-3)}`;
}

function formatDateTime(value) {
  return new Intl.DateTimeFormat("ko-KR", {
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(value);
}

function formatFixed(value) {
  return Number(value).toFixed(2);
}

function formatSigned(value) {
  const number = Number(value);
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}`;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function round2(value) {
  return Math.round(Number(value) * 100) / 100;
}

function round4(value) {
  return Math.round(Number(value) * 10000) / 10000;
}

function readableError(error) {
  const message = typeof error?.message === "string" ? error.message : String(error);
  return message.replace(/^Firebase:\s*/, "");
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
  elements.toast.style.background = isError ? "#7f1d1d" : "#1a1a1a";
  elements.toast.classList.add("visible");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    elements.toast.classList.remove("visible");
  }, 2200);
}
