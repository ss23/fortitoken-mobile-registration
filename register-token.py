from requests_pkcs12 import Pkcs12Adapter  # type: ignore
import requests
import argparse
import base64
from pathlib import Path
import uuid
import sys
import logging
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import qrcode  # type: ignore


def setup_logging(verbose: bool):
    """Setup logging configuration"""
    if verbose:
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.WARNING)


def register_token(token: bytes, mobile_id: str) -> bytes:
    # We use the PKCS12 certificate directly from the Fortitoken application
    logging.info(f"Registering token with mobile_id: {mobile_id}")
    logging.debug(f"Token bytes: {token.hex()}")

    s = requests.Session()
    s.mount(
        "https://globalftm.fortinet.net",
        Pkcs12Adapter(pkcs12_filename="ftm.ks", pkcs12_password="Terran2023"),
    )

    # Prepare our payload
    payload = {
        "mobile_id": mobile_id,
        "__type": "SoftToken.MobileProvisionRequest",
        "token_activation_code": token.hex(),
    }

    logging.debug(f"Request payload: {payload}")

    r = s.post(
        "https://globalftm.fortinet.net/SoftToken/Provisioning.asmx/Mobile",
        json={"d": payload},
    )

    logging.debug(f"Response status code: {r.status_code}")
    logging.debug(f"Response headers: {dict(r.headers)}")

    if r.status_code != 200:
        print(r.text, file=sys.stderr)
        raise Exception("Error from globalftm.fortinet.net")

    response = r.json()["d"]
    logging.debug(f"Response data: {response}")

    if "error" in response and response["error"] is not None:
        print(response["error"], file=sys.stderr)
        raise Exception("Could not register token")

    logging.info("Token registration successful")
    logging.debug(f"Encrypted seed received: {response['seed']}")

    # TODO: Additional verification, such as mobile_id_hash
    return decrypt_seed(response["seed"], mobile_id)


def decrypt_seed(encrypted_seed, mobile_id):
    logging.debug(f"Decrypting seed with mobile_id: {mobile_id}")

    # IV must be exactly 16 bytes for AES CBC mode
    iv_string = "fortitokenmobile"
    iv = iv_string.ljust(16, "\x00").encode("utf-8")  # Pad to exactly 16 bytes
    logging.debug(f"IV: {iv.hex()}")

    # Ensure mobile_id is exactly 16 bytes for AES-128
    key = bytes(mobile_id, "utf-8")
    original_key_len = len(key)
    if len(key) != 16:
        # Pad or truncate to 16 bytes
        key = key[:16].ljust(16, b"\x00")
        logging.debug(f"Key adjusted from {original_key_len} to 16 bytes")

    logging.debug(f"Decryption key: {key.hex()}")

    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()

    encrypted_bytes = base64.b64decode(encrypted_seed)
    logging.debug(f"Encrypted seed bytes: {encrypted_bytes.hex()}")

    decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()
    logging.debug(f"Raw decrypted bytes: {decrypted.hex()}")

    decrypted_truncated = decrypted[0:40]  # Truncate trailing null bytes
    logging.debug(f"Truncated decrypted bytes: {decrypted_truncated}")

    final_seed = bytes.fromhex(decrypted_truncated.decode("utf-8"))
    logging.debug(f"Final TOTP seed: {final_seed.hex()}")

    return final_seed


def parse_token(token):
    logging.info(f"Parsing base32 token: {token}")

    raw_token = base64.b32decode(token)
    logging.debug(f"Raw token bytes: {raw_token.hex()}")
    logging.debug(f"Raw token length: {len(raw_token)} bytes")

    if len(raw_token) >= 2:
        prefix = raw_token[0:2]
        logging.debug(f"Token prefix: {prefix.hex()}")

        if prefix == b"\x21\x00":
            logging.info("Token prefix indicates standard FortiToken format")
        elif prefix == b"\x21\x10":
            logging.info(
                "Token prefix indicates alternative FortiToken format (possibly FortiGate)"
            )
        else:
            logging.warning(
                f"Unknown token prefix: {prefix.hex()} - this may indicate a different token type"
            )
            print(f"Token did not begin with expected prefix, got: {prefix.hex()}")

    if len(raw_token) != 10:
        logging.warning(
            f"Unexpected token length: {len(raw_token)} bytes (expected 10)"
        )
        print(f"Token was not 10 bytes, got: {len(raw_token)} bytes")

    token_data = raw_token[2:]
    logging.debug(f"Token data (without prefix): {token_data.hex()}")

    return token_data


def parse_raw_token(token):
    logging.info(f"Parsing raw hex token: {token}")

    raw_token = bytes.fromhex(token)
    logging.debug(f"Raw token bytes: {raw_token.hex()}")
    logging.debug(f"Raw token length: {len(raw_token)} bytes")

    if len(raw_token) != 8:
        logging.warning(
            f"Unexpected raw token length: {len(raw_token)} bytes (expected 8)"
        )
        print("Decoded token was not 8 bytes")

    return raw_token


def get_mobile_id():
    p = Path("config.txt")
    if not p.is_file():
        mobile_id = uuid.uuid4().hex[0:16]
        logging.info(f"Generated new Mobile ID: {mobile_id}")
        print(f"Generated new Mobile ID: {mobile_id}")
        print(
            "This has been saved to config.txt. Please keep it safe if you want to be able to re-register your token again."
        )
        p.write_text(mobile_id)
    else:
        mobile_id = p.read_text()
        logging.info(f"Using existing Mobile ID from config.txt: {mobile_id}")

    return mobile_id


def generate_qr_code(otpauth_url):
    """Generate and display QR code in terminal"""
    logging.debug(f"Generating QR code for: {otpauth_url}")

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=1,
        border=1,
    )
    qr.add_data(otpauth_url)
    qr.make(fit=True)
    qr.print_ascii()


def detect_fortigate_token(raw_token_with_prefix: bytes) -> bool:
    """
    Attempt to detect if this is a FortiGate token based on token characteristics.
    This is experimental and may need refinement.
    """
    if len(raw_token_with_prefix) < 2:
        return False

    prefix = raw_token_with_prefix[0:2]

    # Based on observations, different prefixes might indicate different token types
    if prefix == b"\x21\x10":
        logging.info("Token prefix suggests FortiGate compatibility (60-second period)")
        return True
    elif prefix == b"\x21\x00":
        logging.info("Token prefix suggests standard FortiToken (30-second period)")
        return False
    else:
        logging.warning(
            f"Unknown prefix {prefix.hex()}, unable to auto-detect FortiGate mode"
        )
        return False


def main(args):
    setup_logging(args.verbose)

    logging.info("Starting FortiToken registration process")

    if not args.raw_token:
        # For base32 tokens, we can analyze the full token including prefix
        raw_token_with_prefix = base64.b32decode(args.token)
        token = parse_token(args.token)

        # Auto-detect FortiGate if not explicitly specified
        if not args.fortigate and not args.no_auto_detect:
            detected_fortigate = detect_fortigate_token(raw_token_with_prefix)
            if detected_fortigate:
                logging.info("Auto-detected FortiGate token - using 60-second period")
                print("Auto-detected FortiGate token - using 60-second period")
                args.fortigate = True
    else:
        token = parse_raw_token(args.token)
        logging.info("Raw token provided - cannot auto-detect FortiGate mode")

    if args.mobile_id:
        mobile_id = args.mobile_id
        logging.info(f"Using provided mobile_id: {mobile_id}")
    else:
        mobile_id = get_mobile_id()

    logging.info("Registering token with FortiNet servers...")
    totp = register_token(token, mobile_id)

    base32_secret = base64.b32encode(totp).decode("utf-8")
    period = 60 if args.fortigate else 30

    logging.info(
        f"Using period: {period} seconds ({'FortiGate' if args.fortigate else 'Standard'} mode)"
    )

    otpauth_url = f"otpauth://totp/FortiToken:Mobile?secret={base32_secret}&issuer=FortiToken&period={period}"

    print(f"Token registered: {totp.hex()} (base32: {base32_secret})")
    print(f"To generate a token now, run: oathtool --totp {totp.hex()}")
    print()
    print("Import URL for authenticator apps:")
    print(otpauth_url)

    if args.qr:
        print()
        print("QR Code:")
        generate_qr_code(otpauth_url)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "token", help="Base32 encoded token data, e.g. EEAEVVEYZSERRHEM"
    )
    parser.add_argument("-m", "--mobile-id", default=None)
    parser.add_argument(
        "-r",
        "--raw-token",
        action=argparse.BooleanOptionalAction,
        help="Parse the token as raw hexadecimal bytes with no prefix, e.g. 7A2AAEE00A56C569",
    )
    parser.add_argument(
        "-qr",
        "--qr",
        action="store_true",
        help="Generate and display QR code in terminal for easy import into authenticator apps",
    )
    parser.add_argument(
        "--fortigate",
        action="store_true",
        help="Use 60-second period for FortiGate compatibility (default: 30 seconds)",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging to show detailed token parsing and registration process",
    )
    parser.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable automatic FortiGate token detection based on token prefix",
    )

    args = parser.parse_args()
    main(args)
