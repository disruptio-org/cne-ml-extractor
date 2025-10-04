"""Development web server for the extractor front-end."""
from __future__ import annotations

from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from urllib.parse import unquote, urlsplit

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "index.html"


class ExtractHandler(SimpleHTTPRequestHandler):
    """Serve static assets from :data:`BASE_DIR` safely."""

    def translate_path(self, path: str) -> str:  # type: ignore[override]
        """Resolve the request path against :data:`BASE_DIR` securely.

        The default implementation from :class:`SimpleHTTPRequestHandler`
        performs the resolution using plain string manipulation which can lead
        to directory traversal vulnerabilities.  We instead normalise the
        request using :class:`pathlib` utilities and explicitly verify that the
        resolved path stays under :data:`BASE_DIR`.
        """

        parsed_path = urlsplit(path).path
        pure_path = PurePosixPath(unquote(parsed_path))

        resolved_path = BASE_DIR
        for part in pure_path.parts:
            if part in ("", "/"):
                continue
            resolved_path /= part

        resolved_path = resolved_path.resolve()

        try:
            resolved_path.relative_to(BASE_DIR)
        except ValueError as exc:  # pragma: no cover - documented for clarity
            raise PermissionError("Attempted access outside of BASE_DIR") from exc

        if resolved_path.is_dir():
            index_candidate = resolved_path / INDEX_FILE.name
            if index_candidate.exists():
                return str(index_candidate)

        return str(resolved_path)

    def send_head(self):  # type: ignore[override]
        try:
            return super().send_head()
        except PermissionError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None


def serve(host: str = "0.0.0.0", port: int = 8000) -> None:
    """Start a threaded HTTP server for the web application."""

    httpd = ThreadingHTTPServer((host, port), ExtractHandler)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:  # pragma: no cover - manual stop
        pass
    finally:
        httpd.server_close()


if __name__ == "__main__":  # pragma: no cover - manual invocation
    serve()
