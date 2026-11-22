"""Serve la documentazione compilata in locale (``make docs-serve``).

Come ``python -m http.server 8000``, ma ogni risposta porta
``Cache-Control: no-cache``: il browser rivalida pagine e fogli di stile a
ogni richiesta (304 se non sono cambiati), quindi dopo una nuova build le
modifiche si vedono su tutte le pagine, non solo su quelle ricaricate a mano.

Uso::

    .venv/bin/python scripts/serve_docs.py docs/build/html
"""

from __future__ import annotations

import errno
import functools
import http.server
import sys
from pathlib import Path

PORT = 8000


class NoCacheHandler(http.server.SimpleHTTPRequestHandler):
    """File statici con rivalidazione obbligatoria a ogni richiesta."""

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-cache")
        super().end_headers()


def main() -> None:
    directory = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    handler = functools.partial(NoCacheHandler, directory=str(directory))
    try:
        server = http.server.ThreadingHTTPServer(("", PORT), handler)
    except OSError as exc:
        if exc.errno != errno.EADDRINUSE:
            raise
        sys.exit(
            f"Port {PORT} is already in use: stop the other server "
            f"(ss -ltnp | grep :{PORT}) and run make docs-serve again."
        )
    with server:
        print(f"Serving {directory} at http://localhost:{PORT}/")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
