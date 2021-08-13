
from PyQt5 import uic, QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPixmap, QImage, QPalette, QBrush


DB_NAME = "material.db"
# DB_NAME = "material_for_test.db"

class MyMainWindow(QtWidgets.QMainWindow, uic.loadUiType("windows/Main_window.ui")[0]):
    def __init__(self, db_name=DB_NAME):
        super(MyMainWindow, self).__init__()
        self.setupUi(self)

        oImage = QImage("fon.jpg")
        # sImage = oImage.scaled(QSize(self.window_height, self.window_width))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))
        self.setPalette(palette)

        self.button_list = [
            self.a_recept_but,
            self.b_recept_but,
            self.b_recept_but,
            self.debug_but,
            self.normalise_A,
            self.normalise_B,
            self.update_but,
            self.font_up_but,
            self.font_down_but,
            self.radioButton_A,
            self.radioButton_B,
        ]
        self.big_button_list = [
            self.add_A_but,
            self.add_B_but,
            self.del_A_but,
            self.del_B_but,
        ]
        self.all_labels = [
            self.mass_ratio_label,
            self.tg_main_label,
            self.mass_ratio_label_2,
            self.label_3,
            self.label_4,
            self.label_5,
            self.label_6,
            self.label_7,
            self.label_8,
            self.eew_label,
            self.ahew_label,
            self.extra_ew_label,
            self.sintez_pair_label,
            self.debug_string,
            self.lineEdit_name_a,
            self.lineEdit_name_b,
            self.lineEdit_sintez_mass,
            self.tg_cor_label,
            self.tg_extra_label,
            self.extra_ratio_line,
        ]
        self.all_big_labels = [self.label, self.label_2]
        self.font_size = 10
        self.font_size_big = 15

        with open("style.css", "r") as f:
            self.style, self.style_combobox = f.read().split("$split$")
        self.set_buttom_stylies()

        self.hide_top('A')
        self.hide_top('B')



    def set_buttom_stylies(self):
        for widget in self.button_list + self.big_button_list:
            widget.setStyleSheet(self.style)


    def hide_top(self, komponent: str):
        if komponent == "A":
            self.label_3.hide()
            self.label_5.hide()
            self.normalise_A.hide()
            self.label_lock_a.hide()
            # self.a_ew = 0
        if komponent == "B":
            self.label_4.hide()
            self.label_6.hide()
            self.normalise_B.hide()
            self.label_lock_b.hide()
            # self.ew_b = 0