import os
import logging
from cryptography.x509 import load_pem_x509_certificate, Certificate
from cryptography.hazmat.backends import default_backend
import requests
from datetime import datetime, timedelta

# Enable logging
logging.basicConfig(format="%(asctime)s %(levelname)-8s %(message)s", level=logging.INFO, datefmt="%Y-%m-%d %H:%M:%S")


PORKBUN_URLS: dict = {
    "SSL_CERT_ENDPOINT": "https://api.porkbun.com/api/json/v3/ssl/retrieve/{domain}"
}

CERT_FILE_PATHS: dict = {
    "CHAIN": "certs/{domain}/chain.pem",
    "PUBLIC_KEY": "certs/{domain}/public.key.pem",
    "PRIVATE_KEY": "certs/{domain}/private.key.pem"
}

BASE_PATH: str = ''
PORKBUN_API_KEY: str = ''
PORKBUN_SECRET_API_KEY: str = ''
PORKBUN_DOMAIN: str = ''


def fetch_certificates(domain: str) -> dict:
    logging.info("Fetching Certs from Porkbun")
    response = requests.post(
        url=PORKBUN_URLS.get("SSL_CERT_ENDPOINT").format(domain=domain),
        json={
            "apikey": PORKBUN_API_KEY,
            "secretapikey": PORKBUN_SECRET_API_KEY
        }
    )
    return response.json()

def write_certificates(domain: str, certificates: dict) -> None:
    logging.info(f"Updating {domain} certs...")

    for key in CERT_FILE_PATHS:
        file_location = BASE_PATH + CERT_FILE_PATHS.get(key).format(domain=domain)
        with open(file_location, 'w') as file:
            if key == "PUBLIC_KEY":
                file.write(certificates.get('publickey'))
            elif key == "PRIVATE_KEY":
                file.write(certificates.get('privatekey'))
            elif key == "CHAIN":
                file.write(certificates.get('certificatechain'))

            file.close()

    logging.info(f"Updated {domain} certs.")

def restart_docker_task(task_id: str):
    os.system(f"docker restart {task_id}")


try:
    certificates: dict = fetch_certificates(PORKBUN_DOMAIN)
    certificate: Certificate = load_pem_x509_certificate(str.encode(certificates.get('certificatechain')), default_backend())
    write_certificates(PORKBUN_DOMAIN, certificates)

    if certificate.not_valid_before > datetime.now() - timedelta(2):
        restart_docker_task("adguard")
except Exception as exception:
    logging.error("An error occurred. Exception: " + str(exception))