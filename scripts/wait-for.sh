#!/bin/sh

set -e

host=$(printf "%s\n" "$1" | cut -d : -f 1)
port=$(printf "%s\n" "$1" | cut -d : -f 2)
shift

timeout=30
while ! nc -z "$host" "$port"; do
    timeout=$((timeout-1))
    if [ $timeout -eq 0 ]; then
        echo "Timeout waiting for $host:$port"
        exit 1
    fi
    sleep 1
done

exec "$@"