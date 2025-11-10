#!/bin/bash
# Post-install startup script
# This script runs AFTER all Python and R dependencies are installed during Docker build
# Use this for operations that need dependencies to be installed first
# Examples:
#   - Installing packages that have dependency conflicts
#   - Installing packages that need to be installed in a specific order
#   - Post-installation configuration
#
# If this script fails, the Docker build will abort
#
# This script is OPTIONAL - if it doesn't exist or is empty, the build will continue normally

set -e  # Abort on any error

# Colors for output
GREEN="\033[1;32m"
CYAN="\033[1;36m"
RED="\033[1;31m"
YELLOW="\033[1;33m"
NC="\033[0m" # No Color

echo -e "${CYAN}>> Running post-install script...${NC}"

# Install pyradiomics in the system_python environment
# This is done separately because pyradiomics requires numpy to be installed first,
# and pip may install packages in parallel, causing dependency issues
SYSTEM_PYTHON_VENV="/opt/venvs/system_python"
PYRADIOMICS_VERSION="3.0.1"

if [ ! -d "$SYSTEM_PYTHON_VENV" ]; then
    echo -e "${RED}ERROR: System Python virtual environment not found at $SYSTEM_PYTHON_VENV${NC}"
    exit 1
fi

# Verify numpy is installed (required for pyradiomics build)
echo -e "${CYAN}>> Verifying numpy is installed in system_python...${NC}"
if ! "$SYSTEM_PYTHON_VENV/bin/python" -c "import numpy; print('numpy version:', numpy.__version__)" 2>/dev/null; then
    echo -e "${RED}ERROR: numpy is not installed in system_python. Cannot install pyradiomics.${NC}"
    exit 1
fi
echo -e "${GREEN}>> numpy is available${NC}"

# Install wheel if not already installed (required for building pyradiomics)
echo -e "${CYAN}>> Ensuring wheel is installed...${NC}"
"$SYSTEM_PYTHON_VENV/bin/pip" install --quiet wheel || true

echo -e "${CYAN}>> Installing pyradiomics==${PYRADIOMICS_VERSION} in system_python environment...${NC}"

# Install pyradiomics using pip from the system_python venv
# Use --no-build-isolation so it can use numpy already installed in the venv
if "$SYSTEM_PYTHON_VENV/bin/pip" install --no-build-isolation "pyradiomics==${PYRADIOMICS_VERSION}"; then
    echo -e "${GREEN}>> Successfully installed pyradiomics==${PYRADIOMICS_VERSION}${NC}"
    
    # Verify installation
    if "$SYSTEM_PYTHON_VENV/bin/python" -c "import radiomics; print('pyradiomics version:', radiomics.__version__)" 2>/dev/null; then
        echo -e "${GREEN}>> Verified pyradiomics installation${NC}"
    else
        echo -e "${YELLOW}>> Warning: Could not verify pyradiomics installation${NC}"
    fi
else
    echo -e "${RED}ERROR: Failed to install pyradiomics${NC}"
    exit 1
fi

echo -e "${GREEN}>> Post-install script completed${NC}"

