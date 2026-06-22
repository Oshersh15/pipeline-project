#!/bin/bash

set -e

echo "Removing MongoDB container..."

podman stop asset-publish-mongo 2>/dev/null || true
podman rm asset-publish-mongo 2>/dev/null || true

echo "Creating fresh MongoDB container..."

podman run -d \
    --name asset-publish-mongo \
    -p 27017:27017 \
    docker.io/library/mongo:7

echo "MongoDB reset complete."
podman ps
