from collections.abc import Iterable

import numpy as np
from PyQt5.QtWidgets import QPushButton, QComboBox, QLabel, QLineEdit, QTextEdit, QListWidget, QRadioButton
from pandas import DataFrame
from PyQt5.QtGui import QBrush, QImage, QPalette, QFont


def normalize_df(df: DataFrame) -> DataFrame:
    sum_of_df = sum(df.sum())
    if sum_of_df == 0:
        # df.iloc[(df[df.columns].isna())] = 0
        return df
    return df / sum_of_df


def normalize(array: np.array) -> np.array:
    return array / array.sum()


def set_qt_stile(style_path, window, *args):
    """
    Функция для установки стиля в окнах. Автоматически всё раскрашивает.
    :param style_path: Путь к файлу со стилями.
    :param window: Окно, в котором необходимо установить стиль
    :return:
    """
    oImage = QImage("fon.jpg")
    palette = QPalette()
    palette.setBrush(QPalette.Window, QBrush(oImage))
    window.setPalette(palette)

    with open(style_path, "r") as f:
        style, style_combobox, style_red_but = f.read().split("$split$")

    for attr_name, attr_instance in window.__dict__.items():
        if isinstance(attr_instance, QPushButton):
            attr_instance.setStyleSheet(style)
        elif isinstance(attr_instance, QComboBox):
            attr_instance.setStyleSheet(style_combobox)

    # Проходимся по неименованым переданным аргументам, ищем, что бы раскрасить
    for widget_list in args:
        # Предполагается, что передаются списки объектов, которым нужно установить стиль
        if isinstance(widget_list, Iterable):
            for attr_instance in widget_list:
                if isinstance(attr_instance, QPushButton):
                    attr_instance.setStyleSheet(style)
                elif isinstance(attr_instance, QComboBox):
                    attr_instance.setStyleSheet(style_combobox)
        # Но если вдруг это будут сами объекты, то им тоже попробуем установить стиль
        elif isinstance(widget_list, QPushButton):
            widget_list.setStyleSheet(style)
        elif isinstance(widget_list, QComboBox):
            widget_list.setStyleSheet(style_combobox)


def change_font(window, font_delta: int, *args):
    def font_changer(widget, fd):
        font: QFont = widget.font()
        size = font.pointSize()
        font.setPointSize(size + fd)
        widget.setFont(font)

    checker_list = (QLabel, QPushButton, QComboBox, QLineEdit, QTextEdit, QListWidget)
    for attr_name, attr_instance in window.__dict__.items():
        if isinstance(attr_instance, checker_list):
            font_changer(attr_instance, font_delta)
        elif isinstance(attr_instance, QRadioButton):
            font_changer(attr_instance, font_delta)
    # Проходимся по неименованым переданным аргументам, ищем, что бы раскрасить
    for widget_list in args:
        if isinstance(widget_list, Iterable):
            for attr_instance in widget_list:
                font_changer(attr_instance, font_delta)
        elif isinstance(widget_list, checker_list):
            font_changer(widget_list, font_delta)