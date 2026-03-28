from __future__ import annotations

import logging

from PIL import Image
from pyzbar.pyzbar import decode as pyzbar_decode

logger = logging.getLogger(__name__)


def decode_barcode(image_path: str) -> str | None:
    """Try to decode a barcode from an image. Returns barcode string or None."""
    try:
        image = Image.open(image_path)
        barcodes = pyzbar_decode(image)
        if barcodes:
            return barcodes[0].data.decode("utf-8")
        return None
    except Exception:
        logger.exception("Failed to decode barcode from %s", image_path)
        return None
