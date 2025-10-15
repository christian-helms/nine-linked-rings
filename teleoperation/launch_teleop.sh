#!/bin/bash
# Launch script for Nine Linked Rings teleoperation
# Usage: ./launch_teleop.sh [OPTIONS]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
RECORD=false
RECORD_DIR="demonstrations"
RECORD_FORMAT="pickle"

# Function to print colored messages
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check prerequisites
check_prerequisites() {
    print_info "Checking prerequisites..."
    
    # Check if uv is available
    if ! command -v uv &> /dev/null; then
        print_error "uv command not found. Please install uv package manager."
        exit 1
    fi
    
    # Check if Manus SDK library path is set
    if [ -z "$LD_LIBRARY_PATH" ]; then
        print_warning "LD_LIBRARY_PATH is not set. Manus SDK may not be found."
        print_warning "Set it with: export LD_LIBRARY_PATH=/path/to/manus_sdk/lib:\$LD_LIBRARY_PATH"
    fi
    
    # Check if scene file exists
    if [ ! -f "../assets/assembled.usda" ]; then
        print_warning "Scene file not found at ../assets/assembled.usda"
    fi
    
    print_success "Prerequisites check complete"
}

# Function to display usage
usage() {
    cat << EOF
Nine Linked Rings Teleoperation Launcher

Usage: $0 [OPTIONS]

Options:
    -r, --record              Enable recording of demonstrations
    -d, --dir DIR            Set recording directory (default: demonstrations)
    -f, --format FORMAT      Set recording format: pickle|json|npz (default: pickle)
    -h, --help               Display this help message

Examples:
    # Basic teleoperation without recording
    $0

    # Teleoperation with recording
    $0 --record

    # Custom recording settings
    $0 --record --dir my_demos --format npz

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -r|--record)
            RECORD=true
            shift
            ;;
        -d|--dir)
            RECORD_DIR="$2"
            shift 2
            ;;
        -f|--format)
            RECORD_FORMAT="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Display banner
echo ""
echo "╔═══════════════════════════════════════════════════════════╗"
echo "║        Nine Linked Rings Teleoperation Launcher          ║"
echo "╚═══════════════════════════════════════════════════════════╝"
echo ""

# Check prerequisites
check_prerequisites

# Build command
CMD="uv run teleoperation/teleop_nine_rings.py --xr"

if [ "$RECORD" = true ]; then
    CMD="$CMD --record --record_dir $RECORD_DIR --record_format $RECORD_FORMAT"
    print_info "Recording enabled"
    print_info "  Directory: $RECORD_DIR"
    print_info "  Format: $RECORD_FORMAT"
    
    # Create recording directory if it doesn't exist
    mkdir -p "$RECORD_DIR"
else
    print_info "Recording disabled (practice mode)"
fi

echo ""
print_info "Hardware checklist:"
echo "  - Manus gloves connected and calibrated"
echo "  - Vive trackers attached to wrists"
echo "  - SteamVR running with trackers visible"
echo "  - VR headset (optional)"
echo ""

print_info "Gesture controls:"
echo "  - START: Begin teleoperation and recording"
echo "  - STOP: End teleoperation and save recording"
echo "  - RESET: Reset environment"
echo ""

read -p "Press ENTER to launch teleoperation (Ctrl+C to cancel)..."
echo ""

# Launch teleoperation
print_info "Launching teleoperation..."
print_info "Command: $CMD"
echo ""

cd /home/chris/nine-linked-rings
eval $CMD

# Cleanup message
echo ""
print_success "Teleoperation session ended"

if [ "$RECORD" = true ]; then
    print_info "Recordings saved in: $RECORD_DIR"
    
    # List recordings
    if [ -d "$RECORD_DIR" ]; then
        NUM_FILES=$(ls -1 "$RECORD_DIR" 2>/dev/null | wc -l)
        if [ "$NUM_FILES" -gt 0 ]; then
            print_success "Total recordings: $NUM_FILES"
            print_info "View with: uv run teleoperation/demo_viewer.py $RECORD_DIR/<filename>"
        fi
    fi
fi

echo ""

