#!/usr/bin/env bash
set -euo pipefail

DOMAIN="${1:-}"
OUT_DIR="${2:-certs}"

if [ -z "$DOMAIN" ]; then
  echo "Usage: $0 <domain> [out_dir]" >&2
  echo "Example: $0 your-host.example certs" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

CRT="${OUT_DIR%/}/webhook.crt"
KEY="${OUT_DIR%/}/webhook.key"

openssl req -x509 -newkey rsa:2048 \
  -keyout "$KEY" \
  -out "$CRT" \
  -days 365 \
  -nodes \
  -subj "/CN=${DOMAIN}" \
  -addext "subjectAltName=DNS:${DOMAIN}"

echo "Wrote:"
echo "  cert: $CRT"
echo "  key:  $KEY"
