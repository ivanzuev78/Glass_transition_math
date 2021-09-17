import sys
from typing import Iterable, List, Optional, Tuple, Union

from PyQt5 import QtCore, QtGui, QtWidgets, uic
from PyQt5.QtCore import QMimeData
from PyQt5.QtGui import QDropEvent
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QWidget,
)

from additional_funcs import set_qt_stile
from data_classes import DataMaterial


class EditMaterialWindow(QWidget):
    def __init__(self, profile_window: "ProfileManagerWindow" = None):
        super().__init__()
        self.title = "PyQt5 drag and drop"
        self.left = 500
        self.top = 400
        self.width = 800
        self.height = 500
        self.initUI()
        self.profile_window = profile_window
        self.close_to_edit_material = False

        self.buttons = []
        # Вынести путь к стилю в настройки
        set_qt_stile("style.css", self, comboboxes=self.buttons)

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.data_material_widget = DataMaterialWidget(self)
        self.data_material_widget.move(400, 30)

        self.profile_material_widget = ProfileMaterialWidget(self)
        self.profile_material_widget.move(10, 30)

        self.profile_material_widget.data_material_widget = self.data_material_widget
        self.data_material_widget.profile_material_widget = self.profile_material_widget

        # РАБОТАЕТ

        self.show()

    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        if self.profile_window is not None and not self.close_to_edit_material:
            self.profile_window.show()
            del self

    def faf(self):
        # Текущий ряд
        print(self.listwidget2.currentIndex().row())
        # Текущий текст
        print(self.listwidget2.currentIndex().data())

        print("faf")


class ProfileMaterialWidget(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.main_window = parent
        self.setAcceptDrops(True)
        # self.setDragEnabled(True)
        self.resize(200, 450)
        self.data_material_widget: Optional[
            DataMaterialWidget
        ] = parent.data_material_widget
        self.profile_materials = []
        self.profile_materials_names = []
        self.currentItemChanged.connect(self.change_index_in_data_material_widget)
        self.itemDoubleClicked.connect(self.data_material_widget.open_mat_editor)

    def change_index_in_data_material_widget(self):
        text = self.currentIndex().data()
        if text in self.data_material_widget.names_list:
            index = self.data_material_widget.names_list.index(text)
            self.data_material_widget.setCurrentRow(index)

    def mimeTypes(self):
        mimetypes = super().mimeTypes()
        mimetypes.append("qitem")
        return mimetypes

    def mimeData(self, my_list: Iterable, lwi: QListWidgetItem = None):
        print("my_list", my_list)
        mimedata = super().mimeData(my_list)

        mimedata.setText("qqqqq")
        return mimedata
        pass

    def dropMimeData(self, index, data, action):
        print("dropMimeData")
        if data.hasText():
            self.addItem(data.text())
            return True
        else:
            return super().dropMimeData(index, data, action)

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
        # e.accept()
        e.ignore()
        index = int(e.mimeData().text())
        text = self.data_material_widget.names_list[index]
        if text not in self.profile_materials_names:
            self.addItem(text)
            self.profile_materials_names.append(text)


class DataMaterialWidget(QListWidget):
    def __init__(self, parent: EditMaterialWindow):
        super().__init__(parent)
        self.main_window = parent

        # self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.resize(200, 450)
        self.material_list = []
        self.names_list = []
        self.profile_material_widget: Optional[ProfileMaterialWidget] = None
        self.itemDoubleClicked.connect(self.open_mat_editor)
        self.currentItemChanged.connect(self.change_index_in_profile_material_widget)

        # DEBUG
        for i in range(200):
            self.addItem(f"hare {i}")
            self.names_list.append(f"hare {i}")

    def change_index_in_profile_material_widget(self):
        text = self.currentIndex().data()
        if text in self.profile_material_widget.profile_materials_names:
            index = self.profile_material_widget.profile_materials_names.index(text)
            self.profile_material_widget.setCurrentRow(index)

    def open_mat_editor(self):
        self.mat_editor = MatEditor(self.main_window)
        self.mat_editor.show()
        self.main_window.close_to_edit_material = True
        self.main_window.close()

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


class MatEditor(QtWidgets.QMainWindow, uic.loadUiType("windows/Add_material.ui")[0]):
    def __init__(
        self, main_window: EditMaterialWindow, origin_material: DataMaterial = None
    ):
        super(MatEditor, self).__init__()
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

        self.buttons = ["type_comboBox", "save_but", "cancel_but"]
        self.comboboxes = ["type_comboBox"]
        # Вынести путь к стилю в настройки
        set_qt_stile(
            "style.css", self, buttons=self.buttons, comboboxes=self.comboboxes
        )

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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = EditMaterialWindow()
    sys.exit(app.exec_())
