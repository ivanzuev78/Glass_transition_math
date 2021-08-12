import sys

from PyQt5.QtWidgets import QApplication

from main_window import MyMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MyMainWindow()
    form.show()
    app.exec_()
