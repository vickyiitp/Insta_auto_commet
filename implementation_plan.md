# Comment Launcher — Implementation Plan

A Windows-first Python 3.10+ desktop app that manages prewritten comment lines and pastes them into the currently focused text field via global hotkeys. **No web automation, no API calls** — only clipboard + keyboard simulation.

## Project Structure

```
e:\vickyiitp\Projects\Instacommetn\comment_launcher\
├─ app/
│  ├─ __init__.py
│  ├─ main.py            # Entrypoint: init, start hotkeys, Tkinter mainloop
│  ├─ hotkeys.py         # pynput global hotkey listener, debounce logic
│  ├─ rotation.py        # Round-robin & shuffle engine with recent window
│  ├─ storage.py         # Load/save comments.json, config.json, usage_log.jsonl
│  ├─ clipboard.py       # Copy to clipboard + simulate Ctrl+V with delay
│  ├─ ui.py              # Tkinter UI: listbox, CRUD, config controls, status
│  └─ tray.py            # System tray icon via pystray
├─ data/
│  ├─ comments.json      # Array of 10 sample comments
│  └─ config.json        # Default config
├─ logs/
│  └─ usage_log.jsonl    # Append-only paste log
├─ requirements.txt
├─ README.md
└─ build.spec            # PyInstaller spec (optional)
```

---

## Proposed Changes

### 1. Data Layer — `storage.py`

#### [NEW] [storage.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/storage.py)

- **`load_comments(path) → list[str]`** — Read `comments.json`, return list. Create file with sample data if missing.
- **`save_comments(path, comments: list[str])`** — Atomic write (write to `.tmp`, then rename).
- **`load_config(path) → dict`** — Read `config.json`, merge with defaults for missing keys.
- **`save_config(path, config: dict)`** — Atomic write.
- **`log_usage(path, index: int)`** — Append `{"timestamp": ISO8601, "index": index}` to `usage_log.jsonl`.
- **`setup_logging(log_dir)`** — Configure `logging` module: console WARNING, file DEBUG with rotation.

#### [NEW] [comments.json](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/data/comments.json)

10 sample comment strings covering generic positive engagement.

#### [NEW] [config.json](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/data/config.json)

```json
{
  "mode": "shuffle",
  "recent_window": 10,
  "hotkeys": {
    "next": "<ctrl>+<shift>+v",
    "prev": "<ctrl>+<shift>+b",
    "open_ui": "<ctrl>+<shift>+o",
    "pause": "<ctrl>+<shift>+p"
  },
  "min_interval_ms": 1200
}
```

> [!NOTE]
> Hotkey strings use pynput's `<modifier>+<key>` format for direct compatibility with `pynput.keyboard.GlobalHotKeys`.

---

### 2. Rotation Engine — `rotation.py`

#### [NEW] [rotation.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/rotation.py)

- **Class `RotationEngine`**:
  - Constructor takes `comments: list[str]`, `mode: str`, `recent_window: int`.
  - Maintains a `collections.deque(maxlen=recent_window)` of recently used indices.
  - **Round-robin**: Internal pointer `_index`, cycles `0..N-1`. Skips indices in the recent window (unless all are in window → fallback to next in sequence).
  - **Shuffle**: Generate a permutation of `[0..N-1]`, iterate through it. When exhausted, reshuffle. Skip indices in recent window with same fallback.
  - **`next() → (int, str)`**: Return next (index, comment).
  - **`prev() → (int, str)`**: Step back one position in history and return.
  - **`reset()`**: Clear history, reset pointer.
  - **`set_mode(mode)`**: Switch mode, regenerate order.
  - **`update_comments(comments)`**: Re-initialize with new comment list.

---

### 3. Clipboard Helper — `clipboard.py`

#### [NEW] [clipboard.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/clipboard.py)

- **`paste_text(text: str, delay_ms: int = 80)`**:
  1. Save current clipboard content (best-effort).
  2. `pyperclip.copy(text)`.
  3. `time.sleep(delay_ms / 1000)`.
  4. Simulate `Ctrl+V` via `pynput.keyboard.Controller`.
  5. Brief pause, then restore original clipboard (best-effort).
- No `Enter` key is sent — user submits manually.

---

### 4. Global Hotkeys — `hotkeys.py`

#### [NEW] [hotkeys.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/hotkeys.py)

- **Class `HotkeyManager`**:
  - Uses `pynput.keyboard.GlobalHotKeys` for cross-window hotkey capture.
  - Registers four hotkeys from config: `next`, `prev`, `open_ui`, `pause`.
  - **Debounce**: Each action ignores re-triggers within 300 ms.
  - **Min interval**: `next`/`prev` respect `min_interval_ms` (soft guard — logs a skip if fired too fast).
  - **Pause toggle**: When paused, `next`/`prev` are no-ops; `pause` and `open_ui` still work.
  - Runs listener in a daemon thread so it doesn't block Tkinter's mainloop.
  - **`start()` / `stop()`** lifecycle methods.

---

### 5. Tkinter UI — `ui.py`

#### [NEW] [ui.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/ui.py)

- **`CommentLauncherUI(tk.Tk)`**:
  - **Comment list**: `Listbox` with scrollbar showing all comments.
  - **CRUD buttons**: Add (dialog), Edit (dialog), Delete (with confirmation).
  - **Mode toggle**: Dropdown or radio for `shuffle` / `round`.
  - **Recent window input**: Spinbox (1–50).
  - **Action buttons**: "Shuffle Now", "Reset Order", "Paste Next".
  - **Status bar**: Current index, last-used timestamp, paused state.
  - **Window behavior**: Starts hidden; shown/hidden via `open_ui` hotkey. Uses `withdraw()`/`deiconify()`.
  - **Persistence**: Comment edits → `save_comments()`. Config edits → `save_config()`.

> [!IMPORTANT]
> The Tkinter mainloop runs on the main thread. Hotkey callbacks use `root.after()` to safely schedule UI updates from the hotkey listener thread.

---

### 6. System Tray — `tray.py`

#### [NEW] [tray.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/tray.py)

- Uses **`pystray`** for system tray icon.
- Menu items: "Show/Hide UI", "Pause/Resume", "Exit".
- Tray icon: generated via `PIL.Image` (simple colored square with "CL" text) — no external icon file needed.
- Runs in a separate daemon thread.

> [!NOTE]
> `pystray` and `Pillow` will be added to `requirements.txt`. The tray is optional — the app works without it if import fails (graceful fallback to just Tkinter).

---

### 7. Main Entrypoint — `main.py`

#### [NEW] [main.py](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/app/main.py)

1. Setup logging.
2. Load config and comments from `data/`.
3. Initialize `RotationEngine`.
4. Create `CommentLauncherUI` (hidden initially).
5. Initialize `HotkeyManager` with callbacks wired to rotation engine + clipboard.
6. Start tray icon (if available).
7. Start `root.mainloop()`.
8. On exit: stop hotkeys, save state, cleanup.

---

### 8. Packaging & Documentation

#### [NEW] [requirements.txt](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/requirements.txt)

```
pynput>=1.7.6
pyperclip>=1.8.2
pystray>=0.19.4
Pillow>=9.0.0
```

#### [NEW] [README.md](file:///e:/vickyiitp/Projects/Instacommetn/comment_launcher/README.md)

- Overview, intended use, safety disclaimer
- Installation: `pip install -r requirements.txt`
- Usage: `python -m app.main` or `python app/main.py`
- Hotkey reference table
- Configuration guide
- Build: `pyinstaller --onefile --noconsole app/main.py --name CommentLauncher`

---

## Open Questions

> [!IMPORTANT]
> **Clipboard restoration**: After pasting, should the app restore the user's original clipboard content? This adds a ~200ms delay but prevents the user from losing clipboard data. **Currently planned: yes, best-effort restore.**

> [!NOTE]
> **System tray dependency**: Adding `pystray` + `Pillow` brings in ~3MB of dependencies. The tray is a nice-to-have. **Currently planned: include with graceful fallback if unavailable.**

---

## Verification Plan

### Automated Tests
1. **Run the app**: `cd comment_launcher && python -m app.main` — verify it starts without errors.
2. **Hotkey test**: Press `Ctrl+Shift+V` with a text editor focused — verify a comment is pasted.
3. **Rotation test**: Press `next` 10+ times — verify no repeats within the recent window.
4. **UI test**: Press `Ctrl+Shift+O` — verify UI appears. Add/edit/delete a comment, verify JSON persistence.

### Manual Verification
- Open Notepad, press the next hotkey repeatedly, verify different comments paste in.
- Toggle pause, verify hotkeys stop working.
- Check `logs/usage_log.jsonl` for correct entries.
