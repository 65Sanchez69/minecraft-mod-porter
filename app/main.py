import sys

from PySide6.QtWidgets import QApplication

from app.ui import ModPorterWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = ModPorterWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
