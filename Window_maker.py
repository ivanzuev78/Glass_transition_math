import sys
from typing import Union
from collections import defaultdict

from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import *

from math import inf, fabs
from Materials import *
from Sintez_windows import SintezWindow, ChoosePairReactWindow

DB_NAME = "material.db"


class MainWindow(QtWidgets.QMainWindow, uic.loadUiType("Main_window.ui")[0]):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setupUi(self)

        self.db_name = DB_NAME

        self.__current_tg = None
        self.__a_ew = None
        self.__b_ew = None
        self.__mass_ratio = None
        self.sum_a = 0
        self.sum_b = 0

        # windows
        self.material_window = None
        self.tg_window = None
        self.tg_influence_window = None
        self.tg_view_window = None

        self.a_receipt_window: Union[SintezWindow, None] = None
        self.b_receipt_window: Union[SintezWindow, None] = None

        # TODO добавить сброс при изменении компонентов
        self.pair_react_window = None


        # Строка вещества, которое было добавлено.
        # Нужно для добавления в выпадающий список в рецептуре не меняя его
        self.material_to_add = None

        # Комбобоксы с типами материалов в рецептурах
        self.material_a_types = []
        self.material_b_types = []

        # Комбобоксы с материалами в рецептурах
        self.material_comboboxes_a = []
        self.material_comboboxes_b = []

        # QLines с процентами в рецептурах
        self.material_percent_lines_a = []
        self.material_percent_lines_b = []

        # Чекбоксы для фиксации процентов при нормировке
        self.lock_checkboxies_a = []
        self.lock_checkboxies_b = []

        # QLine со значением суммы в конце рецептуры
        self.final_a = None
        self.final_b = None

        # QLine "Итого" в конце рецептуры
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
        self.tg_view_but.clicked.connect(self.show_tg_table)
        self.a_recept_but.clicked.connect(self.add_receipt_window('A'))
        self.b_recept_but.clicked.connect(self.add_receipt_window('B'))

        pixmap = QPixmap("lock.png")
        self.label_lock_a.setPixmap(pixmap)
        self.label_lock_b.setPixmap(pixmap)

        # Прячем верхушки рецептур, пока нет строк
        self.hide_top("A")
        self.hide_top("B")

    def debug(self):
        self.count_glass()
        # self.enable_recept("A")
        # self.add_choose_pair_react_window()
        self.debug_string.setText("Good")

    @property
    def current_tg(self):
        return self.__current_tg

    @current_tg.setter
    def current_tg(self, value):
        self.__current_tg = value
        self.tg_label.setText(f"Стеклование {value}°C")

    def add_receipt_window(self, komponent):

        def wrapper():
            if komponent == "A":
                if not self.a_receipt_window:
                    self.a_receipt_window = SintezWindow(self, "A")
                self.a_receipt_window.show()
                self.disable_recept("A")
            elif komponent == "B":
                if not self.b_receipt_window:
                    self.b_receipt_window = SintezWindow(self, "B")
                self.b_receipt_window.show()
                self.disable_recept("B")
            else:
                return None

        return wrapper

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
            lock_checkboxies = self.lock_checkboxies_a
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

            lock_checkboxies = self.lock_checkboxies_b
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
        row_count = grid.count()

        check = QCheckBox()
        lock_checkboxies.append(check)
        items_type.append(materia_typel_combobox)
        items.append(material_combobox)
        items_lines.append(line)

        grid.addWidget(materia_typel_combobox, row_count + 1, 0)
        grid.addWidget(material_combobox, row_count + 1, 1)
        grid.addWidget(line, row_count + 1, 2)
        grid.addWidget(check, row_count + 1, 3)

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
            lock_check_boxies = self.lock_checkboxies_a
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
            lock_check_boxies = self.lock_checkboxies_b
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
            lock_check_boxies.pop(-1).deleteLater()

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

    def disable_recept(self, komponent):
        if komponent == "A":
            for i in range(len(self.material_comboboxes_a)):
                self.material_comboboxes_a[i].setEnabled(False)
                self.material_percent_lines_a[i].setEnabled(False)
                self.material_a_types[i].setEnabled(False)
                self.lock_checkboxies_a[i].setEnabled(False)
                self.normalise_A.setEnabled(False)

        elif komponent == "B":
            for i in range(len(self.material_comboboxes_b)):
                self.material_comboboxes_b[i].setEnabled(False)
                self.material_percent_lines_b[i].setEnabled(False)
                self.material_b_types[i].setEnabled(False)
                self.lock_checkboxies_b[i].setEnabled(False)
                self.normalise_B.setEnabled(False)

    def enable_recept(self, komponent):
        if komponent == "A":
            for i in range(len(self.material_comboboxes_a)):
                self.material_comboboxes_a[i].setEnabled(True)
                self.material_percent_lines_a[i].setEnabled(True)
                self.material_a_types[i].setEnabled(True)
                self.lock_checkboxies_a[i].setEnabled(True)
                self.normalise_A.setEnabled(True)

        elif komponent == "B":
            for i in range(len(self.material_comboboxes_b)):
                self.material_comboboxes_b[i].setEnabled(True)
                self.material_percent_lines_b[i].setEnabled(True)
                self.material_b_types[i].setEnabled(True)
                self.lock_checkboxies_b[i].setEnabled(True)
                self.normalise_B.setEnabled(True)

    # Нормирует рецептуру
    def normalise_func(self, komponent: str):
        if komponent == "A":
            items_lines = self.material_percent_lines_a
            lock_checkbox = self.lock_checkboxies_a

        if komponent == "B":
            items_lines = self.material_percent_lines_b
            lock_checkbox = self.lock_checkboxies_b

        def wrap():

            self.to_float(komponent)
            sum_all = 0
            total_sum_left = 100
            for index, widget in enumerate(items_lines):

                if lock_checkbox[index].isChecked():
                    total_sum_left -= float(widget.text())
                    continue
                sum_all += float(widget.text())
            if sum_all:
                for index, widget in enumerate(items_lines):
                    if lock_checkbox[index].isChecked():
                        continue
                    widget.setText(
                        f"{round(float(widget.text()) / sum_all * total_sum_left, 2):.{2}f}"
                    )
                sum_all = 0
                sum_all_without_last = 0
                for index, widget in enumerate(items_lines):
                    if lock_checkbox[index].isChecked():
                        continue
                    sum_all += float(widget.text())
                    if widget is items_lines[-1]:
                        break
                    sum_all_without_last += float(widget.text())
                if sum_all != 100:
                    for index, widget in reversed(list(enumerate(items_lines))):
                        current_numb = float(widget.text())
                        if current_numb != 0 and not lock_checkbox[index].isChecked():
                            widget.setText(
                                f"{round(current_numb + (total_sum_left - sum_all), 2):.{2}f}"
                            )
                            break
            self.count_sum(komponent)

            self.count_ew(komponent)
            self.count_mass_ratio()

        return wrap

    # Вызывает окно для добавления сырья
    def add_material_window(self):
        if not self.material_window:
            self.material_window = AddMaterial(self)
        self.setEnabled(False)
        self.material_window.show()
        self.hide()

    def count_mass_ratio(self):
        a = self.a_ew
        b = self.ew_b
        print(a, b)
        if a and b:
            if a * b < 0:
                self.mass_ratio = - a / b
                return None
        self.mass_ratio = 0

    def add_choose_pair_react_window(self):

        self.pair_react_window = ChoosePairReactWindow(self, self.get_all_pairs_react('A'),
                                                       self.get_all_pairs_react('B'))
        self.pair_react_window.show()

    def get_all_pairs_react(self, komponent):
        if komponent == "A":
            material_types = self.material_a_types
            material_comboboxes = self.material_comboboxes_a
        elif komponent == "B":
            material_types = self.material_b_types
            material_comboboxes = self.material_comboboxes_b
        else:
            return None

        epoxies = []
        amines = []
        for mat_type, name in zip(material_types, material_comboboxes):

            mat_type = mat_type.currentText()
            name = name.currentText()
            if mat_type == 'Epoxy':
                epoxies.append(name)
            elif mat_type == 'Amine':
                amines.append(name)

        all_pairs = [(epoxy, amine) for epoxy in epoxies for amine in amines]

        return all_pairs


    @property
    def mass_ratio(self):
        return self.__mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value):
        self.__mass_ratio = value
        if value >= 1:
            numb_a = round(value, 2)
            numb_b = 1
            self.mass_ratio_label.setText(f"Соотношение по массе\n{numb_a} : {numb_b}")
        elif 0 < value < 1:
            numb_a = 1
            numb_b = round(1 / value, 2)
            self.mass_ratio_label.setText(f"Соотношение по массе\n{numb_a} : {numb_b}")
        else:
            self.mass_ratio_label.setText(f"Продукты не реагируют")

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

    def add_tg_view(self):
        if not self.tg_view_window:
            self.tg_view_window = TgViewWindow(self)
        self.setEnabled(False)
        self.hide()
        self.tg_view_window.show()

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
                    combobox.addItem(self.material_to_add[1])

    def set_percents_from_recept_window(self, komponent, percents):
        if komponent == "A":
            material_percent_lines = self.material_percent_lines_a
        elif komponent == "B":
            material_percent_lines = self.material_percent_lines_b
        else:
            return None

        for line, percent in zip(material_percent_lines, percents):
            line.setText(str(percent))
        self.count_glass()
        self.count_ew(komponent)

    # Прячет шапку рецептуры, когда нет компонентов
    def hide_top(self, komponent: str):
        if komponent == "A":
            self.label_3.hide()
            self.label_5.hide()
            self.normalise_A.hide()
            self.label_lock_a.hide()
        if komponent == "B":
            self.label_4.hide()
            self.label_6.hide()
            self.normalise_B.hide()
            self.label_lock_b.hide()

    # Отображает шапку рецептуры, когда есть компоненты
    def show_top(self, komponent: str):
        if komponent == "A":
            self.label_3.show()
            self.label_5.show()
            self.normalise_A.show()
            self.label_lock_a.show()

        if komponent == "B":
            self.label_4.show()
            self.label_6.show()
            self.normalise_B.show()
            self.label_lock_b.show()

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

        # if 99.9999 < total_sum < 100.0001:
        #     total_sum = 100
        # total_sum_str = f"{total_sum:.{2}f}"

        if komponent == "A" and self.final_a_numb_label:
            self.sum_a = total_sum
            self.final_a_numb_label.setText(f"{round(total_sum, 2)}")
        elif komponent == "B" and self.final_b_numb_label:
            self.sum_b = total_sum
            self.final_b_numb_label.setText(f"{round(total_sum, 2)}")

    def show_tg_table(self):
        df = get_tg_df(self.db_name)
        headers = df.columns.values.tolist()
        rows = df.index.tolist()

        table = QTableWidget()
        table.sizeHint()
        table.adjustSize()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        table.setVerticalHeaderLabels(rows)
        # layout = QGridLayout()
        # layout.addWidget(table)
        # layout.geometry()
        # self.layout().addWidget(table)

        for i, row in enumerate(df.iterrows()):
            # Добавление строки
            for j in range(table.columnCount()):
                table.setItem(i, j, QTableWidgetItem(str(row[1][j])))
        table.show()
        self.table = table
        pass

    def count_ew(self, komponent):
        resin_names = []
        resin_values = []
        amine_names = []
        amine_values = []

        if komponent == "A":
            material_comboboxes = self.material_comboboxes_a
            material_types = self.material_a_types
            material_percent_lines = self.material_percent_lines_a
        elif komponent == "B":
            material_comboboxes = self.material_comboboxes_b
            material_types = self.material_b_types
            material_percent_lines = self.material_percent_lines_b
        else:
            return None

        for index, widget in enumerate(material_comboboxes):
            if material_types[index].currentText() == "Amine":
                amine_names.append(widget.currentText())
                amine_values.append(float(material_percent_lines[index].text()))
            elif material_types[index].currentText() == "Epoxy":
                resin_names.append(widget.currentText())
                resin_values.append(float(material_percent_lines[index].text()))

        resin_eew = np.array(
            [
                i
                for i in map(
                    get_ew_by_name,
                    resin_names,
                    ["Epoxy" for _ in range(len(resin_names))],
                    [self.db_name for _ in range(len(resin_names))],
                )
            ]
        )
        amine_ahew = np.array(
            [
                i
                for i in map(
                    get_ew_by_name,
                    amine_names,
                    ["Amine" for _ in range(len(amine_names))],
                    [self.db_name for _ in range(len(amine_names))],
                )
            ]
        )

        resin_values = np.array(resin_values) / 100
        amine_values = np.array(amine_values) / 100

        amine_equivalents = amine_values / amine_ahew
        epoxy_equivalents = resin_values / resin_eew
        ew = 1 / (epoxy_equivalents.sum() - amine_equivalents.sum())
        if ew == inf:
            ew = 0

        if komponent == "A":
            self.a_ew = ew
        elif komponent == "B":
            self.ew_b = ew

        # self.set_ew(komponent)

    def set_ew(self, komponent):
        if komponent == "A":
            if self.a_ew > 0:
                self.eew_label.setText(f"EEW = {round(self.a_ew, 2)}")
            elif self.a_ew < 0:
                self.eew_label.setText(f"AHEW = {-round(self.a_ew, 2)}")
            else:
                self.eew_label.setText(f"No EW")
        if komponent == "B":
            if self.b_ew > 0:
                self.ahew_label.setText(f"EEW = {round(self.b_ew, 2)}")
            elif self.b_ew < 0:
                self.ahew_label.setText(f"AHEW = {-round(self.b_ew, 2)}")
            else:
                self.ahew_label.setText(f"No EW")

    @property
    def a_ew(self):
        return self._a_ew

    @a_ew.setter
    def a_ew(self, value):
        if value == self.__a_ew:
            return None
        if value > 0:
            self.eew_label.setText("EEW  " + str(round(value, 2)))
        elif value == 0:
            self.eew_label.setText("No EW")
        else:
            self.eew_label.setText("AHEW  " + str(-round(value, 2)))
        self.__a_ew = value
        if self.a_receipt_window:
            self.a_receipt_window.EW = value
        self.count_mass_ratio()

    @a_ew.getter
    def a_ew(self):
        return self.__a_ew

    @property
    def ew_b(self):
        return self.__b_ew

    @ew_b.setter
    def ew_b(self, value):
        if value == self.__b_ew:
            return None
        if value > 0:
            self.ahew_label.setText("EEW  " + str(round(value, 2)))
        elif value == 0:
            self.ahew_label.setText("No EW")
        else:
            self.ahew_label.setText("AHEW  " + str(-round(value, 2)))
        self.__b_ew = value
        if self.b_receipt_window:
            self.b_receipt_window.EW = value
        self.count_mass_ratio()

    @ew_b.getter
    def ew_b(self):
        return self.__b_ew

    def count_glass(self):
        # Вспомогательная функция, которая учитывает ступенчатый синтез
        def count_reaction_in_komponent(names_list, eq_list, pair_react):

            # TODO Реализовать интерфейс для выбора взаимодействующий веществ + проверка, что все прореагировали
            # pair_react = [('KER-828', 'ИФДА'), ('KER-828', 'MXDA')]
            # на первом месте тот, кто прореагирует полностью
            # если наоборот, то поменять нужно
            # pair_react = [(i[1], i[0]) for i in pair_react]

            if not pair_react:
                return eq_list, []
            dict_react_index = defaultdict(list)
            pair_react_index = [(names_list.index(epoxy), names_list.index(amine)) for epoxy, amine in pair_react]
            dict_react_eq = defaultdict(list)

            # Здесь количество эквивалентов прореагировавших пар
            result_eq_table = []

            for epoxy, amine in pair_react_index:
                dict_react_index[epoxy].append(amine)
                dict_react_eq[epoxy].append(eq_list[amine])

            for epoxy in dict_react_eq:
                if sum(dict_react_eq[epoxy]) == 0:
                    dict_react_eq[epoxy] = [0 for amine in dict_react_eq[epoxy]]
                else:
                    dict_react_eq[epoxy] = [amine / sum(dict_react_eq[epoxy]) for amine in dict_react_eq[epoxy]]

            for epoxy_index in dict_react_index:
                for amine_index, amine_percent in zip(dict_react_index[epoxy_index], dict_react_eq[epoxy_index]):
                    eq_reacted = (names_list[epoxy_index], names_list[amine_index], eq_list[epoxy_index]*amine_percent)
                    eq_list[amine_index] += eq_list[epoxy_index]*amine_percent
                    result_eq_table.append(eq_reacted)
                eq_list[epoxy_index] = 0

            return eq_list, result_eq_table

        if not (self.a_ew and self.ew_b):
            self.tg_label.setText('Стеклование отсутствует')
            # TODO прописать, что нет одного из компонентов в строку со стеклом

            return None

        if self.a_ew * self.ew_b > 0:
            self.tg_label.setText('Стеклование отсутствует')
            # TODO прописать, что продукты не реагируют в строку со стеклом
            return None

        # Получаем все названия и % эпоксидки в Компоненте А
        a_types = []
        a_names = []
        a_values = []
        a_eq = []
        for index, widget in enumerate(self.material_comboboxes_a):
            mat_type = self.material_a_types[index].currentText()
            mat_name = widget.currentText()
            percent = float(self.material_percent_lines_a[index].text()) / 100
            ew = get_ew_by_name(mat_name, mat_type, self.db_name)
            if ew:
                eq = percent / ew * self.mass_ratio
                if mat_type == 'Amine':
                    eq = -eq
            else:
                eq = 0
            a_types.append(mat_type)
            a_names.append(mat_name)
            a_values.append(percent)
            a_eq.append(eq)

        # Получаем все названия и % эпоксидки в Компоненте B
        b_types = []
        b_names = []
        b_values = []
        b_eq = []
        for index, widget in enumerate(self.material_comboboxes_b):
            mat_type = self.material_b_types[index].currentText()
            mat_name = widget.currentText()
            percent = float(self.material_percent_lines_b[index].text()) / 100
            ew = get_ew_by_name(mat_name, mat_type, self.db_name)
            if ew:
                eq = percent / ew
                if mat_type == 'Amine':
                    eq = -eq
            else:
                eq = 0
            b_types.append(mat_type)
            b_names.append(mat_name)
            b_values.append(percent)
            b_eq.append(eq)

        total_eq = fabs(sum(a_eq))
        print('total_eq', total_eq)

        if not self.pair_react_window:
            self.pair_react_window = ChoosePairReactWindow(self, self.get_all_pairs_react('A'),
                                                             self.get_all_pairs_react('B'))

        a = self.pair_react_window.get_react_pairs('A')
        b = self.pair_react_window.get_react_pairs('B')
        if sum(a_eq) > 0:
            a = [(i[1], i[0]) for i in a]
        if sum(b_eq) > 0:
            b = [(i[1], i[0]) for i in b]

        print('a_eq до обработки', a_eq)
        # TODO необходимо передать списки со взаимодействиями
        a_eq, a_result_eq_table = count_reaction_in_komponent(a_names, a_eq, a)
        b_eq, b_result_eq_table = count_reaction_in_komponent(b_names, b_eq, b)
        print('a_eq после обработки', a_eq)
        print('a_result_eq_table', a_result_eq_table)
        print('b_result_eq_table', b_result_eq_table)

        a_names_only_react = []
        a_eq_only_react = []
        a_type = None
        if sum(a_eq) > 0:
            a_type = 'Epoxy'
            for mat_type, name, eq in zip(a_types, a_names, a_eq):
                if mat_type == 'Epoxy':
                    a_names_only_react.append(name)
                    a_eq_only_react.append(eq)
        elif sum(a_eq) < 0:
            a_type = 'Amine'
            for mat_type, name, eq in zip(a_types, a_names, a_eq):
                if mat_type == 'Amine':
                    a_names_only_react.append(name)
                    a_eq_only_react.append(eq)

        print('a_names_only_react', a_names_only_react)
        print('a_eq_only_react', a_eq_only_react)
        print('a_type', a_type)


        b_names_only_react = []
        b_eq_only_react = []
        b_type = None
        if sum(b_eq) > 0:
            b_type = 'Epoxy'
            for mat_type, name, eq in zip(b_types, b_names, b_eq):
                if mat_type == 'Epoxy':
                    b_names_only_react.append(name)
                    b_eq_only_react.append(eq)
        elif sum(b_eq) < 0:
            b_type = 'Amine'
            for mat_type, name, eq in zip(b_types, b_names, b_eq):
                if mat_type == 'Amine':
                    b_names_only_react.append(name)
                    b_eq_only_react.append(eq)

        print('b_names_only_react', b_names_only_react)
        print('b_eq_only_react', b_eq_only_react)
        print('b_type', b_type)

        if a_type == b_type:
            return None

        a_eq_only_react_percent = normalize(np.array(a_eq_only_react))
        b_eq_only_react_percent = normalize(np.array(b_eq_only_react))

        print('a_eq_only_react_percent', a_eq_only_react_percent)
        print('b_eq_only_react_percent', b_eq_only_react_percent)

        # Получаем матрицу процентов пар
        percent_matrix = np.outer(a_eq_only_react_percent, b_eq_only_react_percent)

        print('percent_matrix', percent_matrix)

        eq_matrix = percent_matrix * total_eq
        print('eq_matrix sum', eq_matrix.sum())

        # Получаем датафрейм процентов пар
        df_percent_matrix = pd.DataFrame(
            eq_matrix,
            index=a_names_only_react,
            columns=b_names_only_react,

        )


        if a_type == 'Amine':
            df_percent_matrix = df_percent_matrix.T

            for pair in a_result_eq_table:
                if pair[0] not in df_percent_matrix.index.tolist():
                    df_percent_matrix.loc[pair[0]] = [0 for _ in range(len(df_percent_matrix.columns.values.tolist()))]
                    df_percent_matrix[pair[1]][pair[0]] += pair[2]

        else:
            for pair in a_result_eq_table:
                if pair[0] not in df_percent_matrix.columns.values.tolist():
                    df_percent_matrix[pair[0]] = [0 for _ in range(len(df_percent_matrix.index.tolist()))]
                    df_percent_matrix[pair[0]][pair[1]] += pair[2]

        if b_type == 'Amine':

            for pair in b_result_eq_table:
                if pair[0] not in df_percent_matrix.index.tolist():
                    df_percent_matrix.loc[pair[0]] = [0 for _ in range(len(df_percent_matrix.columns.values.tolist()))]
                    df_percent_matrix[pair[1]][pair[0]] += pair[2]

        else:
            for pair in b_result_eq_table:
                if pair[0] not in df_percent_matrix.columns.values.tolist():
                    df_percent_matrix[pair[0]] = [0 for _ in range(len(df_percent_matrix.index.tolist()))]
                    df_percent_matrix[pair[0]][pair[1]] += pair[2]

        print(df_percent_matrix)

        epoxy_names_list = df_percent_matrix.index.tolist()
        amine_names_list = df_percent_matrix.columns.values.tolist()

        normalized_matrix = normalize(np.array(df_percent_matrix))


        print('-----------------')
        normalized_matrix_df = pd.DataFrame(
            normalized_matrix,
            index=epoxy_names_list,
            columns=amine_names_list,
        )
        print(normalized_matrix_df)
        print(normalized_matrix.sum())


        tg_df = get_tg_df("material.db")

        # Получаем все пары, которые не имеют стекла
        all_pairs_na = []
        for name in tg_df:
            a = tg_df[tg_df[name].isna()]
            par = [(resin, name) for resin in list(a.index)]
            all_pairs_na += par

        current_pairs = [
            (resin, amine) for resin in a_names_only_react for amine in b_names_only_react
        ]

        current_pairs_without_tg = [
            pair for pair in current_pairs if pair in all_pairs_na
        ]
        # TODO реализовать обработку отсутствующих пар стёкол
        # print(sovpadenie)

        # дропаем неиспользуемые колонки и строки стеклования
        for name in tg_df:
            if name not in amine_names_list + epoxy_names_list:
                tg_df = tg_df.drop(name, 1)
        for name in tg_df.index:
            if name not in epoxy_names_list + amine_names_list:
                tg_df = tg_df.drop(name)

        # if a_type == 'Amine':
        #     tg_df = tg_df.T
        # Сортируем колонки и строки в соответствии с матрицей процентов

        tg_df = tg_df[df_percent_matrix.columns.values.tolist()]
        tg_df = tg_df.T
        tg_df = tg_df[df_percent_matrix.index.tolist()].T

        total_tg = np.array(tg_df) * normalized_matrix
        total_tg = round(total_tg.sum(), 1)

        self.current_tg = total_tg


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


class TgViewWindow(QtWidgets.QMainWindow, uic.loadUiType("glass_view.ui")[0]):
    def __init__(self, main_window: MainWindow):
        super(TgViewWindow, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.db_name = DB_NAME
        self.fill_table()

    def fill_table(self):

        df = get_tg_df(self.db_name)
        headers = df.columns.values.tolist()
        rows = df.index.tolist()

        table = QTableWidget()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.setRowCount(len(rows))
        table.setVerticalHeaderLabels(rows)
        layout = QGridLayout()
        layout.addWidget(table)
        layout.geometry()
        # self.layout().addWidget(table)

        for i, row in enumerate(df.iterrows()):
            # Добавление строки
            for j in range(table.columnCount()):
                table.setItem(i, j, QTableWidgetItem(str(row[1][j])))
        table.show()
        pass

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.setEnabled(True)
        self.main_window.show()
        a0.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    form = MainWindow()
    form.show()
    app.exec_()
