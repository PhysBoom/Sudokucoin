import base64
import json
import random
from typing import List, Tuple

class SudokuBoardException(Exception):
    pass

class SudokuBoard:
    """
    Simple nxn sudoku board:

    Attributes:
        <int> n: Size of board
        <string> seed: Seed to generate the puzzle with
        <List<List<int>>> board: 2D list of integers representing the board (None by default)

    @Properties:
        <bool> solved: True if the board is solved, False otherwise
        <bool> valid: True if the board is valid, False otherwise

    Public Methods:
        <void> hide_squares(int n): Hides n squares randomly from the board.
        <str> encode(): Encodes the board in base64
        <SudokuBoard> decode(str encoded_board): Decodes the board from base64
        <bool> is_valid_solution(SudokuBoard other): Checks if the other board is a valid solution to this board
    """

    def __init__(self, n: int, seed: str, board: List[List[int]] = None) -> None:
        self.n = n
        self.seed = seed
        self.board = board
        if not self.board:
            self._generate_solved_board()

    @property
    def valid(self) -> bool:
        """Returns True if the board is valid, False otherwise"""
        for row in range(self.n):
            for col in range(self.n):
                if not self._is_valid_location(row, col, self.board[row][col]):
                    return False
        return True

    @property
    def solved(self) -> bool:
        """Returns True if the board is solved, False otherwise"""
        return self.valid and all(0 not in row for row in self.board)

    def __str__(self):
        pretty_board = "\n".join([' '.join(map(str, row)) for row in self.board]) # TODO: Make this prettier
        return f"Sudoku Board of size {self.n}x{self.n} with seed {self.seed}.\n\nBoard:\n\n{pretty_board}"

    def _get_box_size(self) -> Tuple[int, int]:
        """Gets the dimensions of one sudoku box (i.e. if n=9, this returns (3, 3); if n=8 it's (2, 4))"""

        possible_factors = [(i, self.n // i) for i in range(1, int(self.n**0.5)+1) if self.n % i == 0]
        sqrt_n = self.n ** 0.5
        # Find the tuple where the first element is closest (and lower) to sqrt_n
        return min(possible_factors, key=lambda x: abs(x[0] - sqrt_n))

    def _is_valid_location(self, row: int, col: int, number: int) -> bool:
        """Checks if the location is valid"""
        if number == 0:
            return True

        if not 1 <= number <= self.n:
            return False
        # Check row
        for i in range(self.n):
            if self.board[row][i] == number and i != col:
                return False
        # Check column
        for i in range(self.n):
            if self.board[i][col] == number and i != row:
                return False

        # Check box
        box_size = self._get_box_size()
        # Find the top left corner of the box that the row, col is in
        box_horiz_no, box_vert_no = row // box_size[0], col // box_size[1]
        top_left_x, top_left_y = box_horiz_no * box_size[0], box_vert_no * box_size[1]
        for i in range(top_left_x, top_left_x + box_size[0]):
            for j in range(top_left_y, top_left_y + box_size[1]):
                if (i, j) != (row, col) and self.board[i][j] == number:
                    return False
        return True

    def _generate_solved_board(self) -> None:
        """
        Generates the solved board

        Stolen from Stackoverflow.
        """
        r_base, c_base = self._get_box_size()
        random.seed(self.seed)

        def pattern(row: int, col: int) -> int:
            """Returns the pattern for the given row and column"""
            return (c_base * (row%r_base) + row//r_base + col)%self.n

        def shuffle(s):
            return random.sample(s, len(s))

        row_range = range(r_base)
        col_range = range(c_base)
        rows = [ g*r_base + r for g in shuffle(col_range) for r in shuffle(row_range) ]
        cols = [ g*c_base + c for g in shuffle(row_range) for c in shuffle(col_range) ]
        nums = shuffle(range(1, self.n+1))

        self.board = [[nums[pattern(r, c)] for c in cols] for r in rows]

    def hide_squares(self, n: int) -> None:
        random.seed(self.seed)
        if self.n**2 < n:
            raise SudokuBoardException("Cannot hide more squares than are available")
        indices_to_hide = list(range(self.n**2))
        random.shuffle(indices_to_hide)
        for i in range(n):
            index = indices_to_hide[i]
            row = index // self.n
            col = index % self.n
            self.board[row][col] = 0

    def encode(self) -> str:
        json_board = {
            "n": self.n,
            "seed": self.seed,
            "board": self.board,
            "box_size": self._get_box_size()
        }
        return base64.b64encode(json.dumps(json_board).encode()).decode()

    def is_valid_solution(self, other: 'SudokuBoard') -> bool:
        """Checks if the other board is a valid solution to this board"""
        if not other.solved:
            return False
        for row in range(self.n):
            for col in range(self.n):
                if self.board[row][col] != 0 and self.board[row][col] != other.board[row][col]:
                    return False
        return True

    @classmethod
    def decode(cls, encoded_board: str) -> "SudokuBoard":
        json_board = json.loads(base64.b64decode(encoded_board).decode())
        return cls(json_board["n"], json_board["seed"], json_board["board"])






