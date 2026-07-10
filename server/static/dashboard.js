"use strict";

const FINISH_DISTANCE_M = 1000;
const SCORE_GOOD_THRESHOLD = 70;
const SCORE_WARNING_THRESHOLD = 40;
const COPY_FEEDBACK_MS = 2000;

const roomCode = document.body.dataset.roomCode;
const rowsByPlayerId = new Map();

const els = {
  tableBody: document.querySelector("#leaderboard-body"),
  table: document.querySelector("#leaderboard-table"),
  emptyState: document.querySelector("#empty-state"),
  connectionBanner: document.querySelector("#connection-banner"),
  updatedAt: document.querySelector("#updated-at"),
  liveRegion: document.querySelector("#live-region"),
  sessionEndedBanner: document.querySelector("#session-ended-banner"),
  copyButton: document.querySelector("#copy-room-code"),
  endSessionButton: document.querySelector("#end-session"),
  exportButton: document.querySelector("#export-csv"),
  exportFeedback: document.querySelector("#export-feedback"),
};

// ── rendering ────────────────────────────────────────────

function scoreBand(score) {
  if (score === null || score === undefined) return "low";
  if (score >= SCORE_GOOD_THRESHOLD) return "good";
  if (score >= SCORE_WARNING_THRESHOLD) return "warning";
  return "low";
}

function avatarColor(name) {
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = (hash << 5) - hash + name.charCodeAt(i);
    hash |= 0;
  }
  const hue = Math.abs(hash) % 360;
  return `hsl(${hue}, 65%, 55%)`;
}

function rankBadge(rank) {
  if (rank === 1) return "🥇";
  if (rank === 2) return "🥈";
  if (rank === 3) return "🥉";
  return String(rank);
}

function restartAnimation(el) {
  el.classList.remove("flash-update");
  void el.offsetWidth; // force reflow so the animation restarts on repeated updates
  el.classList.add("flash-update");
}

function buildRow(row, rank) {
  const tr = document.createElement("tr");
  tr.dataset.playerId = row.player_id;

  const rankTd = document.createElement("td");
  rankTd.className = "rank-cell";
  rankTd.textContent = rankBadge(rank);

  const playerTd = document.createElement("td");
  playerTd.className = "player-cell";
  const avatar = document.createElement("span");
  avatar.className = "avatar";
  avatar.style.backgroundColor = avatarColor(row.player_name);
  avatar.textContent = row.player_name.charAt(0).toUpperCase();
  const nameSpan = document.createElement("span");
  nameSpan.textContent = row.player_name;
  playerTd.append(avatar, nameSpan);

  const distanceTd = document.createElement("td");
  distanceTd.className = "distance-cell";
  const track = document.createElement("div");
  track.className = "progress-track";
  const fill = document.createElement("div");
  fill.className = "progress-fill";
  track.appendChild(fill);
  const label = document.createElement("div");
  label.className = "distance-label";
  distanceTd.append(track, label);

  const respawnTd = document.createElement("td");
  respawnTd.className = "respawn-cell";

  const scoreTd = document.createElement("td");
  const scoreChip = document.createElement("span");
  scoreChip.className = "score-chip";
  scoreTd.appendChild(scoreChip);

  const statusTd = document.createElement("td");
  const statusPill = document.createElement("span");
  statusPill.className = "status-pill";
  const dot = document.createElement("span");
  dot.className = "dot";
  const statusLabel = document.createElement("span");
  statusPill.append(dot, statusLabel);
  statusTd.appendChild(statusPill);

  tr.append(rankTd, playerTd, distanceTd, respawnTd, scoreTd, statusTd);
  return tr;
}

function updateRow(tr, row, rank) {
  tr.dataset.rank = String(rank);
  tr.querySelector(".rank-cell").textContent = rankBadge(rank);

  const nameSpan = tr.querySelector(".player-cell span:last-child");
  nameSpan.textContent = row.player_name;
  const avatar = tr.querySelector(".avatar");
  avatar.style.backgroundColor = avatarColor(row.player_name);
  avatar.textContent = row.player_name.charAt(0).toUpperCase();

  const pct = Math.max(0, Math.min(100, (row.distance_m / FINISH_DISTANCE_M) * 100));
  tr.querySelector(".progress-fill").style.width = `${pct}%`;
  tr.querySelector(".distance-label").textContent = `${row.distance_m} / ${FINISH_DISTANCE_M} m`;

  tr.querySelector(".respawn-cell").textContent = `🔄 ×${row.respawn_count}`;

  const scoreChip = tr.querySelector(".score-chip");
  const score = row.environmental_score;
  scoreChip.dataset.band = scoreBand(score);
  scoreChip.textContent = score === null || score === undefined ? "—" : score.toFixed(1);

  const statusPill = tr.querySelector(".status-pill");
  statusPill.dataset.status = row.status;
  statusPill.querySelector("span:last-child").textContent = row.status;

  restartAnimation(tr);
}

function announceRankChange(rows) {
  if (rows.length === 0) return;
  const leader = rows[0];
  if (els.liveRegion.dataset.leaderId !== leader.player_id) {
    els.liveRegion.dataset.leaderId = leader.player_id;
    els.liveRegion.textContent = `${leader.player_name} moved to 1st place`;
  }
}

function renderEmptyState() {
  els.table.hidden = true;
  els.emptyState.hidden = false;
}

function renderLeaderboard(rows) {
  if (rows.length === 0) {
    renderEmptyState();
    return;
  }
  els.table.hidden = false;
  els.emptyState.hidden = true;

  const seen = new Set();
  const fragment = document.createDocumentFragment();

  requestAnimationFrame(() => {
    rows.forEach((row, index) => {
      const rank = index + 1;
      seen.add(row.player_id);
      let tr = rowsByPlayerId.get(row.player_id);
      if (!tr) {
        tr = buildRow(row, rank);
        rowsByPlayerId.set(row.player_id, tr);
      }
      updateRow(tr, row, rank);
      fragment.appendChild(tr);
    });

    for (const [playerId, tr] of rowsByPlayerId) {
      if (!seen.has(playerId)) {
        tr.remove();
        rowsByPlayerId.delete(playerId);
      }
    }

    els.tableBody.appendChild(fragment);
    announceRankChange(rows);
  });
}

function updateConnectionStatus(state) {
  const labels = {
    live: "🟢 Live",
    reconnecting: "🟠 Reconnecting…",
    disconnected: "🔴 Disconnected",
  };
  els.connectionBanner.dataset.state = state;
  els.connectionBanner.textContent = labels[state];
}

function updateTimestamp() {
  const now = new Date();
  els.updatedAt.textContent = `Updated ${now.toLocaleTimeString("en-GB")}`;
}

const ui = {
  renderLeaderboard,
  renderRow: updateRow,
  updateHeader: updateTimestamp,
  renderEmptyState,
  updateConnectionStatus,
};

// ── initial render (server-provided, before the socket connects) ────────

const initialLeaderboardEl = document.querySelector("#initial-leaderboard");
if (initialLeaderboardEl) {
  const initialRows = JSON.parse(initialLeaderboardEl.textContent);
  ui.renderLeaderboard(initialRows);
  ui.updateHeader();
}

// ── socket wiring ────────────────────────────────────────

const socket = io();

function onConnect() {
  ui.updateConnectionStatus("live");
  socket.emit("join_dashboard", { room_code: roomCode });
}

function onDisconnect() {
  ui.updateConnectionStatus("disconnected");
}

function onReconnectAttempt() {
  ui.updateConnectionStatus("reconnecting");
}

function onLeaderboardUpdate(rows) {
  ui.renderLeaderboard(rows);
  ui.updateHeader();
}

function onSessionEnded() {
  els.sessionEndedBanner.classList.add("visible");
}

const socketHandlers = { onConnect, onDisconnect, onReconnectAttempt, onLeaderboardUpdate };

socket.off("connect");
socket.off("disconnect");
socket.off("reconnect_attempt");
socket.off("leaderboard_update");
socket.off("session_ended");

socket.on("connect", socketHandlers.onConnect);
socket.on("disconnect", socketHandlers.onDisconnect);
socket.on("reconnect_attempt", socketHandlers.onReconnectAttempt);
socket.on("leaderboard_update", socketHandlers.onLeaderboardUpdate);
socket.on("session_ended", onSessionEnded);

// ── toolbar ──────────────────────────────────────────────

els.copyButton?.addEventListener("click", async () => {
  const original = els.copyButton.textContent;
  try {
    await navigator.clipboard.writeText(roomCode);
    els.copyButton.textContent = "Copied ✓";
  } catch {
    els.copyButton.textContent = "✗ Copy failed";
  }
  setTimeout(() => {
    els.copyButton.textContent = original;
  }, COPY_FEEDBACK_MS);
});

els.endSessionButton?.addEventListener("click", async () => {
  if (!window.confirm("End this session for everyone?")) return;
  els.endSessionButton.disabled = true;
  try {
    await fetch(`/api/sessions/${roomCode}/end`, { method: "POST" });
  } finally {
    els.endSessionButton.disabled = false;
  }
});

els.exportButton?.addEventListener("click", async () => {
  els.exportButton.disabled = true;
  els.exportFeedback.textContent = "";
  try {
    const response = await fetch(`/dashboard/${roomCode}/export.csv`);
    if (!response.ok) throw new Error("export failed");
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${roomCode}-report.csv`;
    link.click();
    URL.revokeObjectURL(url);
    els.exportFeedback.textContent = "✔ Exported";
  } catch {
    els.exportFeedback.textContent = "✗ Export failed";
  } finally {
    els.exportButton.disabled = false;
  }
});
