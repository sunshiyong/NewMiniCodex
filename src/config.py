"""配置管理"""
import os
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("请设置 DEEPSEEK_API_KEY")

BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")
MODEL_FALLBACK = "deepseek-chat"

ROOT_DIR = Path(__file__).parent.parent
SANDBOX_DIR = ROOT_DIR / "sandbox"
SANDBOX_DIR.mkdir(exist_ok=True)

MAX_STEPS = 10
STUCK_LIMIT = 3
CONTEXT_LIMIT = 80000
RESULT_TRUNCATE = 2000
