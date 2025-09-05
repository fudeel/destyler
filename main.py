"""
HTML/CSS/JS Cleaning Tool — Curses-based Checkbox CLI

Features:
- Arrow-key menu with SPACE to toggle and ENTER to continue
- Remove class="..." from .html/.htm files
- Clear content from .css/.scss files
- Remove class/className and style attributes from .js/.ts and .jsx/.tsx template strings
- Asks for project path and confirmation before applying changes
- Graceful fallback if curses unavailable

Windows: pip install windows-curses
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Set, Optional

# --------------------------
# File operation patterns
# --------------------------

CLASS_ATTR_PATTERN = re.compile(
    r'\s*class\s*=\s*(?:"[^"]*"|\'[^\']*\'|[^\s>]+)',
    re.IGNORECASE
)

# JS/TS template patterns for class and style removal
JS_PATTERNS = [
    # className="..." or className='...' (React)
    re.compile(r'\s*className\s*=\s*(?:"[^"]*"|\'[^\']*\'|`[^`]*`)', re.IGNORECASE),
    # class="..." or class='...' in template literals
    re.compile(r'\s*class\s*=\s*(?:"[^"]*"|\'[^\']*\')', re.IGNORECASE),
    # style={{...}} (React inline styles)
    re.compile(r'\s*style\s*=\s*\{\{[^}]*\}\}', re.IGNORECASE),
    # style="..." or style='...' in templates
    re.compile(r'\s*style\s*=\s*(?:"[^"]*"|\'[^\']*\')', re.IGNORECASE),
]


def remove_class_attributes(content: str) -> str:
    """Remove class attributes from HTML content."""
    return re.sub(CLASS_ATTR_PATTERN, "", content)


def remove_js_template_attributes(content: str) -> str:
    """Remove class/className and style attributes from JS/TS template strings."""
    for pattern in JS_PATTERNS:
        content = re.sub(pattern, "", content)
    return content


def process_file(file_path: Path, processor_func) -> Tuple[bool, str]:
    """Process a file with given processor function."""
    try:
        text = file_path.read_text(encoding="utf-8", errors="replace")
        cleaned = processor_func(text)
        file_path.write_text(cleaned, encoding="utf-8")
        return True, f"✓ Processed: {file_path}"
    except Exception as e:
        return False, f"✗ Error processing {file_path}: {e}"


def clear_file(file_path: Path) -> Tuple[bool, str]:
    """Empty a file."""
    try:
        file_path.write_text("", encoding="utf-8")
        return True, f"✓ Cleared: {file_path}"
    except Exception as e:
        return False, f"✗ Error clearing {file_path}: {e}"


def find_files(root: Path, extensions: List[str]) -> List[Path]:
    """Find files by extension recursively."""
    files = []
    for ext in extensions:
        files.extend(root.rglob(f"*.{ext}"))
    return sorted(set(files), key=lambda p: str(p).lower())


# --------------------------
# Menu configuration
# --------------------------

MENU_OPTIONS = [
    (
        "Remove classes from .html files",
        'Removes all class="..." attributes from HTML elements.',
        True,
    ),
    (
        "Clear content from .css/.scss files",
        "Empties all CSS/SCSS files (sets content to empty).",
        True,
    ),
    (
        "Remove classes/styles from .js/.ts and .jsx/.tsx templates",
        "Removes className, class, and style attributes from JS/TS template strings.",
        True,
    ),
]


# --------------------------
# Curses menu
# --------------------------

def run_curses_menu() -> Optional[Set[int]]:
    """Render checkbox menu using curses."""
    try:
        import curses
    except ImportError:
        return None

    selected = set()

    def _menu(stdscr):
        curses.curs_set(0)
        stdscr.nodelay(False)
        stdscr.keypad(True)
        current = 0

        while True:
            stdscr.clear()
            h, w = stdscr.getmaxyx()

            # Title and help
            title = " HTML/CSS/JS CLEANING TOOL "
            help_text = "↑/↓ move • SPACE toggle • ENTER continue • ESC quit"
            stdscr.addstr(1, max(0, (w - len(title)) // 2), title, curses.A_BOLD | curses.A_REVERSE)
            stdscr.addstr(3, max(0, (w - len(help_text)) // 2), help_text, curses.A_DIM)

            # Options
            start_row = 6
            for i, (name, desc, enabled) in enumerate(MENU_OPTIONS):
                prefix = "[*]" if i in selected else "[ ]"
                status = "" if enabled else " (DISABLED)"
                line = f"  {prefix} {name}{status}"

                attr = curses.A_BOLD if i == current else curses.A_NORMAL
                stdscr.addstr(start_row + i * 2, 2, line, attr)
                stdscr.addstr(start_row + i * 2 + 1, 4, desc, curses.A_DIM)

            # Footer
            chosen = [MENU_OPTIONS[i][0] for i in sorted(selected)]
            chosen_line = "Selected: " + (", ".join(chosen) if chosen else "(none)")
            stdscr.addstr(h - 2, 2, chosen_line[:w - 4], curses.A_DIM)

            stdscr.refresh()

            key = stdscr.getch()
            if key in (curses.KEY_UP, ord('k')):
                current = (current - 1) % len(MENU_OPTIONS)
            elif key in (curses.KEY_DOWN, ord('j')):
                current = (current + 1) % len(MENU_OPTIONS)
            elif key in (curses.KEY_ENTER, 10, 13):
                return selected if selected else set()
            elif key == 27:  # ESC
                return None
            elif key == ord(' '):
                if MENU_OPTIONS[current][2]:  # if enabled
                    if current in selected:
                        selected.remove(current)
                    else:
                        selected.add(current)

    try:
        import curses
        return curses.wrapper(_menu)
    except (KeyboardInterrupt, Exception):
        return None


# --------------------------
# Fallback menu
# --------------------------

def run_fallback_menu() -> Optional[Set[int]]:
    """Simple numbered menu fallback."""
    print("\n" + "=" * 60)
    print("   HTML/CSS/JS CLEANING TOOL (Fallback Mode)")
    print("=" * 60)
    print("Curses UI not available. Using numbered toggles.")
    selected = set()

    while True:
        print("\nOptions:")
        for i, (name, _, enabled) in enumerate(MENU_OPTIONS, start=1):
            box = "[*]" if (i - 1) in selected else "[ ]"
            status = "" if enabled else " (DISABLED)"
            print(f"  {i}. {box} {name}{status}")

        print("\nCommands: 1/2/3 to toggle • 'go' to continue • 'q' to quit")
        cmd = input("Command: ").strip().lower()

        if cmd in ("q", "quit", "exit"):
            return None
        elif cmd in ("go", "start", "continue"):
            return selected
        elif cmd in ("1", "2", "3"):
            idx = int(cmd) - 1
            if idx < len(MENU_OPTIONS) and MENU_OPTIONS[idx][2]:
                if idx in selected:
                    selected.remove(idx)
                else:
                    selected.add(idx)
            else:
                print("Invalid option or disabled.")
        else:
            print("Invalid command.")


# --------------------------
# User input helpers
# --------------------------

def prompt_for_path() -> Optional[Path]:
    """Prompt user for project path with validation."""
    print("\n" + "=" * 60)
    print("Project Path")
    print("=" * 60)

    while True:
        try:
            raw = input("📂 Enter the project folder path: ").strip()
            # Remove quotes if present
            if (raw.startswith('"') and raw.endswith('"')) or (raw.startswith("'") and raw.endswith("'")):
                raw = raw[1:-1]

            if not raw:
                print("❌ Path cannot be empty.")
                continue

            path = Path(raw).expanduser().resolve()
            if not path.exists():
                print(f"❌ Path does not exist: {path}")
                if input("Try again? (y/N): ").strip().lower() not in ("y", "yes"):
                    return None
                continue
            if not path.is_dir():
                print(f"❌ Not a directory: {path}")
                if input("Try again? (y/N): ").strip().lower() not in ("y", "yes"):
                    return None
                continue
            return path
        except KeyboardInterrupt:
            return None


def confirm(prompt: str) -> bool:
    """Get yes/no confirmation from user."""
    return input(f"{prompt} (y/N): ").strip().lower() in ("y", "yes")


# --------------------------
# Operation functions
# --------------------------

def remove_html_classes(project_path: Path):
    """Remove class attributes from HTML files."""
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
    success_count = 0
    for f in html_files:
        success, msg = process_file(f, remove_class_attributes)
        print(msg)
        if success:
            success_count += 1
    print(f"\n✅ Successfully processed {success_count}/{len(html_files)} file(s).")


def clear_css_files(project_path: Path):
    """Clear CSS/SCSS files."""
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
    success_count = 0
    for f in css_files:
        success, msg = clear_file(f)
        print(msg)
        if success:
            success_count += 1
    print(f"\n✅ Successfully cleared {success_count}/{len(css_files)} file(s).")


def clean_js_templates(project_path: Path):
    """Remove class/style attributes from JS/TS template strings."""
    print(f"\n🔍 Searching for JS/TS files in: {project_path}")
    js_files = find_files(project_path, ["js", "ts", "jsx", "tsx"])

    if not js_files:
        print("❌ No JS/TS files found.")
        return

    print(f"📁 Found {len(js_files)} JS/TS file(s).")
    if not confirm(f"Remove class/style attributes from {len(js_files)} file(s)?"):
        print("Operation cancelled.")
        return

    print("\n🧹 Processing JS/TS files...")
    success_count = 0
    for f in js_files:
        success, msg = process_file(f, remove_js_template_attributes)
        print(msg)
        if success:
            success_count += 1
    print(f"\n✅ Successfully processed {success_count}/{len(js_files)} file(s).")


def can_use_curses() -> bool:
    """Check if curses UI is available."""
    if not (sys.stdin.isatty() and sys.stdout.isatty()):
        return False
    try:
        import curses
        return True
    except ImportError:
        return False


# --------------------------
# Main
# --------------------------

def main():
    """Main application entry point."""
    print("🚀 HTML/CSS/JS Cleaning Tool")

    # Try curses menu, fallback to simple menu
    selected = run_curses_menu() if can_use_curses() else None
    if selected is None:
        selected = run_fallback_menu()

    if selected is None:
        print("\nGoodbye! 👋")
        return
    if not selected:
        print("\n❌ No operations selected. Goodbye!")
        return

    project_path = prompt_for_path()
    if project_path is None:
        print("\nCancelled. Goodbye! 👋")
        return

    print(f"\n🚀 Processing: {project_path}")

    # Execute selected operations
    operations = [
        (0, "HTML Class Removal", remove_html_classes),
        (1, "CSS/SCSS Clearing", clear_css_files),
        (2, "JS/TS Template Cleaning", clean_js_templates),
    ]

    for idx, title, func in operations:
        if idx in selected:
            print("\n" + "=" * 50)
            print(f"OPERATION: {title}")
            print("=" * 50)
            func(project_path)

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