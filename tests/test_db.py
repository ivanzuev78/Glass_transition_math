import pytest
from shutil import copyfile
import sqlite3

from res.data_classes import ORMDataBase, DataMaterial, DataGlass, Profile, CorrectionFunction, Correction


# conn = sqlite3.connect(':memory:')


@pytest.fixture
def orm_db():
    db_name = "test_db_run.db"
    copyfile("test_data.db", db_name)

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
    mat_list.append(DataMaterial("test", "my_type", 234, db_id=1))
    mat_list.append(DataMaterial("test2", "my_type", 42, db_id=2))
    mat_list.append(DataMaterial("test3", "my_type", 666, db_id=3))
    return mat_list


@pytest.fixture
def added_materials(orm_db, materials):
    for mat in materials:
        orm_db.add_material(mat)
    return materials


@pytest.fixture
def correction_funcs():
    cor_list = []
    cor_list.append(CorrectionFunction("test", "comment", polynomial_coefficients=[34, 0, 0, 0, 28], db_id=1))
    cor_list.append(CorrectionFunction("test1", "comment", polynomial_coefficients=[34, 0, 0], db_id=2))
    cor_list.append(CorrectionFunction("test2", "comment", db_id=3))
    return cor_list


@pytest.fixture
def added_correction_funcs(orm_db, correction_funcs):
    for cor in correction_funcs:
        orm_db.add_correction_func(cor)
    return correction_funcs


@pytest.fixture
def tg_list(materials):
    tg_list = []
    tg_list.append(DataGlass(materials[0], materials[1], 100))
    tg_list.append(DataGlass(materials[0], materials[2], 200))
    tg_list.append(DataGlass(materials[1], materials[2], 300))
    return tg_list


@pytest.fixture
def added_tg_list(orm_db, tg_list):
    for data_glass in tg_list:
        orm_db.add_tg(data_glass)
    return tg_list


@pytest.fixture
def profiles(orm_db):
    profile_list = []
    profile_list.append(Profile('name 1', orm_db))
    profile_list.append(Profile('name 2', orm_db))
    profile_list.append(Profile('name 3', orm_db))
    return profile_list


@pytest.fixture
def added_profiles(orm_db, profiles):
    names_list = [prof.profile_name for prof in profiles]
    for name in names_list:
        orm_db.add_profile(name)
    return profiles


@pytest.fixture
def corrections(added_materials, added_correction_funcs):
    cor_list = []
    cor_list.append(Correction(0, 20, added_correction_funcs[0], added_materials[0], added_materials[2]))
    cor_list.append(Correction(0, 15, added_correction_funcs[1], added_materials[1], added_materials[2]))
    cor_list.append(Correction(0, 10, added_correction_funcs[2]))
    return cor_list


@pytest.fixture
def added_corrections(orm_db, corrections):
    for correction in corrections:
        orm_db.add_correction(correction)
    return corrections


def test_add_material(orm_db, db_cursor, materials):
    for mat in materials:
        orm_db.add_material(mat)
    db_cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
    result = db_cursor.fetchall()
    assert len(result) == len(materials)
    for (name, mat_type, ew, db_id), material in zip(result, materials):
        assert material.name == name
        assert material.mat_type == mat_type
        assert material.ew == ew

    # Проверяем, что материалы не будут дублироваться
    for mat in materials:
        orm_db.add_material(mat)
    db_cursor.execute(f"SELECT Name, Type, ew, id  FROM Materials")
    result = db_cursor.fetchall()
    assert len(result) == len(materials)


def test_remove_material(orm_db, db_cursor, materials):
    # Предполагается, что функция add_material работает правильно
    for db_id, mat in enumerate(materials, start=1):
        mat.db_id = db_id
        orm_db.add_material(mat)

    for mat in materials:
        orm_db.remove_material(mat)

    db_cursor.execute(f"SELECT * FROM Materials")
    result = db_cursor.fetchall()
    assert len(result) == 0


def test_add_correction_funcs(orm_db, db_cursor, correction_funcs):
    all_poly_coef = []
    for cor in correction_funcs:
        orm_db.add_correction_func(cor)
        for power, value in enumerate(cor.polynomial_coefficients):
            if value > 0:
                all_poly_coef.append((power, value))

    db_cursor.execute(f"SELECT * FROM Correction_funcs")
    result = db_cursor.fetchall()
    assert len(result) == len(correction_funcs)
    for (cor_id, name, comment, k_e, k_exp), cor in zip(result, correction_funcs):
        cor: CorrectionFunction
        assert cor.name == name
        assert cor.comment == comment
        assert cor.k_e == k_e
        assert cor.k_exp == k_exp

    db_cursor.execute(f"SELECT * FROM corr_poly_coef_map")
    result = db_cursor.fetchall()
    for cor_id, power, value in result:
        assert (power, value) in all_poly_coef
        all_poly_coef.remove((power, value))

    assert len(all_poly_coef) == 0


def test_remove_correction_funcs(orm_db, db_cursor, correction_funcs):
    # Предполагается, что функция add_correction работает правильно
    for cor in correction_funcs:
        orm_db.add_correction_func(cor)

    for cor in correction_funcs:
        orm_db.remove_correction_func(cor)

    db_cursor.execute(f"SELECT * FROM Correction_funcs")
    result = db_cursor.fetchall()
    assert len(result) == 0

    db_cursor.execute(f"SELECT * FROM corr_poly_coef_map")
    result = db_cursor.fetchall()
    assert len(result) == 0


def test_add_tg(orm_db, db_cursor, tg_list):
    for data_glass in tg_list:
        orm_db.add_tg(data_glass)

    db_cursor.execute(f"SELECT * FROM Tg")
    result = db_cursor.fetchall()
    assert len(result) == len(tg_list)
    for (tg_id, epoxy, amine, value), data_glass in zip(result, tg_list):
        data_glass: DataGlass
        assert tg_id == data_glass.db_id
        assert epoxy == data_glass.epoxy.db_id
        assert amine == data_glass.amine.db_id
        assert value == data_glass.value


def test_remove_tg(orm_db, db_cursor, tg_list):
    for data_glass in tg_list:
        orm_db.add_tg(data_glass)

    for data_glass in tg_list:
        orm_db.remove_tg(data_glass)

    db_cursor.execute(f"SELECT * FROM Tg")
    result = db_cursor.fetchall()
    assert len(result) == 0


def test_add_profile(orm_db, db_cursor, profiles):
    names_list = [prof.profile_name for prof in profiles]
    for name in names_list:
        orm_db.add_profile(name)
    db_cursor.execute(f"SELECT * FROM Profiles")
    result = db_cursor.fetchall()
    assert len(result) == len(names_list)
    for db_name, test_name in zip(result, names_list):
        assert db_name[0] == test_name


def test_remove_profile(orm_db, db_cursor, profiles, materials):
    names_list = [prof.profile_name for prof in profiles]
    for name in names_list:
        orm_db.add_profile(name)

    for name in names_list:
        orm_db.remove_profile(name)

    db_cursor.execute(f"SELECT * FROM Profiles")
    result = db_cursor.fetchall()
    assert len(result) == 0


def test_add_material_to_profile(orm_db, db_cursor, added_materials, added_profiles):
    for mat in added_materials:
        for profile in added_profiles:
            orm_db.add_material_to_profile(mat, profile)

    db_cursor.execute(f"SELECT * FROM Prof_mat_map")
    result = db_cursor.fetchall()

    assert len(result) == len(added_materials) * len(added_profiles)

    # Проверяем, что материалы не будут дублироваться в профиле
    for mat in added_materials:
        for profile in added_profiles:
            orm_db.add_material_to_profile(mat, profile)
    db_cursor.execute(f"SELECT * FROM Prof_mat_map")
    result = db_cursor.fetchall()
    assert len(result) == len(added_materials) * len(added_profiles)


def test_remove_material_from_profile(orm_db, db_cursor, added_materials, added_profiles):
    for mat in added_materials:
        for profile in added_profiles:
            orm_db.add_material_to_profile(mat, profile)

    profile_to_remove_from = added_profiles[0]
    for mat in added_materials:
        orm_db.remove_material_from_profile(mat, profile_to_remove_from)

    db_cursor.execute(f"SELECT * FROM Prof_mat_map")
    result = db_cursor.fetchall()
    assert len(result) == len(added_materials) * (len(added_profiles) - 1)


def test_add_correction(orm_db, db_cursor, corrections):
    for correction in corrections:
        orm_db.add_correction(correction)

    db_cursor.execute(f"SELECT * FROM Correction_map")
    result = db_cursor.fetchall()
    assert len(result) == len(corrections)

    for cor_data, correction in zip(result, corrections):
        cor_id, amine, epoxy, x_min, x_max, cor_func = cor_data
        amine_in_cor = correction.amine.db_id if isinstance(correction.amine, DataMaterial) else correction.amine
        epoxy_in_cor = correction.epoxy.db_id if isinstance(correction.epoxy, DataMaterial) else correction.epoxy
        assert cor_id == correction.db_id
        assert epoxy == epoxy_in_cor
        assert amine == amine_in_cor
        assert x_min == correction.x_min
        assert x_max == correction.x_max
        assert cor_func == correction.correction_func.db_id


def test_remove_correction(orm_db, db_cursor, added_corrections):
    db_cursor.execute(f"SELECT * FROM Correction_map")
    result = db_cursor.fetchall()
    assert len(result) == len(added_corrections)

    for correction in added_corrections:
        orm_db.remove_correction(correction)

    db_cursor.execute(f"SELECT * FROM Correction_map")
    result = db_cursor.fetchall()
    assert len(result) == 0


def test_add_association_material_to_correction(orm_db, db_cursor, added_materials, added_corrections):
    for material, correction in zip(added_materials, added_corrections):
        orm_db.add_association_material_to_correction(material, correction)

    db_cursor.execute(f"SELECT * FROM Mat_cor_map")
    result = db_cursor.fetchall()
    assert len(result) == len(added_corrections)

    for (mat_id, cor_id), material, correction in zip(result, added_materials, added_corrections):
        assert mat_id == material.db_id
        assert cor_id == correction.db_id


def test_remove_association_material_to_correction(orm_db, db_cursor, added_materials, added_corrections):
    for material, correction in zip(added_materials, added_corrections):
        orm_db.add_association_material_to_correction(material, correction)

    db_cursor.execute(f"SELECT * FROM Mat_cor_map")
    result = db_cursor.fetchall()
    assert len(result) == len(added_corrections)

    for material, correction in zip(added_materials, added_corrections):
        orm_db.remove_association_material_to_correction(material, correction)

    db_cursor.execute(f"SELECT * FROM Mat_cor_map")
    result = db_cursor.fetchall()
    assert len(result) == 0
