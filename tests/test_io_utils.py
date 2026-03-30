import pytest

from mech_lab_tools import load_csv


def test_load_csv_basic(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n3,4\n")
    df = load_csv(csv)
    assert list(df.columns) == ["a", "b"]
    assert len(df) == 2
    assert df["a"].tolist() == [1, 3]


def test_load_csv_rename_columns(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("x,y\n1,2\n")
    df = load_csv(csv, rename_columns={"x": "alfa", "y": "beta"})
    assert list(df.columns) == ["alfa", "beta"]


def test_load_csv_required_columns_ok(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b,c\n1,2,3\n")
    df = load_csv(csv, required_columns=["a", "c"])
    assert len(df) == 1


def test_load_csv_required_columns_missing(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n")
    with pytest.raises(ValueError, match="Colonne mancanti"):
        load_csv(csv, required_columns=["a", "z"])


def test_load_csv_raises_on_missing_values(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n3,\n")
    with pytest.raises(ValueError, match="valori mancanti"):
        load_csv(csv)


def test_load_csv_drop_missing(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a,b\n1,2\n3,\n5,6\n")
    df = load_csv(csv, drop_missing=True)
    assert len(df) == 2
    assert df["a"].tolist() == [1, 5]


def test_load_csv_custom_sep_and_decimal(tmp_path):
    csv = tmp_path / "data.csv"
    csv.write_text("a;b\n1,5;2,3\n")
    df = load_csv(csv, sep=";", decimal=",")
    assert df["a"].iloc[0] == pytest.approx(1.5)
    assert df["b"].iloc[0] == pytest.approx(2.3)
