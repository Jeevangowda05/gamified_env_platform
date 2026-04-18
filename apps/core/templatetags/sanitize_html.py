from html.parser import HTMLParser

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()


class _AllowlistSanitizer(HTMLParser):
    ALLOWED_TAGS = {
        'p', 'br', 'strong', 'em', 'b', 'i', 'u',
        'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'blockquote', 'code', 'pre', 'a', 'span', 'div',
    }
    ALLOWED_ATTRS = {'href', 'title', 'target', 'rel', 'class'}

    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_starttag(self, tag, attrs):
        if tag not in self.ALLOWED_TAGS:
            return
        safe_attrs = []
        for name, value in attrs:
            if name not in self.ALLOWED_ATTRS:
                continue
            if name == 'href' and not self._is_safe_href(value):
                continue
            safe_attrs.append((name, escape(value)))
        attrs_string = ''.join(f' {name}="{value}"' for name, value in safe_attrs)
        self.parts.append(f'<{tag}{attrs_string}>')

    def handle_endtag(self, tag):
        if tag in self.ALLOWED_TAGS:
            self.parts.append(f'</{tag}>')

    def handle_data(self, data):
        self.parts.append(escape(data))

    def get_html(self):
        return ''.join(self.parts)

    @staticmethod
    def _is_safe_href(value):
        if not value:
            return True
        normalized = value.strip().lower()
        if normalized.startswith(('#', '/')):
            return True
        return normalized.startswith(('http://', 'https://', 'mailto:'))


@register.filter
def sanitize_html(value):
    parser = _AllowlistSanitizer()
    parser.feed(value or '')
    parser.close()
    return mark_safe(parser.get_html())
