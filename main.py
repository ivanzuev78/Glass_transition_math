import sys

from PyQt5.QtWidgets import QApplication

from Window_maker import TgViewWindow, MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()