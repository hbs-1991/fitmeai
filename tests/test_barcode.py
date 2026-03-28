import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from nutrition_agent.services.barcode import decode_barcode


def test_decode_barcode_returns_none_for_no_barcode(tmp_path):
    from PIL import Image

    img = Image.new("RGB", (100, 100), color="white")
    img_path = tmp_path / "blank.jpg"
    img.save(str(img_path))

    result = decode_barcode(str(img_path))
    assert result is None


def test_decode_barcode_returns_string_when_found():
    mock_barcode = MagicMock()
    mock_barcode.data = b"4600682500117"
    mock_barcode.type = "EAN13"

    with patch("nutrition_agent.services.barcode.pyzbar_decode", return_value=[mock_barcode]), \
         patch("nutrition_agent.services.barcode.Image") as mock_image:
        mock_image.open.return_value = MagicMock()
        result = decode_barcode("dummy_path.jpg")
        assert result == "4600682500117"


def test_decode_barcode_returns_none_on_error():
    with patch("nutrition_agent.services.barcode.pyzbar_decode", side_effect=Exception("bad")):
        result = decode_barcode("nonexistent.jpg")
        assert result is None
