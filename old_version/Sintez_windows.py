import os
import sys
from itertools import cycle
from math import inf
from typing import Optional

import openpyxl as opx
from pandas import DataFrame
from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtGui import QBrush, QImage, QPalette
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QSpacerItem,
)


class SintezWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/EEWAHEW.ui")[0]):
    def __init__(self, main_window: "MainWindow", component):
        super(SintezWindow, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.component = component
        self.horizontalSlider = {}
        self.line_percent = {}
        self.line_EW = {}
        self.line_name_of_component = {}
        self.percents = {}
        self.previousPercents = {}
        self.sumpercent = 0
        self.checkBoxAHEW = {}
        self.checkBoxEEW = {}
        self.label_activity = {}
        self.checkBoxChange = {}

        self.__EW = 0
        self.slider_is_pushed = {}

        self.base_df: Optional[DataFrame] = None
        self.current_df: Optional[DataFrame] = None

        self.gridLayout.addItem(QSpacerItem(1, 1), 1000, 0, 1000, 5)

        # self.total_EW_lineEdit = QtWidgets.QLineEdit(self.centralwidget)
        # self.total_EW_lineEdit.setGeometry(QtCore.QRect(100, 60, 200, 20))
        # self.total_EW_lineEdit.setObjectName("total_EW_lineEdit")

        self.material_types = []
        self.material_comboboxes = []
        self.material_percent_lines = []

        self.label.setText("Компонент " + component)

        if component == "A":
            self.setWindowTitle("Редактирование рецептуры Компонента А")
            self.label.setText("Редактирование рецептуры Компонента А")
            self.main_window_material_comboboxes = (
                self.main_window.material_comboboxes_a
            )
            self.main_window_material_types = self.main_window.material_a_types
            self.main_window_material_percent_lines = (
                self.main_window.material_percent_lines_a
            )

        elif component == "B":
            self.setWindowTitle("Редактирование рецептуры Компонента Б")
            self.label.setText("Редактирование рецептуры Компонента Б")
            self.main_window_material_comboboxes = (
                self.main_window.material_comboboxes_b
            )
            self.main_window_material_types = self.main_window.material_b_types
            self.main_window_material_percent_lines = (
                self.main_window.material_percent_lines_b
            )
        else:
            raise TypeError

        with open("style.css", "r") as f:
            self.style, self.style_combobox = f.read().split("$split$")

        self.numb_of_components = len(self.main_window_material_comboboxes)

        self.percent_list = []
        self.name_list = []

        for index, widget in enumerate(self.main_window_material_comboboxes):
            percent = float(self.main_window_material_percent_lines[index].text())
            name = widget.currentText()
            self.percents[index] = percent

            # new
            self.percent_list.append(percent)
            self.name_list.append(name)

            self.previousPercents[index] = percent
            self.add_line(
                index,
                self.main_window_material_types[index].currentText(),
                widget.currentText(),
                component,
                percent,
            )

        self.sootnoshenie = {}
        # Составим словарь соотношений
        for index, name in enumerate(self.name_list):
            if len(self.name_list) > index + 1:
                for next_name in self.name_list[index + 1 :]:
                    self.sootnoshenie[frozenset([name, next_name])] = (
                        self.percent_list[index] / self.percent_list[index + 1]
                    )

        print(self.sootnoshenie)
        oImage = QImage("fon.jpg")
        # sImage = oImage.scaled(QSize(self.window_height, self.window_width))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))
        self.setPalette(palette)

        self.resize(680, 85 + 38 * len(self.material_types))

        self.change_font()
        # self.line = QtWidgets.QFrame(self.centralwidget)
        # self.line.setGeometry(QtCore.QRect(150, 100, 20, 300))
        # self.line.setFrameShape(QtWidgets.QFrame.VLine)
        # self.line.setFrameShadow(QtWidgets.QFrame.Sunken)
        # self.line.setObjectName("line")
        # self.line_2 = QtWidgets.QFrame(self.centralwidget)
        # self.line_2.setGeometry(QtCore.QRect(20, 140, 761, 16))
        # self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        # self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        # self.line_2.setObjectName("line_2")

    def change_font(self):

        font = QtGui.QFont("Times New Roman", self.main_window.font_size)
        big_bold_font = QtGui.QFont("Times New Roman", self.main_window.font_size_big)
        # big_bold_font.setBold(True)
        self.label.setFont(big_bold_font)
        for line_numb in range(len(self.material_types)):
            self.material_types[line_numb].setFont(font)
            self.material_comboboxes[line_numb].setFont(font)
            self.material_percent_lines[line_numb].setFont(font)

    @property
    def EW(self):
        return self.__EW

    @EW.setter
    def EW(self, value):
        # if value > 0:
        #     self.total_EW_lineEdit.setText("EEW  " + str(round(value, 2)))
        # elif value == 0:
        #     self.total_EW_lineEdit.setText("No EW")
        # else:
        #     self.total_EW_lineEdit.setText("AHEW  " + str(-round(value, 2)))
        self.__EW = value

    def slider_is_moved(self, numb_of_slider):
        def wrapper():
            value_of_slider = int(self.horizontalSlider[numb_of_slider].value()) / 100
            # self.try_to_change(numb_of_slider, self.percents[numb_of_slider], value_of_slider)
            self.percents[numb_of_slider] = value_of_slider
            # self.count_EW()
            self.line_percent[numb_of_slider].setText(str(value_of_slider))

        return wrapper

    # def change_activivty(self, numb_of_line, box):
    #     def wrapper():
    #         if box == 'AHEW':
    #             if self.checkBoxEEW[numb_of_line].isChecked() or self.label_activity[numb_of_line].text() == 'None':
    #                 self.label_activity[numb_of_line].setText('AHEW')
    #                 self.checkBoxEEW[numb_of_line].setChecked(False)
    #                 return None
    #
    #         elif box == 'EEW':
    #             if self.checkBoxAHEW[numb_of_line].isChecked() or self.label_activity[numb_of_line].text() == 'None':
    #                 self.label_activity[numb_of_line].setText('EEW')
    #                 self.checkBoxAHEW[numb_of_line].setChecked(False)
    #                 return None
    #
    #         self.label_activity[numb_of_line].setText('None')
    #
    #     return wrapper

    def change_percent_in_line(self, numb_of_line):
        def wrapper():
            text = self.line_percent[numb_of_line].text()
            if text.isdigit():
                numb = float(text)
                self.horizontalSlider[numb_of_line].setSliderPosition(numb * 100)
                self.line_percent[numb_of_line].setText(text)
            else:
                # Вписать инструкцию, которая будет сообщать об ошибке
                pass

        return wrapper

    def add_line(
        self,
        numb_of_line,
        mat_type,
        mat_name,
        component,
        percent=None,
    ):

        items_type = self.material_types
        items = self.material_comboboxes
        items_lines = self.material_percent_lines
        grid = self.gridLayout
        material_combobox = QComboBox()
        materia_type_combobox = QComboBox()

        materia_type_combobox.setStyleSheet(self.style_combobox)
        material_combobox.setStyleSheet(self.style_combobox)
        # Подтянуть соответствующий индекс
        materia_type_combobox.addItems(self.main_window.types_of_items)
        materia_type_combobox.setCurrentIndex(
            self.main_window_material_types[numb_of_line].currentIndex()
        )
        print(self.main_window_material_types[numb_of_line].currentIndex())
        materia_type_combobox.setFixedWidth(60)

        materia_type_combobox.currentIndexChanged.connect(
            self.main_window.change_list_of_materials(
                material_combobox, materia_type_combobox, component
            )
        )

        # Подцепить соответствующие вещества
        material_combobox.addItems(self.main_window.list_of_item_names[mat_type])
        material_combobox.setCurrentIndex(
            self.main_window_material_comboboxes[numb_of_line].currentIndex()
        )
        material_combobox.setFixedWidth(120)

        line = QLineEdit()
        line.setText(self.main_window_material_percent_lines[numb_of_line].text())
        # line.editingFinished.connect(lambda: self.to_float(component))
        # line.editingFinished.connect(lambda: self.count_sum(component))

        items_type.append(materia_type_combobox)
        items.append(material_combobox)
        items_lines.append(line)
        row_count = numb_of_line
        grid.addWidget(materia_type_combobox, row_count + 1, 0)
        grid.addWidget(material_combobox, row_count + 1, 1)
        grid.addWidget(line, row_count + 1, 2)

        # grid.addWidget(final_label, row_count + 2, 1, alignment=QtCore.Qt.AlignRight)
        # grid.addWidget(final_label_numb, row_count + 2, 2)
        # self.count_sum(component)
        line.setFixedWidth(60)
        self.line_percent[numb_of_line] = line
        # self.line_name_of_component[numb_of_line] = QComboBox(self.centralwidget)
        # self.line_name_of_component[numb_of_line].setGeometry(QtCore.QRect(x + 140, 110 + interval * numb_of_line, 141, 20))
        # self.line_name_of_component[numb_of_line].setObjectName(f"line_name_of_component{numb_of_line}")

        # Создаём окно для процентов
        # self.line_percent[numb_of_line] = QtWidgets.QLineEdit(self.centralwidget)
        # self.line_percent[numb_of_line].setGeometry(QtCore.QRect(x + 300, 110 + interval * numb_of_line, 51, 20))
        # self.line_percent[numb_of_line].setObjectName(f"line_percent{numb_of_line}")
        if percent:
            self.line_percent[numb_of_line].setText(str(percent))
        self.line_percent[numb_of_line].editingFinished.connect(
            self.try_to_change(numb_of_line, "line")
        )

        self.checkBoxChange[numb_of_line] = QtWidgets.QCheckBox()
        # self.checkBoxChange[numb_of_line].setGeometry(QtCore.QRect(x + 370, 112 + interval * numb_of_line, 16, 17))
        # self.checkBoxChange[numb_of_line].setText("")
        # self.checkBoxChange[numb_of_line].setObjectName(f"checkBoxChange{numb_of_line}")
        # self.checkBoxChange[numb_of_line].clicked.connect()
        grid.addWidget(self.checkBoxChange[numb_of_line], row_count + 1, 3)

        slider = QtWidgets.QSlider()
        # self.horizontalSlider[numb_of_line].setGeometry(QtCore.QRect(x + 390, 110 + interval * numb_of_line, 400, 20))
        # self.horizontalSlider[numb_of_line].setProperty("value", 20)
        # self.horizontalSlider[numb_of_line].setSliderPosition(10 + 3 * numb_of_line)
        slider.setOrientation(QtCore.Qt.Horizontal)
        slider.setTickInterval(10)
        slider.setObjectName(f"horizontalSlider{numb_of_line}")
        slider.setRange(0, 10000)

        self.horizontalSlider[numb_of_line] = slider
        grid.addWidget(slider, row_count + 1, 4)
        if percent:
            slider.setSliderPosition(percent * 100)

        slider.valueChanged.connect(self.try_to_change(numb_of_line, "slider"))
        # self.horizontalSlider[numb_of_line].sliderMoved.connect(self.try_to_change(numb_of_line, 'slider'))
        slider.sliderPressed.connect(self.slider_push_changer(numb_of_line, True))
        slider.sliderReleased.connect(self.set_percents)
        self.slider_is_pushed[numb_of_line] = False

    def slider_push_changer(self, line: int, is_push: bool):
        def wrapper():
            self.slider_is_pushed[line] = is_push

        return wrapper

    # def count_EW(self):
    #     activ_group = 0
    #     for numb_of_line in range(self.numb_of_components):
    #         if self.label_activity[numb_of_line].text() != 'None':
    #
    #             current_activ_group = 1 / float(self.line_EW[numb_of_line].text()) * \
    #                                   float(self.line_percent[numb_of_line].text()) / 100
    #
    #             if self.label_activity[numb_of_line].text() == 'AHEW':
    #                 activ_group += current_activ_group
    #             else:
    #                 activ_group -= current_activ_group
    #     if activ_group != 0:
    #         self.EW = int((1 / activ_group) * 1000) / 1000
    #     else:
    #         self.EW = 0

    def try_to_change(self, numb_of_line, source):
        def wrapper():
            if self.slider_is_pushed[numb_of_line]:
                # Вроде, не нужно
                # if self.checkBoxChange[numb_of_line].isChecked():
                #     # self.horizontalSlider[numb_of_line].setSliderPosition(
                #     #     self.percents[numb_of_line] * 100
                #     # )
                #     return None

                lines_to_change = []
                for line in self.checkBoxChange:
                    if self.checkBoxChange[line].isChecked() and line != numb_of_line:
                        lines_to_change.append(line)

                previos_value = self.previousPercents[numb_of_line]

                if source == "slider":
                    new_value = round(
                        int(self.horizontalSlider[numb_of_line].value()) / 100, 2
                    )
                else:
                    new_value = self.line_percent[numb_of_line].text()
                    try:
                        new_value = round(float(new_value), 2)
                    except:
                        self.line_percent[numb_of_line].setText(
                            str(self.percents[numb_of_line])
                        )
                        return None

                delta = round(new_value - previos_value, 2)

                if delta > 0:
                    change_way_is_up = True
                else:
                    change_way_is_up = False
                    delta = -delta

                if delta < 0.01:
                    return None

                for line in self.percents:
                    self.previousPercents[line] = self.percents[line]

                # Функция, меняющая компоненты без сохранения EW
                else:
                    sum_percent = 0
                    sum_ostatok_percent = 0
                    for line in lines_to_change:
                        sum_percent += self.percents[line]
                        sum_ostatok_percent += 100 - self.percents[line]

                    if ((sum_percent > delta) and change_way_is_up) or (
                        (sum_ostatok_percent > delta) and not change_way_is_up
                    ):

                        # if change_way_is_up:
                        #     self.percents[numb_of_line] += delta
                        # else:
                        #     self.percents[numb_of_line] -= delta

                        self.percents[numb_of_line] = round(
                            self.percents[numb_of_line], 2
                        )
                        break_flag = []
                        for line in cycle(lines_to_change):
                            # Ходим по концентрациям других продуктов и меняем при проходе на 0,01%, если там что-то еще осталось
                            # Когда ничего не осталось, возвращаем компонент, который меняли обратно на оставшуюся дельту

                            if delta < 0.01:
                                break

                            if not change_way_is_up:
                                self.percents[line] += 0.01
                                self.percents[line] = round(self.percents[line], 2)
                                self.percents[numb_of_line] -= 0.01
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )

                            if self.percents[line] == 0:
                                if line not in break_flag:
                                    break_flag.append(line)
                                if len(break_flag) == len(lines_to_change):
                                    break

                                continue

                            if change_way_is_up:
                                self.percents[line] -= 0.01
                                self.percents[line] = round(self.percents[line], 2)
                                self.percents[numb_of_line] += 0.01
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )

                            # self.set_percents(numb_of_line)

                            delta -= 0.01
                            delta = round(delta, 2)

                    else:
                        # Когда нам надо добить до конца
                        if change_way_is_up:
                            for line in lines_to_change:
                                self.percents[numb_of_line] += self.percents[line]
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )
                                self.percents[line] = 0
                            # self.horizontalSlider[numb_of_line].setSliderPosition(self.percents[numb_of_line] * 100)
                            # return None
                        else:
                            for line in lines_to_change:
                                self.percents[numb_of_line] -= 100 - self.percents[line]
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )
                                self.percents[line] = 100
                            # self.horizontalSlider[numb_of_line].setSliderPosition(self.percents[numb_of_line] * 100)
                            # return None

                self.set_percents(numb_of_line)
                sum_percent_all = 0
                for i in self.percents.values():
                    sum_percent_all += i

                for line in self.percents:
                    self.previousPercents[line] = self.percents[line]

                # self.count_EW()
                self.main_window.set_percents_from_receipt_window(
                    self.component,
                    [self.percents[i] for i in range(len(self.percents))],
                )

        return wrapper

    def try_to_change_new(self, numb_of_line, source):
        def wrapper():
            if self.slider_is_pushed[numb_of_line]:
                # Фикирует слайдер
                # if self.checkBoxChange[numb_of_line].isChecked():
                #     return None

                lines_to_change = []
                for line in self.checkBoxChange:
                    if self.checkBoxChange[line].isChecked() and line != numb_of_line:
                        lines_to_change.append(line)

                previos_value = self.previousPercents[numb_of_line]

                if source == "slider":
                    new_value = round(
                        int(self.horizontalSlider[numb_of_line].value()) / 100, 2
                    )
                else:
                    new_value = self.line_percent[numb_of_line].text()
                    try:
                        new_value = round(float(new_value), 2)
                    except:
                        self.line_percent[numb_of_line].setText(
                            str(self.percents[numb_of_line])
                        )
                        return None

                delta = round(new_value - previos_value, 2)

                if delta > 0:
                    change_way_is_up = True
                else:
                    change_way_is_up = False
                    delta = -delta

                if delta < 0.01:
                    return None

                for line in self.percents:
                    self.previousPercents[line] = self.percents[line]

                # Функция, меняющая компоненты без сохранения EW
                else:
                    sum_percent = 0
                    sum_ostatok_percent = 0
                    for line in lines_to_change:
                        sum_percent += self.percents[line]
                        sum_ostatok_percent += 100 - self.percents[line]

                    if ((sum_percent > delta) and change_way_is_up) or (
                        (sum_ostatok_percent > delta) and not change_way_is_up
                    ):

                        # if change_way_is_up:
                        #     self.percents[numb_of_line] += delta
                        # else:
                        #     self.percents[numb_of_line] -= delta

                        self.percents[numb_of_line] = round(
                            self.percents[numb_of_line], 2
                        )
                        break_flag = []
                        for line in cycle(lines_to_change):
                            # Ходим по концентрациям других продуктов и меняем при проходе на 0,01%, если там что-то еще осталось
                            # Когда ничего не осталось, возвращаем компонент, который меняли обратно на оставшуюся дельту

                            if delta < 0.01:
                                break

                            if not change_way_is_up:
                                self.percents[line] += 0.01
                                self.percents[line] = round(self.percents[line], 2)
                                self.percents[numb_of_line] -= 0.01
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )

                            if self.percents[line] == 0:
                                if line not in break_flag:
                                    break_flag.append(line)
                                if len(break_flag) == len(lines_to_change):
                                    break

                                continue

                            if change_way_is_up:
                                self.percents[line] -= 0.01
                                self.percents[line] = round(self.percents[line], 2)
                                self.percents[numb_of_line] += 0.01
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )

                            # self.set_percents(numb_of_line)

                            delta -= 0.01
                            delta = round(delta, 2)

                    else:
                        # Когда нам надо добить до конца
                        if change_way_is_up:
                            for line in lines_to_change:
                                self.percents[numb_of_line] += self.percents[line]
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )
                                self.percents[line] = 0
                            # self.horizontalSlider[numb_of_line].setSliderPosition(self.percents[numb_of_line] * 100)
                            # return None
                        else:
                            for line in lines_to_change:
                                self.percents[numb_of_line] -= 100 - self.percents[line]
                                self.percents[numb_of_line] = round(
                                    self.percents[numb_of_line], 2
                                )
                                self.percents[line] = 100
                            # self.horizontalSlider[numb_of_line].setSliderPosition(self.percents[numb_of_line] * 100)
                            # return None

                self.set_percents(numb_of_line)
                sum_percent_all = 0
                for i in self.percents.values():
                    sum_percent_all += i

                for line in self.percents:
                    self.previousPercents[line] = self.percents[line]

                # self.count_EW()
                self.main_window.set_percents_from_receipt_window(
                    self.component,
                    [self.percents[i] for i in range(len(self.percents))],
                )

        return wrapper

    def set_percents(self, current_line=-1):
        for line in self.percents:
            self.line_percent[line].setText(str(self.percents[line]))
            if line == current_line:
                continue
            self.horizontalSlider[line].setSliderPosition(self.percents[line] * 100)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.component == "A":
            self.main_window.a_receipt_window = None
        if self.component == "B":
            self.main_window.b_receipt_window = None

        self.main_window.enable_receipt(self.component)
        self.close()


class ChoosePairReactWindow(
    QtWidgets.QMainWindow, uic.loadUiType("windows/choose_pair_react.ui")[0]
):
    def __init__(self, main_window: "MainWindow", all_pairs_a, all_pairs_b):
        super(ChoosePairReactWindow, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.labels_a = []
        self.labels_b = []
        self.checkboxes_a = []
        self.checkboxes_b = []
        self.all_pairs_a = all_pairs_a
        self.all_pairs_b = all_pairs_b
        self.pairs_to_react_a = []
        self.pairs_to_react_b = []
        self.fill_window()

        oImage = QImage("fon.jpg")
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))
        self.setPalette(palette)

    def fill_window(self):
        for pair in self.all_pairs_a:
            self.add_line(pair, self.gridLayout_a, self.labels_a, self.checkboxes_a)
        self.gridLayout_a.addItem(QSpacerItem(100, 10), 100, 0, 100, 2)
        for pair in self.all_pairs_b:
            self.add_line(pair, self.gridLayout_b, self.labels_b, self.checkboxes_b)
        self.gridLayout_b.addItem(QSpacerItem(100, 10), 100, 0, 100, 2)

    @staticmethod
    def add_line(
        pair: tuple, layout: QGridLayout, labels_list: list, checkboxes_list: list
    ):
        label = QLabel()
        label.setText(f"{pair[0]} + {pair[1]}")
        labels_list.append(label)
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        checkbox.setFixedWidth(20)
        checkbox.setFixedHeight(20)
        checkboxes_list.append(checkbox)

        row_count = layout.count()
        layout.addWidget(checkbox, row_count + 1, 0)
        layout.addWidget(label, row_count + 1, 1)

    def get_react_pairs(self, component):
        if component == "A":
            checkboxes_list = self.checkboxes_a
            all_pairs = self.all_pairs_a
            self.pairs_to_react_a = []
            pairs_to_react = self.pairs_to_react_a
        elif component == "B":
            checkboxes_list = self.checkboxes_b
            all_pairs = self.all_pairs_b
            self.pairs_to_react_b = []
            pairs_to_react = self.pairs_to_react_b
        else:
            return None
        for checkbox, pair in zip(checkboxes_list, all_pairs):
            if checkbox.isChecked():
                pairs_to_react.append(pair)
        return pairs_to_react

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if not all(
            chbox.isChecked() for chbox in self.checkboxes_b + self.checkboxes_a
        ):
            self.main_window.sintez_pair_label.setText("Ступенчатый синтез")
        a0.accept()
