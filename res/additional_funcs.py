import numpy as np
from PyQt5.QtWidgets import QPushButton, QComboBox
from pandas import DataFrame
from PyQt5.QtGui import QBrush, QImage, QPalette


def normalize_df(df: DataFrame) -> DataFrame:
    sum_of_df = sum(df.sum())
    if sum_of_df == 0:
        # df.iloc[(df[df.columns].isna())] = 0
        return df
    return df / sum_of_df


def normalize(array: np.array) -> np.array:
    return array / array.sum()


def set_qt_stile(style_path, window):
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

