# Debian deployment

Layout:

```
/opt/email-sender/           code + .venv (created by uv)
/etc/email-sender/env        config, chmod 600
/var/lib/email-sender/data/  watch dir; sent/ and failed/ are created here
```

## Install

Needs `uv` and git:

```sh
sudo apt install -y git
curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh
```

Then:

```sh
sudo useradd --system --no-create-home --shell /usr/sbin/nologin email-sender

sudo git clone https://github.com/yann-dubrana/email-sender /opt/email-sender
cd /opt/email-sender
sudo uv sync --frozen          # builds .venv from uv.lock, fetches Python 3.13 if needed

sudo mkdir -p /etc/email-sender /var/lib/email-sender/data
sudo chown -R email-sender:email-sender /var/lib/email-sender

sudo install -m 600 -o root -g email-sender deploy/env.template /etc/email-sender/env
sudo nano /etc/email-sender/env   # fill in credentials, unquoted

sudo install -m 644 deploy/email-sender.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now email-sender
```

`uv sync` provisions Python 3.13 itself, so Debian's system Python version does
not matter — bookworm ships 3.11 and this still works.

## Update

```sh
cd /opt/email-sender
sudo git pull
sudo uv sync --frozen
sudo systemctl restart email-sender
```

## Check

```sh
systemd-analyze verify /etc/systemd/system/email-sender.service
systemctl status email-sender
journalctl -u email-sender -f
```

Drop a PDF into `/var/lib/email-sender/data/` and it is mailed, then moved to
`sent/`. Failures land in `failed/` and are not retried automatically — move a
file back into the watch directory to retry it.

The unit has not been run on a live Debian host — validate it with
`systemd-analyze verify` and confirm one real send before relying on it.
If sends fail with a name-resolution error, check that
`RestrictAddressFamilies` still includes `AF_UNIX`.

## Notes

- `uv.lock` must be committed for `--frozen` to work. Drop `--frozen` to let uv
  resolve and write one instead.
- `EnvironmentFile` values are not quote-stripped. `PASSWORD="x"` sends `"x"`.
- The unit runs with `ProtectSystem=strict`; `ReadWritePaths=/var/lib/email-sender`
  is what lets the service move files into `sent/`/`failed/`. If you relocate the
  watch directory, update both `ExecStart` and `ReadWritePaths`.
- Gmail requires an app password, not the account password, and port 587 with
  `SMTP__USE_SSL=false` (STARTTLS). For implicit TLS use port 465 and `true`.
- The startup sweep mails anything already sitting in the watch directory, so a
  restart picks up whatever arrived while the service was down.
