const state = {
  apiBase: localStorage.getItem("mule_api_base") || window.location.origin,
  apiKey: localStorage.getItem("mule_api_key") || "",
};

const byId = (id) => document.getElementById(id);

function pretty(obj) {
  return JSON.stringify(obj, null, 2);
}

function setOutput(id, value) {
  const el = byId(id);
  el.classList.remove("skeleton");
  el.textContent = typeof value === "string" ? value : pretty(value);
}

function prefersReducedMotion() {
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches;
}

function setLoading(id, message) {
  const el = byId(id);
  el.classList.add("skeleton");
  el.textContent = message;
}

function wirePanelReveal() {
  if (prefersReducedMotion()) {
    document.querySelectorAll(".panel").forEach((panel) => panel.classList.add("is-visible"));
    return;
  }

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.1, rootMargin: "0px 0px -40px 0px" }
  );

  document.querySelectorAll("[data-reveal]").forEach((panel) => observer.observe(panel));
}

function wireButtonGlow() {
  if (prefersReducedMotion()) {
    return;
  }

  document.querySelectorAll(".btn").forEach((btn) => {
    btn.addEventListener("mousemove", (event) => {
      const rect = btn.getBoundingClientRect();
      const x = ((event.clientX - rect.left) / rect.width) * 100;
      const y = ((event.clientY - rect.top) / rect.height) * 100;
      btn.style.setProperty("--mx", `${x}%`);
      btn.style.setProperty("--my", `${y}%`);
    });
  });
}

function animateTextValue(id, nextText) {
  const el = byId(id);
  if (prefersReducedMotion()) {
    el.textContent = nextText;
    return;
  }

  el.animate(
    [{ transform: "translateY(4px)", opacity: 0.4 }, { transform: "translateY(0)", opacity: 1 }],
    { duration: 260, easing: "cubic-bezier(0.2, 0.8, 0.2, 1)" }
  );
  el.textContent = nextText;
}

async function refreshLiveStatus() {
  const dot = byId("liveDot");
  const text = byId("liveText");
  try {
    await api("/health/live");
    dot.classList.remove("is-down");
    dot.classList.add("is-live");
    text.textContent = "Live";
  } catch {
    dot.classList.remove("is-live");
    dot.classList.add("is-down");
    text.textContent = "Unavailable";
  }
}

async function api(path, options = {}) {
  const url = `${state.apiBase}${path}`;
  const authHeader = state.apiKey ? { "x-api-key": state.apiKey } : {};
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...authHeader, ...(options.headers || {}) },
    ...options,
  });

  let body;
  try {
    body = await response.json();
  } catch {
    body = { message: await response.text() };
  }

  if (!response.ok) {
    throw new Error(pretty({ status: response.status, body }));
  }

  return body;
}

function initializeApiBase() {
  const baseInput = byId("apiBase");
  const keyInput = byId("apiKey");
  baseInput.value = state.apiBase;
  keyInput.value = state.apiKey;

  byId("saveApiBase").addEventListener("click", () => {
    state.apiBase = baseInput.value.trim() || window.location.origin;
    state.apiKey = keyInput.value.trim();
    localStorage.setItem("mule_api_base", state.apiBase);
    localStorage.setItem("mule_api_key", state.apiKey);
  });
}

async function refreshStats() {
  setLoading("statsRaw", "Loading stats...");
  try {
    const stats = await api("/v1/stats");
    const obs = stats.observability || {};

    animateTextValue("mRequests", String(obs.requests_total ?? "-"));
    animateTextValue("mErrors", String(obs.errors_total ?? "-"));
    animateTextValue("mLatAvg", `${obs.latency_ms_avg ?? "-"} ms`);
    animateTextValue("mLatP95", `${obs.latency_ms_p95 ?? "-"} ms`);
    animateTextValue("mFraud", obs.fraud_rate != null ? `${(obs.fraud_rate * 100).toFixed(2)}%` : "-");

    setOutput("statsRaw", stats);
  } catch (err) {
    setOutput("statsRaw", String(err));
  }
}

function wireDemo() {
  document.querySelectorAll("[data-scenario]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      try {
        const scenario = btn.getAttribute("data-scenario");
        const result = await api(`/v1/demo/run/${scenario}`, { method: "POST" });
        setOutput("demoOutput", result);
        refreshStats();
      } catch (err) {
        setOutput("demoOutput", String(err));
      }
    });
  });
}

function buildPayload(form) {
  const channel = form.channel.value;
  const amount = Number(form.amount.value);
  const lat = Number(form.lat.value);
  const lon = Number(form.lon.value);
  const now = new Date().toISOString();

  if (channel === "MOBILE") {
    return {
      channel,
      raw_event: {
        user_id: form.userId.value,
        transfer_to_wallet: form.destination.value,
        transfer_amount: amount,
        transfer_time: now,
        location: { latitude: lat, longitude: lon, country: "IN" },
      },
    };
  }

  if (channel === "WEB") {
    return {
      channel,
      raw_event: {
        user_id: form.userId.value,
        beneficiary_account: form.destination.value,
        transfer_amount: amount,
        transfer_time: now,
        location: { latitude: lat, longitude: lon, country: "IN" },
      },
    };
  }

  if (channel === "ATM") {
    return {
      channel,
      raw_event: {
        terminal_id: form.userId.value,
        withdrawal_amount: amount,
        withdrawal_time: now,
        location: { latitude: lat, longitude: lon, country: "IN" },
      },
    };
  }

  return {
    channel: "UPI",
    raw_event: {
      upi_id: form.userId.value,
      recipient_upi: form.destination.value,
      txn_amount: amount,
      txn_ref_id: `UPI_${Date.now()}`,
      timestamp: now,
    },
  };
}

function wireTransactionForm() {
  const form = byId("txnForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = buildPayload(form);
      const result = await api("/v1/transactions/process", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setOutput("txnOutput", result);
      refreshStats();
    } catch (err) {
      setOutput("txnOutput", String(err));
    }
  });
}

async function refreshStream() {
  setLoading("streamOutput", "Fetching stream activity...");
  try {
    const result = await api("/v1/stream/results?limit=10");
    setOutput("streamOutput", result);
  } catch (err) {
    setOutput("streamOutput", String(err));
  }
}

function wireStreamActions() {
  byId("pushToStream").addEventListener("click", async () => {
    try {
      const payload = {
        event: {
          channel: "MOBILE",
          raw_event: {
            user_id: `USER_${Date.now()}`,
            transfer_to_wallet: "wallet_demo",
            transfer_amount: 1800,
            transfer_time: new Date().toISOString(),
            location: { latitude: 12.97, longitude: 77.59, country: "IN" },
          },
        },
      };

      const result = await api("/v1/stream/publish", {
        method: "POST",
        body: JSON.stringify(payload),
      });
      setOutput("streamOutput", result);
      setTimeout(refreshStream, 400);
    } catch (err) {
      setOutput("streamOutput", String(err));
    }
  });
}

async function refreshIntel() {
  setLoading("intelOutput", "Fetching intel summary...");
  try {
    const result = await api("/v1/intel/summary");
    setOutput("intelOutput", result);
  } catch (err) {
    setOutput("intelOutput", String(err));
  }
}

function wireRefreshButtons() {
  byId("refreshStats").addEventListener("click", refreshStats);
  byId("refreshStream").addEventListener("click", refreshStream);
  byId("refreshIntel").addEventListener("click", refreshIntel);
}

function boot() {
  wirePanelReveal();
  wireButtonGlow();
  initializeApiBase();
  wireRefreshButtons();
  wireDemo();
  wireTransactionForm();
  wireStreamActions();

  refreshLiveStatus();
  refreshStats();
  refreshStream();
  refreshIntel();

  setInterval(refreshLiveStatus, 12000);
}

boot();
