#!/bin/bash
# RNAS-OpenWrt Build Script
# Builds accel-ppp for OpenWrt with musl libc

set -e

# Configuration
OPENWRT_VERSION="23.05"
ARCH="x86_64"
TOOLCHAIN_DIR="${HOME}/openwrt-sdk-${OPENWRT_VERSION}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v git &> /dev/null; then
        log_error "git is required but not installed"
        exit 1
    fi
    
    if ! command -v cmake &> /dev/null; then
        log_error "cmake is required but not installed"
        exit 1
    fi
    
    if ! command -v make &> /dev/null; then
        log_error "make is required but not installed"
        exit 1
    fi
    
    log_info "All prerequisites satisfied"
}

# Clone accel-ppp
clone_accel_ppp() {
    local build_dir="${1:-$(pwd)/accel-ppp-build}"
    
    if [ -d "$build_dir" ]; then
        log_warn "Build directory exists, using existing clone"
    else
        log_info "Cloning accel-ppp..."
        git clone https://github.com/accel-ppp/accel-ppp.git "$build_dir"
    fi
    
    cd "$build_dir"
    git submodule update --init
}

# Configure build with CMake
configure_build() {
    local build_type="${1:-Release}"
    local install_prefix="${2:-$(pwd)/install}"
    
    log_info "Configuring build..."
    
    mkdir -p build
    cd build
    
    cmake .. \
        -DCMAKE_BUILD_TYPE="$build_type" \
        -DCMAKE_INSTALL_PREFIX="$install_prefix" \
        -DBUILD_IPOE=yes \
        -DBUILD_L2TP=yes \
        -DBUILD_PPTP=yes \
        -DBUILD_SSTP=yes \
        -DBUILD_PPPOE=yes \
        -DDEFAULT_CONFIG_DIR=/etc/accel-ppp \
        -DLOG_PGSQL=no \
        -DLOG_MYSQL=no \
        -DLOG_SQLITE=yes \
        -DLOG_PGSQL=no \
        -DLOG_MYSQL=no \
        -DLOG_FILE=yes \
        -DCPACK_TYPE="${OPENWRT_VERSION}"
    
    log_info "Configuration complete"
}

# Build
build() {
    local cores=$(nproc)
    
    log_info "Building with $cores cores..."
    make -j"$cores"
    make -j"$cores" accel-pppd
    make -j"$cores" accel-cmd
}

# Create package
create_package() {
    local output_dir="${1:-$(pwd)/output}"
    local install_dir="$(pwd)/install"
    
    log_info "Creating package..."
    
    mkdir -p "$output_dir"
    mkdir -p "$install_dir"
    
    make install DESTDIR="$install_dir"
    
    # Create tarball
    cd "$install_dir"
    tar czf "$output_dir/accel-ppp-${OPENWRT_VERSION}-${ARCH}.tar.gz" *
    
    log_info "Package created: $output_dir/accel-ppp-${OPENWRT_VERSION}-${ARCH}.tar.gz"
}

# Main
main() {
    local action="${1:-all}"
    local build_dir="${2:-$(pwd)/accel-ppp-build}"
    
    case "$action" in
        clone)
            check_prerequisites
            clone_accel_ppp "$build_dir"
            ;;
        configure)
            configure_build
            ;;
        build)
            build
            ;;
        package)
            create_package
            ;;
        all)
            check_prerequisites
            clone_accel_ppp "$build_dir"
            configure_build
            build
            create_package
            ;;
        help|--help|-h)
            echo "Usage: $0 [action] [build_dir]"
            echo ""
            echo "Actions:"
            echo "  clone       - Clone accel-ppp repository"
            echo "  configure   - Configure build"
            echo "  build       - Build accel-ppp"
            echo "  package     - Create distribution package"
            echo "  all         - Run all steps (default)"
            echo "  help        - Show this help"
            ;;
        *)
            log_error "Unknown action: $action"
            exit 1
            ;;
    esac
}

main "$@"
