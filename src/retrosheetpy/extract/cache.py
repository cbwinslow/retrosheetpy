"""Local caching and archive management for downloaded Retrosheet files."""

from __future__ import annotations

import os
import shutil
import zipfile
from pathlib import Path


class CacheManager:
    """Manages raw zip archives and extracted files in the local cache directory."""

    def __init__(self, cache_dir: Path | str | None = None) -> None:
        if cache_dir is None:
            env_val = os.environ.get("RETROSHEETPY_CACHE_DIR")
            self.root = Path(env_val) if env_val else Path.home() / ".cache" / "retrosheetpy"
        else:
            self.root = Path(cache_dir)
        self.root.mkdir(parents=True, exist_ok=True)

    def _dataset_dir(self, dataset: str) -> Path:
        d = self.root / dataset
        d.mkdir(parents=True, exist_ok=True)
        return d

    def get_archive_path(self, dataset: str, key: int | str) -> Path:
        """Returns the path where a raw archive is stored."""
        return self._dataset_dir(dataset) / f"{key}.zip"

    def get_extracted_dir(self, dataset: str, key: int | str) -> Path:
        """Returns the directory containing extracted contents of an archive."""
        return self._dataset_dir(dataset) / f"{key}_extracted"

    def has_archive(self, dataset: str, key: int | str) -> bool:
        """Checks if a valid archive exists in the cache."""
        p = self.get_archive_path(dataset, key)
        return p.is_file() and p.stat().st_size > 0

    def is_extracted(self, dataset: str, key: int | str) -> bool:
        """Checks if an archive has already been unpacked."""
        d = self.get_extracted_dir(dataset, key)
        return d.is_dir() and any(d.iterdir())

    def save_archive(self, dataset: str, key: int | str, content: bytes) -> Path:
        """Atomically saves raw zip content to disk."""
        target = self.get_archive_path(dataset, key)
        tmp = target.with_suffix(".tmp")
        tmp.write_bytes(content)
        tmp.replace(target)
        return target

    def extract_archive(self, dataset: str, key: int | str) -> Path:
        """Extracts an archive into its dedicated extraction directory."""
        archive_path = self.get_archive_path(dataset, key)
        if not archive_path.exists():
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        extracted_dir = self.get_extracted_dir(dataset, key)
        extracted_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(archive_path, "r") as zf:
            zf.extractall(extracted_dir)

        return extracted_dir

    def clear(self, dataset: str | None = None) -> None:
        """Clears all or a specific dataset from the cache."""
        if dataset:
            target = self.root / dataset
            if target.exists():
                shutil.rmtree(target)
        else:
            if self.root.exists():
                shutil.rmtree(self.root)
            self.root.mkdir(parents=True, exist_ok=True)
