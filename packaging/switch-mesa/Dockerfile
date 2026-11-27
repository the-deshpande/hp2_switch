# devkitA64 image with a Switch Mesa that exposes GL program binaries.
#
# devkitPro's switch-mesa (20.1.0-rc3, pkgrel 5) is built without the disk
# shader cache, and Mesa only advertises GL_ARB_get_program_binary when that
# cache exists. Without program binaries every boot recompiles all shaders
# (~7.5 s for the 44 XOpenGL programs). This image rebuilds the same Mesa
# with devkitPro's own patches plus hp2-program-binary.patch, which exposes
# program binaries without the cache, so XOpenGL can store linked programs on
# the SD card and reload them on the next boot.
#
# Built and used automatically by build_switch.sh (image tag hp2-devkita64).
FROM devkitpro/devkita64:latest

RUN apt-get update \
 && apt-get install -y --no-install-recommends python3-mako python3-pip bison flex pkg-config xz-utils curl ca-certificates \
 && pip3 install --break-system-packages meson==0.56.2 \
 && rm -rf /var/lib/apt/lists/*

# Same source and checksum as devkitPro's PKGBUILD (switch/mesa, pkgrel 5).
ARG MESA_URL=https://archive.mesa3d.org/older-versions/20.x/mesa-20.1.0-rc3.tar.xz
ARG MESA_SHA256=c90b75ea34302ebde9b81b87c5642fa864c40fe9c4ad34ce0793170c1413168d

COPY switch-mesa-20.1.0-5.patch gl_XML.py.patch glX_XML.py.patch hp2-program-binary.patch /mesa/

RUN set -eux; \
    cd /mesa; \
    curl -fsSL "$MESA_URL" -o mesa.tar.xz; \
    echo "$MESA_SHA256  mesa.tar.xz" | sha256sum -c -; \
    tar xf mesa.tar.xz; \
    cd mesa-20.1.0-rc3; \
    patch -p1 -i ../switch-mesa-20.1.0-5.patch; \
    patch -p1 -i ../gl_XML.py.patch; \
    patch -p1 -i ../glX_XML.py.patch; \
    patch -p1 -i ../hp2-program-binary.patch; \
    export DEVKITPRO=/opt/devkitpro; \
    /opt/devkitpro/meson-cross.sh switch ../crossfile.txt build -Db_ndebug=true; \
    ninja -C build; \
    ninja -C build install; \
    sed -i "s,-lEGL ,-lEGL -ldrm_nouveau ," /opt/devkitpro/portlibs/switch/lib/pkgconfig/egl.pc; \
    cd /; rm -rf /mesa
