import math
import os
import sqlite3
from collections import defaultdict
from copy import copy, deepcopy
from datetime import datetime
from itertools import chain
from math import exp
from typing import Any, Dict, Iterable, List, Optional, Tuple, Union
from openpyxl.utils import get_column_letter as letter

import numpy as np
import pandas
from PyQt5.QtWidgets import QWidget
from pandas import DataFrame
# import init_class
from res.additional_funcs import normalize, normalize_df


class Material:
    def __init__(self, mat_type: str, mat_index: int, profile: "Profile", receipt: "Receipt"):
        self.profile = profile
        self.__mat_type = None
        self.__name = None
        self.__ew = None
        self.__data_material = None
        self.__percent: float = 0.0
        self.receipt = receipt
        self.set_type_and_name(mat_type, mat_index)
        receipt.add_material(self)

    @property
    def data_material(self) -> "DataMaterial":
        return self.__data_material

    @data_material.setter
    def data_material(self, data_material):
        if data_material is not None:
            self.mat_type = data_material.mat_type
            self.name = data_material.name
            self.ew = data_material.ew
            self.__data_material = data_material

    @property
    def percent(self) -> float:
        return self.__percent

    @percent.setter
    def percent(self, value: float):
        # TODO сеттер на изменение процентов
        if isinstance(value, (float, int)):
            self.__percent = value
            self.data_material.correction.percent = value
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
        else:
            self.__ew = 0

    @property
    def name(self) -> str:
        return self.__name

    @name.setter
    def name(self, value: str):
        # TODO сеттер на изменение материала
        if isinstance(value, str):
            self.__name = value

    @property
    def mat_type(self) -> str:
        return self.__mat_type

    @mat_type.setter
    def mat_type(self, value: str):
        # TODO сеттер на изменение типа материала
        if isinstance(value, str):
            self.__mat_type = value

    def set_type_and_name(self, mat_type: str, mat_index: int) -> None:
        self.data_material = self.profile.get_data_material(mat_type, mat_index)
        self.receipt.update_all_pairs_material()
        self.receipt.update_all_parameters()

    def __str__(self):
        return self.__name

    def __repr__(self):
        return "< " + self.receipt.component + "_" + self.__name + ">"

    def __float__(self):
        return float(self.__percent)

    def __add__(self, other):
        return self.__percent + float(other)

    def __radd__(self, other):
        return self.__percent + float(other)

    def __rsub__(self, other):
        return float(other) - self.__percent


class Receipt:
    def __init__(self, component: str, profile: "Profile"):
        from res.qt_windows import MyMainWindow, PairReactWindow

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

    # def check_all_react(self):
    #     # TODO доделать
    #     for mat in self.materials:
    #         if self.ew and self.ew < 0:
    #             if mat.mat_type == "Amine":
    #                 if mat not in chain.from_iterable(self.react_pairs):
    #                     print("good")
    #                 else:
    #                     print("Bad")

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

    def __getitem__(self, index):
        return self.materials[index]

    def __len__(self):
        return len(self.materials)

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
        self.pairs = []
        from res.qt_windows import MyMainWindow, PairReactWindow

        self.main_window: Optional[MyMainWindow] = main_window
        self.receipt_a = receipt_a
        self.receipt_b = receipt_b
        self.__tg: Optional[float] = None
        self.__tg_inf: Optional[float] = None
        self.__mass_ratio: Optional[float] = None
        self.extra_ratio = extra_ratio
        self.percent_df: Optional[MyTableCounter] = None
        self.__tg_df: Optional[DataFrame] = None

        self.tg_correction_manager: Optional[TgCorrectionManager] = None

        # TODO прописать ссылки на окна для передачи параметров
        self.profile = self.main_window.profile
        self.pair_react_window: Optional[PairReactWindow] = None

    @property
    def tg_df(self):
        if self.__tg_df is None:
            self.update_tg_df()
        return self.__tg_df

    @tg_df.setter
    def tg_df(self, value):
        self.__tg_df = value

    @property
    def tg(self):
        return self.__tg

    @tg.setter
    def tg(self, value):
        # TODO сеттер для передачи значений в окна
        self.__tg = value
        self.main_window.set_tg(value)

    @property
    def tg_inf(self):
        return self.__tg_inf

    @tg_inf.setter
    def tg_inf(self, value):
        # TODO сеттер для передачи значений в окна
        self.__tg_inf = value
        self.main_window.set_tg_inf(value)

    @property
    def mass_ratio(self):
        return self.__mass_ratio

    @mass_ratio.setter
    def mass_ratio(self, value):
        # TODO сеттер для передачи значений в окна
        self.__mass_ratio = value
        self.main_window.set_mass_ratio(value)

    def count_mass_ratio(self):
        self.mass_ratio = -self.receipt_a.ew / self.receipt_b.ew

    def count_percent_df(self):
        """

        :return:
        """
        a_eq_dict = {material: material.percent / material.ew * self.mass_ratio
        if material.ew * self.mass_ratio != 0 else 0 for material in self.receipt_a if
                     material.mat_type in ('Amine', "Epoxy")}

        b_eq_dict = {
            material: material.percent / material.ew if material.ew != 0 else 0
            for material in self.receipt_b if material.mat_type in ("Amine", "Epoxy")}

        pairs_a = self.pair_react_window.get_react_pairs("A")
        if self.receipt_a.ew < 0:
            pairs_a = [(pair[1], pair[0]) for pair in pairs_a]
        pairs_b = self.pair_react_window.get_react_pairs("B")
        if self.receipt_b.ew < 0:
            pairs_b = [(pair[1], pair[0]) for pair in pairs_b]

        new_eq_a, a_reacted_dict = count_first_state(a_eq_dict, pairs_a)
        new_eq_b, b_reacted_dict = count_first_state(b_eq_dict, pairs_b)

        df = MyTableCounter(is_percent_table=True)
        sum_a = round(sum(new_eq_a.values()), 6)
        sum_b = round(sum(new_eq_b.values()), 6)

        # if sum_a != - sum_b:
        #     print('count_percent_df - Сумма эквивалентов не сходится!')
        #     print(sum_a, sum_b)

        a_percent_dict = {mat: eq / sum_a for mat, eq in new_eq_a.items()}
        b_percent_dict = {mat: eq / sum_b for mat, eq in new_eq_b.items()}

        if sum_a > 0 and sum_b < 0:
            # a - Epoxy, b - Amine
            epoxy_percent_dict = a_percent_dict
            amine_percent_dict = b_percent_dict
        elif sum_a < 0 and sum_b > 0:
            # a - Amine, b - Epoxy
            epoxy_percent_dict = b_percent_dict
            amine_percent_dict = a_percent_dict
        else:
            # print("count_percent_df - продукты не реагируют")
            return None

        for material_epoxy, percent_epoxy in epoxy_percent_dict.items():
            for material_amine, percent_amine in amine_percent_dict.items():
                df.set_value(material_epoxy.data_material, material_amine.data_material, percent_epoxy * percent_amine)

        df = df * abs(sum_a)
        os.system('cls')
        print(self.tg_df)
        print("+==================================")

        for (material_epoxy, material_amine), eq in a_reacted_dict.items() | b_reacted_dict.items():
            df.add_value(material_epoxy.data_material, material_amine.data_material, eq)

        df.normalize()
        print('Матрица процентов пар')
        print(df)
        self.percent_df = df

    def count_tg(self):
        self.count_percent_df()

        if self.percent_df is None:
            return None

        percent_df = copy(self.percent_df)
        tg_df = copy(self.tg_df)

        total_tg_df = tg_df * percent_df
        primary_tg = total_tg_df.sum()
        self.tg = primary_tg
        inf_receipt_percent_dict = self.count_influence_material_percents()

        if inf_receipt_percent_dict:
            print("-------------------------------------")
            print("Содержание непрореагировавших веществ")
            for name, percent in inf_receipt_percent_dict.items():
                print(name, round(percent * 100, 4), " %")
        inf_value = self.tg_correction_manager.count_full_influence(inf_receipt_percent_dict, percent_df)
        print("-------------------------------------")
        print("Полное влияние: ", round(inf_value, 4), " °C")

        self.tg_inf = self.tg + inf_value

    def update_tg_df(self) -> None:
        tg_df = copy(self.profile.get_tg_df())
        # if self.percent_df is not None:
        #     # TODO Продумать алгоритм отслеживания изменения компонентов, чтобы не дропать каждый раз
        #     # дропаем неиспользуемые колонки и строки стеклования
        #     for name in tg_df.columns:
        #         if name not in self.percent_df.columns.values.tolist():
        #             tg_df = tg_df.drop(name, 1)
        #     for name in tg_df.index:
        #         if name not in self.percent_df.index.tolist():
        #             tg_df = tg_df.drop(name)

        self.__tg_df = tg_df

    def drop_labels(self) -> None:
        """
        Убирает все расчёты, когда одна из сумм рецептуры не равна 100 или продукты не реагируют
        :return:
        """
        self.mass_ratio = None
        self.percent_df = None
        self.tg = None
        self.tg_inf = None

    def update_labels(self) -> None:
        """
        Пересчитывает все показатели в программе
        :return:
        """
        if self.receipt_a.sum_percent == 100 and self.receipt_b.sum_percent == 100:
            if self.receipt_a.ew and self.receipt_b.ew:
                if self.receipt_a.ew * self.receipt_b.ew < 0:
                    self.count_mass_ratio()
                    self.count_tg()
                    return None

        self.drop_labels()

    def count_influence_material_percents(self) -> Dict[Material, float]:
        """
        Функция для определения содержания непрореагировавших веществ.
        :return:
        """
        total = defaultdict(float)  # Для расчёта процентов материала в системе
        # Для вычисления избытков аминов и эпоксидов
        total_a = defaultdict(float)
        total_b = defaultdict(float)

        for material in self.receipt_a:
            total[material] += material.percent * self.mass_ratio
            if material.mat_type not in ("Epoxy", "Amine"):
                total_a[material] += material.percent * self.mass_ratio
            else:
                # TODO учёт аминов и эпоксидов при избытке
                pass

        for material in self.receipt_b:
            total[material] += material.percent
            if material.mat_type not in ("Epoxy", "Amine"):
                total_b[material] += material.percent

        total_percent_dict = {material: value / sum(total.values()) for material, value in
                              total_a.items() | total_b.items()}
        return total_percent_dict


class TgInfluenceCounter:
    def __init__(self):
        ...


class MyTableCounter:
    data: defaultdict[Any, defaultdict[Any, Optional[float]]]

    def __init__(self, is_percent_table=False):
        self.epoxy_list: List[DataMaterial] = []
        self.amine_list: List[DataMaterial] = []
        self.is_percent_table = is_percent_table
        if self.is_percent_table:
            self.data = defaultdict(lambda: defaultdict(float))
        else:
            self.data = defaultdict(lambda: defaultdict(lambda: None))

    def set_value(self, epoxy: "DataMaterial", amine: "DataMaterial", value: float):
        # if not isinstance(epoxy, DataMaterial):
        #     print('debug')
        self.data[epoxy][amine] = value
        if epoxy not in self.epoxy_list:
            self.epoxy_list.append(epoxy)
        if amine not in self.amine_list:
            self.amine_list.append(amine)

    def add_value(self, epoxy: "DataMaterial", amine: "DataMaterial", value: float):
        # if not isinstance(epoxy, DataMaterial):
        #     print('debug')
        self.data[epoxy][amine] += value
        if epoxy not in self.epoxy_list:
            self.epoxy_list.append(epoxy)
        if amine not in self.amine_list:
            self.amine_list.append(amine)

    def loc(self, epoxy, amine):
        return self.data[epoxy][amine]

    def normalize(self):
        sum_data = self.sum()
        if sum_data != 0:
            for epoxy in self.data:
                for amine in self.data[epoxy]:
                    self.data[epoxy][amine] = self.data[epoxy][amine] / sum_data

    def sum(self):
        return sum([sum(i for i in d.values()) for d in self.data.values()])

    def __str__(self):
        df = DataFrame()
        for epoxy in self.data:
            for amine in self.data[epoxy]:
                df.loc[epoxy, amine] = self.data[epoxy][amine]
        if self.is_percent_table:
            df = df.fillna(0)
        return str(df)

    def __mul__(self, other):
        if isinstance(other, MyTableCounter):
            if self.is_percent_table:
                data_table = copy(other)
                percent_table = copy(self)
            else:
                data_table = copy(self)
                percent_table = copy(other)

            # Убираем все значения, у которых нет стекла / влияния
            for epoxy in percent_table.epoxy_list:
                for amine in percent_table.amine_list:
                    if data_table.loc(epoxy, amine) is None:
                        if percent_table.loc(epoxy, amine) != 0:
                            # TODO Как-то передавать отсутствие стекла или влияния
                            percent_table.set_value(epoxy, amine, 0)
            percent_table.normalize()

            new_df = MyTableCounter()

            for epoxy in percent_table.epoxy_list:
                for amine in percent_table.amine_list:
                    if data_table.loc(epoxy, amine) is not None:
                        new_df.set_value(epoxy, amine, data_table.loc(epoxy, amine) * percent_table.loc(epoxy, amine))

            return new_df
        elif isinstance(other, (int, float)):
            for epoxy in self.epoxy_list:
                for amine in self.amine_list:
                    self.data[epoxy][amine] *= other
            return copy(self)

    def __rmul__(self, other):
        return self.__mul__(other)

    def __copy__(self):
        new_instance = MyTableCounter(self.is_percent_table)
        for epoxy in self.epoxy_list:
            for amine in self.amine_list:
                new_instance.set_value(epoxy, amine, self.loc(epoxy, amine))
        return new_instance


def count_first_state(eq_dict: dict, pairs_react: List[Tuple[Material, Material]]) -> \
        Tuple[Dict[Material, float], Dict[Tuple[Material, Material], float]]:
    """

    :param eq_dict: {Material: eq}  Компоненты и их эквиваленты
    :param pairs_react: Пары, которые реагируют. На первом месте пожиратель
    :return:
    """
    master_eq_dict = {}  # только пожиратели
    slave_eq_dict = {}  # Все, кто будут поглощены
    # разделяем компоненты на пожирателей и поглощенных
    for master_mat, slave_mat in pairs_react:
        master_eq_dict[master_mat] = eq_dict[master_mat]
        slave_eq_dict[slave_mat] = eq_dict[slave_mat]

    # Считаем % каждого пожирателя в системе
    master_sum = sum(master_eq_dict.values())
    if master_sum == 0:
        return eq_dict, {}
    master_percent_dict = {}
    for db_id, eq in master_eq_dict.items():
        master_percent_dict[db_id] = eq / master_sum

    reacted_dict = {}
    for master_mat, master_percent in master_percent_dict.items():
        for slave_mat, slave_eq in slave_eq_dict.items():
            eq_dict[master_mat] += slave_eq * master_percent
            # На первом месте всегда эпоксид
            if master_mat.mat_type == 'Epoxy':
                reacted_dict[(master_mat, slave_mat)] = abs(slave_eq * master_percent)
            else:
                reacted_dict[(slave_mat, master_mat)] = abs(slave_eq * master_percent)

    for slave_mat in slave_eq_dict.keys():
        del eq_dict[slave_mat]

    return eq_dict, reacted_dict


# ===========================================


class DataMaterial:
    def __init__(self, name, mat_type, ew, db_id=None):
        self.name: str = name
        self.mat_type: str = mat_type
        self.ew: float = ew
        self.db_id: int = db_id
        self.correction: TgCorrectionMaterial = TgCorrectionMaterial(self)

    # Возможно, не используется
    def create_new(self, name: str, mat_type: str, ew: float):
        self.name = name
        self.mat_type = mat_type
        self.ew = ew

    # Возможно, не используется
    def to_json(self):
        data = {}
        data["name"] = self.name
        data["mat_type"] = self.mat_type
        data["ew"] = self.ew
        data["db_id"] = self.db_id
        return data

    def add_correction(self, correction: "Correction"):
        self.correction.add_correction(correction)

    def get_all_corrections(self):
        return self.correction.get_all_corrections()

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"<{self.name}>"
    # def get_tg_influence(self, percent: float) -> float:
    #     return self.correction(percent)
    # def remove_correction(self, correction: Correction):
    #     if correction in self.corrections:
    #         self.corrections.remove(correction)


class DataGlass:
    """
    Не знаю, как лучше реализовать
    """

    def __init__(self, epoxy: DataMaterial, amine: DataMaterial, value: float, db_id: int = None):
        self.db_id = db_id
        self.epoxy = epoxy
        self.amine = amine
        self.value = value


class ReceiptData:
    def __init__(self, name: str, comment: str, profile: "Profile",
                 materials_id: List[int], percents: List[float], mass: float, date: datetime, receipt_id: int,
                 materials: List[DataMaterial] = None):
        self.name = str(name)
        self.comment = str(comment)
        self.profile = profile
        self.materials_id = materials_id
        if materials is None:
            self.materials = [profile.get_material_by_db_id(id_db) for id_db in materials_id]
        else:
            self.materials = materials
        self.percents = percents
        self.mass = mass
        self.date = date
        self.receipt_id = receipt_id
        self.col_start = 1
        self.row_start = 1

    def __iter__(self):
        return iter(zip(self.materials_id, self.percents))

    def to_excel(self, row_start: int = None, col_start: int = None, empty_rows_end: int = 0):
        if row_start is not None:
            self.row_start = row_start
        else:
            row_start = self.row_start
        if col_start is not None:
            self.col_start = col_start
        else:
            col_start = self.col_start
        row_end = row_start + len(self.materials) + 3
        col_type = letter(col_start)
        # col_comp = letter(col_start+1)
        col_percent = letter(col_start + 2)
        col_mass = letter(col_start + 3)
        col_ew = letter(col_start + 4)
        col_1_div_ew = letter(col_start + 5)
        rows = list()
        rows.append([self.name, "", self.date.date(), self.date.time(), "", ""])
        rows.append([self.comment] + ["" for _ in range(5)])
        rows.append(["Тип", "Компонент", "Содержание, %", "Загрузка, г", "ew", r"% / ew"])
        for row, (mat_id, percent) in enumerate(zip(self.materials_id, self.percents), start=row_start + 3):
            material = self.profile.get_material_by_db_id(mat_id)
            formula_1_div_ew = f"=IF({col_ew}{row}<>0, IF({col_type}{row}=\"Amine\", - {col_percent}{row}/{col_ew}{row}, {col_percent}{row}/{col_ew}{row}), 0)"
            formula_mass = f"={col_percent}{row} * {col_mass}{row_end} / 100"
            if material is not None:
                row_line = [material.mat_type, material.name, percent, formula_mass, material.ew, formula_1_div_ew]
                rows.append(row_line)
            else:
                row_line = ["None", "Материал не найден", percent, formula_mass, 0, formula_1_div_ew]
                rows.append(row_line)
        formula_sum_percent = f"=SUM({col_percent}{row_start + 3}:{col_percent}{row_end - 1})"
        formula_1_div_ew = f"=SUM({col_1_div_ew}{row_start + 3}:{col_1_div_ew}{row_end - 1})"
        row_line = ["", "", formula_sum_percent, self.mass, "", formula_1_div_ew]
        rows.append(row_line)
        formula_eew_ahew = f'=IF({col_1_div_ew}{row_end}>0,"EEW","AHEW")'
        row_line = ["", "", "", formula_eew_ahew, f"=ABS(100/{col_1_div_ew}{row_end})", ""]
        rows.append(row_line)
        for _ in range(empty_rows_end):
            rows.append(["" for _ in range(6)])
        return rows

    @property
    def final_ew_link(self):
        return f"{letter(self.col_start + 4)}{self.row_start + len(self.materials) + 4}"


class CorrectionFunction:
    """
    f(x) = k_e * exp(k_exp * x) + k0 + k1 * x + k2 * x2 ...
    """

    def __init__(
            self,
            cor_name: str = '',
            cor_comment: str = '',
            k_e: float = 0,
            k_exp: float = 0,
            db_id: int = None,
            polynomial_coefficients: Iterable = None,
    ):
        self.name = str(cor_name)
        self.comment = str(cor_comment)
        self.k_e = k_e
        self.k_exp = k_exp
        if polynomial_coefficients is not None:
            self.polynomial_coefficients = [c for c in polynomial_coefficients]
        else:
            self.polynomial_coefficients = []
        self.db_id = db_id

    def edit_polynomial_coefficient(self, coef: float, power: int) -> None:
        """
        Позволяет добавить коэффициент при любой степени Х в полиноме
        :param coef: Значение коэффициента
        :param power: Степень икса, перед которой стоит этот коэффициент
        :return: None
        """
        while len(self.polynomial_coefficients) <= power:
            self.polynomial_coefficients.append(0.0)
        self.polynomial_coefficients[power] = coef

    def edit_name_comment(self, name: str = None, comment: str = None) -> None:
        """
        Редактирует имя и комментарий корректировки
        :param name:
        :param comment:
        :return:
        """
        if name is not None:
            self.name = name
        if comment is not None:
            self.comment = comment

    def edit_exp_coef(self, k_e: float = None, k_exp: float = None) -> None:
        """
        Редактировние экспоненциальных кэофициентов: k_e * exp(k_exp * x)
        :param k_e: Коэффициент перед экспонентой
        :param k_exp: Коэффициент в степени экспоненты
        """
        if k_e is not None:
            self.k_e = k_e
        if k_exp is not None:
            self.k_exp = k_exp

    def __call__(self, value: float) -> float:
        """
        Функция для расчёта влияния на заданных коэффициентов
        :param value: Значение Х
        :return: Значение Y
        """
        # Считаем экспоненциальную часть функции
        result = self.k_e * exp(self.k_exp * value)
        # Считаем полиномиальную часть функции
        for power, coef in enumerate(self.polynomial_coefficients):
            result += coef * value ** power
        return result


class Correction:
    def __init__(self, x_min: float, x_max: float, correction_func: CorrectionFunction,
                 amine: DataMaterial = None, epoxy: DataMaterial = None, db_id: int = None,
                 inf_material: DataMaterial = None):
        self.inf_material = inf_material
        self.x_min = x_min
        self.x_max = x_max
        self.amine = amine
        self.epoxy = epoxy
        self.correction_func = correction_func
        self.db_id = db_id

    def __call__(self, value):
        return self.correction_func(value)

    def show_graph(self, save=False):
        import matplotlib.pyplot as plt
        import numpy as np

        x_min = self.x_min
        x_max = self.x_max
        if self.epoxy is not None:
            pair = (self.epoxy.name, self.amine.name)
        else:
            pair = None
        # Data for plotting
        t = np.arange(x_min, x_max, 0.1)
        s = [self(x) for x in t]

        fig, ax = plt.subplots()
        ax.plot(t, s)
        string = "систему в целом "
        if self.inf_material:
            title = f"Влияние '{self.inf_material.name}' на {pair if pair is not None else string}"
        else:
            title = "Красивый график"
        ax.set(
            xlabel="Содержание вещества в системе, %",
            ylabel="Влияние на температуру стеклования, °С",
            title=title,
        )
        ax.grid()
        if save:
            filename = "graph.png"
            fig.savefig(filename)
        plt.show()


class TgCorrectionMaterial:
    """ """

    def __init__(self, material: DataMaterial):
        self.material = material  # Материал, который влияет на систему
        self.corrections = defaultdict(dict)
        self.global_correction = {}
        self.__percent = 0.0

    @property
    def percent(self) -> float:
        return self.__percent

    @percent.setter
    def percent(self, value):
        # TODO Посчитать влияние на каждую пару
        self.__percent = value

    def add_correction(self, correction: Correction) -> None:
        """
        Добавляет коррекцию
        :param correction: Коррекция для расчёта
        """
        # TODO добавить обработку случаев, когда границы накладываются
        x_min = correction.x_min
        x_max = correction.x_max
        pair = (correction.epoxy, correction.amine) if correction.amine is not None else None
        if pair is not None:
            self.corrections[pair][(x_min, x_max)] = correction
        else:
            self.global_correction[(x_min, x_max)] = correction

    def remove_correction(self, limit: Tuple[float], pair: Tuple[DataMaterial, DataMaterial] = None) -> None:
        """
        Удаляет коррекцию с заданной позиции
        :param pair:
        :param limit:
        :return:
        """
        if pair is not None:
            if pair in self.corrections.keys():
                if limit in self.corrections[pair]:
                    del self.corrections[pair][limit]
                    if not self.corrections[pair]:
                        del self.corrections[pair]
        else:
            if limit in self.global_correction.keys():
                del self.global_correction[limit]

    def get_all_corrections(self) -> List[Correction]:
        """
        Возвращает список коррекций данного материала
        :return: [ [CorrectionFunction, limits, pair] , [...], ... ]
        """
        corrections = []

        # for pair, cor_dict in self.correction_funcs.items():
        #     for limits, correction in cor_dict.items():
        #         corrections.append([correction, limits, pair])
        # for limits, correction in self.global_correction.items():
        #     corrections.append((correction, limits, None))

        for cor_dict in self.corrections.values():
            for correction in cor_dict.values():
                corrections.append(correction)
        for correction in self.global_correction.values():
            corrections.append(correction)

        return corrections

    def __call__(self, value: float, pair: Tuple[DataMaterial, DataMaterial] = None) -> dict:
        """
        Позволяет рассчитать коррекцию данного вещества для конкретной пары или на систему в целом
        :param value: % материала в системе
        :param pair: Пара, на которую рассчитывается влияние
        :return: Словарь со значениями влияния и кодом
        Коды:
        1 - Влияние на заданную пару:
        2 - Влияние по глобальной формуле
        3 - Не задана функция влияния
        """
        if pair is not None:
            if pair in self.corrections.keys():
                for limit in self.corrections[pair].keys():
                    if limit[0] <= value <= limit[1]:
                        return {
                            "value": self.corrections[pair][limit](value),
                            "code": 1,
                        }
        for limit in self.global_correction.keys():
            if limit[0] <= value <= limit[1]:
                return {"value": self.global_correction[limit](value), "code": 2}
        return {"value": 0.0, "code": 3}

    def __add__(self, other):
        """
        Функционал для объединения коррекций.
        Может объединять только коррекции для одного материала.
        :param other:
        :return:
        """
        if isinstance(other, TgCorrectionMaterial):
            if self.material == other.material:
                for pair in other.corrections.keys():
                    for limit, correction in other.corrections[pair].items():
                        self.add_correction(
                            correction=correction,
                        )
                for limit, correction in other.global_correction.items():
                    self.add_correction(
                        correction=correction
                    )


class TgCorrectionManager:
    def __init__(self, profile: "Profile"):
        self.all_corrections_materials = []
        self.all_corrections_funcs = []
        self.used_corrections_materials: Dict[DataMaterial, TgCorrectionMaterial] = {}
        self.profile: Profile = profile

    def add_tg_correction_material(
            self, correction_material: TgCorrectionMaterial
    ) -> None:
        """
        Добавляет коррекцию материала в менеджер
        :param correction_material:
        :return:
        """
        self.all_corrections_materials.append(correction_material)
        self.used_corrections_materials[correction_material.material] = correction_material

    def turn_on_correction(self):
        """
        Включает коррекцию для конкретного материала в работу
        :return:
        """

    def turn_off_correction(self):
        """
        Выключает коррекцию для конкретного материала в работу
        :return:
        """

    def fill_data(self):
        for mat_list in self.profile.materials.values():
            for material in mat_list:
                ...

    def count_influence_of_one_material(self, material: DataMaterial, percent: float,
                                        pair_list: List[Tuple[DataMaterial, DataMaterial]]) -> MyTableCounter:
        df = MyTableCounter()

        for pair in pair_list:
            result = material.correction(percent, pair)
            # TODO Установить индикаторы согласно кодам
            if result['code'] == 1:
                df.set_value(pair[0], pair[1], result["value"])
                ...
            elif result['code'] == 2:
                df.set_value(pair[0], pair[1], result["value"])
                ...
            elif result['code'] == 3:
                ...

        return df

    def count_full_influence(self, material_dict: Dict["Material", float], percent_df: MyTableCounter) -> float:
        epoxy_list = percent_df.epoxy_list
        amine_list = percent_df.amine_list
        pair_list = [(epoxy, amine) for epoxy in epoxy_list for amine in amine_list]
        total_influence = 0.0

        for material, percent in material_dict.items():
            mat_inf_df: MyTableCounter = self.count_influence_of_one_material(material.data_material, percent * 100,
                                                                              pair_list)
            # TODO Обработать отсутствующие стёкла (код 3)
            mat_inf_table = mat_inf_df * percent_df
            print("-------------------------------------")
            print(f"Матрица влияния '{material}'")
            if mat_inf_table.sum() == 0:
                print("\tВлияние при данной концентрации отсутствует")
            else:
                print(mat_inf_table)
            mat_sum_inf = mat_inf_table.sum()
            total_influence += mat_sum_inf
        return total_influence


class Profile:
    def __init__(self, profile_name: str, orm_db: "ORMDataBase"):

        self.profile_name = profile_name
        # {тип: [список материалов]}
        self.materials: Dict[str, List[DataMaterial]] = defaultdict(list)  # Тип: Список материалов данного типа
        self.id_material_dict: Dict[int, DataMaterial] = {}
        # Хранение стеклований
        self.tg_list: List[DataGlass] = []
        self.id_tg_dict: Dict[int, DataGlass] = {}
        self.correction_funcs = []

        self.orm_db = orm_db
        self.my_main_window: Optional["MyMainWindow"] = None
        self.tg_df: Optional[MyTableCounter] = None

    def add_material(self, material: DataMaterial) -> None:
        """
        Функция для добавления материала в профиль
        :param material:
        :return:
        """
        if material is None:
            return None
        if material not in self.materials[material.mat_type]:
            if material.db_id is None:
                self.orm_db.add_material(material, self)
            self.materials[material.mat_type].append(material)
            self.id_material_dict[material.db_id] = material
            if self.my_main_window is not None:
                self.my_main_window.update_list_of_material_names()
            # Если материал Амин или Эпоксид, обнуляем tg_df
            if self.tg_df is not None and material.mat_type in ("Amine", "Epoxy"):
                self.tg_df = None

    def add_material_to_db(self, mat_name: str, mat_type: str, ew: float, add_to_profile: bool = True):
        """
        Добавляет материал в БД
        :return:
        """
        material = DataMaterial(mat_name, mat_type, ew)
        self.orm_db.add_material(material, profile=self if add_to_profile else None)
        self.add_material(material)
        return material

    def update_material_in_db(self, material: DataMaterial, new_type: str = None, new_ew=None):
        self.orm_db.update_material(material.name, new_type, new_ew)
        material.ew = new_ew
        material.mat_type = new_type

    def remove_material(self, material: DataMaterial) -> None:
        """
        Функция для удаления материала из профиля
        :param material:
        :return:
        """
        mat_type: str = material.mat_type
        if mat_type in self.materials:
            if material in self.materials[mat_type]:
                self.materials[mat_type].remove(material)
        if material.db_id in self.id_material_dict:
            del self.id_material_dict[material.db_id]
        if self.my_main_window is not None:
            self.my_main_window.update_list_of_material_names()
        # Если материал Амин или Эпоксид, обнуляем tg_df
        if self.tg_df is not None and material.mat_type in ("Amine", "Epoxy"):
            self.tg_df = None
        self.orm_db.remove_material_from_profile(material, self)

    def get_materials_by_type(self, mat_type: str) -> List[DataMaterial]:
        """
        Функция для получения всех материалов конкретного типа
        :param mat_type: Тип материала
        :return: Список материалов
        """
        return self.materials[mat_type]

    def get_material_by_db_id(self, db_id: int) -> DataMaterial:
        if db_id in self.id_material_dict:
            return self.id_material_dict[db_id]
        else:
            material = self.orm_db.get_material_by_id(db_id)
            self.add_material(material)
            return material

    def get_mat_names_by_type(self, mat_type: str) -> List[str]:
        """
        Функция для получения всех названий материалов конкретного типа
        :param mat_type:
        :return:
        """
        return [mat.name for mat in self.get_materials_by_type(mat_type)]

    def get_all_types(self) -> List[str]:
        """
        Функция для получения списка всех типов материала в профиле
        :return: список типов материалов
        """
        all_types = list(
            mat_type
            for mat_type in self.materials.keys()
            if len(self.materials[mat_type]) > 0
        )
        if len(all_types) > 0:
            return all_types
        return all_types

    def get_all_correction_funcs(self) -> List[CorrectionFunction]:
        if not self.correction_funcs:
            self.correction_funcs = self.orm_db.get_all_correction_funcs()
        return self.correction_funcs

    def copy_profile(self, profile_name: str) -> "Profile":
        """
        Функция для копирования профиля
        :param profile_name: Имя нового пользователя
        :return: Новый профиль
        """
        new_dp = Profile(profile_name, self.orm_db)
        for mat_type in self.materials:
            materials = self.get_materials_by_type(mat_type)
            for material in materials:
                new_dp.add_material(material)
        return new_dp

    def get_ew_by_name(self, mat_type: str, material: str):
        for mat in self.materials[mat_type]:
            if mat.name == material:
                return mat.ew
        return 0

    def get_tg_df(self) -> MyTableCounter:
        if self.tg_df is None:
            self.tg_df = MyTableCounter()
            if "Epoxy" in self.materials.keys() and "Amine" in self.materials.keys():
                all_id_epoxy = [mat.db_id for mat in self.materials["Epoxy"]]
                all_id_amine = [mat.db_id for mat in self.materials["Amine"]]
                self.tg_list = self.orm_db.get_tg_by_materials_ids(all_id_epoxy, all_id_amine)
                for data_glass in self.tg_list:
                    self.id_tg_dict[data_glass.db_id] = data_glass
                    self.tg_df.set_value(data_glass.epoxy, data_glass.amine, data_glass.value)

        return self.tg_df

    def get_data_material(self, mat_type: str, mat_index: int) -> Optional[DataMaterial]:
        if not mat_type or mat_index == -1:
            return None
        return self.materials[mat_type][mat_index]

    def add_tg_to_db(self, epoxy_material: DataMaterial, amine_material: DataMaterial, value: float):
        """
        Добавляет стеклование в БД
        """
        # TODO Добавить проверку на повтор
        data_glass = DataGlass(epoxy_material, amine_material, value)
        self.orm_db.add_tg(data_glass)
        self.tg_list.append(data_glass)
        self.id_tg_dict[data_glass.db_id] = data_glass
        return data_glass

    def add_correction_to_db(self, correction: Correction):
        self.orm_db.add_correction_func(correction.correction_func)
        self.orm_db.add_correction(correction)
        self.orm_db.add_association_material_to_correction(correction.inf_material, correction)
        self.correction_funcs.append(correction.correction_func)

    def remove_correction_from_db(self, correction: Correction):
        self.orm_db.remove_correction_func(correction.correction_func)
        self.orm_db.remove_association_material_to_correction(correction.inf_material, correction)
        self.orm_db.remove_correction(correction)


class ProfileManager:
    def __init__(self, profile_list=None):
        if profile_list is not None:
            self.profile_list = profile_list
        else:
            self.profile_list = []

    def add_profile(self, profile: Profile) -> None:
        self.profile_list.append(profile)

    def remove_profile(self, profile: Profile) -> None:
        if profile in self.profile_list:
            self.profile_list.remove(profile)


class ORMDataBase:
    def __init__(self, db_name):
        self.db_name = db_name
        self.current_profile = None
        # все материалы в базе {material_id: DataMaterial}
        self.all_materials = {}
        self.all_tg = {}

        self.update_all_materials()

    def read_profile(self, profile_name: str) -> Profile:
        profile = Profile(profile_name, self)
        for mat_id in self.get_profile_materials(profile_name):
            profile.add_material(self.all_materials[mat_id])
            # TODO Подключить коррекцию к профилю (нужно реализовать логику в самом профиле)
        self.current_profile = profile
        return profile

    def update_all_materials(self) -> None:
        self.all_materials = {}
        for name, mat_type, ew, mat_id in self.get_all_materials_data():
            material = DataMaterial(name, mat_type, ew, mat_id)
            self.all_materials[mat_id] = material
        for material in self.all_materials.values():
            for correction in self.get_all_corrections_of_one_material(material):
                material.correction.add_correction(correction)

    def get_all_materials(self) -> List[DataMaterial]:
        return [i for i in self.all_materials.values()]

    # =========================== Получение обработанных данных из БД ==================================

    def get_material_by_id(self, mat_id: int) -> Optional[DataMaterial]:
        """
        Получение материала по id. Используется после получения всех id материалов в профиле
        :param mat_id:
        :return:
        """
        if mat_id not in self.all_materials:
            connection = sqlite3.connect(self.db_name)
            cursor = connection.cursor()
            cursor.execute(
                f"SELECT Name, Type, ew  FROM Materials WHERE (id = '{mat_id}') "
            )
            result = cursor.fetchall()
            if len(result) == 0:
                return None
            material = DataMaterial(*result[0], mat_id)
            connection.close()
            return material
        else:
            return self.all_materials[mat_id]

    def get_tg_by_materials_ids(self, epoxy_id: List[int], amine_id: List[int]) -> List[DataGlass]:
        """
        Проходится
        :param epoxy_id:
        :param amine_id:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        epoxy_str = "".join([f"{i}, " for i in epoxy_id])[:-2]
        amine_str = "".join([f"{i}, " for i in amine_id])[:-2]
        string = (
            f"SELECT * FROM Tg WHERE Epoxy in ({epoxy_str}) AND Amine in ({amine_str})"
        )
        cursor.execute(string)
        tg_list = []
        for tg_id, epoxy_id, amine_id, value in cursor.fetchall():
            # if epoxy_id not in self.all_materials or amine_id not in self.all_materials:
            #     print("ORMDataBase.get_tg_by_materials_ids нет материала в базе")
            #     print("epoxy_id", epoxy_id)
            #     print("amine_id", amine_id)
            epoxy = self.all_materials[epoxy_id]
            amine = self.all_materials[amine_id]
            tg_list.append(DataGlass(epoxy, amine, value, tg_id))
        connection.close()
        return tg_list

    def get_all_corrections_of_one_material(self, material: DataMaterial) -> List[Correction]:
        all_corrections_id = self._get_all_corrections_id_of_one_material(material.db_id)
        all_corrections = []
        for correction_id in all_corrections_id:
            cor_func, x_min, x_max, pair = self.get_correction_by_id(correction_id)
            correction = Correction(x_min, x_max, cor_func, db_id=correction_id,
                                    amine=pair[1] if pair is not None else None,
                                    epoxy=pair[0] if pair is not None else None,
                                    inf_material=material)
            all_corrections.append(correction)
        return all_corrections

    def get_all_tg(self) -> List[DataGlass]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"SELECT * FROM Tg"
        cursor.execute(string)
        tg_list = []
        for tg_id, epoxy, amine, value in cursor.fetchall():
            tg_list.append(DataGlass(epoxy, amine, value, tg_id))
        connection.close()
        return tg_list

    def get_all_correction_funcs(self) -> List[CorrectionFunction]:
        """
        Получение всех графиков коррекций
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Получаем параметры корректировки
        cursor.execute(
            f"SELECT id, Name, Comment, k_e, k_exp FROM Correction_funcs "
        )

        all_corrections = []
        for correction_id, cor_name, cor_comment, k_e, k_exp in cursor.fetchall():
            # Получаем полиномиальные коэффициенты корректировки
            cursor.execute(
                f"SELECT Power, coef FROM corr_poly_coef_map WHERE (Correction = '{correction_id}') "
            )
            polynom_coefs = cursor.fetchall()

            cor_func = CorrectionFunction(cor_name, cor_comment, k_e, k_exp, correction_id)
            for power, coef in polynom_coefs:
                cor_func.edit_polynomial_coefficient(coef, power)

            all_corrections.append(cor_func)

        connection.close()
        return all_corrections

    def get_all_mat_types(self):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT DISTINCT Type FROM Materials")
        all_types = [data[0] for data in cursor.fetchall()]
        connection.close()
        return all_types

    def get_profile_receipts(self, profile: Profile) -> List[ReceiptData]:
        """

        :param profile:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT receipt_id FROM Receipt_profile_map WHERE profile='{profile.profile_name}'")

        all_receipt_id = [data[0] for data in cursor.fetchall()]
        print(*all_receipt_id)
        # for receipt_id in all_receipt_id:
        insert = ", ".join([f"{i}" for i in all_receipt_id])
        print(f"SELECT * FROM Receipt WHERE receipt_id in ({insert})")
        cursor.execute(f"SELECT * FROM Receipt WHERE receipt_id in ({insert})")
        all_receipts = []
        receipt_data = cursor.fetchall()
        for receipt_id, name, comment, mass, date in receipt_data:
            materials = []
            percents = []
            date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S.%f")
            cursor.execute(f"SELECT material, percent FROM Receipt_data WHERE receipt_id={receipt_id}")
            # cursor.execute(f"SELECT material, percent FROM Receipt_data")
            cur_receipt = cursor.fetchall()
            for material, percent in cur_receipt:
                materials.append(material)
                percents.append(percent)
            all_receipts.append(ReceiptData(name, comment, profile, materials, percents, mass, date, receipt_id))

        connection.close()
        return all_receipts

    # =========================== Получение сырых данных из БД ==================================
    def get_all_profiles(self) -> List[str]:
        """
        Получение всех профилей из базы
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM Profiles")
        all_profiles = [res[0] for res in cursor.fetchall()]
        connection.close()
        return all_profiles

    def get_profile_materials(self, profile_name: Union[str, Profile]) -> List[int]:
        """
        Получение списка всех материалов в профиле и их коррекций
        :param profile_name: Имя профиля или сам профиль
        :return: Список материалов, которые подключены к профилю
        """
        if isinstance(profile_name, Profile):
            profile_name = profile_name.profile_name
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT Material FROM Prof_mat_map WHERE (Profile = '{profile_name}') "
        )
        result = [i[0] for i in cursor.fetchall()]
        connection.close()
        return result

    def _get_all_corrections_id_of_one_material(self, mat_id: int) -> List[int]:
        """
        Возвращает список коррекций поданного материала
        :param mat_id: id материала
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Получаем информацию о одной функции
        cursor.execute(
            f"SELECT Correction FROM Mat_cor_map WHERE (Material = '{mat_id}') "
        )
        result = [i[0] for i in cursor.fetchall()]
        connection.close()
        return result

    def get_correction_by_id(self, cor_map_id: int):
        """
        Получение параметров функции влияния
        :param cor_map_id:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Получаем информацию о одной функции
        cursor.execute(
            f"SELECT Amine, Epoxy, x_max, x_min, Correction_func FROM Correction_map WHERE (id = '{cor_map_id}') "
        )

        amine_id, epoxy_id, x_max, x_min, correction_id = cursor.fetchall()[0]
        pair = None
        # Если есть амин, значит коррекция для пары, а не на всю систему
        if amine_id is not None:
            pair = (self.get_material_by_id(epoxy_id), self.get_material_by_id(amine_id))

        # Получаем параметры корректировки
        cursor.execute(
            f"SELECT Name, Comment, k_e, k_exp FROM Correction_funcs WHERE (id = '{correction_id}') "
        )
        cor_name, cor_comment, k_e, k_exp = cursor.fetchall()[0]
        # Получаем полиномиальные коэффициенты корректировки
        cursor.execute(
            f"SELECT Power, coef FROM corr_poly_coef_map WHERE (Correction = '{correction_id}') "
        )
        polynom_coefs = cursor.fetchall()

        cor_func = CorrectionFunction(cor_name, cor_comment, k_e, k_exp, correction_id)
        for power, coef in polynom_coefs:
            cor_func.edit_polynomial_coefficient(coef, power)

        # tg_correction_material.add_correction(correction, x_min, x_max,
        #                                       (amine_name, epoxy_name) if amine_id is not None else None)
        # TODO Возможно, стоит привязывать коррекцию к материалу по id, а не по названию
        connection.close()

        correction = Correction(x_min, x_max, cor_func, db_id=cor_map_id)
        return (cor_func, x_min, x_max, pair)

    def get_all_materials_data(self) -> List[Tuple]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
        result = cursor.fetchall()
        connection.close()
        return result

    # ============================= Редактирование БД =======================================
    def add_material(self, material: DataMaterial, profile: Profile = None):
        """
        Добавляет материал в базу. Если указан профиль, то привязывает материал к нему.
        :param material:
        :param profile:
        :return:
        """

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        # Проверяем, что материала нет в базе
        cursor.execute(
            f"SELECT * FROM Materials WHERE Name='{material.name}'")
        result = cursor.fetchall()
        if len(result) > 0:
            # TODO Подумать, что делать, если пытаются добавить материал, который уже есть в базе.
            self.update_material(material.name, mat_type=material.mat_type, ew=material.ew)
            return None

        cursor.execute(f"SELECT MAX(id) FROM Materials")
        max_id = cursor.fetchone()
        mat_id = max_id[0] + 1 if max_id[0] is not None else 1
        material.db_id = mat_id

        data = [mat_id, material.name, material.mat_type, material.ew]
        insert = f"INSERT INTO Materials (id, name, type, ew) VALUES (?, ?, ?, ?);"
        cursor.execute(insert, data)
        connection.commit()
        if profile is not None:
            self.add_material_to_profile(material, profile)
        elif self.current_profile is not None:
            self.add_material_to_profile(material, self.current_profile)
        self.all_materials[mat_id] = material
        connection.close()

    def remove_material(self, material: DataMaterial):
        """
        Удаление материала из БД.
        Из-за того, что ON DELETE CASCADE не работает, удаляю всё в ручную.
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        strings = []
        strings.append(f"DELETE FROM Materials WHERE Id={material.db_id}")
        # TODO Возможно, не обязательно вручную всё удалять. Нужны тесты и рефакторинг
        # strings.append(f"DELETE FROM Prof_mat_map WHERE Material={material.db_id}")
        # strings.append(f"DELETE FROM Correction_map WHERE Material_id={material.db_id}")
        for string in strings:
            cursor.execute(string)
        del self.all_materials[material.db_id]
        del material
        connection.commit()
        connection.close()

    def update_material(self, name: str, mat_type: str = None, ew: float = None):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT ew, Type FROM Materials WHERE Name='{name}'")
        result = cursor.fetchone()
        if result is None:
            return None
        result = list(result)
        if mat_type is not None:
            result[0] = mat_type
        if ew is not None:
            result[1] = ew
        cursor.execute(f"UPDATE Materials SET ew={result[1]}, Type='{result[0]}' WHERE Name='{name}'")
        connection.commit()
        connection.close()

    def add_correction_func(self, correction_func: CorrectionFunction):

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(id) FROM Correction_funcs")
        max_id = cursor.fetchone()
        cor_id = max_id[0] + 1 if max_id[0] is not None else 1
        correction_func.db_id = cor_id
        data = [
            cor_id,
            correction_func.name,
            correction_func.comment,
            correction_func.k_e,
            correction_func.k_exp,
        ]
        insert = f"INSERT INTO Correction_funcs (id, Name, Comment, k_e, k_exp) VALUES (?, ?, ?, ?, ?);"
        cursor.execute(insert, data)
        # Добавляем коэффициенты в таблицу полиномиальных коэффициентов
        for power, coef in enumerate(correction_func.polynomial_coefficients):
            if coef != 0.0:
                data = [cor_id, power, coef]
                insert = f"INSERT INTO corr_poly_coef_map (Correction, Power, coef) VALUES (?, ?, ?);"
                cursor.execute(insert, data)
        connection.commit()
        connection.close()

    def remove_correction_func(self, correction: CorrectionFunction):
        """
        Удаляем коррекцию из БД
        :param correction:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Correction_funcs WHERE Id={correction.db_id}"
        cursor.execute(string)
        string = f"DELETE FROM corr_poly_coef_map WHERE Correction={correction.db_id}"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def add_tg(self, tg: DataGlass):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(id) FROM Tg")
        max_id = cursor.fetchone()
        tg_id = max_id[0] + 1 if max_id[0] is not None else 1
        tg.db_id = tg_id
        data = [tg_id, tg.epoxy.db_id, tg.amine.db_id, tg.value]
        insert = f"INSERT INTO Tg (id, Epoxy, Amine, Value) VALUES (?, ?, ?, ?);"
        cursor.execute(insert, data)
        connection.commit()
        connection.close()

    def remove_tg(self, tg: DataGlass):
        """
        Удаляем коррекцию из БД
        :param tg:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Tg WHERE Id={tg.db_id}"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def add_material_to_profile(self, material: DataMaterial, profile: Profile):
        """
        Прикрепляет материал к профилю.
        Материал должен быть базе данных.
        :param material:
        :param profile:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        if material.db_id in self.get_profile_materials(profile.profile_name):
            return None
        insert = f"INSERT INTO Prof_mat_map (Profile, Material) VALUES (?, ?);"
        data = [profile.profile_name, material.db_id]
        cursor.execute(insert, data)
        connection.commit()
        connection.close()
        profile.add_material(material)

    def remove_material_from_profile(self, material: DataMaterial, profile: Profile):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Prof_mat_map WHERE Profile='{profile.profile_name}' AND Material='{material.db_id}'"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def add_profile(self, profile_name: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        insert = f"INSERT INTO Profiles (Name) VALUES (?);"
        cursor.execute(insert, [profile_name])
        connection.commit()
        connection.close()

    def remove_profile(self, profile_name: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Profiles WHERE Name='{profile_name}'"
        cursor.execute(string)
        string = f"DELETE FROM Prof_mat_map WHERE Profile='{profile_name}'"
        cursor.execute(string)
        string = f"DELETE FROM Receipt_profile_map WHERE profile='{profile_name}'"
        cursor.execute(string)

        connection.commit()
        connection.close()

    def add_correction(self, correction: Correction):
        """
        Добавляет коррекцию в БД. Предполагается, что функция коррекции уже в базе
        :param correction:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(id) FROM Correction_map")
        max_id = cursor.fetchone()
        cor_id = max_id[0] + 1 if max_id[0] is not None else 1
        correction.db_id = cor_id
        epoxy_id = correction.epoxy.db_id if isinstance(correction.epoxy, DataMaterial) else None
        amine_id = correction.amine.db_id if isinstance(correction.amine, DataMaterial) else None
        insert = f"INSERT INTO Correction_map (id, Amine, Epoxy, x_max, x_min, Correction_func) VALUES (?, ?, ?, ?, ?, ?);"
        insert_data = [cor_id, amine_id, epoxy_id, correction.x_max, correction.x_min, correction.correction_func.db_id]
        cursor.execute(insert, insert_data)
        connection.commit()
        connection.close()

    def remove_correction(self, correction: Correction):
        """
        Удаляет коррекцию из БД
        :param correction:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Correction_map WHERE id='{correction.db_id}'"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def add_association_material_to_correction(self, material: DataMaterial, correction: Correction):
        """
        Создает ассоциацию материала и коррекции.
        Добавляет связку в таблицу Mat_cor_map
        :param material: материал
        :param correction: коррекция
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        insert = f"INSERT INTO Mat_cor_map (Material, Correction) VALUES (?, ?);"
        insert_data = [material.db_id, correction.db_id]
        cursor.execute(insert, insert_data)
        connection.commit()
        connection.close()

    def remove_association_material_to_correction(self, material: DataMaterial, correction: Correction):
        """
        Удаляет ассоциацию материала и коррекции.
        Удаляет запись из в таблицы Mat_cor_map
        :param material: материал
        :param correction: коррекция
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Mat_cor_map WHERE Material='{material.db_id}' AND Correction='{correction.db_id}'"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def save_receipt(self, materials: List[Material], name: str, comment: str, mass: float, profile: Profile):
        """
        Сохраняет рецептуру в БД
        :param profile:
        :param comment:
        :param name:
        :param materials:
        :param mass:
        :return:
        """
        if not name:
            # TODO Реализовать уведомление, что рецептура без имени и не сохранена в БД
            return None

        time = datetime.now()

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT receipt_id FROM Receipt WHERE name='{name}'")
        receipt_id = cursor.fetchone()
        if receipt_id is not None:
            self.update_receipt(materials, name, comment, mass, profile, receipt_id[0])
            # Обновить рецептуру
            ...
            return None

        # Добавление данных о рецептуре
        cursor.execute(f"SELECT MAX(receipt_id) FROM Receipt")
        max_id = cursor.fetchone()
        receipt_id = max_id[0] + 1 if max_id[0] is not None else 1
        insert = f"INSERT INTO Receipt (receipt_id, name, comment, mass, date) VALUES (?, ?, ?, ?, ?);"
        insert_data = [receipt_id, name, comment, mass, time]
        cursor.execute(insert, insert_data)

        # Добавление самой рецептуры
        for material in materials:
            insert = f"INSERT INTO Receipt_data (receipt_id, material, percent) VALUES (?, ?, ?);"
            insert_data = [receipt_id, material.data_material.db_id, material.percent]
            cursor.execute(insert, insert_data)

        # Добавление рецептуры к профилю
        insert = f"INSERT INTO Receipt_profile_map (profile, receipt_id) VALUES (?, ?);"
        insert_data = [profile.profile_name, receipt_id]
        cursor.execute(insert, insert_data)

        connection.commit()
        connection.close()
        return ReceiptData(name, comment, profile, [mat.data_material.db_id for mat in materials],
                           [mat.percent for mat in materials], mass, time, receipt_id)

    def remove_receipt(self, receipt: Union[ReceiptData, int]):
        """
        Удаляет рецептуру из БД
        :param receipt: Рецептура
        :return:
        """
        if isinstance(receipt, ReceiptData):
            receipt = receipt.receipt_id

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Receipt WHERE receipt_id={receipt}"
        cursor.execute(string)
        string = f"DELETE FROM Receipt_data WHERE receipt_id={receipt}"
        cursor.execute(string)
        string = f"DELETE FROM Receipt_profile_map WHERE receipt_id={receipt}"
        cursor.execute(string)
        connection.commit()
        connection.close()

    def update_receipt(self, materials: List[Material] = None, name: str = None, comment: str = None,
                       mass: float = None, profile: Profile = None, receipt_id: int = None,
                       receipt: ReceiptData = None):
        if receipt is not None:
            if name is None:
                name = receipt.name
            if comment is None:
                comment = receipt.comment
            if mass is None:
                mass = receipt.mass
            if receipt_id is None:
                receipt_id = receipt.receipt_id

        if receipt_id is None:
            return None

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            f"UPDATE Receipt SET name='{name}', comment='{comment}', mass={mass} WHERE receipt_id={receipt_id}")

        if materials is not None:
            string = f"DELETE FROM Receipt_data WHERE receipt_id={receipt_id}"
            cursor.execute(string)
            # Добавление самой рецептуры
            for material in materials:
                insert = f"INSERT INTO Receipt_data (receipt_id, material, percent) VALUES (?, ?, ?);"
                insert_data = [receipt_id, material.data_material.db_id, material.percent]
                cursor.execute(insert, insert_data)

        if profile is not None:
            cursor.execute(
                f"SELECT * FROM Receipt_profile_map WHERE profile='{profile.profile_name}' AND receipt_id={receipt_id}")
            if cursor.fetchone() is None:
                # Добавление рецептуры к профилю
                insert = f"INSERT INTO Receipt_profile_map (profile, receipt_id) VALUES (?, ?);"
                insert_data = [profile.profile_name, receipt_id]
                cursor.execute(insert, insert_data)

        connection.commit()
        connection.close()

    # ============================= Создание БД =======================================

    def create_db(self):
        """
        # TODO реализовать создание базы данных при отсутствии файла
        (После того, как структура будет окончательной)
        """

    def get_profile_name_by_computer(self, user_name: str, computer_name: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"SELECT profile FROM User_computer WHERE user_name = '{user_name}' and computer_name = '{computer_name}'"
        cursor.execute(string)
        profile = cursor.fetchone()
        if profile is not None:
            return profile[0]
        return None

    def add_computer_to_profile(self, user_name: str, computer_name: str, profile: str):
        if self.get_profile_name_by_computer(user_name, computer_name) is None:
            connection = sqlite3.connect(self.db_name)
            cursor = connection.cursor()
            insert = f"INSERT INTO User_computer (user_name, computer_name, profile) VALUES (?, ?, ?);"
            insert_data = [user_name, computer_name, profile]
            cursor.execute(insert, insert_data)
            connection.commit()
            connection.close()

    def remove_computer_from_db(self, user_name: str, computer_name: str):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM User_computer WHERE user_name='{user_name}' AND computer_name='{computer_name}'"
        cursor.execute(string)
        connection.commit()
        connection.close()