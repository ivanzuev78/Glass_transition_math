import sys
from typing import Iterable, List, Optional, Tuple, Union, Callable

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QPushButton,
    QTextBrowser, QTableWidget, QTableWidgetItem, QRadioButton, QTextEdit, QLabel,
)

from res.additional_funcs import set_qt_stile
from res.material_classes import DataMaterial, Profile, CorrectionFunction, DataGlass, Correction


class EditDataWindow(QWidget):
    def __init__(self, main_window=None, profile: Profile = None):
        super().__init__()
        self.title = "PyQt5 drag and drop"
        self.left = 500
        self.top = 400
        self.width = 800
        self.height = 500
        self.profile = profile
        self.initUI()
        self.main_window = main_window
        self.close_to_edit_material = False

        # Вынести путь к стилю в настройки
        set_qt_stile("style.css", self)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.data_material_widget = DataMaterialWidget(self)
        self.data_material_widget.move(235, 30)

        self.profile_material_widget = ProfileMaterialWidget(self)
        self.profile_material_widget.move(10, 30)

        but_width = 155
        but_height = 25
        but_x_pos = 450
        but_y_pos = 30
        but_y_delta = 35

        self.add_mat_but = QPushButton(self)
        self.add_mat_but.move(but_x_pos, but_y_pos)
        self.add_mat_but.resize(but_width, but_height)
        self.add_mat_but.setText("Добавить материал")
        self.add_mat_but.clicked.connect(self.add_material_but_click)

        self.add_tg_but = QPushButton(self)
        self.add_tg_but.move(but_x_pos, but_y_pos + but_y_delta)
        self.add_tg_but.resize(but_width, but_height)
        self.add_tg_but.setText("Добавить стеклование")
        self.add_tg_but.clicked.connect(self.add_tg_but_click)

        self.del_mat_from_prof_but = QPushButton(self)
        self.del_mat_from_prof_but.move(10, 450)
        self.del_mat_from_prof_but.resize(200, but_height)
        self.del_mat_from_prof_but.setText("Удалить материал из профиля")
        self.del_mat_from_prof_but.clicked.connect(self.profile_material_widget.del_mat_from_prof)

        self.del_mat_from_db_but = QPushButton(self)
        self.del_mat_from_db_but.move(235, 450)
        self.del_mat_from_db_but.resize(200, but_height)
        self.del_mat_from_db_but.setText("Удалить материал из программы")
        self.del_mat_from_db_but.clicked.connect(self.data_material_widget.del_mat_from_db)

        self.profile_material_widget.data_material_widget = self.data_material_widget
        self.data_material_widget.profile_material_widget = self.profile_material_widget

        self.label_1 = QLabel(self)
        self.label_1.move(290, 10)
        self.label_1.resize(but_width, but_height)
        self.label_1.setText('Все материалы')
        self.label_1.setFont(QFont("Times", 10))

        self.label_2 = QLabel(self)
        self.label_2.move(45, 10)
        self.label_2.resize(but_width, but_height)
        self.label_2.setText('Материалы профиля')
        self.label_2.setFont(QFont("Times", 10))

        # РАБОТАЕТ
        self.show()

    def add_material_but_click(self):
        self.edit_material_window = EditMaterialWindow(self, self.profile)
        self.close_to_edit_material = True
        self.close()
        self.edit_material_window.show()

    def add_tg_but_click(self):
        self.add_material = EditTgWindow(self, self.profile)
        self.close_to_edit_material = True
        self.close()
        self.add_material.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.main_window is not None and not self.close_to_edit_material:
            self.main_window.show()
            del self
        else:
            self.close_to_edit_material = False


class ProfileMaterialWidget(QListWidget):
    def __init__(self, parent: EditDataWindow):
        super().__init__(parent)
        self.edit_window = parent
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)
        self.resize(200, 410)
        self.data_material_widget: Optional[
            DataMaterialWidget
        ] = parent.data_material_widget
        self.profile: Profile = self.edit_window.profile
        self.orm_db = self.profile.orm_db

        self.profile_materials = []  # Все материалы в виде DataMaterial
        self.profile_materials_names = (
            []
        )  # Все названия материалов (порядок совпадает с profile_materials)
        for mat_type in self.profile.get_all_types():
            self.profile_materials += self.profile.get_materials_by_type(mat_type)
            self.profile_materials_names += self.profile.get_mat_names_by_type(mat_type)

        self.addItems(self.profile_materials_names)

        self.currentItemChanged.connect(self.change_index_in_data_material_widget)
        # TODO Добавить вызов окна редактирования материала
        self.itemDoubleClicked.connect(self.data_material_widget.open_mat_editor)

    def del_mat_from_prof(self, *args, material_to_del: DataMaterial = None):
        index = self.currentIndex().row()

        if material_to_del is not None:
            if material_to_del not in self.profile_materials:
                return None
            material = material_to_del
            index = self.profile_materials.index(material)
        elif index != -1:
            material = self.profile_materials[index]
        else:
            return None
        self.profile_materials.remove(material)
        self.profile_materials_names.pop(index)
        self.profile.remove_material(material)
        self.clear()
        self.addItems(self.profile_materials_names)

    def change_index_in_data_material_widget(self):
        text = self.currentIndex().data()
        if text in self.data_material_widget.names_list:
            index = self.data_material_widget.names_list.index(text)
            self.data_material_widget.setCurrentRow(index)

    # вызывается при попадании в область
    def dragEnterEvent(self, e):
        # Позволяет перетащить объект в этот виджет
        e.accept()
        # e.ignore()

    # вызывается при покидании области
    def dragLeaveEvent(self, e):
        # e.ignore()
        e.accept()

    def dropEvent(self, e):
        e.accept()
        index = int(e.mimeData().text())
        material: DataMaterial = self.data_material_widget.material_list[index]
        self.add_material_to_profile(material)

    def add_material_to_profile(self, material: DataMaterial):
        mat_name = material.name
        if mat_name not in self.profile_materials_names:
            self.addItem(mat_name)
            self.profile_materials_names.append(mat_name)
            self.profile_materials.append(material)
            # материала в дб к профилю
            self.orm_db.add_material_to_profile(material, self.profile)
            self.profile.add_material(material)

class DataMaterialWidget(QListWidget):
    def __init__(self, parent: EditDataWindow):
        super().__init__(parent)
        self.edit_window = parent

        # self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.resize(200, 410)
        self.orm_db = self.edit_window.profile.orm_db
        self.material_list: List[DataMaterial] = self.orm_db.get_all_materials()
        self.names_list: List[str] = []

        for material in self.material_list:
            self.addItem(material.name)
            self.names_list.append(material.name)

        self.profile_material_widget: Optional[ProfileMaterialWidget] = None
        # TODO Добавить вызов окна редактирования материала
        self.itemDoubleClicked.connect(self.open_mat_editor)
        self.currentItemChanged.connect(self.change_index_in_profile_material_widget)

    def del_mat_from_db(self):
        index = self.currentIndex().row()
        print(index)
        if index != -1:
            material = self.material_list.pop(index)
            self.names_list.pop(index)
            self.orm_db.remove_material(material)
            self.clear()
            self.addItems(self.names_list)
            self.profile_material_widget.del_mat_from_prof(material_to_del=material)

    def change_index_in_profile_material_widget(self):
        row = self.currentIndex().row()
        material = self.material_list[row]
        if material in self.profile_material_widget.profile_materials:
            index = self.profile_material_widget.profile_materials.index(material)
            self.profile_material_widget.setCurrentRow(index)

    def open_mat_editor(self):
        material = self.material_list[self.currentIndex().row()]
        self.mat_editor = EditMaterialWindow(self.edit_window, self.edit_window.profile, material)
        self.mat_editor.show()
        self.edit_window.close_to_edit_material = True
        self.edit_window.close()

    def add_material(self, material: DataMaterial):
        self.material_list.append(material)
        self.names_list.append(material.name)
        self.addItem(material.name)

    def mimeData(self, my_list: Iterable, lwi: QListWidgetItem = None):
        mimedata = super().mimeData(my_list)
        mimedata.setText(str(self.currentIndex().row()))
        return mimedata

    def dropMimeData(self, index, data, action):

        if data.hasText():
            self.addItem(data.text())
            return True
        else:
            return super().dropMimeData(index, data, action)

    # вызывается при попадании в область
    def dragEnterEvent(self, e):
        self.takeItem(0)
        # Позволяет или нет перетащить объект в этот виджет
        e.accept()

    # вызывается при покидании области
    def dragLeaveEvent(self, e):
        e.accept()

    def dropEvent(self, e):
        e.accept()
        # self.addItem()


# Устарело, вроде как
class CreateMaterialWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/Add_material.ui")[0]):
    def __init__(self, main_window: EditDataWindow, origin_material: DataMaterial = None):
        super(CreateMaterialWindow, self).__init__()
        self.setupUi(self)
        self.main_window = main_window
        self.material = origin_material
        self.name_lineEdit: QLineEdit
        self.type_comboBox: QComboBox
        self.ew_lineEdit: QLineEdit
        # TODO передать типы веществ
        self.type_comboBox.addItems(["Epoxy", "Amine", "None"])
        if origin_material is not None:
            self.name_lineEdit.setText(origin_material.name)
            # TODO Установить соответствующий индекс
            self.type_comboBox.setCurrentIndex(1)
            self.ew_lineEdit.setText(str(origin_material.ew))

        # Вынести путь к стилю в настройки
        set_qt_stile("style.css", self)

        self.cancel_but.clicked.connect(self.closeEvent)

    def save_data(self):
        if self.material is not None:
            # TODO Описать логику редактирования материала
            ...
        else:
            # TODO Описать логику создания нового материала
            name = self.name_lineEdit.text()
            mat_type = self.type_comboBox.currentText()
            ew = self.ew_lineEdit.text()
            material = DataMaterial(name, mat_type, ew)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.main_window.show()
        self.main_window.close_to_edit_material = False
        del self


class EditCorrectionWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/edit_correction.ui")[0]):
    power_lineEdit: QLineEdit  # Выбор степени
    coef_lineEdit: QLineEdit  # Добавление коэффициента перед степенью
    coef_tableWidget: QTableWidget  # Таблица полиномиальных коэффициентов
    k_e_lineEdit: QLineEdit
    k_exp_lineEdit: QLineEdit
    inf_full_radio: QRadioButton  # Выбор влияния на систему в целом
    inf_pair_radio: QRadioButton  # Выбор влияния на пару
    moove_to_zero_but: QRadioButton  # Сдвиг функции в 0
    epoxy_combobox: QComboBox  # Выбор эпоксида при влияния на пару
    amine_combobox: QComboBox  # Выбор амина при влияния на пару
    x_min_line: QLineEdit  # Выбор начала диапазона влияния
    x_max_line: QLineEdit  # Выбор конца диапазона влияния
    move_x_line: QLineEdit  # Выбор конца диапазона влияния
    move_y_line: QLineEdit  # Выбор конца диапазона влияния
    name_line: QLineEdit  # Выбор конца диапазона влияния
    comment_text_edit: QTextEdit  # Выбор конца диапазона влияния

    def __init__(self, previous_window, material: DataMaterial = None, correction: CorrectionFunction = None,
                 close_action: Callable = None):
        super(EditCorrectionWindow, self).__init__()
        self.setupUi(self)
        self.previous_window = previous_window
        self.correction = correction
        self.coef_tableWidget.resizeColumnsToContents()
        self.polynomial_coefficients = []
        self.profile = previous_window.profile
        self.inf_material = material
        self.close_action = close_action

        self.epoxy_list = self.profile.get_materials_by_type("Epoxy")
        self.amine_list = self.profile.get_materials_by_type("Amine")

        self.epoxy_combobox.addItems(self.profile.get_mat_names_by_type("Epoxy"))
        self.amine_combobox.addItems(self.profile.get_mat_names_by_type("Amine"))
        self.coef_tableWidget.currentItemChanged.connect(self.set_power_to_widget)

        if correction is not None:
            # TODO Загрузка коррекции в окно
            ...

        # Вынести путь к стилю в настройки
        set_qt_stile("style.css", self)
        self.cancel_but.clicked.connect(self.close)
        self.add_coef_but.clicked.connect(self.add_power_coef)
        self.save_but.clicked.connect(self.save_data)
        self.create_graph_but.clicked.connect(self.plot_graph)
        self.del_coef_but.clicked.connect(self.del_poly_coef)
        self.move_to_zero_but.clicked.connect(self.move_func)
        self.move_func_but.clicked.connect(
            lambda: self.move_func(float(self.move_x_line.text()), float(self.move_y_line.text())))

        self.k_e_lineEdit.editingFinished.connect(lambda: self.check_float_text(self.k_e_lineEdit))
        self.k_exp_lineEdit.editingFinished.connect(lambda: self.check_float_text(self.k_exp_lineEdit))
        self.x_min_line.editingFinished.connect(lambda: self.check_float_text(self.x_min_line))
        self.x_max_line.editingFinished.connect(lambda: self.check_float_text(self.x_max_line))
        self.move_x_line.editingFinished.connect(lambda: self.check_float_text(self.move_x_line))
        self.move_y_line.editingFinished.connect(lambda: self.check_float_text(self.move_y_line))

        self.inf_full_radio.toggled.connect(self.change_influence_radiobutton)
        self.inf_pair_radio.toggled.connect(self.change_influence_radiobutton)

    def update_polynomial_coefficients(self):
        self.coef_tableWidget.clear()
        self.coef_tableWidget.setRowCount(sum([1 if i else 0 for i in self.polynomial_coefficients]))
        self.coef_tableWidget.setVerticalHeaderLabels(
            [f"k{power}" for power, coef in enumerate(self.polynomial_coefficients) if coef])
        self.coef_tableWidget.setHorizontalHeaderLabels(["Степень X", "Коэффициент"])

        row = 0
        for power, coef in enumerate(self.polynomial_coefficients):
            if coef == 0:
                continue
            self.coef_tableWidget.setItem(row, 0, QTableWidgetItem(f"{power}"))
            self.coef_tableWidget.setItem(row, 1, QTableWidgetItem(f"{coef}"))
            row += 1
        self.coef_tableWidget.resizeColumnsToContents()

    def add_power_coef(self):
        power = self.power_lineEdit.text().replace(",", ".")
        coef = self.coef_lineEdit.text().replace(",", ".")
        try:
            power = int(power)
            coef = float(coef)
            while len(self.polynomial_coefficients) <= power:
                self.polynomial_coefficients.append(0.0)
            self.polynomial_coefficients[power] = coef
            self.update_polynomial_coefficients()
        except:
            pass

        self.power_lineEdit.setText("")
        self.coef_lineEdit.setText("")

    def set_power_to_widget(self):
        index = self.coef_tableWidget.currentIndex()
        row = index.row()
        power_item = self.coef_tableWidget.item(row, 0)
        if power_item is not None:
            power = power_item.data(0)
            data = self.coef_tableWidget.item(row, 1).data(0)
            if row != -1:
                self.power_lineEdit.setText(power)
                self.coef_lineEdit.setText(data)

    def move_func(self, x=0.0, y=0.0):
        k_e = float(self.k_e_lineEdit.text())
        k_exp = float(self.k_exp_lineEdit.text())
        cor_func = CorrectionFunction(k_e=k_e, k_exp=k_exp, polynomial_coefficients=self.polynomial_coefficients)
        number = round(cor_func(x), 10)
        while number != y:
            if len(self.polynomial_coefficients) == 0:
                self.polynomial_coefficients.append(0)
            self.polynomial_coefficients[0] -= number - y
            self.update_polynomial_coefficients()
            cor_func.polynomial_coefficients = self.polynomial_coefficients
            number = round(cor_func(x), 10)

    @staticmethod
    def check_float_text(widget):
        try:
            text = float(widget.text().replace(",", "."))
            widget.setText(str(text))
        except:
            widget.setText('0')

    def save_data(self):
        name = self.name_line.text()
        comment = self.comment_text_edit.toPlainText()
        k_e = float(self.k_e_lineEdit.text())
        k_exp = float(self.k_exp_lineEdit.text())
        cor_func = CorrectionFunction(name, comment, k_e, k_exp, polynomial_coefficients=self.polynomial_coefficients)
        x_min = float(self.x_min_line.text())
        x_max = float(self.x_max_line.text())
        amine = self.amine_list[self.amine_combobox.currentIndex()] if self.inf_pair_radio.isChecked() else None
        epoxy = self.epoxy_list[self.epoxy_combobox.currentIndex()] if self.inf_pair_radio.isChecked() else None
        correction = Correction(x_min, x_max, cor_func, amine, epoxy, inf_material=self.inf_material)
        if self.close_action is not None:
            self.close_action(correction)
        # self.profile.add_correction_to_db(correction)
        self.close()

    def plot_graph(self):
        k_e = float(self.k_e_lineEdit.text())
        k_exp = float(self.k_exp_lineEdit.text())
        cor_func = CorrectionFunction(k_e=k_e, k_exp=k_exp, polynomial_coefficients=self.polynomial_coefficients)
        x_min = float(self.x_min_line.text())
        x_max = float(self.x_max_line.text())

        import matplotlib.pyplot as plt
        import numpy as np

        amine = self.amine_list[self.amine_combobox.currentIndex()] if self.inf_pair_radio.isChecked() else None
        epoxy = self.epoxy_list[self.epoxy_combobox.currentIndex()] if self.inf_pair_radio.isChecked() else None
        if amine is not None:
            pair = (epoxy.name, amine.name)
        else:
            pair = None

        # Data for plotting
        t = np.arange(x_min, x_max, (x_max - x_min) / 100)
        s = [cor_func(x) for x in t]

        fig, ax = plt.subplots()
        ax.plot(t, s)
        string = "систему в целом "
        if self.inf_material:
            title = f"Влияние '{self.inf_material.name}' на {pair if pair is not None else string}"
        else:
            title = "Красивый график"
        ax.set(
            xlabel="Содержание вещества в системе, %",
            ylabel="Влияние на температуру стеклования, °С",
            title=title,
        )
        if len(s) > 0:
            plt.annotate(f"{s[0]}", (0, s[0]))
        ax.grid()
        # if save:
        #     filename = "graph.png"
        #     fig.savefig(filename)
        plt.show()

    def del_poly_coef(self):
        index = self.coef_tableWidget.currentIndex()
        row = index.row()
        power_item = self.coef_tableWidget.item(row, 0)
        if power_item is not None:
            power = int(power_item.data(0))
            if row != -1:
                self.polynomial_coefficients[power] = 0
                self.update_polynomial_coefficients()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.previous_window.show()
        if isinstance(self.previous_window, EditDataWindow):
            self.previous_window.close_to_edit_material = False
        a0.accept()

    def change_influence_radiobutton(self):

        if self.inf_full_radio.isChecked():
            self.epoxy_combobox.setEnabled(False)
            self.amine_combobox.setEnabled(False)
        else:
            self.epoxy_combobox.setEnabled(True)
            self.amine_combobox.setEnabled(True)


class EditMaterialWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/edit_material_with_corrections.ui")[0]):
    corrections_listWidget: QListWidget
    cor_textBrowser: QTextBrowser
    type_comboBox: QComboBox
    add_new_cor_but: QPushButton
    remove_cor_but: QPushButton
    save_but: QPushButton
    cancel_but: QPushButton
    name_lineEdit: QLineEdit
    ew_lineEdit: QLineEdit

    def __init__(self, previous_window: EditDataWindow, profile: Profile, material: DataMaterial = None):
        super(EditMaterialWindow, self).__init__()
        self.setupUi(self)
        self.previos_window = previous_window
        self.profile = profile
        self.types = self.profile.orm_db.get_all_mat_types()
        self.type_comboBox.addItems(self.types)
        self.material = material
        self.corrections: List[Correction] = []  # Коррекции, которые уже в БД
        self.corrections_to_add: List[Correction] = []  # Коррекции для добавления в БД
        self.corrections_in_widget: List[Correction] = []  # Коррекции в виджете

        self.open_new_window = False
        # Режим редактирования или создания нового материала
        self.edit_mode = False
        if material is not None:
            self.edit_mode = True
            self.set_material()
            self.name_lineEdit.setEnabled(False)

        set_qt_stile("style.css", self)

        self.corrections_listWidget.currentItemChanged.connect(self.change_row)
        self.corrections_listWidget.itemDoubleClicked.connect(self.show_correction)
        self.save_but.clicked.connect(self.save)
        self.cancel_but.clicked.connect(self.closeEvent)
        self.add_new_cor_but.clicked.connect(self.open_correction_window)
        self.remove_cor_but.clicked.connect(self.del_correction)

        self.new_cor_window = None

    def set_material(self):
        if self.edit_mode:
            index = self.types.index(self.material.mat_type)
            self.type_comboBox.setCurrentIndex(index)
            self.name_lineEdit.setText(self.material.name)
            self.ew_lineEdit.setText(str(self.material.ew))
            self.corrections = self.material.correction.get_all_corrections()

            self.update_corrections_in_widget()

    def change_row(self):

        row_numb = self.corrections_listWidget.currentRow()
        if row_numb == -1:
            return None
        cor = self.corrections_in_widget[row_numb]
        self.cor_textBrowser.setText(cor.correction_func.comment)

    def show_correction(self):
        row_numb: int = self.corrections_listWidget.currentRow()
        self.corrections_in_widget[row_numb].show_graph()

    def save(self):

        ew = self.ew_lineEdit.text().replace(',', '.')
        try:
            ew = float(ew)
        except:
            ew = 0
        name = self.name_lineEdit.text()
        if name == '':
            # TODO Попросить ввести имя
            return None
        mat_type = self.type_comboBox.currentText()
        if self.edit_mode:
            material = self.material
            self.profile.update_material_in_db(material, mat_type, ew)
        else:
            material = self.profile.add_material_to_db(name, mat_type, ew)
            self.previos_window.data_material_widget.add_material(material)
            self.previos_window.profile_material_widget.add_material_to_profile(material)
        if self.corrections_to_add:
            for cor in self.corrections_to_add:
                cor.inf_material = material
                self.profile.add_correction_to_db(cor)

        self.close()

    def del_correction(self):
        row_numb: int = self.corrections_listWidget.currentRow()
        if row_numb == -1:
            return None
        current_correction = self.corrections_in_widget.pop(row_numb)
        if current_correction in self.corrections:
            self.corrections.remove(current_correction)
            self.profile.remove_correction_from_db(current_correction)
        elif current_correction in self.corrections_to_add:
            self.corrections_to_add.remove(current_correction)
        self.update_corrections_in_widget()

    def open_correction_window(self):
        self.new_cor_window = EditCorrectionWindow(self, self.material,
                                                   close_action=self.get_correction_from_new_cor_window)
        self.new_cor_window.show()
        self.open_new_window = True
        self.close()

    def get_correction_from_new_cor_window(self, correction: Correction) -> None:
        if self.edit_mode is True:
            self.profile.add_correction_to_db(correction)
            self.corrections.append(correction)
        else:
            self.corrections_to_add.append(correction)
        self.update_corrections_in_widget()

    def update_corrections_in_widget(self):
        self.corrections_in_widget = []
        self.corrections_listWidget.clear()
        for correction in self.corrections:
            correction_func = correction.correction_func
            self.corrections_listWidget.addItem(correction_func.name)
            self.corrections_in_widget.append(correction)
        for correction in self.corrections_to_add:
            correction_func = correction.correction_func
            self.corrections_listWidget.addItem(correction_func.name)
            self.corrections_in_widget.append(correction)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if not self.open_new_window:
            self.previos_window.show()
            # if isinstance(self.previos_window, EditDataWindow):
            #     self.previos_window.close_to_edit_material = False
            #     del self
        self.open_new_window = False
        self.close()


class EditTgWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/Add_Tg.ui")[0]):
    def __init__(self, previous_window: EditDataWindow, profile: Profile, data_glass: DataGlass = None):
        super(EditTgWindow, self).__init__()
        self.setupUi(self)
        self.previos_window = previous_window
        self.profile = profile
        self.data_glass = data_glass
        set_qt_stile("style.css", self)
        self.epoxy_comboBox: QComboBox
        self.epoxy_list = profile.get_materials_by_type('Epoxy')
        self.amine_list = profile.get_materials_by_type('Amine')
        self.epoxy_comboBox.addItems([mat.name for mat in self.epoxy_list])
        self.amine_comboBox.addItems([mat.name for mat in self.amine_list])
        if data_glass is not None:
            amine_index = self.amine_list.index(data_glass.amine)
            epoxy_index = self.amine_list.index(data_glass.epoxy)
            self.amine_comboBox.setCurrentIndex(amine_index)
            self.epoxy_comboBox.setCurrentIndex(epoxy_index)
            self.tg_lineEdit.setText(str(data_glass.value))

        self.save_but.clicked.connect(self.save)
        self.cancel_but.clicked.connect(self.cancel)
        self.tg_lineEdit: QLineEdit
        self.tg_lineEdit.editingFinished.connect(self.test_tg_value)

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.previos_window.show()
        self.previos_window.close_to_edit_material = False
        del self

    def save(self):
        # TODO Реализовать логику сохранения стеклования
        self.epoxy_comboBox: QComboBox
        amine_index = self.amine_comboBox.currentIndex()
        epoxy_index = self.epoxy_comboBox.currentIndex()
        amine = self.amine_list[amine_index]
        epoxy = self.epoxy_list[epoxy_index]
        value: str = self.tg_lineEdit.text().replace(',', '.')
        if value.isdigit():
            self.profile.add_tg_to_db(epoxy, amine, float(value))
            self.close()
        else:
            self.tg_lineEdit.setText('Ошибка значения!')

    def cancel(self):
        self.close()

    def test_tg_value(self):
        value = self.tg_lineEdit.text().replace(',', '.')
        try:
            float(value)
        except:
            self.tg_lineEdit.setText('')


# пока не актуально
class ConnectFuncPair(QtWidgets.QMainWindow, uic.loadUiType("windows/connect_func_and_pair.ui")[0]):
    epoxy_combobox: QComboBox
    amine_combobox: QComboBox
    x_min_line: QLineEdit
    x_max_line: QLineEdit
    func_list_widget: QListWidget
    create_graph_but: QPushButton
    cancel_but: QPushButton
    save_but: QPushButton

    def __init__(self, previous_window: EditDataWindow):
        super(ConnectFuncPair, self).__init__()
        self.setupUi(self)
        self.previos_window = previous_window
        self.profile = previous_window.profile

        self.new_cor_window = None
        self.open_new_window = False

        set_qt_stile("style.css", self)
        self.correction_funcs = self.profile.get_all_correction_funcs()
        self.func_list_widget.addItems([cor_func.name for cor_func in self.correction_funcs])

        self.epoxy_list = self.profile.get_materials_by_type("Epoxy")
        self.amine_list = self.profile.get_materials_by_type("Amine")

        self.epoxy_combobox.addItems(self.profile.get_mat_names_by_type("Epoxy"))
        self.amine_combobox.addItems(self.profile.get_mat_names_by_type("Amine"))

        self.save_but.clicked.connect(self.save)
        self.cancel_but.clicked.connect(self.closeEvent)
        self.create_graph_but.clicked.connect(self.create_correction_function)

    def save(self):
        epoxy = self.epoxy_list[self.epoxy_combobox.currentIndex()]
        amine = self.amine_list[self.amine_combobox.currentIndex()]

    def create_correction_function(self):
        self.new_cor_window = EditCorrectionWindow(self)
        self.new_cor_window.show()
        self.open_new_window = True
        self.close()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if not self.open_new_window:
            self.previos_window.show()
            # if isinstance(self.previos_window, EditDataWindow):
            #     self.previos_window.close_to_edit_material = False
            #     del self
        self.open_new_window = False
        self.close()


if __name__ == "__main__":
    ...
