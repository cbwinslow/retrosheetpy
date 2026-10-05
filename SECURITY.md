# Security

Report vulnerabilities privately through GitHub: Security tab -> "Report a vulnerability".
Do not open a public issue. Expect an acknowledgement within a few days.

The package downloads files from retrosheet.org and unpacks zip archives into a cache folder.
It rejects unsafe archive members (path traversal, oversized or malformed archives) and checks
a SHA-256 for every cached download. Releases are built and published only by the GitHub Actions
workflow, through PyPI trusted publishing (no long-lived token exists).
