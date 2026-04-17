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

###############################################
# LOGGING
###############################################

def log(msg): print(f"[INFO] {msg}")
def ok(msg): print(f"[OK] {msg}")
def warn(msg): print(f"[WARN] {msg}")
def error(msg): print(f"[ERROR] {msg}")

###############################################
# SAFE RUN
###############################################

def run(cmd, allow_fail=False):
    log("Running: " + " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except FileNotFoundError:
        error(f"Missing command: {cmd[0]}")
        sys.exit(1)
    except subprocess.CalledProcessError:
        if allow_fail:
            warn("Command failed (ignored)")
        else:
            error("Command failed")
            sys.exit(1)

###############################################
# PATH FIX
###############################################

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

###############################################
# SELF INSTALL (COPY, NOT MOVE)
###############################################

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

    error("Automatic install failed.")
    print(f"Manual: mv \"{current}\" ~/.local/bin/{SCRIPT_NAME}")

###############################################
# INSTALL GIT
###############################################

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
        error("Unsupported OS")
        sys.exit(1)

###############################################
# GIT IDENTITY
###############################################

def ensure_identity():
    name = subprocess.getoutput("git config --global user.name")
    email = subprocess.getoutput("git config --global user.email")

    if name and email:
        ok(f"Identity OK: {name}")
        return

    warn("Git identity missing")

    name = input("Enter your name: ")
    email = input("Enter your GitHub email: ")

    run(["git", "config", "--global", "user.name", name])
    run(["git", "config", "--global", "user.email", email])

    ok("Identity configured")

###############################################
# SSH SETUP
###############################################

def ensure_ssh():
    ssh_dir = os.path.expanduser("~/.ssh")
    key_path = os.path.join(ssh_dir, "id_ed25519")

    if os.path.exists(key_path):
        ok("SSH key exists")
        return

    warn("No SSH key — generating...")

    os.makedirs(ssh_dir, exist_ok=True)

    email = subprocess.getoutput("git config --global user.email")

    run([
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", key_path,
        "-N", ""
    ])

    ok("SSH key created")

    print("\n=== COPY THIS KEY TO GITHUB ===\n")
    subprocess.run(["cat", key_path + ".pub"])

    print("\nGo to: https://github.com/settings/keys")
    input("Press ENTER after adding SSH key...")

###############################################
# MAIN
###############################################

def main():

    if shutil.which(SCRIPT_NAME) is None:
        if input("Install globally? (y/n): ").lower() == "y":
            install_self()

    log("Starting git automation tool")

    ensure_git()

    cwd = os.getcwd()
    if input(f"Use current dir ({cwd})? (y/n): ").lower() != "y":
        os.chdir(input("Enter directory: "))

    ###########################################
    # INIT
    ###########################################
    if not os.path.isdir(".git"):
        run(["git", "init"])

    ###########################################
    # BRANCH
    ###########################################
    branch = input("Branch (default main): ") or "main"
    run(["git", "checkout", "-B", branch])

    ###########################################
    # REMOTE
    ###########################################
    print("\n1) Existing URL (HTTPS)")
    print("2) GitHub new repo (HTTPS)")
    print("3) Use SSH (recommended)")

    choice = input("Choice: ")

    if choice == "1":
        remote = input("Enter repo URL: ")

    elif choice == "2":
        repo = input("Repo name: ")
        user = input("GitHub username: ")
        remote = f"https://github.com/{user}/{repo}.git"

        print("\nCreate repo:")
        print("https://github.com/new")
        input("Press ENTER after creating repo...")

    elif choice == "3":
        repo = input("Repo name: ")
        user = input("GitHub username: ")
        remote = f"git@github.com:{user}/{repo}.git"

        ensure_ssh()

    else:
        error("Invalid choice")
        sys.exit(1)

    ###########################################
    # REMOTE SET
    ###########################################
    run(["git", "remote", "remove", "origin"], allow_fail=True)
    run(["git", "remote", "add", "origin", remote])
    ok(f"Remote set: {remote}")

    ###########################################
    # ADD + COMMIT
    ###########################################
    run(["git", "add", "."])

    ensure_identity()

    msg = input("Commit message: ") or "initial commit"
    run(["git", "commit", "-m", msg])

    ###########################################
    # PUSH
    ###########################################
    run(["git", "push", "-u", "origin", branch])

    ok("Push complete.")

###############################################
# ENTRY
###############################################

if __name__ == "__main__":
    main()
