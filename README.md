<div align="center">

```
██████╗ ██████╗ ██╗   ██╗████████╗███████╗██╗  ██╗
██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝╚██╗██╔╝
██████╔╝██████╔╝██║   ██║   ██║   █████╗   ╚███╔╝
██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝   ██╔██╗
██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██╔╝ ██╗
╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝
```

# 🔥 BRUTEX v4.0 PRO

**Multi-Platform Credential Validator — Authorized Pentest Edition**

> The evolution of *SocialStrike v3.0* — 39 attack endpoints, an interactive menu system,
> smart password mutations, and full reporting. Built for authorized security testing.

[![Python 3.8+](https://img.shields.io/badge/Python-3.8%2B-blue)](#)
[![License: Custom](https://img.shields.io/badge/License-Custom%20%7C%20No%20Resale-red)](#)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-lightgrey)](#)

---

## ⚡ Features

- 🎯 **39 endpoints** — 22 web (social, email/accounts, self-hosted CMS & routers) + 17 network services
- 🖥️ **Interactive menu** — pick a platform, answer 5 questions, hit GO. No CLI memorization needed
- 🧠 **Smart mutations** — auto-expands passwords with years, symbols, leet-speak, case variants
- 🌈 **Killer UI** — rainbow banner, boxed screens, live `█░` progress bar with RPS counter
- ⚡ **Multi-threaded engine** — up to 500 concurrent workers, retry adapters, session pooling
- 🕵️ **Proxy rotation** — drop a proxy list, BruteX rotates automatically per request
- 🔒 **CSRF-aware** — auto-fetches tokens for web platforms that need them
- 📁 **Persistent config** — save/load settings from `brutex_config.json`
- 📊 **Full reporting** — hit logs (`brutex_hits_*.txt`) + JSON reports (`brutex_report_*.json`)
- 🛑 **Stop-on-hit** — abort the run the moment a valid credential is found

---

## 📦 Installation

```bash
# 1. Clone / copy the project
git clone https://github.com/script-ill/BruteX.git
cd BruteX

# 2. Install required dependencies
pip install requests colorama

# 3. (Optional) Network-service engines — install what you need
pip install paramiko pymysql pg8000 pymongo ldap3 impacket pycryptodome

# 4. Run
python3 brutex.py
```

> **Note:** Network modules are loaded lazily. Missing libraries only disable their
> protocol — the rest of the tool works fine.

---

## 🚀 Quick Start

### Interactive Menu (recommended)

```bash
python3 brutex.py
```

```
┌─────────────────────────────────────────────┐
│            BRUTEX v4.0 PRO - MAIN MENU       │
│                                              │
│  1.  RUN ATTACK      pick platform -> GO     │
│  2.  TARGET SETUP    configure only          │
│  3.  PLATFORM LIST   browse all 39 endpoints │
│  4.  LOAD CONFIG     restore saved settings  │
│  5.  SAVE CONFIG     store current settings  │
│  6.  VIEW RESULTS    show latest hits file   │
│  7.  EXIT            quit BruteX             │
└─────────────────────────────────────────────┘
```

### Headless / CLI

```bash
# Single user against a password list (network service)
python3 brutex.py -p ssh --host 10.10.10.5 -u root -P rockyou.txt -t 40 --stop-on-hit

# Combo file (user:pass per line)
python3 brutex.py -p ftp --host 10.10.10.20 --combo combos.txt -t 30

# Userlist × Passlist matrix
python3 brutex.py -p wordpress --host 10.10.10.30 -U users.txt -P passwords.txt -t 50

# Smart mutations + proxies
python3 brutex.py -p mysql --host 10.10.10.40 -U users.txt -P passwords.txt --smart --proxy-file proxies.txt

# List all platforms
python3 brutex.py --list-platforms
```

---

## 🎯 Supported Platforms

### 🌐 Social Networks

| Platform | Type | Notes |
|---|---|---|
| Instagram | Web | CSRF + encrypted password format |
| Facebook | Web | mbasic endpoint |
| Twitter / X | Web | API onboarding flow |
| LinkedIn | Web | CSRF-protected |
| Reddit | Web | JSON API |
| TikTok | Web | Web passport API |
| Snapchat | Web | *experimental* |
| GitHub | Web | CSRF-protected |
| Pinterest | Web | Resource API |

### ✉️ Email & Accounts

| Platform | Type | Notes |
|---|---|---|
| eBay | Web | *experimental* |
| Netflix | Web | *experimental* |
| Spotify | Web | CSRF-protected |
| PayPal | Web | *experimental* |
| Roblox | Web | JSON API + CSRF header |

### 🖧 Self-Hosted — CMS / Panels / Routers

| Platform | Type | Notes |
|---|---|---|
| WordPress | Web | `{HOST}/wp-login.php` |
| Drupal | Web | `{HOST}/user/login` — *experimental* |
| Joomla | Web | admin login + anti-CSRF token |
| cPanel | Web | `:2083` JSON API |
| Nextcloud | Web | CSRF-protected |
| phpMyAdmin | Web | DB panel login |
| MikroTik | Web | RouterOS login — *experimental* |
| pfSense | Web | Firewall login |

### 🖥️ Network Services

| Protocol | Default Port | TLS Variant | Requires |
|---|---|---|---|
| FTP | 21 | — | — |
| SSH | 22 | — | paramiko |
| Telnet | 23 | — | — |
| SMTP | 25 | SMTPS :465 | — |
| POP3 | 110 | POP3S :995 | — |
| IMAP | 143 | IMAPS :993 | — |
| MySQL | 3306 | — | pymysql |
| PostgreSQL | 5432 | — | pg8000 |
| MongoDB | 27017 | — | pymongo |
| Redis | 6379 | — | (password only) |
| VNC | 5900 | — | pycryptodome |
| SMB | 445 | — | impacket |
| LDAP | 389 | LDAPS :636 | ldap3 |

---

## ⚙️ Configuration

Settings are stored in `brutex_config.json` (created by the menu's **Save Config**).

| Key | Description | Default |
|---|---|---|
| `threads` | Concurrent workers | 25 |
| `delay` | Jitter delay between requests (seconds) | 0.0 |
| `timeout` | Per-request timeout (seconds) | 25 |
| `proxy_file` | Proxy list (one per line) | — |
| `smart` | Enable password mutations | false |
| `stop_on_hit` | Halt after first success | false |

---

## 📁 Outputs

| File | Contents |
|---|---|
| `brutex_hits_YYYYMMDD_HHMMSS.txt` | Every valid credential found, timestamped |
| `brutex_report_YYYYMMDD_HHMMSS.json` | Full run stats + credential list (machine-readable) |
| `brutex_config.json` | Your saved settings |

---

## 🧩 Extending — Add Your Own Platform

Every web platform is one block. Copy an existing one and edit:

```python
W("myapp",
  "https://{HOST}/login",                        # endpoint ({HOST} = target)
  csrf_url=None,                                  # or URL to fetch a token from
  regex=r'name="token"\s+value="([^"]+)"',        # CSRF extraction regex
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"username": u, "password": p, "token": c or ""},
  ok=('dashboard', 'welcome'),                    # substrings / status codes = success
  bad=('Invalid credentials',),                   # substrings = failure
  lock=('captcha', 'too many'),                   # substrings = lockout/rate-limit
  hosted=True)                                    # True if it needs a {HOST} target
```

Network services register with a checker function:

```python
N("myproto", 1234, my_checker, tls=False)
# def my_checker(host, port, user, pw, timeout, tls) -> ("hit"|"fail"|"lock"|"err", info)
```

---

## ⚠️ Legal Disclaimer

> **BruteX is a security testing tool for AUTHORIZED use only.**
>
> You may only use BruteX against systems you own or have **explicit written
> permission** to test. Unauthorized credential testing is illegal in most
> jurisdictions and can result in criminal prosecution. The author takes no
> responsibility for misuse. Use responsibly. Stay in scope.

---

```
## 📜 License

[Custom License](LICENSE) © 2026 Imin — **No resale, no rebranding, no commercial use
without written permission.** See [LICENSE](LICENSE) for full terms.
```

---

## 🙏 Credits

Built with 🧡 for the offensive-security community —