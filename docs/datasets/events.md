# Play-by-Play Events

Retrosheet event files (`.EVA`, `.EVN`) record every pitch, play, substitution, and baserunning event in Major League Baseball.

`retrosheetpy` parses these event archives into a **164-column strongly-typed schema** via `chadwickpy`.

---

## Usage

```python
import retrosheetpy as rs

# Download & parse 2024 plays (returns Polars DataFrame)
events = rs.events(year=2024, backend="polars")

# Filter for home runs
home_runs = events.filter(events["HR_FL"] == True)
print(f"Total 2024 MLB Home Runs: {home_runs.height}")
```

---

## Key Column Reference (164 Columns)

The full 164 columns are categorized below:

### 1. Game & State Identifiers
| Column | Type | Description |
| :--- | :--- | :--- |
| `GAME_ID` | `string` | Retrosheet game identifier (e.g. `BOS202404090`) |
| `YEAR` | `int32` | Season year (e.g. `2024`) |
| `INN_CT` | `int16` | Inning number (1–9+) |
| `BAT_HOME_ID` | `int16` | Batting team flag (`0` = Visiting, `1` = Home) |
| `OUTS_CT` | `int16` | Outs before play occurred (0, 1, 2) |
| `BALLS_CT` | `int16` | Balls before play occurred (0–3) |
| `STRIKES_CT` | `int16` | Strikes before play occurred (0–2) |
| `PITCH_SEQ_TX` | `string` | Pitches thrown in the plate appearance (e.g. `BBSFX`) |

### 2. Player Identifiers
| Column | Type | Description |
| :--- | :--- | :--- |
| `BAT_ID` | `string` | Retrosheet player ID of batter (e.g. `ohtas001`) |
| `BAT_HAND_CD` | `string` | Batter handedness (`L`, `R`, `S`) |
| `RESP_BAT_ID` | `string` | Batter responsible for the plate appearance |
| `PIT_ID` | `string` | Pitcher ID |
| `PIT_HAND_CD` | `string` | Pitcher handedness (`L`, `R`) |
| `RESP_PIT_ID` | `string` | Pitcher responsible for runners / run |
| `POS2_FLD_ID` - `POS9_FLD_ID` | `string` | Player IDs for fielders by position (Catcher through RF) |

### 3. Base Runners
| Column | Type | Description |
| :--- | :--- | :--- |
| `BASE1_RUN_ID` | `string` | Runner on first before play (empty if vacant) |
| `BASE2_RUN_ID` | `string` | Runner on second before play |
| `BASE3_RUN_ID` | `string` | Runner on third before play |

### 4. Play Details & Scores
| Column | Type | Description |
| :--- | :--- | :--- |
| `EVENT_TX` | `string` | Raw Retrosheet play descriptor (e.g. `HR/7/F`, `K`, `S8/L.1-3`) |
| `EVENT_CD` | `int16` | Chadwick numeric event code (e.g. `23` = Home run) |
| `AWAY_SCORE_CT` | `int16` | Visiting team score before play |
| `HOME_SCORE_CT` | `int16` | Home team score before play |
| `RBI_CT` | `int16` | Runs batted in on play |
| `EVENT_OUTS_CT` | `int16` | Number of outs recorded on play (0, 1, 2, 3) |

### 5. Boolean Indicators
| Column | Type | Description |
| :--- | :--- | :--- |
| `AB_FL` | `bool` | At-bat indicator |
| `H_FL` | `bool` | Hit indicator (single, double, triple, HR) |
| `SH_FL` | `bool` | Sacrifice hit / bunt |
| `SF_FL` | `bool` | Sacrifice fly |
| `DP_FL` | `bool` | Double play turned on play |
| `TP_FL` | `bool` | Triple play turned on play |
| `HR_FL` | `bool` | Home run hit on play |
| `WP_FL` | `bool` | Wild pitch occurred |
| `PB_FL` | `bool` | Passed ball occurred |

---

## Multi-Season Processing

You can fetch multiple seasons in a single call. `retrosheetpy` automatically concatenates the Arrow record batches efficiently:

```python
import retrosheetpy as rs

# 2020 through 2024 (approx 900,000 plays)
multi_events = rs.events(year=range(2020, 2025), backend="polars")
```
