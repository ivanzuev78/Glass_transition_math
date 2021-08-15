import math
import sqlite3
from typing import Optional, Union

from pandas import DataFrame

import init_class


class Material:
    def __init__(self, mat_type: str, mat_name: str, receipt: "Receipt"):
        self.__mat_type = mat_type
        self.__name = mat_name
        self.__ew = None
        self.receipt = receipt
        self.__percent: float = 0.0
        receipt.add_material(self)
        self.ew = self.receipt.data_driver.get_ew_by_name(mat_type, mat_name)

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
        self.set_ew()

    def set_ew(self):
        self.ew = self.receipt.data_driver.get_ew_by_name(self.mat_type, self.name)
        self.receipt.update_all_parameters()

    def __str__(self):
        return self.__name

    def __float__(self):
        return self.__percent

    def __add__(self, other):
        return self.__percent + float(other)

    def __radd__(self, other):
        return self.__percent + float(other)

    def __rsub__(self, other):
        return float(other) - self.__percent


class Receipt:

    def __init__(self, component: str, data_driver: "DataDriver"):
        from qt_windows import MyMainWindow

        self.main_window: Optional[MyMainWindow] = None
        self.data_driver = data_driver
        self.materials: list = []
        self.sum_percent: float = 0.0
        self.component = component
        self.ew: Optional[float] = None
        self.receipt_counter: Optional[ReceiptCounter] = None
        self.scope_trigger = 0

    def add_material(self, material: Material):
        # TODO пересчёт всего в связи с изменением рецептуры
        self.materials.append(material)

    def set_main_window(self, main_window):
        self.main_window = main_window
        if self.component == "A":
            self.materials = self.main_window.material_list_a
        if self.component == "B":
            self.materials = self.main_window.material_list_b

    def remove_material(self):
        # TODO пересчёт всего в связи с изменением рецептуры
        del self.materials[-1]

    def count_sum(self):
        # Ждём, пока все материалы установят себе процент
        if self.scope_trigger:
            self.scope_trigger -= 1
            # Если остались ещё, то прерываем функцию и ждём остальных
            if not self.scope_trigger:
                return None
        self.sum_percent = round(sum(self.materials), 2)
        self.set_sum_to_qt()
        self.count_ew()
        if self.sum_percent == 100.0:
            self.update_all_parameters()

            # TODO Команда, вызывающая расчёты
            ...
        else:
            # TODO Сброс всех полей с параметрами (Стеклование, соотношение и т.д.)
            # Возможно нужно будет сбросить что-то в ReceiptCounter
            ...

    def update_all_parameters(self):
        """
        Предполагается, что сумма процентов уже посчитана
        :return:
        """
        if self.sum_percent == 100:
            self.count_ew()
            self.receipt_counter.count_mass_ratio()
        else:
            ...

    def count_ew(self):
        if self.sum_percent == 100:
            inverse_ew = 0
            for material in self.materials:
                if material.mat_type in ("Epoxy", "Amine"):
                    inverse_ew += (material.percent / material.ew)
            if inverse_ew:
                self.ew = 100 / inverse_ew
            else:
                self.ew = None
        else:
            self.ew = None
        self.set_ew_to_qt()

    def set_sum_to_qt(self):
        self.main_window.set_sum(self.sum_percent, self.component)

    def set_ew_to_qt(self):
        self.main_window.set_ew(self.component, self.ew)


class ReceiptCounter:
    def __init__(
        self, receipt_a: Receipt, receipt_b: Receipt, main_window, extra_ratio: bool = False
    ):
        from qt_windows import MyMainWindow
        self.main_window: Optional[MyMainWindow] = main_window
        self.receipt_a = receipt_a
        self.receipt_b = receipt_b
        self.__tg: Optional[float] = None
        self.__mass_ratio: Optional[float] = None
        self.extra_ratio = extra_ratio
        self.percent_df: Optional[DataFrame] = None
        # TODO прописать ссылки на окна для передачи параметров

    @property
    def tg(self):
        return self.__tg

    @tg.setter
    def tg(self, value):
        # TODO сеттер для передачи значений в окна
        if isinstance(value, float):
            self.__tg = value

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
                self.mass_ratio = - self.receipt_a.ew / self.receipt_b.ew
                return None
        self.mass_ratio = None


    def count_percent_df(self):
        # TODO реализовать логику расчёта percent_df
        ...


class DataDriver:

    def __init__(self, db_name: str):
        self.db_name = db_name

    def get_ew_by_name(self, mat_type: str, material: str):
        if material == "":
            return None
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        if mat_type == "Epoxy":
            return cursor.execute(
                f"SELECT EEW FROM Epoxy WHERE name == '{material}'"
            ).fetchall()[0][0]
        elif mat_type == "Amine":
            return cursor.execute(
                f"SELECT AHEW FROM Amine WHERE name == '{material}'"
            ).fetchall()[0][0]
        else:
            return math.inf

