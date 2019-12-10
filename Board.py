import numpy as np


# src and dst are tuples with the form (y, x)
class Move:
    def __init__(self, src, dst):
        self.src = src
        self.dst = dst

    def __repr__(self):
        return "(" + str(self.src) + "," + str(self.dst) + ")"

    def get_distance(self):
        return (self.dst[0]-self.src[0], self.dst[1]-self.src[1])


class Board:
    def __init__(self):
        # Black pieces have an even sum of indices
        # White pieces have an odd sum of indices
        self.board = np.ones((18, 18))
        self.last_move = None

    def __repr__(self):
        return str(self.board)

    def is_move_valid(self, move, multi=False):
        distance = move.get_distance()

        if any([abs(x) > 2 for x in distance]):
            # if we are given a multi-move, iterate through it
            middle = tuple(move.src + np.sign(distance))
            next_src = tuple(move.src + (2*np.sign(distance)))
            if self.board[middle] == 1 and self.board[next_src] == 0 and \
                    (multi or self.board[move.src] == 1):
                return self.is_move_valid(Move(next_src, move.dst), True)
            else:
                return False
        else:
            middle = tuple(move.src + np.sign(move.get_distance()))
            # Check if the src has a piece, if the destination is empty, and if the spot in between them has a piece
            if self.board[move.dst] == 0 and self.board[middle] == 1 \
                    and (multi or self.board[move.src] == 1):
                return True
            else:
                return False

    # get all moves *to* (col, row)
    def get_valid_moves_to(self, col, row):
        moves = self.get_vertical_jumps(col, row)
        moves += self.get_vertical_jumps(col, row, -1)
        moves += self.get_horizontal_jumps(col, row)
        moves += self.get_horizontal_jumps(col, row, -1)
        return moves

    def get_vertical_jumps(self, col, row, s=1):
        moves = []
        for col2 in range(0, 8):
            new_index = (col2*2*s)
            if 17 >= new_index >= 0:
                temp_move = Move((new_index, row), (col, row))
                if self.is_move_valid(temp_move):
                    moves.append(temp_move)
            else:
                break
        return moves

    def get_horizontal_jumps(self, col, row, s=1):
        moves = []
        for row2 in range(0, 8):
            new_index = row + (row2*2*-s)
            if 17 >= new_index >= 0:
                temp_move = Move((col, new_index), (col, row))
                if self.is_move_valid(temp_move):
                    moves.append(temp_move)
            else:
                break
        return moves

    # returns a list of tuples
    def get_all_valid_moves(self, player):
        moves = []
        # find all empty spaces
        col, row = np.where(self.board == 0)

        for i in range(len(col)):
            if (col[i] + row[i]) % 2 == player:
                moves += self.get_valid_moves_to(col[i], row[i])
        return moves

    # returns a list of tuples
    def get_valid_removes(self, player):
        if player == -1:
            # We are first, we can remove any one of the following
            moves = [(0, 0), (0, 17), (17, 0), (17, 17), (8, 8), (8, 9), (9, 8), (9, 9)]
        else:
            # We are second, we can only remove pieces adjacent to what our opponent removed
            col, row = np.where(self.board == 0)
            col = col[0]
            row = row[0]
            # Collect list of valid pieces we can remove
            moves = []
            if col - 1 >= 0:
                moves.append((col - 1, row))
            if col + 1 <= 17:
                moves.append((col + 1, row))
            if row - 1 >= 0:
                moves.append((col, row - 1))
            if row + 1 <= 17:
                moves.append((col, row + 1))
        return moves

    # Given a tuple (y,x), clear it from the board
    def update_board_remove(self, piece):
        self.board[piece] = 0
        self.last_move = piece

    # Given a Move(), update the board
    def update_board_jump(self, move):
        distance = move.get_distance()

        # Check and handle multi-jump moves, then single jump moves
        if abs(distance[0]) > 2:
            for i in range(move.src[0], move.dst[0], np.sign(distance[0])):
                self.board[(i, move.src[1])] = 0
        elif abs(distance[1]) > 2:
            for i in range(move.src[1], move.dst[1], np.sign(distance[1])):
                self.board[(move.src[0], i)] = 0
        else:
            jumped_space = (move.src[0] + np.sign(distance[0]), move.src[1] + np.sign(distance[1]))
            self.board[jumped_space] = 0

        # Update source and destination spaces
        self.board[move.src] = 0
        self.board[move.dst] = 1
        self.last_move = move
