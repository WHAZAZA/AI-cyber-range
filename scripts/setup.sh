#!/usr/bin/env bash
set -e

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "==========================================="
echo "  LLM OWASP Labs - Environment Setup"
echo "==========================================="
echo "[*] Project root: $ROOT_DIR"

# --- Helper: detect sudo usage ---
if [ "$(id -u)" -eq 0 ]; then
  SUDO=""
else
  SUDO="sudo"
fi

# --- 1. Check we are on a Debian/Ubuntu-like system ---
if ! command -v apt-get >/dev/null 2>&1; then
  echo "[!] This setup script currently supports only Debian/Ubuntu (apt-get)."
  echo "    Install Docker, docker-compose-plugin, Python3, pip3, and venv manually, then rerun."
  exit 1
fi

echo "[*] Updating package index..."
$SUDO apt-get update -y

# --- 2. Install Python & pip & venv ---
echo "[*] Installing Python3, pip3, and venv (if not already present)..."
$SUDO apt-get install -y python3 python3-pip python3-venv

# --- 3. Install Docker Engine & Compose plugin ---
echo "[*] Installing Docker Engine and docker-compose plugin..."
$SUDO apt-get install -y docker.io docker-compose-plugin

echo "[*] Enabling and starting Docker service (if systemd is present)..."
if command -v systemctl >/dev/null 2>&1; then
  $SUDO systemctl enable docker || true
  $SUDO systemctl start docker || true
fi

# --- 4. Add current user to docker group (for non-sudo docker usage) ---
echo "[*] Adding user '$USER' to 'docker' group (if not already)..."
$SUDO groupadd -f docker
$SUDO usermod -aG docker "$USER" || true

echo "[*] NOTE: You may need to log out and log back in for docker group changes to apply."
echo "          Until then, you might still need 'sudo' for docker commands."

# --- 5. Python virtual environment for controller + tooling ---
VENV_DIR="$ROOT_DIR/.venv"

if [ ! -d "$VENV_DIR" ]; then
  echo "[*] Creating Python virtual environment at $VENV_DIR..."
  python3 -m venv "$VENV_DIR"
else
  echo "[*] Virtual environment already exists at $VENV_DIR."
fi

echo "[*] Activating virtual environment and installing Python dependencies..."
# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

# Common requirements (controller + lab apps)
REQ_FILE="$ROOT_DIR/common/requirements.txt"
if [ -f "$REQ_FILE" ]; then
  pip install --upgrade pip
  pip install -r "$REQ_FILE"
else
  echo "[!] WARNING: $REQ_FILE not found. Skipping Python deps from common/requirements.txt."
fi

# Controller-specific extras (if any)
pip install pyyaml rich InquirerPy pyfiglet >/dev/null 2>&1 || true

# --- 6. Build base Docker image used by all labs ---
BASE_DOCKERFILE="$ROOT_DIR/common/base.Dockerfile"
if [ -f "$BASE_DOCKERFILE" ]; then
  echo "[*] Building base Docker image: llm-labs-base:latest"
  $SUDO docker build -t llm-labs-base:latest -f "$BASE_DOCKERFILE" "$ROOT_DIR"
else
  echo "[!] WARNING: Base Dockerfile not found at $BASE_DOCKERFILE. Skipping base image build."
fi

echo "==========================================="
echo "[✓] Setup complete."
echo "-------------------------------------------"
echo "Next steps:"
echo "  1) If this is your first time in the 'docker' group, LOG OUT and LOG IN again"
echo "     (or reboot) so docker commands work without sudo."
echo "  2) Activate the virtualenv when working on the project:"
echo "        source \"$VENV_DIR/bin/activate\""
echo "  3) Run the controller:"
echo "        cd \"$ROOT_DIR\" && python3 scripts/labctl.py"
echo "==========================================="
