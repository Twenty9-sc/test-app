/* =========================================================================
   BOSS-E 🎯 — Application (beta v2)
   ========================================================================= */
"use strict";

/* ------------------------------- État ------------------------------- */
const state = {
  route: { view: "home" },
  subject: "cpp",
  quiz: { tab: "new", phase: "setup", subjectId: "cpp", count: 10, difficulty: "mixte", questions: [], index: 0, answers: [], done: false },
  tools: { tool: "repertoire", subject: "cpp", chapterId: null },
  flash: { index: 0, flipped: false },
  filePickerTarget: null,
};
const history = [];

const $ = (s) => document.querySelector(s);
const $$ = (s) => document.querySelectorAll(s);

/* --------------------------- Stockage local --------------------------- */
const LS_KEY = "bosse_data";
let userData = null;

function seedStore() {
  const fiches = [];
  SUBJECT_IDS.forEach((sid) => SUBJECTS[sid].chapters.forEach((ch) =>
    ch.fiches.forEach((f) => fiches.push({ id: f.id, subjectId: sid, chapterId: ch.id, title: f.title, content: f.content, createdAt: Date.now(), updatedAt: Date.now() }))
  ));
  return { _v: 3, fiches, quizzes: [], files: [], chapters: [], history: [], deletedChapters: [], flashcards: [], mindmaps: {}, llmConfig: { key: "", endpoint: "https://api.openai.com/v1/chat/completions", model: "gpt-4o-mini" }, trash: { fiches: [], quizzes: [], files: [], chapters: [] } };
}
function loadStore() {
  try { userData = JSON.parse(localStorage.getItem(LS_KEY)); } catch (e) { userData = null; }
  if (!userData || !userData._v) { userData = seedStore(); saveStore(); }
  else {
    if (!userData.deletedChapters) userData.deletedChapters = [];
    if (!userData.llmConfig) userData.llmConfig = { key: "", endpoint: "https://api.openai.com/v1/chat/completions", model: "gpt-4o-mini" };
    if (!userData.trash.chapters) userData.trash.chapters = [];
    if (!userData.flashcards) userData.flashcards = [];
    if (!userData.mindmaps) userData.mindmaps = {};
    saveStore();
  }
}
function saveStore() { try { localStorage.setItem(LS_KEY, JSON.stringify(userData)); } catch (e) {} }
function uid() { return Date.now().toString(36) + Math.random().toString(36).slice(2, 7); }

/* IndexedDB pour les blobs PDF */
const idb = (() => {
  let db = null;
  const open = () => new Promise((res, rej) => {
    if (db) return res(db);
    const r = indexedDB.open("bosse_files", 1);
    r.onupgradeneeded = () => r.result.createObjectStore("files");
    r.onsuccess = () => { db = r.result; res(db); };
    r.onerror = () => rej(r.error);
  });
  return {
    put: async (id, blob) => { const d = await open(); return new Promise((res, rej) => { const tx = d.transaction("files", "readwrite"); tx.objectStore("files").put(blob, id); tx.oncomplete = res; tx.onerror = () => rej(tx.error); }); },
    get: async (id) => { const d = await open(); return new Promise((res, rej) => { const rq = d.transaction("files", "readonly").objectStore("files").get(id); rq.onsuccess = () => res(rq.result); rq.onerror = () => rej(rq.error); }); },
    del: async (id) => { const d = await open(); return new Promise((res, rej) => { const tx = d.transaction("files", "readwrite"); tx.objectStore("files").delete(id); tx.oncomplete = res; tx.onerror = () => rej(tx.error); }); },
  };
})();

/* ------------------------------- Utilitaires ------------------------------- */
function el(tag, cls, html) { const n = document.createElement(tag); if (cls) n.className = cls; if (html !== undefined) n.innerHTML = html; return n; }
function toast(msg) { const t = $("#toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(t._t); t._t = setTimeout(() => t.classList.remove("show"), 2200); }
function md(s) {
  return (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\*\*(.+?)\*\*/g, "<b>$1</b>").replace(/\n/g, "<br>").replace(/^- /gm, "• ");
}
function openSheet(html) { $("#sheetContent").innerHTML = '<div class="grab"></div>' + html; $("#modal").classList.add("open"); }
function closeSheet() { $("#modal").classList.remove("open"); }
function shuffle(a) { a = [...a]; for (let i = a.length - 1; i > 0; i--) { const j = Math.floor(Math.random() * (i + 1)); [a[i], a[j]] = [a[j], a[i]]; } return a; }
function subjectProgress(s) { const ch = s.chapters.filter((c) => !userData.deletedChapters.includes(c.id)); if (!ch.length) return 0; return Math.round(ch.reduce((a, c) => a + c.pct, 0) / ch.length); }

/* ------------------------------- Données dérivées ------------------------------- */
function builtinChapters(sid) { return SUBJECTS[sid].chapters.filter((c) => !userData.deletedChapters.includes(c.id)); }
function userChapters(sid) { return userData.chapters.filter((c) => c.subjectId === sid && !userData.deletedChapters.includes(c.id)); }
function allChapters(sid) { return builtinChapters(sid).concat(userChapters(sid)); }
function getChapter(sid, cid) { return allChapters(sid).find((c) => c.id === cid); }
function isBuiltinChapter(sid, cid) { return SUBJECTS[sid].chapters.some((c) => c.id === cid); }
function fichesOf(chapterId) { return userData.fiches.filter((f) => f.chapterId === chapterId); }
function quizzesOf(chapterId) { return userData.quizzes.filter((q) => q.chapterId === chapterId); }
function filesOf(chapterId) { return userData.files.filter((f) => f.chapterId === chapterId); }

/* ------------------------------- Navigation ------------------------------- */
/* PDF locaux déposés dans web/pdf/ (chargés depuis catalog.json) */
let LOCAL_PDFS = [];
async function loadLocalPdfs() {
  try {
    const r = await fetch("pdf/catalog.json", { cache: "no-cache" });
    if (r.ok) LOCAL_PDFS = await r.json();
  } catch (e) { LOCAL_PDFS = []; }
}
function localPdfsOf(chapterId) { return LOCAL_PDFS.filter((p) => p.chapterId === chapterId); }

function navigate(route) {
  history.push(JSON.stringify(state.route));
  state.route = route;
  applyRoute();
  render();
}
function goBack() { const r = history.pop(); if (r) { state.route = JSON.parse(r); applyRoute(); render(); } }
function applyRoute() {
  const r = state.route;
  if (r.view === "quiz") state.quiz.phase = r.phase || "setup";
  if (r.view === "tools") state.tools.chapterId = r.chapterId || null;
}
function tabTo(view) {
  if (view === "quiz") { state.quiz.phase = "setup"; state.quiz.done = false; }
  navigate({ view });
}
$$(".tab").forEach((t) => t.addEventListener("click", () => tabTo(t.dataset.view)));
$("#backBtn").addEventListener("click", goBack);

function render() {
  const r = state.route;
  $$(".tab").forEach((t) => t.classList.toggle("active", t.dataset.view === r.view));
  ["home", "quiz", "stats", "tools", "ia"].forEach((v) => $("#view-" + v).classList.toggle("hidden", v !== r.view));
  $("#backBtn").style.display = history.length ? "grid" : "none";

  const titles = { home: "", quiz: "Quiz", stats: "Progression", tools: "Outils", ia: "Assistant IA" };
  $("#appTitle").textContent = titles[r.view] || "";
  $("#appLogo").style.display = r.view === "home" ? "flex" : "none";

  if (r.view === "home") renderHome();
  else if (r.view === "quiz") renderQuiz();
  else if (r.view === "stats") renderStats();
  else if (r.view === "tools") renderTools();
  else if (r.view === "ia") renderIA();
}

/* ============================= ACCUEIL ============================= */
function renderHome() {
  const grid = $("#subjectsGrid"); grid.innerHTML = "";
  SUBJECT_IDS.forEach((id) => {
    const s = SUBJECTS[id], pct = subjectProgress(s);
    const card = el("div", "subject-card");
    card.style.background = s.gradient;
    card.innerHTML = `<div class="ico">${s.icon}</div><div><div class="name">${s.name}</div><div class="sub">${s.tagline}</div></div>
      <div><div class="bar"><span style="width:${pct}%"></span></div><div class="pct">${pct}% maîtrisé</div></div>`;
    card.addEventListener("click", () => { state.subject = id; state.tools.subject = id; navigate({ view: "tools", chapterId: null }); });
    grid.appendChild(card);
  });

  // stats rapides depuis l'historique
  const h = userData.history;
  $("#statQuiz").textContent = h.length;
  $("#statAvg").textContent = h.length ? Math.round(h.reduce((a, x) => a + x.pct, 0) / h.length) + "%" : "—";
  $("#statStreak").textContent = computeStreak();

  // à faire
  const todo = [];
  SUBJECT_IDS.forEach((id) => allChapters(id).forEach((c) => {
    if (c.tag === "À réviser" || c.tag === "Nouveau chapitre") todo.push({ ...c, subjectId: id });
  }));
  const list = $("#todoList"); list.innerHTML = "";
  if (!todo.length) list.innerHTML = '<div class="card">Rien à faire 🎉</div>';
  todo.slice(0, 5).forEach((t) => list.appendChild(chapterItem(t.subjectId, t)));
}

function computeStreak() {
  const days = new Set(userData.history.map((h) => new Date(h.date).toDateString()));
  let streak = 0, d = new Date();
  if (!days.has(d.toDateString())) d.setDate(d.getDate() - 1);
  while (days.has(d.toDateString())) { streak++; d.setDate(d.getDate() - 1); }
  return streak;
}

function chapterItem(sid, c) {
  const s = SUBJECTS[sid];
  const tag = c.tag || "Dossier";
  const tagCls = tag === "À réviser" ? "reviser" : tag === "Nouveau chapitre" ? "nouveau" : "pdf";
  const icon = tag === "À réviser" ? "🔁" : tag === "Nouveau chapitre" ? "🆕" : tag === "PDF" ? "📄" : "📁";
  const sub = c.chapter ? s.name + " · " + c.chapter : s.name;
  const it = el("div", "list-item", `
    <div class="file-ico">${icon}</div>
    <div class="meta"><div class="title">${c.title}</div><div class="sub">${sub}</div></div>
    <div class="right"><span class="tag ${tagCls}">${tag}</span>${c.days ? `<span class="tag days">⏱️ ${c.days}</span>` : ""}</div>`);
  it.addEventListener("click", () => { state.tools.subject = sid; navigate({ view: "tools", chapterId: c.id }); });
  return it;
}

/* ============================= QUIZ ============================= */
function renderQuiz() {
  const v = $("#view-quiz");
  const tabs = [["new", "📝 Nouveau"], ["history", "🕘 Historique"], ["errors", "❌ Erreurs"]];
  v.innerHTML = `<div class="pills" style="margin-bottom:14px;">` +
    tabs.map(([k, l]) => `<div class="pill ${state.quiz.tab === k ? "active" : ""}" data-qt="${k}">${l}</div>`).join("") + `</div><div id="quizBody"></div>`;
  v.querySelectorAll(".pill[data-qt]").forEach((p) => p.addEventListener("click", () => { state.quiz.tab = p.dataset.qt; renderQuiz(); }));

  const body = $("#quizBody");
  if (state.quiz.tab === "history") renderQuizHistory(body);
  else if (state.quiz.tab === "errors") renderQuizErrors(body);
  else if (state.quiz.phase === "setup") renderQuizSetup(body);
  else if (state.quiz.phase === "play") renderQuizPlay(body);
  else renderQuizResults(body);
}

function renderQuizSetup(body) {
  const q = state.quiz;
  const subjPills = SUBJECT_IDS.map((id) => `<div class="pill ${q.subjectId === id ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  const sizePills = QUIZ_SIZES.map((n) => `<div class="pill ${q.count === n ? "active" : ""}" data-size="${n}">${n}</div>`).join("");
  const diffs = [["mixte", "🎲 Mixte"], ["facile", "🟢 Facile"], ["moyen", "🟡 Moyen"], ["difficile", "🔴 Difficile"]];
  const diffPills = diffs.map(([k, l]) => `<div class="pill ${q.difficulty === k ? "active" : ""}" data-diff="${k}">${l}</div>`).join("");

  body.innerHTML = `
    <div class="card" style="margin-bottom:14px;">
      <h3 style="font-size:15px;font-weight:800;margin-bottom:10px;">1 · Matière</h3>
      <div class="pills">${subjPills}</div>
    </div>
    <div class="card" style="margin-bottom:14px;">
      <h3 style="font-size:15px;font-weight:800;margin-bottom:10px;">2 · Nombre de questions</h3>
      <div class="pills">${sizePills}</div>
    </div>
    <div class="card" style="margin-bottom:14px;">
      <h3 style="font-size:15px;font-weight:800;margin-bottom:10px;">3 · Difficulté</h3>
      <div class="pills">${diffPills}</div>
    </div>
    <button class="btn btn-primary" id="startQuiz">▶️ Commencer le quiz</button>`;

  body.querySelectorAll(".pill[data-subj]").forEach((p) => p.addEventListener("click", () => { q.subjectId = p.dataset.subj; renderQuiz(); }));
  body.querySelectorAll(".pill[data-size]").forEach((p) => p.addEventListener("click", () => { q.count = +p.dataset.size; renderQuiz(); }));
  body.querySelectorAll(".pill[data-diff]").forEach((p) => p.addEventListener("click", () => { q.difficulty = p.dataset.diff; renderQuiz(); }));
  $("#startQuiz").addEventListener("click", () => startQuiz());
}

function startQuiz() {
  const q = state.quiz;
  state.subject = q.subjectId;
  let pool = QUESTION_BANK[q.subjectId] || [];
  if (q.difficulty !== "mixte") { const f = pool.filter((x) => x.difficulty === q.difficulty); if (f.length) pool = f; }
  const qs = [];
  while (qs.length < q.count && pool.length) { qs.push(...shuffle(pool)); }
  q.questions = qs.slice(0, q.count).map((x) => ({ ...x }));
  q.index = 0; q.answers = []; q.done = false; q.phase = "play";
  navigate({ view: "quiz", phase: "play" });
}

function renderQuizPlay(body) {
  const q = state.quiz, s = SUBJECTS[q.subjectId];
  const quiz = q.questions;
  if (!quiz.length) { body.innerHTML = '<div class="card">Aucune question disponible pour ces critères.</div>'; return; }
  const cq = quiz[q.index], total = quiz.length, sel = q.answers[q.index];

  body.innerHTML = `
    <div class="card">
      <div class="quiz-head"><span class="q-number">Question ${q.index + 1} / ${total}</span><span class="q-number">${s.icon} ${s.name}</span></div>
      <div class="progress-track"><span style="width:${(q.index / total) * 100}%"></span></div>
      <div class="question-text">${cq.q}</div>
      <div id="options"></div>
      <div style="display:flex;gap:9px;">
        <button class="btn btn-ghost btn-sm" id="quizPrev" style="flex:1;" ${q.index === 0 ? "disabled" : ""}>←</button>
        <button class="btn btn-primary" id="quizNext" style="flex:2;" ${sel === undefined ? "disabled" : ""}>${q.index + 1 === total ? "Voir les résultats 🎯" : "Suivant →"}</button>
      </div>
    </div>`;

  const opts = $("#options");
  cq.options.forEach((opt, i) => {
    const o = el("div", "option" + (sel === i ? " selected" : ""), `<span class="key">${"ABCD"[i]}</span><span>${opt}</span>`);
    o.addEventListener("click", () => { q.answers[q.index] = i; $$("#options .option").forEach((x, j) => x.classList.toggle("selected", j === i)); $("#quizNext").disabled = false; });
    opts.appendChild(o);
  });
  $("#quizNext").addEventListener("click", () => {
    if (q.index + 1 < total) { q.index++; renderQuiz(); }
    else finishQuiz();
  });
  $("#quizPrev").addEventListener("click", () => { if (q.index > 0) { q.index--; renderQuiz(); } });
}

function finishQuiz() {
  const q = state.quiz;
  q.phase = "results"; q.done = true;
  const correct = q.questions.filter((cq, i) => q.answers[i] === cq.correct).length;
  const pct = q.questions.length ? Math.round((correct / q.questions.length) * 100) : 0;
  userData.history.push({ id: uid(), date: Date.now(), subjectId: q.subjectId, count: q.questions.length, difficulty: q.difficulty, score: correct, pct, answers: q.questions.map((cq, i) => ({ qid: cq.id, q: cq.q, options: cq.options, chosen: q.answers[i], correct: cq.correct, ref: cq.ref })) });
  saveStore();
  navigate({ view: "quiz", phase: "results" });
}

function renderQuizResults(body) {
  const q = state.quiz, s = SUBJECTS[q.subjectId];
  const correct = q.questions.filter((cq, i) => q.answers[i] === cq.correct).length;
  const pct = q.questions.length ? Math.round((correct / q.questions.length) * 100) : 0;

  body.innerHTML = `
    <div class="card score-hero">
      <div class="lbl">Résultat · ${s.name}</div>
      <div class="big" style="color:${pct >= 70 ? "var(--good)" : pct >= 40 ? "var(--warn)" : "var(--bad)"}">${pct}%</div>
      <div class="lbl">${correct} / ${q.questions.length} · ${pct}% de réussite</div>
      <div style="margin-top:14px;display:flex;gap:9px;">
        <button class="btn btn-primary" id="rezRetry" style="flex:1;">🔄 Refaire</button>
        <button class="btn btn-ghost" id="rezSetup" style="flex:1;">⚙️ Régler</button>
      </div>
    </div>
    <div class="section-title">Correction & références</div>
    <div id="resultsList"></div>`;

  const list = $("#resultsList");
  q.questions.forEach((cq, i) => {
    const good = q.answers[i] === cq.correct;
    list.innerHTML += `<div class="card" style="margin-bottom:12px;">
      <div style="display:flex;align-items:center;gap:9px;margin-bottom:9px;">
        <span style="font-size:20px;">${good ? "✅" : "❌"}</span>
        <div style="font-weight:700;font-size:14px;">${i + 1}. ${cq.q}</div>
      </div>` +
      cq.options.map((opt, j) => {
        let cls = j === cq.correct ? " correct" : (j === q.answers[i] ? " wrong" : "");
        return `<div class="option${cls}" style="padding:10px 13px;font-size:13px;"><span class="key">${"ABCD"[j]}</span><span>${opt}</span>${j === cq.correct ? '<span style="margin-left:auto">✔</span>' : ""}${j === q.answers[i] && j !== cq.correct ? '<span style="margin-left:auto">✖</span>' : ""}</div>`;
      }).join("") + refHTML(cq.ref) + `</div>`;
  });
  $("#rezRetry").onclick = () => { q.index = 0; q.answers = []; q.done = false; q.phase = "play"; render(); };
  $("#rezSetup").onclick = () => { q.phase = "setup"; q.done = false; render(); };
  bindPdfLinks(list);
}

function refHTML(ref) {
  if (!ref) return "";
  const links = (ref.links || []).map((l) => `<a class="link-pill" href="${l.url}" target="_blank" rel="noopener">🔗 ${l.label}</a>`).join("");
  return `<div class="ref-box"><div class="ref-head">📚 Référence détaillée</div><div class="ref-body">
    <div class="ref-meta"><span class="chip">📄 Page ${ref.page}</span><span class="chip">📖 ${ref.chapter}</span><span class="chip">🏷️ ${ref.title}</span></div>
    <div style="font-style:italic;color:var(--text-soft);margin-bottom:8px;">« ${ref.text} »</div>
    <div><b>Explication :</b> ${ref.explanation}</div>
    <div class="ref-actions"><span class="link-pill pdf" data-pdf="${ref.pdf || ""}">📄 Ouvrir le PDF</span>${links}</div>
  </div></div>`;
}
function bindPdfLinks(scope) {
  scope.querySelectorAll(".link-pill.pdf[data-pdf]").forEach((a) => a.addEventListener("click", () => openBuiltinPdf(a.dataset.pdf)));
}

function renderQuizHistory(body) {
  const h = userData.history.slice().reverse();
  if (!h.length) { body.innerHTML = '<div class="card">Aucun quiz effectué pour le moment.</div>'; return; }
  body.innerHTML = `<div class="section-title">Historique des quiz (${h.length})</div>` +
    h.map((x) => {
      const s = SUBJECTS[x.subjectId] || { icon: "📘", name: x.subjectId };
      const d = new Date(x.date);
      return `<div class="list-item" data-hid="${x.id}">
        <div class="file-ico">${s.icon}</div>
        <div class="meta"><div class="title">${s.name} — ${x.count} questions</div>
        <div class="sub">${d.toLocaleDateString("fr-FR")} · ${x.difficulty}</div></div>
        <div class="right"><span class="tag ${x.pct >= 70 ? "nouveau" : x.pct >= 40 ? "days" : "reviser"}">${x.pct}%</span></div>
      </div>`;
    }).join("");
  body.querySelectorAll(".list-item[data-hid]").forEach((it) => it.addEventListener("click", () => showHistoryDetail(it.dataset.hid)));
}

function showHistoryDetail(hid) {
  const h = userData.history.find((x) => x.id === hid);
  if (!h) return;
  const s = SUBJECTS[h.subjectId] || { name: h.subjectId };
  let html = `<h3>${s.name} · ${h.count} questions</h3>
    <div class="ref-meta"><span class="chip">${new Date(h.date).toLocaleString("fr-FR")}</span><span class="chip">Score ${h.pct}%</span></div>
    <div class="section-title">Détail des réponses</div>`;
  h.answers.forEach((a, i) => {
    const good = a.chosen === a.correct;
    html += `<div class="card" style="margin-bottom:10px;"><div style="display:flex;gap:8px;margin-bottom:7px;font-weight:700;font-size:13.5px;"><span>${good ? "✅" : "❌"}</span>${i + 1}. ${a.q}</div>
      ${a.options.map((o, j) => `<div class="option${j === a.correct ? " correct" : (j === a.chosen ? " wrong" : "")}" style="padding:9px 12px;font-size:12.5px;"><span class="key">${"ABCD"[j]}</span><span>${o}</span></div>`).join("")}
      ${!good && a.ref ? `<div style="font-size:12.5px;color:var(--text-soft);margin-top:6px;"><b>Explication :</b> ${a.ref.explanation}</div>` : ""}
    </div>`;
  });
  openSheet(html);
}

function renderQuizErrors(body) {
  const errors = [];
  userData.history.forEach((h) => h.answers.forEach((a) => { if (a.chosen !== a.correct) errors.push(a); }));
  if (!errors.length) { body.innerHTML = '<div class="card">Aucune erreur — bravo ! 🎉</div>'; return; }
  body.innerHTML = `<div class="section-title">Erreurs à corriger (${errors.length})</div>
    <p style="color:var(--text-soft);font-size:12.5px;margin:-6px 0 10px;">Chaque erreur est expliquée pour que tu ne la refasses plus.</p>` +
    errors.slice(-30).map((a) => `<div class="card" style="margin-bottom:10px;">
      <div style="font-weight:700;font-size:13.5px;margin-bottom:8px;">❌ ${a.q}</div>
      <div style="font-size:12.5px;margin-bottom:8px;"><b>Ta réponse :</b> ${a.options[a.chosen] ?? "—"}<br/><b>Bonne réponse :</b> <span style="color:var(--good);font-weight:700;">${a.options[a.correct]}</span></div>
      ${a.ref ? `<div style="font-size:12.5px;color:var(--text-soft);"><b>💡 Explication :</b> ${a.ref.explanation}</div>` : ""}
    </div>`).join("");
}

/* ============================= STATS ============================= */
let statsMetric = "maitrise";
const STATS_METRICS = [["maitrise", "🎯 Maîtrise"], ["statut", "📚 Statut des chapitres"], ["quiz", "❓ Résultats quiz"]];

function renderStats() {
  const v = $("#view-stats");
  v.innerHTML = `<div class="pills" id="statsPills" style="margin-bottom:14px;"></div><div id="statsBody"></div>`;
  const pills = $("#statsPills");
  pills.innerHTML = SUBJECT_IDS.map((id) => `<div class="pill ${id === state.subject ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  pills.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { state.subject = p.dataset.subj; renderStats(); }));
  const s = SUBJECTS[state.subject];
  $("#statsBody").innerHTML = `
    <div class="section-title">Spider map</div>
    <div class="card chart-card"><h3>Comparaison des notes</h3><div class="hint">Premier essai · Deuxième essai · Réel · Globale · Globale réel</div>
      <div id="radarWrap" style="display:flex;justify-content:center;"></div><div class="legend" id="radarLegend"></div></div>
    <div class="section-title">Histogramme</div>
    <div class="card chart-card" id="barChart"></div>
    <div class="section-title">Répartition</div>
    <div class="card chart-card" id="pieChart"></div>`;
  drawRadar(s); drawBarChart(s); drawPieChart(s);
}

function drawRadar(s) {
  const wrap = $("#radarWrap"), size = 250, cx = size / 2, cy = size / 2, r = 92, n = s.radar.axes.length;
  const angle = (i) => (-90 + (360 / n) * i) * Math.PI / 180;
  const pt = (i, val) => { const rr = r * (val / 100); return [cx + rr * Math.cos(angle(i)), cy + rr * Math.sin(angle(i))]; };
  let svg = `<svg width="${size}" height="${size}">`;
  for (let lvl = 1; lvl <= 5; lvl++) { svg += `<polygon points="${Array.from({ length: n }, (_, i) => pt(i, lvl * 20).join(",")).join(" ")}" fill="none" stroke="#e5e7f0"/>`; }
  for (let i = 0; i < n; i++) { const p = pt(i, 100); svg += `<line x1="${cx}" y1="${cy}" x2="${p[0]}" y2="${p[1]}" stroke="#eef0f7"/>`;
    const lp = pt(i, 118); svg += `<text x="${lp[0]}" y="${lp[1]}" font-size="10" font-weight="700" fill="#8a90a6" text-anchor="middle" dominant-baseline="middle">${s.radar.axes[i]}</text>`; }
  RADAR_LEGEND.forEach((name) => { const vals = s.radar.series[name]; if (!vals) return;
    svg += `<polygon points="${vals.map((v, i) => pt(i, v).join(",")).join(" ")}" fill="${RADAR_COLORS[name]}" fill-opacity="0.14" stroke="${RADAR_COLORS[name]}" stroke-width="2"/>`;
    vals.forEach((v, i) => { const p = pt(i, v); svg += `<circle cx="${p[0]}" cy="${p[1]}" r="2.5" fill="${RADAR_COLORS[name]}"/>`; }); });
  wrap.innerHTML = svg + "</svg>";
  $("#radarLegend").innerHTML = RADAR_LEGEND.map((name) => `<div class="lg"><span class="swatch dot" style="background:${RADAR_COLORS[name]}"></span>${name}</div>`).join("");
}

function drawBarChart(s) {
  const elc = $("#barChart"), entries = Object.entries(s.bars), max = Math.max(...entries.map(([, v]) => v), 1);
  const color = (v) => v >= 70 ? "#34C759" : v >= 40 ? "#FF9500" : "#FF3B30";
  elc.innerHTML = `<h3>Réussite par chapitre</h3><div class="hint">${s.name}</div>` +
    entries.map(([k, v]) => `<div class="bar-row"><div class="b-lbl">${k}</div><div class="b-track"><div class="b-fill" data-w="${(v / max) * 100}" style="background:${color(v)}"></div></div><div class="b-val">${v}%</div></div>`).join("") +
    `<div class="legend"><div class="lg"><span class="swatch" style="background:#34C759;border-radius:4px;"></span>≥ 70 % maîtrisé</div><div class="lg"><span class="swatch" style="background:#FF9500;border-radius:4px;"></span>40–69 % partiel</div><div class="lg"><span class="swatch" style="background:#FF3B30;border-radius:4px;"></span>&lt; 40 % à revoir</div></div>`;
  requestAnimationFrame(() => setTimeout(() => elc.querySelectorAll(".b-fill").forEach((b) => (b.style.width = b.dataset.w + "%")), 30));
}

function computePie(s, metric) {
  if (metric === "statut") {
    const tags = { "À réviser": 0, "Nouveau chapitre": 0, "PDF / OK": 0 };
    s.chapters.filter((c) => !userData.deletedChapters.includes(c.id)).forEach((c) => {
      if (c.tag === "À réviser") tags["À réviser"]++;
      else if (c.tag === "Nouveau chapitre") tags["Nouveau chapitre"]++;
      else tags["PDF / OK"]++;
    });
    const colors = { "À réviser": "#FF9500", "Nouveau chapitre": "#1C1C1E", "PDF / OK": "#34C759" };
    return Object.entries(tags).filter(([, v]) => v > 0).map(([k, v]) => ({ label: k, value: v, color: colors[k] }));
  }
  if (metric === "quiz") {
    const h = userData.history.filter((x) => x.subjectId === s.id);
    const tot = h.reduce((a, x) => a + x.count, 0);
    const correct = h.reduce((a, x) => a + x.score, 0);
    if (!tot) return [{ label: "Aucun quiz", value: 1, color: "#E5E5EA" }];
    const wrong = tot - correct;
    return [ { label: "Correct", value: correct, color: "#34C759" }, { label: "Erreurs", value: wrong, color: "#FF3B30" } ];
  }
  // maîtrise (défaut)
  const avg = subjectProgress(s);
  return [ { label: "Maîtrisé", value: avg, color: "#34C759" }, { label: "À travailler", value: 100 - avg, color: "#E5E5EA" } ];
}

function drawPieChart(s) {
  const elc = $("#pieChart");
  const pills = STATS_METRICS.map(([k, l]) => `<div class="pill ${statsMetric === k ? "active" : ""}" data-m="${k}">${l}</div>`).join("");
  const segs = computePie(s, statsMetric);
  const total = segs.reduce((a, b) => a + b.value, 0) || 1;
  const R = 60, C = 2 * Math.PI * R;
  let off = 0;
  const arc = segs.map((p) => { const dash = (p.value / total) * C; const o = off; off += dash; return { ...p, dash, off: o }; });

  let svg = `<svg width="170" height="170" viewBox="0 0 170 170">`;
  arc.forEach((p) => {
    svg += `<circle cx="85" cy="85" r="${R}" fill="none" stroke="${p.color}" stroke-width="24" stroke-dasharray="${p.dash} ${C - p.dash}" stroke-dashoffset="${-p.off}" transform="rotate(-90 85 85)"/>`;
  });
  const centerVal = statsMetric === "maitrise" ? segs[0].value + "%" : statsMetric === "quiz" && segs.length === 2 ? (total ? Math.round((segs[0].value / total) * 100) + "%" : "—") : (total || "—");
  svg += `<text x="85" y="88" text-anchor="middle" font-size="24" font-weight="800">${centerVal}</text>
    <text x="85" y="104" text-anchor="middle" font-size="9" fill="#8a90a6">${statsMetric === "quiz" ? "réussite" : statsMetric === "statut" ? "chapitres" : "maîtrisé"}</text></svg>`;

  elc.innerHTML = `<h3>Répartition</h3><div class="hint">Choisis ce que tu veux mettre en avant.</div>
    <div class="pills" style="margin-bottom:12px;">${pills}</div>
    <div class="donut-wrap">${svg}
      <div style="flex:1;">${arc.map((p) => `<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;"><span class="swatch" style="background:${p.color};border-radius:4px;"></span><span style="font-size:12px;font-weight:600;">${p.label}</span><span style="margin-left:auto;font-weight:800;font-size:12.5px;">${p.value}${statsMetric === "maitrise" ? "%" : ""}</span></div>`).join("")}</div>
    </div>`;
  elc.querySelectorAll(".pill[data-m]").forEach((p) => p.addEventListener("click", () => { statsMetric = p.dataset.m; drawPieChart(s); }));
}

/* ============================= OUTILS ============================= */
function renderTools() {
  const v = $("#view-tools");
  const tools = [["repertoire", "📚 Répertoire"], ["anki", "🃏 Cartes"], ["mindmap", "🕸️ Mindmap"], ["brouillon", "✏️ Brouillon"], ["pdf", "📄 PDF"]];
  v.innerHTML = `<div class="pills" style="margin-bottom:12px;">` + tools.map(([k, l]) => `<div class="pill ${state.tools.tool === k ? "active" : ""}" data-tool="${k}">${l}</div>`).join("") + `</div><div id="toolsBody"></div>`;
  v.querySelectorAll(".pill[data-tool]").forEach((p) => p.addEventListener("click", () => { state.tools.tool = p.dataset.tool; state.tools.chapterId = null; renderTools(); }));

  const body = $("#toolsBody");
  if (state.tools.tool === "repertoire" && state.tools.chapterId) renderChapter(body);
  else if (state.tools.tool === "repertoire") renderRepertoire(body);
  else if (state.tools.tool === "anki") renderAnki(body);
  else if (state.tools.tool === "mindmap") renderMindmap(body);
  else if (state.tools.tool === "brouillon") renderBrouillon(body);
  else renderPdfTool(body);
}

function renderRepertoire(body) {
  const sid = state.tools.subject, s = SUBJECTS[sid];
  body.innerHTML = `<div class="pills" id="repSubj" style="margin-bottom:12px;"></div>
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:11px;">
      <span style="font-weight:700;font-size:13.5px;">📁 Dossiers · ${s.name}</span>
      <button class="btn btn-ghost btn-sm" id="btnTrash">🗑️ Corbeille</button>
    </div><div id="repList"></div>
    <button class="btn btn-ghost" id="btnNewChapter" style="width:100%;margin-top:4px;">➕ Nouveau dossier</button>`;

  const sp = $("#repSubj");
  sp.innerHTML = SUBJECT_IDS.map((id) => `<div class="pill ${id === sid ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  sp.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { state.tools.subject = p.dataset.subj; renderTools(); }));

  const list = $("#repList"); list.innerHTML = "";
  allChapters(sid).forEach((c) => list.appendChild(chapterItem(sid, c)));
  if (!allChapters(sid).length) list.innerHTML = '<div class="card">Aucun dossier.</div>';
  $("#btnTrash").onclick = trashSheet;
  $("#btnNewChapter").onclick = newChapterSheet;
}

function renderChapter(body) {
  const sid = state.tools.subject, c = getChapter(sid, state.tools.chapterId);
  if (!c) { state.tools.chapterId = null; renderTools(); return; }
  const fiches = fichesOf(c.id), files = filesOf(c.id), quizzes = quizzesOf(c.id);

  body.innerHTML = `
    <div class="card" style="margin-bottom:14px;">
      <h3 style="font-size:16px;font-weight:800;">${c.title}</h3>
      <div class="sub" style="color:var(--text-soft);font-size:12.5px;margin-top:3px;">${SUBJECTS[sid].name} · ${c.chapter || ""} ${c.days ? "· ⏱️ " + c.days : ""}</div>
      <div style="display:flex;gap:8px;margin-top:12px;">
        <button class="btn btn-primary btn-sm" id="chAddPdf" style="flex:1;">📤 Ajouter un PDF</button>
        <button class="btn btn-ghost btn-sm" id="chDel" title="Supprimer ce cours">🗑️</button>
      </div>
    </div>

    <div class="section-title">📄 Fichiers (${files.length})</div>
    <div id="chFiles">${files.length ? "" : '<div class="card" style="color:var(--text-soft);font-size:13px;">Aucun fichier — ajoute le PDF de ton cours.</div>'}</div>
    ${c.pdf ? `<div class="list-item" id="builtinPdf"><div class="file-ico">📄</div><div class="meta"><div class="title">${c.pdf.name}</div><div class="sub">PDF du cours</div></div><div class="right"><span class="tag pdf">Lire</span></div></div>` : ""}

    <div class="section-title">📝 Fiches de révision (${fiches.length})</div>
    <div id="chFiches"></div>
    <button class="btn btn-ghost btn-sm" id="chNewFiche" style="width:100%;margin-top:2px;">➕ Nouvelle fiche</button>

    <div class="section-title">❓ Quiz du dossier (${quizzes.length})</div>
    <div id="chQuizzes"></div>
    <button class="btn btn-ghost btn-sm" id="chNewQuiz" style="width:100%;margin-top:2px;">➕ Nouveau quiz</button>`;

  const fList = $("#chFiles"); files.forEach((f) => {
    const it = el("div", "list-item", `<div class="file-ico">📄</div><div class="meta"><div class="title">${f.name}</div><div class="sub">${(f.size / 1024).toFixed(0)} Ko</div></div><div class="right"><span class="tag pdf">Lire</span></div>`);
    it.addEventListener("click", () => openUploadedPdf(f));
    const del = el("button", "icon-btn", "🗑️"); del.title = "Supprimer"; del.style.cssText = "margin-left:6px;";
    del.addEventListener("click", (e) => { e.stopPropagation(); confirmTrash("file", f); });
    it.querySelector(".right").appendChild(del);
    fList.appendChild(it);
  });
  // PDF fournis (déposés dans web/pdf/) — lecture dans la même fenêtre
  localPdfsOf(c.id).forEach((lp) => {
    const it = el("div", "list-item", `<div class="file-ico">📄</div><div class="meta"><div class="title">${lp.title}</div><div class="sub">PDF de cours</div></div><div class="right"><span class="tag pdf">Lire</span></div>`);
    it.addEventListener("click", () => openLocalPdf(lp));
    fList.appendChild(it);
  });
  $("#builtinPdf")?.addEventListener("click", () => openBuiltinPdf(c.pdf.name));

  const fl = $("#chFiches"); fiches.forEach((f) => {
    const it = el("div", "list-item", `<div class="file-ico">📝</div><div class="meta"><div class="title">${f.title}</div><div class="sub">Fiche de révision</div></div><div class="right"><span class="tag days">Voir</span></div>`);
    it.addEventListener("click", () => ficheSheet(f));
    fl.appendChild(it);
  });
  const ql = $("#chQuizzes"); quizzes.forEach((z) => {
    const it = el("div", "list-item", `<div class="file-ico">❓</div><div class="meta"><div class="title">${z.title}</div><div class="sub">${z.questions.length} questions</div></div><div class="right"><span class="tag pdf">Ouvrir</span></div>`);
    it.addEventListener("click", () => quizSheet(z));
    ql.appendChild(it);
  });

  $("#chAddPdf").onclick = () => pickFile(sid, c.id);
  $("#chNewFiche").onclick = () => newFicheSheet(sid, c.id);
  $("#chNewQuiz").onclick = () => newQuizSheet(sid, c.id);
  const chDel = $("#chDel");
  if (chDel) chDel.onclick = () => {
    openSheet(`<h3>Supprimer ce cours ?</h3><p style="color:var(--text-soft);font-size:13.5px;margin-bottom:12px;">« ${c.title} » et son contenu seront déplacés vers la corbeille.</p>
      <div class="sheet-btn danger" id="dDelYes">🗑️ Supprimer</div><div class="sheet-btn" id="dDelNo">Annuler</div>`);
    $("#dDelYes").onclick = () => {
      if (isBuiltinChapter(sid, c.id)) {
        if (!userData.deletedChapters.includes(c.id)) userData.deletedChapters.push(c.id);
        userData.trash.chapters.push({ kind: "builtin", id: c.id, subjectId: sid, title: c.title });
      } else {
        userData.chapters = userData.chapters.filter((x) => x.id !== c.id);
        userData.trash.chapters.push({ kind: "user", obj: { ...c }, title: c.title });
      }
      userData.fiches = userData.fiches.filter((f) => f.chapterId !== c.id);
      userData.quizzes = userData.quizzes.filter((q) => q.chapterId !== c.id);
      userData.flashcards = userData.flashcards.filter((f) => f.chapterId !== c.id);
      if (userData.mindmaps[c.id]) delete userData.mindmaps[c.id];
      userData.files.filter((f) => f.chapterId === c.id).forEach((f) => idb.del(f.id));
      userData.files = userData.files.filter((f) => f.chapterId !== c.id);
      saveStore(); closeSheet(); state.tools.chapterId = null; renderTools(); toast("Cours supprimé 🗑️");
    };
    $("#dDelNo").onclick = closeSheet;
  };
}

/* ---------- Fichiers (PDF) ---------- */
function pickFile(sid, chapterId) {
  const inp = document.createElement("input");
  inp.type = "file"; inp.accept = "application/pdf"; inp.multiple = true;
  inp.onchange = async () => {
    for (const file of inp.files) {
      const id = uid();
      try { await idb.put(id, file); } catch (e) { toast("Stockage du fichier impossible"); return; }
      const rec = { id, subjectId: sid, chapterId, name: file.name, size: file.size, createdAt: Date.now() };
      userData.files.push(rec);
      saveStore();
      renderTools();
      toast("📤 PDF ajouté — analyse du texte…");
      try {
        const text = await extractTextFromBlob(file);
        const result = generateFromText(text, sid, chapterId, file.name);
        if (result) {
          applyGeneratedContent(result, sid, chapterId, file.name);
          toast("✨ Résumé + cartes + quiz + mindmap générés !");
        } else {
          toast("PDF ajouté, mais texte trop court pour générer du contenu.");
        }
      } catch (e) {
        console.error(e);
        toast("PDF ajouté (génération impossible sur ce fichier).");
      }
      renderTools();
    }
  };
  inp.click();
}

/* Extrait le texte d'un File/Blob (sans ouvrir le lecteur) */
async function extractTextFromBlob(blob) {
  if (!PDFJS_READY) return "";
  const doc = await pdfjsLib.getDocument({ data: await blob.arrayBuffer() }).promise;
  let text = "";
  const max = Math.min(doc.numPages, 60);
  for (let i = 1; i <= max; i++) {
    const page = await doc.getPage(i);
    const tc = await page.getTextContent();
    text += tc.items.map((it) => ("str" in it ? it.str : "")).join(" ") + "\n";
  }
  return text;
}

/* =========================================================================
   LECTEUR PDF — rendu direct dans la page (pdf.js) + extraction + génération
   ========================================================================= */
let PDFJS_READY = (typeof pdfjsLib !== "undefined");
if (PDFJS_READY) {
  try {
    pdfjsLib.GlobalWorkerOptions.workerSrc = "js/vendor/pdf.worker.min.js";
  } catch (e) {}
}

const PDF = { doc: null, numPages: 0, page: 1, scale: 1.4, title: "", source: null };

async function openUploadedPdf(f) {
  const blob = await idb.get(f.id);
  if (!blob) { toast("Fichier introuvable"); return; }
  await openPdfFromArrayBuffer(await blob.arrayBuffer(), f.name, null, { kind: "file", file: f });
}

async function openLocalPdf(lp) {
  try {
    const res = await fetch("pdf/" + encodeURIComponent(lp.file));
    if (!res.ok) throw new Error("introuvable");
    const buf = await res.arrayBuffer();
    await openPdfFromArrayBuffer(buf, lp.title, "PDF de cours", { kind: "local", lp });
  } catch (e) {
    toast("Impossible de charger ce PDF (fichier manquant ?)");
  }
}

function findBuiltinPdf(name) {
  for (const sid of SUBJECT_IDS) for (const c of SUBJECTS[sid].chapters)
    if (c.pdf && (c.pdf.name === name || (name && c.pdf.name && name.includes(c.chapter)))) return { ...c.pdf, title: c.title, subject: SUBJECTS[sid] };
  return null;
}

async function openBuiltinPdf(name) {
  const p = findBuiltinPdf(name);
  if (p && p.url) {
    openPDFReader(p.name, p.title + " · " + p.subject.name);
    $("#pdfSidebar").classList.add("hidden");
    $("#pdfPageLabel").textContent = "…";
    $("#pdfCanvasWrap").innerHTML = '<div class="pr-loading">Chargement du PDF…</div>';
    // 1) essai direct
    try {
      const res = await fetch(p.url, { mode: "cors" });
      if (res.ok) {
        const buf = await res.arrayBuffer();
        if (isPdfBuffer(buf)) { await openPdfFromArrayBuffer(buf, p.name, p.title + " · " + p.subject.name, { kind: "remote", url: p.url }); return; }
      }
    } catch (e) {}
    // 2) via proxy CORS (allorigins) → rendu direct dans la page
    try {
      const proxyUrl = "https://api.allorigins.win/raw?url=" + encodeURIComponent(p.url);
      const res = await fetch(proxyUrl);
      if (res.ok) {
        const buf = await res.arrayBuffer();
        if (isPdfBuffer(buf)) { await openPdfFromArrayBuffer(buf, p.name, p.title + " · " + p.subject.name, { kind: "remote", url: p.url }); return; }
      }
    } catch (e) {}
    // 3) échec : message clair, jamais de "télécharger/ouvrir"
    $("#pdfCanvasWrap").innerHTML = `<div class="pr-page"><h3>PDF indisponible en ligne</h3><p>Ce PDF distant ne peut pas être affiché directement (accès bloqué par le site source).</p><p style="margin-top:10px;color:#555;">💡 <b>Conseil :</b> télécharge-le puis ajoute-le dans « Outils → Répertoire → Ajouter un PDF » pour le lire et générer fiches/quiz/cartes automatiquement.</p></div>`;
    return;
  }
  const content = p ? p.content : null;
  if (content) {
    // pas de vrai fichier : on affiche le texte dans le lecteur (direct, sans option ouvrir)
    showTextReader(p ? p.name : (name || "Document"), content, p ? p.title : null);
    return;
  }
  toast("Ce document n'est pas disponible dans la beta.");
}

/* Vérifie qu'un buffer ressemble à un PDF (%PDF...) */
function isPdfBuffer(buf) {
  const head = new Uint8Array(buf.slice(0, 8));
  return head[0] === 0x25 && head[1] === 0x50 && head[2] === 0x44 && head[3] === 0x46; // "%PDF"
}

/* ---- Lecteur pdf.js ---- */
async function openPdfFromArrayBuffer(buf, title, subtitle, source) {
  if (!PDFJS_READY) { toast("Lecteur PDF indisponible (vérifie ta connexion)."); return; }
  try {
    const task = pdfjsLib.getDocument({ data: buf });
    const doc = await task.promise;
    PDF.doc = doc;
    PDF.numPages = doc.numPages;
    PDF.page = 1;
    PDF.title = title;
    PDF.source = source;
    openPDFReader(title, subtitle);
    renderPdfSidebar();
    renderPdfPage();
  } catch (e) {
    console.error(e);
    toast("Impossible de lire ce PDF (fichier corrompu ?)");
  }
}

function openPDFReader(title, subtitle) {
  $("#pdfTitle").textContent = title;
  $("#pdfSub").textContent = subtitle || "";
  $("#pdfGen").style.display = (PDF.source && PDF.source.kind === "file") ? "grid" : "none";
  $("#pdfSidebar").classList.remove("hidden");
  $("#pdfReader").classList.remove("hidden");
}

function showTextReader(title, content, subtitle) {
  PDF.doc = null; PDF.numPages = 0; PDF.source = null;
  openPDFReader(title, subtitle || "");
  $("#pdfSidebar").classList.add("hidden");
  $("#pdfPageLabel").textContent = "texte";
  $("#pdfCanvasWrap").innerHTML = `<div class="pr-page">${md(content)}</div>`;
}

function renderPdfSidebar() {
  const sb = $("#pdfSidebar");
  sb.classList.remove("hidden");
  let html = "";
  for (let i = 1; i <= PDF.numPages; i++) {
    html += `<button class="pr-page-btn${i === PDF.page ? " active" : ""}" data-p="${i}">${i}</button>`;
  }
  sb.innerHTML = html;
  sb.querySelectorAll(".pr-page-btn").forEach((b) => b.addEventListener("click", () => {
    PDF.page = +b.dataset.p;
    renderPdfSidebar();
    renderPdfPage();
  }));
}

async function renderPdfPage() {
  const wrap = $("#pdfCanvasWrap");
  if (!PDF.doc) return;
  wrap.innerHTML = "";
  const page = await PDF.doc.getPage(PDF.page);
  const base = page.getViewport({ scale: 1 });
  // largeur utile
  const avail = wrap.clientWidth - 28;
  const scale = Math.max(0.6, Math.min(PDF.scale, avail / base.width));
  const viewport = page.getViewport({ scale });
  const canvas = document.createElement("canvas");
  const dpr = window.devicePixelRatio || 1;
  canvas.width = Math.floor(viewport.width * dpr);
  canvas.height = Math.floor(viewport.height * dpr);
  canvas.style.width = Math.floor(viewport.width) + "px";
  canvas.style.height = Math.floor(viewport.height) + "px";
  wrap.appendChild(canvas);
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  await page.render({ canvasContext: ctx, viewport }).promise;
  $("#pdfPageLabel").textContent = `${PDF.page} / ${PDF.numPages}`;
}

function closePDFReader() {
  PDF.doc = null; PDF.numPages = 0; PDF.page = 1; PDF.source = null;
  $("#pdfReader").classList.add("hidden");
  $("#pdfCanvasWrap").innerHTML = "";
  $("#pdfSidebar").innerHTML = "";
}

$("#pdfBack").addEventListener("click", closePDFReader);
$("#pdfPrev").addEventListener("click", () => { if (PDF.doc && PDF.page > 1) { PDF.page--; renderPdfSidebar(); renderPdfPage(); } });
$("#pdfNext").addEventListener("click", () => { if (PDF.doc && PDF.page < PDF.numPages) { PDF.page++; renderPdfSidebar(); renderPdfPage(); } });
$("#pdfSidebarToggle").addEventListener("click", () => { const s = $("#pdfSidebar"); if (PDF.doc) s.classList.toggle("hidden"); });

/* ---- Extraction du texte + génération automatique ---- */
$("#pdfGen").addEventListener("click", async () => {
  if (!PDF.doc || !PDF.source || PDF.source.kind !== "file") { toast("Génération dispo pour tes PDF ajoutés."); return; }
  const f = PDF.source.file;
  const btn = $("#pdfGen");
  btn.textContent = "⏳";
  try {
    const text = await extractPdfText();
    const result = generateFromText(text, f.subjectId, f.chapterId, f.name);
    if (result) {
      applyGeneratedContent(result, f.subjectId, f.chapterId, f.name);
      toast("Contenu généré ✨ (résumé, cartes, quiz, mindmap)");
    } else {
      toast("Texte trop court pour générer du contenu.");
    }
  } catch (e) {
    console.error(e);
    toast("Erreur pendant la génération.");
  } finally {
    btn.textContent = "✨";
    closePDFReader();
    renderTools();
  }
});

async function extractPdfText() {
  let text = "";
  for (let i = 1; i <= PDF.numPages; i++) {
    const page = await PDF.doc.getPage(i);
    const tc = await page.getTextContent();
    const line = tc.items.map((it) => ("str" in it ? it.str : "")).join(" ");
    text += line + "\n";
  }
  return text;
}

/* Génération heuristique (sans IA externe) : résumé + cartes + quiz + mindmap */
const FR_STOP = new Set("le la les un une des du de et ou où mais donc or ni car est sont etre avoir avec pour dans sur que qui quoi dont ce cette ces son sa ses notre votre leur il elle ils elles nous vous je tu on ne pas plus moins aussi alors comme très tout tous toute toutes autre autres même mêmes être avoir fait faire grand petit deux trois entre après avant".split(" "));

function generateFromText(raw, subjectId, chapterId, fileName) {
  const text = raw.replace(/\s+/g, " ").trim();
  if (text.length < 250) return null;

  const title = (fileName || "Document").replace(/\.pdf$/i, "");

  // Phrases
  let sentences;
  try { sentences = text.split(/(?<=[.!?])\s+/).map((s) => s.trim()).filter((s) => s.length > 25 && s.length < 420); }
  catch (e) { sentences = text.split(/[.!?]\s+/).map((s) => s.trim() + ".").filter((s) => s.length > 25); }

  // Termes fréquents (clés)
  const freq = {};
  text.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").split(/[^a-z0-9+]+/)
    .forEach((w) => { if (w.length >= 3 && !FR_STOP.has(w) && !STOPWORDS.has(w)) freq[w] = (freq[w] || 0) + 1; });
  const topTerms = Object.entries(freq).filter(([, c]) => c >= 2).sort((a, b) => b[1] - a[1]).slice(0, 14).map(([w]) => w);

  // Définitions (flashcards)
  const defRe = /^(.{2,60}?)\s+(?:est|sont|signifie|désigne|représente|correspond(?: à)?|se définit comme|appelle)\s+(.{6,220})/i;
  const flashcards = [];
  for (const s of sentences) {
    const m = s.match(defRe);
    if (m && flashcards.length < 10) {
      const term = m[1].replace(/^(le|la|les|un|une|l'|l’)\s*/i, "").trim();
      if (term.length >= 2) flashcards.push({ front: term, back: m[2].trim().replace(/\.$/, "") });
    }
  }
  if (flashcards.length < 4) {
    for (const t of topTerms) {
      if (flashcards.length >= 10) break;
      if (flashcards.some((f) => f.front === t)) continue;
      const s = sentences.find((x) => x.toLowerCase().includes(t));
      if (s) flashcards.push({ front: t, back: s.slice(0, 200) });
    }
  }

  // Quiz (QCM à partir des définitions)
  const quizQs = [];
  const defs = flashcards.slice(0, 8);
  defs.forEach((d) => {
    if (quizQs.length >= 6) return;
    const others = defs.filter((x) => x !== d).map((x) => x.back);
    if (others.length < 3) return;
    const options = shuffle([d.back, ...shuffle(others).slice(0, 3)]);
    quizQs.push({ q: "Que signifie « " + d.front + " » ?", options, correct: options.indexOf(d.back) });
  });

  // Mindmap (titres / sections détectés)
  const headings = [];
  const lines = raw.split(/\n+/).map((l) => l.trim()).filter((l) => l.length > 2 && l.length < 90);
  for (const l of lines) {
    if (/^\d+(\.\d+)*[\.\)]?\s/.test(l) || /^(chapitre|section|partie|chapter|section|leçon|introduction|conclusion)\b/i.test(l)) {
      headings.push(l.replace(/^\d+(\.\d+)*[\.\)]?\s*/, "").slice(0, 46));
    }
    if (headings.length >= 6) break;
  }
  const mindmapNodes = headings.length ? headings : topTerms.slice(0, 5).map((t) => t[0].toUpperCase() + t.slice(1));

  // Résumé
  const summary = sentences.slice(0, 7).map((s) => "• " + s).join("\n");

  return { title, summary, flashcards, quizQs, mindmap: mindmapNodes };
}

function applyGeneratedContent(result, subjectId, chapterId, fileName) {
  const stamp = Date.now();
  // Résumé
  userData.fiches.push({ id: uid(), subjectId, chapterId, title: "📄 Résumé · " + result.title, content: result.summary, auto: true, source: fileName, createdAt: stamp, updatedAt: stamp });
  // Cartes
  result.flashcards.forEach((f) => userData.flashcards.push({ id: uid(), subjectId, chapterId, front: f.front, back: f.back, auto: true, source: fileName, createdAt: stamp }));
  // Quiz
  if (result.quizQs.length >= 2) {
    userData.quizzes.push({ id: uid(), subjectId, chapterId, title: "❓ Quiz auto · " + result.title, questions: result.quizQs.map((q) => ({ q: q.q, options: q.options, correct: q.correct })), auto: true, source: fileName, createdAt: stamp });
  }
  // Mindmap
  if (result.mindmap.length) {
    userData.mindmaps[chapterId] = { title: "🕸️ " + result.title, nodes: result.mindmap, subjectId, source: fileName, createdAt: stamp };
  }
  saveStore();
}

/* ---------- Fiches de révision (CRUD) ---------- */
function ficheSheet(f) {
  openSheet(`<h3>📝 ${f.title}</h3><div style="font-size:14px;line-height:1.7;white-space:pre-wrap;">${md(f.content)}</div>
    <div class="sheet-btn" id="fEdit">✏️ Modifier</div>
    <div class="sheet-btn danger" id="fDel">🗑️ Supprimer</div>
    <div class="sheet-btn" id="fClose">↩️ Fermer</div>`);
  $("#fEdit").onclick = () => editFicheSheet(f);
  $("#fDel").onclick = () => confirmTrash("fiche", f);
  $("#fClose").onclick = closeSheet;
}

function newFicheSheet(sid, chapterId) {
  openSheet(`<h3>➕ Nouvelle fiche de révision</h3>
    <label>Titre</label><input type="text" id="nfTitle" placeholder="Ex. Les pointeurs" />
    <label>Contenu</label><textarea id="nfContent" placeholder="Écris tes points clés…"></textarea>
    <div style="display:flex;gap:8px;margin-top:14px;"><button class="btn btn-primary" id="nfSave">Enregistrer</button><button class="btn btn-ghost" id="nfCancel">Annuler</button></div>`);
  $("#nfCancel").onclick = closeSheet;
  $("#nfSave").onclick = () => {
    const title = $("#nfTitle").value.trim(), content = $("#nfContent").value.trim();
    if (!title) { toast("Donne un titre"); return; }
    userData.fiches.push({ id: uid(), subjectId: sid, chapterId, title, content, createdAt: Date.now(), updatedAt: Date.now() });
    saveStore(); closeSheet(); renderTools(); toast("Fiche créée ✅");
  };
}

function editFicheSheet(f) {
  openSheet(`<h3>✏️ Modifier la fiche</h3>
    <label>Titre</label><input type="text" id="efTitle" value="${f.title.replace(/"/g, "&quot;")}" />
    <label>Contenu</label><textarea id="efContent">${f.content.replace(/</g, "&lt;")}</textarea>
    <div style="display:flex;gap:8px;margin-top:14px;"><button class="btn btn-primary" id="efSave">Enregistrer</button><button class="btn btn-ghost" id="efCancel">Annuler</button></div>`);
  $("#efCancel").onclick = closeSheet;
  $("#efSave").onclick = () => {
    f.title = $("#efTitle").value.trim() || f.title;
    f.content = $("#efContent").value; f.updatedAt = Date.now();
    saveStore(); closeSheet(); renderTools(); toast("Fiche modifiée ✏️");
  };
}

/* ---------- Quiz personnalisés (CRUD) ---------- */
function newQuizSheet(sid, chapterId) {
  const qs = [{ q: "", options: ["", "", "", ""], correct: 0 }];
  renderQuizEditor(sid, chapterId, null, qs, "➕ Nouveau quiz");
}

function renderQuizEditor(sid, chapterId, existing, qs, title) {
  let html = `<h3>${title}</h3><label>Titre du quiz</label><input type="text" id="qzTitle" value="${existing ? existing.title.replace(/"/g, "&quot;") : ""}" placeholder="Ex. Quiz chapitre 1" /><div id="qzList"></div>
    <button class="btn btn-ghost btn-sm" id="qzAdd" style="width:100%;margin-top:10px;">➕ Ajouter une question</button>
    <div style="display:flex;gap:8px;margin-top:14px;"><button class="btn btn-primary" id="qzSave">Enregistrer</button><button class="btn btn-ghost" id="qzCancel">Annuler</button></div>`;
  openSheet(html);
  const list = $("#qzList");
  function draw() {
    list.innerHTML = qs.map((qq, i) => `<div class="card" style="margin:10px 0;padding:12px;">
      <div style="font-weight:700;font-size:13px;margin-bottom:6px;">Question ${i + 1}</div>
      <input type="text" class="qq" data-i="${i}" placeholder="Énoncé" value="${qq.q.replace(/"/g, "&quot;")}" style="margin-bottom:6px;" />
      ${qq.options.map((o, j) => `<input type="text" class="qo" data-i="${i}" data-j="${j}" placeholder="Réponse ${"ABCD"[j]}" value="${o.replace(/"/g, "&quot;")}" style="margin-bottom:4px;" />`).join("")}
      <label style="margin:6px 0 2px;">Bonne réponse</label>
      <select class="qc" data-i="${i}">${qq.options.map((o, j) => `<option value="${j}" ${qq.correct === j ? "selected" : ""}>${"ABCD"[j]}</option>`).join("")}</select>
    </div>`).join("");
  }
  draw();
  $("#qzAdd").onclick = () => { qs.push({ q: "", options: ["", "", "", ""], correct: 0 }); draw(); };
  $("#qzCancel").onclick = closeSheet;
  $("#qzSave").onclick = () => {
    // relire les champs
    list.querySelectorAll(".qq").forEach((inp) => { qs[+inp.dataset.i].q = inp.value.trim(); });
    list.querySelectorAll(".qo").forEach((inp) => { qs[+inp.dataset.i].options[+inp.dataset.j] = inp.value.trim(); });
    list.querySelectorAll(".qc").forEach((sel) => { qs[+sel.dataset.i].correct = +sel.value; });
    const valid = qs.filter((x) => x.q && x.options.every((o) => o.trim()));
    if (!valid.length) { toast("Ajoute au moins une question complète"); return; }
    const quizTitle = $("#qzTitle").value.trim() || "Quiz sans titre";
    if (existing) { existing.title = quizTitle; existing.questions = valid; }
    else userData.quizzes.push({ id: uid(), subjectId: sid, chapterId, title: quizTitle, questions: valid, createdAt: Date.now() });
    saveStore(); closeSheet(); renderTools(); toast("Quiz enregistré ❓");
  };
}

function quizSheet(z) {
  openSheet(`<h3>❓ ${z.title}</h3><p style="color:var(--text-soft);font-size:13px;margin-bottom:12px;">${z.questions.length} questions</p>
    <div class="sheet-btn" id="zPlay">▶️ Jouer ce quiz</div>
    <div class="sheet-btn" id="zEdit">✏️ Modifier</div>
    <div class="sheet-btn danger" id="zDel">🗑️ Supprimer</div>
    <div class="sheet-btn" id="zClose">↩️ Fermer</div>`);
  $("#zPlay").onclick = () => { closeSheet(); playCustomQuiz(z); };
  $("#zEdit").onclick = () => { closeSheet(); renderQuizEditor(state.tools.subject, z.chapterId, z, z.questions.map((x) => ({ ...x, options: [...x.options] })), "✏️ Modifier le quiz"); };
  $("#zDel").onclick = () => confirmTrash("quiz", z);
  $("#zClose").onclick = closeSheet;
}

function playCustomQuiz(z) {
  const q = state.quiz;
  q.subjectId = state.tools.subject; state.subject = state.tools.subject;
  q.questions = z.questions.map((x, i) => ({ id: "custom-" + i, q: x.q, options: x.options, correct: x.correct, ref: null }));
  q.index = 0; q.answers = []; q.done = false; q.phase = "play"; q.tab = "new";
  navigate({ view: "quiz" });
}

/* ---------- Nouveau dossier ---------- */
function newChapterSheet() {
  openSheet(`<h3>➕ Nouveau dossier</h3><label>Nom du dossier</label><input type="text" id="ncTitle" placeholder="Ex. Chapitre 7" />
    <div style="display:flex;gap:8px;margin-top:14px;"><button class="btn btn-primary" id="ncSave">Créer</button><button class="btn btn-ghost" id="ncCancel">Annuler</button></div>`);
  $("#ncCancel").onclick = closeSheet;
  $("#ncSave").onclick = () => {
    const t = $("#ncTitle").value.trim(); if (!t) { toast("Donne un nom"); return; }
    userData.chapters.push({ id: uid(), subjectId: state.tools.subject, title: t, createdAt: Date.now() });
    saveStore(); closeSheet(); renderTools(); toast("Dossier créé 📁");
  };
}

/* ---------- Corbeille ---------- */
function confirmTrash(kind, obj) {
  openSheet(`<h3>Confirmer la suppression ?</h3><p style="color:var(--text-soft);font-size:13.5px;margin-bottom:12px;">« ${obj.title || obj.name} » sera déplacé vers la corbeille.</p>
    <div class="sheet-btn danger" id="ctYes">🗑️ Mettre à la corbeille</div><div class="sheet-btn" id="ctNo">Annuler</div>`);
  $("#ctYes").onclick = () => {
    const arr = kind === "fiche" ? userData.fiches : kind === "quiz" ? userData.quizzes : userData.files;
    const i = arr.indexOf(obj); if (i >= 0) arr.splice(i, 1);
    userData.trash[kind === "fiche" ? "fiches" : kind === "quiz" ? "quizzes" : "files"].push(obj);
    if (kind === "file") idb.del(obj.id);
    saveStore(); closeSheet(); renderTools(); toast("Déplacé vers la corbeille 🗑️");
  };
  $("#ctNo").onclick = closeSheet;
}

function trashSheet() {
  const t = userData.trash;
  const items = [...t.chapters.map((x) => ({ kind: "chapter", x })), ...t.fiches.map((x) => ({ kind: "fiche", x })), ...t.quizzes.map((x) => ({ kind: "quiz", x })), ...t.files.map((x) => ({ kind: "file", x }))];
  if (!items.length) { openSheet(`<h3>🗑️ Corbeille</h3><p style="color:var(--text-soft);font-size:13.5px;">La corbeille est vide.</p><div class="sheet-btn" id="tClose">↩️ Fermer</div>`); $("#tClose").onclick = closeSheet; return; }
  let html = `<h3>🗑️ Corbeille (${items.length})</h3><p style="color:var(--text-soft);font-size:12px;margin-bottom:8px;">Touche un élément pour le restaurer.</p>`;
  items.forEach((it, i) => html += `<div class="sheet-btn" id="tr${i}">${it.kind === "chapter" ? "📁" : it.kind === "fiche" ? "📝" : it.kind === "quiz" ? "❓" : "📄"} ${it.x.title || it.x.name}</div>`);
  html += `<div class="sheet-btn" id="tClose">↩️ Fermer</div>`;
  openSheet(html);
  items.forEach((it, i) => $("#tr" + i).onclick = () => restoreItem(it.kind, it.x));
  $("#tClose").onclick = closeSheet;
}
function restoreItem(kind, obj) {
  if (kind === "chapter") {
    const i = userData.trash.chapters.indexOf(obj); if (i >= 0) userData.trash.chapters.splice(i, 1);
    if (obj.kind === "builtin") userData.deletedChapters = userData.deletedChapters.filter((id) => id !== obj.id);
    else userData.chapters.push(obj.obj);
    saveStore(); closeSheet(); renderTools(); toast("Cours restauré ✅");
    return;
  }
  const src = kind === "fiche" ? "fiches" : kind === "quiz" ? "quizzes" : "files";
  const i = userData.trash[src].indexOf(obj); if (i >= 0) userData.trash[src].splice(i, 1);
  if (kind === "fiche") userData.fiches.push(obj);
  else if (kind === "quiz") userData.quizzes.push(obj);
  else userData.files.push(obj);
  saveStore(); closeSheet(); renderTools(); toast("Élément restauré ✅");
}

/* ---------- Cartes (Anki) ---------- */
function renderAnki(body) {
  const sid = state.tools.subject, s = SUBJECTS[sid];
  body.innerHTML = `<div class="pills" id="ankSubj" style="margin-bottom:12px;"></div><div id="ankBody"></div>`;
  const sp = $("#ankSubj");
  sp.innerHTML = SUBJECT_IDS.map((id) => `<div class="pill ${id === sid ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  sp.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { state.tools.subject = p.dataset.subj; renderTools(); }));

  const builtin = (FLASHCARDS[sid] || []).map((c) => ({ front: c.front, back: c.back }));
  const generated = userData.flashcards.filter((f) => f.subjectId === sid).map((f) => ({ front: f.front, back: f.back }));
  const cards = [...builtin, ...generated];
  const ab = $("#ankBody");
  if (!cards.length) { ab.innerHTML = '<div class="card">Pas de cartes pour cette matière.<br/><span style="color:var(--text-soft);font-size:12.5px;">Ajoute un PDF : ses cartes seront générées automatiquement.</span></div>'; return; }
  const i = state.flash.index % cards.length, c = cards[i];
  ab.innerHTML = `<div class="flash ${state.flash.flipped ? "flipped" : ""}" id="flashCard"><div class="inner">
      <div class="face front"><span class="mono">${c.front}</span><span class="hint">👆 Touche pour retourner</span></div>
      <div class="face back">${c.back}</div></div></div>
    <div class="review-btns"><button class="rb again" id="rbAgain">🔄 Encore</button><button class="rb hard" id="rbHard">⏳ Difficile</button><button class="rb good" id="rbGood">✅ Facile</button></div>
    <p style="text-align:center;color:var(--text-soft);font-size:12px;margin-top:11px;">Carte ${i + 1} / ${cards.length} · ${s.name}</p>`;
  $("#flashCard").addEventListener("click", () => { state.flash.flipped = !state.flash.flipped; renderTools(); });
  const next = () => { state.flash.index++; state.flash.flipped = false; renderTools(); };
  $("#rbAgain").onclick = () => { toast("Reviendra rapidement 🔁"); next(); };
  $("#rbHard").onclick = () => { toast("Programmée dans 10 min ⏳"); next(); };
  $("#rbGood").onclick = () => { toast("Bien joué ✅"); next(); };
}

/* ---------- Mindmap ---------- */
let mmSel = "__subject__";
function renderMindmap(body) {
  const sid = state.tools.subject, s = SUBJECTS[sid];
  const gens = Object.entries(userData.mindmaps).filter(([, m]) => m.subjectId === sid);
  body.innerHTML = `<div class="pills" id="mmSubj" style="margin-bottom:12px;"></div>
    <div class="pills" id="mmSrc" style="margin-bottom:12px;"></div>
    <div class="card" style="padding:12px;"><h3 style="font-size:14px;font-weight:800;margin:6px 4px 10px;" id="mmTitle">🕸️ Mindmap</h3>
    <div class="mindmap" id="mm"></div><p style="color:var(--text-soft);font-size:11px;margin-top:8px;text-align:center;">Glisse les nœuds pour organiser ta carte.</p></div>`;
  const sp = $("#mmSubj");
  sp.innerHTML = SUBJECT_IDS.map((id) => `<div class="pill ${id === sid ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  sp.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { state.tools.subject = p.dataset.subj; mmSel = "__subject__"; renderTools(); }));

  // Sources : matière + mindmaps générées
  const srcs = [["__subject__", "🗺️ " + s.name], ...gens.map(([cid, m]) => [cid, m.title])];
  if (gens.length && !srcs.some(([k]) => k === mmSel)) mmSel = "__subject__";
  const src = $("#mmSrc");
  src.innerHTML = srcs.map(([k, l]) => `<div class="pill ${mmSel === k ? "active" : ""}" data-src="${k}">${l}</div>`).join("");
  src.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { mmSel = p.dataset.src; renderTools(); }));

  if (mmSel === "__subject__") {
    const nodes = s.chapters.filter((c) => !userData.deletedChapters.includes(c.id)).slice(0, 5).map((c) => ({ t: c.title.split(" ").slice(0, 2).join(" "), ch: c.chapter }));
    $("#mmTitle").textContent = "🕸️ Mindmap — " + s.name;
    drawMindmap(nodes, s);
  } else {
    const m = userData.mindmaps[mmSel];
    $("#mmTitle").textContent = m.title;
    drawMindmap(m.nodes.map((t) => ({ t, ch: "" })), s);
  }
}

function drawMindmap(nodes, s) {
  const c = $("#mm"), W = c.clientWidth || 380, H = 300, cx = W / 2, cy = H / 2, n = nodes.length;
  const pos = nodes.map((_, i) => { const a = (-90 + (360 / n) * i) * Math.PI / 180; return { x: cx + Math.cos(a) * 105, y: cy + Math.sin(a) * 90 }; });
  let svg = `<svg viewBox="0 0 ${W} ${H}">`;
  pos.forEach((p) => svg += `<path d="M${cx} ${cy} Q ${(cx + p.x) / 2} ${(cy + p.y) / 2} ${p.x} ${p.y}" stroke="#c9cde0" stroke-width="2" fill="none"/>`);
  svg += `<g class="mm-node"><circle cx="${cx}" cy="${cy}" r="32" fill="${s.accent}"/><text x="${cx}" y="${cy + 4}" text-anchor="middle" fill="#fff" font-size="15">${s.icon}</text><text x="${cx}" y="${cy + 20}" text-anchor="middle" fill="#fff" font-size="8.5" font-weight="700">${s.name}</text></g>`;
  pos.forEach((p, i) => svg += `<g class="mm-node"><circle cx="${p.x}" cy="${p.y}" r="25" fill="#fff" stroke="${s.accent}" stroke-width="2"/><text x="${p.x}" y="${p.y - 1}" text-anchor="middle" font-size="8.5" font-weight="700" fill="#333">${nodes[i].t}</text><text x="${p.x}" y="${p.y + 11}" text-anchor="middle" font-size="7" fill="#8a90a6">${nodes[i].ch}</text></g>`);
  c.innerHTML = svg + "</svg>";
  c.querySelectorAll(".mm-node").forEach((g) => {
    const circle = g.querySelector("circle"), ox = +circle.getAttribute("cx"), oy = +circle.getAttribute("cy");
    const texts = [...g.querySelectorAll("text")].map((t) => ({ t, dx: +t.getAttribute("x") - ox, dy: +t.getAttribute("y") - oy }));
    let dragging = false;
    g.addEventListener("pointerdown", (e) => { dragging = true; g.setPointerCapture(e.pointerId); });
    g.addEventListener("pointermove", (e) => { if (!dragging) return; const r = c.querySelector("svg").getBoundingClientRect();
      const x = e.clientX - r.left, y = e.clientY - r.top; circle.setAttribute("cx", x); circle.setAttribute("cy", y);
      texts.forEach(({ t, dx, dy }) => { t.setAttribute("x", x + dx); t.setAttribute("y", y + dy); }); });
    g.addEventListener("pointerup", () => { dragging = false; });
  });
}

/* ---------- Brouillon (stylet) ---------- */
function renderBrouillon(body) {
  body.innerHTML = `<div class="card" style="padding:12px;">
    <h3 style="font-size:14px;font-weight:800;margin:6px 4px 10px;">✏️ Brouillon</h3>
    <div class="board-tools">
      <button class="tool active" data-t="pen">🖊️</button>
      <button class="tool" data-t="eraser">🧽</button>
      <button class="tool" data-t="clear">🗑️</button>
      <input type="color" id="boardColor" value="#1e2235" title="Couleur" />
    </div>
    <div class="canvas-wrap"><canvas id="whiteboard"></canvas></div>
    <p style="color:var(--text-soft);font-size:11px;margin-top:8px;">Fonctionne avec le stylet (sensibilité à la pression) et le doigt.</p></div>`;
  initDrawing("#whiteboard", "pen", true);
}

function renderPdfTool(body) {
  const sid = state.tools.subject, s = SUBJECTS[sid];
  const c = s.chapters.filter((x) => !userData.deletedChapters.includes(x.id))[0];
  body.innerHTML = `<div class="pills" id="pdfSubj" style="margin-bottom:12px;"></div>
    <div class="card" style="padding:12px;"><h3 style="font-size:14px;font-weight:800;margin:6px 4px 10px;">📄 PDF interactif — ${s.name}</h3>
    <div class="board-tools"><button class="tool active" data-t="pen">🖊️</button><button class="tool" data-t="highlight">🖍️</button><button class="tool" data-t="eraser">🧽</button><button class="tool" data-t="clear">🗑️</button></div>
    <div class="pdf-frame"><div class="pdf-page"><div class="p-title">${c ? c.title : s.name}</div><div class="p-body">${c && c.pdf ? c.pdf.content : "Ajoute un PDF pour l'annoter ici."}</div><canvas id="pdfCanvas"></canvas></div></div>
    <p style="color:var(--text-soft);font-size:11px;margin-top:8px;">🖍️ Surligne ou écris directement sur le document.</p></div>`;
  const sp = $("#pdfSubj");
  sp.innerHTML = SUBJECT_IDS.map((id) => `<div class="pill ${id === sid ? "active" : ""}" data-subj="${id}">${SUBJECTS[id].icon} ${SUBJECTS[id].name}</div>`).join("");
  sp.querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => { state.tools.subject = p.dataset.subj; renderTools(); }));
  initDrawing("#pdfCanvas", "highlight", false);
}

function initDrawing(canvasSel, defaultTool, white) {
  const cv = document.querySelector(canvasSel);
  if (!cv) return;
  requestAnimationFrame(() => {
    const dpr = window.devicePixelRatio || 1, r = cv.getBoundingClientRect();
    cv.width = Math.max(1, r.width * dpr); cv.height = Math.max(1, r.height * dpr);
    const ctx = cv.getContext("2d"); ctx.scale(dpr, dpr); ctx.lineCap = "round"; ctx.lineJoin = "round";
    if (white) { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, r.width, r.height); }
    let tool = defaultTool, drawing = false, last = null, activePointer = null;

    const tools = cv.closest(".card")?.querySelectorAll(".board-tools .tool") || [];
    tools.forEach((b) => b.addEventListener("click", () => {
      if (b.dataset.t === "clear") { ctx.clearRect(0, 0, r.width, r.height); if (white) { ctx.fillStyle = "#fff"; ctx.fillRect(0, 0, r.width, r.height); } return; }
      tool = b.dataset.t; tools.forEach((x) => x.classList.toggle("active", x === b));
    }));

    const pos = (e) => { const rr = cv.getBoundingClientRect(); return { x: e.clientX - rr.left, y: e.clientY - rr.top }; };
    cv.addEventListener("pointerdown", (e) => { if (activePointer !== null) return; activePointer = e.pointerId; drawing = true; last = pos(e); cv.setPointerCapture(e.pointerId); });
    cv.addEventListener("pointermove", (e) => {
      if (!drawing || e.pointerId !== activePointer) return;
      const p = pos(e), pressure = e.pressure || 0.5;
      ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y);
      if (tool === "pen") {
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 1; ctx.lineWidth = 2.5 + pressure * 5; ctx.strokeStyle = "#1e2235";
      }
      else if (tool === "highlight") {
        // opacité réduite : le texte du PDF reste lisible sous le surlignage
        ctx.globalCompositeOperation = "source-over";
        ctx.globalAlpha = 0.18; ctx.lineWidth = 22; ctx.strokeStyle = "#fbbf24";
      }
      else if (tool === "eraser") {
        // destination-out : efface UNIQUEMENT les annotations, jamais le texte natif du PDF
        ctx.globalCompositeOperation = "destination-out";
        ctx.globalAlpha = 1; ctx.lineWidth = 24; ctx.strokeStyle = "rgba(0,0,0,1)";
      }
      ctx.stroke(); last = p;
    });
    const end = (e) => { if (e.pointerId === activePointer) { drawing = false; activePointer = null; } };
    cv.addEventListener("pointerup", end); cv.addEventListener("pointercancel", end);
  });
}

/* ============================= ASSISTANT IA ============================= */
let aiGreeted = false;
let aiConvo = []; // historique envoyé au LLM

function renderIA() {
  const v = $("#view-ia");
  if (!v.dataset.ready) {
    v.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
        <span style="font-size:12px;color:var(--text-soft);" id="aiStatus"></span>
        <button class="btn btn-ghost btn-sm" id="aiConfig">⚙️ Configurer</button>
      </div>
      <div class="pills" id="aiSuggest" style="margin-bottom:14px;"></div>
      <div class="chat" id="chatLog"></div>
      <div class="chat-input" style="margin-top:14px;"><input id="chatInput" type="text" placeholder="Calcul, culture, cours… tout !" /><button class="send-btn" id="chatSend">➤</button></div>`;
    v.dataset.ready = "1";
    const sugg = [
      ["combien font 15 * 12 ?", "🧮 Calcul"],
      ["Qui a inventé Python ?", "🌍 Culture G"],
      ["explique les pointeurs", "💻 Cours"],
      ["C'est quoi un tableur ?", "📊 Excel"],
    ];
    $("#aiSuggest").innerHTML = sugg.map(([q, l]) => `<div class="pill" data-q="${q.replace(/"/g, "&quot;")}">${l}</div>`).join("");
    $("#aiSuggest").querySelectorAll(".pill").forEach((p) => p.addEventListener("click", () => askAI(p.dataset.q)));
    $("#chatSend").addEventListener("click", sendChat);
    $("#chatInput").addEventListener("keydown", (e) => { if (e.key === "Enter") sendChat(); });
    $("#aiConfig").addEventListener("click", aiConfigSheet);
  }
  $("#aiStatus").textContent = userData.llmConfig.key ? "🟢 IA connectée" : "🟡 Calcul + Wikipédia (gratuit)";
  if (!aiGreeted) { aiGreeted = true; pushMsg("bot", "Salut ! Je suis l'assistant **Boss-e** 🎯. Je peux **calculer**, répondre sur **tes cours**, et chercher des infos sur **Wikipédia**. Pour discuter de tout, branche une vraie IA (⚙️ Configurer)."); }
}

function sendChat() {
  const inp = $("#chatInput"); const t = inp.value.trim();
  if (t) { inp.value = ""; askAI(t); }
}

function pushMsg(role, text) {
  const log = $("#chatLog"); if (!log) return;
  const m = el("div", "msg " + role, linkify(text));
  log.appendChild(m); log.parentElement.scrollTop = log.parentElement.scrollHeight;
  return m;
}
function linkify(text) {
  let out = (text || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  out = out.replace(/\*\*(.+?)\*\*/g, "<b>$1</b>");
  out = out.replace(/(https?:\/\/[^\s<]+)/g, '<a href="$1" target="_blank" rel="noopener" style="color:#1C1C1E;font-weight:700;text-decoration:underline;">$1</a>');
  return out.replace(/\n/g, "<br>");
}

async function askAI(input) {
  const log = $("#chatLog");
  pushMsg("user", input);
  aiConvo.push({ role: "user", content: input });
  const typing = el("div", "msg bot", '<div class="typing"><span></span><span></span><span></span></div>');
  log.appendChild(typing); log.parentElement.scrollTop = log.parentElement.scrollHeight;
  let reply;
  try { reply = await computeAIAnswer(input); }
  catch (err) { reply = ["Oups, une erreur est survenue : " + err.message]; }
  typing.remove();
  reply.forEach((line) => pushMsg("bot", line));
  log.parentElement.scrollTop = log.parentElement.scrollHeight;
}

async function computeAIAnswer(input) {
  const t = norm(input);

  // 1. Calcul (hors ligne)
  const m = tryMath(input);
  if (m !== null) return ["**Résultat :** " + input.trim() + " = **" + m + "**"];

  // 2. Salutations & questions simples
  const small = smallTalk(t);
  if (small) return small;

  // 3. Exercices
  if (/(exercice|exo|entraine|quiz|test)/.test(t)) return makeExercise(t);

  // 4. Connaissance des cours (hors ligne, précise)
  const hit = searchKnowledge(t);
  if (hit) { const out = [hit.text]; if (hit.src) out.push("📄 Source : " + hit.src); return out; }

  // 5. IA réelle (si une clé est configurée)
  if (userData.llmConfig.key) return [await callLLM(input)];

  // 6. Wikipédia (internet, gratuit)
  const w = await wikiLookup(input);
  if (w) return [w.text, "🔗 Source : " + w.url];

  // 7. Vue d'ensemble d'une matière
  const sid = detectSubject(t);
  if (sid) return subjectOverview(sid);

  // 8. Fallback
  return ["Je n'ai rien trouvé de précis sur « " + input.trim() + " ».", "Tu peux me poser un **calcul**, une question sur un **cours**, ou brancher une **vraie IA** (⚙️ Configurer) pour discuter de tout."];
}

function smallTalk(t) {
  if (/(^|[^a-z])(bonjour|salut|coucou|hello|bonsoir|hey)([^a-z]|$)/.test(t))
    return ["Bonjour 👋", "Je peux calculer, répondre sur tes cours et chercher sur Wikipédia. Essaie « combien font 12×8 ? » ou « explique les pointeurs »."];
  if (/merci/.test(t)) return ["Avec plaisir ! 😊"];
  if (/(comment )?(ca|ça) va|comment vas[- ]tu|tu vas bien|ca roule/.test(t)) return ["Je vais très bien, merci ! 😊", "Et toi ? Pose-moi une question, je suis là."];
  if (/qui es[- ]tu|comment tu t.appelles|que sais[- ]tu faire|\baide\b|help/.test(t))
    return ["Je suis **Boss-e**, ton assistant 🎯.", "Je sais **calculer** (1+1, 15×12…), répondre sur **tes cours** (C++, Python, Arduino, Excel, langues) et **chercher sur Wikipédia** pour le reste. Pour discuter de tout, branche une clé IA (⚙️ Configurer)."];
  return null;
}

function tryMath(text) {
  let t = " " + norm(text).toLowerCase() + " ";
  t = t.replace(/\b(combien font|combien fait|combien|que vaut|que font|que fait|ca fait|ça fait|calcule|calculer|calcul|resultat|résultat|donne le resultat|donne)\b/g, " ");
  const rm = t.match(/racine carr[ée]e de\s*(-?\d+(?:[.,]\d+)?)/);
  if (rm) { const n = parseFloat(rm[1].replace(",", ".")); if (isFinite(n) && n >= 0) return Math.round(Math.sqrt(n) * 1e6) / 1e6; }
  t = t.replace(/\bmultipli[ée] par\b/g, "*").replace(/\bdivis[ée] par\b/g, "/").replace(/\bdiviser\b/g, "/")
       .replace(/\bplus\b/g, "+").replace(/\bmoins\b/g, "-").replace(/\bfois\b/g, "*").replace(/\bdivise\b/g, "/");
  t = t.replace(/(-?\d+(?:[.,]\d+)?)\s*au carr[ée]/g, "($1^2)");
  t = t.replace(/(-?\d+(?:[.,]\d+)?)\s*au cube/g, "($1^3)");
  t = t.replace(/(-?\d+(?:[.,]\d+)?)\s*(puissance|\^)\s*(-?\d+(?:[.,]\d+)?)/g, "($1^$3)");
  t = t.replace(/,/g, ".");
  const cleaned = t.replace(/[^0-9+\-*/^(). ]/g, " ").replace(/\s+/g, " ").trim();
  if (!/\d/.test(cleaned) || !/[+\-*/^]/.test(cleaned)) return null;
  if (cleaned.length > 80) return null;
  const val = safeEval(cleaned);
  return (typeof val === "number" && isFinite(val)) ? Math.round(val * 1e6) / 1e6 : null;
}
function safeEval(expr) {
  const e = expr.replace(/\^/g, "**");
  if (/[^0-9+\-*/().\s]/.test(e)) return null;
  try { const v = Function('"use strict"; return (' + e + ');')(); return typeof v === "number" ? v : null; }
  catch (err) { return null; }
}

function cleanQuery(q) {
  let t = q.toLowerCase();
  t = t.replace(/[?.!]+/g, " ").replace(/[,;:]/g, " ");
  t = t.replace(/\b(qui a|qui est|qu'est[- ]ce que|qu'est[- ]ce qu'un|c'est quoi|ca veut dire quoi|que veut dire|que signifie|explique|expliquer|explique[- ]moi|dis[- ]moi|peux[- ]tu|peut[- ]tu|definis|définis|definir|définir|parle[- ]moi de|quand|pourquoi|comment|quel|quelle)\b/g, " ");
  return t.replace(/\s+/g, " ").trim();
}
async function wikiLookup(query) {
  const q = cleanQuery(query) || query.trim();
  try {
    const r = await fetch("https://fr.wikipedia.org/api/rest_v1/page/summary/" + encodeURIComponent(q));
    if (r.ok) {
      const j = await r.json();
      if (j && j.extract) return { text: j.extract, url: (j.content_urls && j.content_urls.desktop && j.content_urls.desktop.page) || ("https://fr.wikipedia.org/wiki/" + encodeURIComponent((j.title || q).replace(/ /g, "_"))) };
    }
  } catch (e) {}
  try {
    const r2 = await fetch("https://fr.wikipedia.org/w/api.php?action=query&list=search&srsearch=" + encodeURIComponent(q) + "&format=json&origin=*&srlimit=3");
    if (r2.ok) {
      const j = await r2.json();
      const hits = (j.query && j.query.search) || [];
      if (hits.length) return await wikiLookup(hits[0].title);
    }
  } catch (e) {}
  return null;
}

async function callLLM(input) {
  const cfg = userData.llmConfig;
  const messages = [
    { role: "system", content: "Tu es Boss-e, un assistant d'apprentissage français. Réponds de façon claire, utile et concise, en français." },
    ...aiConvo.slice(-10),
  ];
  const res = await fetch(cfg.endpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json", "Authorization": "Bearer " + cfg.key },
    body: JSON.stringify({ model: cfg.model, messages, temperature: 0.7 }),
  });
  if (!res.ok) throw new Error("Erreur API (" + res.status + "). Vérifie ta clé ou ton endpoint.");
  const j = await res.json();
  const content = j.choices && j.choices[0] && j.choices[0].message && j.choices[0].message.content;
  if (!content) throw new Error("Réponse vide de l'IA.");
  aiConvo.push({ role: "assistant", content });
  return content;
}

function aiConfigSheet() {
  const cfg = userData.llmConfig;
  openSheet(`<h3>⚙️ Configurer l'IA</h3>
    <p style="color:var(--text-soft);font-size:12.5px;margin-bottom:8px;">Sans clé, Boss-e utilise <b>le calcul</b> + <b>Wikipédia</b> (gratuit, sans compte). Pour discuter de tout avec une vraie IA, colle une clé API OpenAI-compatible (OpenAI, OpenRouter, Mistral…).</p>
    <label>Clé API (optionnelle)</label><input type="password" id="cfgKey" value="${cfg.key}" placeholder="sk-…" />
    <label>Endpoint</label><input type="text" id="cfgEndpoint" value="${cfg.endpoint}" />
    <label>Modèle</label><input type="text" id="cfgModel" value="${cfg.model}" />
    <div style="display:flex;gap:8px;margin-top:14px;"><button class="btn btn-primary" id="cfgSave">Enregistrer</button><button class="btn btn-ghost" id="cfgCancel">Annuler</button></div>`);
  $("#cfgCancel").onclick = closeSheet;
  $("#cfgSave").onclick = () => {
    cfg.key = $("#cfgKey").value.trim();
    cfg.endpoint = $("#cfgEndpoint").value.trim() || cfg.endpoint;
    cfg.model = $("#cfgModel").value.trim() || cfg.model;
    saveStore(); closeSheet(); renderIA(); toast("Configuration IA enregistrée ⚙️");
  };
}

function norm(s) { return (s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, ""); }

const STOPWORDS = new Set(["est", "les", "des", "une", "un", "que", "qui", "pour", "dans", "sur", "avec", "pas", "plus", "comme", "mais", "sont", "quoi", "comment", "cest", "faire", "fait", "peux", "peut", "explique", "expliquer", "donne", "dit", "alors", "donc", "aussi", "entre", "apres", "avant", "etre", "avoir", "question"]);

function detectSubject(t) {
  if (/c\+\+|cpp|pointeur|programmation|vector|template|classe|memoire/.test(t)) return "cpp";
  if (/python|numpy|pandas|\bliste\b|\btuple\b|dictionnaire/.test(t)) return "python";
  if (/excel|tableur|cellule|formule|recherchev|classeur/.test(t)) return "excel";
  if (/arduino|pwm|electronique|led|broche|analogique|serie|loop\(/.test(t)) return "arduino";
  if (/anglais|english|anglaise|british|grammar|conditional|phrasal/.test(t)) return "anglais";
  if (/espagnol|espanol|espagnole|ser |estar|subjonctif|conjug|preterit/.test(t)) return "espagnol";
  return null;
}

function subjectOverview(sid) {
  const s = SUBJECTS[sid];
  return ["Voici **" + s.name + "** (" + s.tagline + ") — contenu disponible :", "📁 " + s.chapters.map((c) => c.title).join(" · "), "Pose-moi une question précise (ex. « explique les pointeurs ») ou demande « fais-moi un exercice »."];
}

function stem(w) { return w.replace(/(?:es|s|x)$/, ""); }
function tokenStems(s) { return s.split(/[^a-z0-9]+/).filter(Boolean).map(stem); }
function searchKnowledge(t) {
  const words = tokenStems(t).filter((w) => w.length > 2 && !STOPWORDS.has(w));
  let best = null, bestScore = 0;
  // questions de la banque
  SUBJECT_IDS.forEach((sid) => (QUESTION_BANK[sid] || []).forEach((qq) => {
    const toks = tokenStems(norm(qq.q + " " + qq.options.join(" ") + " " + (qq.ref ? qq.ref.text + " " + qq.ref.title + " " + qq.ref.explanation : "")));
    let score = 0; words.forEach((w) => { if (toks.includes(w)) score++; });
    if (score > bestScore) { bestScore = score; best = { text: "**" + qq.q + "**\nRéponse : " + qq.options[qq.correct] + "\n" + (qq.ref ? qq.ref.explanation : ""), src: qq.ref ? qq.ref.title + " · " + qq.ref.chapter : null }; }
  }));
  // fiches
  userData.fiches.forEach((f) => {
    const toks = tokenStems(norm(f.title + " " + f.content));
    let score = 0; words.forEach((w) => { if (toks.includes(w)) score++; });
    if (score > bestScore) { bestScore = score; best = { text: "**" + f.title + "**\n" + f.content, src: "Fiche de révision · " + f.title }; }
  });
  return bestScore >= 1 ? best : null;
}

function makeExercise(t) {
  let sid = "cpp";
  if (/arduino|pwm|led|electro/.test(t)) sid = "arduino";
  else if (/python|numpy|liste|tuple/.test(t)) sid = "python";
  else if (/excel|tableur|formule|cellule/.test(t)) sid = "excel";
  else if (/anglais|english|angl/.test(t)) sid = "anglais";
  else if (/espagnol|esp|ser|estar|subjonctif/.test(t)) sid = "espagnol";
  const bank = QUESTION_BANK[sid] || [];
  if (!bank.length) return ["Je n'ai pas d'exercice disponible pour cette matière dans la beta."];
  const q = bank[Math.floor(Math.random() * bank.length)];
  return ["Voici un exercice (" + SUBJECTS[sid].name + ") :", "❓ " + q.q + "\nA. " + q.options[0] + "\nB. " + q.options[1] + "\nC. " + q.options[2] + "\nD. " + q.options[3], "Réponds et je te dis si c'est juste ! (La bonne réponse est dans la source ci-dessous 👇)", "📄 Source : " + (q.ref ? q.ref.title : "Question du cours")];
}

/* ============================= Divers ============================= */
$("#helpPill").addEventListener("click", () => tabTo("ia"));
$("#btnBell").addEventListener("click", () => toast("3 rappels de révision 🔔"));
$("#globalSearch").addEventListener("input", (e) => {
  const q = e.target.value.toLowerCase().trim();
  if (!q) { renderHome(); return; }
  const grid = $("#subjectsGrid"); grid.innerHTML = "";
  const todo = $("#todoList"); todo.innerHTML = '<div class="section-title">Résultats</div>';
  let found = 0;
  const addResult = (icon, title, sub, onclick) => {
    const it = el("div", "list-item", `<div class="file-ico">${icon}</div><div class="meta"><div class="title">${title}</div><div class="sub">${sub}</div></div>`);
    it.addEventListener("click", onclick); todo.appendChild(it); found++;
  };
  const match = (s) => s && s.toLowerCase().includes(q);

  // 1. Matières
  SUBJECT_IDS.forEach((sid) => {
    const s = SUBJECTS[sid];
    if (match(s.name) || match(s.tagline))
      addResult(s.icon, s.name, s.tagline, () => { state.subject = sid; state.tools.subject = sid; navigate({ view: "tools", chapterId: null }); });
  });
  // 2. Chapitres / dossiers (par défaut + créés)
  SUBJECT_IDS.forEach((sid) => {
    const s = SUBJECTS[sid];
    allChapters(sid).forEach((c) => {
      if (match(c.title) || match(c.chapter)) addResult("📁", c.title, s.name + (c.chapter ? " · " + c.chapter : ""), () => { state.tools.subject = sid; navigate({ view: "tools", chapterId: c.id }); });
    });
  });
  // 3. Fiches de révision
  userData.fiches.forEach((f) => {
    const s = SUBJECTS[f.subjectId] || { name: "" };
    if (match(f.title) || match(f.content)) addResult("📝", f.title, "Fiche · " + s.name, () => { state.tools.subject = f.subjectId; navigate({ view: "tools", chapterId: f.chapterId }); });
  });
  // 4. Quiz créés
  userData.quizzes.forEach((z) => {
    if (match(z.title)) addResult("❓", z.title, "Quiz · " + z.questions.length + " questions", () => { state.tools.subject = z.subjectId; navigate({ view: "tools", chapterId: z.chapterId }); });
  });
  // 5. Fichiers uploadés
  userData.files.forEach((f) => {
    if (match(f.name)) addResult("📄", f.name, "Fichier PDF", () => { state.tools.subject = f.subjectId; navigate({ view: "tools", chapterId: f.chapterId }); });
  });
  // 6. Cartes de mémorisation
  SUBJECT_IDS.forEach((sid) => {
    (FLASHCARDS[sid] || []).forEach((c) => { if (match(c.front) || match(c.back)) addResult("🃏", c.front, "Carte · " + SUBJECTS[sid].name, () => { state.tools.subject = sid; state.tools.tool = "anki"; navigate({ view: "tools" }); }); });
  });
  // 7. Questions de la banque
  SUBJECT_IDS.forEach((sid) => {
    (QUESTION_BANK[sid] || []).forEach((qq) => { if (match(qq.q)) addResult("❔", qq.q, "Question · " + SUBJECTS[sid].name, () => { tabTo("quiz"); }); });
  });

  if (!found) todo.innerHTML = '<div class="card">Aucun résultat pour « ' + e.target.value + ' ».<br/><span style="color:var(--text-soft);font-size:12.5px;">Astuce : essaie un mot-clé comme « pointeur », « fonction », « formule »…</span></div>';
});

/* ------------------------------ Démarrage ------------------------------ */
loadStore();
loadLocalPdfs().then(() => { render(); });
