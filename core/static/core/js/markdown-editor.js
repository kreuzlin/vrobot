// Turns every textarea.markdown-editor in the admin into an EasyMDE editor.
// Toolbar buttons use German text labels instead of an icon font, so no
// external resources are loaded.
(function () {
  "use strict";

  function button(name, label, action, title) {
    return { name: name, action: action, icon: label, className: "md-btn", title: title || label };
  }

  // CSRF token from the admin form the editor sits in.
  function csrfToken(textarea) {
    var form = textarea.form || document;
    var input = form.querySelector("input[name=csrfmiddlewaretoken]");
    return input ? input.value : "";
  }

  // Preview rendered by the server (core.views.markdown_preview), so it uses
  // the same Markdown renderer and sanitiser as the website. EasyMDE expects
  // the HTML synchronously: return the current content (or a loading note)
  // and fill in the server's answer when it arrives.
  function serverPreview(textarea) {
    var url = textarea.dataset.previewUrl;
    var pending = 0;

    return function (plainText, preview) {
      var request = ++pending;
      var body = new URLSearchParams();
      body.append("text", plainText);
      fetch(url, {
        method: "POST",
        body: body,
        credentials: "same-origin",
        headers: { "X-CSRFToken": csrfToken(textarea) },
      })
        .then(function (response) {
          if (!response.ok) throw new Error(response.status);
          return response.text();
        })
        .then(function (html) {
          // Ignore answers to older requests that arrive late.
          if (request === pending) preview.innerHTML = html;
        })
        .catch(function () {
          if (request === pending) {
            preview.innerHTML =
              "<p><strong>Die Vorschau konnte nicht geladen werden.</strong> " +
              "Ist die Anmeldung abgelaufen? Der Text geht dabei nicht verloren.</p>";
          }
        });
      return preview.innerHTML || "<p>Vorschau wird geladen …</p>";
    };
  }

  function init(textarea) {
    if (textarea.dataset.mdInitialised) return;
    textarea.dataset.mdInitialised = "1";

    new EasyMDE({
      element: textarea,
      autoDownloadFontAwesome: false,
      forceSync: true,
      spellChecker: false,
      nativeSpellcheck: true,
      status: false,
      minHeight: "300px",
      toolbar: [
        button("bold", "Fett", EasyMDE.toggleBold),
        button("italic", "Kursiv", EasyMDE.toggleItalic),
        button("heading-2", "Überschrift", EasyMDE.toggleHeading2),
        button("heading-3", "Zwischentitel", EasyMDE.toggleHeading3),
        "|",
        button("unordered-list", "Aufzählung", EasyMDE.toggleUnorderedList),
        button("ordered-list", "Nummerierung", EasyMDE.toggleOrderedList),
        button("quote", "Zitat", EasyMDE.toggleBlockquote),
        button("link", "Link", EasyMDE.drawLink),
        "|",
        // noDisable: keep this button active in preview mode, otherwise there
        // is no way back to editing.
        Object.assign(button("preview", "Vorschau", EasyMDE.togglePreview), {
          noDisable: true,
          title: "Vorschau ein/aus",
        }),
      ],
      previewClass: ["editor-preview", "prose"],
      previewRender: serverPreview(textarea),
      promptURLs: true,
      promptTexts: { link: "Adresse des Links (https://…):" },
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("textarea.markdown-editor").forEach(init);
  });
})();
