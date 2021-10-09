import math
from collections import defaultdict
from copy import copy
from itertools import chain
from typing import List, Optional, Tuple, Dict

import numpy as np
import pandas
from pandas import DataFrame

# import init_class
from res.additional_funcs import normalize, normalize_df
from res.data_classes import Profile, TgCorrectionManager


class Material:
    def __init__(self, mat_type: str, mat_index: int, profile: Profile, receipt: "Receipt"):
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
    def data_material(self):
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
    def __init__(self, component: str, profile: Profile):
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
        self.__mass_ratio: Optional[float] = None
        self.extra_ratio = extra_ratio
        self.percent_df: Optional[DataFrame] = None
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
                     if material.ew * self.mass_ratio != 0 else 0 for material in self.receipt_a if material.mat_type in ('Amine', "Epoxy")}

        b_eq_dict = {
            material: material.percent / material.ew if material.ew != 0 else 0
            for material in self.receipt_b  if material.mat_type in ("Amine", "Epoxy")}

        pairs_a = self.pair_react_window.get_react_pairs("A")
        if self.receipt_a.ew < 0:
            pairs_a = [(pair[1], pair[0]) for pair in pairs_a]
        pairs_b = self.pair_react_window.get_react_pairs("B")
        if self.receipt_b.ew < 0:
            pairs_b = [(pair[1], pair[0]) for pair in pairs_b]

        new_eq_a, a_reacted_dict = count_first_state(a_eq_dict, pairs_a)
        new_eq_b, b_reacted_dict = count_first_state(b_eq_dict, pairs_b)

        df = DataFrame()
        sum_a = round(sum(new_eq_a.values()), 6)
        sum_b = round(sum(new_eq_b.values()), 6)

        if sum_a != - sum_b:
            print('count_percent_df - Сумма эквивалентов не сходится!')
            print(sum_a, sum_b)

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
            print("count_percent_df - продукты не реагируют")
            return None

        for material_epoxy, percent_epoxy in epoxy_percent_dict.items():
            for material_amine, percent_amine in amine_percent_dict.items():
                df.loc[material_epoxy.data_material.db_id, material_amine.data_material.db_id]\
                    = percent_epoxy * percent_amine

        df: DataFrame = df * abs(sum_a)
        print("+==================================")
        print(df)
        for (material_epoxy, material_amine), eq in a_reacted_dict.items() | b_reacted_dict.items():
            epoxy_index = material_epoxy.data_material.db_id
            amine_index = material_amine.data_material.db_id
            if material_epoxy.data_material.db_id in df.index and material_amine.data_material.db_id in df.columns:
                if pandas.isna(df.loc[epoxy_index, amine_index]):
                    df.loc[epoxy_index, amine_index] = 0
                df.loc[epoxy_index, amine_index] += eq
            else:
                df.loc[epoxy_index, amine_index] = eq

        df = normalize_df(df)
        print(df)
        self.percent_df = df

    def count_tg(self):
        self.count_percent_df()

        if self.percent_df is None:
            return None

        percent_df = copy(self.percent_df)
        tg_df = copy(self.tg_df)
        # Получаем все пары, которые не имеют стекла
        all_pairs_na = []
        for name in tg_df:
            pairs_a = tg_df[tg_df[name].isna()]
            par = [(resin, name) for resin in list(pairs_a.index)]
            all_pairs_na += par

        # TODO реализовать обработку отсутствующих пар стёкол (вывод индикатора)
        all_pairs_na_dict = {}
        # Убираем в матрице процентов отсутствующие пары
        for resin, amine in all_pairs_na:
            if amine in percent_df.columns and resin in percent_df.index:
                # all_pairs_na_dict[(resin, amine)] = percent_df[amine][resin]
                percent_df[amine][resin] = 0.0

        percent_df = normalize_df(percent_df)

        total_tg_df = tg_df * percent_df
        primary_tg = sum(total_tg_df.sum())
        self.tg = primary_tg
        inf_receipt_percent_dict = self.count_influence_material_percents()
        print(inf_receipt_percent_dict)
        inf_value = self.tg_correction_manager.count_full_influence(inf_receipt_percent_dict, percent_df)
        print(inf_value)


        # TODO продолжить

    def update_tg_df(self) -> None:

        tg_df = copy(self.profile.get_tg_df())
        if self.percent_df is not None:
            # TODO Продумать алгоритм отслеживания изменения компонентов, чтобы не дропать каждый раз
            # дропаем неиспользуемые колонки и строки стеклования
            for name in tg_df.columns:
                if name not in self.percent_df.columns.values.tolist():
                    tg_df = tg_df.drop(name, 1)
            for name in tg_df.index:
                if name not in self.percent_df.index.tolist():
                    tg_df = tg_df.drop(name)

        self.__tg_df = tg_df

    def drop_labels(self) -> None:
        """
        Убирает все расчёты, когда одна из сумм рецептуры не равна 100 или продукты не реагируют
        :return:
        """
        self.mass_ratio = None
        self.percent_df = None
        self.tg = None

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
