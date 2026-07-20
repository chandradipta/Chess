DIFFICULTY_SETTINGS = {
    "easy": {
        "depth": 8,
        "movetime_ms": 150,
        "uci_options": {"UCI_LimitStrength": True, "UCI_Elo": 1000}
    },
    "medium": {
        "depth": 12,
        "movetime_ms": 400,
        "uci_options": {"UCI_LimitStrength": True, "UCI_Elo": 1500}
    },
    "hard": {
        "depth": 20,
        "movetime_ms": 1200,
        "uci_options": {"UCI_LimitStrength": False}
    }
}