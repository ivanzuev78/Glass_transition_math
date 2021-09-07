import configparser
from os.path import exists

from new_material_classes import DataDriver, Receipt, ReceiptCounter
from qt_windows import MyMainWindow, PairReactWindow

DB_NAME = "material.db"


class InitClass:
    def __init__(self, debug=False):

        src_ini_setting = 'settings.ini'
        if not exists(src_ini_setting):
            print(f'\n\n\n[CALC]: ФАЙЛ С НАСТРОЙКАМИ {src_ini_setting} НЕ НАЙДЕН')
            exit(1)
        config = configparser.ConfigParser()
        config.read(src_ini_setting)

        self.data_driver = DataDriver(config['profile']['old_db'])
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

        if not debug:
            self.my_main_window.show()
