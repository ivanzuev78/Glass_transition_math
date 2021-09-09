import configparser
import pickle
from os.path import exists

from data_classes import ProfileManager, Profile, DataDriver
from material_classes import Receipt, ReceiptCounter
from qt_windows import MyMainWindow, PairReactWindow, ProfileManagerWindow

DB_NAME = "material.db"


class InitClass:
    def __init__(self, debug=False):

        src_ini_setting = 'settings.ini'
        if not exists(src_ini_setting):
            print(f'\n\n\n[CALC]: ФАЙЛ С НАСТРОЙКАМИ {src_ini_setting} НЕ НАЙДЕН')
            exit(1)
        config = configparser.ConfigParser()
        config.read(src_ini_setting)
        if exists(config['profile']['profile_manager']):
            with open(config['profile']['profile_manager'], 'rb') as file:
                self.profile_manager = ProfileManager(config['profile']['profile_manager'], pickle.load(file))
        else:
            self.profile_manager = ProfileManager(config['profile']['profile_manager'])
            # TODO убрать заглушку создания профиля
            self.profile_manager.profile_list.append(Profile('Ivan'))

        self.data_driver = DataDriver(config['profile']['old_db'], self.profile_manager.profile_list[0])
        # self.data_driver.migrate_db()
        # self.profile_manager.save_profile_manager()

        # ==== Создаём главное окно ====
        self.my_main_window = MyMainWindow(self.data_driver, debug=debug)

        # ============== Создаем рецептуры и передаём их в главное окно ==================
        self.receipt_a = Receipt("A", self.data_driver)
        self.receipt_b = Receipt("B", self.data_driver)
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
        self.receipt_counter.data_driver = self.data_driver
        self.receipt_a.receipt_counter = self.receipt_counter
        self.receipt_b.receipt_counter = self.receipt_counter

        self.profile_manager_window = ProfileManagerWindow(self.my_main_window, self.profile_manager)

        if not debug:
            self.profile_manager_window.show()
