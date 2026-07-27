"""Ponto de entrada do SoloRef.

Uso:
    python main.py
"""
import sys
from PySide6.QtWidgets import QApplication

from soloref.ui.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("SoloRef")
    app.setOrganizationName("ITA - IC")
    win = MainWindow()
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
