import base64
import math
import random

from blockchain.utils import CompositeNumbers

from .sudoku_board import SudokuBoard

class SudokuGenerator:
    """
    Class to generate a sudoku puzzle given a seed and difficulty

    Attributes:
        <int> difficulty: Difficulty of the puzzle
        <str> seed: Seed to generate the puzzle with

    Public Methods:
        <SudokuBoard> generate_puzzle: Generates the sudoku puzzle
        <str> encode(): Encodes self in base64
        <SudokuGenerator> decode(str): Decodes self from base64
    """

    def __init__(self, difficulty: int, seed: str) -> None:
        self.difficulty = difficulty
        self.seed = seed

    @property
    def n(self):
        """We only generate boards where n is not prime"""
        n = int(math.log(self.difficulty, 3)) if self.difficulty > 1 else 1
        return CompositeNumbers.get_instance().get_nth(n)
    def _get_n_and_num_squares(self):
        """Gets size of board (nxn) and number of squares to keep"""

        # For number of squares shown, we calculate as follows:
        # 1. Calculate the number of squares on the board (n^2)
        # 2. Find at which difficulty n will increase and at which difficulty n last increased
        # 3. Assuming we want to hide anywhere between 4n/5 (hardest) and n/2 (easiest) squares, we scale the difference to that range
        num_squares = self.n ** 2
        last_n_increase = 3**(self.n-2)
        next_n_increase = 3**(self.n-1)
        max_hidden, min_hidden = 4*num_squares//5, num_squares//2

        # Scale difficulty (between last_n and next_n) to range (n/2, 4n/5)
        num_squares_hidden = int((max_hidden - min_hidden)*(self.difficulty-last_n_increase)/(next_n_increase - last_n_increase)+min_hidden)

        return self.n, 0

    def generate_board(self) -> SudokuBoard:
        board = SudokuBoard(self.n, self.seed)
        board.hide_squares(self._get_n_and_num_squares()[1])
        return board

    def encode(self) -> str:
        return base64.b64encode(f"{self.difficulty}:{self.seed}".encode()).decode()

    @classmethod
    def decode(cls, encoded: str) -> "SudokuGenerator":
        difficulty, seed = base64.b64decode(encoded).decode().split(":")
        return cls(int(difficulty), seed)

