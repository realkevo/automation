#!/usr/bin/env python3

import os
import sys
import shutil
import subprocess
import stat

SCRIPT_NAME = "gitx"

INSTALL_PATHS = [
    "/usr/local/bin",
    os.path.expanduser("~/.local/bin"),
    os.path.expanduser("~/bin"),
]

# =========================
# LOGGING
# =========================
def log(msg): print(f"[INFO] {msg}")
def ok(msg): print(f"[OK] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def error(msg): print(f"[ERROR] {msg}")

# =========================
# SAFE RUN
# =========================
def run(cmd, allow_fail=False):
    log("Running: " + " ".join(cmd))
    try:
        subprocess.run(
            cmd,
            check=True,
            stdin=sys.stdin,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
    except FileNotFoundError:
        error(f"Missing command: {cmd[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError:
        if allow_fail:
            warn(f"Command failed (ignored): {' '.join(cmd)}")
        else:
            error(f"Command failed: {' '.join(cmd)}")
            sys.exit(1)

# =========================
# PATH FIX
# =========================
def ensure_path():
    local_bin = os.path.expanduser("~/.local/bin")

    if local_bin in os.environ.get("PATH", ""):
        return

    bashrc = os.path.expanduser("~/.bashrc")
    line = 'export PATH=$HOME/.local/bin:$PATH\n'

    try:
        with open(bashrc, "a") as f:
            f.write("\n# added by gitx\n")
            f.write(line)

        os.environ["PATH"] = f"{local_bin}:{os.environ.get('PATH','')}"
        ok("PATH updated")
    except Exception as e:
        warn(f"PATH update failed: {e}")

# =========================
# SELF INSTALL
# =========================
def make_exec(path):
    st = os.stat(path)
    os.chmod(path, st.st_mode | stat.S_IEXEC)

def install_self():
    current = os.path.realpath(sys.argv[0])
    make_exec(current)

    for d in INSTALL_PATHS:
        target = os.path.join(d, SCRIPT_NAME)
        log(f"Trying install → {target}")

        try:
            os.makedirs(d, exist_ok=True)
            shutil.copy2(current, target)
            make_exec(target)

            ensure_path()

            ok(f"Installed at {target}")
            print(f"\nRun anywhere using: {SCRIPT_NAME}")
            sys.exit(0)

        except PermissionError:
            try:
                subprocess.run(["sudo", "cp", current, target], check=True)
                subprocess.run(["sudo", "chmod", "+x", target], check=True)

                ensure_path()

                ok(f"Installed at {target} (sudo)")
                sys.exit(0)
            except Exception:
                warn(f"Failed: {d}")

        except Exception:
            warn(f"Failed: {d}")

    error("Install failed")
    print(f"Manual: mv {current} ~/.local/bin/{SCRIPT_NAME}")

# =========================
# GIT INSTALL
# =========================
def ensure_git():
    if shutil.which("git"):
        ok("Git found")
        return

    warn("Git missing — installing...")

    if "com.termux" in os.environ.get("PREFIX", ""):
        run(["pkg", "update", "-y"])
        run(["pkg", "install", "git", "-y"])
    elif shutil.which("apt"):
        run(["sudo", "apt", "update"])
        run(["sudo", "apt", "install", "-y", "git"])
    else:
        error("Unsupported system")
        sys.exit(1)

# =========================
# IDENTITY
# =========================
def ensure_identity():
    name = subprocess.getoutput("git config --global user.name").strip()
    email = subprocess.getoutput("git config --global user.email").strip()

    if name and email:
        ok(f"Identity OK: {name} <{email}>")
        return

    warn("Missing git identity")

    name = name or input("Enter name: ").strip()
    email = email or input("Enter email: ").strip()

    run(["git", "config", "--global", "user.name", name])
    run(["git", "config", "--global", "user.email", email])

    ok("Identity set")

# =========================
# SSH PRECHECK (CRITICAL FIX)
# =========================
def ensure_ssh():
    ssh_key = os.path.expanduser("~/.ssh/id_ed25519")

    if os.path.exists(ssh_key):
        ok("SSH already configured — skipping setup")
        return

    warn("SSH not configured — generating now")

    ssh_dir = os.path.expanduser("~/.ssh")
    os.makedirs(ssh_dir, exist_ok=True)

    email = subprocess.getoutput("git config --global user.email").strip()

    run([
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", ssh_key,
        "-N", ""
    ])

    ok("SSH key generated")

    print("\n========== ADD THIS KEY TO GITHUB ==========\n")
    with open(ssh_key + ".pub") as f:
        print(f.read())

    print("\nGo here:")
    print("https://github.com/settings/keys")

    print("\nIMPORTANT:")
    print("Rerun gitx after adding SSH key")
    sys.exit(0)

# =========================
# PUSH
# =========================
def push(branch):
    env = os.environ.copy()
    env["GIT_TERMINAL_PROMPT"] = "0"

    try:
        subprocess.run(
            ["git", "push", "-u", "origin", branch],
            check=True,
            env=env
        )
    except subprocess.CalledProcessError:
        error("Push failed")
        print("\nFix:")
        print("- Ensure SSH key is added to GitHub")
        print("- Or use HTTPS remote URL")
        sys.exit(1)

# =========================
# MAIN FLOW (SSH FIRST FIXED)
# =========================
def main():

    # SELF INSTALL
    if shutil.which(SCRIPT_NAME) is None:
        if input("Install globally? (y/n): ").lower() == "y":
            install_self()

    log("Starting git automation tool")

    # PRE-REQUISITES FIRST
    ensure_git()
    ensure_identity()

    # 🔥 SSH MUST BE READY BEFORE ANYTHING ELSE
    if not os.path.exists(os.path.expanduser("~/.ssh/id_ed25519")):
        warn("SSH not ready — running setup first")
        ensure_ssh()

    ok("SSH ready — continuing workflow")

    # DIRECTORY
    cwd = os.getcwd()
    if input(f"Use current dir ({cwd})? (y/n): ").lower() != "y":
        os.chdir(input("Enter directory: "))

    # INIT
    if not os.path.isdir(".git"):
        run(["git", "init"])
        ok("Repository initialized")

    # BRANCH
    branch = input("Branch (default main): ") or "main"
    run(["git", "checkout", "-B", branch])

    # =========================
    # REMOTE
    # =========================
    print("\n1) Existing URL")
    print("2) Create repo manually")
    print("3) Paste repo URL")

    choice = input("Choice: ").strip()

    if choice == "1":
        remote = input("Repo URL: ").strip()

    elif choice == "2":
        repo = input("Repo name: ").strip()
        user = input("GitHub username: ").strip()

        print("\nCreate repo here:")
        print("https://github.com/new")
        input("Press ENTER after creating repo...")

        remote = input("Paste repo URL: ").strip()

    elif choice == "3":
        remote = input("Paste repo URL: ").strip()

    else:
        error("Invalid choice")
        sys.exit(1)

    ok(f"Remote: {remote}")

    run(["git", "remote", "remove", "origin"], allow_fail=True)
    run(["git", "remote", "add", "origin", remote])

    # COMMIT
    run(["git", "add", "."])

    msg = input("Commit message: ") or "initial commit"
    run(["git", "commit", "-m", msg])

    # PUSH
    push(branch)

    ok("Push complete")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()
