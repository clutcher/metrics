from typing import Optional


def django_normalized_base_url(value: Optional[str]) -> str:
    if not value:
        return ''
    base = str(value).strip()
    if base in ('', '/'):
        return ''
    if base.startswith('/'):
        base = base.lstrip('/')
    base = base.rstrip('/')
    if not base:
        return ''
    return base + '/'
