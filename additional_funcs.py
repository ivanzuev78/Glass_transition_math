from collections import defaultdict
from copy import copy
from typing import Union, Dict

import pandas as pd
from PyQt5 import QtCore
from PyQt5.QtCore import QRect
from PyQt5.QtGui import QImage, QPalette, QBrush, QColor
from PyQt5.QtWidgets import QFrame, QTabWidget, QTableWidget, QTableWidgetItem
from pandas import DataFrame

from Materials import get_tg_influence, get_influence_func, normalize_df


class TgMaterialInfluence:
    def __init__(self, name: str, epoxy_list: list, amine_list: list, db_name: str):
        self.name = name
        self.epoxy_list = epoxy_list
        self.amine_list = amine_list
        self.nan_df = pd.DataFrame(
            columns=amine_list,
            index=epoxy_list,
        )
        self.db_name = db_name
        self.existence_df: Union[pd.DataFrame, None] = None
        self.base_influence_dict: Union[dict, None] = {}

        # Первый ключ - tuple(epoxy, amine). Второй ключ tuple(x_min, x_max). Вызовом передается значение
        # all_funcs[('KER-828', 'ИФДА')][(0.0, 26.0)](15)
        self.all_funcs: Union[defaultdict, None] = None
        self.fill_base_df(name, db_name)

    def fill_base_df(self, name: str, db_name: str) -> None:
        all_inf_mat = get_tg_influence(name, db_name)
        all_funcs = defaultdict(dict)
        for mat_inf_dict in all_inf_mat:
            if mat_inf_dict["epoxy"] == "None" and mat_inf_dict["amine"] == "None":
                self.base_influence_dict[
                    (mat_inf_dict["x_min"], mat_inf_dict["x_max"])
                ] = get_influence_func(
                    mat_inf_dict["k0"],
                    mat_inf_dict["ke"],
                    mat_inf_dict["kexp"],
                    mat_inf_dict["k1"],
                    mat_inf_dict["k2"],
                    mat_inf_dict["k3"],
                    mat_inf_dict["k4"],
                    mat_inf_dict["k5"],
                )
            else:
                epoxy = mat_inf_dict["epoxy"]
                amine = mat_inf_dict["amine"]
                all_funcs[(epoxy, amine)][
                    (mat_inf_dict["x_min"], mat_inf_dict["x_max"])
                ] = get_influence_func(
                    mat_inf_dict["k0"],
                    mat_inf_dict["ke"],
                    mat_inf_dict["kexp"],
                    mat_inf_dict["k1"],
                    mat_inf_dict["k2"],
                    mat_inf_dict["k3"],
                    mat_inf_dict["k4"],
                    mat_inf_dict["k5"],
                )
        self.all_funcs = all_funcs

    def get_df_for_current_percent(self, percent: float) -> DataFrame:
        percent = percent * 100
        current_df = copy(self.nan_df)
        for epoxy, amine in self.all_funcs:
            for x_min, x_max in self.all_funcs[(epoxy, amine)]:
                if x_min <= percent <= x_max:
                    current_df[amine][epoxy] = self.all_funcs[(epoxy, amine)][
                        (x_min, x_max)
                    ](percent)
        return current_df

    def __call__(self, percent: float, *args, **kwargs) -> DataFrame:
        return self.get_df_for_current_percent(percent)

    def __getitem__(self, percent: float) -> Union[float, None]:
        percent = percent * 100
        for x_min, x_max in self.base_influence_dict:
            if x_min <= percent <= x_max:
                return self.base_influence_dict[(x_min, x_max)](percent)
        else:
            return None


def create_tab_with_tables(dict_of_df: Dict) -> QTabWidget:

    tabWidget = QTabWidget()
    tabWidget.setWindowTitle('Спектр влияний')
    tabWidget.setMovable(True)
    tabWidget.setGeometry(QRect(0, 0, 281, 251))
    tabWidget.setObjectName("tabWidget")

    css = """
            QTabWidget::pane {
            background: transparent;
            border:0;
            }
            /*
            QTabBar::tab:selected  {
            background-color: red;
            border-radius: 6px;
            border-color: #000000;
            border: 1px solid #586072;
            padding: 1px;
            font: 9;
            }
            */
            """

    css2 = """
            QTableWidget{
            background: transparent;
            border:0;
            
            }
            QTabWidget::pane{
            background-color: #CBDBFF;
            border-radius: 6px;
            border-color: #000000;
            border: 1px solid #586072;
            padding: 1px;
            font: 9;
        
        }
            
            QHeaderView::section {
            background: transparent;
            padding: 4px;

            border-style: none;
            border-bottom: 1px solid #fffff8;
            border-right: 1px solid #fffff8;
        }
            QTableView QTableCornerButton::section{
            background: transparent;
            }
                        
            """

    tabWidget.setStyleSheet(css)

    oImage = QImage("fon.jpg")
    # sImage = oImage.scaled(QSize(self.window_height, self.window_width))
    palette = QPalette()
    palette.setBrush(QPalette.Background, QBrush(oImage))
    tabWidget.setPalette(palette)

    tabs = []
    for name in dict_of_df:
        table = QTableWidget()
        table.setStyleSheet(css2)
        # table.setPalette(palette)
        # table.setBackgroundRole(palette)

        inf_df = dict_of_df[name]
        df_exists = get_existence_df(inf_df)
        headers = df_exists.columns.values.tolist()
        table.setColumnCount(len(headers))
        table.setHorizontalHeaderLabels(headers)
        rows = df_exists.index.tolist()
        table.setRowCount(len(rows))
        table.setVerticalHeaderLabels(rows)
        tabWidget.addTab(table, f"{name}")
        tabs.append(table)



        for index_epoxy, epoxy in enumerate(rows):
            for index_amine, amine in enumerate(headers):
                cell_exists = df_exists[amine][epoxy]
                cell_percent = inf_df[amine][epoxy]
                # Продумать условие получше
                if cell_exists != 0:
                    item = QTableWidgetItem(str(round(cell_percent, 4)))
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)
                    item.setBackground(QColor('#00F000'))
                    table.setItem(index_epoxy, index_amine, item)
                else:
                    item = QTableWidgetItem('N/A')
                    item.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsEnabled)
                    item.setBackground(QColor('red'))
                    table.setItem(index_epoxy, index_amine, item)




    return tabWidget


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)


def count_total_influence_df(df_percent: DataFrame, df_inf: DataFrame, save_na: bool = False):
    return normalize_df(df_percent * get_existence_df(df_inf, save_na)) * df_inf


def get_existence_df(df: DataFrame, save_na: bool = False) -> DataFrame:
    df.iloc[(df[df.columns] > 0)] = 1
    if not save_na:
        df.iloc[(df[df.columns].isna())] = 0
    return df


if __name__ == "__main__":
    epoxy_list = ["KER-828", "Лапроксид_БД"]
    amine_list = ["ИФДА", "PACM", "MXDA"]
    epoxy_list2 = ["KER-828", "Лапроксид_БД", "Херня"]
    amine_list2 = ["ИФДА", "PACM"]

    index_1 = [str(i) for i in range(5)]
    colums_1 = [i for i in 'abcde']
    index_2 = [str(i) for i in range(8)]
    colums_2 = [i for i in 'abcdefg']

    df_1 = DataFrame(index=index_1, columns=colums_1)
    print(df_1)



