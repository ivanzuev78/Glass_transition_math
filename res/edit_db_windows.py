import sys
from typing import Iterable, List, Optional, Tuple, Union

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
    QPushButton,
    QTextBrowser,
)

from res.additional_funcs import set_qt_stile
from res.corrections import CorrectionFunction
from res.data_classes import DataMaterial, Profile


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
        self.data_material_widget.move(400, 30)

        self.profile_material_widget = ProfileMaterialWidget(self)
        self.profile_material_widget.move(10, 30)

        self.add_mat_but = QPushButton(self)
        self.add_mat_but.move(630, 30)
        self.add_mat_but.resize(120, 25)
        self.add_mat_but.setText("Добавить материал")

        self.profile_material_widget.data_material_widget = self.data_material_widget
        self.data_material_widget.profile_material_widget = self.profile_material_widget

        # РАБОТАЕТ
        self.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.main_window is not None and not self.close_to_edit_material:
            self.main_window.show()
            del self

    def faf(self):
        # Текущий ряд
        print(self.listwidget2.currentIndex().row())
        # Текущий текст
        print(self.listwidget2.currentIndex().data())

        print("faf")


class ProfileMaterialWidget(QListWidget):
    def __init__(self, parent: EditDataWindow):
        super().__init__(parent)
        self.edit_window = parent
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)
        self.resize(200, 450)
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
        self.resize(200, 450)
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

    def change_index_in_profile_material_widget(self):
        row = self.currentIndex().row()
        material = self.material_list[row]
        if material in self.profile_material_widget.profile_materials:
            index = self.profile_material_widget.profile_materials.index(material)
            self.profile_material_widget.setCurrentRow(index)

    def open_mat_editor(self):
        material = self.material_list[self.currentIndex().row()]
        self.mat_editor = EditMaterialWindow(self.edit_window, material)
        self.mat_editor.show()
        self.edit_window.close_to_edit_material = True
        self.edit_window.close()

    def add_material(self, material: DataMaterial):
        self.material_list.append(material)
        self.names_list.append(material.name)
        self.addItem(material.name)

    def mimeData(self, my_list: Iterable, lwi: QListWidgetItem = None):
        print("my_list", my_list, lwi)
        mimedata = super().mimeData(my_list)
        mimedata.setText(str(self.currentIndex().row()))
        return mimedata

    def dropMimeData(self, index, data, action):
        print("dropMimeData")
        if data.hasText():
            self.addItem(data.text())
            return True
        else:
            return super().dropMimeData(index, data, action)

    # вызывается при попадании в область
    def dragEnterEvent(self, e):
        print("dragEnterEvent")
        self.takeItem(0)
        print(e.mimeData())
        # Позволяет или нет перетащить объект в этот виджет
        e.accept()

    # вызывается при покидании области
    def dragLeaveEvent(self, e):
        print("QDragLeaveEvent")

        e.accept()

    def dropEvent(self, e):

        print("dropEvent")

        e.accept()
        print(e.mimeData().text())
        # self.addItem()


class CreateMaterialWindow(
    QtWidgets.QMainWindow, uic.loadUiType("windows/Add_material.ui")[0]
):
    def __init__(
        self, main_window: EditDataWindow, origin_material: DataMaterial = None
    ):
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


class EditCorrectionWindow(
    QtWidgets.QMainWindow, uic.loadUiType("windows/edit_correction.ui")[0]
):
    def __init__(self, previous_window, correction: CorrectionFunction = None):
        super(EditCorrectionWindow, self).__init__()
        self.setupUi(self)
        self.previos_window = previous_window
        self.correction = correction
        if correction is not None:
            # TODO Загрузка коррекции в окно
            ...

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


class EditMaterialWindow(
    QtWidgets.QMainWindow,
    uic.loadUiType("windows/edit_material_with_corrections.ui")[0],
):
    def __init__(self, previous_window: EditDataWindow, material: DataMaterial = None):
        super(EditMaterialWindow, self).__init__()
        self.setupUi(self)
        self.previos_window = previous_window
        self.profile = previous_window.profile
        self.material = material
        set_qt_stile("style.css", self)
        self.corrections: List[
            Tuple[CorrectionFunction, Tuple[float, float], Union[Tuple, None]]
        ] = []
        self.set_material()
        self.corrections_listWidget.currentItemChanged.connect(self.change_row)
        self.corrections_listWidget.itemDoubleClicked.connect(self.show_correction)

    def set_material(self):
        self.type_comboBox: QComboBox
        self.corrections_listWidget: QListWidget
        self.cor_textBrowser: QTextBrowser
        types = self.profile.get_all_types()
        self.type_comboBox.addItems(types)
        if self.material is not None:
            index = types.index(self.material.mat_type)
            self.type_comboBox.setCurrentIndex(index)
            self.name_lineEdit.setText(self.material.name)
            self.ew_lineEdit.setText(str(self.material.ew))
            self.corrections = self.material.correction.get_all_corrections()
            for correction in self.corrections:
                correction_func = correction.correction_func

                self.corrections_listWidget.addItem(correction_func.name)

    def change_row(self):
        self.corrections_listWidget: QListWidget
        self.cor_textBrowser: QTextBrowser
        row_numb = self.corrections_listWidget.currentRow()
        cor = self.corrections[row_numb]
        self.cor_textBrowser.setText(cor[0].comment)

    def show_correction(self):
        row_numb: int = self.corrections_listWidget.currentRow()
        cor, limit, pair = self.corrections[row_numb]
        import matplotlib.pyplot as plt
        import numpy as np

        x_min, x_max = limit
        # Data for plotting
        t = np.arange(x_min, x_max, 0.1)
        s = [cor(x) for x in t]

        fig, ax = plt.subplots()
        ax.plot(t, s)
        string = "систему в целом "
        ax.set(
            xlabel="Содержание вещества в системе, %",
            ylabel="Влияние на температуру стеклования, °С",
            title=f"Влияние '{self.material.name}' на {pair if pair is not None else string }",
        )
        ax.grid()

        fig.savefig("test.png")
        plt.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.previos_window.show()
        self.previos_window.close_to_edit_material = False
        del self


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = EditMaterialWindow(None)
    ex.show()
    sys.exit(app.exec_())
