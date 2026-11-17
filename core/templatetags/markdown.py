from django import template

from core.markdown import render_markdown

register = template.Library()


@register.filter(name="markdown")
def markdown_filter(text):
    """Render Markdown to sanitised HTML: `{{ post.body|markdown }}`."""
    return render_markdown(text)
