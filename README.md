Fortinet Token Registration
===========================

This script emulates [FortiToken Mobile](https://play.google.com/store/apps/details?id=com.fortinet.android.ftm) to "register" a token, converting it into a raw TOTP code you can import into any authenticator app or password manager.

Installation
------------

Set up a virtual environment and install dependencies:

```sh
python3 -mvenv ./venv
source ./venv/bin/activate
pip install -r requirements.txt
```

Basic Usage
-----------

Simply provide your activation code (add `--qr` to generate a QR code for easy import):

```bash
$ python3 register-token.py EEAEVVEYZSERRHEM --qr
Generated new Mobile ID: a1b2c3d4e5f6g7h8
This has been saved to config.txt. Please keep it safe if you want to be able to re-register your token again.
Token registered: 986f4ba5ea241a9dce10cc14e4c142b248999ed9 (base32: TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ)
To generate a token now, run: oathtool --totp 986f4ba5ea241a9dce10cc14e4c142b248999ed9

Import URL for authenticator apps:
otpauth://totp/FortiToken:Mobile?secret=TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ&issuer=FortiToken&period=30

QR Code:
█▀▀▀▀▀█ ▀▄▀█ ▀ █▀▀▀▀▀█
█ ███ █ ██▄█▄▄█ █ ███ █
█ ▀▀▀ █ ▀█▄ █▀▄ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄█▄█▄█ ▀▀▀▀▀▀▀
█▀█▀█▀▀▄▄▄ ▀█▀█▄▄█▄▄▄▀█
▄█ ▄▀ ▀▄█▄█▄▀▄▀▄█▄█▀▄▄█
█▀▀▀▀▀█ █ ▀█▄▄█ ▀ ▀█▄▀▄
█ ███ █ ▄▀▄▀█▄▄█▀██▄█▄█
█ ▀▀▀ █ ▀█▄▀ ▀▀█▄▀▄▄▀▄█
▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

Mobile ID Management
--------------------

The script automatically generates and manages a mobile ID for you:

- **Automatically generated** if not provided
- **Automatically saved** to `config.txt` for future use
- **Reused automatically** on subsequent runs
- **Required for re-registration** of the same token

**Important**: Keep the `config.txt` file safe! If you lose it, you won't be able to re-register the same token.

If you want to use a specific mobile ID (e.g., from your Android device):

```bash
python3 register-token.py EEAEVVEYZSERRHEM --mobile-id e248e1e9527f20ff
```

FortiGate Support
-----------------

The script automatically detects FortiGate tokens and uses the correct 60-second period:

```bash
$ python3 register-token.py EEAEVVEYZSERRHEM
Auto-detected FortiGate token - using 60-second period
Token registered: 986f4ba5ea241a9dce10cc14e4c142b248999ed9 (base32: TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ)
To generate a token now, run: oathtool --totp 986f4ba5ea241a9dce10cc14e4c142b248999ed9

Import URL for authenticator apps:
otpauth://totp/FortiToken:Mobile?secret=TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ&issuer=FortiToken&period=60
```

The detection works by analyzing the token prefix:

- `\x21\x00`: Standard FortiToken (30-second period)
- `\x21\x10`: FortiGate token (60-second period)

You can also manually force FortiGate mode or disable auto-detection:

```bash
# Force FortiGate mode (60-second period)
python3 register-token.py EEAEVVEYZSERRHEM --fortigate

# Disable auto-detection
python3 register-token.py EEAEVVEYZSERRHEM --no-auto-detect
```

QR Code Generation
------------------

Generate a QR code for easy import into authenticator apps:

```bash
$ python3 register-token.py EEAEVVEYZSERRHEM --qr
Token registered: 986f4ba5ea241a9dce10cc14e4c142b248999ed9 (base32: TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ)
To generate a token now, run: oathtool --totp 986f4ba5ea241a9dce10cc14e4c142b248999ed9

Import URL for authenticator apps:
otpauth://totp/FortiToken:Mobile?secret=TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ&issuer=FortiToken&period=30

QR Code:
█▀▀▀▀▀█ ▀▄▀█ ▀ █▀▀▀▀▀█
█ ███ █ ██▄█▄▄█ █ ███ █
█ ▀▀▀ █ ▀█▄ █▀▄ █ ▀▀▀ █
▀▀▀▀▀▀▀ ▀▄█▄█▄█ ▀▀▀▀▀▀▀
█▀█▀█▀▀▄▄▄ ▀█▀█▄▄█▄▄▄▀█
▄█ ▄▀ ▀▄█▄█▄▀▄▀▄█▄█▀▄▄█
█▀▀▀▀▀█ █ ▀█▄▄█ ▀ ▀█▄▀▄
█ ███ █ ▄▀▄▀█▄▄█▀██▄█▄█
█ ▀▀▀ █ ▀█▄▀ ▀▀█▄▀▄▄▀▄█
▀▀▀▀▀▀▀ ▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀
```

The QR code works with any authenticator app including 1Password, Google Authenticator, Microsoft Authenticator, and Authy.

You can combine flags:

```bash
# FortiGate token with QR code
python3 register-token.py EEAEVVEYZSERRHEM --fortigate --qr
```

Verbose Mode
------------

Use `--verbose` (or `-v`) to see detailed information about the registration process:

```bash
$ python3 register-token.py -v EEAEVVEYZSERRHEM
INFO: Starting FortiToken registration process
INFO: Parsing base32 token: EEAEVVEYZSERRHEM
DEBUG: Raw token bytes: 210010aa15964912211a
DEBUG: Token prefix: 2100
INFO: Token prefix indicates standard FortiToken format
INFO: Using existing Mobile ID from config.txt: a1b2c3d4e5f6g7h8
INFO: Token registration successful
Token registered: 986f4ba5ea241a9dce10cc14e4c142b248999ed9 (base32: TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ)
...
```

Verbose mode is helpful for debugging token parsing issues and understanding the registration process.

How Token Registration Works
----------------------------

FortiToken allows you to register a token once. The first device that registers a token is bound to it through a unique mobile device identifier. This script lets you control that identifier so you can:

- **Recover tokens** if you lose your authenticator app
- **Transfer tokens** between devices
- **Use the same token** on multiple authenticator apps

To maintain compatibility with your real mobile phone, you can use the same ID as your phone:

```sh
android:/ # cat /data/system/users/0/settings_ssaid.xml | grep com.fortinet.android.ftm
  <setting id="19" name="10187" value="e248e1e9527f20ff" package="com.fortinet.android.ftm" defaultValue="e248e1e9527f20ff" defaultSysSet="false" tag="null" />
```

Then use that ID with `--mobile-id e248e1e9527f20ff`.

References
----------

<https://web.archive.org/web/20240525172251/https://jonstoler.me/blog/extracting-fortitoken-mobile-totp-secret>
