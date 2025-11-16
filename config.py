# -*- coding: utf-8 -*-
"""
Zyntalic Configuration
Centralized configuration management for the Zyntalic translator
"""
import os
from pathlib import Path
from typing import Optional

# Base paths
REPO_ROOT = Path(__file__).parent.absolute()
MODELS_DIR = REPO_ROOT / "models"
LEXICON_DIR = REPO_ROOT / "lexicon"
OUTPUTS_DIR = REPO_ROOT / "outputs"
RAW_ANCHORS_DIR = REPO_ROOT / "raw_anchors"

# Ensure directories exist
MODELS_DIR.mkdir(exist_ok=True)
OUTPUTS_DIR.mkdir(exist_ok=True)

# Core Zyntalic parameters
DEFAULT_MIRROR_RATE = 0.8
DEFAULT_TOP_K_ANCHORS = 3
DEFAULT_EMBEDDING_DIM = 300
MAX_TEXT_LENGTH = 200_000

# Available anchors (cultural Schelling points)
ANCHORS = [
    "Homer_Iliad",
    "Homer_Odyssey",
    "Plato_Republic",
    "Aristotle_Organon",
    "Virgil_Aeneid",
    "Dante_DivineComedy",
    "Shakespeare_Sonnets",
    "Goethe_Faust",
    "Cervantes_DonQuixote",
    "Milton_ParadiseLost",
    "Melville_MobyDick",
    "Darwin_OriginOfSpecies",
    "Austen_PridePrejudice",
    "Tolstoy_WarPeace",
    "Dostoevsky_BrothersKaramazov",
    "Laozi_TaoTeChing",
    "Sunzi_ArtOfWar",
    "Descartes_Meditations",
    "Bacon_NovumOrganum",
    "Spinoza_Ethics"
]

# Alphabet components
CHOSEONG = ["ㄱ","ㄲ","ㄴ","ㄷ","ㄸ","ㄹ","ㅁ","ㅂ","ㅃ","ㅅ","ㅆ","ㅇ","ㅈ","ㅉ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]
JUNGSEONG = ["ㅏ","ㅐ","ㅑ","ㅒ","ㅓ","ㅔ","ㅕ","ㅖ","ㅗ","ㅘ","ㅙ","ㅚ","ㅛ","ㅜ","ㅝ","ㅞ","ㅟ","ㅠ","ㅡ","ㅢ","ㅣ"]
JONGSEONG = ["","ㄱ","ㄲ","ㄳ","ㄴ","ㄵ","ㄶ","ㄷ","ㄹ","ㄺ","ㄻ","ㄼ","ㄽ","ㄾ","ㄿ","ㅀ","ㅁ","ㅂ","ㅄ","ㅅ","ㅆ","ㅇ","ㅈ","ㅊ","ㅋ","ㅌ","ㅍ","ㅎ"]

POLISH_CONSONANTS = "bcćdđfghjklłmnńprsśtvwzźż"
POLISH_VOWELS = "aąeęioóuy"

# Web application settings
WEBAPP_HOST = os.getenv("ZYNTALIC_HOST", "0.0.0.0")
WEBAPP_PORT = int(os.getenv("ZYNTALIC_PORT", "8000"))
WEBAPP_DEBUG = os.getenv("ZYNTALIC_DEBUG", "false").lower() == "true"

# Logging configuration
LOG_LEVEL = os.getenv("ZYNTALIC_LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Model settings
MODEL_PATH = MODELS_DIR / "W.npy"
META_PATH = MODELS_DIR / "meta.json"

def get_config() -> dict:
    """Return configuration as dictionary."""
    return {
        "repo_root": str(REPO_ROOT),
        "models_dir": str(MODELS_DIR),
        "lexicon_dir": str(LEXICON_DIR),
        "outputs_dir": str(OUTPUTS_DIR),
        "mirror_rate": DEFAULT_MIRROR_RATE,
        "top_k_anchors": DEFAULT_TOP_K_ANCHORS,
        "embedding_dim": DEFAULT_EMBEDDING_DIM,
        "max_text_length": MAX_TEXT_LENGTH,
        "anchors": ANCHORS,
        "webapp": {
            "host": WEBAPP_HOST,
            "port": WEBAPP_PORT,
            "debug": WEBAPP_DEBUG
        }
    }
