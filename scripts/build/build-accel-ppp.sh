#!/bin/bash
# ============================================================================
# RNAS-OpenWrt Build Script
# Builds accel-ppp with full OpenWrt integration
# ============================================================================
# This script builds accel-ppp for OpenWrt with all protocol support
# and RADIUS features. It creates an OpenWrt-compatible package that
# seamlessly integrates into the OpenWrt ecosystem.
#
# Usage:
#   ./scripts/build/build-accel-ppp.sh           # Full build
#   ./scripts/build/build-accel-ppp.sh --sdk DIR  # Use existing SDK
#   ./scripts/build/build-accel-ppp.sh --package  # Package only
# ============================================================================

set -e

# --- Configuration ---------------------------------------------------------
OPENWRT_VERSION="${OPENWRT_VERSION:-23.05}"
ARCH="${ARCH:-x86_64}"
BUILD_DIR="${BUILD_DIR:-$(pwd)/build/accel-ppp}"
OUTPUT_DIR="${OUTPUT_DIR:-$(pwd)/output}"
INSTALL_DIR="${INSTALL_DIR:-${BUILD_DIR}/install}"
SDK_DIR="${SDK_DIR:-${HOME}/openwrt-sdk-${OPENWRT_VERSION}}"
PARALLEL_JOBS="${PARALLEL_JOBS:-$(nproc)}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Prerequisites ---------------------------------------------------------
check_prerequisites() {
    local missing=0

    log_info "Checking build prerequisites..."

    for cmd in git cmake make gcc g++ wget tar xz; do
        if ! command -v "$cmd" &>/dev/null; then
            log_error "Missing: $cmd"
            missing=1
        fi
    done

    # Check for required libraries
    for pkg in libssl-dev libpam0g-dev; do
        if ! dpkg -l "$pkg" &>/dev/null 2>&1; then
            log_warn "Recommended package not found: $pkg"
        fi
    done

    if [ "$missing" -eq 1 ]; then
        log_error "Install missing tools: sudo apt install build-essential cmake git libssl-dev"
        exit 1
    fi

    log_info "All prerequisites satisfied"
}

# --- Fetch accel-ppp source ------------------------------------------------
fetch_source() {
    if [ -d "$BUILD_DIR/src" ]; then
        log_warn "Source directory exists, updating..."
        cd "$BUILD_DIR/src"
        git pull --ff-only 2>/dev/null || true
        return
    fi

    log_info "Cloning accel-ppp source..."
    mkdir -p "$BUILD_DIR"
    git clone --depth 1 \
        https://github.com/accel-ppp/accel-ppp.git \
        "$BUILD_DIR/src"

    cd "$BUILD_DIR/src"
    git submodule update --init --depth 1 2>/dev/null || true
    log_info "Source fetched successfully"
}

# --- Configure build -------------------------------------------------------
configure_build() {
    log_info "Configuring accel-ppp build..."

    mkdir -p "$BUILD_DIR/build"
    cd "$BUILD_DIR/build"

    cmake "$BUILD_DIR/src" \
        -DCMAKE_BUILD_TYPE=Release \
        -DCMAKE_INSTALL_PREFIX="$INSTALL_DIR/usr" \
        -DBUILD_PPPOE=yes \
        -DBUILD_IPOE=yes \
        -DBUILD_L2TP=yes \
        -DBUILD_PPTP=yes \
        -DBUILD_SSTP=yes \
        -DBUILD_RADIUS=yes \
        -DBUILD_VLAN=yes \
        -DBUILD_IPPOOL=yes \
        -DLOG_FILE=yes \
        -DLOG_SYSLOG=yes \
        -DLOG_SQLITE=yes \
        -DLOG_PGSQL=no \
        -DLOG_MYSQL=no \
        -DCRYPTO=openssl \
        -DCPACK_TYPE="openwrt-${OPENWRT_VERSION}"

    log_info "Configuration complete"
    echo "  Build type: Release"
    echo "  Install prefix: ${INSTALL_DIR}"
}

# --- Build -----------------------------------------------------------------
build() {
    log_info "Building accel-ppp with ${PARALLEL_JOBS} parallel jobs..."

    cd "$BUILD_DIR/build"
    make -j"$PARALLEL_JOBS"
    make install

    log_info "Build complete"
}

# --- Create native OpenWrt package directory structure --------------------
create_package_structure() {
    local pkg_dir="$BUILD_DIR/package/accel-ppp"

    log_info "Creating OpenWrt package structure..."

    mkdir -p "$pkg_dir/files/etc/config"
    mkdir -p "$pkg_dir/files/etc/init.d"
    mkdir -p "$pkg_dir/files/etc/uci-defaults"
    mkdir -p "$pkg_dir/files/usr/sbin"
    mkdir -p "$pkg_dir/files/etc/accel-ppp"
    mkdir -p "$pkg_dir/patches"

    # Copy built binaries
    cp "$INSTALL_DIR/usr/sbin/accel-pppd" "$pkg_dir/files/usr/sbin/"
    cp "$INSTALL_DIR/usr/sbin/accel-cmd"  "$pkg_dir/files/usr/sbin/"
    [ -f "$INSTALL_DIR/usr/bin/radclient" ] && \
        cp "$INSTALL_DIR/usr/bin/radclient" "$pkg_dir/files/usr/sbin/"

    log_info "Package structure created at ${pkg_dir}"
}

# --- Create distribution package ------------------------------------------
create_package() {
    log_info "Creating distribution package..."

    mkdir -p "$OUTPUT_DIR"

    # Create tarball for manual deployment
    local tarball="${OUTPUT_DIR}/accel-ppp-${OPENWRT_VERSION}-${ARCH}.tar.gz"
    cd "$INSTALL_DIR"
    tar czf "$tarball" .
    log_info "Package created: ${tarball}"

    # Create comprehensive deployment archive
    local deploy_archive="${OUTPUT_DIR}/rnas-openwrt-deploy-${OPENWRT_VERSION}-${ARCH}.tar.gz"
    mkdir -p /tmp/rnas-pkg

    # Binaries
    cp "$INSTALL_DIR/usr/sbin/accel-pppd" /tmp/rnas-pkg/
    cp "$INSTALL_DIR/usr/sbin/accel-cmd"  /tmp/rnas-pkg/

    # Integration files
    cp -r "$BUILD_DIR/package/accel-ppp/files/"* /tmp/rnas-pkg/

    # Configs
    mkdir -p /tmp/rnas-pkg/configs
    cp -r "$(pwd)/configs/"* /tmp/rnas-pkg/configs/ 2>/dev/null || true

    # Scripts
    mkdir -p /tmp/rnas-pkg/scripts
    cp -r "$(pwd)/scripts/"* /tmp/rnas-pkg/scripts/ 2>/dev/null || true

    cd /tmp/rnas-pkg
    tar czf "$deploy_archive" .
    rm -rf /tmp/rnas-pkg

    log_info "Deployment archive: ${deploy_archive}"
    echo ""
    echo "  Binaries:"
    echo "    - accel-pppd  (core daemon)"
    echo "    - accel-cmd   (control tool)"
    echo "  Integration:"
    echo "    - /etc/config/accel-ppp     (UCI config)"
    echo "    - /etc/init.d/accel-ppp     (procd init)"
    echo "    - /usr/sbin/accel-ppp-uci   (config translator)"
    echo "    - /etc/uci-defaults/accel-ppp (first-boot)"
}

# --- Clean -----------------------------------------------------------------
clean() {
    log_info "Cleaning build artifacts..."
    rm -rf "$BUILD_DIR/build"
    rm -rf "$INSTALL_DIR"
    log_info "Done"
}

clean_all() {
    log_info "Cleaning all artifacts..."
    rm -rf "$BUILD_DIR"
    rm -rf "$OUTPUT_DIR"
    log_info "Done"
}

# --- OpenWrt SDK Build (if SDK available) ---------------------------------
build_sdk() {
    if [ ! -d "$SDK_DIR" ]; then
        log_warn "OpenWrt SDK not found at ${SDK_DIR}"
        log_info "Downloading OpenWrt SDK..."

        mkdir -p "$SDK_DIR"
        cd "$SDK_DIR/.."

        local sdk_url
        case "$ARCH" in
            x86_64)
                sdk_url="https://downloads.openwrt.org/releases/${OPENWRT_VERSION}/targets/x86/64/openwrt-sdk-${OPENWRT_VERSION}-x86-64_gcc-12.3.0_musl.Linux-x86_64.tar.xz"
                ;;
            *)
                log_error "Unsupported architecture: ${ARCH}"
                exit 1
                ;;
        esac

        wget -q "$sdk_url" -O sdk.tar.xz
        tar xf sdk.tar.xz --strip-components=1 -C "$SDK_DIR"
        rm sdk.tar.xz
        log_info "SDK downloaded to ${SDK_DIR}"
    fi

    log_info "Copying accel-ppp package to SDK..."
    cp -r "$BUILD_DIR/package/accel-ppp" "$SDK_DIR/package/"

    log_info "Building with OpenWrt SDK..."
    cd "$SDK_DIR"
    make package/accel-ppp/compile V=s -j"$PARALLEL_JOBS"

    log_info "SDK build complete"
    echo "  Packages: ${SDK_DIR}/bin/packages/"
}

# --- Help ------------------------------------------------------------------
usage() {
    cat << 'EOF'
Usage: build-accel-ppp.sh [OPTIONS]

Build accel-ppp with full OpenWrt integration.

Options:
  --help, -h      Show this help
  --clean         Clean build artifacts
  --clean-all     Clean everything (incl. source)
  --sdk DIR       Build using OpenWrt SDK at DIR
  --package       Package only (skip build)
  --skip-build    Skip build step (package existing)

Environment variables:
  OPENWRT_VERSION  OpenWrt version (default: 23.05)
  ARCH             Target architecture (default: x86_64)
  BUILD_DIR        Build directory
  OUTPUT_DIR       Output directory
  SDK_DIR          OpenWrt SDK directory
  PARALLEL_JOBS    Parallel build jobs
EOF
    exit 0
}

# --- Main ------------------------------------------------------------------
main() {
    local action="full"
    local skip_build=0

    while [ $# -gt 0 ]; do
        case "$1" in
            --help|-h) usage ;;
            --clean) action="clean" ;;
            --clean-all) action="clean_all" ;;
            --sdk) SDK_DIR="$2"; action="sdk"; shift ;;
            --package) action="package" ;;
            --skip-build) skip_build=1 ;;
            *) log_error "Unknown option: $1"; usage ;;
        esac
        shift
    done

    case "$action" in
        clean)
            clean
            exit 0
            ;;
        clean_all)
            clean_all
            exit 0
            ;;
        sdk)
            check_prerequisites
            fetch_source
            configure_build
            build
            create_package_structure
            build_sdk
            ;;
        package)
            create_package_structure
            create_package
            ;;
        full)
            check_prerequisites
            fetch_source
            [ "$skip_build" -eq 1 ] || {
                configure_build
                build
            }
            create_package_structure
            create_package
            log_info "Build completed successfully!"
            ;;
    esac
}

main "$@"
