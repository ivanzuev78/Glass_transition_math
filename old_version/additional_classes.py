from math import sqrt
from typing import Optional

from PyQt5 import QtCore, QtWidgets
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QLabel,
    QTabWidget,
    QTableWidget,
    QGridLayout,
    QTableWidgetItem,
    QSpacerItem,
)
from pandas import DataFrame, Series
import numpy as np

from Materials import normalize_df, get_ew_by_name

from additional_funcs import count_total_influence_df


class MyQLabel(QLabel):
    def __init__(self, hint: str, *args, **kwargs):
        super(MyQLabel, self).__init__(*args, **kwargs)
        self.__base_cor = True
        self.__extra_cor = True
        self.setFixedHeight(10)
        self.setFixedWidth(10)
        self.hint = hint
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

    def __del__(self):
        print(f"MyQLabel {self.hint} deleted")
        del self


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

    def del_item(self, item):
        index = self.all_labels.index(item)
        self.itemAt(index + 1).widget().setParent(None)
        self.all_labels.pop(index)


class MyMainQTabWidget(QTabWidget):
    def __init__(
        self,
        dict_of_df_inf_base: dict,
        dict_of_df_inf_extra: dict,
        percent_df: DataFrame,
        grid: MyQGridLayout,
        *args,
        **kwargs,
    ):
        super(MyMainQTabWidget, self).__init__(*args, **kwargs)
        self.base_tab = MyQTabWidget(dict_of_df_inf_base, percent_df, grid, True)
        self.extra_tab = MyQTabWidget(dict_of_df_inf_extra, percent_df, grid, False)
        self.addTab(self.base_tab, "Без избытка")
        self.addTab(self.extra_tab, "С избытком")

    def update_tabs(self, dict_of_df_inf_base, dict_of_df_inf_extra, percent_df):
        self.base_tab.update_tabs(dict_of_df_inf_base, percent_df)
        self.extra_tab.update_tabs(dict_of_df_inf_extra, percent_df)


class MyQTabWidget(QTabWidget):
    def __init__(
        self,
        dict_of_df_inf: dict,
        percent_df: DataFrame,
        grid: MyQGridLayout,
        main_inf: bool,
        *args,
        **kwargs,
    ):
        super(MyQTabWidget, self).__init__(*args, **kwargs)

        # TODO setStyle MyQTabWidget

        self.all_tabs = {}
        self.resize(500, 300)

        for name in dict_of_df_inf:
            table = MyQTabWidgetOneMaterial(
                name, dict_of_df_inf[name], percent_df, grid, main_inf
            )
            self.all_tabs[name] = table
            self.addTab(table, f"{name}")

    def update_tabs(self, dict_of_df_inf: dict, percent_df: DataFrame) -> None:
        for name in dict_of_df_inf:
            if name not in self.all_tabs:
                continue
            self.all_tabs[name].update_tables(dict_of_df_inf[name], percent_df)


class MyQTabWidgetOneMaterial(QTabWidget):
    def __init__(
        self,
        name: str,
        inf_df: DataFrame,
        percent_df: DataFrame,
        grid: MyQGridLayout,
        main_inf: bool,
        *args,
        **kwargs,
    ):
        super(MyQTabWidgetOneMaterial, self).__init__(*args, **kwargs)

        # TODO setStyle MyQTabWidgetOneMaterial

        self.inf_tab = MyQTableWidget(inf_df, name, grid, main_inf=main_inf)
        self.addTab(self.inf_tab, "Полное влияние")

        inf_percent_df = count_total_influence_df(percent_df, inf_df, save_na=True)

        self.inf_percent_tab = MyQTableWidget(inf_percent_df)
        self.addTab(self.inf_percent_tab, "Влияние на рецептуру")

        percent_of_inf_df = normalize_df(inf_percent_df) * 100
        percent_of_inf_df = percent_of_inf_df.applymap(
            lambda x: round(x, 2), na_action="ignore"
        )

        self.percent_of_inf_tab = MyQTableWidget(percent_of_inf_df, heatmap=True)
        self.addTab(self.percent_of_inf_tab, "Процент влияний")

    def update_tables(self, inf_df, percent_df):
        self.inf_tab.update_table(inf_df)
        inf_percent_df = count_total_influence_df(percent_df, inf_df, save_na=True)
        self.inf_percent_tab.update_table(inf_percent_df)
        percent_of_inf_df = normalize_df(inf_percent_df) * 100
        percent_of_inf_df = percent_of_inf_df.applymap(
            lambda x: round(x, 2), na_action="ignore"
        )
        self.percent_of_inf_tab.update_table(percent_of_inf_df)


class MyQTableWidget(QTableWidget):
    def __init__(
        self,
        df: DataFrame,
        name: str = "",
        grid: Optional[MyQGridLayout] = None,
        heatmap=False,
        main_inf=False,
        *args,
        **kwargs,
    ):
        super(MyQTableWidget, self).__init__(*args, **kwargs)

        self.df_with_items = DataFrame(
            index=df.index.tolist(), columns=df.columns.values.tolist()
        )

        headers = df.columns.values.tolist()
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        rows = df.index.tolist()
        self.setRowCount(len(rows))
        self.setVerticalHeaderLabels(rows)

        for index_epoxy, epoxy in enumerate(rows):
            for index_amine, amine in enumerate(headers):
                if grid is not None:
                    item = MyQTableWidgetItem(
                        df[amine][epoxy],
                        f"{name}: {epoxy} | {amine}",
                        grid,
                        heatmap,
                        main_inf,
                    )
                    self.df_with_items.loc[epoxy][amine] = item
                    self.setItem(index_epoxy, index_amine, item)
                else:
                    item = MyQTableWidgetItem(df[amine][epoxy], heatmap=heatmap)
                    self.df_with_items.loc[epoxy][amine] = item
                    self.setItem(index_epoxy, index_amine, item)

        # TODO setStyle MyQTableWidget
        pass

    def update_table(self, df: DataFrame):
        for epoxy in df.index.tolist():
            for amine in df.columns.values.tolist():
                item = self.df_with_items.loc[epoxy][amine]
                if not isinstance(item, MyQTableWidgetItem):
                    continue
                else:
                    item.set_value(df[amine][epoxy])


class MyQTableWidgetItem(QTableWidgetItem):
    def __init__(
        self,
        value: Optional[float],
        hint: str = "",
        grid: Optional[MyQGridLayout] = None,
        heatmap=None,
        main_inf: bool = False,
        *args,
        **kwargs,
    ):
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

        self.set_value(value)

    def set_label_correction(self, value):
        if self.label is not None:
            if self.main_inf:
                self.label.base_cor = value
            else:
                self.label.extra_cor = value

    @property
    def value(self):
        return self.__value

    def set_value(self, value):
        if isinstance(value, (Series, DataFrame)):
            self.setBackground(QColor("#000000"))
            return None
        self.__value = value
        if not self.heatmap:
            if str(value) != "nan":
                self.setText(str(round(value, 2)))
                self.setBackground(QColor("#00F000"))
                self.set_label_correction(True)
            else:
                self.setText("N/A")
                self.setBackground(QColor("red"))
                self.set_label_correction(False)
        else:
            if str(value) != "nan":
                value = float(value)
                color = (
                    255,
                    int(255 - 25.5 * sqrt(value)),
                    int(255 - 25.5 * sqrt(value)),
                )
                self.setBackground(QColor(*color))
                self.setText(str(round(value, 2)) + " %")
            else:
                self.setBackground(QColor("#FFFFFF"))
                self.setText("N/A")

    def __del__(self):
        if self.label is not None:
            self.grid.del_item(self.label)
            del self.label

        del self


class ReceiptCounter:
    def __init__(self, main_window: "MyMainWindow"):

        self.main_window = main_window
        self.material_types_a = []
        self.material_types_b = []
        self.material_names_a = []
        self.material_names_b = []
        self.percents_a = np.array([])
        self.percents_b = np.array([])
        self.ew_line_a = []
        self.ew_line_b = []
        self.ew_dict = {}
        self.ew_a = 0
        self.ew_b = 0

    def change_receipt(self, component, material_types, material_names):
        if "" in material_names:
            return None
        if component == "A":
            self.material_types_a = material_types
            self.material_names_a = material_names
            self.percents_a = np.array([0.0 for _ in material_names])
            ew_line_a = []
            for mat_type, name in zip(material_types, material_names):
                if name not in self.ew_dict:
                    ew = get_ew_by_name(name, mat_type, self.main_window.db_name)
                    if mat_type == "Amine":
                        ew = -ew
                    self.ew_dict[name] = ew
                ew_line_a.append(self.ew_dict[name])
            self.ew_line_a = np.array(ew_line_a)

        elif component == "B":
            self.material_types_b = material_types
            self.material_names_b = material_names
            self.percents_b = np.array([0.0 for _ in material_names])
            ew_line_b = []
            for mat_type, name in zip(material_types, material_names):
                if name not in self.ew_dict:
                    ew = get_ew_by_name(name, mat_type, self.main_window.db_name)
                    if mat_type == "Amine":
                        ew = -ew
                    self.ew_dict[name] = ew
                ew_line_b.append(self.ew_dict[name])
            self.ew_line_b = np.array(ew_line_b)

    def count_ew(self, component):
        if component == "A":
            eq = sum(self.percents_a / self.ew_line_a)
            if eq != 0:
                ew = 100 / eq
                self.main_window.a_ew = ew
                self.ew_a = ew
            else:
                self.main_window.a_ew = 0
                self.ew_a = 0

        elif component == "B":
            eq = sum(self.percents_b / self.ew_line_b)
            if eq != 0:
                ew = 100 / eq
                self.main_window.ew_b = ew
                self.ew_b = ew
            else:
                self.main_window.ew_b = 0
                self.ew_b = 0

    def set_percent(self, line, percent, component):
        if component == "A":
            self.percents_a[line] = percent
            self.count_parameters()

        elif component == "B":
            self.percents_b[line] = percent
            self.count_parameters()

    def count_parameters(self):
        sum_a = self.percents_a.sum()
        self.main_window.set_sum(sum_a, "A")
        sum_b = self.percents_b.sum()
        self.main_window.set_sum(sum_b, "B")

        if round(sum_a, 2) == 100:
            self.count_ew("A")
            self.main_window.a_ew = self.ew_a
        else:
            self.main_window.a_ew = 0

        if round(sum_b, 2) == 100:
            self.count_ew("B")
            self.main_window.ew_b = self.ew_b
        else:
            self.main_window.ew_b = 0

        if round(sum_a, 2) == 100 and round(sum_b, 2) == 100:
            self.main_window.count_all_parameters()

    def get_sum(self, component):
        return self.percents_a.sum() if component == "A" else self.percents_b.sum()
