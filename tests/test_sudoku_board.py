import unittest

from sudoku.sudoku_board import SudokuBoard


class TestValidLocation(unittest.TestCase):
    def test_is_valid_location_small(self):
        board = SudokuBoard(3, "seed", [[1, 2, 3], [3, 0, 0], [2, 3, 1]])
        self.assertTrue(board._is_valid_location(1, 1, 1))
        self.assertFalse(board._is_valid_location(1, 1, 3))
        self.assertFalse(board._is_valid_location(1, 1, 2))
        self.assertFalse(board._is_valid_location(1, 1, 10))
        self.assertFalse(board._is_valid_location(1, 1, 4))

    def test_is_valid_location_9_by_9(self):
        board = SudokuBoard(
            9,
            "seed",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9],
                [4, 0, 6, 0, 0, 0, 0, 0, 0],
                [7, 8, 9, 0, 0, 0, 0, 0, 0],
            ]
            + [[0 for _ in range(9)] for _ in range(6)],
        )
        self.assertTrue(board._is_valid_location(1, 1, 5))  # In a box
        self.assertFalse(board._is_valid_location(1, 1, 1))  # Box invalid
        self.assertFalse(board._is_valid_location(4, 6, 7))  # Column invalid
        self.assertFalse(board._is_valid_location(1, 6, 4))  # Row invalid

    def test_is_valid_location_8_by_8(self):
        board = SudokuBoard(
            8,
            "seed",
            [
                [1, 2, 3, 4, 5, 6, 7, 8],
                [5, 0, 6, 0, 0, 0, 0, 0],
                [7, 8, 0, 0, 0, 0, 0, 0],
            ]
            + [[0 for _ in range(8)] for _ in range(5)],
        )
        self.assertTrue(board._is_valid_location(1, 1, 7))
        self.assertFalse(board._is_valid_location(1, 1, 4))  # 2 row x 4 col box invalid
        self.assertFalse(board._is_valid_location(1, 6, 7))  # Column
        self.assertFalse(board._is_valid_location(1, 6, 6))  # Row
        self.assertFalse(board._is_valid_location(1, 6, 8))  # Box 2


class TestBoxSize(unittest.TestCase):
    def test_box_size(self):
        board = SudokuBoard(9, "seed")
        self.assertEqual(board._get_box_size(), (3, 3))
        board = SudokuBoard(8, "seed")
        self.assertEqual(board._get_box_size(), (2, 4))
        board = SudokuBoard(16, "seed")
        self.assertEqual(board._get_box_size(), (4, 4))
        board = SudokuBoard(143, "seed")
        self.assertEqual(board._get_box_size(), (11, 13))


class TestGenerate(unittest.TestCase):
    def test_valid(self):
        board = SudokuBoard(
            4, "seed", [[1, 4, 2, 3], [2, 3, 1, 4], [4, 2, 3, 1], [3, 1, 4, 2]]
        )
        self.assertTrue(board.valid)
        board = SudokuBoard(
            4, "seed", [[1, 2, 3, 4], [2, 3, 4, 1], [2, 4, 3, 1], [4, 1, 2, 3]]
        )
        self.assertFalse(board.valid)
        board = SudokuBoard(
            4, "seed", [[1, 4, 2, 3], [2, 3, 1, 4], [4, 2, 3, 1], [3, 1, 4, 0]]
        )
        self.assertTrue(board.valid)

    def test_solved(self):
        board = SudokuBoard(
            4, "seed", [[1, 4, 2, 3], [2, 3, 1, 4], [4, 2, 3, 1], [3, 1, 4, 2]]
        )
        self.assertTrue(board.solved)
        board = SudokuBoard(
            4, "seed", [[1, 2, 3, 4], [2, 3, 4, 1], [2, 4, 3, 1], [4, 1, 2, 3]]
        )
        self.assertFalse(board.solved)
        board = SudokuBoard(
            4, "seed", [[1, 4, 2, 3], [2, 3, 1, 4], [4, 2, 3, 1], [3, 1, 4, 0]]
        )
        self.assertFalse(board.solved)

    def test_generate_solved(self):
        board = SudokuBoard(4, "seed")
        self.assertTrue(board.valid)
        self.assertTrue(board.solved)
        self.assertEqual(len(board.board), 4)
        self.assertEqual(len(board.board[0]), 4)
        board = SudokuBoard(6, "seed")
        self.assertTrue(board.solved)
        self.assertEqual(len(board.board), 6)
        self.assertEqual(len(board.board[0]), 6)


class TestOtherIsValid(unittest.TestCase):
    def test_empty_board(self):
        board = SudokuBoard(
            4, "seed", [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]
        )
        self.assertTrue(
            board.is_valid_solution(SudokuBoard(4, "iosdjfiosdjiojfiosjoi"))
        )

    def test_some_removed(self):
        board = SudokuBoard(4, "seed")
        board.hide_squares(10)
        self.assertTrue(board.is_valid_solution(SudokuBoard(4, "seed")))

    def test_some_removed_invalid(self):
        board = SudokuBoard(4, "seed")
        board.hide_squares(10)
        self.assertFalse(board.is_valid_solution(SudokuBoard(4, "seedfsdf")))
