"""Solve word search puzzles."""


from __future__ import annotations

import argparse
import enum
import dataclasses

class Direction(enum.IntEnum):
    RIGHT = enum.auto()
    BOTTOM = enum.auto()
    LEFT = enum.auto()
    TOP = enum.auto()
    BOTTOMRIGHT = enum.auto()
    BOTTOMLEFT = enum.auto()
    TOPRIGHT = enum.auto()
    TOPLEFT = enum.auto()


DIRECTION_DELTAS: Dict[Direction, Tuple[int, int]] = {
    Direction.RIGHT: (0, 1),
    Direction.LEFT: (0, -1),
    Direction.BOTTOM: (1, 0),
    Direction.TOP: (-1, 0),
    Direction.BOTTOMRIGHT: (1, 1),
    Direction.BOTTOMLEFT: (1, -1),
    Direction.TOPRIGHT: (-1, 1),
    Direction.TOPLEFT: (-1, -1),
}


DEFAULT_MASK_CHAR = "\u2588"   # full block


def reverse_lines(lines: List[str]) -> List[str]:
    return [line[::-1] for line in lines]


@dataclasses.dataclass
class WordPosition:
    row: int
    column: int
    direction: Direction


    def cells(self, length: int) -> List[Tuple[int, int]]:
        row_delta, column_delta = DIRECTION_DELTAS[self.direction]
        return [
            (self.row + i * row_delta, self.column + i * column_delta)
            for i in range(length)
        ]


@dataclasses.dataclass
class Solution:
    field: SearchField
    word_positions: Dict[str, Optional[WordPosition]]

    def remaining_text(self) -> str:
        return "".join(
            char
            for text_row, mask_row in zip(self.field.lines, self.array_mask())
            for char, mask_flag in zip(text_row, mask_row)
            if not mask_flag
        )

    def array_mask(self) -> List[List[bool]]:
        mask = [[False for i in range(self.field.width)] for j in range(self.field.height)]
        for word, position in self.word_positions.items():
            if position is not None:
                for row, col in position.cells(len(word)):
                    mask[row][col] = True
        return mask

    def string_mask(
        self,
        found_char: str = DEFAULT_MASK_CHAR,
        remaining_char: str = " ",
    ) -> str:
        return "\n".join(
            "".join(found_char if is_found else remaining_char for is_found in row)
            for row in self.array_mask()
        )


class SearchField:
    def __init__(self, lines: List[str]):
        self.width = max(len(line) for line in lines)
        self.lines = [line + "\0" * (self.width - len(line)) for line in lines]
        self._search_registers = None

    def as_text(self, empty_char: str = " ") -> str:
        return "\n".join(self.lines).replace("\0", empty_char)

    @property
    def height(self):
        return len(self.lines)

    def __eq__(self, other) -> bool:
        return self.lines == other.lines

    def _get_search_registers(self) -> Dict[Direction, List[str]]:
        if self._search_registers is None:
            transposed_lines = [
                "".join(line[j] if j < len(line) else "\0" for line in self.lines)
                for j in range(self.width)
            ]
            n_diagonals = self.width + self.height - 1
            bottomright_lines = []
            topright_lines = []
            for diag_i in range(n_diagonals):
                br_i0, br_j0 = self._bottomright_diagonal_start(diag_i)
                tr_i0, tr_j0 = self._topright_diagonal_start(diag_i)
                diag_length = self._diagonal_length(diag_i)
                bottomright_lines.append("".join(self.lines[br_i0+i][br_j0+i] for i in range(diag_length)))
                topright_lines.append("".join(self.lines[tr_i0-i][tr_j0+i] for i in range(diag_length)))
            self._search_registers = {
                Direction.RIGHT: self.lines,
                Direction.LEFT: reverse_lines(self.lines),
                Direction.BOTTOM: transposed_lines,
                Direction.TOP: reverse_lines(transposed_lines),
                Direction.BOTTOMRIGHT: bottomright_lines,
                Direction.TOPLEFT: reverse_lines(bottomright_lines),
                Direction.TOPRIGHT: topright_lines,
                Direction.BOTTOMLEFT: reverse_lines(topright_lines),
            }
        return self._search_registers

    def _diagonal_length(self, diag_i: int) -> int:
        br_i0 = self._bottomright_diagonal_start(diag_i)[0]
        return min(self.height - br_i0, diag_i + 1 - br_i0)

    def _bottomright_diagonal_start(self, diag_i: int) -> Tuple[int, int]:
        d = self.width - 1 - diag_i
        br_i0 = max(-d, 0)
        br_j0 = br_i0 + d
        return br_i0, br_j0

    def _topright_diagonal_start(self, diag_i: int) -> Tuple[int, int]:
        tr_i0 = min(diag_i, self.height - 1)
        tr_j0 = diag_i - tr_i0
        return tr_i0, tr_j0

    @classmethod
    def from_string(
        cls,
        field: str,
        horizontal_spacing: Optional[int] = 0,
        vertical_spacing: Optional[int] = 0,
        empty_characters: str = " ",
    ) -> SearchField:
        for char in empty_characters:
            field = field.replace(char, "\0")
        lines = field.split("\n")
        if horizontal_spacing != 0:
            if horizontal_spacing is None:
                raise NotImplementedError("spacing detection not implemented")
            lines = [line[::(horizontal_spacing + 1)] for line in lines]
        if vertical_spacing != 0:
            if vertical_spacing is None:
                raise NotImplementedError("spacing detection not implemented")
            lines = lines[::(vertical_spacing + 1)]
        return cls(lines)

    def find_words(
        self,
        words: List[str],
        not_found: str = "error",
        multiple_finds: str = "first",
        allowed_directions: Optional[List[Direction]] = None,
    ) -> Dict[str, WordPosition]:
        if multiple_finds != "first":
            raise NotImplementedError("multiple find detection/reconciliation not implemented")
        registers = self._get_search_registers()
        if allowed_directions is None:
            allowed_directions = list(registers.keys())
        finds = {}
        remaining_words = set(words)
        for direction in allowed_directions:
            dir_register = registers[direction]
            for line_i, line in enumerate(dir_register):
                dir_found = set()
                for word in remaining_words:
                    find_i = line.find(word)
                    if find_i != -1:
                        finds[word] = WordPosition(
                            *self._regularize_register_position(direction, line_i, find_i), 
                            direction=direction,
                        )
                        dir_found.add(word)
                remaining_words -= dir_found
        if remaining_words:
            if not_found == "error":
                raise ValueError(f"could not find words: {remaining_words}")
            elif not_found == "keep":
                for w in remaining_words:
                    finds[w] = None
            elif not_found != "ignore":
                raise ValueError(f"invalid not_found argument value: {not_found!r}")
        return finds

    def solve(self, words: List[str], **kwargs) -> Solution:
        return Solution(self, self.find_words(words, **kwargs))

    def _regularize_register_position(
        self,
        direction: Direction,
        line_i: int,
        find_i: int,
    ) -> WordPosition:
        if direction == Direction.RIGHT:
            return line_i, find_i
        elif direction == Direction.LEFT:
            return line_i, self.width - find_i - 1
        elif direction == Direction.BOTTOM:
            return find_i, line_i
        elif direction == Direction.TOP:
            return self.height - find_i - 1, line_i
        elif direction == Direction.BOTTOMRIGHT:
            i0, j0 = self._bottomright_diagonal_start(line_i)
            return i0 + find_i, j0 + find_i
        elif direction == Direction.TOPLEFT:
            i0, j0 = self._bottomright_diagonal_start(line_i)
            diag_length = self._diagonal_length(line_i)
            return i0 + diag_length - find_i - 1, j0 + diag_length - find_i - 1
        elif direction == Direction.TOPRIGHT:
            i0, j0 = self._topright_diagonal_start(line_i)
            return i0 - find_i, j0 + find_i
        elif direction == Direction.BOTTOMLEFT:
            i0, j0 = self._topright_diagonal_start(line_i)
            diag_length = self._diagonal_length(line_i)
            return i0 - diag_length + find_i + 1, j0 + diag_length - find_i - 1
        else:
            raise ValueError(f"invalid direction: {direction!r}")


def read_txt(file_or_str: Any, **kwargs) -> Tuple[SearchField, List[str]]:
    """Read a word search puzzle from a text file.

    The file should first contain a rectangular search field,
    then an empty line, then lines containing whitespace-delimited words to search for.

    Any keyword arguments are passed on to :func:`SearchField.from_string`.

    :param file_or_str: A readable text file-like object or a string-convertible object with the file contents.
    """
    if hasattr(file_or_str, "read"):
        text = file_or_str.read()
    elif not isinstance(file_or_str, str):
        text = str(file_or_str)
    else:
        text = file_or_str
    field_text, word_text = text.rsplit("\n\n", maxsplit=1)
    field = SearchField.from_string(field_text, **kwargs)
    words = word_text.split()
    return field, words


parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("file", help=(
    "text file to read the puzzle from; should first contain a rectangular search field, "
     "then an empty line, then lines containing whitespace-delimited words to search for",
))
parser.add_argument("-e", "--encoding", default="utf8", help="encoding of input file")
parser.add_argument("-H", "--horizontal-spacing", type=int, default=0, help=(
    "horizontal spacing in the search field, i.e. how many meaningless characters separate "
     "each two search field characters on each line"
))
parser.add_argument("-V", "--vertical-spacing", type=int, default=0, help=(
    "vertical spacing in the search field, i.e. how many meaningless lines separate "
    "each two search field lines"
))
parser.add_argument("-m", "--mask-only", action="store_true", help=(
    "only show mask of letters belonging to found words, do not show remaining text"
))
parser.add_argument("-M", "--mask-char", default=DEFAULT_MASK_CHAR, help=(
    "character to use in mask for letters in found words"
))
parser.add_argument("-r", "--remaining-text-only", action="store_true", help=(
    "only show remaining text after removing letters belonging to found words, do not show mask"
))


if __name__ == "__main__":
    args = parser.parse_args()
    with open(args.file, encoding=args.encoding) as infile:
        field, words = read_txt(
            infile,
            horizontal_spacing=args.horizontal_spacing,
            vertical_spacing=args.vertical_spacing
        )
    solution = field.solve(words)
    if not args.remaining_text_only:
        print(solution.string_mask(found_char=args.mask_char))
    if not args.mask_only:
        print(solution.remaining_text())
