import configparser
import pickle
from os.path import exists

from data_classes import Profile, ProfileManager, ORMDataBase
from material_classes import Receipt, ReceiptCounter
from qt_windows import MyMainWindow, PairReactWindow, ProfileManagerWindow

DB_NAME = "material.db"


class InitClass:
    def __init__(self, debug=False):
        self.debug = debug
        src_ini_setting = "settings.ini"
        if not exists(src_ini_setting):
            print(
                f"ФАЙЛ С НАСТРОЙКАМИ {src_ini_setting} НЕ НАЙДЕН\nУстановленны настройки по умолчанию"
            )
            # Создаем файл с настройками по умолчанию
            with open(src_ini_setting, "w") as file:
                file.write("[profile]\n")
                file.write("path_db=data.db\n")
                file.write("[style]\n")
                file.write("style_path=style.css\n")

        # Парсим данные
        self.config = configparser.ConfigParser()
        self.config.read(src_ini_setting)

        self.orm_db = ORMDataBase(self.config["profile"]["path_db"])

        self.profile_manager_window = ProfileManagerWindow(
            self.orm_db.get_all_profiles(), self
        )

        if not debug:
            self.profile_manager_window.show()

    def setup_program(self, profile_name: str):
        # новый профиль с БД

        self.profile: Profile = self.orm_db.read_profile(profile_name)

        # self.data_driver.migrate_db()
        # self.profile_manager.save_profile_manager()

        # ==== Создаём главное окно ====
        self.my_main_window = MyMainWindow(self.profile, debug=self.debug)
        self.profile.my_main_window = self.my_main_window

        # ============== Создаем рецептуры и передаём их в главное окно ==================
        self.receipt_a = Receipt("A", self.profile)
        self.receipt_b = Receipt("B", self.profile)
        self.receipt_a.set_main_window(self.my_main_window)
        self.receipt_b.set_main_window(self.my_main_window)

        self.my_main_window.receipt_a = self.receipt_a
        self.my_main_window.receipt_b = self.receipt_b
        self.my_main_window.pair_react_window = PairReactWindow(
            self.my_main_window, self.receipt_a, self.receipt_b
        )

        # =============== Настраиваем ReceiptCounter ==========================

        self.receipt_counter = ReceiptCounter(
            self.receipt_a, self.receipt_b, self.my_main_window
        )
        self.receipt_counter.pair_react_window = self.my_main_window.pair_react_window
        # self.receipt_counter.profile = profile
        self.receipt_a.receipt_counter = self.receipt_counter
        self.receipt_b.receipt_counter = self.receipt_counter

        if not self.debug:
            self.my_main_window.show()
