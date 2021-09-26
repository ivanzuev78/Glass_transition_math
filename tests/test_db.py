import pytest
from shutil import copyfile
import sqlite3

from res.data_classes import ORMDataBase, DataMaterial
# conn = sqlite3.connect(':memory:')


@pytest.fixture
def data_base():
    db_name = "test_db_run.db"
    copyfile('test_data.db', db_name)

    orm_db = ORMDataBase(db_name)
    yield orm_db


@pytest.fixture
def db_cursor():
    db_name = "test_db_run.db"
    connection = sqlite3.connect(db_name)
    cursor = connection.cursor()
    yield cursor
    cursor.close()

@pytest.fixture
def materials():
    mat_list = []
    mat_list.append(DataMaterial('test', 'my_type', 234))
    mat_list.append(DataMaterial('test2', 'my_type', 42))
    mat_list.append(DataMaterial('test3', 'my_type', 666))
    yield mat_list


def test_add_material(data_base, db_cursor, materials):

    for mat in materials:
        data_base.add_material(mat)
    db_cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
    result = db_cursor.fetchall()
    assert len(result) == 3
    for (name, mat_type, ew, db_id), material in zip(result, materials):
        assert material.name == name
        assert material.mat_type == mat_type
        assert material.ew == ew


def test_remove_material(data_base, db_cursor, materials):

    # Предполагается, что функция add_material работает правильно
    for db_id, mat in enumerate(materials, start=1):
        mat.db_id = db_id
        data_base.add_material(mat)

    for mat in materials:
        data_base.remove_material(mat)

    db_cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
    result = db_cursor.fetchall()
    assert len(result) == 0
