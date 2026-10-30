/* Maison Heure Concierge — the chat widget on every page.
   Talks to /api/chat/ (answers) and /api/feedback/ (thumbs up/down), both CSRF-protected. */
(function () {
  "use strict";

  const SOURCE_LABELS = {
    error_code: "Answered from our error-code guide",
    order: "From your order records",
    catalogue: "From our live catalogue",
    faq: "Answered from our FAQ",
    ai: "Answered by our concierge",
    ticket: "Support ticket created",
    smalltalk: "Concierge",
  };
  const HISTORY_KEY = "mh-chat-history";

  document.addEventListener("DOMContentLoaded", () => {
    const root = document.querySelector("[data-chat]");
    if (!root) return;
    const SH = window.MaisonHeure || {};
    const panel = root.querySelector("[data-chat-panel]");
    const launcher = root.querySelector("[data-chat-open]");
    const closeBtn = root.querySelector("[data-chat-close]");
    const log = root.querySelector("[data-chat-log]");
    const form = root.querySelector("[data-chat-form]");
    const input = form.querySelector("input[name=message]");
    const emailInput = form.querySelector("input[name=email]");
    const csrf = root.querySelector("input[name=csrfmiddlewaretoken]").value;
    const session = SH.storage ? SH.storage("sessionStorage") : null;
    const local = SH.storage ? SH.storage("localStorage") : null;
    let busy = false;

    function sessionId() {
      let id = local && local.getItem("mh-chat-session");
      if (!id) {
        id = window.crypto && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2);
        try { local && local.setItem("mh-chat-session", id); } catch (e) { /* storage blocked */ }
      }
      return id;
    }

    /* Escape everything first, then add our tiny bit of formatting: **bold**, links, line breaks. */
    function format(text) {
      const escaped = String(text)
        .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
      return escaped
        .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
        .replace(/(^|[\s(])(\/[a-z0-9][a-z0-9\-/]*\/)/gi, '$1<a href="$2">$2</a>')
        .replace(/(^|[\s(])(https:\/\/[^\s<]+)/g, '$1<a href="$2" rel="noopener" target="_blank">$2</a>');
    }

    function saveHistory() {
      if (!session) return;
      try { session.setItem(HISTORY_KEY, log.innerHTML); } catch (e) { /* quota */ }
    }

    function restoreHistory() {
      const saved = session && session.getItem(HISTORY_KEY);
      if (saved) { log.innerHTML = saved; log.scrollTop = log.scrollHeight; }
    }

    function addMessage(role, html) {
      const msg = document.createElement("div");
      msg.className = `chat-msg ${role}`;
      msg.innerHTML = html;
      log.appendChild(msg);
      log.scrollTop = log.scrollHeight;
      return msg;
    }

    function open() {
      panel.removeAttribute("inert");
      panel.classList.add("is-open");
      launcher.setAttribute("aria-expanded", "true");
      setTimeout(() => input.focus(), 60);
    }

    function close() {
      panel.classList.remove("is-open");
      panel.setAttribute("inert", "");
      launcher.setAttribute("aria-expanded", "false");
      launcher.focus();
    }

    async function send(text) {
      text = (text || "").trim();
      if (!text || busy) return;
      busy = true;
      addMessage("user", format(text));
      const typing = addMessage("bot", '<span class="chat-typing" aria-label="Concierge is typing"><span></span><span></span><span></span></span>');
      try {
        const response = await fetch(root.dataset.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-CSRFToken": csrf, Accept: "application/json" },
          body: JSON.stringify({ message: text, page: window.location.pathname, email: emailInput.value.trim(), session_id: sessionId() }),
        });
        const data = await response.json();
        let html = format(data.answer || "Sorry, something went wrong.");
        html += `<span class="chat-source">${SOURCE_LABELS[data.source] || (response.status === 429 ? "Rate limited (429)" : "")}</span>`;
        if (data.log_id) {
          html += `<div class="chat-feedback" data-log-id="${data.log_id}"><span>Helpful?</span>` +
            '<button type="button" data-helpful="true" aria-label="Yes, helpful">👍</button>' +
            '<button type="button" data-helpful="false" aria-label="Not helpful">👎</button></div>';
        }
        typing.innerHTML = html;
      } catch (err) {
        typing.innerHTML = format("I couldn't reach the help desk just now. Please try again, or use the contact page.");
      } finally {
        busy = false;
        log.scrollTop = log.scrollHeight;
        saveHistory();
      }
    }

    function sendFeedback(button) {
      const box = button.closest("[data-log-id]");
      box.querySelectorAll("button").forEach((b) => { b.disabled = true; b.setAttribute("aria-pressed", String(b === button)); });
      fetch(root.dataset.feedbackEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf },
        body: JSON.stringify({ log_id: box.dataset.logId, helpful: button.dataset.helpful === "true", session_id: sessionId() }),
      }).finally(() => {
        box.querySelector("span").textContent = "Thanks for the feedback";
        saveHistory();
      });
    }

    launcher.addEventListener("click", open);
    closeBtn.addEventListener("click", close);
    panel.addEventListener("keydown", (e) => { if (e.key === "Escape") close(); });
    form.addEventListener("submit", (e) => { e.preventDefault(); const text = input.value; input.value = ""; send(text); });
    root.querySelectorAll("[data-chat-chip]").forEach((chip) => chip.addEventListener("click", () => send(chip.textContent)));
    log.addEventListener("click", (e) => {
      const button = e.target.closest("[data-helpful]");
      if (button && !button.disabled) sendFeedback(button);
    });

    // Any element with data-ask="..." (error pages, product pages) opens the chat with that question.
    document.addEventListener("click", (e) => {
      const trigger = e.target.closest("[data-ask]");
      if (!trigger) return;
      e.preventDefault();
      open();
      send(trigger.dataset.ask);
    });

    restoreHistory();
  });
})();
