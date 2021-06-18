import logging
import sqlite3
from typing import List

import numpy as np
import pandas as pd
from numpy.ma import exp


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
    all = [i[0] for i in cursor.fetchall() if i[0] not in ("Tg", "Tg_influence")]
    all.insert(0, all.pop(all.index("None")))
    return all


def get_all_material_of_one_type(material_type: str, db_name: str) -> List[str]:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute(f"SELECT name FROM {material_type}")
    all = [i[0] for i in cursor.fetchall()]
    return all


def get_tg_df(db_name: str) -> pd.DataFrame:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    cursor.execute("SELECT Name FROM Epoxy")
    epoxy_name = [name[0] for name in cursor.fetchall()]
    cursor.execute("SELECT Name FROM Amine")
    amine_name = [name[0] for name in cursor.fetchall()]
    cursor.execute("SELECT * FROM Tg")
    all_tg = cursor.fetchall()
    df_tg_base = pd.DataFrame(index=epoxy_name, columns=amine_name)
    for tg in all_tg:
        df_tg_base[tg[1]][tg[0]] = tg[2]
    connection.close()
    return df_tg_base


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


def add_tg_base(epoxy: str, amine: str, tg: float, db_name) -> None:
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


def normalize(array: np.array):
    return array / array.sum()

def normalize_df(array: pd.DataFrame):
    summ = sum(array.sum())
    return array / summ


def get_ew_by_name(material, mat_type, db_name):
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


# print(get_ew_by_name('MXDA', 'Amine', 'material.db'))


def get_influence_func(x_min, x_max, k0, ke, kexp, k1, k2, k3, k4, k5):
    def function(*args):
        x = np.arange(x_min, x_max, 0.00001)
        f = (
                k0
                + k1 * x
                + k2 * x ** 2
                + k3 * x ** 3
                + k4 * x ** 4
                + k5 * x ** 5
                + ke * exp(kexp * x)
        )
        if args:
            if len(args) == 1:
                print(int(round(args[0], 5) * 100000))
                print(f[int(round(args[0], 5) * 100000)])
                return f[int(round(args[0], 5) * 100000)]
            else:
                return [f[int(round(numb, 5) * 100000)] for numb in args]
        else:
            return x, f
    return function


if __name__ == "__main__":
    import numpy as np
    import matplotlib.pyplot as plt

    a = get_tg_influence("Бензиловый спирт", "material.db")
    a_1 = a[0]
    x = np.arange(a_1["x_min"], a_1["x_max"], 0.01)
    y = get_influence_func(
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
