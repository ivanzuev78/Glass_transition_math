from copy import copy
from typing import Optional, Union

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QLabel, QTabWidget, QTableWidget, QGridLayout, QTableWidgetItem, QSpacerItem
from pandas import DataFrame
import numpy as np

from Materials import normalize_df
from additional_funcs import count_total_influence_df


class MyQLabel(QLabel):
    def __init__(self, hint: str, *args, **kwargs):
        super(MyQLabel, self).__init__(*args, **kwargs)
        self.__base_cor = True
        self.__extra_cor = True
        self.setFixedHeight(10)
        self.setFixedWidth(10)
        self.setToolTip(hint)
        self.set_color()

    def set_color(self):
        if self.base_cor and self.extra_cor:
            self.setStyleSheet("background-color: rgb(0, 255, 0);")
        elif self.base_cor or self.extra_cor:
            self.setStyleSheet("background-color: rgb(255, 155, 0);")
        else:
            self.setStyleSheet("background-color: rgb(255, 0, 0);")

    @property
    def base_cor(self):
        return self.__base_cor

    @base_cor.setter
    def base_cor(self, value: bool):
        self.__base_cor = value
        self.set_color()

    @property
    def extra_cor(self):
        return self.__extra_cor

    @extra_cor.setter
    def extra_cor(self, value: bool):
        self.__extra_cor = value
        self.set_color()


class MyQGridLayout(QGridLayout):
    def __init__(self, *args, **kwargs):
        super(MyQGridLayout, self).__init__(*args, **kwargs)

        self.setSizeConstraint(QtWidgets.QLayout.SetMinimumSize)
        self.setContentsMargins(0, 0, 0, 0)
        self.setSpacing(5)
        self.setObjectName("warring_grid")
        self.addItem(QSpacerItem(1, 1), 1000, 0, 1000, 10)

        self.all_labels = []

    def add_label(self, label):
        row = len(self.all_labels) // 10
        col = len(self.all_labels) % 10
        self.all_labels.append(label)
        self.addWidget(label, row, col)

        pass

    def update_items(self):
        pass


class MyQTabWidget(QTabWidget):
    def __init__(self, dict_of_df_inf: dict, percent_df: DataFrame, grid: MyQGridLayout, main_inf: bool, *args, **kwargs):
        super(MyQTabWidget, self).__init__(*args, **kwargs)

        # TODO setStyle MyQTabWidget

        self.all_tabs = {}

        for name in dict_of_df_inf:
            table = MyQTabWidgetOneMaterial(name, dict_of_df_inf[name], percent_df, grid, main_inf)
            self.all_tabs[name] = table
            self.addTab(table, f"{name}")



class MyQTabWidgetOneMaterial(QTabWidget):
    def __init__(self, name: str, inf_df: DataFrame, percent_df: DataFrame, grid: MyQGridLayout, main_inf:bool, *args, **kwargs):
        super(MyQTabWidgetOneMaterial, self).__init__(*args, **kwargs)

        # TODO setStyle MyQTabWidgetOneMaterial

        self.inf_tab = MyQTableWidget(inf_df, name, grid, main_inf=main_inf)
        self.addTab(self.inf_tab, "Полное влияние")

        inf_percent_df = count_total_influence_df(percent_df, inf_df)

        self.inf_percent_tab = MyQTableWidget(inf_percent_df)
        self.addTab(self.inf_percent_tab, "Влияние на рецептуру")

        percent_of_inf_df = normalize_df(inf_percent_df) * 100
        percent_of_inf_df = percent_of_inf_df.applymap(lambda x: round(x, 2), na_action='ignore')

        # TODO передать heatmap=True, когда она будет прописана
        self.percent_of_inf_tab = MyQTableWidget(percent_of_inf_df, heatmap=True)
        self.addTab(self.percent_of_inf_tab, "Процент влияний")



class MyQTableWidget(QTableWidget):
    def __init__(self, df: DataFrame, name: str = '',
                 grid: Optional[MyQGridLayout] = None, heatmap=False, main_inf=False, *args, **kwargs):
        super(MyQTableWidget, self).__init__(*args, **kwargs)

        self.df_with_items = copy(df)

        headers = df.columns.values.tolist()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        rows = df.index.tolist()
        self.setRowCount(len(rows))
        self.setVerticalHeaderLabels(rows)

        for index_epoxy, epoxy in enumerate(rows):
            for index_amine, amine in enumerate(headers):
                if grid is not None:
                    item = MyQTableWidgetItem(df[amine][epoxy], f'{name}: {epoxy} | {amine}', grid, heatmap, main_inf)
                    self.df_with_items[amine][epoxy] = item
                    self.setItem(index_epoxy, index_amine, item)
                else:
                    item = MyQTableWidgetItem(df[amine][epoxy], heatmap=heatmap)
                    self.df_with_items[amine][epoxy] = item
                    self.setItem(index_epoxy, index_amine, item)

        # TODO setStyle MyQTableWidget

    def update_table(self, df: DataFrame):
        for epoxy in df.index.tolist():
            for amine in df.columns.values.tolist():
                self.df_with_items[amine][epoxy].value = df[amine][epoxy]




class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(self, value: Optional[float], hint: str = '', grid: Optional[MyQGridLayout] = None,
                 heatmap=None, main_inf: bool=False, *args, **kwargs):
        super(MyQTableWidgetItem, self).__init__(*args, **kwargs)


        self.heatmap = heatmap
        self.hint = hint
        self.main_inf = main_inf

        self.__value = None
        self.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)
        self.grid = grid

        if grid is not None:
            self.label = MyQLabel(hint)
            grid.add_label(self.label)
        else:
            self.label = None

        self.value = value

    def set_label_correction(self, value):
        if self.label is not None:
            if self.main_inf:
                self.label.base_cor = value
            else:
                self.label.extra_cor = value

    @property
    def value(self):
        return self.__value

    @value.setter
    def value(self, value):
        self.__value = value
        if not self.heatmap:
            if str(value) != 'nan':
                self.setText(str(round(value, 4)))
                self.setBackground(QColor('#00F000'))
                self.set_label_correction(True)
            else:
                self.setText('N/A')
                self.setBackground(QColor('red'))
                self.set_label_correction(False)
        else:
            # TODO Подобрать цвета для градиента
            if str(value) != 'nan':
                if 0 <= value <= 5:
                    color = '#200000'
                elif 5 < value <= 10:
                    color = '#300000'
                elif 10 < value <= 15:
                    color = '#400000'
                elif 15 < value <= 20:
                    color = '#600000'
                elif 20 < value <= 30:
                    color = '#800000'
                elif 30 < value <= 40:
                    color = '#A00000'
                elif 40 < value <= 50:
                    color = '#A00000'
                elif 50 < value <= 70:
                    color = '#A00000'
                else:
                    color = '#F00000'
                self.setBackground(QColor(color))
                self.setText(str(round(value, 2)) + ' %')
            else:
                self.setBackground(QColor('#000000'))
                self.setText('N/A')

        # TODO построить heatmap для процентов влияния

    def __del__(self):
        if self.label is not None:
            del self.label
            self.grid.update_items()
        del self

