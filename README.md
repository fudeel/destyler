# 🧹 HTML/CSS Cleaning Tool

> **Purpose:** Reset projects where an AI (or careless developer) produced terrible, bloated, or messy styling.  
> This tool quickly **removes all HTML classes** and/or **empties CSS/SCSS files** so you can start fresh.

---

## 🎯 Target Audience

This tool is intended for developers who:
- Generated or inherited code with **ugly, AI-made, or overcomplicated styling**.
- Want to **reset styles** to a clean slate while keeping the structural HTML intact.
- Prefer an **interactive CLI menu** to choose operations, instead of running raw scripts.

Typical use case:  
You’ve got a messy Angular/React/Vue/static HTML project with 200+ files where every element has useless classes or the CSS is beyond saving. This tool lets you strip it all down in one go.

---

## ⚙️ What It Does

When you run the program, you’ll see a **menu**:

- **Remove classes from `.html` / `.htm` files**  
  Every `class="..."` (or `class='...'`) attribute is removed.  
  Example:  
  ```html
  <div class="row col-md-6">Hello</div>
  ```
  becomes:
    ```html
  <div>Hello</div>
  ```
  
- **Clears content from `.css` / `.scss` files**
    Example:
    ```css
    body { background: red; }
  ```
  becomes:
    ```html
  
  ```
  
# 🖥️ How It Works

1. **Interactive menu**
   * When you start the program, you'll see a simple checkbox menu.
   * Use the **arrow keys (↑/↓)** to move between options.
   * Press **SPACE** to toggle an option on or off.
   * Press **ENTER** to confirm your selection.
   * If your terminal doesn't support interactive mode (common inside IDEs), the program automatically falls back to a **numbered menu**, where you type `1`, `2`, etc. to toggle options.

2. **Project path prompt**
   * The program will ask you to type the **path to your project folder**.
   * It searches that folder (and all subfolders) for:
      * `.html` and `.htm` files
      * `.css` and `.scss` files

3. **Confirmation step**
   * Before making any changes, the program tells you exactly **how many files it found** for each selected operation.
   * It asks you to confirm (`y/N`) before continuing.

4. **Cleaning phase**
   * If you confirm, the program processes each file one by one.
   * You'll see messages like:
      * `✓ Processed: .../index.html`
      * `✓ Cleared: .../styles/main.scss`
   * When finished, it shows how many files were successfully cleaned.