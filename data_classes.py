import math
import pickle
import sqlite3
from math import exp
from os.path import exists
from typing import List, Tuple

from pandas import DataFrame

from corrections import TgCorrectionMaterial, Correction


class DataMaterial:
    def __init__(self, name, mat_type, ew, db_id=None):
        self.name = name
        self.mat_type = mat_type
        self.ew = ew
        self.db_id = db_id

    def save(self):
        # TODO Вынести путь в конфигуратор и сделать автоматическое создание папки, если её нет.
        file_name = r"data/" + f"{self.mat_type}_{self.name}_{self.ew}"
        if not exists(file_name):
            with open(file_name, "wb") as file:
                pickle.dump(self, file)
        ...

    def create_new(self, name, mat_type, ew):
        self.name = name
        self.mat_type = mat_type
        self.ew = ew
        self.save()

    def load(self, path):
        ...

    def to_json(self):
        data = {}
        data["name"] = self.name
        data["mat_type"] = self.mat_type
        data["ew"] = self.ew
        return data


class DataGlass:
    """
    Не знаю, как лучше реализовать
    """


class Profile:
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

    def copy_profile(self, profile_name: str) -> "Profile":
        """
        Функция для копирования профиля
        :param profile_name: Имя нового пользователя
        :return: Новый профиль
        """
        new_dp = Profile(profile_name)
        for mat_type in self._materials:
            materials = self.get_materials_by_type(mat_type)
            for material in materials:
                new_dp.add_material(material)
        return new_dp


class ProfileManager:
    def __init__(self, path: str, profile_list=None):
        if profile_list is not None:
            self.profile_list = profile_list
        else:
            self.profile_list = []
        self.path = path
        self.save_profile_manager()

    def load_profile_manager(self) -> None:
        with open(self.path, "rb") as file:
            self.profile_list = pickle.load(file)

    def save_profile_manager(self) -> None:
        with open(self.path, "wb") as file:
            pickle.dump(self.profile_list, file)

    def add_profile(self, profile: Profile) -> None:
        self.profile_list.append(profile)

    def remove_profile(self, profile: Profile) -> None:
        self.profile_list.remove(profile)


class DataDriver:
    def __init__(self, db_name: str, profile: Profile):
        self.db_name = db_name
        self.profile = profile

    def get_ew_by_name(self, mat_type: str, material: str):
        for mat in self.profile._materials[mat_type]:
            if mat.name == material:
                return mat.ew
        return 0

    def get_ew_by_name_old(self, mat_type: str, material: str):
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

    def get_all_material_types_old(self) -> List[str]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        all_material = [
            i[0] for i in cursor.fetchall() if i[0] not in ("Tg", "Tg_influence")
        ]
        all_material.insert(0, all_material.pop(all_material.index("None")))
        return all_material

    def get_all_material_types(self) -> List[str]:
        return self.profile.get_all_types()

    def get_all_material_of_one_type_old(self, material_type: str) -> List[str]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT name FROM {material_type}")
        all_material = [i[0] for i in cursor.fetchall()]
        return all_material

    def get_all_material_of_one_type(self, mat_type: str) -> List[str]:
        return [mat.name for mat in self.profile.get_materials_by_type(mat_type)]

    def get_tg_df(self) -> DataFrame:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT Name FROM Epoxy")
        epoxy_name = [name[0] for name in cursor.fetchall()]
        cursor.execute("SELECT Name FROM Amine")
        amine_name = [name[0] for name in cursor.fetchall()]
        cursor.execute("SELECT * FROM Tg")
        all_tg = cursor.fetchall()
        df_tg_main = DataFrame(index=epoxy_name, columns=amine_name)
        for tg in all_tg:
            df_tg_main[tg[1]][tg[0]] = tg[2]
        connection.close()
        return df_tg_main

    def add_material_to_profile_manager(self, material: DataMaterial):
        self.profile.add_material(material)

    def migrate_db(self):
        for mat_type in self.get_all_material_types_old():
            for name in self.get_all_material_of_one_type_old(mat_type):
                ew = self.get_ew_by_name(mat_type, name)
                material = DataMaterial(name, mat_type, ew, None)
                self.add_material_to_profile_manager(material)


class ORMDataBase:
    def __init__(self):
        self.db_name = "data.db"
        self.current_profile = None

    def read_profile(self, profile_name: str) -> Profile:
        profile = Profile(profile_name)
        for mat_id, correction_map_str in self.get_profile_material_map(profile_name):
            mat_name, mat_type, ew = self.get_material_by_id(mat_id)
            profile.add_material(DataMaterial(mat_name, mat_type, ew, mat_id))
            if correction_map_str is not None:
                correction_material_id_list = map(
                    lambda x: int(x), correction_map_str.split(",")
                )
                tg_correction_material = TgCorrectionMaterial(mat_name)
                for cor_map_id in correction_material_id_list:
                    correction, x_min, x_max, pair = self.get_correction_by_id(
                        cor_map_id
                    )
                    tg_correction_material.add_correction(
                        correction, x_min, x_max, pair
                    )
                # TODO Подключить коррекцию к профилю (нужно реализовать логику в самом профиле)
        return profile

    def get_all_profiles(self) -> List[str]:
        """
        Получение всех профилей из базы
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM Profiles")
        all_profiles = [res[0] for res in cursor.fetchall()]
        return all_profiles

    def get_profile_material_map(self, profile: str) -> List[Tuple]:
        """
        Получение списка всех материалов в профиле и их коррекций
        :param profile: Имя профиля
        :return: Список материалов, которые подключены к профилю
        """
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(
            f"SELECT Material, CorrMat_map FROM Prof_mat_map WHERE (Profile = '{profile}') "
        )
        return cursor.fetchall()

    def get_material_by_id(self, mat_id: int) -> Tuple:
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
        return cursor.fetchall()[0]

    # ??????????????????????????????????
    def get_tg_by_material_id(self, mat_id):
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM Materials WHERE (id = '{mat_id}') ")
        return cursor.fetchall()[0]

    def get_correction_by_id(self, cor_map_id):
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

        # Если есть амин, значит коррекция для пары, а не на всю систему
        if amine_id is not None:
            cursor.execute(f"SELECT Name FROM Materials WHERE (id = '{amine_id}') ")
            amine_name = cursor.fetchall()[0][0]
            cursor.execute(f"SELECT Name FROM Materials WHERE (id = '{epoxy_id}') ")
            epoxy_name = cursor.fetchall()[0][0]

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

        correction = Correction(cor_name, cor_comment, k_e, k_exp)
        for power, coef in polynom_coefs:
            correction.edit_polynomial_coefficient(coef, power)

        # tg_correction_material.add_correction(correction, x_min, x_max,
        #                                       (amine_name, epoxy_name) if amine_id is not None else None)

        return (
            correction,
            x_min,
            x_max,
            (amine_name, epoxy_name) if amine_id is not None else None,
        )

    def add_material(self, material: DataMaterial, profile: Profile = None):

        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT id FROM Materials")
        all_id = cursor.fetchall()
        mat_id = max(all_id, key=lambda x: int(x[0]))[0] + 1
        material.db_id = mat_id

        data = [mat_id, material.name, material.mat_type, material.ew]
        insert = f"INSERT INTO Materials (id, name, type, ew) VALUES (?, ?, ?, ?);"
        cursor.execute(insert, data)
        connection.commit()
        if profile is not None:
            insert = f"INSERT INTO Prof_mat_map (Profile, Material) VALUES (?, ?);"
            data = [profile.profile_name, mat_id]
            cursor.execute(insert, data)
            connection.commit()
        elif self.current_profile is not None:
            insert = f"INSERT INTO Prof_mat_map (Profile, Material) VALUES (?, ?);"
            data = [self.current_profile.profile_name, mat_id]
            cursor.execute(insert, data)
            connection.commit()
