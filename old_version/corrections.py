from collections import defaultdict
from math import exp
from typing import Tuple


class Correction:
    """
    f(x) = k_e * exp(k_exp * x) + k0 + k1 * x + k2 * x2 ...
    """
    def __init__(self):
        self.k_e = 0
        self.k_exp = 0
        self.polynomial_coefficients = []

    def add_polynomial_coefficient(self, coef: float, power: int) -> None:
        """
        Позволяет добавить коэффициент при любой степени Х в полиноме
        :param coef: Значение кожффициента
        :param power: Степень икса, перед которой стоит этот коэффициент
        :return: None
        """
        while len(self.polynomial_coefficients) < power:
            self.polynomial_coefficients.append(0.0)
        self.polynomial_coefficients[power] = coef

    def __call__(self, value) -> float:
        """
        Функция для расчёта влияния на заданных коэффициентов
        :param value:
        :return:
        """
        result = self.k_e * exp(self.k_exp * value)
        for power, coef in enumerate(self.polynomial_coefficients):
            result += coef * value ** power
        return result


class TgCorrectionMaterial:
    def __init__(self):

        self.corrections_funcs = defaultdict(dict)
        self.global_correction = {}
        ...

    def add_correction(self, correction: Correction, x_min: float, x_max: float, pair: Tuple = None) -> None:
        """
        Добавляет коррекцию
        :param correction: Коррекция для расчёта
        :param x_min: Нижний предел применения функции
        :param x_max: Верхний предел применения функции
        :param pair: Пара, на которую идет влияние. Если нет, то будет влиять на всю систему
        """
        if pair is not None:
            self.corrections_funcs[pair][(x_min, x_max)] = correction
        else:
            self.global_correction[(x_min, x_max)] = correction

    def remove_correction(self, limits: Tuple[float], pair: Tuple[str] = None) -> None:
        """
        Удаляет коррекцию с заданной позиции
        :param pair:
        :param limits:
        :return:
        """
        if pair is not None:
            if pair in self.corrections_funcs.keys():
                if limits in self.corrections_funcs[pair]:
                    del self.corrections_funcs[pair][limits]
                    if not self.corrections_funcs[pair]:
                        del self.corrections_funcs[pair]
        else:
            if limits in self.global_correction.keys():
                del self.global_correction[limits]





class TgCorrectionManager:
    def __init__(self):
        self.all_corrections_materials = []
        self.all_corrections_funcs = []
        self.used_corrections_materials = {}


        ...


