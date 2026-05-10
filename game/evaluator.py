import sys
import importlib.util
import traceback
from game import Game

def capitalize_first_letter(s):
    return s[0].upper() + s[1:] if s else s

def comparePlayers(player1_class, player2_class):
    scores = [0, 0, 0]
    
    repeats = 1000

    for t in range(repeats):
        player1 = player1_class("")
        player2 = player2_class("")
        game = Game([player1, player2], log = False)
        
        while True:
            valid, player = game.takeTurn(log = False)
            if game.moves[0] > 100 or game.moves[1] > 100:
                scores[1] += 1
                if (game.player_cards[0] < game.player_cards[1]):
                    scores[0] += 1
                if (game.player_cards[0] > game.player_cards[1]):
                    scores[2] += 1
                break
            if not valid:
                scores[2-player*2] += 1
                break
            if game.isFinished(log = False):
                scores[player*2] += 1
                break
            
    return scores

def loadPlayer(path):
    spec = importlib.util.spec_from_file_location(
        "agent_module",
        path
    )

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    simpleName = capitalize_first_letter(path.split("/")[-1].split(".")[0])
    if not hasattr(module, simpleName):
        raise Exception(f"Expected class named {simpleName} in {path}")
    return getattr(module, simpleName)

try:
    player1_class = loadPlayer(sys.argv[1])
    player2_class = loadPlayer(sys.argv[2])

    score = comparePlayers(player1_class, player2_class)

    print(score[0] - score[2])
except Exception:
    print(traceback.format_exc())
    sys.exit(1)