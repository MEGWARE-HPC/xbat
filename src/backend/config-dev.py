"""
Development Gunicorn configuration.
"""

import tempfile
from datetime import datetime, timedelta
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa

wsgi_app = "restapi:create_app()"
bind = "0.0.0.0:7000"
workers = 4
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 15
keepalive = 30
preload_app = False
reload = False
errorlog = "-"
loglevel = "debug"
accesslog = "-"
capture_output = True


def generate_self_signed_cert():
    """Generate a self-signed certificate using cryptography module."""
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

    subject = x509.Name([
        x509.NameAttribute(NameOID.COMMON_NAME, "localhost"),
    ])
    cert = (x509.CertificateBuilder().subject_name(subject).issuer_name(
        subject).public_key(key.public_key()).serial_number(
            x509.random_serial_number()).not_valid_before(
                datetime.utcnow()).not_valid_after(datetime.utcnow() +
                                                   timedelta(days=365)).sign(
                                                       key, hashes.SHA256()))

    key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".key")
    cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".crt")

    key_file.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()))
    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))

    key_file.close()
    cert_file.close()

    return cert_file.name, key_file.name


certfile = "../../dev/certs/cert.pem"
keyfile = "../../dev/certs/key.pem"

# Uncomment the following line to use a self-signed auto-generated certificate instead
# certfile, keyfile = generate_self_signed_cert()


def worker_abort(worker):
    worker.log.info("WORKERABORT worker received SIGABRT signal")
    raise Exception(f"Gunicorn worker aborted: {worker}")
