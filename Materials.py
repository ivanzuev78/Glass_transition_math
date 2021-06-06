import logging
import sqlite3
from typing import List

import numpy as np
import pandas as pd


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
    all = [i[0] for i in cursor.fetchall() if i[0] != 'Tg']
    all.insert(0, all.pop(all.index('None')))
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
    cursor.execute('SELECT Name FROM Epoxy')
    epoxy_name = [name[0] for name in cursor.fetchall()]
    cursor.execute('SELECT Name FROM Amine')
    amine_name = [name[0] for name in cursor.fetchall()]
    cursor.execute('SELECT * FROM Tg')
    all_tg = cursor.fetchall()
    df_tg_base = pd.DataFrame(index=epoxy_name, columns=amine_name)
    for tg in all_tg:
        df_tg_base[tg[1]][tg[0]] = tg[2]
    connection.close()
    return df_tg_base


def add_material(db_name: str, table: str, name: str, activity: float = None,
                 tg_inf_type: str = None, a: float = None, b: float = None) -> None:
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    #INSERT INTO Product (type, model, maker)  VALUES ('PC', 1157, 'B')
    try:
        command = f"INSERT INTO {table} VALUES ('{name}', {activity}, '{tg_inf_type}', '{a}', '{b}')"
        cursor.execute(command)
        connection.commit()
    except sqlite3.IntegrityError as e:
        # TODO вызывать подсказку о том, что материал уже существует и сделать так, что бы не добавлялось сырье в список
        print(e)
        pass

    connection.close()


def add_tg_base(epoxy: str, amine: str, tg: float) -> None:

    try:
        connection = sqlite3.connect('material.db')
        cursor = connection.cursor()
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




























