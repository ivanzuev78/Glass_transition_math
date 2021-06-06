import os
import sys
from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QFileDialog
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *


def isfloat(value):
  try:
    float(value)
    return True
  except ValueError:
    return False


class MainWindow(QtWidgets.QMainWindow, uic.loadUiType("Main_window.ui")[0]):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.widgetList = []
        self.items_a = []
        self.items_a_type = []
        self.items_b_type = []
        self.items_lines_a = []
        self.items_b = []
        self.items_lines_b = []

        self.final_a = None
        self.final_b = None
        self.final_a_numb = 0
        self.final_b_numb = 0

        self.types_of_items = ["None", 'Epoxy', 'NH2', 'OH', 'NCO']
        self.list_of_item_names = ["KER-828", "YDPN-638",
                        "Лапроксид БД"]
        self.space = QSpacerItem

        self.gridLayout_a.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)
        self.gridLayout_b.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)

        self.layout = QGridLayout()
        # print(self.layout.itemAt())

        self.setLayout(self.gridLayout_a)
        self.add_A_but.clicked.connect(self.add_A_line)
        self.del_A_but.clicked.connect(self.del_A_line)
        self.add_B_but.clicked.connect(self.add_B_line)
        self.del_B_but.clicked.connect(self.del_B_line)
        self.debug_but.clicked.connect(self.debug)
        self.normalise_A.clicked.connect(self.normalise_func('A'))
        self.normalise_B.clicked.connect(self.normalise_func('B'))
        # delBUtton.clicked.connect(self.delete)

    def debug(self):
        self.debug_string.setText('Good')

    def to_float(self, komponent):
        if komponent == "A":
            items_lines = self.items_lines_a
        if komponent == "B":
            items_lines = self.items_lines_b

        for widget in items_lines:
            numb = widget.text().replace(',', '.')
            if not isfloat(numb):
                numb = 0
            widget.setText(str(numb))


    def add_line(self, komponent):
        final_label = QLabel('Итого')
        if komponent == 'A':
            items_type = self.items_a_type
            items = self.items_a
            items_lines = self.items_lines_a
            grid = self.gridLayout_a
            if self.final_a:
                self.final_a.deleteLater()
            self.final_a = final_label

        if komponent == 'B':
            items_type = self.items_b_type
            items = self.items_b
            items_lines = self.items_lines_b
            grid = self.gridLayout_b
            if self.final_b:
                self.final_b.deleteLater()
            self.final_b = final_label


        item = QComboBox()
        item.addItems(self.list_of_item_names)
        item.setFixedWidth(120)
        itemtype = QComboBox()
        itemtype.addItems(self.types_of_items)
        itemtype.setFixedWidth(50)
        line = QLineEdit()
        line.setText('0')
        items_type.append(itemtype)
        items.append(item)
        items_lines.append(line)
        row_count = grid.count()
        grid.addWidget(itemtype, row_count + 1, 0)
        grid.addWidget(item, row_count + 1, 1)
        grid.addWidget(line, row_count + 1, 2)
        grid.addWidget(final_label, row_count + 2, 1, alignment=QtCore.Qt.AlignRight)

    def del_line(self, komponent):
        if komponent == "A":
            items_type = self.items_a_type
            items = self.items_a
            items_lines = self.items_lines_a
            grid = self.gridLayout_a
            if self.final_a:
                self.final_a.deleteLater()
                self.final_a = None

        if komponent == "B":
            items_type = self.items_b_type
            items = self.items_b
            items_lines = self.items_lines_b
            grid = self.gridLayout_b
            if self.final_b:
                self.final_b.deleteLater()
                self.final_b = None

        if items:
            items.pop(-1).deleteLater()
            items_lines.pop(-1).deleteLater()
            items_type.pop(-1).deleteLater()

            if items:
                final = QLabel('Итого')
                grid.addWidget(final, grid.count()+1, 1, alignment=QtCore.Qt.AlignRight)
                if komponent == "A":
                    self.final_a = final
                else:
                    self.final_b = final

    def add_A_line(self):
        self.add_line('A')

    def add_B_line(self):
        self.add_line('B')

    def del_A_line(self):
        self.del_line('A')

    def del_B_line(self):
        self.del_line('B')

    def normalise_func(self, komponent):
        if komponent == 'A':
            items_lines = self.items_lines_a
        if komponent == 'B':
            items_lines = self.items_lines_b

        def wrap():
            self.to_float(komponent)
            sum_all = 0
            for widget in items_lines:
                sum_all += float(widget.text())
            if sum_all:
                for widget in items_lines:
                    widget.setText(str(round(float(widget.text()) / sum_all * 100, 2)))
                sum_all = 0
                sum_all_without_last = 0
                for widget in items_lines:
                    sum_all += float(widget.text())
                    if widget is items_lines[-1]:
                        break
                    sum_all_without_last += float(widget.text())
                if sum_all != 100:
                    for widget in reversed(items_lines):
                        current_numb = float(widget.text())
                        if current_numb != 0:
                            widget.setText(str(round(current_numb + (100 - sum_all), 2)))
                            break
        return wrap



if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()