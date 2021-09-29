import math
import pickle
import sqlite3
from collections import defaultdict
from math import exp
from os.path import exists
from typing import List, Tuple, Optional, Dict, Union

from pandas import DataFrame

from res.corrections import TgCorrectionMaterial, Correction


class DataMaterial:
    def __init__(self, name, mat_type, ew, db_id=None):
        self.name: str = name
        self.mat_type: str = mat_type
        self.ew: float = ew
        self.db_id: int = db_id
        self.correction: TgCorrectionMaterial = TgCorrectionMaterial(name)

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

    def add_correction(self, correction: Correction, x_min, x_max, pair):
        self.correction.add_correction(correction, x_min, x_max, pair)

    def get_all_corrections(self):
        return self.correction.get_all_corrections()

    # def remove_correction(self, correction: Correction):
    #     if correction in self.corrections:
    #         self.corrections.remove(correction)


class DataGlass:
    """
    Не знаю, как лучше реализовать
    """

    def __init__(self, epoxy: DataMaterial, amine: DataMaterial, value: float, db_id=None):
        self.db_id = db_id
        self.epoxy = epoxy
        self.amine = amine
        self.value = value


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
            for correction_id in self.get_all_corrections_of_one_material(mat_id):
                correction_id = correction_id[0]
                correction, x_min, x_max, pair = self.get_correction_by_id(
                    correction_id
                )
                material.add_correction(correction, x_min, x_max, pair)
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
            f"SELECT Material_id, Amine,  Epoxy, x_max, x_min, Correction FROM CorrectionMaterial_map WHERE (id = '{cor_map_id}') "
        )

        (
            material_id,
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
            f"SELECT Name, Comment, k_e, k_exp FROM Corrections WHERE (id = '{correction_id}') "
        )
        cor_name, cor_comment, k_e, k_exp = cursor.fetchall()[0]
        # Получаем полиномиальные коэффициенты корректировки
        cursor.execute(
            f"SELECT Power, coef FROM corr_poly_coef_map WHERE (Correction = '{correction_id}') "
        )
        polynom_coefs = cursor.fetchall()

        correction = Correction(cor_name, cor_comment, k_e, k_exp, correction_id)
        for power, coef in polynom_coefs:
            correction.edit_polynomial_coefficient(coef, power)

        # tg_correction_material.add_correction(correction, x_min, x_max,
        #                                       (amine_name, epoxy_name) if amine_id is not None else None)
        # TODO Возможно, стоит привязывать коррекцию к материалу по id, а не по названию
        connection.close()
        return (
            correction,
            x_min,
            x_max,
            pair,
        )

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
        cursor.execute(f"SELECT * FROM Materials WHERE Name='{material.name}' AND Type='{material.mat_type}' AND ew={material.ew}")
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
        strings.append(f"DELETE FROM Prof_mat_map WHERE Material={material.db_id}")
        strings.append(
            f"DELETE FROM CorrectionMaterial_map WHERE Material_id={material.db_id}"
        )
        strings.append(
            f"DELETE FROM CorrectionMaterial_map WHERE Amine={material.db_id}"
        )
        strings.append(
            f"DELETE FROM CorrectionMaterial_map WHERE Epoxy={material.db_id}"
        )
        for string in strings:
            cursor.execute(string)
        connection.commit()
        connection.close()

    def add_correction(self, correction: Correction):

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT MAX(id) FROM Corrections")
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
        insert = f"INSERT INTO Corrections (id, Name, Comment, k_e, k_exp) VALUES (?, ?, ?, ?, ?);"
        cursor.execute(insert, data)
        # Добавляем коэффициенты в таблицу полиномиальных коэффициентов
        for power, coef in enumerate(correction.polynomial_coefficients):
            if coef != 0.0:
                data = [cor_id, power, coef]
                insert = f"INSERT INTO corr_poly_coef_map (Correction, Power, coef) VALUES (?, ?, ?);"
                cursor.execute(insert, data)
        connection.commit()
        connection.close()

    def remove_correction(self, correction: Correction):
        """
        Удаляем коррекцию из БД
        :param correction:
        :return:
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        string = f"DELETE FROM Corrections WHERE Id={correction.db_id}"
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

    # ============================= Создание БД =======================================

    def create_db(self):
        """
        # TODO реализовать создание базы данных при отсутствии файла
        (После того, как структура будет окончательной)
        """
