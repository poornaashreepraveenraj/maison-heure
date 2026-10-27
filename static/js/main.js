/* Maison Heure — shared UI behaviour (vanilla JS, no dependencies).
   Exposes a small helper namespace on window.MaisonHeure for chat.js / shop.js. */
(function () {
  "use strict";

  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const finePointer = window.matchMedia("(pointer: fine)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  function getCsrfToken() {
    const input = $("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  function storage(kind) {
    try { return window[kind]; } catch (e) { return null; }
  }

  /* ---------- Focus trap for drawers / dialogs ---------- */
  const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select, textarea, [tabindex]:not([tabindex="-1"])';

  function createDrawer(panel, backdrop, openers, closers) {
    let lastFocus = null;

    function onKey(event) {
      if (event.key === "Escape") { close(); return; }
      if (event.key !== "Tab") return;
      const items = $$(FOCUSABLE, panel).filter((el) => el.offsetParent !== null);
      if (!items.length) return;
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }

    function open() {
      lastFocus = document.activeElement;
      panel.removeAttribute("inert");
      panel.classList.add("is-open");
      if (backdrop) { backdrop.hidden = false; requestAnimationFrame(() => backdrop.classList.add("is-open")); }
      openers.forEach((b) => b.setAttribute("aria-expanded", "true"));
      document.body.classList.add("drawer-open");
      document.addEventListener("keydown", onKey);
      const first = $$(FOCUSABLE, panel)[0];
      if (first) setTimeout(() => first.focus(), 50);
    }

    function close() {
      panel.classList.remove("is-open");
      panel.setAttribute("inert", "");
      if (backdrop) { backdrop.classList.remove("is-open"); setTimeout(() => { backdrop.hidden = true; }, 250); }
      openers.forEach((b) => b.setAttribute("aria-expanded", "false"));
      document.body.classList.remove("drawer-open");
      document.removeEventListener("keydown", onKey);
      if (lastFocus) lastFocus.focus();
    }

    openers.forEach((b) => b.addEventListener("click", open));
    closers.forEach((b) => b.addEventListener("click", close));
    if (backdrop) backdrop.addEventListener("click", close);
    return { open, close };
  }

  /* ---------- Scroll reveal (fade + rise 24px, staggered 60ms per card) ---------- */
  let revealObserver = null;
  function initReveal(root = document) {
    const items = $$(".reveal:not(.is-visible)", root);
    if (reduceMotion || !("IntersectionObserver" in window)) {
      items.forEach((el) => el.classList.add("is-visible"));
      return;
    }
    if (!revealObserver) {
      revealObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
            revealObserver.unobserve(entry.target);
          }
        });
      }, { rootMargin: "0px 0px -40px 0px", threshold: 0.08 });
    }
    items.forEach((el) => {
      if (el.classList.contains("card") && el.parentElement) {
        const index = Array.from(el.parentElement.children).indexOf(el) % 8;
        el.style.setProperty("--reveal-delay", index * 60 + "ms");
      }
      revealObserver.observe(el);
    });
  }

  /* ---------- Currency conversion (third-party FX API with fallback) ---------- */
  const SYMBOLS = { INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "AED " };
  let rates = null;
  let ratesSource = null;
  let currency = (storage("localStorage") && storage("localStorage").getItem("mh-currency")) || "INR";

  function formatMoney(inr) {
    const code = rates && rates[currency] ? currency : "INR";
    const value = code === "INR" ? inr : inr * rates[code];
    const locale = code === "INR" ? "en-IN" : "en-GB";
    const digits = code === "INR" || value >= 1000 ? 0 : 2;
    return (SYMBOLS[code] || code + " ") + Math.round(value).toLocaleString(locale, { maximumFractionDigits: digits });
  }

  function convertPrices(root = document) {
    $$("[data-price-inr]", root).forEach((el) => {
      const inr = Number(el.dataset.priceInr);
      if (!Number.isNaN(inr) && inr > 0) el.textContent = formatMoney(inr);
    });
  }

  function updateCurrencyUI() {
    $$("[data-currency]").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.currency === currency)));
    $$("[data-currency-select]").forEach((s) => { s.value = currency; });
    $$("[data-rates-status]").forEach((el) => {
      if (!ratesSource) el.textContent = "Loading rates…";
      else el.textContent = ratesSource === "live" ? "Live rates" : "Showing fallback rates";
    });
  }

  function setCurrency(code) {
    currency = code;
    const ls = storage("localStorage");
    if (ls) { try { ls.setItem("mh-currency", code); } catch (e) { /* private mode */ } }
    updateCurrencyUI();
    convertPrices();
  }

  function loadRates() {
    const url = document.body.dataset.ratesUrl;
    if (!url) return;
    fetch(url, { headers: { Accept: "application/json" } })
      .then((r) => r.json())
      .then((data) => {
        rates = data.rates;
        ratesSource = data.source;
        updateCurrencyUI();
        if (currency !== "INR") convertPrices();
      })
      .catch(() => { ratesSource = "fallback"; updateCurrencyUI(); });
  }

  /* ---------- Bag: add without reload + fly-to-bag animation ---------- */
  function bumpBagCount(count) {
    $$("[data-bag-count]").forEach((badge) => {
      badge.textContent = count;
      badge.classList.toggle("is-empty", !count);
      badge.classList.remove("bounce");
      void badge.offsetWidth; // restart animation
      badge.classList.add("bounce");
    });
    const icon = $("[data-bag-icon]");
    if (icon) icon.setAttribute("aria-label", `Bag, ${count} item${count === 1 ? "" : "s"}`);
  }

  function flyToBag(sourceImg) {
    const bag = $("[data-bag-icon]");
    if (!sourceImg || !bag || reduceMotion) return;
    const from = sourceImg.getBoundingClientRect();
    const to = bag.getBoundingClientRect();
    const thumb = document.createElement("div");
    thumb.className = "fly-thumb";
    thumb.innerHTML = `<img src="${sourceImg.currentSrc || sourceImg.src}" alt="">`;
    thumb.style.left = from.left + from.width / 2 - 36 + "px";
    thumb.style.top = from.top + from.height / 2 - 36 + "px";
    document.body.appendChild(thumb);
    requestAnimationFrame(() => {
      const dx = to.left + to.width / 2 - (from.left + from.width / 2);
      const dy = to.top + to.height / 2 - (from.top + from.height / 2);
      thumb.style.transform = `translate(${dx}px, ${dy}px) scale(.2)`;
      thumb.style.opacity = ".3";
    });
    setTimeout(() => thumb.remove(), 750);
  }

  /* Small toast in the corner; text is set with textContent so it is never parsed as HTML. */
  function showToast(message, image) {
    let stack = $(".toast-stack");
    if (!stack) {
      stack = document.createElement("div");
      stack.className = "toast-stack";
      stack.setAttribute("role", "status");
      stack.setAttribute("aria-live", "polite");
      document.body.appendChild(stack);
    }
    const toast = document.createElement("div");
    toast.className = "toast";
    if (image) {
      const img = document.createElement("img");
      img.src = image.currentSrc || image.src;
      img.alt = "";
      toast.appendChild(img);
    }
    const text = document.createElement("span");
    const title = document.createElement("strong");
    title.textContent = "Added to bag";
    text.append(title, message.replace(" added to your bag.", ""));
    const link = document.createElement("a");
    link.href = "/bag/";
    link.textContent = "View bag";
    toast.append(text, link);
    stack.appendChild(toast);
    setTimeout(() => {
      toast.classList.add("is-leaving");
      setTimeout(() => toast.remove(), 300);
    }, 3800);
  }

  function initAddToBag() {
    document.addEventListener("submit", (event) => {
      const form = event.target.closest("[data-add-to-bag]");
      if (!form) return;
      event.preventDefault();
      const button = form.querySelector("button");
      if (button) button.disabled = true;
      fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "fetch", Accept: "application/json" },
        body: new FormData(form),
      })
        .then((r) => r.json().then((data) => ({ status: r.status, data })))
        .then(({ status, data }) => {
          if (status === 470) { form.removeAttribute("data-add-to-bag"); form.submit(); return; } // show the 470 page
          if (!data.ok) throw new Error("add failed");
          const card = form.closest(".card");
          const image = (card && $(".img-main", card)) || $("[data-gallery-image]");
          flyToBag(image);
          bumpBagCount(data.count);
          showToast(data.message, image);
          // Only the forms for this watch change (a page can list many watches).
          $$("[data-add-to-bag]").filter((f) => f.action === form.action).forEach((f) => {
            if (f.classList.contains("quick-add")) {
              const badge = document.createElement("span");
              badge.className = "badge badge-ink in-bag";
              badge.textContent = "In your bag";
              f.replaceWith(badge);
              return;
            }
            const link = document.createElement("a");
            link.className = f.querySelector("button").className.replace("btn-block", "") + " btn-block";
            link.href = "/bag/";
            link.textContent = "In your bag — view bag";
            f.replaceWith(link);
          });
        })
        .catch(() => { form.removeAttribute("data-add-to-bag"); form.submit(); });
    });
  }

  /* ---------- Wishlist heart ---------- */
  function initWishlist() {
    document.addEventListener("submit", (event) => {
      const form = event.target.closest("[data-wishlist]");
      if (!form) return;
      event.preventDefault();
      fetch(form.action, {
        method: "POST",
        headers: { "X-CSRFToken": getCsrfToken(), "X-Requested-With": "fetch", Accept: "application/json" },
        body: new FormData(form),
      })
        .then((r) => {
          if (r.status === 401) { window.location = "/login/?next=" + encodeURIComponent(window.location.pathname); return null; }
          return r.json();
        })
        .then((data) => {
          if (!data) return;
          const btn = form.querySelector("button");
          btn.setAttribute("aria-pressed", String(data.in_wishlist));
          btn.setAttribute("aria-label", data.in_wishlist ? "Remove from wishlist" : "Save to wishlist");
        })
        .catch(() => form.submit());
    });
  }

  /* ---------- Landing: brand tabs fetch JSON without reload ---------- */
  function moveIndicator(tabs, tab) {
    const indicator = $(".tab-indicator", tabs);
    if (!indicator || !tab) return;
    indicator.style.width = tab.offsetWidth + "px";
    indicator.style.transform = `translateX(${tab.offsetLeft}px)`;
  }

  function initTabs() {
    $$("[data-tabs]").forEach((tabs) => {
      const grid = document.getElementById(tabs.dataset.target);
      const buttons = $$("[role=tab]", tabs);
      const active = () => buttons.find((b) => b.getAttribute("aria-selected") === "true");
      moveIndicator(tabs, active());
      window.addEventListener("resize", () => moveIndicator(tabs, active()));
      // Tab widths change once the web fonts arrive, so measure again then.
      if (document.fonts) document.fonts.ready.then(() => moveIndicator(tabs, active()));
      buttons.forEach((button, index) => {
        button.addEventListener("click", () => {
          buttons.forEach((b) => b.setAttribute("aria-selected", String(b === button)));
          moveIndicator(tabs, button);
          grid.classList.add("is-loading");
          grid.style.minHeight = grid.offsetHeight + "px"; // no page jump while cards swap
          fetch(`${tabs.dataset.apiUrl}?brand=${encodeURIComponent(button.dataset.brand)}&limit=8`, { headers: { Accept: "application/json" } })
            .then((r) => r.json())
            .then((data) => {
              grid.innerHTML = data.html;
              initReveal(grid);
              convertPrices(grid);
            })
            .finally(() => {
              grid.classList.remove("is-loading");
              setTimeout(() => { grid.style.minHeight = ""; }, 700);
            });
        });
        button.addEventListener("keydown", (e) => {
          if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
          const next = buttons[(index + (e.key === "ArrowRight" ? 1 : buttons.length - 1)) % buttons.length];
          next.focus();
          next.click();
        });
      });
    });
  }

  /* ---------- Header: sticky, hides on scroll down, returns on scroll up.
     On the landing page it is transparent over the dark hero. ---------- */
  function initHeader() {
    const header = $("[data-header]");
    if (!header) return;
    const hero = document.body.classList.contains("is-home") ? $(".hero") : null;
    let lastY = window.scrollY;
    let ticking = false;
    const update = () => {
      const y = window.scrollY;
      const drawerOpen = document.body.classList.contains("drawer-open");
      header.classList.toggle("is-hidden", !drawerOpen && y > lastY && y > 160);
      if (hero) header.classList.toggle("is-over-hero", y < hero.offsetHeight - header.offsetHeight - 10);
      lastY = y;
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
    update();
  }

  /* ---------- Hero parallax: blobs drift at different speeds, content eases away ---------- */
  function initParallax() {
    const hero = $(".hero");
    if (!hero || reduceMotion) return;
    const blobs = $$(".blob", hero);
    const content = $("[data-hero-content]", hero);
    let ticking = false;
    const update = () => {
      const y = Math.min(window.scrollY, hero.offsetHeight);
      blobs.forEach((blob, i) => { blob.style.transform = `translate3d(0, ${y * (0.15 + i * 0.12)}px, 0)`; });
      if (content) {
        content.style.transform = `translate3d(0, ${y * 0.28}px, 0)`;
        content.style.opacity = String(Math.max(0, 1 - y / (hero.offsetHeight * 0.75)));
      }
      ticking = false;
    };
    window.addEventListener("scroll", () => {
      if (!ticking) { ticking = true; requestAnimationFrame(update); }
    }, { passive: true });
  }

  /* ---------- Hero: watch tilts toward the cursor (desktop only) ---------- */
  function initTilt() {
    const tilt = $("[data-tilt]");
    if (!tilt || reduceMotion || !finePointer) return;
    const img = $("img", tilt);
    const hero = tilt.closest(".hero") || document.body;
    hero.addEventListener("mousemove", (e) => {
      const rect = hero.getBoundingClientRect();
      const x = (e.clientX - rect.left) / rect.width - 0.5;
      const y = (e.clientY - rect.top) / rect.height - 0.5;
      img.style.transform = `perspective(800px) rotateY(${x * 14}deg) rotateX(${-y * 10}deg)`;
    });
    hero.addEventListener("mouseleave", () => { img.style.transform = ""; });
  }

  /* ---------- Authentication process line fills as you scroll ---------- */
  function initProcess() {
    $$("[data-process]").forEach((process) => {
      const fill = $("[data-process-fill]", process);
      if (!fill) return;
      const vertical = () => window.matchMedia("(max-width: 760px)").matches;
      const update = () => {
        const rect = process.getBoundingClientRect();
        const start = window.innerHeight * 0.85;
        const progress = Math.min(1, Math.max(0, (start - rect.top) / (rect.height + start * 0.4)));
        const pct = reduceMotion ? 100 : Math.round(progress * 100);
        fill.style.width = vertical() ? "100%" : pct + "%";
        fill.style.height = vertical() ? pct + "%" : "100%";
      };
      window.addEventListener("scroll", update, { passive: true });
      window.addEventListener("resize", update);
      update();
    });
  }

  /* ---------- "What's my watch worth?" estimator (client-side formula) ---------- */
  // Indicative median prices (INR) for a recent, excellent, full-set example.
  const BRAND_BASE = { rolex: 1150000, omega: 480000, cartier: 420000, "patek-philippe": 3200000, "audemars-piguet": 3600000, tudor: 290000 };
  const CONDITION = { unworn: 1.08, excellent: 1.0, very_good: 0.9, good: 0.78 };

  function initEstimator() {
    const form = $("[data-estimator]");
    if (!form) return;
    const brand = $("[data-est-brand]", form);
    const year = $("[data-est-year]", form);
    const yearOut = $("[data-est-year-out]", form);
    const papers = $("[data-est-papers]", form);
    const low = $("[data-est-low]", form);
    const high = $("[data-est-high]", form);

    function estimate() {
      const slug = brand.selectedOptions[0].dataset.slug;
      const base = BRAND_BASE[slug] || 400000;
      const age = new Date().getFullYear() - Number(year.value);
      // Modern watches lose ~1.5%/yr for 25 years; true vintage (>40 yrs) regains a collector premium.
      let ageFactor = Math.max(0.6, 1 - Math.min(age, 25) * 0.015);
      if (age > 40) ageFactor += Math.min(0.35, (age - 40) * 0.02);
      const condition = CONDITION[(form.querySelector("input[name=condition]:checked") || {}).value] || 1;
      const mid = base * ageFactor * condition * (papers.checked ? 1.12 : 1);
      low.dataset.priceInr = Math.round((mid * 0.88) / 1000) * 1000;
      high.dataset.priceInr = Math.round((mid * 1.12) / 1000) * 1000;
      yearOut.textContent = year.value;
      convertPrices(form);
    }
    form.addEventListener("input", estimate);
    form.addEventListener("change", estimate);
    estimate();
  }

  /* ---------- Small bits ---------- */
  function initCarousel() {
    $$("[data-carousel]").forEach((track) => {
      const section = track.closest("section");
      const step = () => (track.firstElementChild ? track.firstElementChild.offsetWidth + 16 : 300);
      const prev = $("[data-carousel-prev]", section), next = $("[data-carousel-next]", section);
      if (prev) prev.addEventListener("click", () => track.scrollBy({ left: -step(), behavior: reduceMotion ? "auto" : "smooth" }));
      if (next) next.addEventListener("click", () => track.scrollBy({ left: step(), behavior: reduceMotion ? "auto" : "smooth" }));
    });
  }

  function initNewsletter() {
    $$("[data-newsletter]").forEach((form) => {
      form.addEventListener("submit", (e) => {
        e.preventDefault();
        const input = $("input[type=email]", form);
        const status = form.parentElement.querySelector("[data-newsletter-status]");
        const valid = input.checkValidity() && input.value.trim();
        if (status) status.textContent = valid ? "Thank you — you're on the list (demo: no email is stored)." : "Please enter a valid email address.";
        if (valid) form.reset();
      });
    });
  }

  function initPasswordToggles() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-toggle-password]");
      if (!btn) return;
      const input = btn.parentElement.querySelector("input");
      const show = input.type === "password";
      input.type = show ? "text" : "password";
      btn.textContent = show ? "Hide" : "Show";
      btn.setAttribute("aria-pressed", String(show));
      btn.setAttribute("aria-label", show ? "Hide password" : "Show password");
    });
  }

  function initMessages() {
    document.addEventListener("click", (e) => {
      const btn = e.target.closest("[data-dismiss]");
      if (btn) btn.closest(".message").remove();
    });
  }

  function initTimeline() {
    const timeline = $("[data-timeline]");
    if (timeline) setTimeout(() => timeline.classList.add("is-animated"), reduceMotion ? 0 : 200);
  }

  /* Page transitions are handled by CSS (@view-transition in base.css): no JS
     delay before navigating, so links respond instantly. */

  /* Submit once: a second click on a slow sign-up/checkout/contact form would
     post twice (and could create a duplicate), so buttons disable while sending.
     Forms handled by fetch() call preventDefault first and are skipped. */
  function initSubmitOnce() {
    document.addEventListener("submit", (e) => {
      const form = e.target;
      if (e.defaultPrevented || (form.getAttribute("method") || "").toLowerCase() !== "post" || form.hasAttribute("data-pay-form")) return;
      if (form.dataset.submitting) { e.preventDefault(); return; }
      form.dataset.submitting = "1";
      const submitter = e.submitter;
      if (submitter && submitter.name) {
        // Disabled buttons aren't sent, so keep the clicked button's value in a hidden field.
        const hidden = document.createElement("input");
        hidden.type = "hidden";
        hidden.name = submitter.name;
        hidden.value = submitter.value;
        form.appendChild(hidden);
      }
      $$("button[type=submit], button:not([type])", form).forEach((b) => { b.disabled = true; b.setAttribute("aria-busy", "true"); });
      if (submitter && submitter.tagName === "BUTTON") {
        submitter.dataset.label = submitter.textContent;
        submitter.textContent = "Please wait…";
      }
    });
    // Coming back with the browser's Back button restores the form from cache: re-enable it.
    window.addEventListener("pageshow", () => {
      $$("form[data-submitting]").forEach((form) => {
        delete form.dataset.submitting;
        $$("button[aria-busy]", form).forEach((b) => {
          b.disabled = false;
          b.removeAttribute("aria-busy");
          if (b.dataset.label) b.textContent = b.dataset.label;
        });
      });
    });
  }

  /* ================= Live UI ================= */

  /* Poll only while the tab is visible, so background tabs don't hit the server. */
  function every(ms, fn) {
    fn();
    return setInterval(() => { if (!document.hidden) fn(); }, ms);
  }

  /* Hero watch tells the visitor's real local time; the seconds hand sweeps smoothly. */
  function initLiveClock() {
    const clock = $("[data-live-clock]");
    if (!clock) return;
    const hands = {
      hour: $('[data-hand="hour"]', clock),
      minute: $('[data-hand="minute"]', clock),
      second: $('[data-hand="second"]', clock),
    };
    const date = $("[data-live-date]", clock);
    const label = $("[data-live-time]");
    const fmt = new Intl.DateTimeFormat(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit" });
    let lastSecond = -1;

    function frame() {
      const now = new Date();
      // Reduced motion: the seconds hand ticks once a second instead of sweeping.
      const s = now.getSeconds() + (reduceMotion ? 0 : now.getMilliseconds() / 1000);
      const m = now.getMinutes() + s / 60;
      const h = (now.getHours() % 12) + m / 60;
      hands.hour.setAttribute("transform", `rotate(${h * 30} 300 300)`);
      hands.minute.setAttribute("transform", `rotate(${m * 6} 300 300)`);
      hands.second.setAttribute("transform", `rotate(${s * 6} 300 300)`);
      if (now.getSeconds() !== lastSecond) {
        lastSecond = now.getSeconds();
        if (label) label.textContent = fmt.format(now);
        if (date) date.textContent = now.getDate();
      }
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
  }

  /* Demo market index: values drift every few seconds and flash when they change. */
  function initTicker() {
    const ticker = $("[data-ticker]");
    if (!ticker) return;
    const items = $$("[data-tick]", ticker);
    const count = items.length / 2; // the track is duplicated for a seamless loop
    setInterval(() => {
      if (document.hidden) return;
      const index = Math.floor(Math.random() * count);
      const value = Math.round((Number(items[index].dataset.tick) + (Math.random() - 0.5) * 0.6) * 10) / 10;
      [items[index], items[index + count]].forEach((item) => {
        const old = Number(item.dataset.tick);
        item.dataset.tick = value;
        const b = $("b", item);
        b.className = value >= 0 ? "up" : "down";
        b.textContent = `${value >= 0 ? "▲" : "▼"}${Math.abs(value).toFixed(1)}%`;
        void b.offsetWidth; // restart the flash animation
        b.classList.add(value >= old ? "flash-up" : "flash-down");
      });
    }, 2600);
  }

  /* Checkout: live countdown of the 15-minute hold on the watches in the bag. */
  function initHoldCountdown() {
    $$("[data-hold-until]").forEach((note) => {
      const until = new Date(note.dataset.holdUntil).getTime();
      const out = $("[data-hold-countdown]", note);
      const timer = setInterval(() => {
        const left = Math.max(0, Math.round((until - Date.now()) / 1000));
        out.textContent = `${String(Math.floor(left / 60)).padStart(2, "0")}:${String(left % 60).padStart(2, "0")}`;
        note.classList.toggle("is-urgent", left < 120);
        if (left === 0) {
          clearInterval(timer);
          note.textContent = "Your hold has expired — refresh the page to hold the watches again (if they're still available).";
        }
      }, 1000);
    });
  }

  /* Product page: notice if the watch is sold or reserved while you're looking at it. */
  function initLiveAvailability() {
    const page = $("[data-live-status-url]");
    if (!page) return;
    let wasAvailable = page.dataset.available === "true";
    every(15000, () => {
      fetch(page.dataset.liveStatusUrl, { headers: { Accept: "application/json" } })
        .then((r) => r.json())
        .then((data) => {
          if (wasAvailable && !data.is_available) {
            wasAvailable = false;
            const banner = document.createElement("div");
            banner.className = "live-banner";
            banner.setAttribute("role", "status");
            banner.textContent = data.status === "sold"
              ? "This watch has just been sold to another collector."
              : "Another collector has just reserved this watch. It may come back in 15 minutes.";
            $(".purchase-actions").prepend(banner);
            $$("[data-add-to-bag], .btn-express").forEach((el) => {
              const btn = el.tagName === "FORM" ? $("button", el) : el;
              if (btn) { btn.disabled = true; btn.textContent = data.status === "sold" ? "Sold" : "Reserved"; }
            });
          }
        })
        .catch(() => {});
    });
  }

  /* Order page: the timeline refreshes itself when staff update the status in admin. */
  function initLiveTimeline() {
    const timeline = $("[data-timeline]");
    if (!timeline || !timeline.dataset.status) return;
    let status = timeline.dataset.status;
    every(20000, () => {
      fetch(window.location.href, { headers: { Accept: "text/html" } })
        .then((r) => r.text())
        .then((html) => {
          const doc = new DOMParser().parseFromString(html, "text/html");
          const fresh = $("[data-timeline]", doc);
          if (!fresh || fresh.dataset.status === status) return;
          status = fresh.dataset.status;
          timeline.replaceWith(fresh);
          const badge = $("[data-order-status]"), freshBadge = $("[data-order-status]", doc);
          if (badge && freshBadge) badge.replaceWith(freshBadge);
          setTimeout(() => fresh.classList.add("is-animated"), 50);
        })
        .catch(() => {});
    });
  }

  /* /health/ refreshes its checks every 10 seconds. */
  function initLiveHealth() {
    const panel = $("[data-health]");
    if (!panel) return;
    setInterval(() => {
      if (document.hidden) return;
      fetch("?format=json", { headers: { Accept: "application/json" } })
        .then((r) => r.json())
        .then((data) => {
          Object.entries(data.checks).forEach(([key, value]) => {
            const el = $(`[data-check="${key}"]`, panel);
            if (el) el.textContent = typeof value === "boolean" ? (value ? "configured" : "not configured") : value;
          });
          const overall = $("[data-health-status]"), uptime = $("[data-health-uptime]");
          if (overall) overall.textContent = data.status;
          if (uptime) uptime.textContent = data.uptime_seconds;
        })
        .catch(() => {});
    }, 10000);
  }

  document.addEventListener("DOMContentLoaded", () => {
    const drawer = $("[data-drawer]");
    if (drawer) createDrawer(drawer, $("[data-drawer-backdrop]"), $$("[data-drawer-open]"), $$("[data-drawer-close]", drawer));

    $$("[data-currency]").forEach((b) => b.addEventListener("click", () => setCurrency(b.dataset.currency)));
    $$("[data-currency-select]").forEach((s) => s.addEventListener("change", () => setCurrency(s.value)));

    updateCurrencyUI();
    loadRates();
    initReveal();
    initHeader();
    initTabs();
    initTilt();
    initProcess();
    initEstimator();
    initCarousel();
    initNewsletter();
    initPasswordToggles();
    initMessages();
    initAddToBag();
    initWishlist();
    initTimeline();
    initParallax();
    initLiveClock();
    initTicker();
    initHoldCountdown();
    initLiveAvailability();
    initLiveTimeline();
    initLiveHealth();
    initSubmitOnce(); // registered last so fetch-based forms have already called preventDefault
  });

  window.MaisonHeure = { getCsrfToken, createDrawer, initReveal, convertPrices, storage, reduceMotion };
})();
