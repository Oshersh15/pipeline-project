#!/bin/bash

set -e

if ! podman container exists asset-publish-mongo 2>/dev/null; then
    echo "Creating MongoDB container..."
    podman run -d \
        --name asset-publish-mongo \
        -p 27017:27017 \
        docker.io/library/mongo:7
else
    echo "Starting existing MongoDB container..."
    podman start asset-publish-mongo
fi

echo "MongoDB is running."
podman ps
