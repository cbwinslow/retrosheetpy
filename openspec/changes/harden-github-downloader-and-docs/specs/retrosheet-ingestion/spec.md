# Spec Delta

## MODIFIED Requirements

### Requirement: Download and Cache Retrosheet Archives
The system MUST download event files, game logs, schedules, and reference data from configurable sources (defaulting to the GitHub raw CDN of the Chadwick Baseball Bureau mirror, with automatic fallback to retrosheet.org or custom mirror URLs) and store them in a local cache directory (`~/.cache/retrosheetpy/`) without re-downloading existing archives unless forced.

Network communication MUST reuse HTTP client sessions across multiple file transfers to leverage connection pooling and HTTP keep-alive. During multi-file season downloads via GitHub raw CDN, the system MUST distinguish between expected missing files (HTTP 404 for split seasons or non-participating teams) and network errors (timeouts, dropped connections, non-404 status codes). Network failures MUST abort the season download and trigger fallback to `retrosheet.org` when `source="auto"`, or raise an exception when `source="github"`.

#### Scenario: First download of a season
- **GIVEN** the local cache does not contain `2024seve.zip`
- **WHEN** the user or pipeline requests 2024 event data
- **THEN** the client downloads `2024seve.zip` from retrosheet.org, verifies the archive, and extracts it to the cache.

#### Scenario: Repeated request uses cached data
- **GIVEN** `2024seve.zip` is already present and valid in the local cache
- **WHEN** the user requests 2024 event data without `--refresh`
- **THEN** no network request is made and the cached files are used directly.

#### Scenario: First download of a season via GitHub mirror
- **GIVEN** the local cache does not contain event data for year 2024
- **WHEN** the user requests 2024 event data with `source="github"` (or default "auto")
- **THEN** the client resolves the season manifest (`TEAM2024`), downloads uncompressed event and roster files via GitHub raw CDN, and populates the local cache directory.

#### Scenario: Network interruption during team download triggers fallback
- **GIVEN** `source="auto"` and a network timeout or connection reset occurs while fetching a team `.EVA` or `.ROS` file from GitHub
- **WHEN** downloading season events
- **THEN** the partial files in the season directory are cleaned up and the system falls back to downloading the full season archive from `retrosheet.org`.

#### Scenario: Network interruption during team download under explicit github source raises error
- **GIVEN** `source="github"` and a network timeout occurs while fetching a team `.EVA` or `.ROS` file from GitHub
- **WHEN** downloading season events
- **THEN** the downloader raises the network exception and does not mark the season cache as valid.

#### Scenario: Missing team event file on GitHub (HTTP 404) is skipped
- **GIVEN** a team listed in `TEAM{year}` has no separate event file on GitHub (returning HTTP 404)
- **WHEN** downloading season events
- **THEN** the missing file is skipped without raising an error and the remaining season files are downloaded.

#### Scenario: Fallback to retrosheet.org on mirror failure
- **GIVEN** the GitHub raw mirror returns an HTTP error or is unreachable
- **WHEN** the user requests a dataset with `source="auto"`
- **THEN** the system falls back to downloading the official archive bundle from `retrosheet.org`.
