(() => {
  "use strict";

  const state = {
    token: localStorage.getItem("token") || null,
    refreshToken: localStorage.getItem("refreshToken") || null,
    email: localStorage.getItem("email") || null,
    authMode: "login", // "login" | "register"
    txnOffset: 0,
    txnLimit: 10,
    txnCategory: "",
  };

  // ---------------------------------------------------------------------
  // API helper
  // ---------------------------------------------------------------------

  function storeTokens(accessToken, refreshToken) {
    state.token = accessToken;
    state.refreshToken = refreshToken;
    localStorage.setItem("token", accessToken);
    localStorage.setItem("refreshToken", refreshToken);
  }

  // Access tokens are short-lived (60 min by default) so a demo session
  // shouldn't die mid-conversation - on a 401, try the refresh token once
  // before giving up and surfacing an error.
  async function tryRefreshToken() {
    if (!state.refreshToken) return false;
    try {
      const resp = await fetch("/auth/refresh", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: state.refreshToken }),
      });
      if (!resp.ok) return false;
      const data = await resp.json();
      storeTokens(data.access_token, data.refresh_token);
      return true;
    } catch {
      return false;
    }
  }

  async function rawFetch(path, options) {
    const headers = { ...(options.headers || {}) };
    if (state.token) headers["Authorization"] = "Bearer " + state.token;
    const resp = await fetch(path, { ...options, headers });
    let body = null;
    try {
      body = await resp.json();
    } catch {
      /* no JSON body (e.g. 204) */
    }
    return { resp, body };
  }

  async function apiFetch(path, options = {}, _isRetry = false) {
    let { resp, body } = await rawFetch(path, options);

    if (resp.status === 401 && !_isRetry && path !== "/auth/refresh") {
      if (await tryRefreshToken()) {
        return apiFetch(path, options, true);
      }
      logout();
    }

    if (!resp.ok) {
      const detail = body && body.detail ? body.detail : `Request failed (${resp.status})`;
      throw new Error(typeof detail === "string" ? detail : JSON.stringify(detail));
    }
    return body;
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function fmtMoney(amount, currency) {
    const n = Number(amount);
    return `${n.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} ${currency}`;
  }

  // ---------------------------------------------------------------------
  // Auth
  // ---------------------------------------------------------------------

  const authScreen = document.getElementById("auth-screen");
  const appScreen = document.getElementById("app-screen");
  const authForm = document.getElementById("auth-form");
  const authSubmit = document.getElementById("auth-submit");
  const authError = document.getElementById("auth-error");
  const authToggleBtn = document.getElementById("auth-toggle-btn");
  const authModeText = document.getElementById("auth-mode-text");

  function setAuthMode(mode) {
    state.authMode = mode;
    if (mode === "register") {
      authSubmit.textContent = "Create account";
      authModeText.textContent = "Already have an account?";
      authToggleBtn.textContent = "Log in instead";
    } else {
      authSubmit.textContent = "Log in";
      authModeText.textContent = "New here?";
      authToggleBtn.textContent = "Create an account instead";
    }
    authError.classList.add("hidden");
  }

  authToggleBtn.addEventListener("click", () => {
    setAuthMode(state.authMode === "login" ? "register" : "login");
  });

  authForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    authError.classList.add("hidden");
    authSubmit.disabled = true;

    const email = document.getElementById("auth-email").value.trim();
    const password = document.getElementById("auth-password").value;
    const endpoint = state.authMode === "register" ? "/auth/register" : "/auth/login";

    try {
      const result = await apiFetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      storeTokens(result.access_token, result.refresh_token);
      state.email = email;
      localStorage.setItem("email", state.email);
      enterApp();
    } catch (err) {
      authError.textContent = err.message;
      authError.classList.remove("hidden");
    } finally {
      authSubmit.disabled = false;
    }
  });

  function logout() {
    state.token = null;
    state.refreshToken = null;
    localStorage.removeItem("token");
    localStorage.removeItem("refreshToken");
    localStorage.removeItem("email");
    resetChat();
    appScreen.classList.add("hidden");
    authScreen.classList.remove("hidden");
  }

  document.getElementById("logout-btn").addEventListener("click", logout);

  function enterApp() {
    document.getElementById("user-email").textContent = state.email || "";
    authScreen.classList.add("hidden");
    appScreen.classList.remove("hidden");
    loadTransactions();
  }

  // ---------------------------------------------------------------------
  // Tabs
  // ---------------------------------------------------------------------

  document.querySelectorAll(".nav-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".nav-btn").forEach((b) => b.classList.remove("active"));
      document.querySelectorAll(".tab-panel").forEach((p) => p.classList.remove("active"));
      btn.classList.add("active");
      document.getElementById("tab-" + btn.dataset.tab).classList.add("active");
    });
  });

  // ---------------------------------------------------------------------
  // Chat
  // ---------------------------------------------------------------------

  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const chatEmptyStateHtml = document.getElementById("chat-empty-state").outerHTML;

  function clearEmptyState() {
    const emptyState = document.getElementById("chat-empty-state");
    if (emptyState) emptyState.remove();
  }

  function resetChat() {
    chatMessages.innerHTML = chatEmptyStateHtml;
  }

  function addUserBubble(text) {
    clearEmptyState();
    const row = document.createElement("div");
    row.className = "msg-row user";
    row.innerHTML = `<div class="bubble">${escapeHtml(text)}</div><div class="avatar avatar-user">${escapeHtml((state.email || "?")[0].toUpperCase())}</div>`;
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function addThinkingBubble() {
    const row = document.createElement("div");
    row.className = "msg-row assistant";
    row.innerHTML = `<div class="avatar avatar-assistant">&#9670;</div><div class="bubble thinking">Thinking <span class="typing-dots"><span></span><span></span><span></span></span></div>`;
    chatMessages.appendChild(row);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return row;
  }

  function renderAnswerBody(answer) {
    if (answer.transactions) {
      const rows = answer.transactions
        .map(
          (t) =>
            `<tr><td>${escapeHtml(t.date)}</td><td>${escapeHtml(t.merchant)}</td><td>${escapeHtml(t.category)}</td><td class="num">${fmtMoney(t.amount, t.currency)}</td></tr>`
        )
        .join("");
      return `<table class="mini-table"><thead><tr><th>Date</th><th>Merchant</th><th>Category</th><th class="num">Amount</th></tr></thead><tbody>${rows}</tbody></table>`;
    }

    if (answer.totals) {
      const rows = answer.totals
        .map((t) => `<div class="answer-stat"><span class="amount">${fmtMoney(t.total, t.currency)}</span><span class="label">total</span></div>`)
        .join("");
      return rows;
    }

    if (answer.categories) {
      return `<div class="answer-meta">${answer.categories.map((c) => `<span class="tag">${escapeHtml(c)}</span>`).join("")}</div>`;
    }

    if (answer.reason) {
      return escapeHtml(answer.reason);
    }

    if (typeof answer.percentage === "number") {
      const pct = Math.min(100, Math.max(0, answer.percentage));
      return `
        <div class="answer-stat"><span class="amount">${answer.percentage}%</span><span class="label">of total spending on ${escapeHtml(answer.category)}</span></div>
        <div class="percentage-bar"><div style="width:${pct}%"></div></div>
        <div class="answer-meta">
          <span class="tag">${fmtMoney(answer.category_total, answer.currency)} / ${fmtMoney(answer.overall_total, answer.currency)}</span>
        </div>`;
    }

    if (answer.sources !== undefined && answer.answer !== undefined) {
      return escapeHtml(answer.answer);
    }

    if (answer.total !== undefined && answer.category !== undefined) {
      return `<div class="answer-stat">
        <span class="amount">${fmtMoney(answer.total, answer.currency)}</span>
        <span class="label">on ${escapeHtml(answer.category)} &middot; ${answer.transaction_count} transaction${answer.transaction_count === 1 ? "" : "s"}</span>
      </div>`;
    }

    return `<pre>${escapeHtml(JSON.stringify(answer, null, 2))}</pre>`;
  }

  function replaceWithAnswer(row, body) {
    const isRefusal = body.answer && body.answer.reason !== undefined;
    const bubbleClass = isRefusal ? "bubble refusal" : "bubble";

    let meta = "";
    if (body.tool_calls && body.tool_calls.length) {
      meta += body.tool_calls.map((t) => `<span class="tag">${escapeHtml(t)}</span>`).join("");
    }
    if (body.sources && body.sources.length) {
      meta += body.sources.map((s) => `<span class="tag source">&#128196; ${escapeHtml(s)}</span>`).join("");
    }
    if (body.usage) {
      meta += `<span class="tag usage">${body.usage.total_tokens} tokens</span>`;
    }

    row.innerHTML = `
      <div class="avatar avatar-assistant">&#9670;</div>
      <div class="${bubbleClass}">
        ${renderAnswerBody(body.answer)}
        ${meta ? `<div class="answer-meta">${meta}</div>` : ""}
      </div>`;
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function replaceWithError(row, message) {
    row.innerHTML = `<div class="avatar avatar-assistant">&#9670;</div><div class="bubble error">${escapeHtml(message)}</div>`;
  }

  chatMessages.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    chatInput.value = chip.dataset.question;
    chatForm.requestSubmit();
  });

  chatForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const text = chatInput.value.trim();
    if (!text) return;

    addUserBubble(text);
    chatInput.value = "";
    const thinkingRow = addThinkingBubble();

    try {
      const body = await apiFetch("/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text }),
      });
      replaceWithAnswer(thinkingRow, body);
    } catch (err) {
      replaceWithError(thinkingRow, err.message);
    }
  });

  // ---------------------------------------------------------------------
  // Transactions
  // ---------------------------------------------------------------------

  const txnBody = document.getElementById("transactions-body");
  const pageInfo = document.getElementById("page-info");
  const categoryFilter = document.getElementById("category-filter");

  async function loadTransactions() {
    const params = new URLSearchParams({ limit: state.txnLimit, offset: state.txnOffset });
    if (state.txnCategory) params.set("category", state.txnCategory);

    try {
      const page = await apiFetch("/transactions?" + params.toString());
      txnBody.innerHTML = page.transactions
        .map(
          (t) =>
            `<tr><td>${escapeHtml(t.date)}</td><td>${escapeHtml(t.merchant)}</td><td>${escapeHtml(t.category)}</td><td class="num">${fmtMoney(t.amount, t.currency)}</td></tr>`
        )
        .join("") || `<tr><td colspan="4" style="color:var(--text-faint)">No transactions.</td></tr>`;

      const shown = page.transactions.length;
      const from = page.total === 0 ? 0 : page.offset + 1;
      const to = page.offset + shown;
      pageInfo.textContent = `${from}-${to} of ${page.total}`;

      document.getElementById("prev-page").disabled = page.offset === 0;
      document.getElementById("next-page").disabled = to >= page.total;
    } catch (err) {
      txnBody.innerHTML = `<tr><td colspan="4" style="color:var(--danger)">${escapeHtml(err.message)}</td></tr>`;
    }
  }

  document.getElementById("prev-page").addEventListener("click", () => {
    state.txnOffset = Math.max(0, state.txnOffset - state.txnLimit);
    loadTransactions();
  });
  document.getElementById("next-page").addEventListener("click", () => {
    state.txnOffset += state.txnLimit;
    loadTransactions();
  });

  let categoryDebounce;
  categoryFilter.addEventListener("input", () => {
    clearTimeout(categoryDebounce);
    categoryDebounce = setTimeout(() => {
      state.txnCategory = categoryFilter.value.trim();
      state.txnOffset = 0;
      loadTransactions();
    }, 400);
  });

  const importResult = document.getElementById("import-result");
  document.getElementById("csv-input").addEventListener("change", async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append("file", file);

    importResult.className = "banner hidden";
    try {
      const result = await apiFetch("/transactions/import", { method: "POST", body: formData });
      const errorList = result.errors.length
        ? `<ul>${result.errors.map((x) => `<li>${escapeHtml(x)}</li>`).join("")}</ul>`
        : "";
      importResult.className = `banner ${result.skipped ? "banner-warn" : "banner-success"}`;
      importResult.innerHTML = `Imported ${result.imported}, skipped ${result.skipped}.${errorList}`;
      state.txnOffset = 0;
      loadTransactions();
    } catch (err) {
      importResult.className = "banner banner-error";
      importResult.textContent = err.message;
    }
    e.target.value = "";
  });

  // ---------------------------------------------------------------------
  // Documents
  // ---------------------------------------------------------------------

  const docResult = document.getElementById("doc-result");
  const docInput = document.getElementById("doc-input");
  const dropzone = document.getElementById("doc-dropzone");

  async function uploadDocument(file) {
    if (!file) return;
    const formData = new FormData();
    formData.append("file", file);

    docResult.className = "banner hidden";
    try {
      const result = await apiFetch("/documents", { method: "POST", body: formData });
      docResult.className = "banner banner-success";
      docResult.textContent = `Stored "${result.source}" as ${result.chunks_stored} chunk${result.chunks_stored === 1 ? "" : "s"}. Try asking about it in Chat.`;
    } catch (err) {
      docResult.className = "banner banner-error";
      docResult.textContent = err.message;
    }
  }

  docInput.addEventListener("change", (e) => uploadDocument(e.target.files[0]));

  ["dragenter", "dragover"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.add("dragover");
    })
  );
  ["dragleave", "drop"].forEach((evt) =>
    dropzone.addEventListener(evt, (e) => {
      e.preventDefault();
      dropzone.classList.remove("dragover");
    })
  );
  dropzone.addEventListener("drop", (e) => {
    const file = e.dataTransfer.files[0];
    uploadDocument(file);
  });

  // ---------------------------------------------------------------------
  // Theme
  // ---------------------------------------------------------------------

  const themeToggleBtn = document.getElementById("theme-toggle-btn");

  function currentTheme() {
    return (
      document.documentElement.getAttribute("data-theme") ||
      (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")
    );
  }

  function applyTheme(theme) {
    document.documentElement.setAttribute("data-theme", theme);
    themeToggleBtn.innerHTML =
      theme === "dark"
        ? '<span class="nav-icon">&#9680;</span> Light mode'
        : '<span class="nav-icon">&#9680;</span> Dark mode';
  }

  themeToggleBtn.addEventListener("click", () => {
    const next = currentTheme() === "dark" ? "light" : "dark";
    localStorage.setItem("theme", next);
    applyTheme(next);
  });

  const savedTheme = localStorage.getItem("theme");
  applyTheme(savedTheme || currentTheme());

  // ---------------------------------------------------------------------
  // Boot
  // ---------------------------------------------------------------------

  if (state.token) {
    enterApp();
  } else {
    setAuthMode("login");
  }
})();
