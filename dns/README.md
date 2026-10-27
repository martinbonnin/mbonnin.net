# dns

DNS-as-code for `mbonnin.net`, hosted at [Porkbun](https://porkbun.com). Records
live in [`zones/mbonnin.net.yaml`](zones/mbonnin.net.yaml) and are kept in
sync with Porkbun by [octoDNS](https://github.com/octodns/octodns) via the
[octodns-porkbun](https://github.com/major/octodns-porkbun) provider.

Workflow:

1. Edit `dns/zones/mbonnin.net.yaml` on a branch and open a PR.
2. GitHub Actions (`.github/workflows/dns-plan.yml`) runs `octodns-sync` in
   dry-run mode and posts the diff as a PR comment.
3. Review the diff, get it approved, merge.
4. GitHub Actions (`.github/workflows/dns-apply.yml`) runs `octodns-sync
   --doit` on `main`, which pushes the change to Porkbun.

No Terraform-style state file to manage: octoDNS diffs the YAML in this repo
directly against Porkbun's live records on every run.

## One-time setup

1. **Enable API access for the domain.** In the Porkbun dashboard, under
   Domain Management for `mbonnin.net`, toggle "API Access" on. This is
   separate from having an account-level API key.
2. **Create an API key.** [porkbun.com/account/api](https://porkbun.com/account/api)
   → generate a key. You get an API Key (`pk1_...`) and a Secret API Key
   (`sk1_...`).
3. **Add repo secrets.** In this repo's Settings → Secrets and variables →
   Actions, add:
   - `PORKBUN_API_KEY`
   - `PORKBUN_SECRET_KEY`
4. **(Recommended) Protect the `production` environment.** The apply
   workflow runs under the `production` GitHub environment
   (Settings → Environments → New environment → `production`). Add required
   reviewers there if you want a manual approval gate on top of PR review
   before changes actually hit Porkbun.
5. **Seed real records** (see below) before merging anything for real — the
   committed `zones/mbonnin.net.yaml` is currently a placeholder.

## Seeding real records

`zones/mbonnin.net.yaml` starts as a placeholder. To replace it with what's
actually live at Porkbun:

```bash
cd dns
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

export PORKBUN_API_KEY=pk1_...
export PORKBUN_SECRET_KEY=sk1_...

octodns-dump --config-file=config/octodns.yaml --output-dir=zones --lenient mbonnin.net. porkbun
```

This overwrites `zones/mbonnin.net.yaml` with the current live records.
Review the diff and commit.

## Local dry run

```bash
cd dns
source .venv/bin/activate
export PORKBUN_API_KEY=pk1_...
export PORKBUN_SECRET_KEY=sk1_...

octodns-validate --config-file=config/octodns.yaml   # syntax/config check only
octodns-sync --config-file=config/octodns.yaml       # dry run, prints the plan
octodns-sync --config-file=config/octodns.yaml --doit  # actually apply
```

## Layout

```
config/octodns.yaml     # octoDNS provider config (source: ./zones, target: Porkbun)
zones/mbonnin.net.yaml  # source of truth for mbonnin.net records
requirements.txt        # octoDNS + Porkbun provider
```

The workflows live in the repo root's `.github/workflows/dns-*.yml`.
