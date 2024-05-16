Fortinet Token Registration
===========================

This script will emulate [FortiToken Mobile](https://play.google.com/store/apps/details?id=com.fortinet.android.ftm) to "register" a token, converting it into a raw TOTP code you can import into any other application, including a password manager.

Example:
```
$ python3 register-token.py EEAEVVEYZSERRHEM --mobile-id e248e1e9527f20ff
Token registered: 986f4ba5ea241a9dce10cc14e4c142b248999ed9 (base32: TBXUXJPKEQNJ3TQQZQKOJQKCWJEJTHWZ)
To generate a token now, run: oathtool --totp 986f4ba5ea241a9dce10cc14e4c142b248999ed9
```

# Installation
Set up a virtual environment, install the dependencies, and run it:
```sh
python3 -mvenv ./venv
pip install -r requirements.txt
source ./venv/bin/activate
```

# What does registration mean?
FortiToken allows you to register a token once. The first mobile device that registers a token is bound to it and no one else can use the registration token unless it is transfered to another user by the person who first registered it.
This is done through a unique identifier Android assigns to each device. This means if we are careful, we can pick an ID once and re-use it so the token can be recovered or transfered in future.
If you want to maintain compatibility with your real mobile phone, simply use the same ID as your phone already has:
```sh
android:/ # cat /data/system/users/0/settings_ssaid.xml | grep com.fortinet.android.ftm
  <setting id="19" name="10187" value="e248e1e9527f20ff" package="com.fortinet.android.ftm" defaultValue="e248e1e9527f20ff" defaultSysSet="false" tag="null" />
```
By using this ID (`e248e1e9527f20ff`), we can transfer a token using the real application on a phone.

# References
https://jonstoler.me/blog/extracting-fortitoken-mobile-totp-secret
