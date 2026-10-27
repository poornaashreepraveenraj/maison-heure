/* Shop page (live filters, search, sort, load more, filter drawer, dual price slider) and product gallery. */
(function () {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

  /* ---------- Live results: filters, search and sort update the grid without reloading ---------- */
  function initLiveShop() {
    const form = $("[data-filter-form]");
    const results = $("[data-results]");
    if (!form || !results) return;
    const MH = window.MaisonHeure;
    const search = $("#shop-q");
    const sort = $("[data-sort]");
    const range = $("[data-dual-range]", form);
    const count = $("[data-results-count]");
    const heading = $(".page-head h1");
    const loadMoreWrap = $("[data-load-more-wrap]");
    const loadMore = $("[data-load-more]");
    let controller = null;

    // Build the query from the current controls. Untouched price bounds are left
    // out so shareable URLs stay clean.
    function query() {
      const params = new URLSearchParams();
      new FormData(form).forEach((value, key) => {
        if (key === "q" || key === "sort") return;
        if (range && key === "price_min" && Number(value) <= Number(range.dataset.min)) return;
        if (range && key === "price_max" && Number(value) >= Number(range.dataset.max)) return;
        if (value !== "") params.append(key, value);
      });
      if (search && search.value.trim()) params.set("q", search.value.trim());
      if (sort && sort.value !== "newest") params.set("sort", sort.value);
      return params;
    }

    async function refresh() {
      const params = query();
      if (controller) controller.abort(); // only the latest request wins
      controller = new AbortController();
      results.classList.add("is-updating");
      try {
        const response = await fetch(`/shop/?${params}${params.toString() ? "&" : ""}partial=1`, { signal: controller.signal });
        const holder = document.createElement("div");
        holder.innerHTML = await response.text();
        const info = $("[data-page-info]", holder);
        results.innerHTML = holder.innerHTML;
        MH.initReveal(results);
        MH.convertPrices(results);
        history.replaceState(null, "", `/shop/${params.toString() ? "?" + params : ""}`);
        if (info) {
          const total = Number(info.dataset.total);
          count.lastChild.textContent = `${total} watch${total === 1 ? "" : "es"}${params.get("q") ? ` for “${params.get("q")}”` : ""}`;
          if (heading && info.dataset.heading) heading.textContent = info.dataset.heading;
          loadMoreWrap.hidden = info.dataset.hasNext !== "1";
          loadMore.dataset.next = info.dataset.next || "";
          loadMore.dataset.query = params.toString();
        }
      } catch (e) {
        if (e.name !== "AbortError") window.location.href = `/shop/?${params}`; // fall back to a normal page load
      } finally {
        results.classList.remove("is-updating");
      }
    }

    let typing = null;
    form.addEventListener("change", refresh);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      refresh();
      $("[data-filters-close]")?.click(); // on mobile, close the drawer to show results
    });
    if (search) {
      search.addEventListener("input", () => { clearTimeout(typing); typing = setTimeout(refresh, 280); });
      search.form.addEventListener("submit", (e) => { e.preventDefault(); clearTimeout(typing); refresh(); });
    }
    if (sort) sort.addEventListener("change", refresh);
    $("[data-clear-filters]")?.addEventListener("click", (e) => {
      e.preventDefault();
      $$("input[type=checkbox]", form).forEach((c) => { c.checked = false; });
      $$("input[type=number]", form).forEach((n) => { n.value = ""; });
      if (range) {
        $("[data-range-min]", range).value = range.dataset.min;
        $("[data-range-max]", range).value = range.dataset.max;
        $("[data-range-min]", range).dispatchEvent(new Event("input"));
      }
      if (search) search.value = "";
      refresh();
    });

    // "Load more" appends the next page of the current results.
    loadMore.addEventListener("click", async () => {
      loadMore.disabled = true;
      loadMore.textContent = "Loading…";
      const q = loadMore.dataset.query ? loadMore.dataset.query + "&" : "";
      try {
        const response = await fetch(`/shop/?${q}page=${loadMore.dataset.next}&partial=1`);
        const holder = document.createElement("div");
        holder.innerHTML = await response.text();
        const info = $("[data-page-info]", holder);
        $$("[data-page-info]", holder).forEach((n) => n.remove());
        $$("[data-page-info]", results).forEach((n) => n.remove());
        while (holder.firstChild) results.appendChild(holder.firstChild);
        MH.initReveal(results);
        MH.convertPrices(results);
        loadMoreWrap.hidden = !(info && info.dataset.hasNext === "1");
        if (info) loadMore.dataset.next = info.dataset.next || "";
      } finally {
        loadMore.disabled = false;
        loadMore.textContent = "Load more";
      }
    });
  }

  /* ---------- Filter drawer on tablets / phones ---------- */
  function initFilterDrawer() {
    const panel = $("[data-filters]");
    if (!panel) return;
    const isDrawer = () => window.matchMedia("(max-width: 1024px)").matches;
    if (isDrawer()) panel.setAttribute("inert", "");
    window.MaisonHeure.createDrawer(panel, $("[data-filters-backdrop]"), $$("[data-filters-open]"), $$("[data-filters-close]"));
    window.addEventListener("resize", () => {
      if (!isDrawer()) { panel.removeAttribute("inert"); panel.classList.remove("is-open"); }
      else if (!panel.classList.contains("is-open")) panel.setAttribute("inert", "");
    });
  }

  function initDualRange() {
    $$("[data-dual-range]").forEach((range) => {
      const min = $("[data-range-min]", range), max = $("[data-range-max]", range);
      const fill = $("[data-range-fill]", range);
      const minOut = document.querySelector("[data-range-min-out]"), maxOut = document.querySelector("[data-range-max-out]");
      const lo = Number(range.dataset.min), hi = Number(range.dataset.max);
      const update = (moved) => {
        if (Number(min.value) > Number(max.value)) {
          if (moved === min) min.value = max.value; else max.value = min.value;
        }
        const span = hi - lo || 1;
        fill.style.left = ((min.value - lo) / span) * 100 + "%";
        fill.style.right = 100 - ((max.value - lo) / span) * 100 + "%";
        minOut.dataset.priceInr = min.value;
        maxOut.dataset.priceInr = max.value;
        window.MaisonHeure.convertPrices(range.parentElement);
      };
      min.addEventListener("input", () => update(min));
      max.addEventListener("input", () => update(max));
      update();
    });
  }

  function initGallery() {
    const gallery = $("[data-gallery]");
    if (!gallery) return;
    const main = $("[data-gallery-main]", gallery);
    const image = $("[data-gallery-image]", gallery);
    $$("[data-gallery-thumb]", gallery).forEach((thumb) => {
      thumb.addEventListener("click", () => {
        $$("[data-gallery-thumb]", gallery).forEach((t) => t.removeAttribute("aria-current"));
        thumb.setAttribute("aria-current", "true");
        image.style.opacity = "0";
        setTimeout(() => { image.src = thumb.dataset.src; image.alt = thumb.dataset.alt; image.style.opacity = "1"; }, 150);
      });
    });
    main.addEventListener("click", () => {
      const zoomed = main.classList.toggle("is-zoomed");
      main.setAttribute("aria-label", zoomed ? "Zoom out" : "Zoom image");
      if (!zoomed) image.style.transformOrigin = "";
    });
    main.addEventListener("mousemove", (e) => {
      if (!main.classList.contains("is-zoomed")) return;
      const rect = main.getBoundingClientRect();
      image.style.transformOrigin = `${((e.clientX - rect.left) / rect.width) * 100}% ${((e.clientY - rect.top) / rect.height) * 100}%`;
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    initFilterDrawer();
    initDualRange();
    initLiveShop();
    initGallery();
  });
})();
