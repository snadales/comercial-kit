"""Renderers para comercial-kit (K2)."""

from rest_framework.renderers import JSONRenderer


class ProblemJsonRenderer(JSONRenderer):
    """Renderer para application/problem+json según RFC 9457."""
    media_type = "application/problem+json"
    format = "problem"
