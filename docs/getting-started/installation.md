# Installation

`retrosheetpy` is available on PyPI and requires **Python 3.11** or higher. It is packaged with pre-compiled wheels for Windows, macOS, and Linux, meaning **no C compiler or build tools are required**.

---

## Basic Installation

Install the base package with `pip` or `uv`:

=== "uv (Recommended)"
    ```bash
    uv add retrosheetpy
    ```

=== "pip"
    ```bash
    pip install retrosheetpy
    ```

---

## Optional Backend Extras

`retrosheetpy` is designed to be lean by default. You can install optional dependencies depending on your workflow:

| Extra | Command | Included Functionality |
| :--- | :--- | :--- |
| **`polars`** | `pip install "retrosheetpy[polars]"` | Native conversion to [Polars DataFrames](https://pola.rs) (`backend="polars"`). |
| **`pandas`** | `pip install "retrosheetpy[pandas]"` | Native conversion to [pandas DataFrames](https://pandas.pydata.org) (`backend="pandas"`). |
| **`dlt`** | `pip install "retrosheetpy[dlt]"` | [Data Load Tool](https://dlthub.com) integration for streaming into Postgres, Snowflake, BigQuery, etc. |
| **`all`** | `pip install "retrosheetpy[all]"` | Installs all optional backends and connectors. |

=== "uv with extras"
    ```bash
    # Install with Polars and dlt
    uv add "retrosheetpy[polars,dlt]"

    # Or install everything
    uv add "retrosheetpy[all]"
    ```

=== "pip with extras"
    ```bash
    pip install "retrosheetpy[all]"
    ```

---

## Verification

After installation, verify that the CLI and Python package are functional:

```bash
retrosheetpy --version
```

Or from Python:

```python
import retrosheetpy as rs

print(rs.__version__)
```
