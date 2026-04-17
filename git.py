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
# GIT IDENTITY (SAFE + IDEMPOTENT)
# =========================
def ensure_identity():
    name = subprocess.getoutput("git config --global user.name").strip()
    email = subprocess.getoutput("git config --global user.email").strip()

    if name and email:
        ok(f"Identity OK: {name} <{email}>")
        return

    warn("Git identity missing — configuring...")

    name = name or input("Enter your name: ").strip()
    email = email or input("Enter your GitHub email: ").strip()

    run(["git", "config", "--global", "user.name", name])
    run(["git", "config", "--global", "user.email", email])

    ok("Identity configured")

# =========================
# SSH SETUP (SAFE SKIP)
# =========================
def ensure_ssh():
    ssh_dir = os.path.expanduser("~/.ssh")
    private = os.path.join(ssh_dir, "id_ed25519")
    public = private + ".pub"

    if os.path.exists(private) and os.path.exists(public):
        ok("SSH already configured — skipping setup")
        return

    warn("No SSH key found — generating...")

    os.makedirs(ssh_dir, exist_ok=True)

    email = subprocess.getoutput("git config --global user.email").strip()

    run([
        "ssh-keygen",
        "-t", "ed25519",
        "-C", email,
        "-f", private,
        "-N", ""
    ])

    ok("SSH key created")

    print("\n=== ADD THIS TO GITHUB ===\n")
    subprocess.run(["cat", public])

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

    # INIT
    if not os.path.isdir(".git"):
        run(["git", "init"])

    branch = input("Branch (default main): ") or "main"
    run(["git", "checkout", "-B", branch])

    # =========================
    # REMOTE HANDLING (FIXED)
    # =========================
    print("\n1) Existing URL (HTTPS or SSH)")
    print("2) Create repo manually (GitHub page)")
    print("3) Paste repo URL (recommended)")

    choice = input("Choice: ").strip()

    remote = ""

    if choice == "1":
        remote = input("Enter repo URL: ").strip()

    elif choice == "2":
        repo = input("Repo name: ").strip()
        user = input("GitHub username: ").strip()

        print("\n📌 CREATE REPO NOW:")
        print("https://github.com/new")
        print(f"Repo name must be: {repo}")
        print("❗ DO NOT add README\n")

        input("Press ENTER after creating repo...")

        remote = input("Paste repo URL for verification: ").strip()

    elif choice == "3":
        remote = input("Paste repo URL: ").strip()

    else:
        error("Invalid choice")
        sys.exit(1)

    # VALIDATION
    if "github.com" not in remote and "git@" not in remote:
        error("Invalid remote URL")
        sys.exit(1)

    ok(f"Remote set: {remote}")

    # SET REMOTE
    run(["git", "remote", "remove", "origin"], allow_fail=True)
    run(["git", "remote", "add", "origin", remote])

    # ADD + COMMIT
    run(["git", "add", "."])
    ensure_identity()

    msg = input("Commit message: ") or "initial commit"
    run(["git", "commit", "-m", msg])

    # SSH if needed
    if remote.startswith("git@"):
        ensure_ssh()

    # PUSH
    run(["git", "push", "-u", "origin", branch])

    ok("Push complete")

# =========================
# ENTRY
# =========================
if __name__ == "__main__":
    main()
