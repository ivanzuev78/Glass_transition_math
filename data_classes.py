import math
import pickle
import sqlite3
from math import exp
from os.path import exists
from typing import List

from pandas import DataFrame


class DataMaterial:
    def __init__(self):
        self.name = None
        self.mat_type = None
        self.ew = None
        self.path = None

    def save(self):
        # TODO Вынести путь в конфигуратор и сделать автоматическое создание папки, если её нет.
        file_name = r'data/' + f'{self.mat_type}_{self.name}_{self.ew}'
        if not exists(file_name):
            with open(file_name, 'wb') as file:
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
        with open(self.path, 'rb') as file:
            self.profile_list = pickle.load(file)

    def save_profile_manager(self) -> None:
        with open(self.path, 'wb') as file:
            pickle.dump(self.profile_list, file)

    def add_profile(self, profile: Profile) -> None:
        self.profile_list.append(profile)

    def remove_profile(self, profile: Profile) -> None:
        self.profile_list.remove(profile)


class DataDriver:
    def __init__(self, db_name: str, profile_manager: Profile):
        self.db_name = db_name
        self.profile_manager = profile_manager

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
        return self.profile_manager.get_all_types()

    def get_all_material_of_one_type_old(self, material_type: str) -> List[str]:
        connection = sqlite3.connect(self.db_name)
        cursor = connection.cursor()
        cursor.execute(f"SELECT name FROM {material_type}")
        all_material = [i[0] for i in cursor.fetchall()]
        return all_material

    def get_all_material_of_one_type(self, mat_type: str) -> List[str]:
        return [mat.name for mat in self.profile_manager.get_materials_by_type(mat_type)]

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
        self.profile_manager.add_material(material)

    def migrate_db(self):
        for mat_type in self.get_all_material_types_old():
            for name in self.get_all_material_of_one_type_old(mat_type):
                ew = self.get_ew_by_name(mat_type, name)
                material = DataMaterial()
                material.create_new(name, mat_type, ew)

                self.add_material_to_profile_manager(material)

