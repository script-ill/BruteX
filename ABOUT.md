# 🧡 ABOUT BRUTEX

## The Story

BruteX didn't start as a product. It started as a question:             
> *"What if credential validation for authorized pentests didn't require
> memorizing a dozen different tools, endpoints, and token formats?"*
                                                                        The answer became **SocialStrike v3.0** — a lean, single-file credential
validator. But every great tool wants to grow. So SocialStrike evolved.

**BruteX v4.0** is that evolution:                                      
- **3× the platforms** — from a handful of social networks to 39 endpoints
  across web, mail, databases, and infrastructure protocols
- **From flags to a menu** — anyone can run a professional credential test
  after answering 5 questions
- **From raw output to a report** — every run produces structured, shareable
  results
- **From fixed wordlists to smart attacks** — mutations generate thousands of
  realistic candidates from a single base password

## The Philosophy

1. **Authorization first.** BruteX exists for penetration testers, red teams,
   and defenders who were *hired* to break in. Unauthorized use is not just
   illegal — it poisons the well for everyone who does this professionally.

2. **Automation with respect.** We automate the repetitive work — CSRF tokens,
   session handling, proxy rotation, progress tracking — so the human can
   focus on what machines can't do: judgment.

3. **Simple beats complex.** One file, plain Python, readable code. If BruteX
   ever stops making sense to read, it has failed.

4. **Extensible by design.** A new platform is one block of data, not a new
   framework. Your targets are unique — BruteX should grow with them.

## Architecture

```
brutex.py
│
├── PLATFORMS      → 22 web targets (URL, CSRF, form, ok/bad/lock rules)
├── NETPLATFORMS   → 17 network services (FTP, SSH, SMB, DBs, mail...)
├── WebEngine      → session pooling, CSRF fetch, proxy rotation, response eval
├── NetEngine      → socket-level protocol checkers (raw / library-backed)
├── smart_passwords→ mutation engine (years, symbols, leet, case)
├── load_pairs     → combo / matrix / single-user credential builder
├── Reports        → TXT hits + JSON report writer
└── Menu           → interactive UI + headless CLI fallback
```

## Roadmap (ideas for v5)

- [ ] More self-hosted targets (Confluence, Jenkins, Grafana, Keycloak...)
- [ ] Hashcat/JtR integration for offline cracking pipelines
- [ ] Distributed mode — multiple workers, one coordinator
- [ ] WebSocket / GraphQL login support
- [ ] Playwright-based browser auth for fully JS-protected targets
- [ ] `--format` report export (CSV, HTML)

## The Human Behind It

BruteX is a dream made real — an idea turned into lines of code, built with
help, shipped with love. If you're reading this: you're now part of that
story. Use it well. Learn from it. Break it. Improve it. That's how tools
live forever.

— **Imin**, 2026