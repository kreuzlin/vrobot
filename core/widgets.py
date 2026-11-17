from django import forms


class MarkdownEditor(forms.Textarea):
    """Textarea with the EasyMDE toolbar and preview (admin only).

    EasyMDE is vendored under core/static/core/vendor/easymde, so the admin
    loads no external resources.
    """

    def __init__(self, attrs=None):
        attrs = {"class": "markdown-editor", "rows": 20, **(attrs or {})}
        super().__init__(attrs)

    class Media:
        css = {
            "all": [
                "core/vendor/easymde/easymde.min.css",
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
