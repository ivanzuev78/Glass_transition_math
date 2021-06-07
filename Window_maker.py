import sys
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import *


from Materials import *

DB_NAME = "material.db"

# f"{numb:.{digits}f}"
class MainWindow(QtWidgets.QMainWindow, uic.loadUiType("Main_window.ui")[0]):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.db_name = DB_NAME
        self.add_material_window = None
        self.material_to_add = None
        self.widgetList = []

        self.material_comboboxes_a = []
        self.material_comboboxes_b = []
        self.material_a_types = []
        self.material_b_types = []
        self.material_percent_lines_a = []
        self.material_percent_lines_b = []

        self.final_a = None
        self.final_b = None
        self.final_a_numb_label = None
        self.final_b_numb_label = None

        self.types_of_items = get_all_material_types(self.db_name)

        self.list_of_item_names = {
            material: get_all_material_of_one_type(material, self.db_name)
            for material in self.types_of_items
        }

        self.gridLayout_a.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)
        self.gridLayout_b.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)

        self.layout = QGridLayout()

        self.setLayout(self.gridLayout_a)
        self.add_A_but.clicked.connect(self.add_A_line)
        self.del_A_but.clicked.connect(self.del_A_line)
        self.add_B_but.clicked.connect(self.add_B_line)
        self.del_B_but.clicked.connect(self.del_B_line)
        self.debug_but.clicked.connect(self.debug)
        self.add_raw.clicked.connect(self.add_material)
        self.normalise_A.clicked.connect(self.normalise_func("A"))
        self.normalise_B.clicked.connect(self.normalise_func("B"))

        self.hide_top("A")
        self.hide_top("B")

    def debug(self):
        self.debug_string.setText("Good")

    def to_float(self, komponent: str):
        if komponent == "A":
            items_lines = self.material_percent_lines_a
        elif komponent == "B":
            items_lines = self.material_percent_lines_b

        for widget in items_lines:
            numb = widget.text().replace(",", ".")
            if not self.isfloat(numb):
                numb = 0
            widget.setText(f"{float(numb):.{2}f}")

    def add_line(self, komponent: str):
        final_label = QLabel("Итого")
        final_label_numb = QLabel("0.00")
        if komponent == "A":
            items_type = self.material_a_types
            items = self.material_comboboxes_a
            items_lines = self.material_percent_lines_a
            grid = self.gridLayout_a
            if self.final_a:
                self.final_a.deleteLater()
            self.final_a = final_label
            if self.final_a_numb_label:
                self.final_a_numb_label.deleteLater()
            self.final_a_numb_label = final_label_numb

        elif komponent == "B":
            items_type = self.material_b_types
            items = self.material_comboboxes_b
            items_lines = self.material_percent_lines_b
            grid = self.gridLayout_b
            if self.final_b:
                self.final_b.deleteLater()
            self.final_b = final_label
            if self.final_b_numb_label:
                self.final_b_numb_label.deleteLater()
            self.final_b_numb_label = final_label_numb
        else:
            return None

        self.show_top(komponent)

        material_combobox = QComboBox()
        material_combobox.addItems(self.list_of_item_names["None"])
        material_combobox.setFixedWidth(120)
        materia_typel_combobox = QComboBox()
        materia_typel_combobox.addItems(self.types_of_items)
        materia_typel_combobox.setFixedWidth(60)
        materia_typel_combobox.currentIndexChanged.connect(
            self.change_list_of_materials(material_combobox, materia_typel_combobox)
        )
        line = QLineEdit()
        line.setText("0.00")
        items_type.append(materia_typel_combobox)
        items.append(material_combobox)
        items_lines.append(line)
        row_count = grid.count()
        grid.addWidget(materia_typel_combobox, row_count + 1, 0)
        grid.addWidget(material_combobox, row_count + 1, 1)
        grid.addWidget(line, row_count + 1, 2)
        grid.addWidget(final_label, row_count + 2, 1, alignment=QtCore.Qt.AlignRight)
        grid.addWidget(final_label_numb, row_count + 2, 2)
        self.count_sum(komponent)

    def change_list_of_materials(self, material_combobox, material_type):
        def wrapper():
            material_combobox.clear()
            material_combobox.addItems(
                self.list_of_item_names[material_type.currentText()]
            )

        return wrapper

    def del_line(self, komponent: str):
        if komponent == "A":
            items_type = self.material_a_types
            items = self.material_comboboxes_a
            items_lines = self.material_percent_lines_a
            grid = self.gridLayout_a
            if self.final_a:
                self.final_a.deleteLater()
                self.final_a = None
            if self.final_a_numb_label:
                self.final_a_numb_label.deleteLater()
                self.final_a_numb_label = None

        elif komponent == "B":
            items_type = self.material_b_types
            items = self.material_comboboxes_b
            items_lines = self.material_percent_lines_b
            grid = self.gridLayout_b
            if self.final_b:
                self.final_b.deleteLater()
                self.final_b = None
            if self.final_b_numb_label:
                self.final_b_numb_label.deleteLater()
                self.final_b_numb_label = None
        else:
            return None

        if items:
            items.pop(-1).deleteLater()
            items_lines.pop(-1).deleteLater()
            items_type.pop(-1).deleteLater()

            if items:
                final = QLabel("Итого")
                final_numb_label = QLabel()
                row_count = grid.count()
                grid.addWidget(
                    final, row_count + 1, 1, alignment=QtCore.Qt.AlignRight
                )
                grid.addWidget(
                    final_numb_label, row_count + 1, 2)
                if komponent == "A":
                    self.final_a = final
                    self.final_a_numb_label = final_numb_label
                    self.count_sum('A')
                else:
                    self.final_b = final
                    self.final_b_numb_label = final_numb_label
                    self.count_sum('B')
            else:
                self.hide_top(komponent)

    def add_A_line(self):
        self.add_line("A")

    def add_B_line(self):
        self.add_line("B")

    def del_A_line(self):
        self.del_line("A")

    def del_B_line(self):
        self.del_line("B")

    def normalise_func(self, komponent: str):
        if komponent == "A":
            items_lines = self.material_percent_lines_a
        if komponent == "B":
            items_lines = self.material_percent_lines_b

        def wrap():
            self.to_float(komponent)
            sum_all = 0
            for widget in items_lines:
                sum_all += float(widget.text())
            if sum_all:
                for widget in items_lines:
                    widget.setText(f"{round(float(widget.text()) / sum_all * 100, 2):.{2}f}")
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
                            widget.setText(
                                str(round(current_numb + (100 - sum_all), 2))
                            )
                            break
            self.count_sum(komponent)
        return wrap

    def add_material(self):
        if not self.add_material_window:
            self.add_material_window = AddMaterial(self)
        self.setEnabled(False)
        self.add_material_window.show()

    def update_materials(self):
        self.list_of_item_names = {
            material: get_all_material_of_one_type(material, self.db_name)
            for material in self.types_of_items
        }
        if self.material_to_add:

            for index, combobox in enumerate(self.material_comboboxes_a):
                if (
                    self.material_to_add[0]
                    == self.material_a_types[index].currentText()
                ):
                    combobox.addItem(self.material_to_add[1])

            for index, combobox in enumerate(self.material_comboboxes_b):
                if (
                    self.material_to_add[0]
                    == self.material_b_types[index].currentText()
                ):
                    combobox.addItems(self.material_to_add[1])

    def hide_top(self, komponent: str):
        if komponent == "A":
            self.label_3.hide()
            self.label_5.hide()
            self.normalise_A.hide()
        if komponent == "B":
            self.label_4.hide()
            self.label_6.hide()
            self.normalise_B.hide()

    def show_top(self, komponent: str):
        if komponent == "A":
            self.label_3.show()
            self.label_5.show()
            self.normalise_A.show()
        if komponent == "B":
            self.label_4.show()
            self.label_6.show()
            self.normalise_B.show()

    @staticmethod
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def count_sum(self, komponent: str):
        if komponent == "A":
            item_lines = self.material_percent_lines_a
        elif komponent == "B":
            item_lines = self.material_percent_lines_b
        else:
            return None

        total_sum = 0
        for widget in item_lines:
            try:
                numb = float(widget.text().replace(',', '.'))
            except Exception:
                numb = 0
                widget.setText('Error!')
            total_sum += numb

        total_sum = f"{total_sum:.{2}f}"

        if komponent == "A":
            self.final_a_numb_label.setText(f'{total_sum}')
        elif komponent == "B":
            self.final_b_numb_label.setText(f'{total_sum}')


class AddMaterial(QtWidgets.QMainWindow, uic.loadUiType("Add_material.ui")[0]):
    def __init__(self, main_window: MainWindow):
        super(AddMaterial, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.db_name = DB_NAME
        self.save_but.clicked.connect(self.add_material)
        self.mat_type.addItems(self.main_window.types_of_items)

    def add_material(self):

        mat_type = self.mat_type.currentText()
        name = self.mat_name.text().replace(" ", "")
        try:
            activity = float(self.mat_EW.text().replace(",", "."))
        except Exception as e:
            # TODO уведомить, что проблемы с EW
            activity = None
            pass
        tg_inf = self.tg_inf_type.currentText()
        a = self.koef_a.text()
        b = self.koef_b.text()

        add_material(
            self.db_name,
            mat_type,
            name,
            activity if activity else None,
            tg_inf,
            a if a else None,
            b if b else None,
        )

        self.main_window.material_to_add = (mat_type, name)

        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.setEnabled(True)
        self.main_window.update_materials()
        self.main_window.add_material_window = None
        a0.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
