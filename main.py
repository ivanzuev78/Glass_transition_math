import sys

from PyQt5.QtWidgets import QApplication

from init_class import InitClass
from qt_windows import MyMainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = InitClass()
    app.exec_()
