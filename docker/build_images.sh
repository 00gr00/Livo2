#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

CORE_IMAGE="${CORE_IMAGE:-livo2-core:dev}"
MVS_IMAGE="${MVS_IMAGE:-livo2-mvs:dev}"
REBUILD_FROM_ZERO="${REBUILD_FROM_ZERO:-false}"
BUILD_CORE_ONLY="${BUILD_CORE_ONLY:-false}"
USE_NO_CACHE="${USE_NO_CACHE:-false}"
MVS_SDK_PATH="${MVS_SDK_PATH:-/opt/MVS}"

NO_CACHE_ARGS=()
if [[ "${USE_NO_CACHE}" == "true" ]]; then
  NO_CACHE_ARGS+=(--no-cache)
fi

echo "Project root: ${ROOT_DIR}"
echo "Core image:   ${CORE_IMAGE}"
echo "MVS image:    ${MVS_IMAGE}"
echo "MVS SDK path: ${MVS_SDK_PATH}"

if [[ "${REBUILD_FROM_ZERO}" == "true" ]]; then
  echo "[1/4] Pruning Docker builder cache..."
  docker builder prune -af
else
  echo "[1/4] Skipping builder cache prune."
fi

echo "[2/4] Building core image..."
docker build \
  "${NO_CACHE_ARGS[@]}" \
  -f "${ROOT_DIR}/docker/Dockerfile" \
  -t "${CORE_IMAGE}" \
  "${ROOT_DIR}"

if [[ "${BUILD_CORE_ONLY}" == "true" ]]; then
  echo "[3/4] BUILD_CORE_ONLY=true, skipping MVS image build."
  echo "Done."
  exit 0
fi

if [[ ! -d "${MVS_SDK_PATH}" ]]; then
  echo "ERROR: MVS SDK path not found: ${MVS_SDK_PATH}" >&2
  exit 1
fi

echo "[3/4] Building MVS image..."
docker build \
  "${NO_CACHE_ARGS[@]}" \
  -f "${ROOT_DIR}/docker/Dockerfile.mvs" \
  --build-context "mvs_sdk=${MVS_SDK_PATH}" \
  --build-arg "CORE_IMAGE=${CORE_IMAGE}" \
  -t "${MVS_IMAGE}" \
  "${ROOT_DIR}"

echo "[4/4] Build summary"
docker images "${CORE_IMAGE}"
docker images "${MVS_IMAGE}"

echo "Done."

