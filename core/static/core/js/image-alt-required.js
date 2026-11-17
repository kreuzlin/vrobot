// Admin: make the alt text field required as soon as an image is chosen.
// The browser then validates before submitting, so the selected file is not
// lost (browsers clear file inputs when the server returns form errors).
//
// Usage: give the file input `data-alt-field="<id of alt text input>"`.
(function () {
  "use strict";

  function setup(fileInput) {
    var alt = document.getElementById(fileInput.dataset.altField);
    if (!alt) return;
    // With an image already saved, Django's ClearableFileInput wraps the
    // input in <p class="file-upload"> together with a "Currently" link.
    var hasExisting = !!fileInput.closest("p.file-upload");
    var clear = document.getElementById(fileInput.id + "-clear_id");

    function update() {
      var chosen = fileInput.files && fileInput.files.length > 0;
      var keeps = hasExisting && !(clear && clear.checked);
      alt.required = chosen || keeps;
    }

    fileInput.addEventListener("change", update);
    if (clear) clear.addEventListener("change", update);
    update();
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("input[type=file][data-alt-field]").forEach(setup);
  });
})();
