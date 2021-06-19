import sys

from PyQt5.QtWidgets import QApplication

from Window_maker import MainWindow


import pytest


# @pytest.fixture()
# def filename():
#     app = QApplication(sys.argv)
#     self = MainWindow()
#     yield filename


def test_eew_a():
    app = QApplication(sys.argv)
    self = MainWindow()
    self.add_line("A")
    self.add_line("A")
    self.material_a_types[0].setCurrentIndex(2)
    self.material_comboboxes_a[1].setCurrentIndex(1)
    self.material_percent_lines_a[0].setText("50.00")
    self.material_percent_lines_a[1].setText("50.00")
    self.count_ew("A")
    eew = self.a_ew
    assert eew == 376


def test_eew_b():
    app = QApplication(sys.argv)
    self = MainWindow()
    self.add_line("B")
    self.add_line("B")
    self.material_b_types[0].setCurrentIndex(2)
    self.material_comboboxes_b[1].setCurrentIndex(1)
    self.material_percent_lines_b[0].setText("50.00")
    self.material_percent_lines_b[1].setText("50.00")
    self.count_ew("B")
    assert self.ew_b == 376


def test_ahew_a():
    app = QApplication(sys.argv)
    self = MainWindow()
    self.add_line("A")
    self.add_line("A")
    self.material_a_types[0].setCurrentIndex(1)
    self.material_a_types[1].setCurrentIndex(1)
    self.material_comboboxes_a[1].setCurrentIndex(1)
    self.material_percent_lines_a[0].setText("50.00")
    self.material_percent_lines_a[1].setText("50.00")
    self.count_ew("A")
    assert self.a_ew == -36.54421768707483


def test_ahew_b():
    app = QApplication(sys.argv)
    self = MainWindow()
    self.add_line("B")
    self.add_line("B")
    self.material_b_types[0].setCurrentIndex(1)
    self.material_b_types[1].setCurrentIndex(1)
    self.material_comboboxes_b[1].setCurrentIndex(1)
    self.material_percent_lines_b[0].setText("50.00")
    self.material_percent_lines_b[1].setText("50.00")
    self.count_ew("B")
    assert self.ew_b == -36.54421768707483
