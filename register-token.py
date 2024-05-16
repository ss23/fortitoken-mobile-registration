from requests_pkcs12 import Pkcs12Adapter
import requests
import argparse
import base64
from pathlib import Path
import uuid
import sys
from Crypto.Cipher import AES


def register_token(token, mobile_id):
    # We use the PKCS12 certificate directly from the Fortitoken application
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

    r = s.post(
        "https://globalftm.fortinet.net/SoftToken/Provisioning.asmx/Mobile",
        json={"d": payload},
    )

    if r.status_code != 200:
        print(r.text, file=sys.stderr)
        raise Exception("Error from globalftm.fortinet.net")

    response = r.json()["d"]
    if "error" in response and response["error"] != None:
        print(response["error"], file=sys.stderr)
        raise Exception("Could not register token")

    # TODO: Additional verification, such as mobile_id_hash
    return decrypt_seed(response["seed"], mobile_id)


def decrypt_seed(encrypted_seed, mobile_id):
    iv = bytes("fortitokenmobile", "utf-8")
    aes = AES.new(bytes(mobile_id, "utf-8"), AES.MODE_CBC, iv)
    decrypted = aes.decrypt(base64.b64decode(encrypted_seed))[
        0:40
    ]  # Truncate trailing null bytes
    return bytes.fromhex(decrypted.decode("utf-8"))


def parse_token(token):
    raw_token = base64.b32decode(token)
    if raw_token[0:2] != b"\x21\x00":
        # Example tokens tested all start with \x21\x00, likely a version identifier
        print("Token did not begin with \x21\x00")
    if len(raw_token) != 10:
        print("Token was not 10 bytes")
    return raw_token[2:]


def parse_raw_token(token):
    raw_token = bytes.fromhex(token)

    if len(raw_token) != 8:
        print("Decoded token was not 8 bytes")

    return raw_token


def get_mobile_id():
    p = Path("config.txt")
    if not p.is_file():
        mobile_id = uuid.uuid4().hex[0:16]
        print(f"Generated new Mobile ID: {mobile_id}")
        print(
            f"This has been saved to config.txt. Please keep it safe if you want to be able to re-register your token again."
        )
        p.write_text(mobile_id)
    return p.read_text()


def main(args):
    if not args.raw_token:
        token = parse_token(args.token)
    else:
        token = parse_raw_token(args.token)

    if args.mobile_id:
        mobile_id = args.mobile_id
    else:
        mobile_id = get_mobile_id()

    totp = register_token(token, mobile_id)
    print(
        f"Token registered: {totp.hex()} (base32: {base64.b32encode(totp).decode('utf-8')})"
    )
    print(f"To generate a token now, run: oathtool --totp {totp.hex()}")


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

    args = parser.parse_args()
    main(args)
