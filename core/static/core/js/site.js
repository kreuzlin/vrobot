// Mobile navigation: the menu button shows and hides the main navigation.
// Without JavaScript the navigation is always visible (see site.css).
(function () {
  "use strict";

  document.addEventListener("DOMContentLoaded", function () {
    var button = document.querySelector(".nav-toggle");
    var nav = document.getElementById("main-nav");
    if (!button || !nav) return;

    function setOpen(open) {
      button.setAttribute("aria-expanded", open ? "true" : "false");
      nav.classList.toggle("is-open", open);
    }

    button.addEventListener("click", function () {
      setOpen(button.getAttribute("aria-expanded") !== "true");
    });

    // Close with Escape and return focus to the button.
    document.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && nav.classList.contains("is-open")) {
        setOpen(false);
        button.focus();
      }
    });
  });
})();
