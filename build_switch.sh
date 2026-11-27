#!/bin/bash
# Build HarryPotter2.nro for Nintendo Switch.
# If /opt/devkitpro is not installed locally, runs itself inside the
# hp2-devkita64 Docker image: devkitpro/devkita64 plus a Switch Mesa rebuilt
# with GL program binaries enabled (packaging/switch-mesa), which lets the
# game reload its compiled shaders instead of recompiling them every boot.
# The image is built on first use.
set -e

if [ ! -d "/opt/devkitpro" ]; then
    IMAGE=hp2-devkita64
    if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
        echo "Building $IMAGE (devkitA64 + patched Switch Mesa, one-time)..."
        docker build -t "$IMAGE" packaging/switch-mesa
    fi
    echo "Running build inside $IMAGE container..."
    docker run --rm -v "$PWD:/work" -w /work "$IMAGE" ./build_switch.sh "$@"
    exit $?
fi

export DEVKITPRO=/opt/devkitpro
export DEVKITA64=/opt/devkitpro/devkitA64
export PATH=$DEVKITA64/bin:$DEVKITPRO/tools/bin:$PATH

git config --global --add safe.directory "*" 2>/dev/null || true

echo "=== GCC ==="
aarch64-none-elf-g++ --version | head -n 1

echo "=== CMAKE CONFIGURE ==="
cmake --preset switch-arm64 "$@"

echo "=== BUILD HARRY POTTER 2 NRO ==="
cmake --build --preset switch-arm64 --target HarryPotter2

if [ -f "out/switch-arm64/hp2_game.elf" ]; then
    echo "=== GENERATE NSO (main) ==="
    elf2nso out/switch-arm64/hp2_game.elf out/switch-arm64/main
fi

if [ -f "out/switch-arm64/HarryPotter2.nro" ]; then
    echo "=== SUCCESS ==="
    echo "Built NRO: out/switch-arm64/HarryPotter2.nro"
    echo "Built NSO: out/switch-arm64/main"
fi
