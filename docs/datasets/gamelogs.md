# Historical Game Logs

Retrosheet's historical game logs cover every official Major League Baseball game from **1871 to the present day** (over 230,000 games).

Each game log contains **161 columns** recording game date, participating teams, final scores, line scores, team statistics, umpire crews, winning/losing pitchers, and starting lineups.

---

## Usage

```python
import retrosheetpy as rs

# Download and parse 2024 game logs
gl = rs.game_logs(year=2024, backend="polars")

# Look at opening day games
opening_day = gl.filter(gl["date"] == "2024-03-28").select(
    ["visiting_team", "visiting_score", "home_team", "home_score", "attendance"]
)
print(opening_day)
```

---

## Schema Overview (161 Columns)

The game log schema uses strict native types rather than strings:

### 1. General Game Metadata
| Column | Type | Example | Description |
| :--- | :--- | :--- | :--- |
| `date` | `date32` | `2024-03-28` | Official game date |
| `game_number` | `int16` | `0`, `1`, `2` | Doubleheader indicator (`0` = single game) |
| `day_of_week` | `string` | `Thu` | Day of week |
| `visiting_team` | `string` | `LAN` | Visiting team 3-letter code |
| `visiting_league` | `string` | `NL` | Visiting team league (`AL`, `NL`) |
| `visiting_game_num` | `int16` | `1` | Game number for visiting team in season |
| `home_team` | `string` | `SDN` | Home team 3-letter code |
| `home_league` | `string` | `NL` | Home team league |
| `home_game_num` | `int16` | `1` | Game number for home team in season |
| `visiting_score` | `int16` | `5` | Runs scored by visitor |
| `home_score` | `int16` | `2` | Runs scored by home team |
| `outs_total` | `int16` | `54` | Length of game in outs (54 = standard 9 innings) |
| `day_night` | `string` | `D`, `N` | Day or night game indicator |
| `park_id` | `string` | `SEO01` | Retrosheet ballpark ID |
| `attendance` | `int32` | `15952` | Paid attendance (nullable) |
| `game_time_minutes` | `int16` | `185` | Length of game in minutes |

### 2. Line Scores
| Column | Type | Description |
| :--- | :--- | :--- |
| `visiting_linescore` | `string` | Inning-by-inning runs for visitor (e.g. `000101003`) |
| `home_linescore` | `string` | Inning-by-inning runs for home team (e.g. `000000020`) |

### 3. Team Statistics (Both Visiting & Home)
Columns are prefixed with `v_` (visiting) and `h_` (home):
* `at_bats`, `hits`, `doubles`, `triples`, `home_runs`, `rbi` (`int16`)
* `walks`, `intentional_walks`, `strikeouts`, `stolen_bases`, `caught_stealing` (`int16`)
* `errors`, `passed_balls`, `double_plays`, `triple_plays` (`int16`)
* `pitchers_used`, `individual_earned_runs`, `team_earned_runs` (`int16`)

### 4. Personnel & Pitchers of Record
| Column | Type | Description |
| :--- | :--- | :--- |
| `winning_pitcher_id` / `name` | `string` | Winning pitcher ID & full name |
| `losing_pitcher_id` / `name` | `string` | Losing pitcher ID & full name |
| `saving_pitcher_id` / `name` | `string` | Saving pitcher ID & full name (if applicable) |
| `visiting_manager_id` / `name` | `string` | Visiting team manager |
| `home_manager_id` / `name` | `string` | Home team manager |
| `hp_umpire_id` / `name` | `string` | Home plate umpire |

### 5. Starting Lineups
For positions 1 through 9 for both visitor (`v_batter_1_id` ... `v_batter_9_id`) and home (`h_batter_1_id` ... `h_batter_9_id`), including fielding position code (`1`–`10`, where `10` = DH).
