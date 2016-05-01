"""@package docstring
The Hackiest UCI Engine Chess Tournament System

Pit two raspberry pis with serial connections (already logged in to a prompt on the console) against each other
in a battle of the wits!
"""

import chess
import chess.pgn
import ctypes
import datetime
import serial
import time
import logging
import os
import sys
from dateutil.relativedelta import relativedelta

from colorama import init, Fore, Back, Style
init()

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

termwidth = 75  # Width of the terminal display
stopsleep = .1  # How much time to sleep before clearing the buffer after a "stop".  This time is added back to the player's clock
turneytime = 30000  # Move clock in seconds for both players.

# Put the starting position for this match here:
board = chess.Board("rnbqkbnr/pppp1ppp/8/4p3/4PP2/8/PPPP2PP/RNBQKBNR b KQkq - 3 1")

# Configure the two pis here:
chesspi =\
    {
        'white': {
            'friendlyname': 'Stockfish #1',
            'port': 'COM3',
            'engine': 'stockfish',
            'matchstring': 'Stockfish',
            'serial': False,
            'pondermove': False,
        },
        'black': {
            'friendlyname': 'Stockfish #2',
            'port': 'COM4',
            'engine': './stockfish',
            'matchstring': 'Stockfish',
            'serial': False,
            'pondermove': False,
        },
    }

# Clock rules for this match:
clock =\
    {
        'white_time_seconds': turneytime,
        'black_time_seconds': turneytime,
        'move_time_seconds_increment': 0,
        'white_move': True,
    }


def shutdown(msg=''):
    global chesspi
    if msg is not '':
        print Fore.LIGHTRED_EX + "Error: " + msg
    for pi in chesspi:
        if chesspi[pi]['serial'] is False:
            continue
        flush(pi)
        chesspi[pi]['serial'].write("quit\n")
        flush(pi)
    exit(-1)


def send(pi='white', command='uci'):
    global chesspi
    global clock
    global stopsleep
    infogobble(pi)
    if 'position' in command:
        time.sleep(stopsleep)
        chesspi[pi]['serial'].read(chesspi[pi]['serial'].in_waiting)  # Gobble up any remaining output.
    chesspi[pi]['serial'].write(command + "\n")
    echo = infogobble(pi)
    if command is 'stop':
        time.sleep(stopsleep)
        chesspi[pi]['serial'].read(chesspi[pi]['serial'].in_waiting)  # Gobble up any remaining output.
        return
    if command not in echo:
        shutdown("Attempted command '" + command + "' but got invalid response '" + echo + "'")
    logging.debug("Sent: " + command)

##############################
### TODO
### Need a better way to stop pondering. Something that can happily gobble everything.

def infogobble(pi='white'):
    '''Sometimes you just need to get rid of all the superfluous info'''
    while True:
        stuff = recv(pi)
        logging.debug("Infogobble saw: '" + stuff + "'")
        if stuff == '\n':
            # Just trash any empty lines being gobbled.
            continue
        if 'info' not in stuff:
            return stuff


def spinwait(pi='white', watchval='', lines=60):
    """Keep gobbling up output until you see the watchval string in output, then return that one line"""
    while True:
        stuff = recv(pi)
        logging.debug("Spinwaiting saw: " + stuff)
        if watchval in stuff:
            return stuff
        lines -= 1
        if lines == 0:
            shutdown('I was waiting to see ' + watchval + ' but it never showed up.')


def recv(pi='white'):
    global chesspi
    logging.debug("Inwaiting: {} Outwaiting: {}".format(chesspi[pi]['serial'].in_waiting, chesspi[pi]['serial'].out_waiting))
    return chesspi[pi]['serial'].readline()


def flush(pi='white'):
    global chesspi
    chesspi[pi]['serial'].reset_input_buffer()
    chesspi[pi]['serial'].reset_output_buffer()


for pi in chesspi:
    chesspi[pi]['serial'] = serial.Serial(chesspi[pi]['port'], baudrate=115200, timeout=1)
    send(pi, chesspi[pi]['engine'])
    enginename = recv(pi)
    if chesspi[pi]['matchstring'] not in enginename:
        shutdown('Chess engine not responding with expected name.  Returned: ' + enginename)
    send(pi, 'uci')
    spinwait(pi, 'uciok')
    print "UCI OK!"

    send(pi, 'setoption name Hash value 768')
    send(pi, 'isready')
    spinwait(pi, 'readyok')
    print "Chess engine on " + chesspi[pi]['port'] + " initialized with " + chesspi[pi]['engine'] + " engine."

# Now, run the chessboard forward in time!
player = 'white'
while True:
    os.system('cls')
    print Fore.GREEN + "Gamium Bakery Computer Chess Championship Series"
    versus = Fore.CYAN + chesspi['white']['friendlyname'] + ' vs ' + chesspi['black']['friendlyname']
    print versus
    print Fore.YELLOW + "White Clock: {}  Black Clock: {}".\
        format(clock['white_time_seconds'], clock['black_time_seconds'])

    if board.turn:
        print Fore.WHITE + Back.BLACK + "White to move."
        player = 'white'
    else:
        print Fore.BLACK + Back.WHITE + "Black to move."
        player = 'black'
    print Fore.WHITE + Back.BLACK
    print '---------------------------------------------------------------------------'
    print "{} moves in game.".format(board.fullmove_number)
    print "{} half moves since last capture or pawn move.".format(board.halfmove_clock)
    print "{} legal moves available to play.".format(len(board.legal_moves))
    print ""
    print board

    captures = {'white': '', 'black': ''}
    for capture in board.captured_piece_stack:
        if capture is None:
            continue
        else:
            if capture.symbol() == capture.symbol().lower():
                captures['white'] += capture.symbol()
            else:
                captures['black'] += capture.symbol()

    print "Captures: " + captures['white'] + " : " + captures['black']

    if board.is_check():
        print Fore.LIGHTWHITE_EX + Back.RED +\
              "-----------------------------------CHECK!----------------------------------"\
              + Back.RESET + Fore.RESET


    # Check to see if the game is over.
    if board.is_game_over() or board.is_fivefold_repetition() or board.is_seventyfive_moves():
        print "Game is complete."
        break

    # Now, with the fluff out of the way, send the chess board to the engine.
    # Check to see if the other player's move matches this player's pondermove
    if board.move_stack and chesspi[player]['pondermove'] == board.move_stack[-1]:
        # It did!  Let the engine know:
        send(player, 'ponderhit')
    else:
        send(player, 'stop')  # Just in case you're pondering.
        send(player, 'position fen {}'.format(board.fen()))
        send(player, 'go wtime {} winc {} btime {} binc {}'.format(
                clock['white_time_seconds']*100, clock['move_time_seconds_increment']*100,
                clock['black_time_seconds']*100, clock['move_time_seconds_increment']*100
            )
        )

    # Search for bestmove, and time it.
    playermove_start = time.clock()
    playermove = spinwait(player, 'bestmove', int(clock[player + '_time_seconds']) + 1)
    clock[player + '_time_seconds'] -= time.clock() - playermove_start

    playermove = playermove.split()  # bestmove [x1y1] ponder [x2y2]
    board.push(chess.Move.from_uci(playermove[1]))
    chesspi[player]['pondermove'] = playermove[3]

    print board.status()
    print board.move_stack

    send(player, 'position fen {} moves {}'.format(board.fen(), chesspi[player]['pondermove']))
    send(player, 'go ponder')

if board.is_stalemate():
    print "Game ended in stalemate.  DRAW."
    gameresult = "1/2-1/2"

if board.is_insufficient_material():
    print "Game ended due to insufficient material.  DRAW."
    gameresult = "1/2-1/2"

if board.is_fivefold_repetition():
    print "Game ended due to fivefold repetition.  DRAW."
    gameresult = "1/2-1/2"

if board.is_seventyfive_moves():
    print "Game ended due to 75 moves without pawn movement or capture.  DRAW."
    gameresult = "1/2-1/2"

if board.is_checkmate():
    print "Game ended due to checkmate!"
    if board.turn:
        print "Victory goes to Black."
        gameresult = "0-1"
    else:
        print "Victory goes to White."
        gameresult = "1-0"

pgn = chess.pgn.Game.from_board(board)
pgn.headers['Event'] = "Gamium Bakery Computer Chess Championship Series"
pgn.headers['Site']  = "Gamium HQ, Houston, Texas"
pgn.headers['Date']  = datetime.datetime.now()
pgn.headers['White'] = chesspi['white']['friendlyname']
pgn.headers['Black'] = chesspi['black']['friendlyname']
pgn.headers['Result'] = gameresult
print(pgn)

shutdown()
