from http import HTTPStatus
from http.client import HTTPConnection
from http.server import ThreadingHTTPServer
from pathlib import Path
from threading import Thread
from time import sleep
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import pytest

from webapp.server import ExtractHandler


@pytest.fixture(name="http_server")
def fixture_http_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), ExtractHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    # Give the server a moment to start
    sleep(0.1)
    try:
        yield server
    finally:
        server.shutdown()
        thread.join()


def test_directory_traversal_is_rejected(http_server):
    conn = HTTPConnection("127.0.0.1", http_server.server_port)
    conn.request("GET", "/../../etc/passwd")
    response = conn.getresponse()
    assert response.status == HTTPStatus.NOT_FOUND
    conn.close()


def test_repository_file_is_not_exposed(http_server):
    conn = HTTPConnection("127.0.0.1", http_server.server_port)
    conn.request("GET", "/../../README.md")
    response = conn.getresponse()
    assert response.status == HTTPStatus.NOT_FOUND
    conn.close()
