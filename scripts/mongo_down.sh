#!/bin/bash

set -e

echo "Stopping MongoDB container..."
podman stop asset-publish-mongo

echo "MongoDB stopped."
