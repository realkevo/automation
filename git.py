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

    error("Automatic install failed.")
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
        error("Unsupported OS")
        sys.exit(1)

# =========================
# GIT IDENTITY (IDEMPOTENT)
# =========================
def ensure_identity():
    name = subprocess.getoutput("git config --global user.name").strip()
    email = subprocess.getoutput("git config --global user.email").strip()

    if name and email:
        ok(f"Identity OK: {name} <{email}>")
        return

    warn("Git identity missing — configuring...")

    if not name:
        name = input("Enter your name: ").strip()

    if not email:
        email = input("Enter your GitHub email: ").strip()

    run(["git", "config", "--global", "user.name", name])
    run(["git", "config", "--global", "user.email", email])

    ok("Identity configured")

# =========================
# SSH SETUP (IDEMPOTENT)
# =========================
def ensure_ssh():
    ssh_dir = os.path.expanduser("~/.ssh")
    private_key = os.path.join(ssh_dir, "id_ed25519")
    public_key = private_key + ".pub"

    # ✅ Skip if already exists
    if os.path.exists(private_key) and os.path.exists(public_key):
        ok("SSH already configured — skipping setup")
        return

    warn("No SSH key found — generating...")

    os.makedirs(ssh_dir, exist_ok=True)

    email = subprocess.getoutput("git config --global user.email").strip()

    run([
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", private_key,
        "-N", ""
    ])

    ok("SSH key created")

    print("\n=== ADD THIS KEY TO GITHUB ===\n")
    subprocess.run(["cat", public_key])

    print("\nGo to: https://github.com/settings/keys")
    input("Press ENTER after adding SSH key...")

    ok("SSH setup complete")

# =========================
# MAIN
# =========================
def main():

    # SELF INSTALL
    if shutil.which(SCRIPT_NAME) is None:
        if input("Install globally? (y/n): ").lower() == "y":
            install_self()

    log("Starting git automation tool")

    ensure_git()

    cwd = os.getcwd()
    if input(f"Use current dir ({cwd})? (y/n): ").lower() != "y":
        os.chdir(input("Enter directory: "))

    # INIT REPO
    if not os.path.isdir(".git"):
        run(["git", "init"])

    branch = input("Branch (default main): ") or "main"
    run(["git", "checkout", "-B", branch])

    # REMOTE
    print("\n1) Existing URL (HTTPS)")
    print("2) GitHub new repo (HTTPS)")
    print("3) SSH (recommended)")

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

    # REMOTE SET
    run(["git", "remote", "remove", "origin"], allow_fail=True)
    run(["git", "remote", "add", "origin", remote])
    ok(f"Remote set: {remote}")

    # ADD + COMMIT
    run(["git", "add", "."])
    ensure_identity()

    msg = input("Commit message: ") or "initial commit"
    run(["git", "commit", "-m", msg])

    # PUSH
    try:
        run(["git", "push", "-u", "origin", branch])

    except SystemExit:
        print("\n" + "="*50)
        error("PUSH FAILED — REMOTE REPOSITORY NOT FOUND")
        print("="*50)

        print("\nWHAT HAPPENED:")
        print("- The GitHub repository does not exist yet.\n")

        print("FIX STEPS:")
        print("1. Go to: https://github.com/new")
        print("2. Create repository with the exact name used above")
        print("3. DO NOT initialize with README\n")

        print("THEN RUN:")
        print(f"git push -u origin {branch}\n")

        print("OPTIONAL MANUAL FIX:")
        print(f"""
echo "# {repo if 'repo' in locals() else 'project'}" >> README.md
git init
git add .
git commit -m "first commit"
git branch -M {branch}
git remote add origin {remote if 'remote' in locals() else 'URL'}
git push -u origin {branch}
""")

        sys.exit(1)

    ok("Push complete")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()
