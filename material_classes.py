import math
import sqlite3
from collections import defaultdict
from copy import copy
from itertools import chain
from typing import List, Optional, Tuple, Union

import numpy as np
from pandas import DataFrame

# import init_class
from additional_funcs import normalize, normalize_df
from data_classes import Profile


class Material:
    def __init__(self, mat_type: str, mat_name: str, receipt: "Receipt"):
        self.__mat_type = mat_type
        self.__name = mat_name
        self.__ew = None
        self.receipt = receipt
        self.__percent: float = 0.0
        receipt.add_material(self)
        self.ew = self.receipt.profile.get_ew_by_name(mat_type, mat_name)

    @property
    def percent(self) -> float:
        return self.__percent

    @percent.setter
    def percent(self, value: float):
        # TODO сеттер на изменение процентов
        if isinstance(value, (float, int)):
            self.__percent = float(value)
            self.receipt.count_sum()

    @property
    def ew(self) -> float:
        return self.__ew

    @ew.setter
    def ew(self, value: float):
        # TODO сеттер на изменение ew
        if isinstance(value, float):
            if self.mat_type == "Amine":
                value = -value
            self.__ew = value

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str):
        # TODO сеттер на изменение материала
        if isinstance(value, str):
            self.__name = value
            self.receipt.update_all_pairs_material()

    @property
    def mat_type(self) -> str:
        return self.__mat_type

    @mat_type.setter
    def mat_type(self, value: str):
        # TODO сеттер на изменение типа материала
        if isinstance(value, str):
            self.__mat_type = value

    def set_type_and_name(self, mat_type: str, name: str) -> None:
        self.mat_type = mat_type
        self.name = name
        self.ew = self.receipt.profile.get_ew_by_name(mat_type, name)
        self.receipt.update_all_parameters()

    def __str__(self):
        return self.__name

    def __repr__(self):
        return "< " + self.receipt.component + "_" + self.__name + ">"

    def __float__(self):
        return self.__percent

    def __add__(self, other):
        return self.__percent + float(other)

    def __radd__(self, other):
        return self.__percent + float(other)

    def __rsub__(self, other):
        return float(other) - self.__percent


class Receipt:
    def __init__(self, component: str, profile: Profile):
        from qt_windows import MyMainWindow, PairReactWindow

        self.main_window: Optional[MyMainWindow] = None
        self.profile = profile
        self.materials: List[Material] = []
        self.sum_percent: float = 0.0
        self.component = component
        self.ew: Optional[float] = None
        self.receipt_counter: Optional[ReceiptCounter] = None
        self.scope_trigger: int = 0
        self.pair_react_window: Optional["PairReactWindow"] = None

        # TODO Поставить сеттер на передачу пар в окно синтеза
        self.all_pairs_material: List[(Material, Material)] = []

        self.react_pairs: List[(Material, Material)] = []

    def check_all_react(self):
        # TODO доделать
        for mat in self.materials:
            if self.ew and self.ew < 0:
                if mat.mat_type == "Amine":
                    if mat not in chain.from_iterable(self.react_pairs):
                        print("good")
                    else:
                        print("Bad")

    def add_material(self, material: Material):
        # TODO пересчёт всего в связи с изменением рецептуры
        self.materials.append(material)
        self.update_all_pairs_material()

    def set_main_window(self, main_window):
        self.main_window = main_window
        if self.component == "A":
            self.materials = self.main_window.material_list_a
        if self.component == "B":
            self.materials = self.main_window.material_list_b

    def remove_material(self):
        # TODO пересчёт всего в связи с изменением рецептуры
        del self.materials[-1]
        self.update_all_pairs_material()

    def count_sum(self):
        # Ждём, пока все материалы установят себе процент
        if self.scope_trigger:
            self.scope_trigger -= 1
            # Если остались ещё, то прерываем функцию и ждём остальных
            if not self.scope_trigger:
                return None
        self.sum_percent = round(sum(self.materials), 2)
        self.set_sum_to_qt()
        self.update_all_parameters()

    def __iter__(self):
        for material in self.materials:
            yield material
        return StopIteration

    def update_all_parameters(self):
        """
        Предполагается, что сумма процентов уже посчитана
        :return:
        """
        self.count_ew()
        self.receipt_counter.update_labels()

    def count_ew(self):
        if self.sum_percent == 100:
            inversed_ew = 0
            for material in self.materials:
                if material.mat_type in ("Epoxy", "Amine"):
                    if material.ew != 0:
                        inversed_ew += material.percent / material.ew
            if inversed_ew:
                self.ew = 100 / inversed_ew
            else:
                self.ew = None
        else:
            self.ew = None
        self.set_ew_to_qt()

    def set_sum_to_qt(self):
        self.main_window.set_sum(self.sum_percent, self.component)

    def set_ew_to_qt(self):
        self.main_window.set_ew(self.component, self.ew)

    def update_all_pairs_material(self):
        epoxy_list = []
        amine_list = []
        for mat in self.materials:
            if mat.mat_type == "Epoxy":
                epoxy_list.append(mat)
            elif mat.mat_type == "Amine":
                amine_list.append(mat)
        self.all_pairs_material = [
            (epoxy, amine) for epoxy in epoxy_list for amine in amine_list
        ]
        if self.pair_react_window is not None:
            self.pair_react_window.update_component(self.component)


class ReceiptCounter:
    def __init__(
        self,
        receipt_a: Receipt,
        receipt_b: Receipt,
        main_window,
        extra_ratio: bool = False,
    ):
        from qt_windows import MyMainWindow, PairReactWindow

        self.main_window: Optional[MyMainWindow] = main_window
        self.receipt_a = receipt_a
        self.receipt_b = receipt_b
        self.__tg: Optional[float] = None
        self.__mass_ratio: Optional[float] = None
        self.extra_ratio = extra_ratio
        self.percent_df: Optional[DataFrame] = None
        self.tg_df: Optional[DataFrame] = None

        # TODO прописать ссылки на окна для передачи параметров
        self.profile = self.main_window.profile
        self.pair_react_window: Optional[PairReactWindow] = None

    @property
    def tg(self):
        return self.__tg

    @tg.setter
    def tg(self, value):
        # TODO сеттер для передачи значений в окна
        self.__tg = value
        self.main_window.set_tg(value)

    @property
    def mass_ratio(self):
        return self.__mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value):
        # TODO сеттер для передачи значений в окна
        self.__mass_ratio = value
        self.main_window.set_mass_ratio(value)

    def count_mass_ratio(self):
        if self.receipt_a.ew and self.receipt_b.ew:
            if self.receipt_a.ew * self.receipt_b.ew < 0:
                self.mass_ratio = -self.receipt_a.ew / self.receipt_b.ew
                return None
        self.mass_ratio = None
        self.drop_labels()

    def count_percent_df(self):
        if (
            not (self.receipt_a.ew and self.receipt_b.ew)
            or self.receipt_a.ew * self.receipt_b.ew >= 0
        ):
            self.percent_df = None
            return None

        def count_reaction_in_component(
            names_list, eq_list, pair_react: List[Tuple[Material, Material]]
        ):

            # TODO Реализовать интерфейс для выбора взаимодействующий веществ (есть) + проверка, что все прореагировали
            # pair_react = [('KER-828', 'ИФДА'), ('KER-828', 'MXDA')]
            # на первом месте тот, кто прореагирует полностью
            # если наоборот, то поменять нужно
            # pair_react = [(i[1], i[0]) for i in pair_react]

            if not pair_react:
                return eq_list, []
            dict_react_index = defaultdict(list)
            pair_react_index = [
                (names_list.index(epoxy.name), names_list.index(amine.name))
                for epoxy, amine in pair_react
            ]
            dict_react_eq = defaultdict(list)

            # Здесь количество эквивалентов прореагировавших пар
            result_eq_table = []

            for epoxy, amine in pair_react_index:
                dict_react_index[epoxy].append(amine)
                dict_react_eq[epoxy].append(eq_list[amine])

            for epoxy in dict_react_eq:
                if sum(dict_react_eq[epoxy]) == 0:
                    dict_react_eq[epoxy] = [0 for _ in dict_react_eq[epoxy]]
                else:
                    dict_react_eq[epoxy] = [
                        amine / sum(dict_react_eq[epoxy])
                        for amine in dict_react_eq[epoxy]
                    ]

            for epoxy_index in dict_react_index:
                for amine_index, amine_percent in zip(
                    dict_react_index[epoxy_index], dict_react_eq[epoxy_index]
                ):
                    eq_reacted = (
                        names_list[epoxy_index],
                        names_list[amine_index],
                        eq_list[epoxy_index] * amine_percent,
                    )
                    eq_list[amine_index] += eq_list[epoxy_index] * amine_percent
                    result_eq_table.append(eq_reacted)
                eq_list[epoxy_index] = 0

            return eq_list, result_eq_table

        # Получаем все названия и % эпоксидки в Компоненте А
        a_types = [material.mat_type for material in self.receipt_a]
        a_names = [material.name for material in self.receipt_a]
        a_eq = [
            material.percent / material.ew * self.mass_ratio if material.ew * self.mass_ratio != 0 else 0
            for material in self.receipt_a
        ]

        # Получаем все названия и % эпоксидки в Компоненте B
        b_types = [material.mat_type for material in self.receipt_b]
        b_names = [material.name for material in self.receipt_b]
        b_eq = [material.percent / material.ew if material.ew != 0 else 0 for material in self.receipt_b]

        total_eq = math.fabs(sum(a_eq))

        pairs_a = self.pair_react_window.get_react_pairs("A")
        pairs_b = self.pair_react_window.get_react_pairs("B")
        if sum(a_eq) > 0:
            pairs_a = [(i[1], i[0]) for i in pairs_a]
        if sum(b_eq) > 0:
            pairs_b = [(i[1], i[0]) for i in pairs_b]

        a_eq, a_result_eq_table = count_reaction_in_component(a_names, a_eq, pairs_a)
        b_eq, b_result_eq_table = count_reaction_in_component(b_names, b_eq, pairs_b)

        a_names_only_react = []
        a_eq_only_react = []
        a_type = None
        if sum(a_eq) > 0:
            a_type = "Epoxy"
            for mat_type, name, eq in zip(a_types, a_names, a_eq):
                if mat_type == "Epoxy":
                    a_names_only_react.append(name)
                    a_eq_only_react.append(eq)
        elif sum(a_eq) < 0:
            a_type = "Amine"
            for mat_type, name, eq in zip(a_types, a_names, a_eq):
                if mat_type == "Amine":
                    a_names_only_react.append(name)
                    a_eq_only_react.append(eq)

        b_names_only_react = []
        b_eq_only_react = []
        b_type = None
        if sum(b_eq) > 0:
            b_type = "Epoxy"
            for mat_type, name, eq in zip(b_types, b_names, b_eq):
                if mat_type == "Epoxy":
                    b_names_only_react.append(name)
                    b_eq_only_react.append(eq)
        elif sum(b_eq) < 0:
            b_type = "Amine"
            for mat_type, name, eq in zip(b_types, b_names, b_eq):
                if mat_type == "Amine":
                    b_names_only_react.append(name)
                    b_eq_only_react.append(eq)

        if a_type == b_type:
            return None

        a_eq_only_react_percent = normalize(np.array(a_eq_only_react))
        b_eq_only_react_percent = normalize(np.array(b_eq_only_react))

        # Получаем матрицу процентов пар
        percent_matrix = np.outer(a_eq_only_react_percent, b_eq_only_react_percent)

        eq_matrix = percent_matrix * total_eq

        # Получаем dataframe процентов пар
        df_eq_matrix = DataFrame(
            eq_matrix,
            index=a_names_only_react,
            columns=b_names_only_react,
        )

        # Учитываем реакцию в ступенчатом синтезе
        if a_type == "Amine":
            df_eq_matrix = df_eq_matrix.T

            for pair in a_result_eq_table:
                if pair[0] not in df_eq_matrix.index.tolist():
                    df_eq_matrix.loc[pair[0]] = [
                        0 for _ in range(len(df_eq_matrix.columns.values.tolist()))
                    ]
                df_eq_matrix[pair[1]][pair[0]] += pair[2]

        else:
            for pair in a_result_eq_table:
                if pair[0] not in df_eq_matrix.columns.values.tolist():
                    df_eq_matrix[pair[0]] = [
                        0 for _ in range(len(df_eq_matrix.index.tolist()))
                    ]

                # TODO тут что-то ломается. KeyError
                df_eq_matrix[pair[0]][pair[1]] += pair[2]

        if b_type == "Amine":

            for pair in b_result_eq_table:
                if pair[0] not in df_eq_matrix.index.tolist():
                    df_eq_matrix.loc[pair[0]] = [
                        0 for _ in range(len(df_eq_matrix.columns.values.tolist()))
                    ]

                df_eq_matrix[pair[1]][pair[0]] += pair[2]

        else:
            for pair in b_result_eq_table:
                if pair[0] not in df_eq_matrix.columns.values.tolist():
                    df_eq_matrix[pair[0]] = [
                        0 for _ in range(len(df_eq_matrix.index.tolist()))
                    ]

                if pair[1] not in df_eq_matrix.index.values.tolist():
                    df_eq_matrix.loc[pair[1]] = [
                        0 for _ in range(len(df_eq_matrix.columns.tolist()))
                    ]

                df_eq_matrix[pair[0]][pair[1]] += pair[2]

        percent_df = normalize_df(df_eq_matrix)

        # Сохраняем матрицу процентов пар
        self.percent_df = copy(percent_df)

    def count_tg(self):
        self.count_percent_df()
        if self.percent_df is None:
            return None
        if self.tg_df is None:
            self.get_tg_df()

        percent_df = self.percent_df
        tg_df = self.tg_df
        # Получаем все пары, которые не имеют стекла
        all_pairs_na = []
        for name in tg_df:
            pairs_a = tg_df[tg_df[name].isna()]
            par = [(resin, name) for resin in list(pairs_a.index)]
            all_pairs_na += par

        # TODO реализовать обработку отсутствующих пар стёкол
        all_pairs_na_dict = {}
        # Убираем в матрице процентов отсутствующие пары
        for resin, amine in all_pairs_na:
            if amine in percent_df.columns and resin in percent_df.index:
                # all_pairs_na_dict[(resin, amine)] = percent_df[amine][resin]
                percent_df[amine][resin] = 0.0

        # self.all_pairs_na_tg = all_pairs_na_dict
        percent_df = normalize_df(percent_df)

        # Сотрирует строки и столбцы. В данный момент не актуально
        # tg_df = tg_df[df_eq_matrix.columns.values.tolist()]
        # tg_df = tg_df.T
        # tg_df = tg_df[df_eq_matrix.index.tolist()].T

        total_tg_df = tg_df * percent_df
        primary_tg = sum(total_tg_df.sum())
        self.tg = primary_tg
        # TODO продолжить

    def get_tg_df(self) -> None:
        tg_df = self.profile.get_tg_df()
        if self.percent_df is not None:
            # дропаем неиспользуемые колонки и строки стеклования
            for name in tg_df:
                if name not in self.percent_df.columns.values.tolist():
                    tg_df = tg_df.drop(name, 1)
            for name in tg_df.index:
                if name not in self.percent_df.index.tolist():
                    tg_df = tg_df.drop(name)
        self.tg_df = tg_df

    def drop_labels(self) -> None:
        """
        Убирает все расчёты, когда одна из сумм рецептуры не равна 100
        :return:
        """
        self.mass_ratio = None
        self.tg = None

    def update_labels(self) -> None:
        """
        Пересчитывает все показатели в программе
        :return:
        """
        if self.receipt_a.sum_percent == 100 and self.receipt_b.sum_percent == 100:
            self.count_mass_ratio()
            self.count_tg()
            self.count_percent_df()
        else:
            self.drop_labels()
