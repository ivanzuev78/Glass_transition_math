import sys
from typing import Union

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

        # windows
        self.material_window = None
        self.tg_window = None
        self.tg_influence_window = None

        # Строка вещества, которое было добавлено.
        # Нужно для добавления в выпадающий список в рецептуре не меняя его
        self.material_to_add = None

        # Комбобоксы с типами материалов в рецептурах
        self.material_a_types = []
        self.material_b_types = []

        # Комбобоксы с материалами в рецептурах
        self.material_comboboxes_a = []
        self.material_comboboxes_b = []

        # Qlines с процентами в рецептурах
        self.material_percent_lines_a = []
        self.material_percent_lines_b = []

        # Qline со значением суммы в конце рецептуры
        self.final_a = None
        self.final_b = None

        # Qline "Итого" в конце рецептуры
        self.final_a_numb_label = None
        self.final_b_numb_label = None

        # Все типы материалов, которые есть в БД. Подтягиваются из БД
        self.types_of_items = get_all_material_types(self.db_name)
        # Словарь всех веществ. {Тип: Список материалов}
        self.list_of_item_names = {
            material: get_all_material_of_one_type(material, self.db_name)
            for material in self.types_of_items
        }

        # QSpacerItem в gridLayout для подпирания строк снизу
        self.gridLayout_a.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)
        self.gridLayout_b.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)

        # Подключаем кнопки
        self.add_A_but.clicked.connect(self.add_a_line)
        self.del_A_but.clicked.connect(self.del_a_line)
        self.add_B_but.clicked.connect(self.add_b_line)
        self.del_B_but.clicked.connect(self.del_b_line)
        self.debug_but.clicked.connect(self.debug)
        self.add_raw.clicked.connect(self.add_material_window)
        self.normalise_A.clicked.connect(self.normalise_func("A"))
        self.normalise_B.clicked.connect(self.normalise_func("B"))
        self.add_tg_but.clicked.connect(self.add_tg_window)
        self.add_tg_inf_but.clicked.connect(self.add_tg_inf_window)

        # Прячем верхушки рецептур, пока нет строк
        self.hide_top("A")
        self.hide_top("B")

    def debug(self):
        self.count_glass()
        self.debug_string.setText("Good")

    # Приводит все проценты в рецептуре к типу float и считает +-*/ если есть в строке
    def to_float(self, komponent: str):
        if komponent == "A":
            items_lines = self.material_percent_lines_a
        elif komponent == "B":
            items_lines = self.material_percent_lines_b
        else:
            return None
        numb: Union[str, float]
        for widget in items_lines:
            numb = widget.text().replace(",", ".")
            if len(numb.split("+")) > 1:
                splited_numb = numb.split("+")
                if all([i for i in map(self.isfloat, splited_numb)]):
                    numb = sum(map(float, splited_numb))
                elif self.isfloat(splited_numb[0]):
                    numb = float(splited_numb[0])
            elif len(numb.split("-")) > 1:
                splited_numb = numb.split("-")
                if all([i for i in map(self.isfloat, splited_numb)]):
                    numb = float(splited_numb[0]) - float(splited_numb[1])
                elif self.isfloat(splited_numb[0]):
                    numb = float(splited_numb[0])
            elif len(numb.split("*")) > 1:
                splited_numb = numb.split("*")
                if all([i for i in map(self.isfloat, splited_numb)]):
                    numb = float(splited_numb[0]) * float(splited_numb[1])
                elif self.isfloat(splited_numb[0]):
                    numb = float(splited_numb[0])
            elif len(numb.split("/")) > 1:
                splited_numb = numb.split("/")
                if all([i for i in map(self.isfloat, splited_numb)]):
                    numb = float(splited_numb[0]) / float(splited_numb[1])
                elif self.isfloat(splited_numb[0]):
                    numb = float(splited_numb[0])
            elif len(numb.split("\\")) > 1:
                splited_numb = numb.split("\\")
                if all([i for i in map(self.isfloat, splited_numb)]):
                    numb = float(splited_numb[0]) / float(splited_numb[1])
                elif self.isfloat(splited_numb[0]):
                    numb = float(splited_numb[0])

            if not self.isfloat(numb):
                numb = 0

            if float(numb) < 0:
                numb = 0
            widget.setText(f"{float(numb):.{2}f}")

    # Добавляет строку сырья в соответствующую рецептуру
    def add_line(self, komponent: str):
        final_label = QLabel("Итого")
        final_label_numb = QLabel("0.00")
        final_label_numb.setTextInteractionFlags(
            QtCore.Qt.LinksAccessibleByMouse
            | QtCore.Qt.TextSelectableByKeyboard
            | QtCore.Qt.TextSelectableByMouse
        )

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
        line.editingFinished.connect(lambda: self.to_float(komponent))
        line.editingFinished.connect(lambda: self.count_sum(komponent))

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

    # Меняет список сырья при смене типа в рецептуре
    def change_list_of_materials(self, material_combobox, material_type):
        def wrapper():
            material_combobox.clear()
            material_combobox.addItems(
                self.list_of_item_names[material_type.currentText()]
            )

        return wrapper

    # Удаляет последнюю строку в рецептуре
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
                grid.addWidget(final, row_count + 1, 1, alignment=QtCore.Qt.AlignRight)
                grid.addWidget(final_numb_label, row_count + 1, 2)
                if komponent == "A":
                    self.final_a = final
                    self.final_a_numb_label = final_numb_label
                    self.count_sum("A")
                else:
                    self.final_b = final
                    self.final_b_numb_label = final_numb_label
                    self.count_sum("B")
            else:
                self.hide_top(komponent)

    def add_a_line(self):
        self.add_line("A")

    def add_b_line(self):
        self.add_line("B")

    def del_a_line(self):
        self.del_line("A")

    def del_b_line(self):
        self.del_line("B")

    # Нормирует рецептуру
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
                    widget.setText(
                        f"{round(float(widget.text()) / sum_all * 100, 2):.{2}f}"
                    )
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

    # Вызывает окно для добавления сырья
    def add_material_window(self):
        if not self.material_window:
            self.material_window = AddMaterial(self)
        self.setEnabled(False)
        self.material_window.show()
        self.hide()

    # Вызывает окно для добавления температуры стеклования
    def add_tg_window(self):
        if not self.tg_window:
            self.tg_window = AddTg(self)
        self.setEnabled(False)
        self.tg_window.show()
        self.hide()

    # Вызывает окно для добавления влияния вещества на температуру стеклования
    def add_tg_inf_window(self):
        if not self.tg_influence_window:
            self.tg_influence_window = AddTgInfluence(self)
        self.setEnabled(False)
        self.hide()
        self.tg_influence_window.show()

    # Добавляет добавленный материал в выпадающий список в рецептурах, не меняя текущее значение
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

    # Прячет шапку рецептуры, когда нет компонентов
    def hide_top(self, komponent: str):
        if komponent == "A":
            self.label_3.hide()
            self.label_5.hide()
            self.normalise_A.hide()
        if komponent == "B":
            self.label_4.hide()
            self.label_6.hide()
            self.normalise_B.hide()

    # Отображает шапку рецептуры, когда есть компоненты
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

    # Считает сумму компонентов в рецептуре
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
                numb = float(widget.text().replace(",", "."))
            except Exception:
                numb = 0
                widget.setText("Error!")
            total_sum += numb

        total_sum = f"{total_sum:.{2}f}"

        if komponent == "A":
            self.final_a_numb_label.setText(f"{total_sum}")
        elif komponent == "B":
            self.final_b_numb_label.setText(f"{total_sum}")



    def count_glass(self):
        resin_names = []
        resin_values = []
        for index, widget in enumerate(self.material_comboboxes_a):
            if self.material_a_types[index].currentText() == 'Epoxy':
                resin_names.append(widget.currentText())
                resin_values.append(float(self.material_percent_lines_a[index].text()))


        print(resin_names)
        print(resin_values)
        print(normalize(np.array(resin_values)))












class AddMaterial(QtWidgets.QMainWindow, uic.loadUiType("Add_material.ui")[0]):
    def __init__(self, main_window: MainWindow):
        super(AddMaterial, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.db_name = DB_NAME

        self.save_but.clicked.connect(self.add_material)
        self.cancel_but.clicked.connect(self.close)
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

        add_material(
            self.db_name,
            mat_type,
            name,
            activity if activity else None,
        )

        self.main_window.material_to_add = (mat_type, name)

        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.setEnabled(True)
        self.main_window.update_materials()
        self.main_window.add_material_window = None
        self.main_window.show()
        a0.accept()


class AddTg(QtWidgets.QMainWindow, uic.loadUiType("Add_Tg.ui")[0]):
    def __init__(self, main_window: MainWindow):
        super(AddTg, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.db_name = DB_NAME

        self.epoxy_comboBox.addItems(self.main_window.list_of_item_names["Epoxy"])
        self.amine_comboBox.addItems(self.main_window.list_of_item_names["Amine"])

        self.save_but.clicked.connect(self.add_tg)
        self.cancel_but.clicked.connect(self.close)

    def add_tg(self):
        epoxy = self.epoxy_comboBox.currentText()
        amine = self.amine_comboBox.currentText()
        try:
            tg = float(self.tg_lineEdit.text())
        except Exception as e:
            self.error_lab.setText("Введите число")
            print(e)
            return None
        # TODO добавить проверку наличия этой пары значений и при наличии спросить про замену
        add_tg_base(epoxy, amine, tg, self.db_name)
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.setEnabled(True)
        self.main_window.show()
        a0.accept()


class AddTgInfluence(QtWidgets.QMainWindow, uic.loadUiType("Add_Tg_influence.ui")[0]):
    def __init__(self, main_window: MainWindow):
        super(AddTgInfluence, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.db_name = DB_NAME

        self.material_type_combobox.addItems(self.main_window.types_of_items)
        self.material_type_combobox.currentIndexChanged.connect(
            self.change_type_of_material
        )
        self.material_combobox.addItems(
            self.main_window.list_of_item_names[
                self.material_type_combobox.currentText()
            ]
        )
        self.cancel_but.clicked.connect(self.close)
        # TODO добавить логику сохранения и подключить кнопку

    def change_type_of_material(self):
        self.material_combobox.clear()
        self.material_combobox.addItems(
            self.main_window.list_of_item_names[
                self.material_type_combobox.currentText()
            ]
        )

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.setEnabled(True)
        self.main_window.show()
        a0.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
