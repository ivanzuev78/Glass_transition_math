import sys

from PyQt5.QtWidgets import QApplication

from res.init_class import InitClass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = InitClass()
    app.exec_()
