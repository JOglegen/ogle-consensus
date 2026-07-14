const models = [
  "MA50 cross",
  "MACD",
  "RSI(14)",
  "Bollinger %B",
  "Stochastic %K",
  "Rate of Change",
  "Trend slope",
  "Volume surge",
  "Volume trend",
  "ATR regime",
  "Range position",
  "Candle pattern",
  "Z-score",
];

const state = {
  signal: null,
  log: JSON.parse(localStorage.getItem("oglePaperLog") || "[]"),
  recommendations: [],
  activity: [],
  live: true,
  liveTimer: null,
};

const watchlist = ["BTC-USD", "ETH-USD", "SPY", "QQQ", "AAPL", "NVDA", "MSFT", "TSLA"];

const $ = (id) => document.getElementById(id);

function hashSymbol(symbol) {
  return [...symbol.toUpperCase()].reduce((acc, char) => acc + char.charCodeAt(0), 0);
}

function modelVote(seed, index) {
  const value = Math.sin(seed * (index + 3) * 0.137) + Math.cos((seed + index) * 0.211);
  if (value > 0.42) return "buy";
  if (value < -0.42) return "sell";
  return "hold";
}

function runScan() {
  const symbol = $("symbol").value.trim().toUpperCase() || "BTC-USD";
  const threshold = Number($("threshold").value);
  const account = Math.max(Number($("account").value) || 1000, 100);
  state.signal = createSignal(symbol, threshold, account);

  renderSignal();
  addActivity(`${state.signal.action.toUpperCase()} scan ready`, `${symbol} produced ${state.signal.buyVotes} buy / ${state.signal.sellVotes} sell votes at ${state.signal.confidence}% confidence.`);
}

function createSignal(symbol, threshold, account, offset = 0) {
  const seed = hashSymbol(symbol) + threshold * 17 + new Date().getMinutes() + offset;
  const votes = models.map((name, index) => ({ name, vote: modelVote(seed, index) }));
  const buyVotes = votes.filter((item) => item.vote === "buy").length;
  const sellVotes = votes.filter((item) => item.vote === "sell").length;
  const holdVotes = votes.length - buyVotes - sellVotes;
  const action = buyVotes >= threshold ? "buy" : sellVotes >= threshold ? "sell" : "hold";
  const leadingVotes = Math.max(buyVotes, sellVotes, holdVotes);
  const confidence = Math.round((leadingVotes / models.length) * 100);
  const price = Math.round((50 + (seed % 900) + Math.abs(Math.sin(seed)) * 73) * 100) / 100;
  const size = action === "hold" ? 0 : Math.round(account * Math.min(confidence / 100, 0.72) * 0.08);

  return {
    time: new Date().toLocaleString(),
    symbol,
    action,
    buyVotes,
    sellVotes,
    holdVotes,
    confidence,
    price,
    size,
    votes,
    reason: explainSignal(action, buyVotes, sellVotes, holdVotes),
  };
}

function explainSignal(action, buyVotes, sellVotes, holdVotes) {
  if (action === "buy") return `${buyVotes} models favor upside momentum or trend strength.`;
  if (action === "sell") return `${sellVotes} models flag downside pressure or elevated risk.`;
  return `${holdVotes} hold votes mean the bot is waiting for cleaner agreement.`;
}

function renderSignal() {
  const signal = state.signal;
  if (!signal) {
    $("model-list").innerHTML = "";
    renderLog();
    return;
  }

  const actionLabel = signal.action.toUpperCase();
  $("hero-symbol").textContent = signal.symbol;
  $("hero-action").textContent = actionLabel;
  $("hero-action").className = `pill ${signal.action}`;
  $("signal-title").textContent = `${signal.symbol} consensus scan`;
  $("signal-action").textContent = actionLabel;
  $("signal-action").className = `pill ${signal.action}`;
  $("hero-buy").textContent = `${signal.buyVotes}/13`;
  $("hero-hold").textContent = `${signal.holdVotes}/13`;
  $("hero-sell").textContent = `${signal.sellVotes}/13`;
  $("hero-buy-bar").style.width = `${(signal.buyVotes / 13) * 100}%`;
  $("hero-hold-bar").style.width = `${(signal.holdVotes / 13) * 100}%`;
  $("hero-sell-bar").style.width = `${(signal.sellVotes / 13) * 100}%`;
  $("price").textContent = `$${signal.price.toLocaleString()}`;
  $("confidence").textContent = `${signal.confidence}%`;
  $("size").textContent = signal.size ? `$${signal.size.toLocaleString()}` : "$0";
  $("ticket-copy").textContent =
    signal.action === "hold"
      ? "No trade is suggested. Log this only if you want to track a wait decision."
      : `${actionLabel} paper ticket ready. Suggested size is based on account value and confidence.`;
  $("model-list").innerHTML = signal.votes
    .map(
      (item) => `
        <div class="model-row">
          <span>${item.name}</span>
          <span class="vote ${item.vote}">${item.vote.toUpperCase()}</span>
        </div>
      `,
    )
    .join("");
}

function logTrade() {
  if (!state.signal) runScan();
  state.log.unshift({ ...state.signal, id: crypto.randomUUID() });
  state.log = state.log.slice(0, 50);
  localStorage.setItem("oglePaperLog", JSON.stringify(state.log));
  renderLog();
  addActivity("Paper trade logged", `${state.signal.symbol} ${state.signal.action.toUpperCase()} was added to the browser-side paper log.`);
}

function renderLog() {
  $("trade-log").innerHTML = state.log
    .map(
      (item) => `
        <tr>
          <td>${item.time}</td>
          <td>${item.symbol}</td>
          <td>${item.action.toUpperCase()}</td>
          <td>${item.buyVotes} buy / ${item.sellVotes} sell / ${item.holdVotes} hold</td>
          <td>$${Number(item.price).toLocaleString()}</td>
          <td>$${Number(item.size).toLocaleString()}</td>
          <td>${item.confidence}%</td>
        </tr>
      `,
    )
    .join("");
  $("empty-log").style.display = state.log.length ? "none" : "block";
}

function exportLog() {
  const header = "time,symbol,action,buy_votes,sell_votes,hold_votes,price,size,confidence";
  const rows = state.log.map((item) =>
    [
      item.time,
      item.symbol,
      item.action,
      item.buyVotes,
      item.sellVotes,
      item.holdVotes,
      item.price,
      item.size,
      item.confidence,
    ]
      .map((value) => `"${String(value).replaceAll('"', '""')}"`)
      .join(","),
  );
  const blob = new Blob([[header, ...rows].join("\n")], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "ogle-paper-trades.csv";
  link.click();
  URL.revokeObjectURL(url);
}

function scanWatchlist() {
  const threshold = Number($("threshold").value);
  const account = Math.max(Number($("account").value) || 1000, 100);
  state.recommendations = watchlist
    .map((symbol, index) => createSignal(symbol, threshold, account, index * 11))
    .sort((a, b) => {
      const actionWeight = { buy: 2, sell: 1, hold: 0 };
      return actionWeight[b.action] - actionWeight[a.action] || b.confidence - a.confidence;
    });
  renderRecommendations();
  const leader = state.recommendations[0];
  addActivity("Watchlist scan complete", `Top paper idea: ${leader.symbol} ${leader.action.toUpperCase()} at ${leader.confidence}% confidence.`);
}

function renderRecommendations() {
  $("recommendations").innerHTML = state.recommendations
    .map(
      (item) => `
        <tr>
          <td><strong>${item.symbol}</strong></td>
          <td><span class="score ${item.action}">${item.action.toUpperCase()}</span></td>
          <td>${item.buyVotes} buy / ${item.sellVotes} sell / ${item.holdVotes} hold</td>
          <td>${item.confidence}%</td>
          <td>$${Number(item.price).toLocaleString()}</td>
          <td>${item.reason}</td>
        </tr>
      `,
    )
    .join("");
}

function addActivity(title, detail) {
  state.activity.unshift({
    title,
    detail,
    time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" }),
  });
  state.activity = state.activity.slice(0, 12);
  renderActivity();
}

function renderActivity() {
  $("activity-list").innerHTML = state.activity
    .map(
      (item) => `
        <div class="activity-item">
          <strong>${item.title}</strong>
          <span>${item.time} - ${item.detail}</span>
        </div>
      `,
    )
    .join("");
}

function toggleLive() {
  state.live = !state.live;
  $("toggle-live").textContent = state.live ? "Pause Activity" : "Resume Activity";
  $("live-state").textContent = state.live ? "Live demo" : "Paused";
  if (state.live) {
    addActivity("Activity resumed", "The dashboard will continue refreshing watchlist paper signals.");
  } else {
    addActivity("Activity paused", "Auto-refresh is paused. Manual scans still work.");
  }
}

function startLiveLoop() {
  state.liveTimer = window.setInterval(() => {
    if (!state.live) return;
    scanWatchlist();
  }, 15000);
}

$("scan-form").addEventListener("submit", (event) => {
  event.preventDefault();
  runScan();
});

$("reset-demo").addEventListener("click", () => {
  $("symbol").value = "BTC-USD";
  $("threshold").value = "6";
  $("account").value = "1000";
  runScan();
});

$("log-trade").addEventListener("click", logTrade);
$("export-log").addEventListener("click", exportLog);
$("scan-watchlist").addEventListener("click", scanWatchlist);
$("toggle-live").addEventListener("click", toggleLive);
$("clear-log").addEventListener("click", () => {
  state.log = [];
  localStorage.removeItem("oglePaperLog");
  renderLog();
  addActivity("Paper log cleared", "Browser-side paper trade history was reset.");
});

runScan();
scanWatchlist();
renderLog();
startLiveLoop();
