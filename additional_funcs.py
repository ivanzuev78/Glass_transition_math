import numpy as np
from PyQt5.QtGui import QImage, QPalette, QBrush
from pandas import DataFrame


def normalize_df(df: DataFrame) -> DataFrame:
    sum_of_df = sum(df.sum())
    if sum_of_df == 0:
        # df.iloc[(df[df.columns].isna())] = 0
        return df
    return df / sum_of_df


def normalize(array: np.array) -> np.array:
    return array / array.sum()


def set_qt_stile(buttons, style_path, window):
    oImage = QImage("fon.jpg")
    palette = QPalette()
    palette.setBrush(QPalette.Window, QBrush(oImage))
    window.setPalette(palette)

    with open(style_path, "r") as f:
        style, style_combobox, style_red_but = f.read().split("$split$")

    for but in buttons:
        window.__getattribute__(but).setStyleSheet(style)