import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from optieo.main_window import MainWindow


def main():
    # Must be set before the QApplication is constructed. On Windows with
    # round layout geometry inconsistently between the layout pass and the
    # paint pass, which shows up as overlapping/"ghosted" label text.
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("OPTIEO / EOSSP")
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
