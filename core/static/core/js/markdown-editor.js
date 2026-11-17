// Turns every textarea.markdown-editor in the admin into an EasyMDE editor.
// Toolbar buttons use German text labels instead of an icon font, so no
// external resources are loaded.
(function () {
  "use strict";

  function button(name, label, action, title) {
    return { name: name, action: action, icon: label, className: "md-btn", title: title || label };
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
      promptURLs: true,
      promptTexts: { link: "Adresse des Links (https://…):" },
    });
  }

  document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("textarea.markdown-editor").forEach(init);
  });
})();
