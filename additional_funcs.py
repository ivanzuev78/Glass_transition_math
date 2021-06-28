from collections import defaultdict
from copy import copy
from typing import Union

import pandas as pd
import numpy as np
from PyQt5.QtWidgets import QFrame

from Materials import get_tg_influence, get_influence_func


class TgMaterialInfluence:
    def __init__(self, name: str, epoxy_list: list, amine_list: list, db_name: str):
        self.name = name
        self.epoxy_list = epoxy_list
        self.amine_list = amine_list
        self.empty_df = pd.DataFrame(
            np.zeros((len(epoxy_list), len(amine_list))),
            columns=amine_list,
            index=epoxy_list,
        )
        self.db_name = db_name
        self.existence_df: Union[pd.DataFrame, None] = None
        self.base_influence_dict: Union[callable, None] = None

        # Первый ключ - tuple(epoxy, amine). Второй ключ tuple(x_min, x_max). Вызовом передается значение
        # all_funcs[('KER-828', 'ИФДА')][(0.0, 26.0)](15)
        self.all_funcs: Union[defaultdict, None] = None

        self.fill_base_df(name, db_name)

    def fill_base_df(self, name, db_name):

        all_inf_mat = get_tg_influence(name, db_name)
        all_funcs = defaultdict(dict)
        existence_df = copy(self.empty_df)

        for mat_inf_dict in all_inf_mat:
            if mat_inf_dict["epoxy"] == "None" and mat_inf_dict["amine"] == "None":
                self.base_influence_dict = get_influence_func(
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
                if amine not in existence_df.columns.values.tolist():
                    existence_df[amine] = 0.0
                if epoxy not in existence_df.index.tolist():
                    existence_df.loc[epoxy] = 0.0
                existence_df[amine][epoxy] = 1.0

        self.all_funcs = all_funcs
        self.existence_df = existence_df

    def get_df_for_current_percent(self, percent):
        percent = percent * 100
        current_df = copy(self.empty_df)
        current_existence_df = copy(self.empty_df)
        for epoxy, amine in self.all_funcs:
            for x_min, x_max in self.all_funcs[(epoxy, amine)]:
                if x_min <= percent <= x_max:
                    current_df[amine][epoxy] = self.all_funcs[(epoxy, amine)][
                        (x_min, x_max)
                    ](percent)
                    current_existence_df[amine][epoxy] = 1.0
        return current_existence_df, current_df

    def __call__(self, percent: float, *args, **kwargs):
        return self.get_df_for_current_percent(percent)

    def __getitem__(self, percent):
        if self.base_influence_dict:
            return self.base_influence_dict(percent * 100)
        else:
            return 0.0


class QHLine(QFrame):
    def __init__(self):
        super(QHLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)

# if __name__ == "__main__":
#     epoxy_list = ["KER-828", "Лапроксид_БД"]
#     amine_list = ["ИФДА", "PACM", "MXDA"]
#     epoxy_list2 = ["KER-828", "Лапроксид_БД", "Херня"]
#     amine_list2 = ["ИФДА", "PACM"]
#
#     # create_df_influence('Бензиловый спирт', epoxy_list, amine_list, 'material.db')
#
#     item = TgMaterialInfluence(
#         "Бензиловый спирт", epoxy_list, amine_list, "material.db"
#     )
#     print(*item.get_df_for_current_percent(0.15999), sep='\n')
#     print(*item.get_df_for_current_percent(0.16), sep='\n')
#     print(*item.get_df_for_current_percent(0.160001), sep='\n')
