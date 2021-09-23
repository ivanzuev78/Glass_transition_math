from collections import defaultdict
from math import exp
from typing import Tuple, Iterable, List, Union


class Correction:
    """
    f(x) = k_e * exp(k_exp * x) + k0 + k1 * x + k2 * x2 ...
    """

    def __init__(self, cor_name: str, cor_comment: str, k_e: float = 0, k_exp: float = 0, db_id: int = None,
                 polynomial_coefficients: Iterable = None):
        self.name = cor_name
        self.comment = cor_comment
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


class TgCorrectionMaterial:
    """ """

    def __init__(self, name):
        self.name = name  # Название материала, который влияет на систему
        self.correction_funcs = defaultdict(dict)
        self.global_correction = {}

    def add_correction(
        self, correction: Correction, x_min: float, x_max: float, pair: Tuple = None
    ) -> None:
        """
        Добавляет коррекцию
        :param correction: Коррекция для расчёта
        :param x_min: Нижний предел применения функции
        :param x_max: Верхний предел применения функции
        :param pair: Пара, на которую идет влияние. Если нет, то будет влиять на всю систему
        """
        # TODO добавить обработку случаев, когда границы накладываются
        if pair is not None:
            self.correction_funcs[pair][(x_min, x_max)] = correction
        else:
            self.global_correction[(x_min, x_max)] = correction

    def remove_correction(self, limit: Tuple[float], pair: Tuple[str] = None) -> None:
        """
        Удаляет коррекцию с заданной позиции
        :param pair:
        :param limit:
        :return:
        """
        if pair is not None:
            if pair in self.correction_funcs.keys():
                if limit in self.correction_funcs[pair]:
                    del self.correction_funcs[pair][limit]
                    if not self.correction_funcs[pair]:
                        del self.correction_funcs[pair]
        else:
            if limit in self.global_correction.keys():
                del self.global_correction[limit]

    def get_all_corrections(self) -> List[Tuple[Correction, Tuple[float, float], Union[Tuple, None]]]:
        """
        Возвращает список коррекций данного материала
        :return: [ [Correction, limits, pair] , [...], ... ]
        """
        corrections = []
        for pair, cor_dict in self.correction_funcs.items():
            for limits, correction in cor_dict.items():
                corrections.append([correction, limits, pair])
        for limits, correction in self.global_correction.items():
            corrections.append((correction, limits, None))
        return corrections

    def __call__(self, value: float, pair: Tuple[str] = None) -> dict:
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
            if pair in self.correction_funcs.keys():
                for limit in self.correction_funcs[pair].keys():
                    if limit[0] <= limit <= limit[1]:
                        return {
                            "value": self.correction_funcs[pair][limit](value),
                            "code": 1,
                        }
        for limit in self.global_correction.keys():
            if limit[0] <= limit <= limit[1]:
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
            if self.name == other.name:
                for pair in other.correction_funcs.keys():
                    for limit, correction in other.correction_funcs[pair].items():
                        self.add_correction(
                            correction=correction,
                            pair=pair,
                            x_min=limit[0],
                            x_max=limit[1],
                        )
                for limit, correction in other.global_correction.items():
                    self.add_correction(
                        correction=correction, x_min=limit[0], x_max=limit[1]
                    )


class TgCorrectionManager:
    def __init__(self):
        self.all_corrections_materials = []
        self.all_corrections_funcs = []
        self.used_corrections_materials = {}

    def add_tg_correction_material(
        self, correction_material: TgCorrectionMaterial
    ) -> None:
        """
        Добавляет коррекцию материала в менеджер
        :param correction_material:
        :return:
        """
        self.all_corrections_materials.append(correction_material)
        self.used_corrections_materials[correction_material.name] = correction_material

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
