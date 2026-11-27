# Harry Potter and the Chamber of Secrets (Nintendo Switch Port)

A native Nintendo Switch port of **Harry Potter and the Chamber of Secrets (PC, 2002)** running on Unreal Engine 1 with modern OpenGL / EGL and Nintendo Horizon OS (`libnx`).

> [!IMPORTANT]
> **Game Assets Required**: This repository contains only open-source engine and launcher code. It does **not** include copyrighted game data (maps, textures, sounds, music, dialog). You must provide your own legally owned copy of the PC game.

---

## Formats Supported

The port supports two completely independent execution formats:

- **Standalone NSP (Recommended)**: Installed directly to the Nintendo Switch HOME Menu. Assets are self-contained inside internal RomFS (zero SD card clutter), saves are managed natively via Switch user account partitions (`save:/`), and the game runs in full Application mode with maximum OS memory priority and a dedicated 16 MB game thread stack.
- **Homebrew NRO**: Runs via the Homebrew Launcher (`sdmc:/switch/hp2/HarryPotter2.nro`) with external game assets and saves stored on the SD card (`sdmc:/switch/hp2/User/Save`).

---

## Features & Performance

- **Silky 60 FPS Presentation**: Native 1280x720 rendering in handheld mode and 1920x1080 in docked mode.
- **Integrated Hardware Tuning**: Automatically activates Horizon CPU boost (1224 MHz) and GPU boost (384 MHz) on startup for instant map loading (< 5s) and zero frame stutters, cleanly restoring clocks to stock on exit.
- **Save System & Quick Load**:
  - Automatically loads your latest save (`Slot0/Save0.usa`) on startup if one exists; otherwise starts a fresh game at Privet Drive.
  - **Quick Load Combo**: Press **L + R + Plus + Minus** at any time during gameplay to immediately reload your latest save without needing to go to the main menu.
  - **Dual Save Storage & Migration**: Automatically detects environment—uses internal NAND user account storage (`save:/`) in NSP mode, and SD card (`sdmc:/switch/hp2/User/Save`) in NRO mode. On first boot of the NSP, any existing save file found on the SD card is automatically migrated to internal NAND!
  - **Save Partition Reserved for Saves**: In NSP mode the internal save (64 MB, 16 MB journal) only holds savegames and settings. Saves created by older builds are enlarged automatically on first boot. Commits happen only when a file on `save:/` is complete, and a failed save never replaces the previous one.
  - **SD Card Usage**: The Mesa shader cache lives in `sdmc:/switch/hp2/cache/mesa` (max 64 MB). Crash dumps go to `sdmc:/switch/hp2/crash.log`. In NSP mode no log file is written unless you create an empty file `sdmc:/switch/hp2/debug_log`; the log then goes to `sdmc:/switch/hp2/boot.log`. The NRO always writes `boot.log` (buffered).
- **Docked / Handheld Switching**: The output follows the console mode live (1080p docked, 720p handheld). Set `SwitchDockedFullHD=False` under `[SDLDrv.SDLClient]` in `System.ini` to stay at 720p when docked.
- **Sleep & HOME Menu**: Settings and save data are committed when the game loses focus, and the CPU/GPU boost is re-applied after waking from sleep. Original clocks are restored on exit.
- **Full Controller Integration**: Native Joy-Con and Pro Controller mapping with analog sticks, face buttons, triggers, and jump/spell actions.

---

## Controls

| Button / Stick | Action |
|---|---|
| **Left Stick** | Move Harry |
| **Right Stick** | Camera Look |
| **A** | Primary Cast / Interact / Accept |
| **B** | Jump / Cancel |
| **X** | Sneak / Action |
| **Y** | First Person Look |
| **ZR** | Cast Spell / Use Wand (same as A) |
| **ZL** | Jump (same as B) |
| **Plus (`+`)** | Pause / Spell Book Menu |
| **Minus (`-`)** | Folio Magi (Card Album) / Map |
| **L + R + Plus + Minus** | **Quick Load** latest save |

---

## Installation & Playing

### Method A: Standalone NSP (Recommended)

1. Obtain or build your `Harry Potter and the Chamber of Secrets [0100485032000000][v0].nsp`.
2. Connect your Switch to your PC and launch **DBI** (or use **Tinfoil** / **Goldleaf**).
3. Start **Run MTP Responder**, open the **MicroSD install** or **NAND install** folder on your PC, and copy the `.nsp` file over.
4. Launch the game directly from the **Switch HOME Menu** and select your user profile.

### Method B: Homebrew NRO

1. Copy `HarryPotter2.nro` to your Nintendo Switch SD card:
   ```
   sdmc:/switch/hp2/HarryPotter2.nro
   ```
2. Copy your original PC game folders into `sdmc:/switch/hp2/`:
   ```
   sdmc:/
   └── switch/
       └── hp2/
           ├── HarryPotter2.nro
           ├── Maps/
           ├── Music/
           ├── Sounds/
           ├── system/ (or System/)
           └── Textures/
   ```
3. Launch `HarryPotter2` from the Homebrew Launcher (preferably in Title Override mode: hold `R` while launching any installed game from the HOME menu).

---

## How to Build Your Own Standalone NSP

You can build and package your legally owned PC copy into a standalone, installable NSP directly for the Nintendo Switch.

### Step 1: Prerequisites & Setup

1. **Python 3.8+** installed on your system.
2. **Original PC Game Data**: A folder containing your installed PC copy with `Maps/`, `Music/`, `Sounds/`, `system/`, and `Textures/`.
3. **Switch Keyset (`prod.keys`)**: Dumped from your Switch console (e.g. using Lockpick_RCM or Picofly).
4. **hacbrewpack** (v3.05+):
   - **Download**: Grab the latest release from [hacBrewPack Releases](https://github.com/The-4n/hacBrewPack/releases).
   - **Windows**: Place `hacbrewpack.exe` in `tools/hacbrewpack.exe` inside this repo, or add it to your `PATH`.
   - **Linux / macOS**: Compile or install to your `PATH` (`make && sudo make install`).

---

### Step 2: Compile the Nintendo Switch Binary

The project uses the devkitA64 toolchain. The easiest way to build without configuring a local devkitPro installation is with **Docker** or **WSL**:

- **Linux / macOS / WSL**:
  ```bash
  ./build_switch.sh
  ```
- **Windows (PowerShell with Docker Desktop)**:
  ```powershell
  docker run --rm -v "${PWD}:/work" -w /work devkitpro/devkita64 bash build_switch.sh
  ```
- **Local devkitPro (if installed)**:
  ```bash
  cmake --preset switch-arm64
  cmake --build --preset switch-arm64 --target HarryPotter2
  elf2nso out/switch-arm64/hp2_game.elf out/switch-arm64/main
  ```

This generates:
- `out/switch-arm64/main`: The Switch executable (NSO) for standalone NSP packaging.
- `out/switch-arm64/HarryPotter2.nro`: The homebrew executable.

---

### Step 3: Package the NSP

Run the cross-platform Python builder:

```bash
python scripts/build_nsp.py --game-dir "/path/to/pc/game/files" --keys "/path/to/prod.keys"
```

**Parameters & Options**:
- `--game-dir`: Path to the PC game directory containing `system/`, `Maps/`, `Textures/`, `Sounds/`, etc.
- `--keys`: Path to your dumped `prod.keys`.
- `--hacbrewpack`: (Optional) Explicit path to `hacbrewpack` executable if not in `tools/` or `PATH`.
- `--out-dir`: (Optional) Output directory for the `.nsp` file (defaults to `dist/`).
- `--titleid`: (Optional) Custom Title ID (defaults to `0100485032000000`).

The builder script automatically:
1. Stages the ExeFS (`main`, `main.npdm`) with the required Application permissions and 16 MB stack allocation.
2. Stages RomFS assets using **zero-copy directory junctions** on Windows (or symlinks on Linux) to prevent duplicating large asset files on disk.
3. Generates the Control NCA (with title metadata and 256x256 HOME menu icon).
4. Invokes `hacbrewpack` to create the final signed NSP in `dist/`:
   ```
   dist/Harry Potter and the Chamber of Secrets [0100485032000000][v0].nsp
   ```

*(Alternative)*: On Linux or WSL with Docker, you can run the all-in-one script to build and package in a single command:
```bash
./build_switch_nsp.sh --game-dir "/path/to/pc/game/files" --keys "/path/to/prod.keys"
```

---

### Step 4: Install to Nintendo Switch

1. Connect your Switch to your PC via USB and launch **DBI** on the console.
2. Select **Run MTP Responder**.
3. Open the **MicroSD install** or **NAND install** drive on your PC and drag & drop the generated `.nsp` file.
4. Launch the game from your Switch HOME menu!

---

## Troubleshooting

- **Game crashes at boot or reports missing files**:
  - For **NSP**: Ensure your PC game directory contained valid `system/Default.ini` and all required packages before packaging.
  - For **NRO**: Make sure you launched the Homebrew Launcher in **Title Override** mode (hold `R` while opening any installed game). Applet mode limits available RAM and will cause out-of-memory crashes.
- **Saves not showing up**:
  - In NSP mode, saves are stored in internal Switch NAND per user profile. If you previously played using the NRO, ensure `sdmc:/switch/hp2/User/Save/Slot0/Save0.usa` is present during the first boot so it can be automatically imported.
- **Screen freezes or black screen**:
  - Ensure your Switch firmware and Atmosphere are up to date.

---

## Credits & Acknowledgments

- **Unreal Engine 1** by Epic Games.
- Original game developed by **KnowWonder** / **Electronic Arts** (2002).
- **devkitPro** / **libnx** teams for the Nintendo Switch homebrew toolchain.
- **The-4n** for [hacBrewPack](https://github.com/The-4n/hacBrewPack).
- **Mesa** & **deko3d** contributors for OpenGL on Horizon OS.
- Developed with the assistance of **Google DeepMind's Antigravity** AI assistant.

---

## License

The code modifications and launcher layers are [MIT licensed](LICENSE). Third-party software credits are in [NOTICE.md](NOTICE.md). Original game content and assets are not included; you must supply your own copy.
