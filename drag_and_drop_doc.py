from typing import Iterable

from PyQt5.QtWidgets import QListWidget, QListWidgetItem


class ProfileMaterialWidget(QListWidget):
    def __init__(self, parent):
        super().__init__(parent)

    def mimeTypes(self):
        # Сюда можно добавить свои типы, чтобы по ним проверять, но пока не разобрался
        mimetypes = super().mimeTypes()
        mimetypes.append("my_type")
        return mimetypes

    def mimeData(self, my_list: Iterable, lwi: QListWidgetItem = None):
        # Здесь задается информация для перетаскивания
        # https://doc.qt.io/qtforpython-5/PySide2/QtCore/QMimeData.html#PySide2.QtCore.PySide2.QtCore.QMimeData
        mimedata = super().mimeData(my_list)

        mimedata.setText("data text")
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
        # Позволяет перетащить объект в этот виджет
        e.accept()
        # e.ignore()

    # вызывается при покидании области
    def dragLeaveEvent(self, e):
        # e.ignore()
        e.accept()

    # вызывается, когда объект кидается в области
    def dropEvent(self, e):

        e.accept()

        index = int(e.mimeData().text())
        text = self.data_material_list.names_list[index]
        if text not in self.profile_materials_names:
            self.addItem(text)
            self.profile_materials_names.append(text)
