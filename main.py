import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from optieo.main_window import MainWindow


def main():
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True) if hasattr(
        Qt.ApplicationAttribute, "AA_EnableHighDpiScaling") else None
    app = QApplication(sys.argv)
    app.setApplicationName("OPTIEO / EOSSP")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
