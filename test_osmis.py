
import pytest

from osmis import SearchField, Solution, Direction, WordPosition, read_txt


def test_small_field_dimensions():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    assert test_field.height == 3
    assert test_field.width == 3


def test_small_search_registers():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    registers = test_field._get_search_registers()

    assert registers == {
        Direction.RIGHT: [
            "GHU",
            "BRQ",
            "HJI",
        ],
        Direction.LEFT: [
            "UHG",
            "QRB",
            "IJH",
        ],
        Direction.BOTTOM: [
            "GBH",
            "HRJ",
            "UQI",
        ],
        Direction.TOP: [
            "HBG",
            "JRH",
            "IQU",
        ],
        Direction.BOTTOMRIGHT: [
            "U",
            "HQ",
            "GRI",
            "BJ",
            "H",
        ],
        Direction.TOPLEFT: [
            "U",
            "QH",
            "IRG",
            "JB",
            "H",
        ],
        Direction.BOTTOMLEFT: [
            "G",
            "HB",
            "URH",
            "QJ",
            "I",
        ],
        Direction.TOPRIGHT: [
            "G",
            "BH",
            "HRU",
            "JQ",
            "I",
        ],
    }



def test_small_field_from_string():
    small_text = "G H U\nB R Q\nH J I"
    small_field = SearchField.from_string(small_text, horizontal_spacing=1)

    assert small_field == SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])
    assert small_field.as_text() == small_text.replace(" ", "")



def test_small_find_words():
    expected_positions = {
        "BRQ": WordPosition(1, 0, Direction.RIGHT),
        "JR": WordPosition(2, 1, Direction.TOP),
        "UQ": WordPosition(0, 2, Direction.BOTTOM),
        "JH": WordPosition(2, 1, Direction.LEFT),
    }
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    found_positions = test_field.find_words(list(expected_positions.keys()))
    assert found_positions == expected_positions


def test_small_field_not_found_error():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    with pytest.raises(ValueError, match=".*not find.*HAM.*"):
        test_field.find_words(["HAM"])


def test_small_field_not_found_keep():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    assert test_field.find_words(["HAM"], not_found="keep") == {"HAM": None}


def test_small_field_not_found_ignore():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])

    assert test_field.find_words(["HAM"], not_found="ignore") == {}


def test_small_solution_mask():
    test_field = SearchField([
        "GHU",
        "BRQ",
        "HJI",
    ])
    test_words = ["BRQ", "JR", "UQ", "JH"]

    solution = test_field.solve(test_words)

    assert solution.array_mask() == [[False, False, True], [True, True, True], [True, True, False]]
    assert solution.string_mask(found_char="X") == "  X\nXXX\nXX "
    assert solution.remaining_text() == "GHI"


def test_bigger():
    test_field = SearchField([
        "RUSZQ",
        "WANAR",
        "XNUVE",
        "DIYFU",
    ])
    test_words = ["VUN", "FUA", "XAS", "EF", "SAE", "SNU"]

    solution = test_field.solve(test_words)

    assert test_field.height == 4
    assert test_field.width == 5
    assert solution.word_positions == {
        "VUN": WordPosition(2, 3, Direction.LEFT),
        "FUA": WordPosition(3, 3, Direction.TOPLEFT),
        "XAS": WordPosition(2, 0, Direction.TOPRIGHT),
        "EF": WordPosition(2, 4, Direction.BOTTOMLEFT),
        "SAE": WordPosition(0, 2, Direction.BOTTOMRIGHT),
        "SNU": WordPosition(0, 2, Direction.BOTTOM),
    }
    assert solution.string_mask(found_char="Q") == "  Q  \n QQQ \nQQQQQ\n   Q "
    assert solution.remaining_text() == "RUZQWRDIYU"

def test_example_file():
    with open("example.txt", encoding="utf8") as infile:
        test_field, test_words = read_txt(infile, horizontal_spacing=1)

    solution = test_field.solve(test_words)

    assert solution.remaining_text() == "TYSEMÁŠTOTAMOJEMUSÍIPOSLEDNÍKORUNU"