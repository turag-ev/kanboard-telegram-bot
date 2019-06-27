#!/bin/sh
set -e

# Copy default config if not exists
if [ ! -r /var/bot-data/config.json ]; then
    echo "Creating default config.json ..."
    cp default_config.json /var/bot-data/config.json
fi

# Run payload (CMD in Dockerfile)
exec "$@"
