from pathlib import Path

from PySide6.QtWidgets import QApplication


def main() -> None:
    from app.ui import ModPorterWindow

    app = QApplication([])
    window = ModPorterWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
