# Leapmotor API Certificates

TLS client certificates required for communicating with Leapmotor cloud APIs (mTLS).

Extracted via reverse engineering of the official Leapmotor app.

## Files

| File | Description |
|------|-------------|
| `app_crt.pem` | Client certificate (PEM) |
| `app_key.pem` | Private key (PEM) |

## Usage

These certificates are used by [LeapConnect](https://github.com/markoceri/leapconnect) and the [leapmotor-api](https://github.com/markoceri/leapmotor-api) Python client.

During LeapConnect setup, upload these two files in the **Certificate Setup** step.

## Password Reset

If you are locked out of your **LeapConnect local account** (the app login password, not your Leapmotor cloud credentials), you can reset it from the command line:

```bash
# Direct
python main.py --reset-password "new_password"

# Docker
docker compose exec app uv run python main.py --reset-password "new_password"
```

> **Note:** Quote the password to prevent shell interpretation of special characters (`$`, `&`, `!`, etc.).
>
> This does **not** affect your Leapmotor cloud account password — only the local LeapConnect application login.

## Disclaimer

These files are provided for interoperability and research purposes only. Use at your own risk.
