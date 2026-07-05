import os
import platform
import subprocess
import sys
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    src_main = root / "src" / "desktop" / "main.py"

    if not src_main.exists():
        raise FileNotFoundError(f"Missing entrypoint: {src_main}")

    app_name = "HousingPlatform"
    current_os = platform.system().lower()

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--name",
        app_name,
        str(src_main),
    ]

    if current_os == "darwin":
        cmd.extend(["--windowed"])

    if current_os == "windows":
        cmd.extend(["--console"])

    env = os.environ.copy()
    env["PYTHONPATH"] = str(root / "src")

    print(f"Building desktop app for {current_os}...")
    subprocess.check_call(cmd, cwd=root, env=env)
    print("Build complete. Output is in dist/.")


if __name__ == "__main__":
    main()
