import sqlite3
from collections import defaultdict
from math import exp
from typing import List, Tuple, Optional, Dict, Union, Iterable

from pandas import DataFrame


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


class CorrectionFunction:
    """
    f(x) = k_e * exp(k_exp * x) + k0 + k1 * x + k2 * x2 ...
    """

    def __init__(
            self,
            cor_name: str,
            cor_comment: str,
            k_e: float = 0,
            k_exp: float = 0,
            db_id: int = None,
            polynomial_coefficients: Iterable = None,
    ):
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


class Correction:
    def __init__(self, x_min: float, x_max: float, correction_func: CorrectionFunction,
                 amine: DataMaterial = None, epoxy: DataMaterial = None, db_id: int = None):
        self.x_min = x_min
        self.x_max = x_max
        self.amine = amine
        self.epoxy = epoxy
        self.correction_func = correction_func
        self.db_id = db_id

    def __call__(self, value):
        return self.correction_func(value)


class TgCorrectionMaterial:
    """ """

    def __init__(self, material: DataMaterial):
        self.material = material  # Название материала, который влияет на систему
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
        pair = (correction.amine, correction.epoxy) if correction is not None else None
        if pair is not None:
            self.corrections[pair][(x_min, x_max)] = correction
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
            if pair in self.corrections.keys():
                for limit in self.corrections[pair].keys():
                    if limit[0] <= limit <= limit[1]:
                        return {
                            "value": self.corrections[pair][limit](value),
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


class Profile:
    def __init__(self, profile_name: str, orm_db: "ORMDataBase"):

        self.profile_name = profile_name
        # {тип: [список материалов]}
        self.materials: Dict[str, List[DataMaterial]] = defaultdict(
            list
        )  # Тип: Список материалов данного типа
        self.id_name_dict: Dict[int, DataMaterial] = {}
        self.orm_db = orm_db
        self.my_main_window: Optional["MyMainWindow"] = None
        self.tg_df = None
        self.tg_list = None

    def add_material(self, material: DataMaterial) -> None:
        """
        Функция для добавления материала в профиль
        :param material:
        :return:
        """
        if material not in self.materials[material.mat_type]:
            self.materials[material.mat_type].append(material)
            self.id_name_dict[material.db_id] = material
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
        if material.db_id in self.id_name_dict:
            del self.id_name_dict[material.db_id]
        if self.my_main_window is not None:
            self.my_main_window.update_list_of_material_names()
        # Если материал Амин или Эпоксид, обнуляем tg_df
        if self.tg_df is not None and material.mat_type in ("Amine", "Epoxy"):
            self.tg_df = None

    def get_materials_by_type(self, mat_type: str) -> List[DataMaterial]:
        """
        Функция для получения всех материалов конкретного типа
        :param mat_type: Тип материала
        :return: Список материалов
        """
        return self.materials[mat_type]

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

    def get_tg_df(self) -> DataFrame:
        if self.tg_df is None:
            self.tg_df = DataFrame(
                index=self.get_mat_names_by_type("Epoxy"),
                columns=self.get_mat_names_by_type("Amine"),
            )
            if "Epoxy" in self.materials.keys() and "Amine" in self.materials.keys():
                all_id_epoxy = [mat.db_id for mat in self.materials["Epoxy"]]
                all_id_amine = [mat.db_id for mat in self.materials["Amine"]]
                self.tg_list = self.orm_db.get_tg_by_materials_ids(all_id_epoxy, all_id_amine)
                for data_glass in self.tg_list:
                    epoxy_name = self.id_name_dict[data_glass.epoxy].name
                    amine_name = self.id_name_dict[data_glass.amine].name
                    self.tg_df.loc[epoxy_name, amine_name] = data_glass.value

        return self.tg_df

    def get_data_material(self, mat_type: str, mat_index: int) -> Optional[DataMaterial]:
        if not mat_type or mat_index == -1:
            return None
        return self.materials[mat_type][mat_index]


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

            # Подключаем все коррекции
            # TODO Подключить все коррекции
            # for correction_id in self.get_all_corrections_of_one_material(mat_id):
            #     correction_id = correction_id[0]
            #     correction_func, x_min, x_max, pair = self.get_correction_by_id(
            #         correction_id
            #     )
            #     if pair is not None:
            #
            #     correction = Correction(x_min, x_max, correction_func)
            #     material.add_correction(correction)

            self.all_materials[mat_id] = material

    def get_all_materials(self) -> List[DataMaterial]:
        return [i for i in self.all_materials.values()]

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

    # Пока не используется
    def get_material_by_id(self, mat_id: int) -> DataMaterial:
        """
        Получение материала по id. Используется после получения всех id материалов в профиле
        :param mat_id:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT Name, Type, ew  FROM Materials WHERE (id = '{mat_id}') "
        )
        result = cursor.fetchall()
        material = DataMaterial(*result[0], mat_id)
        connection.close()
        return material

    def get_tg_by_materials_ids(self, epoxy_id: List[int], amine_id: List[int]):
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
        for tg_id, epoxy, amine, value in cursor.fetchall():
            tg_list.append(DataGlass(epoxy, amine, value, tg_id))
        connection.close()
        return tg_list

    def get_all_corrections_of_one_material(self, mat_id: int):
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
        result = cursor.fetchall()
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
            f"SELECT Amine,  Epoxy, x_max, x_min, Correction_func FROM Correction_map WHERE (id = '{cor_map_id}') "
        )

        (
            amine_id,
            epoxy_id,
            x_max,
            x_min,
            correction_id,
        ) = cursor.fetchall()[0]
        pair = None
        # Если есть амин, значит коррекция для пары, а не на всю систему
        if amine_id is not None:
            cursor.execute(f"SELECT Name FROM Materials WHERE (id = '{amine_id}') ")
            amine_name = cursor.fetchall()[0][0]
            cursor.execute(f"SELECT Name FROM Materials WHERE (id = '{epoxy_id}') ")
            epoxy_name = cursor.fetchall()[0][0]
            pair = (amine_name, epoxy_name)

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
        return (cor_func, x_min, x_max, pair)

    def get_all_materials_data(self) -> List[Tuple]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
        result = cursor.fetchall()
        connection.close()
        return result

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
            f"SELECT * FROM Materials WHERE Name='{material.name}' AND Type='{material.mat_type}' AND ew={material.ew}")
        result = cursor.fetchall()
        if len(result) > 0:
            # TODO Подумать, что делать, если пытаются добавить материал, который уже есть в базе.
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
        connection.commit()
        connection.close()

    def add_correction_func(self, correction: CorrectionFunction):

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(id) FROM Correction_funcs")
        max_id = cursor.fetchone()
        cor_id = max_id[0] + 1 if max_id[0] is not None else 1
        correction.db_id = cor_id
        data = [
            cor_id,
            correction.name,
            correction.comment,
            correction.k_e,
            correction.k_exp,
        ]
        insert = f"INSERT INTO Correction_funcs (id, Name, Comment, k_e, k_exp) VALUES (?, ?, ?, ?, ?);"
        cursor.execute(insert, data)
        # Добавляем коэффициенты в таблицу полиномиальных коэффициентов
        for power, coef in enumerate(correction.polynomial_coefficients):
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

    # ============================= Создание БД =======================================

    def create_db(self):
        """
        # TODO реализовать создание базы данных при отсутствии файла
        (После того, как структура будет окончательной)
        """
