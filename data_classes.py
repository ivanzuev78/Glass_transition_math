import pickle
from math import exp
from typing import List


class DataMaterial:
    def __init__(self):
        self.name = None
        self.mat_type = None
        self.ew = None
        self.path = None

    def save(self):
        ...

    def create_new(self, name, mat_type, ew):
        self.name = name
        self.mat_type = mat_type
        self.ew = ew

    def load(self, path):
        ...

    def to_json(self):
        data = {}
        data["name"] = self.name
        data["mat_type"] = self.mat_type
        data["ew"] = self.ew
        return data


class TgInfluence:
    """
    f(x) = k_e * exp(k_exp * x) + k0 + k1 * x + k2 * x2 ...
    """
    def __init__(self):

        self.x_min = None
        self.x_max = None

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
        # TODO Подумать, где сделать обработку пределов: здесь или в классе, который будет управлять влияниями
        if self.x_min <= value <= self.x_max:
            result = self.k_e * exp(self.k_exp * value)
            for power, coef in enumerate(self.polynomial_coefficients):
                result += coef * value ** power
            return result
        else:
            return 0.0


class DataGlass:
    """
    Не знаю, как лучше реализовать
    """


class DataProfile:
    def __init__(self, profile_name: str):
        self.profile_name = profile_name
        # {тип: [список материалов]}
        self._materials = {}

    def add_material(self, material: DataMaterial) -> None:
        """
        Функция для добавления материала в профиль
        :param material:
        :return:
        """
        mat_type: str = material.mat_type
        if mat_type not in self._materials:
            self._materials[mat_type] = []
        self._materials[mat_type].append(material)

    def remove_material(self, material: DataMaterial) -> None:
        """
        Функция для удаления материала из профиля
        :param material:
        :return:
        """
        mat_type: str = material.mat_type
        if mat_type in self._materials:
            if material in self._materials[mat_type]:
                self._materials[mat_type].remove(material)

    def get_materials_by_type(self, mat_type: str) -> List[DataMaterial]:
        """
        Функция для получения всех материалов конкретного типа
        :param mat_type: Тип мптериала
        :return: Список материалов
        """
        if mat_type in self._materials:
            return self._materials[mat_type]
        else:
            return []

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
        return list(self._materials.keys())

    def copy_profile(self, profile_name: str) -> "DataProfile":
        """
        Функция для копирования профиля
        :param profile_name: Имя нового пользователя
        :return: Новый профиль
        """
        new_dp = DataProfile(profile_name)
        for mat_type in self._materials:
            materials = self.get_materials_by_type(mat_type)
            for material in materials:
                new_dp.add_material(material)
        return new_dp


class ProfileManager:
    def __init__(self, path: str):
        self.profile_list = []
        self.path = path

    def load_profile_manager(self) -> None:
        with open(self.path, 'rb') as file:
            self.profile_list = pickle.load(file)

    def save_profile_manager(self) -> None:
        with open(self.path, 'wb') as file:
            pickle.dump(self.profile_list, file)

    def add_profile(self, profile: DataProfile) -> None:
        self.profile_list.append(profile)

    def remove_profile(self, profile: DataProfile) -> None:
        self.profile_list.remove(profile)