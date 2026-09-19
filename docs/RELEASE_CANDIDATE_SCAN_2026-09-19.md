# Release Candidate Security Scan

**Date:** 2026-09-19
**Repository:** `heyooboob/Atmanatic-Research`
**Candidate base:** `e0fb09c3e8051fa9a5679ccdf2e247d8b498fca6` (`main`)
**Purpose:** Record the pre-release history and working-tree secret scan without storing or printing matched content.

## Scope

The scan inspected:

- every commit reachable from local Git refs;
- tracked files in the current working tree;
- common credential, token, password, private-key, and signing-key patterns;
- common GitHub and PyPI token prefixes;
- tracked filenames that resemble secret or private-key material.

## Result

- History pattern matches: **0**
- Current tracked secret-like paths: **0**
- Release signing registry present: `release/keys.jsonl` (**public key material only**)
- Candidate contains no committed private signing key.

## Reproduction

Run from the repository root with Git installed:

```powershell
$git = "C:\Program Files\Git\cmd\git.exe"
$commits = & $git rev-list --all
$patterns = @(
  "(?i)(api[_-]?key|access[_-]?token|secret[_-]?key|private[_-]?key|password\s*[:=])",
  "BEGIN (RSA|OPENSSH|EC|DSA|PRIVATE) KEY",
  "ghp_[A-Za-z0-9]{20,}",
  "pypi-[A-Za-z0-9_-]{20,}"
)
foreach ($pattern in $patterns) {
  & $git grep --all-match -I -n -E $pattern $commits --
}
```

The command is expected to produce no matching lines. The scan must be rerun
against the final release commit before tagging.

## Limitations

This is a repository-local, pattern-based scan. It is evidence of a clean
scan under the listed patterns, not proof that no secret exists. It does not
replace GitHub secret scanning, Dependabot, a dedicated scanner such as
Gitleaks, credential rotation, or maintainer review of external systems.

No private key or token value is included in this record.
