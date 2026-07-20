# Difficulty mapping for Stockfish usage and fallbacks
DIFFICULTY_SETTINGS = {
    "easy": {
        "depth": 8,
        "movetime_ms": 150,        # interactive, very quick
        "uci_options": {          # optional Stockfish options (may not be supported in all builds)
            "UCI_LimitStrength": True,
            "UCI_Elo": 1000,      # if supported, the engine will play weaker
            "SkillLevel": 5       # alternative option in some builds
        }
    },
    "medium": {
        "depth": 12,
        "movetime_ms": 400,
        "uci_options": {
            "UCI_LimitStrength": True,
            "UCI_Elo": 1500,
            "SkillLevel": 10
        }
    },
    "hard": {
        "depth": 20,
        "movetime_ms": 1200,
        "uci_options": {
            "UCI_LimitStrength": False,
            # no UCI_Elo so engine plays full strength
        }
    }
}