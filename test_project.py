import sys

import pytest
from PyQt5.QtWidgets import QApplication

from init_class import InitClass

@pytest.fixture
def receipt():
    app = QApplication(sys.argv)
    form = InitClass(debug=True)

    self = form.my_main_window

    self.add_a_line()
    self.add_a_line()
    self.material_a_types[0].setCurrentIndex(2)
    self.material_a_types[1].setCurrentIndex(2)
    self.material_comboboxes_a[1].setCurrentIndex(1)
    self.material_percent_lines_a[0].setText('50.00')
    self.material_percent_lines_a[1].setText('50.00')
    self.material_list_a[0].percent = 50
    self.material_list_a[1].percent = 50

    # self.normalise_func('A')
    self.to_float('A')
    self.normalise_func('A')

    self.add_b_line()
    self.add_b_line()
    self.material_b_types[0].setCurrentIndex(1)
    self.material_b_types[1].setCurrentIndex(1)
    self.material_comboboxes_b[0].setCurrentIndex(1)
    self.material_comboboxes_b[1].setCurrentIndex(4)

    self.material_percent_lines_b[0].setText('50.00')
    self.material_percent_lines_b[1].setText('50.00')
    self.material_list_b[0].percent = 50
    self.material_list_b[1].percent = 50

    yield self
    # app.exec_()
    # sys.exit(0)


def test_ew_a(receipt):
    self = receipt
    assert self.receipt_a.ew == 183.91304347826087

def test_ew_b(receipt):
    self = receipt
    assert self.receipt_b.ew == -37.97402597402597


def test_mass_ratio(receipt):
    self = receipt
    assert self.receipt_a.receipt_counter.mass_ratio == 4.8431273419377865
