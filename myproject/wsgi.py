"""Compatibility alias for hosts whose default start command is `gunicorn myproject.wsgi:application`.

Render fills its Start Command with that placeholder. The real project package is
`config`, so this re-exports the same WSGI application. Once the Start Command is
`gunicorn config.wsgi:application`, this folder can be deleted.
"""
from config.wsgi import application  # noqa: F401
