from __future__ import annotations

import os
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

APP_CONFIG = {
    'FLASK_ENV': os.getenv('FLASK_ENV', 'development'),
    'PORT': int(os.getenv('PORT', '5000')),
    'HOST': os.getenv('HOST', '0.0.0.0'),
    'DATABASE_PATH': os.getenv('DATABASE_PATH', str(ROOT_DIR / 'data' / 'razor_risk.db')),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
    'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
}
