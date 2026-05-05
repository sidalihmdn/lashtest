import os
import platform
import certifi

_SYSTEM_CA_PATHS = {
    "Darwin": [
        "/usr/local/etc/openssl/cert.pem",
        "/usr/local/ssl/cert.pem",
        "/etc/ssl/cert.pem"
    ],
    "Linux": [
        "/etc/ssl/certs/ca-certificates.crt",
        "/etc/pki/tls/certs/ca-bundle.crt",
        "/etc/ssl/certs/ca-bundle.crt",
        "/etc/pki/ca-trust/extracted/pem/tls-ca-bundle.pem"
    ]
}

def find_system_ca_bundle() -> str:
    system = platform.system()
    paths = _SYSTEM_CA_PATHS.get(system, [])
    for path in paths:
        if os.path.exists(path):
            return path
    return certifi.where()  # Fallback to certifi's CA bundle if no system bundle is found