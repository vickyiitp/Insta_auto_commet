import sys
sys.stdout.reconfigure(encoding='utf-8')
import logging
from pathlib import Path

# Setup simple stdout logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Ensure imports work
sys.path.insert(0, str(Path(__file__).parent / "comment_launcher"))

from app.automation import InstagramAutomation

def on_status(msg):
    print(f"STATUS: {msg}")

def on_error(msg):
    print(f"ERROR: {msg}")

def on_progress(c, t):
    print(f"PROGRESS: {c}/{t}")

def on_complete():
    print("COMPLETE")

comments = [
    "This is a test comment 1. Let's connect!",
    "This is a test comment 2. Let's connect!",
    "This is a test comment 3. Let's connect!",
    "This is a test comment 4. Let's connect!",
    "This is a test comment 5. Let's connect!"
]

data_dir = Path("comment_launcher/data")

auto = InstagramAutomation(
    data_dir=data_dir,
    on_status=on_status,
    on_error=on_error,
    on_progress=on_progress,
    on_complete=on_complete
)

idx = [0]
def get_next():
    i = idx[0]
    idx[0] += 1
    if idx[0] >= len(comments):
        idx[0] = 0
    return i, comments[i]

# Run it directly blocking
auto._run_automation(comments, num_reels=5, delay_min=3.0, delay_max=6.0, get_next_comment=get_next)
