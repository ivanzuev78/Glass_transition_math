from new_material_classes import Receipt, ReceiptCounter
from qt_windows import MyMainWindow


class InitClass:
    def __init__(self):

        # Создаём главное окно
        self.my_main_window = MyMainWindow()
        self.my_main_window.show()
        # Создаем рецептуры и передаём их в главное окно
        self.receipt_a = Receipt("A")
        self.receipt_b = Receipt("B")
        self.receipt_a.set_main_window(self.my_main_window)
        self.receipt_b.set_main_window(self.my_main_window)

        self.my_main_window.receipt_a = self.receipt_a
        self.my_main_window.receipt_b = self.receipt_b

        self.receipt_counter = ReceiptCounter(self.receipt_a, self.receipt_b)
