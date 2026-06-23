#!/usr/bin/env bash
# ════════════════════════════════════════════════════════════════════════════
# RepoDoc Pro — Universal Linux Setup Script
# Detects distro, lets user pick the package manager, installs everything.
# Supports: Debian/Ubuntu (apt), Arch/Manjaro (pacman), Fedora/RHEL (dnf/yum),
#           openSUSE (zypper), Alpine (apk), Void (xbps), Gentoo (emerge)
# ════════════════════════════════════════════════════════════════════════════

set -euo pipefail

# ─── Colors ────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; BOLD='\033[1m'; NC='\033[0m'

info()  { echo -e "${BLUE}ℹ${NC}  $1"; }
ok()    { echo -e "${GREEN}✅${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠️${NC}  $1"; }
err()   { echo -e "${RED}❌${NC} $1"; }
hdr()   { echo -e "\n${BOLD}${CYAN}━━━ $1 ━━━${NC}\n"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"
BACKEND_DIR="$REPO_ROOT/backend"
ELECTRON_DIR="$REPO_ROOT/electron"

hdr "RepoDoc Pro — Universal Linux Setup"

# ════════════════════════════════════════════════════════════════════════════
# STEP 1 — Detect the Linux distribution
# ════════════════════════════════════════════════════════════════════════════

DISTRO_ID=""
DISTRO_NAME=""
PKG_MANAGER=""

detect_distro() {
    if [ -f /etc/os-release ]; then
        # shellcheck disable=SC1091
        . /etc/os-release
        DISTRO_ID="${ID:-unknown}"
        DISTRO_NAME="${PRETTY_NAME:-$ID}"
        DISTRO_LIKE="${ID_LIKE:-}"
    elif [ -f /etc/arch-release ]; then
        DISTRO_ID="arch"
        DISTRO_NAME="Arch Linux"
    elif [ -f /etc/redhat-release ]; then
        DISTRO_ID="rhel"
        DISTRO_NAME=$(cat /etc/redhat-release)
    else
        DISTRO_ID="unknown"
        DISTRO_NAME="Unknown Linux"
    fi
}

detect_distro
info "Detected distribution: ${BOLD}${DISTRO_NAME}${NC} (id: $DISTRO_ID)"

# ════════════════════════════════════════════════════════════════════════════
# STEP 2 — Detect available package managers, let user pick if multiple
# ════════════════════════════════════════════════════════════════════════════

declare -a AVAILABLE_PMS=()

command -v pacman  &>/dev/null && AVAILABLE_PMS+=("pacman")
command -v apt-get &>/dev/null && AVAILABLE_PMS+=("apt")
command -v dnf     &>/dev/null && AVAILABLE_PMS+=("dnf")
command -v yum     &>/dev/null && AVAILABLE_PMS+=("yum")
command -v zypper  &>/dev/null && AVAILABLE_PMS+=("zypper")
command -v apk     &>/dev/null && AVAILABLE_PMS+=("apk")
command -v xbps-install &>/dev/null && AVAILABLE_PMS+=("xbps")
command -v emerge  &>/dev/null && AVAILABLE_PMS+=("emerge")
command -v eopkg   &>/dev/null && AVAILABLE_PMS+=("eopkg")
command -v nix-env &>/dev/null && AVAILABLE_PMS+=("nix")

if [ ${#AVAILABLE_PMS[@]} -eq 0 ]; then
    err "No supported package manager found on this system."
    warn "Skipping system dependency installation — you may need to install"
    warn "Python 3.10+, Node.js 18+, and PDF rendering libs (pango/cairo) manually."
    PKG_MANAGER="none"
elif [ ${#AVAILABLE_PMS[@]} -eq 1 ]; then
    PKG_MANAGER="${AVAILABLE_PMS[0]}"
    ok "Using package manager: ${BOLD}${PKG_MANAGER}${NC}"
else
    # ── Multiple package managers found — let the user choose ──
    hdr "Multiple Package Managers Detected"
    echo "Found the following package managers on your system:"
    echo ""
    for i in "${!AVAILABLE_PMS[@]}"; do
        echo -e "  ${CYAN}$((i+1)))${NC} ${AVAILABLE_PMS[$i]}"
    done
    echo -e "  ${CYAN}$((${#AVAILABLE_PMS[@]}+1)))${NC} Skip system package installation"
    echo ""
    read -rp "$(echo -e "${BOLD}Choose a package manager [1-$((${#AVAILABLE_PMS[@]}+1))]: ${NC}")" choice

    if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#AVAILABLE_PMS[@]}" ]; then
        PKG_MANAGER="${AVAILABLE_PMS[$((choice-1))]}"
    else
        PKG_MANAGER="none"
        warn "Skipping system package installation."
    fi
    ok "Selected: ${BOLD}${PKG_MANAGER}${NC}"
fi

# ════════════════════════════════════════════════════════════════════════════
# STEP 3 — Install system dependencies via chosen package manager
# ════════════════════════════════════════════════════════════════════════════

SUDO=""
if [ "$(id -u)" -ne 0 ]; then
    if command -v sudo &>/dev/null; then
        SUDO="sudo"
    else
        warn "Not root and 'sudo' not found — system package install may fail."
    fi
fi

install_system_deps() {
    hdr "Installing System Dependencies ($PKG_MANAGER)"

    case "$PKG_MANAGER" in
        pacman)
            $SUDO pacman -Sy --noconfirm --needed \
                python python-pip python-virtualenv \
                nodejs npm \
                pango cairo gdk-pixbuf2 libffi \
                ttf-liberation noto-fonts \
                base-devel
            ;;

        apt)
            $SUDO apt-get update -qq
            $SUDO apt-get install -y -qq \
                python3 python3-pip python3-venv \
                nodejs npm \
                libpango-1.0-0 libpangocairo-1.0-0 libcairo2 \
                libgdk-pixbuf2.0-0 libffi-dev \
                fonts-liberation fonts-dejavu \
                build-essential
            ;;

        dnf)
            $SUDO dnf install -y \
                python3 python3-pip python3-virtualenv \
                nodejs npm \
                pango cairo gdk-pixbuf2 libffi-devel \
                liberation-fonts dejavu-sans-fonts \
                gcc gcc-c++ make
            ;;

        yum)
            $SUDO yum install -y \
                python3 python3-pip \
                nodejs npm \
                pango cairo gdk-pixbuf2 libffi-devel \
                liberation-fonts \
                gcc gcc-c++ make
            ;;

        zypper)
            $SUDO zypper --non-interactive install \
                python3 python3-pip python3-virtualenv \
                nodejs npm \
                pango cairo gdk-pixbuf libffi-devel \
                liberation-fonts \
                gcc gcc-c++ make
            ;;

        apk)
            $SUDO apk add --no-cache \
                python3 py3-pip py3-virtualenv \
                nodejs npm \
                pango cairo gdk-pixbuf libffi-dev \
                font-liberation \
                build-base
            ;;

        xbps)
            $SUDO xbps-install -Sy \
                python3 python3-pip python3-virtualenv \
                nodejs \
                pango cairo gdk-pixbuf libffi-devel \
                liberation-fonts-ttf \
                base-devel
            ;;

        emerge)
            $SUDO emerge --ask=n \
                dev-lang/python dev-python/pip \
                net-libs/nodejs \
                x11-libs/pango x11-libs/cairo gdk-pixbuf \
                dev-libs/libffi
            ;;

        eopkg)
            $SUDO eopkg install -y \
                python3 python3-pip \
                nodejs \
                pango cairo gdk-pixbuf libffi-devel
            ;;

        nix)
            nix-env -iA nixpkgs.python3 nixpkgs.nodejs nixpkgs.pango nixpkgs.cairo nixpkgs.libffi
            ;;

        none)
            warn "Skipped — please ensure Python 3.10+, Node.js 18+, pango, and cairo are installed manually."
            return
            ;;

        *)
            err "Unsupported package manager: $PKG_MANAGER"
            return
            ;;
    esac

    ok "System dependencies installed via $PKG_MANAGER"
}

if [ "$PKG_MANAGER" != "none" ]; then
    read -rp "$(echo -e "${BOLD}Install system dependencies now? [Y/n]: ${NC}")" confirm
    confirm="${confirm:-Y}"
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
        install_system_deps
    else
        warn "Skipping system dependency installation."
    fi
fi

# ════════════════════════════════════════════════════════════════════════════
# STEP 4 — Verify Python version
# ════════════════════════════════════════════════════════════════════════════

hdr "Verifying Python"

PYTHON_BIN=""
for candidate in python3.12 python3.11 python3.10 python3 python; do
    if command -v "$candidate" &>/dev/null; then
        PYTHON_BIN="$candidate"
        break
    fi
done

if [ -z "$PYTHON_BIN" ]; then
    err "No Python interpreter found. Please install Python 3.10+ and re-run."
    exit 1
fi

PY_VERSION=$("$PYTHON_BIN" --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 10 ]; }; then
    err "Python 3.10+ required. Found: $PY_VERSION ($PYTHON_BIN)"
    exit 1
fi
ok "Using $PYTHON_BIN — version $PY_VERSION"

# ════════════════════════════════════════════════════════════════════════════
# STEP 5 — Backend virtual environment
# ════════════════════════════════════════════════════════════════════════════

hdr "Setting Up Python Backend"

cd "$BACKEND_DIR"

if [ ! -d ".venv" ]; then
    info "Creating virtual environment..."
    "$PYTHON_BIN" -m venv .venv
fi

# shellcheck disable=SC1091
source .venv/bin/activate
ok "Virtual environment activated"

pip install --upgrade pip -q
info "Installing Python packages (this may take a minute)..."
pip install -r requirements.txt -q
ok "Python packages installed"

# ── Create .env if missing ──
if [ ! -f ".env" ]; then
    cat > .env << 'ENVEOF'
# RepoDoc Pro Backend — Environment Configuration
REPODOC_ENV=development
REPODOC_PORT=8765
REPODOC_LOG_LEVEL=INFO
REPODOC_TEMP_DIR=/tmp/repodoc

# AI Documentation is OPTIONAL — leave blank to disable.
# ANTHROPIC_API_KEY=sk-ant-...
# OPENAI_API_KEY=sk-...
ENVEOF
    ok "Created backend/.env"
else
    info "backend/.env already exists — leaving untouched"
fi

# ════════════════════════════════════════════════════════════════════════════
# STEP 6 — Node.js / Electron frontend (optional)
# ════════════════════════════════════════════════════════════════════════════

hdr "Frontend Setup (Electron + React)"

if command -v node &>/dev/null && command -v npm &>/dev/null; then
    NODE_VERSION=$(node --version)
    ok "Node.js found: $NODE_VERSION"

    read -rp "$(echo -e "${BOLD}Install Electron frontend dependencies? [Y/n]: ${NC}")" confirm_fe
    confirm_fe="${confirm_fe:-Y}"
    if [[ "$confirm_fe" =~ ^[Yy]$ ]]; then
        cd "$ELECTRON_DIR"
        npm install
        ok "Frontend dependencies installed"
    fi
else
    warn "Node.js/npm not found. Frontend setup skipped."
    warn "Install Node.js 18+ to use the Electron desktop app, or run the backend standalone as a REST API."
fi

# ════════════════════════════════════════════════════════════════════════════
# STEP 7 — Run tests (optional)
# ════════════════════════════════════════════════════════════════════════════

cd "$BACKEND_DIR"
read -rp "$(echo -e "${BOLD}Run backend test suite now? [y/N]: ${NC}")" run_tests
run_tests="${run_tests:-N}"
if [[ "$run_tests" =~ ^[Yy]$ ]]; then
    hdr "Running Backend Tests"
    pytest tests/ -x -q --no-header || warn "Some tests failed — check output above"
fi

# ════════════════════════════════════════════════════════════════════════════
# Done
# ════════════════════════════════════════════════════════════════════════════

hdr "Setup Complete! 🚀"

echo -e "${BOLD}Start the backend:${NC}"
echo "  cd backend"
echo "  source .venv/bin/activate"
echo "  python src/main.py --port 8765 --reload"
echo ""
echo -e "${BOLD}Verify it's running:${NC}"
echo "  curl http://localhost:8765/health"
echo ""
if command -v node &>/dev/null; then
    echo -e "${BOLD}Start the frontend (separate terminal):${NC}"
    echo "  cd electron"
    echo "  npm run dev:renderer"
    echo ""
fi
echo -e "${CYAN}Distro:${NC} $DISTRO_NAME"
echo -e "${CYAN}Package manager used:${NC} $PKG_MANAGER"
echo -e "${CYAN}Python:${NC} $PYTHON_BIN ($PY_VERSION)"
echo ""
