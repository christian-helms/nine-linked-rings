#!/usr/bin/env bash
set -euo pipefail

# CloudXR Runtime launcher script
# Usage:
#   ./start_cloudxr_runtime.sh            # starts in background (detached)
#   CXR_ATTACH=1 ./start_cloudxr_runtime.sh  # starts attached (foreground)

CONTAINER_NAME="${CXR_CONTAINER_NAME:-cloudxr-runtime}"
IMAGE="${CXR_IMAGE:-nvcr.io/nvidia/cloudxr-runtime:5.0.1}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ISAACLAB_DIR="${ISAACLAB_DIR:-$SCRIPT_DIR}"
OPENXR_DIR="${CXR_OPENXR_DIR:-$SCRIPT_DIR/openxr}"

if [ ! -d "$OPENXR_DIR" ]; then
  echo "ERROR: OpenXR directory not found: $OPENXR_DIR" >&2
  echo "Create it or set CXR_OPENXR_DIR to the correct path." >&2
  exit 1
fi

# Remove existing container if present
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker rm -f "$CONTAINER_NAME" >/dev/null
fi

# Ensure image is present
docker pull -q "$IMAGE" >/dev/null || true

# Run detached by default; set CXR_ATTACH=1 to run attached
DETACH_FLAG="-d"
if [ "${CXR_ATTACH:-0}" = "1" ]; then
  DETACH_FLAG=""
fi

docker run $DETACH_FLAG \
  --name "$CONTAINER_NAME" \
  --runtime=nvidia --gpus=all \
  -e ACCEPT_EULA=Y \
  -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility,compute,display,video \
  -e XDG_RUNTIME_DIR=/openxr/run \
  -e XR_RUNTIME_JSON=/openxr/share/openxr/1/openxr_cloudxr.json \
  -e VK_ICD_FILENAMES=/usr/share/vulkan/icd.d/nvidia_icd.json \
  -e LD_PRELOAD=/usr/lib/x86_64-linux-gnu/libvulkan.so.1 \
  --mount type=bind,src="$OPENXR_DIR",dst=/openxr \
  --mount type=bind,src=/usr/share/vulkan,dst=/usr/share/vulkan,ro \
  --mount type=bind,src=/usr/share/vulkan/icd.d,dst=/usr/share/vulkan/icd.d,ro \
  --mount type=bind,src=/usr/lib/x86_64-linux-gnu/libvulkan.so.1,dst=/usr/lib/x86_64-linux-gnu/libvulkan.so.1,ro \
  -p 48010:48010 \
  -p 47998:47998/udp \
  -p 47999:47999/udp \
  -p 48000:48000/udp \
  -p 48005:48005/udp \
  -p 48008:48008/udp \
  -p 48012:48012/udp \
  "$IMAGE"

echo "CloudXR runtime started as container '$CONTAINER_NAME'."
if [ -n "$DETACH_FLAG" ]; then
  echo "Follow logs: docker logs -f $CONTAINER_NAME"
fi
