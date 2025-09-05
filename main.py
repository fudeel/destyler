
"""
HTML/CSS Cleaning Tool — Curses-based Checkbox CLI

Features:
- Arrow-key menu with SPACE to toggle and ENTER to continue
- Remove class="..." (or class='...') from .html/.htm files
- Clear content from .css/.scss files
- Asks for a project path and confirmation before applying changes
- Graceful fallback if curses is unavailable

Windows note:
- Install: pip install windows-curses
"""

import os
import re
import sys
import glob
from pathlib import Path
from typing import List, Tuple, Set, Optional

# --------------------------
# Core file operations
# --------------------------

CLASS_ATTR_PATTERN = re.compile(
    r"""\s*class\s*=\s*(?:
        " [^"]* "      |   # double-quoted
        ' [^']* '      |   # single-quoted
        [^\s>]+            # unquoted (rare but possible in malformed HTML)
    )""",
    re.IGNORECASE | re.VERBOSE,
)

def remove_class_attributes_in_text(html_content: str) -> str:
    """Remove class=... attributes from HTML content."""
    return re.sub(CLASS_ATTR_PATTERN, "", html_content)

def process_html_file(file_path: Path) -> Tuple[bool, str]:
    """Process a single HTML/HTM file to remove class attributes."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        cleaned = remove_class_attributes_in_text(text)
        file_path.write_text(cleaned, encoding="utf-8")
        return True, f"✓ Processed: {file_path}"
    except Exception as e:
        return False, f"✗ Error processing {file_path}: {e}"

def clear_file_content(file_path: Path) -> Tuple[bool, str]:
    """Empty a file."""
    try:
        file_path.write_text("", encoding="utf-8")
        return True, f"✓ Cleared: {file_path}"
    except Exception as e:
        return False, f"✗ Error clearing {file_path}: {e}"

def find_files(root: Path, extensions: List[str]) -> List[Path]:
    """Find files by extension (recursive)."""
    files: List[Path] = []
    for ext in extensions:
        files.extend(Path(root).rglob(f"*.{ext}"))
    # De-dup & sort for stable output
    return sorted(set(files), key=lambda p: str(p).lower())

# --------------------------
# TUI (curses) menu
# --------------------------

MENU_OPTIONS: List[Tuple[str, str, bool]] = [
    (
        "Remove classes from .html files",
        'Removes all class="..." (and class=\'...\') attributes from HTML elements.',
        True,
    ),
    (
        "Clear content from .css and .scss files",
        "Empties all CSS/SCSS files (file contents set to empty).",
        True,
    ),
]

def run_curses_menu() -> Optional[Set[int]]:
    """
    Render a checkbox menu using curses.
    Returns:
        set of selected indices, or None if user cancelled (ESC/Ctrl+C).
    """
    try:
        import curses  # type: ignore
    except ImportError:
        return None  # Signal to use fallback

    selected: Set[int] = set()

    def _menu(stdscr) -> Optional[Set[int]]:
        curses.curs_set(0)  # hide cursor within menu screen
        stdscr.nodelay(False)
        stdscr.keypad(True)

        current = 0
        title = "HTML/CSS CLEANING TOOL"
        help_line = "↑/↓ move • SPACE toggle • ENTER continue • ESC quit"

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Title
            title_str = f" {title} "
            stdscr.addstr(1, max(0, (w - len(title_str)) // 2), title_str, curses.A_BOLD | curses.A_REVERSE)

            # Help
            stdscr.addstr(3, max(0, (w - len(help_line)) // 2), help_line, curses.A_DIM)

            # Options
            start_row = 6
            for i, (name, desc, enabled) in enumerate(MENU_OPTIONS):
                is_cur = (i == current)
                prefix = "[*]" if i in selected else "[ ]"
                status = "" if enabled else " (DISABLED)"
                line = f"  {prefix} {name}{status}"

                attr = curses.A_BOLD if is_cur else curses.A_NORMAL
                stdscr.addstr(start_row + i * 2, 2, line, attr)

                # description
                stdscr.addstr(start_row + i * 2 + 1, 4, desc, curses.A_DIM)

            # Footer
            chosen = [MENU_OPTIONS[i][0] for i in sorted(selected)]
            chosen_line = "Selected: " + (", ".join(chosen) if chosen else "(none)")
            stdscr.addstr(h - 2, 2, chosen_line[: w - 4], curses.A_DIM)

            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(MENU_OPTIONS)
            elif key in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(MENU_OPTIONS)
            elif key in (curses.KEY_ENTER, 10, 13):
                # ENTER
                return selected if selected else set()
            elif key == 27:  # ESC
                return None
            elif key == ord(' '):
                # toggle only if enabled
                if MENU_OPTIONS[current][2]:
                    if current in selected:
                        selected.remove(current)
                    else:
                        selected.add(current)

    try:
        import curses  # type: ignore
        return curses.wrapper(_menu)
    except KeyboardInterrupt:
        return None
    except Exception:
        # Any curses failure -> fallback
        return None

# --------------------------
# Fallback (numbered) menu
# --------------------------

def run_fallback_menu() -> Optional[Set[int]]:
    print("\n" + "=" * 60)
    print("   HTML/CSS CLEANING TOOL (Fallback Mode)")
    print("=" * 60)
    print("Curses UI not available. Using numbered toggles.")
    selected: Set[int] = set()

    while True:
        print("\nOptions:")
        for i, (name, _, enabled) in enumerate(MENU_OPTIONS, start=1):
            box = "[*]" if (i - 1) in selected else "[ ]"
            status = "" if enabled else " (DISABLED)"
            print(f"  {i}. {box} {name}{status}")

        print("\nCommands: 1/2 to toggle • 'go' to continue • 'q' to quit")
        cmd = input("Command: ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            return None
        elif cmd in ("go", "start", "continue"):
            return selected
        elif cmd in ("1", "2"):
            idx = int(cmd) - 1
            if MENU_OPTIONS[idx][2]:
                if idx in selected:
                    selected.remove(idx)
                else:
                    selected.add(idx)
            else:
                print("This option is disabled.")
        else:
            print("Invalid command.")

# --------------------------
# Path + confirmation prompts
# --------------------------

def prompt_for_project_path() -> Optional[Path]:
    print("\n" + "=" * 60)
    print("Project Path")
    print("=" * 60)
    while True:
        try:
            raw = input("📂 Enter the project folder path: ").strip()
            if raw.startswith('"') and raw.endswith('"'):
                raw = raw[1:-1]
            if raw.startswith("'") and raw.endswith("'"):
                raw = raw[1:-1]

            if not raw:
                print("❌ Path cannot be empty.")
                continue

            p = Path(raw).expanduser().resolve()
            if not p.exists():
                print(f"❌ Path does not exist: {p}")
                if input("Try again? (y/N): ").strip().lower() not in ("y", "yes"):
                    return None
                continue
            if not p.is_dir():
                print(f"❌ Not a directory: {p}")
                if input("Try again? (y/N): ").strip().lower() not in ("y", "yes"):
                    return None
                continue
            return p
        except KeyboardInterrupt:
            return None

def confirm(prompt: str) -> bool:
    ans = input(f"{prompt} (y/N): ").strip().lower()
    return ans in ("y", "yes")

# --------------------------
# Orchestrator
# --------------------------

def remove_html_classes(project_path: Path) -> None:
    print(f"\n🔍 Searching for HTML files in: {project_path}")
    html_files = find_files(project_path, ["html", "htm"])
    if not html_files:
        print("❌ No HTML files found.")
        return

    print(f"📁 Found {len(html_files)} HTML file(s).")
    if not confirm(f"Remove class attributes from {len(html_files)} file(s)?"):
        print("Operation cancelled.")
        return

    print("\n🧹 Processing HTML files...")
    ok = 0
    for f in html_files:
        success, msg = process_html_file(f)
        print(msg)
        if success:
            ok += 1
    print(f"\n✅ Done. Successfully processed {ok}/{len(html_files)} file(s).")

def clear_css_scss(project_path: Path) -> None:
    print(f"\n🔍 Searching for CSS/SCSS files in: {project_path}")
    css_files = find_files(project_path, ["css", "scss"])
    if not css_files:
        print("❌ No CSS/SCSS files found.")
        return

    print(f"📁 Found {len(css_files)} CSS/SCSS file(s).")
    print("\nFiles that will be cleared:")
    for f in css_files:
        print(f"  • {f}")

    if not confirm(f"\n⚠️  Clear {len(css_files)} file(s)?"):
        print("Operation cancelled.")
        return

    print("\n🧹 Clearing files...")
    ok = 0
    for f in css_files:
        success, msg = clear_file_content(f)
        print(msg)
        if success:
            ok += 1
    print(f"\n✅ Done. Successfully cleared {ok}/{len(css_files)} file(s).")

def can_use_curses() -> bool:
    # Must have a real TTY for both stdin and stdout
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    try:
        import curses  # noqa: F401
    except Exception:
        return False
    return True

def main() -> None:
    print("🚀 HTML/CSS Cleaning Tool")

    # Only try curses when we have a true TTY + curses import works.
    if can_use_curses():
        selected = run_curses_menu()
    else:
        selected = None  # force fallback

    if selected is None:
        selected = run_fallback_menu()

    if selected is None:
        print("\nGoodbye! 👋")
        return
    if not selected:
        print("\n❌ No operations selected. Goodbye!")
        return

    project_path = prompt_for_project_path()
    if project_path is None:
        print("\nCancelled. Goodbye! 👋")
        return

    print(f"\n🚀 Processing: {project_path}")

    if 0 in selected:
        print("\n" + "=" * 50)
        print("OPERATION: HTML Class Removal")
        print("=" * 50)
        remove_html_classes(project_path)

    if 1 in selected:
        print("\n" + "=" * 50)
        print("OPERATION: CSS/SCSS Clearing")
        print("=" * 50)
        clear_css_scss(project_path)

    print("\n🎉 All operations completed!")
    try:
        input("Press Enter to exit...")
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCancelled. Goodbye! 👋")