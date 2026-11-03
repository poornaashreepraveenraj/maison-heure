/* FAQ page: loads the questions from /api/faqs/ and searches them as you type.
   The server-rendered list inside [data-faq-list] is the fallback if this fails. */
(function () {
  "use strict";

  const root = document.querySelector("[data-faq-root]");
  if (!root) return;
  const list = root.querySelector("[data-faq-list]");
  const input = root.querySelector("[data-faq-search]");
  const status = root.querySelector("[data-faq-status]");
  let controller = null;
  let timer = null;

  // Built with DOM methods and textContent, so FAQ text is never parsed as HTML.
  function render(results, query) {
    list.replaceChildren();
    if (!results.length) {
      const empty = document.createElement("div");
      empty.className = "empty-state";
      const title = document.createElement("h3");
      title.textContent = "No matching questions";
      const hint = document.createElement("p");
      hint.textContent = "Try a different word, or ask the concierge — it opens a support ticket if it can't answer.";
      empty.append(title, hint);
      list.appendChild(empty);
      return;
    }
    let currentCategory = null;
    let group = null;
    results.forEach((faq) => {
      if (faq.category !== currentCategory) {
        currentCategory = faq.category;
        const heading = document.createElement("h2");
        heading.className = "faq-category label-lg";
        heading.textContent = faq.category;
        group = document.createElement("div");
        group.className = "faq-list";
        list.append(heading, group);
      }
      const item = document.createElement("details");
      item.className = "faq-item";
      item.id = `faq-${faq.id}`;
      if (query) item.open = true; // show answers straight away while searching
      const summary = document.createElement("summary");
      summary.textContent = faq.question;
      const answer = document.createElement("div");
      answer.className = "answer";
      faq.answer.split("\n").forEach((line, index) => {
        if (index) answer.appendChild(document.createElement("br"));
        answer.appendChild(document.createTextNode(line));
      });
      item.append(summary, answer);
      group.appendChild(item);
    });
  }

  async function load(query) {
    if (controller) controller.abort(); // only the latest search wins
    controller = new AbortController();
    try {
      const response = await fetch(`${root.dataset.apiUrl}?q=${encodeURIComponent(query)}`, {
        headers: { Accept: "application/json" },
        signal: controller.signal,
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      render(data.results, query);
      status.textContent = query
        ? `${data.count} question${data.count === 1 ? "" : "s"} match “${query}”`
        : `${data.count} questions, loaded from the FAQ API`;
    } catch (error) {
      if (error.name !== "AbortError") status.textContent = "Showing the saved list (search is unavailable right now).";
    }
  }

  input.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(() => load(input.value.trim()), 250);
  });
  load("");
})();
