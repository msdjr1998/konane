import telnetlib
from Board import *


class Player:
    def __init__(self):
        # player = 0 -> black, player = 1 -> white
        # Black pieces have an even sum of indices
        # White pieces have an odd sum of indices
        self.player = -1
        self.board = Board()

    def play_game(self):
        username = b'1285'
        password = b'1285'
        opponent = b'5821'
        EOL = b'\n'

        tn = telnetlib.Telnet("artemis.engr.uconn.edu", "4705")
        tn.read_until(b'?Username:')
        tn.write(username + EOL)
        tn.read_until(b'?Password:')
        tn.write(password + EOL)
        tn.read_until(b'?Opponent:')
        tn.write(opponent + EOL)
        print("Successfully logged in.")

        while True:
            line = tn.read_until(EOL).decode('ascii')
            print(line)

            if '?Remove:' in line:
                # Our turn to remove a piece
                move = self.minimax_remove()
                self.board.update_board_remove(move)

                move = self.server_format(move)
                tn.write(move.encode('ascii') + EOL)

            elif 'Removed:' in line:
                # Update the board when the opponent removes a piece
                opponent_move = self.move_parser(line)
                self.board.update_board_remove(opponent_move)

            elif '?Move(' in line:
                # Our turn to make a move
                move = self.minimax_jump()
                self.board.update_board_jump(move)

                move = self.server_format(move)
                tn.write(move.encode('ascii') + EOL)

                # Listen for the server to tell us our move
                tn.read_until(EOL).decode('ascii')

            elif 'Move[' in line:
                # Update the board when the opponent makes a move
                opponent_move = self.move_parser(line)
                self.board.update_board_jump(opponent_move)

            elif 'Color:' in line:
                color = line[6:]
                if color == "BLACK":
                    self.player = 0
                else:
                    self.player = 1

            elif 'wins' in line:
                break
            elif 'Error' in line or 'Connection to host lost.' in line:
                print("ERROR:" + line)
                break

        print('closing connection')
        tn.close()

    # Parses a move out of a server message
    # If line has a Remove message, return a tuple
    # If line has a Moved message, return a Move()
    def move_parser(self, line):
        # If there are more than one bracket groups (ex: []:[]), recursively call the function
        if line.count("]") > 1:
            target1 = line[line.index("["):line.index("]")+1]
            target2 = line[line.index("]:[")+2:]
            return Move(self.move_parser(target1), self.move_parser(target2))
        else:
            target_piece = line[line.index("[") + 1:]
            target_piece = target_piece[0:target_piece.index("]")]
            return tuple([int(x) for x in target_piece.split(":")])

    #format a Move() or a tuple to send to the server
    def server_format(self, move):
        if isinstance(move, Move):
            return "[" + str(move.src[0]) + ":" + str(move.src[1]) + "]:[" + str(move.dst[0]) + ":" + str(move.dst[1]) + "]"
        else:
            return "[" + str(move[0]) + ":" + str(move[1]) + "]"

    #### TO DO ###
    def minimax_remove(self, alpha=-1, beta=-1, depth=-1):
        moves = self.board.get_valid_removes(self.player)

        # returns a tuple

    #### TO DO ###
    def minimax_jump(self, alpha=-1, beta=-1, depth=-1):
        moves = self.board.get_valid_moves()

        # returns a Move()


p = Player()
#p.play_game()

