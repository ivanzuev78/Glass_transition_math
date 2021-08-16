from new_material_classes import Receipt, ReceiptCounter, DataDriver
from qt_windows import MyMainWindow

DB_NAME = "material.db"

class InitClass:
    def __init__(self):

        self.data_driver = DataDriver(DB_NAME)
        # Создаём главное окно
        self.my_main_window = MyMainWindow(self.data_driver)

        # Создаем рецептуры и передаём их в главное окно
        self.receipt_a = Receipt("A", self.data_driver)
        self.receipt_b = Receipt("B", self.data_driver)
        self.receipt_a.set_main_window(self.my_main_window)
        self.receipt_b.set_main_window(self.my_main_window)

        self.my_main_window.receipt_a = self.receipt_a
        self.my_main_window.receipt_b = self.receipt_b


        self.receipt_counter = ReceiptCounter(self.receipt_a, self.receipt_b, self.my_main_window)
        self.receipt_a.receipt_counter = self.receipt_counter
        self.receipt_b.receipt_counter = self.receipt_counter

        self.my_main_window.show()

