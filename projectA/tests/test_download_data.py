"""Tests for download_data.py and for the integrity of data/raw/ against manifest.yaml.

The integrity tests are skipped when data/raw/ is absent (e.g. a fresh clone: data are git-ignored).
Run `uv run python projectA/src/download_data.py` first to fetch the data.
"""
import hashlib
import pathlib
import zipfile

import pytest
import yaml

import download_data as dd

DATA = pathlib.Path(__file__).resolve().parents[1] / "data"


# --- unit tests (no data needed) -----------------------------------------------------------------

def test_digest_matches_hashlib(tmp_path):
    p = tmp_path / "f.txt"
    p.write_bytes(b"uppangala\r1990\r")
    assert dd.digest(p, "md5") == hashlib.md5(b"uppangala\r1990\r").hexdigest()
    assert dd.digest(p, "sha256") == hashlib.sha256(b"uppangala\r1990\r").hexdigest()


def test_unpack_converts_windows_backslash_paths(tmp_path):
    z = tmp_path / "archive.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr("images\\Fig1.jpg", b"jpeg")
        zf.writestr("data.txt", b"x")
    out = dd.unpack(z)
    assert (out / "images" / "Fig1.jpg").read_bytes() == b"jpeg"
    assert (out / "data.txt").exists()


@pytest.mark.parametrize("bad", ["../escape.txt", "..\\escape.txt", "/abs/escape.txt"])
def test_unpack_refuses_paths_outside_target(tmp_path, bad):
    z = tmp_path / "evil.zip"
    with zipfile.ZipFile(z, "w") as zf:
        zf.writestr(bad, b"x")
    with pytest.raises(ValueError, match="unsafe path"):
        dd.unpack(z)
    assert not (tmp_path / "escape.txt").exists()


def test_every_dataset_has_a_published_checksum():
    for ds, files in dd.FILES.items():
        for name, _url, md5 in files:
            assert len(md5) == 32, (ds, name)


# --- integrity of the local data (skipped without data) -------------------------------------------

needs_data = pytest.mark.skipif(not (DATA / "raw").exists() or not any((DATA / "raw").iterdir()),
                                reason="data/raw/ not present; run download_data.py")


@needs_data
def test_raw_files_match_published_md5():
    assert dd.main(check_only=True), "a raw file is missing or its MD5 differs from the publisher's"


@needs_data
def test_manifest_sha256_matches_files_on_disk():
    manifest = yaml.safe_load((DATA / "manifest.yaml").read_text())
    listed = 0
    for ds in manifest["datasets"]:
        for f in ds.get("files") or []:
            p = DATA / f["path"]
            assert p.exists(), f"{ds['id']}: {f['path']} listed in manifest but missing"
            assert dd.digest(p, "sha256") == f["sha256"], f"{ds['id']}: {f['path']} sha256 differs"
            listed += 1
    assert listed > 0
