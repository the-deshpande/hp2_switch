#!/usr/bin/env python3
"""
Harry Potter and the Chamber of Secrets (Nintendo Switch) - Standalone NSP Builder
Packages the compiled NSO executable, packaging assets, and user's PC game files
into an installable standalone NSP for Nintendo Switch using hacbrewpack.
"""

import argparse
import os
import shutil
import struct
import subprocess
import sys

DEFAULT_TITLE_ID = "0100485032000000"
TITLE_NAME = "Harry Potter and the Chamber of Secrets"
PUBLISHER_NAME = "EA Games"
APP_VERSION = "1.3.0"

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
PACKAGING_DIR = os.path.join(REPO_ROOT, "packaging", "nsp")


def find_hacbrewpack(custom_path=None):
    if custom_path and os.path.isfile(custom_path):
        return custom_path

    which_path = shutil.which("hacbrewpack") or shutil.which("hacbrewpack.exe")
    if which_path:
        return which_path

    # Check common local directories
    candidates = [
        os.path.join(REPO_ROOT, "tools", "hacbrewpack.exe"),
        os.path.join(REPO_ROOT, "tools", "hacbrewpack"),
        os.path.join(REPO_ROOT, "hacbrewpack.exe"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def ensure_elf2nso(out_dir):
    """Ensure out/switch-arm64/main exists from hp2_game.elf."""
    main_nso = os.path.join(out_dir, "main")
    if os.path.isfile(main_nso):
        return main_nso

    elf_file = os.path.join(out_dir, "hp2_game.elf")
    if not os.path.isfile(elf_file):
        return None

    elf2nso = shutil.which("elf2nso")
    if elf2nso:
        print("  Converting hp2_game.elf -> main (NSO)...")
        subprocess.check_call([elf2nso, elf_file, main_nso])
        return main_nso

    # Try via Docker if local elf2nso is not present
    if shutil.which("docker"):
        print("  Converting hp2_game.elf -> main (NSO) via Docker container...")
        cmd = [
            "docker", "run", "--rm",
            "-v", f"{REPO_ROOT}:/work",
            "-w", "/work",
            "devkitpro/devkita64:latest",
            "elf2nso", "out/switch-arm64/hp2_game.elf", "out/switch-arm64/main"
        ]
        ret = subprocess.call(cmd)
        if ret == 0 and os.path.isfile(main_nso):
            return main_nso

    return None


# A whole savegame is written before the save partition is committed, so the
# journal must hold one (saves of this engine family reach ~9 MB). Keep in
# sync with GSwitchSaveDataSize / GSwitchSaveJournalSize in SDLLaunch.cpp.
SAVE_DATA_SIZE = 64 * 1024 * 1024
SAVE_JOURNAL_SIZE = 16 * 1024 * 1024


def patch_nacp_save_layout(nacp_path, title_id):
    with open(nacp_path, "r+b") as f:
        f.seek(0x3060)
        f.write(APP_VERSION.encode("ascii").ljust(0x10, b"\x00"))  # display_version
        f.seek(0x3025)
        f.write(b"\x01")  # startup_user_account = 1 (required)
        f.seek(0x3078)
        f.write(struct.pack("<Q", int(title_id, 16)))  # save_data_owner_id
        f.seek(0x3080)
        f.write(struct.pack("<Q", SAVE_DATA_SIZE))     # user_account_save_data_size
        f.seek(0x3088)
        f.write(struct.pack("<Q", SAVE_JOURNAL_SIZE))  # user_account_save_data_journal_size
        f.seek(0x3148)
        f.write(struct.pack("<Q", SAVE_DATA_SIZE))     # user_account_save_data_size_max
        f.seek(0x3150)
        f.write(struct.pack("<Q", SAVE_JOURNAL_SIZE))  # user_account_save_data_journal_size_max


def ensure_packaging_assets(title_id):
    """Ensure control.nacp, main.npdm, and icon exist in packaging/nsp/."""
    exefs_dir = os.path.join(PACKAGING_DIR, "exefs")
    control_dir = os.path.join(PACKAGING_DIR, "control")
    logo_dir = os.path.join(PACKAGING_DIR, "logo")

    os.makedirs(exefs_dir, exist_ok=True)
    os.makedirs(control_dir, exist_ok=True)
    os.makedirs(logo_dir, exist_ok=True)

    # 1. Icon
    icon_dst = os.path.join(control_dir, "icon_AmericanEnglish.dat")
    icon_src = os.path.join(REPO_ROOT, "Build", "Switch", "icon.jpg")
    if not os.path.isfile(icon_dst) and os.path.isfile(icon_src):
        shutil.copy2(icon_src, icon_dst)

    # 2. Control NACP
    nacp_dst = os.path.join(control_dir, "control.nacp")
    if not os.path.isfile(nacp_dst):
        print("  Generating control.nacp...")
        # Try nacptool
        if shutil.which("nacptool"):
            subprocess.check_call([
                "nacptool", "--create", TITLE_NAME, PUBLISHER_NAME, APP_VERSION,
                nacp_dst, f"--titleid={title_id}"
            ])
        elif shutil.which("docker"):
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{REPO_ROOT}:/work",
                "-w", "/work",
                "devkitpro/devkita64:latest",
                "nacptool", "--create", TITLE_NAME, PUBLISHER_NAME, APP_VERSION,
                "packaging/nsp/control/control.nacp", f"--titleid={title_id}"
            ]
            subprocess.check_call(cmd)

    # Always (re)apply the save layout, also to a control.nacp that already
    # exists, so older packaging dirs pick up the current sizes.
    if os.path.isfile(nacp_dst):
        patch_nacp_save_layout(nacp_dst, title_id)

    # 3. NPDM
    npdm_dst = os.path.join(exefs_dir, "main.npdm")
    npdm_json = os.path.join(PACKAGING_DIR, "npdm.json")
    if not os.path.isfile(npdm_dst) and os.path.isfile(npdm_json):
        print("  Generating main.npdm...")
        if shutil.which("npdmtool"):
            subprocess.check_call(["npdmtool", npdm_json, npdm_dst])
        elif shutil.which("docker"):
            cmd = [
                "docker", "run", "--rm",
                "-v", f"{REPO_ROOT}:/work",
                "-w", "/work",
                "devkitpro/devkita64:latest",
                "npdmtool", "packaging/nsp/npdm.json", "packaging/nsp/exefs/main.npdm"
            ]
            subprocess.check_call(cmd)


def main():
    parser = argparse.ArgumentParser(description="Build Standalone NSP for Harry Potter 2 (Switch)")
    parser.add_argument("--game-dir", required=True, help="Path to PC Harry Potter 2 folder (containing system/, Maps/, etc.)")
    parser.add_argument("--keys", required=True, help="Path to Nintendo Switch prod.keys file")
    parser.add_argument("--hacbrewpack", help="Path to hacbrewpack executable")
    parser.add_argument("--out-dir", default=os.path.join(REPO_ROOT, "dist"), help="Output directory for the NSP")
    parser.add_argument("--titleid", default=DEFAULT_TITLE_ID, help=f"Title ID (default: {DEFAULT_TITLE_ID})")
    args = parser.parse_args()

    game_dir = os.path.abspath(args.game_dir)
    keys_file = os.path.abspath(args.keys)
    out_dir = os.path.abspath(args.out_dir)

    print("=== Harry Potter and the Chamber of Secrets - NSP Builder ===")
    print(f"Game Directory : {game_dir}")
    print(f"Keys File      : {keys_file}")
    print(f"Output Dir     : {out_dir}")
    print(f"Title ID       : {args.titleid}")

    # Validate game directory
    if not os.path.isdir(game_dir):
        print(f"ERROR: Game directory does not exist: {game_dir}", file=sys.stderr)
        sys.exit(1)

    # Check for system folder and default.ini
    system_dir = None
    for entry in os.listdir(game_dir):
        if entry.lower() == "system" and os.path.isdir(os.path.join(game_dir, entry)):
            system_dir = os.path.join(game_dir, entry)
            break

    if not system_dir:
        print("ERROR: system/ directory not found in game directory!", file=sys.stderr)
        sys.exit(1)

    default_ini_found = False
    for f in os.listdir(system_dir):
        if f.lower() == "default.ini":
            default_ini_found = True
            break

    if not default_ini_found:
        print("ERROR: default.ini not found inside system/ directory!", file=sys.stderr)
        sys.exit(1)

    if not os.path.isfile(keys_file):
        print(f"ERROR: Keys file not found: {keys_file}", file=sys.stderr)
        sys.exit(1)

    hacbrewpack = find_hacbrewpack(args.hacbrewpack)
    if not hacbrewpack:
        print("ERROR: hacbrewpack executable not found! Specify with --hacbrewpack <path>", file=sys.stderr)
        sys.exit(1)

    # Locate compiled NSO binary ('main')
    build_out_dir = os.path.join(REPO_ROOT, "out", "switch-arm64")
    main_nso = ensure_elf2nso(build_out_dir)
    if not main_nso or not os.path.isfile(main_nso):
        print("ERROR: Compiled NSO binary ('main') not found! Please run ./build_switch.sh first.", file=sys.stderr)
        sys.exit(1)

    # Ensure packaging assets (control.nacp, main.npdm, icon)
    ensure_packaging_assets(args.titleid)

    # Prepare staging directories
    stage_dir = os.path.join(REPO_ROOT, "build_nsp_stage")
    if os.path.exists(stage_dir):
        shutil.rmtree(stage_dir)
    os.makedirs(stage_dir, exist_ok=True)

    stage_exefs = os.path.join(stage_dir, "exefs")
    stage_control = os.path.join(stage_dir, "control")
    stage_logo = os.path.join(stage_dir, "logo")
    stage_romfs = os.path.join(stage_dir, "romfs")

    os.makedirs(stage_exefs, exist_ok=True)
    os.makedirs(stage_control, exist_ok=True)
    os.makedirs(stage_logo, exist_ok=True)
    os.makedirs(stage_romfs, exist_ok=True)

    print("\n[1/4] Staging ExeFS, Control, and Logo...")
    shutil.copy2(main_nso, os.path.join(stage_exefs, "main"))
    shutil.copy2(os.path.join(PACKAGING_DIR, "exefs", "main.npdm"), os.path.join(stage_exefs, "main.npdm"))
    shutil.copy2(os.path.join(PACKAGING_DIR, "control", "control.nacp"), os.path.join(stage_control, "control.nacp"))
    shutil.copy2(os.path.join(PACKAGING_DIR, "control", "icon_AmericanEnglish.dat"), os.path.join(stage_control, "icon_AmericanEnglish.dat"))

    has_logo = False
    logo_png = os.path.join(PACKAGING_DIR, "logo", "NintendoLogo.png")
    startup_gif = os.path.join(PACKAGING_DIR, "logo", "StartupMovie.gif")
    if os.path.isfile(logo_png) and os.path.isfile(startup_gif):
        shutil.copy2(logo_png, os.path.join(stage_logo, "NintendoLogo.png"))
        shutil.copy2(startup_gif, os.path.join(stage_logo, "StartupMovie.gif"))
        has_logo = True

    print("\n[2/4] Staging RomFS assets from PC game directory...")
    # Link or copy each top-level entry in game_dir into stage_romfs
    linked_items = []
    for item in os.listdir(game_dir):
        src_item = os.path.join(game_dir, item)
        dst_item = os.path.join(stage_romfs, item)

        if os.path.isdir(src_item):
            try:
                if sys.platform == "win32":
                    subprocess.check_call(f'cmd /c mklink /J "{dst_item}" "{src_item}"', shell=True)
                else:
                    os.symlink(src_item, dst_item, target_is_directory=True)
                linked_items.append((dst_item, True))
                print(f"  Linked directory: {item}/")
            except Exception as e:
                print(f"  Note: Linking {item} failed ({e}), falling back to copying...")
                shutil.copytree(src_item, dst_item)
        elif os.path.isfile(src_item):
            shutil.copy2(src_item, dst_item)

    # Copy alsoft.conf if present in packaging
    alsoft_conf = os.path.join(PACKAGING_DIR, "alsoft.conf")
    if os.path.isfile(alsoft_conf):
        shutil.copy2(alsoft_conf, os.path.join(stage_romfs, "alsoft.conf"))
        print("  Staged alsoft.conf into RomFS.")

    print("\n[3/4] Packaging Standalone NSP with hacbrewpack...")
    os.makedirs(out_dir, exist_ok=True)
    cmd = [
        hacbrewpack,
        "--titleid", args.titleid,
        "-k", keys_file,
        "--nspdir", out_dir,
        "--exefsdir", stage_exefs,
        "--controldir", stage_control,
        "--romfsdir", stage_romfs,
    ]
    if has_logo:
        cmd.extend(["--logodir", stage_logo])
    else:
        cmd.append("--nologo")

    res = subprocess.run(cmd, cwd=stage_dir)
    if res.returncode != 0:
        print("ERROR: hacbrewpack packaging failed!", file=sys.stderr)
        # Cleanup links before exit
        for path, is_dir in linked_items:
            if is_dir and sys.platform == "win32" and os.path.exists(path):
                subprocess.call(f'cmd /c rmdir "{path}"', shell=True)
        shutil.rmtree(stage_dir, ignore_errors=True)
        sys.exit(res.returncode)

    # Rename output NSP to friendly title
    raw_nsp = os.path.join(out_dir, f"{args.titleid}.nsp")
    pretty_nsp = os.path.join(out_dir, f"Harry Potter and the Chamber of Secrets [{args.titleid}][v0] ({APP_VERSION}).nsp")
    if os.path.isfile(raw_nsp):
        if os.path.isfile(pretty_nsp):
            os.remove(pretty_nsp)
        shutil.move(raw_nsp, pretty_nsp)

    print("\n[4/4] Cleaning up staging files...")
    for path, is_dir in linked_items:
        if is_dir and sys.platform == "win32" and os.path.exists(path):
            subprocess.call(f'cmd /c rmdir "{path}"', shell=True)
    shutil.rmtree(stage_dir, ignore_errors=True)

    print("\n========================================================")
    print("SUCCESS: Standalone NSP created successfully!")
    print(f"File: {pretty_nsp}")
    print("========================================================")


if __name__ == "__main__":
    main()
