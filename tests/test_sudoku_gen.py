from unittest import TestCase

from sudoku.sudoku_gen import SudokuGenerator


class TestSudokuGen(TestCase):
    def test_get_n_and_num_squares(self):
        # TODO: More tests probably
        s = SudokuGenerator(25, "seed")
        n, num_squares_hidden = s._get_n_and_num_squares()
        self.assertEqual(n, 6)
        self.assertEqual(num_squares_hidden, 14)

    def test_encoding(self):
        s = SudokuGenerator(678192, "seed")
        board1 = s.generate_board()
        board2 = SudokuGenerator.decode(s.encode()).generate_board()
        self.assertEqual(board1.__str__(), board2.__str__())