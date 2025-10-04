from io import BytesIO

from PIL import Image

from cne_ml_extractor import utils


class FakePixmap:
    def __init__(self, data: bytes):
        self._data = data

    def tobytes(self, fmt: str) -> bytes:
        assert fmt == "png"
        return self._data


class FakePage:
    def __init__(self, text: str, pixmap: FakePixmap):
        self._text = text
        self._pixmap = pixmap

    def get_text(self, kind: str) -> str:
        assert kind == "text"
        return self._text

    def get_pixmap(self) -> FakePixmap:
        return self._pixmap


class FakeDoc:
    def __init__(self, pages):
        self._pages = pages

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def __iter__(self):
        return iter(self._pages)


def test_pdf_to_lines_uses_ocr(monkeypatch):
    image = Image.new("RGB", (2, 2), color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    fake_pixmap = FakePixmap(buffer.getvalue())

    fake_doc = FakeDoc([FakePage("", fake_pixmap)])

    def fake_open(path):
        return fake_doc

    monkeypatch.setattr(utils.fitz, "open", fake_open)

    def fake_image_to_string(image_obj, lang):
        assert lang == "por"
        return "Linha 1\n\nLinha 2"

    monkeypatch.setattr(utils.pytesseract, "image_to_string", fake_image_to_string)

    result = utils.pdf_to_lines("dummy.pdf")

    assert result == [["Linha 1", "Linha 2"]]
