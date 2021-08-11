import logging
import math
import sqlite3
from functools import cache
from typing import List

import numpy as np
import pandas as pd
from numpy.ma import exp
from pandas import DataFrame


def get_logger(logger_file, name=__file__, encoding="utf-8"):
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "[%(asctime)s] %(filename)s:%(lineno)d %(levelname)-8s %(message)s"
    )
    fh = logging.FileHandler(logger_file, encoding=encoding)
    fh.setFormatter(formatter)
    log.addHandler(fh)
    return log


def get_all_material_types(db_name: str) -> List[str]:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    all_material = [
        i[0] for i in cursor.fetchall() if i[0] not in ("Tg", "Tg_influence")
    ]
    all_material.insert(0, all_material.pop(all_material.index("None")))
    return all_material


def get_all_material_of_one_type(material_type: str, db_name: str) -> List[str]:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT name FROM {material_type}")
    all_material = [i[0] for i in cursor.fetchall()]
    return all_material


def get_tg_df(db_name: str) -> pd.DataFrame:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT Name FROM Epoxy")
    epoxy_name = [name[0] for name in cursor.fetchall()]
    cursor.execute("SELECT Name FROM Amine")
    amine_name = [name[0] for name in cursor.fetchall()]
    cursor.execute("SELECT * FROM Tg")
    all_tg = cursor.fetchall()
    df_tg_main = pd.DataFrame(index=epoxy_name, columns=amine_name)
    for tg in all_tg:
        df_tg_main[tg[1]][tg[0]] = tg[2]
    connection.close()
    return df_tg_main


def add_material(db_name: str, table: str, name: str, activity: float = 0) -> None:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    # INSERT INTO Product (type, model, maker)  VALUES ('PC', 1157, 'B')
    try:
        command = f"INSERT INTO {table} VALUES ('{name}', '{activity}')"
        cursor.execute(command)
        connection.commit()
    except sqlite3.IntegrityError as e:
        # TODO вызывать подсказку о том, что материал уже существует и сделать так, что бы не добавлялось сырье в список
        print(e)
        pass

    connection.close()


def add_tg_main(epoxy: str, amine: str, tg: float, db_name) -> None:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    try:
        command = f"INSERT INTO Tg VALUES ('{epoxy}', '{amine}', {tg})"
        cursor.execute(command)
        connection.commit()
    except Exception as e:
        print(e)
        pass
    connection.close()


def all_tg_from_df(tg_df: pd.DataFrame) -> List[List]:
    all_tg = []
    for i in tg_df.iloc:
        epoxy = [i.name]
        for k in i.iteritems():
            data = epoxy + list(k)
            if data[2] is not np.nan:
                all_tg.append(data)
    return all_tg


def normalize(array: np.array) -> np.array:
    return array / array.sum()


def normalize_df(df: DataFrame) -> DataFrame:
    sum_of_df = sum(df.sum())
    if sum_of_df == 0:
        # df.iloc[(df[df.columns].isna())] = 0
        return df
    return df / sum_of_df


def get_ew_by_name(material: str, mat_type: str, db_name: str):
    if material == "":
        return None
    connection = sqlite3.connect(db_name)
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


def get_tg_influence(mat_name, db_name):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    command = f"SELECT * FROM Tg_influence WHERE inf_material is '{mat_name}'"
    all_values = list(cursor.execute(command))
    key_list = (
        "name",
        "epoxy",
        "amine",
        "x_min",
        "x_max",
        "k0",
        "ke",
        "kexp",
        "k1",
        "k2",
        "k3",
        "k4",
        "k5",
    )

    result = [
        {key: value for key, value in zip(key_list, value_list)}
        for value_list in all_values
    ]
    connection.close()
    return result


def add_tg_influence(
    mat_name, epoxy, amine, k0, k1, k2, k3, k4, k5, ke, kexp, x_min, x_max, db_name
):
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    command = (
        f"INSERT INTO Tg_influence  VALUES ('{mat_name}', '{epoxy}', '{amine}', '{x_min}', '{x_max}', "
        f"'{k0}', '{ke}', '{kexp}', '{k1}', '{k2}', '{k3}', '{k4}', '{k5}')"
    )
    cursor.execute(command)
    connection.commit()
    connection.close()


def get_influence_func(k0, ke, kexp, k1, k2, k3, k4, k5):
    def function(value):
        return (
            k0
            + k1 * value
            + k2 * value ** 2
            + k3 * value ** 3
            + k4 * value ** 4
            + k5 * value ** 5
            + ke * exp(kexp * value)
        )

    return function


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    a = get_tg_influence("Бензиловый спирт", "material.db")
    a_1 = a[0]
    x = np.arange(a_1["x_min"], a_1["x_max"], 0.01)
    y = get_influence_func(
        a_1["k0"],
        a_1["ke"],
        a_1["kexp"],
        a_1["k1"],
        a_1["k2"],
        a_1["k3"],
        a_1["k4"],
        a_1["k5"],
    )()
    print(
        a_1["x_min"],
        a_1["x_max"],
        a_1["k0"],
        a_1["ke"],
        a_1["kexp"],
        a_1["k1"],
        a_1["k2"],
        a_1["k3"],
        a_1["k4"],
        a_1["k5"],
    )

    fig, ax = plt.subplots()
    ax.plot(x, y)

    # ax.set(xlabel='time (s)', ylabel='voltage (mV)',
    #        title='About as simple as it gets, folks')
    ax.grid()
    x = 2.12 * 100
    plt.scatter(2.12, y[int(x)], color="blue")
    fig.savefig("test.png")
    plt.show()

    print(*a, sep="\n")
