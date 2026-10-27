/* Checkout helpers: live PIN-code validation and double-submit protection on payment. */
(function () {
  "use strict";

  const PIN_RE = /^[1-9]\d{5}$/;

  function showError(input, message) {
    const field = input.closest(".field");
    let list = field.querySelector(".errorlist.js-error");
    if (!message) {
      field.classList.remove("has-error");
      if (list) list.remove();
      return;
    }
    if (!list) {
      list = document.createElement("ul");
      list.className = "errorlist js-error";
      field.appendChild(list);
    }
    field.classList.add("has-error");
    list.innerHTML = "";
    const li = document.createElement("li");
    li.textContent = message;
    list.appendChild(li);
  }

  document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll("[data-pincode]").forEach((input) => {
      input.setAttribute("maxlength", "6");
      input.addEventListener("input", () => {
        input.value = input.value.replace(/\D/g, "").slice(0, 6);
        if (PIN_RE.test(input.value)) showError(input, "");
      });
      input.addEventListener("blur", () => {
        showError(input, input.value && !PIN_RE.test(input.value) ? "PIN code must be 6 digits and can't start with 0." : "");
      });
    });

    const pay = document.querySelector("[data-pay-form]");
    if (pay) {
      pay.addEventListener("submit", (e) => {
        const clicked = e.submitter;
        // Keep the clicked button's value: disabled buttons aren't submitted, so copy it into a hidden field.
        if (clicked && clicked.name) {
          const hidden = document.createElement("input");
          hidden.type = "hidden";
          hidden.name = clicked.name;
          hidden.value = clicked.value;
          pay.appendChild(hidden);
        }
        pay.querySelectorAll("button").forEach((b) => { b.disabled = true; });
        if (clicked) clicked.textContent = "Processing…";
      });
    }
  });
})();
