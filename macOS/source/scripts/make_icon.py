"""Render a small code-native provenance graph as the macOS application icon."""

import subprocess
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage, QPainter, QPen
from PySide6.QtWidgets import QApplication


def main() -> None:
    """Draw a resolution-independent node graph, then assemble a native ICNS."""
    application = QApplication([])
    assets = Path(__file__).resolve().parents[1] / "assets"
    iconset = assets / "app.iconset"
    iconset.mkdir(parents=True, exist_ok=True)
    for size in [16, 32, 128, 256, 512]:
        for scale in [1, 2]:
            image = QImage(size * scale, size * scale, QImage.Format.Format_ARGB32)
            image.fill(Qt.GlobalColor.transparent)
            painter = QPainter(image)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.scale(size * scale / 1024, size * scale / 1024)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#0b7775"))
            painter.drawRoundedRect(QRectF(62, 62, 900, 900), 210, 210)
            painter.setPen(
                QPen(QColor("#b9dfdc"), 42, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
            )
            painter.drawLine(QPointF(296, 320), QPointF(690, 510))
            painter.drawLine(QPointF(296, 700), QPointF(690, 510))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#ffffff"))
            for x, y, radius in [(296, 320, 87), (296, 700, 87), (690, 510, 119)]:
                painter.drawEllipse(QPointF(x, y), radius, radius)
            painter.setBrush(QColor("#0b7775"))
            painter.drawEllipse(QPointF(690, 510), 49, 49)
            painter.end()
            suffix = "@2x" if scale == 2 else ""
            image.save(str(iconset / f"icon_{size}x{size}{suffix}.png"))
    subprocess.run(
        ["iconutil", "-c", "icns", str(iconset), "-o", str(assets / "app.icns")], check=True
    )
    application.quit()


if __name__ == "__main__":
    main()
