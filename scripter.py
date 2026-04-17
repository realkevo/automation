#!/usr/bin/env python3

import os
import sys
import shutil
import stat
import subprocess

###############################################
# CONFIG
###############################################

SCRIPT_NAME = "scripter"
INSTALL_PATHS = [
    "/usr/local/bin",
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/bin"),
]

###############################################
# LOGGING
###############################################

def log(msg): print(f"[INFO] {msg}")
def ok(msg): print(f"[OK] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def error(msg): print(f"[ERROR] {msg}")

###############################################
# PATH HANDLING
###############################################

def ensure_path():
    local_bin = os.path.expanduser("~/.local/bin")
    current_path = os.environ.get("PATH", "")

    if local_bin in current_path:
        ok("PATH already configured.")
        return

    warn("~/.local/bin is not in PATH.")

    bashrc = os.path.expanduser("~/.bashrc")
    export_line = 'export PATH=$HOME/.local/bin:$PATH\n'

    try:
        if os.path.exists(bashrc):
            with open(bashrc, "r") as f:
                content = f.read()
        else:
            content = ""

        if export_line.strip() not in content:
            with open(bashrc, "a") as f:
                f.write("\n# Added by scripter\n")
                f.write(export_line)
            ok("Added ~/.local/bin to PATH in ~/.bashrc")
        else:
            log("PATH entry already exists in ~/.bashrc")

        # Update current session
        os.environ["PATH"] = f"{local_bin}:{current_path}"
        ok("PATH updated for current session")

        print("\n[INFO] If command not found, run:")
        print("       source ~/.bashrc\n")

    except Exception as e:
        error(f"Failed to update PATH: {e}")

###############################################
# PATH RESOLUTION
###############################################

def get_script_path():
    return os.path.realpath(sys.argv[0])

def is_in_path():
    return shutil.which(SCRIPT_NAME) is not None

###############################################
# INSTALLATION
###############################################

def make_executable(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def attempt_install(current_path):
    make_executable(current_path)

    for directory in INSTALL_PATHS:
        target = os.path.join(directory, SCRIPT_NAME)
        log(f"Trying install → {target}")

        try:
            os.makedirs(directory, exist_ok=True)
            shutil.move(current_path, target)
            make_executable(target)
            ok(f"Installed at {target}")

            ensure_path()

            print(f"\nRun anywhere using: {SCRIPT_NAME}")
            sys.exit(0)

        except PermissionError:
            try:
                subprocess.run(["sudo", "mv", current_path, target], check=True)
                subprocess.run(["sudo", "chmod", "+x", target], check=True)
                ok(f"Installed at {target} (sudo)")

                ensure_path()

                print(f"\nRun anywhere using: {SCRIPT_NAME}")
                sys.exit(0)
            except Exception:
                warn(f"Failed: {directory}")

        except Exception:
            warn(f"Failed: {directory}")

    print("\n[ERROR] Automatic installation failed.\n")
    print("Manual install options:\n")
    print(f"1) System-wide:")
    print(f"   sudo mv \"{current_path}\" /usr/local/bin/{SCRIPT_NAME}")
    print("\n2) User-only:")
    print("   mkdir -p ~/.local/bin")
    print(f"   mv \"{current_path}\" ~/.local/bin/{SCRIPT_NAME}")
    print("\n3) Ensure PATH contains:")
    print("   export PATH=$HOME/.local/bin:$PATH\n")

###############################################
# TEMPLATE GENERATION
###############################################

def generate_template(file_path, script_type):
    templates = {
        "bash": """#!/usr/bin/env bash
set -euo pipefail

main() {
    echo "Hello from Bash"
}

main "$@"
""",
        "python": """#!/usr/bin/env python3

def main():
    print("Hello from Python")

if __name__ == "__main__":
    main()
""",
        "powershell": """Write-Output "Hello from PowerShell"
""",
        "batch": """@echo off
echo Hello from Batch
pause
"""
    }

    content = templates.get(script_type, "")
    with open(file_path, "w") as f:
        f.write(content)

###############################################
# EXECUTION
###############################################

def run_script(file_path, ext):
    try:
        if ext == ".sh":
            subprocess.run(["bash", file_path])
        elif ext == ".py":
            subprocess.run(["python", file_path])
        elif ext == ".ps1":
            subprocess.run(["pwsh", file_path])
        elif ext == ".bat":
            subprocess.run(["cmd.exe", "/c", file_path])
        else:
            warn("Unknown execution type")
    except Exception as e:
        error(f"Execution failed: {e}")

###############################################
# MAIN
###############################################

def main():
    current_path = get_script_path()

    # Install prompt
    if not is_in_path():
        choice = input("[INPUT] Install globally? (y/n): ").strip().lower()
        if choice == "y":
            attempt_install(current_path)

    # OS detection
    log(f"OS detected: {sys.platform}")

    # Directory
    cwd = os.getcwd()
    use_current = input(f"[INPUT] Use current directory ({cwd})? (y/n): ").strip().lower()

    if use_current == "y":
        directory = cwd
    else:
        directory = input("[INPUT] Enter directory: ").strip()
        os.makedirs(directory, exist_ok=True)

    # Script type
    print("\n1) Bash (.sh)")
    print("2) Python (.py)")
    print("3) PowerShell (.ps1)")
    print("4) Batch (.bat)")
    print("5) Custom")

    choice = input("[INPUT] Choice: ").strip()

    mapping = {
        "1": (".sh", "bash"),
        "2": (".py", "python"),
        "3": (".ps1", "powershell"),
        "4": (".bat", "batch")
    }

    if choice in mapping:
        ext, script_type = mapping[choice]
    elif choice == "5":
        ext = input("[INPUT] Extension: ").strip()
        script_type = "custom"
    else:
        error("Invalid choice")
        sys.exit(1)

    # Name
    name = input("[INPUT] Script name: ").strip()
    file_path = os.path.join(directory, name + ext)

    log("Creating script...")
    generate_template(file_path, script_type)
    ok(f"Created: {file_path}")

    # Permissions (Unix)
    if os.name != "nt":
        make_executable(file_path)

    # Edit
    edit = input("[INPUT] Edit now? (y/n): ").strip().lower()
    if edit == "y":
        editor = os.environ.get("EDITOR", "nano")
        subprocess.run([editor, file_path])

    # Run
    run_now = input("[INPUT] Run now? (y/n): ").strip().lower()
    if run_now == "y":
        run_script(file_path, ext)

    ok(f"Done → {file_path}")

###############################################
# ENTRY
###############################################

if __name__ == "__main__":
    main()
