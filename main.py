from libs import game_lib

import argparse

parser = argparse.ArgumentParser(
    prog="FantasticPhysics",
)
parser.add_argument("-load")
args = vars(parser.parse_args())

game = game_lib.Game()

if args["load"]:
    game.load_from_file(args["load"])

game.loop()

# MOST IMPORTANT
# todo: add molecule saving
# todo: make text widgets use their own fonts

# todo: rebuild widget system
#   todo: add size with draw surface in ask_for_draw()

# todo: change options_lib.py for better performance
# todo: update trimers.json document using trimers.txt
# todo: add extra quick mode
# todo: add all formulas to physics_lib.py

# todo: add molecule constructor
# todo: add documentation to game
# todo: add more details to energy meter
# todo: add pressure calculation

# todo: add overviews
#   todo: add temperature overview
#   todo: add pressure overview

# todo: add simulation options
#   todo: add gravity chooser

# todo: add in-game options menu
#   todo: add controls menu

# todo: add in-game calculator
#   todo: add energy calculator
#   todo: add dimer and trimer calculator

# todo: add console system
#   todo: make a basic programming language

# todo: remake document_lib.py and change surfaces to widget items
#   todo: change power and index in documentation for better visuals
#   todo: add numerical ratio document item
#   todo: add table document item
#   todo: add plain text document
#   todo: add link item

#   todo: update documents
#       todo: make a new file for phi values
#       todo: make a new file for trimer stability table
