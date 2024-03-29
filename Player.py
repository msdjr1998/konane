import telnetlib
import copy
from Board import *

# Feature coefficients
# number of pieces someone control
num_pieces_ratio = 1
# number of moves that can be made
num_moves_us, num_moves_op = 1, 1
# number of "locked" pieces, pieces that can't be moved (no neighbors)
num_lock_us, num_lock_op = 1, 1
# number of pieces that are isolated (have no neighbors, including diagonals)
num_iso_us, num_iso_op = 1, 1

# Not currently implemented
# we had opening move 1: center
op_move_center = 1
# we had opening move 1: corner
op_move_corner = 1


# format a Move() or a tuple to send to the server
def server_format(move):
    if isinstance(move, Move):
        return "[" + str(move.src[0]) + ":" + str(move.src[1]) + "]:[" + str(move.dst[0]) + ":" + str(move.dst[1]) + "]"
    else:
        return "[" + str(move[0]) + ":" + str(move[1]) + "]"


# Parses a move out of a server message
# If line has a Remove message, return a tuple
# If line has a Moved message, return a Move()
def move_parser(line):
    # If there are more than one bracket groups (ex: []:[]), recursively call the function
    if line.count("]") > 1:
        target1 = line[line.index("["):line.index("]") + 1]
        target2 = line[line.index("]:[") + 2:]
        return Move(move_parser(target1), move_parser(target2))
    else:
        target_piece = line[line.index("[") + 1:]
        target_piece = target_piece[0:target_piece.index("]")]
        return tuple([int(x) for x in target_piece.split(":")])


class Player:
    def __init__(self):
        # player = 0 -> black, player = 1 -> white
        # Black pieces have an even sum of indices
        # White pieces have an odd sum of indices
        self.player = -1
        self.board = Board()
        # states is a list of (score, move, board)
        self.states = []
        # delta = 1 if we won, = -1 if we lost
        self.delta = 0

    def play_game(self):
        # username = input("Username (must be an integer): ").encode('ascii')
        username = b'5781'
        # password = input("Password (must be an integer): ").encode('ascii')
        password = b'0000'
        # opponent = input("Opponent (must be an integer): ").encode('ascii')
        opponent = b'1875'
        EOL = b'\n'

        tn = telnetlib.Telnet("artemis.engr.uconn.edu", "4705")
        tn.read_until(b'?Username:')
        tn.write(username + EOL)
        tn.read_until(b'?Password:')
        tn.write(password + EOL)
        tn.read_until(b'?Opponent:')
        tn.write(opponent + EOL)
        print("Successfully logged in.")

        try:
            while True:
                line = tn.read_until(EOL).decode('ascii')
                print(line)

                if '?Remove:' in line:
                    # Our turn to remove a piece
                    score, move = self.minimax_jump(self.player, self.board, True)
                    # self.states.append((score, move, self.board))
                    self.board.update_board_remove(move)

                    move = server_format(move)
                    tn.write(move.encode('ascii') + EOL)

                elif 'Removed:' in line:
                    # Update the board when the opponent removes a piece
                    opponent_move = move_parser(line)
                    self.board.update_board_remove(opponent_move)

                elif '?Move(' in line:
                    # Our turn to make a move
                    score, move = self.minimax_jump(self.player, self.board)

                    if type(score) is Score:
                        # self.states.append((score, move, self.board))
                        self.states.append(score)

                    self.board.update_board_jump(move)
                    move = server_format(move)

                    tn.write(move.encode('ascii') + EOL)
                    print("Move" + move)
                    # Listen for the server to tell us our move
                    tn.read_until(EOL).decode('ascii')

                elif 'Move[' in line:
                    # Update the board when the opponent makes a move
                    opponent_move = move_parser(line)
                    self.board.update_board_jump(opponent_move)

                elif 'Color:' in line:
                    # Set our color
                    if "BLACK" in line:
                        self.player = 0
                    else:
                        self.player = 1

                elif 'win' in line:
                    print(self.board)
                    if "Opponent wins" in line:
                        self.delta = -1
                    else:
                        self.delta = 1
                    break
                elif 'Error' in line or 'Connection to host lost.' in line:
                    break
        except Exception as e:
            print("connection error: ", e)
            # The server is a little wonky with end game stuff. If delta is -1, we probably lost from timing out
            if self.delta == 0:
                self.delta = -1
        print('closing connection...')
        tn.close()
        self.learn()

    def minimax_jump(self, player, board, opening=False, alpha=float("-inf"), beta=float("inf"), depth=0):
        # We've reached the depth limit, get score of current board setup)
        if depth == 2:
            return (Score(player, board), [])

        # Check if this is an opening move
        if opening:
            moves = board.get_valid_removes(player)
        else:
            moves = board.get_all_valid_moves(player)

        if player == self.player:
            # our turn
            current_best = None
            for m in moves:
                next_board = copy.deepcopy(board)
                if opening:
                    next_board.update_board_remove(m)
                else:
                    next_board.update_board_jump(m)
                value, next_move = self.minimax_jump(abs(player - 1), next_board, False, alpha, beta, depth + 1)

                if value > alpha:
                    alpha = value
                    current_best = next_board.last_move
                if alpha >= beta:
                    return (beta, current_best)
            return (alpha, current_best)
        else:
            # opponent turn
            current_best = None
            for m in moves:
                next_board = copy.deepcopy(board)
                if opening:
                    next_board.update_board_remove(m)
                else:
                    next_board.update_board_jump(m)
                value, next_move = self.minimax_jump(abs(player - 1), next_board, False, alpha, beta, depth + 1)

                if value < beta:
                    beta = value
                    current_best = next_board.last_move
                if beta <= alpha:
                    return (alpha, current_best)
            return (beta, current_best)

    def learn(self):
        # iterate through each state
        # look at how the features contributed to the score
        # adjust based on win / lose
        counter = 0
        for i in self.states:
            i.apply_reinforcement(self.delta, counter)
            counter += 1
        print("number of moves: ", len(self.states))
        print(self.delta)


class Score:
    def __init__(self, player, board):
        # number of pieces we control
        self.num_pieces_us_val = 0
        # number of pieces opponent controls
        self.num_pieces_op_val = 0
        # number of moves we can make
        self.num_moves_us_val = 0
        # number of moves opponent can make
        self.num_moves_op_val = 0
        # number of our pieces that are "locked"
        self.num_lock_us_val = 0
        # number of opponent pieces that are "locked"
        self.num_lock_op_val = 0
        # number of our pieces that are isolated
        self.num_iso_us_val = 0
        # number of opponent pieces that are isolated
        self.num_iso_op_val = 0

        self.compute_scores(player, board)
        self.total = self.total()

    def __lt__(self, other):
        return self.total < other

    def __le__(self, other):
        return self.total <= other

    def __gt__(self, other):
        return self.total > other

    def __ge__(self, other):
        return self.total >= other

    def __eq__(self, other):
        return self.total == other

    def __repr__(self):
        return str(self.total)

    def total(self):
        return (self.num_pieces_us_val / self.num_pieces_op_val * num_pieces_ratio) \
               * ((self.num_moves_us_val * num_moves_us) - (self.num_moves_op_val * num_moves_op)
                  - (num_lock_us * self.num_lock_us_val) + (num_lock_op * self.num_lock_op_val)
                  - (num_iso_us * self.num_iso_us_val) + (num_iso_op * self.num_iso_op_val))

    def compute_scores(self, player, board):
        col, row = np.where(board.board == 1)
        for i in range(len(col)):
            is_locked = True
            is_isolated = True

            neighbors = board.board[col[i] - 1:col[i] + 2, row[i] - 1:row[i] + 2]
            for c, r in np.ndindex(neighbors.shape):
                if c != 1 and r != 1:
                    if neighbors[c, r] == 1:
                        is_isolated = False
                        if (r + c) % 2 == 1:
                            is_locked = False
                            break

            if (col[i] + row[i]) % 2 == player:
                self.num_pieces_us_val += 1
                if is_locked:
                    self.num_lock_us_val += 1
                if is_isolated:
                    self.num_iso_us_val += 1
            else:
                self.num_pieces_op_val += 1
                if is_locked:
                    self.num_lock_op_val += 1
                if is_isolated:
                    self.num_iso_op_val += 1

            if board.possible_moves_black != -1 and player == 0:
                self.num_moves_us_val = board.possible_moves_black
            elif board.possible_moves_black != -1 and player == 1:
                self.num_moves_us_val = board.possible_moves_white
            else:
                self.num_moves_us_val = len(board.get_all_valid_moves(player))
            if board.possible_moves_black != -1 and player != 0:
                self.num_moves_op_val = board.possible_moves_black
            elif board.possible_moves_black != -1 and player != 1:
                self.num_moves_op_val = board.possible_moves_white
            else:
                self.num_moves_op_val = len(board.get_all_valid_moves(player))
        self.num_lock_us_val /= 10
        self.num_lock_op_val /= 10

    def apply_reinforcement(self, delta, counter):
        global num_pieces_ratio
        global num_moves_us
        global num_lock_us
        global num_iso_us
        global num_moves_op
        global num_lock_op
        global num_iso_op

        discount = (0.95**counter) * delta

        num_pieces_ratio += (discount * self.num_pieces_us_val / self.num_pieces_op_val)

        num_lock_us += 0.15 * discount * self.num_lock_us_val
        num_iso_us += 0.15 * discount * self.num_iso_us_val
        num_moves_us += 0.15 * discount * self.num_moves_us_val
        num_lock_op -= 0.15 * discount * self.num_lock_us_val
        num_iso_op -= 0.15 * discount * self.num_iso_op_val
        num_moves_op -= 0.15 * discount * self.num_moves_us_val

        if self.num_lock_us_val > self.num_iso_us_val and self.num_lock_us_val > self.num_moves_us_val:
            num_lock_us += 0.3 * discount
        elif self.num_iso_us_val > self.num_lock_us_val and self.num_iso_us_val > self.num_moves_us_val:
            num_iso_us += 0.3 * discount
        elif self.num_moves_us_val > self.num_iso_us_val and self.num_moves_us_val > self.num_lock_us_val:
            num_moves_us += 0.3 * discount

        if self.num_lock_op_val > self.num_iso_op_val and self.num_lock_op_val > self.num_moves_op_val:
            num_lock_op -= 0.3 * discount
        elif self.num_iso_op_val > self.num_lock_op_val and self.num_iso_op_val > self.num_moves_op_val:
            num_iso_op -= 0.3 * discount
        elif self.num_moves_op_val > self.num_iso_op_val and self.num_moves_op_val > self.num_lock_op_val:
            num_moves_op -= 0.3 * discount

        self.print_values(delta)

    def print_values(self, delta):
        print("                 Score   Altered Coefficients")
        print("num pieces ratio:", round(self.num_pieces_us_val / self.num_pieces_us_val, 3), "   ", num_pieces_ratio)
        print("num moves us:     ", round(self.num_moves_us_val, 3), "   ", num_moves_us)
        print("num moves op:     ", round(self.num_moves_op_val, 3), "   ", num_moves_op)
        print("num lock us:     ", round(self.num_lock_us_val, 3), "   ", num_lock_us)
        print("num lock op:     ", round(self.num_lock_op_val, 3), "   ", num_lock_op)
        print("num iso us:      ", round(self.num_iso_us_val, 3), "   ", num_iso_us)
        print("num iso op:      ", round(self.num_iso_op_val, 3), "   ", num_iso_op)
        print("_________________________")


p = Player()
p.play_game()
