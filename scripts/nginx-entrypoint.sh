#!/bin/bash
set -e

# User-specified CERT_DIR is mapped to /etc/ssl in container
CERT_DIR="${CERT_DIR:-/etc/ssl}"

# Detect certificate and key files (.pem, .crt, .key)
CERT_FILE=$(find "$CERT_DIR" -type f \( -name "*.pem" -o -name "*.crt" \) | grep -E "cert|fullchain" | head -n 1)
KEY_FILE=$(find "$CERT_DIR" -type f \( -name "*.pem" -o -name "*.key" \) | grep -E "key|privkey" | head -n 1)

export SSL_CERTIFICATE="${CERT_FILE}"
export SSL_CERTIFICATE_KEY="${KEY_FILE}"

if [[ -z "$SSL_CERTIFICATE" || -z "$SSL_CERTIFICATE_KEY" ]]; then
    echo "No SSL certificate or key found." >&2
    echo "Place [cert|fullchain].[pem|crt] and [key|privkey].[pem|key] in /etc/xbat/certs or location specified by --certificate-dir option during installation." >&2
    exit 1
fi

echo "Using SSL Certificate: $SSL_CERTIFICATE"
echo "Using SSL Key: $SSL_CERTIFICATE_KEY"

# TODO maybe use envsubst https://serverfault.com/questions/577370/how-can-i-use-environment-variables-in-nginx-conf
cp /etc/nginx/nginx.conf.in /etc/nginx/nginx.conf

sed -i "s!#SSL_CERTIFICATE#!$SSL_CERTIFICATE!" /etc/nginx/nginx.conf
sed -i "s!#SSL_CERTIFICATE_KEY#!$SSL_CERTIFICATE_KEY!" /etc/nginx/nginx.conf


# Start nginx
exec nginx -g "daemon off;"
