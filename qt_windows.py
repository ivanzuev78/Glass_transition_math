from typing import Union

from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush
from PyQt5.QtWidgets import QLabel, QComboBox, QLineEdit, QCheckBox, QSpacerItem

from new_material_classes import Material
from old_version.Materials import get_all_material_types, get_all_material_of_one_type

DB_NAME = "material.db"
# DB_NAME = "material_for_test.db"


class MyMainWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/Main_window.ui")[0]):
    def __init__(self, db_name=DB_NAME):
        super(MyMainWindow, self).__init__()
        self.setupUi(self)

        self.db_name = db_name

        oImage = QImage("fon.jpg")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))
        self.setPalette(palette)

        self.button_list = [
            self.a_recept_but,
            self.b_recept_but,
            self.b_recept_but,
            self.debug_but,
            self.normalise_A,
            self.normalise_B,
            self.update_but,
            self.font_up_but,
            self.font_down_but,
            self.radioButton_A,
            self.radioButton_B,
        ]
        self.big_button_list = [
            self.add_A_but,
            self.add_B_but,
            self.del_A_but,
            self.del_B_but,
        ]
        self.all_labels = [
            self.mass_ratio_label,
            self.tg_main_label,
            self.mass_ratio_label_2,
            self.label_3,
            self.label_4,
            self.label_5,
            self.label_6,
            self.label_7,
            self.label_8,
            self.eew_label,
            self.ahew_label,
            self.extra_ew_label,
            self.sintez_pair_label,
            self.debug_string,
            self.lineEdit_name_a,
            self.lineEdit_name_b,
            self.lineEdit_sintez_mass,
            self.tg_cor_label,
            self.tg_extra_label,
            self.extra_ratio_line,
        ]
        self.all_big_labels = [self.label, self.label_2]
        self.font_size = 10
        self.font_size_big = 15

        # QSpacerItem в gridLayout для подпирания строк снизу
        self.gridLayout_a.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)
        self.gridLayout_b.addItem(QSpacerItem(100, 100), 100, 0, 100, 2)

        with open("style.css", "r") as f:
            self.style, self.style_combobox = f.read().split("$split$")
        self.set_bottom_styles()

        self.types_of_items = get_all_material_types(self.db_name)
        self.list_of_item_names = {
            material: get_all_material_of_one_type(material, self.db_name)
            for material in self.types_of_items
        }
        # QLine со значением суммы в конце рецептуры
        self.final_a = None
        self.final_b = None
        self.final_a_numb_label = None
        self.final_b_numb_label = None

        self.hide_top("A")
        self.hide_top("B")

        # Контейнеры для хранения строк
        self.material_a_types = []
        self.material_b_types = []
        self.material_comboboxes_a = []
        self.material_comboboxes_b = []
        self.material_percent_lines_a = []
        self.material_percent_lines_b = []
        self.lock_checkboxies_a = []
        self.lock_checkboxies_b = []
        self.material_list_a = []
        self.material_list_b = []

        # Подключаем кнопки
        # self.a_recept_but.clicked.connect(self.add_receipt_window("A"))
        # self.b_recept_but.clicked.connect(self.add_receipt_window("B"))

        self.add_A_but.clicked.connect(self.add_a_line)
        self.add_B_but.clicked.connect(self.add_b_line)
        self.del_A_but.clicked.connect(self.del_a_line)
        self.del_B_but.clicked.connect(self.del_b_line)

    def set_bottom_styles(self):
        for widget in self.button_list + self.big_button_list:
            widget.setStyleSheet(self.style)

    def hide_top(self, komponent: str):
        if komponent == "A":
            self.label_3.hide()
            self.label_5.hide()
            self.normalise_A.hide()
            self.label_lock_a.hide()
        elif komponent == "B":
            self.label_4.hide()
            self.label_6.hide()
            self.normalise_B.hide()
            self.label_lock_b.hide()

    def add_line(self, component: str) -> None:
        final_label = QLabel("Итого")
        final_label.setStyleSheet(self.style)
        final_label.setFont((QtGui.QFont("Times New Roman", self.font_size)))
        final_label_numb = QLabel("0.00")
        final_label_numb.setStyleSheet(self.style)
        final_label_numb.setFont((QtGui.QFont("Times New Roman", self.font_size)))

        final_label_numb.setTextInteractionFlags(
            QtCore.Qt.LinksAccessibleByMouse
            | QtCore.Qt.TextSelectableByKeyboard
            | QtCore.Qt.TextSelectableByMouse
        )

        if component == "A":
            items_type = self.material_a_types
            items = self.material_comboboxes_a
            items_lines = self.material_percent_lines_a
            grid = self.gridLayout_a
            lock_checkboxes = self.lock_checkboxies_a
            if self.final_a:
                self.final_a.deleteLater()
            self.final_a = final_label
            if self.final_a_numb_label:
                self.final_a_numb_label.deleteLater()
            self.final_a_numb_label = final_label_numb

        elif component == "B":
            items_type = self.material_b_types
            items = self.material_comboboxes_b
            items_lines = self.material_percent_lines_b
            grid = self.gridLayout_b

            lock_checkboxes = self.lock_checkboxies_b
            if self.final_b:
                self.final_b.deleteLater()
            self.final_b = final_label
            if self.final_b_numb_label:
                self.final_b_numb_label.deleteLater()
            self.final_b_numb_label = final_label_numb
        else:
            return None

        self.show_top(component)

        row_count = len(items)

        material_combobox = QComboBox()
        material_combobox.addItems(self.list_of_item_names["None"])
        material_combobox.setFixedWidth(120)
        material_combobox.setFixedHeight(20)
        material_combobox.setStyleSheet(self.style_combobox)
        material_combobox.setFont((QtGui.QFont("Times New Roman", self.font_size)))

        materia_typel_combobox = QComboBox()
        materia_typel_combobox.addItems(self.types_of_items)
        materia_typel_combobox.setFixedWidth(60)

        # TODO Добавить функцию, которая передает тип и название материала в Material
        materia_typel_combobox.currentIndexChanged.connect(
            self.change_list_of_materials(
                material_combobox, materia_typel_combobox, component
            )
        )

        materia_typel_combobox.setFixedHeight(20)
        materia_typel_combobox.setFont(QtGui.QFont("Times New Roman", self.font_size))
        materia_typel_combobox.setStyleSheet(self.style_combobox)

        percent_line = QLineEdit()
        percent_line.setText("0.00")
        percent_line.setFixedWidth(65)
        percent_line.setFont((QtGui.QFont("Times New Roman", self.font_size)))

        percent_line.editingFinished.connect(lambda: self.to_float(component))

        # TODO Добавить функцию, которая передает проценты в Material
        # percent_line.textChanged.connect(self.update_percent(row_count, component))

        check = QCheckBox()
        lock_checkboxes.append(check)
        items_type.append(materia_typel_combobox)
        items.append(material_combobox)
        items_lines.append(percent_line)

        grid.addWidget(materia_typel_combobox, row_count + 1, 0)
        grid.addWidget(material_combobox, row_count + 1, 1)
        grid.addWidget(percent_line, row_count + 1, 2)
        grid.addWidget(check, row_count + 1, 3)

        grid.addWidget(final_label, row_count + 2, 1, alignment=QtCore.Qt.AlignRight)
        grid.addWidget(final_label_numb, row_count + 2, 2)

    def add_a_line(self) -> None:
        self.add_line("A")

    def add_b_line(self) -> None:
        self.add_line("B")

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

    # Удаляет последнюю строку в рецептуре
    def del_line(self, komponent: str) -> None:

        if komponent == "A":
            items_type = self.material_a_types
            items = self.material_comboboxes_a
            items_lines = self.material_percent_lines_a
            grid = self.gridLayout_a
            lock_check_boxes = self.lock_checkboxies_a
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
            lock_check_boxes = self.lock_checkboxies_b
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
            lock_check_boxes.pop(-1).deleteLater()

            if items:
                final_label = QLabel("Итого")
                final_label.setStyleSheet(self.style)
                final_label.setFont((QtGui.QFont("Times New Roman", self.font_size)))
                final_label_numb = QLabel()
                final_label_numb.setStyleSheet(self.style)
                final_label_numb.setFont(
                    (QtGui.QFont("Times New Roman", self.font_size))
                )

                row_count = grid.count()
                grid.addWidget(
                    final_label, row_count + 1, 1, alignment=QtCore.Qt.AlignRight
                )
                grid.addWidget(final_label_numb, row_count + 1, 2)
                if komponent == "A":
                    self.final_a = final_label
                    self.final_a_numb_label = final_label_numb
                    # self.count_sum("A")
                else:
                    self.final_b = final_label
                    self.final_b_numb_label = final_label_numb
                    # self.count_sum("B")
            else:
                self.hide_top(komponent)

    def del_a_line(self) -> None:
        self.del_line("A")

    def del_b_line(self) -> None:
        self.del_line("B")

    @staticmethod
    def isfloat(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    # Приводит все проценты в рецептуре к типу float и считает +-*/ если есть в строке
    def to_float(self, komponent: str) -> None:
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
                split_numb = numb.split("+")
                if all([i for i in map(self.isfloat, split_numb)]):
                    numb = sum(map(float, split_numb))
                elif self.isfloat(split_numb[0]):
                    numb = float(split_numb[0])
            elif len(numb.split("-")) > 1:
                split_numb = numb.split("-")
                if all([i for i in map(self.isfloat, split_numb)]):
                    numb = float(split_numb[0]) - float(split_numb[1])
                elif self.isfloat(split_numb[0]):
                    numb = float(split_numb[0])
            elif len(numb.split("*")) > 1:
                split_numb = numb.split("*")
                if all([i for i in map(self.isfloat, split_numb)]):
                    numb = float(split_numb[0]) * float(split_numb[1])
                elif self.isfloat(split_numb[0]):
                    numb = float(split_numb[0])
            elif len(numb.split("/")) > 1:
                split_numb = numb.split("/")
                if all([i for i in map(self.isfloat, split_numb)]):
                    numb = float(split_numb[0]) / float(split_numb[1])
                elif self.isfloat(split_numb[0]):
                    numb = float(split_numb[0])
            elif len(numb.split("\\")) > 1:
                split_numb = numb.split("\\")
                if all([i for i in map(self.isfloat, split_numb)]):
                    numb = float(split_numb[0]) / float(split_numb[1])
                elif self.isfloat(split_numb[0]):
                    numb = float(split_numb[0])

            if not self.isfloat(numb):
                numb = 0

            if float(numb) < 0:
                numb = 0
            widget.setText(f"{float(numb):.{2}f}")

    # Меняет список сырья при смене типа в рецептуре
    def change_list_of_materials(
        self, material_combobox, material_type, component
    ) -> callable:
        def wrapper():
            material_combobox.clear()
            material_combobox.addItems(
                self.list_of_item_names[material_type.currentText()]
            )
            self.set_receipt_to_counter(component)

        return wrapper

    def set_receipt_to_counter(self, component):
        def wrapper():
            if component == "A":
                material_names = [
                    line.currentText() for line in self.material_comboboxes_a
                ]
                if "" in material_names:
                    return None
                self.receipt_counter.change_receipt(
                    "A",
                    [line.currentText() for line in self.material_a_types],
                    material_names,
                )
                for line, percent in enumerate(self.material_percent_lines_a):
                    self.receipt_counter.set_percent(line, percent.text(), "A")
            elif component == "B":
                material_names = [
                    line.currentText() for line in self.material_comboboxes_b
                ]

                if "" in material_names:
                    return None
                self.receipt_counter.change_receipt(
                    "B",
                    [line.currentText() for line in self.material_b_types],
                    material_names,
                )

                for line, percent in enumerate(self.material_percent_lines_b):
                    self.receipt_counter.set_percent(line, percent.text(), "B")

        return wrapper