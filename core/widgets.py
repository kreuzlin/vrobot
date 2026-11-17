from django import forms
from django.urls import reverse_lazy


class MarkdownEditor(forms.Textarea):
    """Textarea with the EasyMDE toolbar and preview (admin only).

    The preview is rendered by the server with the website's own Markdown
    renderer and styled with prose.css, so it looks like the published page.

    EasyMDE is vendored under core/static/core/vendor/easymde, so the admin
    loads no external resources.
    """

    def __init__(self, attrs=None):
        attrs = {
            "class": "markdown-editor",
            "rows": 20,
            # Server-side preview endpoint, see core.views.markdown_preview.
            "data-preview-url": reverse_lazy("markdown_preview"),
            **(attrs or {}),
        }
        super().__init__(attrs)

    class Media:
        css = {
            "all": [
                "core/vendor/easymde/easymde.min.css",
                "core/css/prose.css",
                "core/css/markdown-editor.css",
            ]
        }
        js = [
            "core/vendor/easymde/easymde.min.js",
            "core/js/markdown-editor.js",
        ]


MARKDOWN_HELP_TEXT = (
    "Formatierung über die Knöpfe oder direkt: **fett**, *kursiv*, "
    "## Überschrift, - Aufzählung, [Linktext](https://…). "
    "Ein leerer Absatz trennt Abschnitte."
)
