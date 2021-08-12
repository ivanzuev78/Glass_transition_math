from typing import Optional

from pandas import DataFrame


class Material:
    def __init__(self, mat_type: str, mat_name: str, mat_ew: float, receipt: "Receipt", extra_receipt: "Receipt"):
        self.__mat_type = mat_type
        self.__name = mat_name
        self.__ew = mat_ew
        self.receipt = receipt
        self.extra_receipt = extra_receipt
        self.__percent: float = 0.0

        receipt.add_material(self)
        extra_receipt.add_material(self)

    @property
    def percent(self) -> float:
        return self.__percent

    @percent.setter
    def percent(self, value: float):
        # TODO сеттер на изменение процентов
        if isinstance(value, float):
            self.__percent = value

    @property
    def ew(self) -> float:
        return self.__ew

    @ew.setter
    def ew(self, value: float):
        # TODO сеттер на изменение ew
        if isinstance(value, float):
            if self.mat_type == 'Amine':
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
        if isinstance(value, float):
            self.__mat_type = value

    def __str__(self):
        return self.__name

    def __float__(self):
        return self.__percent


class Receipt:
    def __init__(self):
        self.materials: list = []
        self.sum_percent: float = 0.0
        self.ew: Optional[float] = None
        self.receipt_counter: Optional[ReceiptCounter] = None

    def add_material(self, material: Material):
        # TODO пересчёт всего в связи с изменением рецептуры
        self.materials.append(material)

    def remove_material(self, material: Material):
        # TODO пересчёт всего в связи с изменением рецептуры
        if material in self.materials:
            self.materials.pop(self.materials.index(material))

    def count_sum(self):
        self.sum_percent = sum(map(float, self.materials))


class ReceiptCounter:
    def __init__(self, receipt_a: Receipt, receipt_b: Receipt, extra_ratio: bool = False):
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
        if isinstance(value, float):
            self.__mass_ratio = value

    def count_percent_df(self):
        # TODO реализовать логику расчёта percent_df
        ...


class InitClass:
    def __init__(self):
        # TODO Прописать MyMainWindow
        self.my_main_window = None
        self.receipt_a = Receipt()
        self.receipt_b = Receipt()
        self.receipt_counter = ReceiptCounter(self.receipt_a, self.receipt_b)
        self.receipt_counter_extra = ReceiptCounter(self.receipt_a, self.receipt_b, extra_ratio=True)
