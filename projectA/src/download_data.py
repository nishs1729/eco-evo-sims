#!/usr/bin/env python3
"""Download Project A's public datasets into projectA/data/raw/ and verify them (activity A02).

Run from the repo root:

    uv run python projectA/src/download_data.py          # download missing files, verify all
    uv run python projectA/src/download_data.py --check  # verify only, no downloads

Each file is checked against the MD5 published by the repository (figshare, Zenodo, Dryad).
The script prints the SHA-256 of every file for projectA/data/manifest.yaml.
Archives are unpacked next to the zip (Windows backslash paths are converted).
Files in data/raw/ are never edited after download.

Not downloadable by script:
  - Global Wood Density Database (Dryad doi:10.5061/dryad.234): Dryad's API needs a login and
    its public link has a bot check. Download GlobalWoodDensityDatabase.xls in a browser from
    https://doi.org/10.5061/dryad.234 into data/raw/wood_density/; this script then verifies it.
"""
import hashlib
import pathlib
import sys
import urllib.request
import zipfile

RAW = pathlib.Path(__file__).resolve().parents[1] / "data" / "raw"
UA = {"User-Agent": "eco-evo-sims/0.1 (research data download)"}

# dataset -> list of (filename, url or None for manual download, published md5)
FILES = {
    "uppangala": [  # figshare 10.6084/m9.figshare.c.3304026 (Ecological Archives E092-115), CC0
        ("ECOL_92_115.zip", "https://ndownloader.figshare.com/files/5619033", "83e1659e8ea45219f1a3885542c096fa"),
        ("default.htm", "https://ndownloader.figshare.com/files/5619030", "3874dd7136f8234592551d88232a90c6"),
    ],
    "cwg96": [  # figshare 10.6084/m9.figshare.3549963 (Ecological Archives E091-216), CC0
        ("ECOL_91_216.zip", "https://ndownloader.figshare.com/files/5617140", "3efba91fb81d806da29ea0a35820372f"),
        ("default.htm", "https://ndownloader.figshare.com/files/5617137", "fca04c108a1908bc64d4890d50fe52da"),
    ],
    "anamalai": [  # Zenodo 10.5281/zenodo.10426971 (concept 10426970), CC-BY-4.0
        (name, f"https://zenodo.org/api/records/10426971/files/{name}/content", md5)
        for name, md5 in [
            ("01_README.txt", "74923f1ad84331a426ae7740415ea4f3"),
            ("02_Candura_annual_census.csv", "2c724185637f8b7500e82ced827925ea"),
            ("03_Manamboli_annual_census.csv", "c4ab57d2c2b56dab2ecf8f2e88ede423"),
            ("04_Candura__vernier.csv", "fba68add64cb5809c4ffe8bf758679d6"),
            ("05_Manamboli_vernier.csv", "b5b535d0c63696ef71ce0608d16823f3"),
            ("06_Candura_Height_data.csv", "6c93e44a7f1dd3295b8cf49a76166b14"),
            ("07_Manamboli_Height_data.csv", "13ab6656c677950ab25a42673763d473"),
            ("08_Species_name_match.csv", "583de1a4f6012bfc55e3113ab467c1b8"),
            ("09_R_scrpt_for_manuscript.R", "aeb996d943008f2a4fbe5de9dd783240"),
        ]
    ],
    "wood_density": [  # Dryad 10.5061/dryad.234, CC0; manual download
        ("GlobalWoodDensityDatabase.xls", None, "49c231b6d35bdc7a96954e69e0e95035"),
    ],
}


def digest(path, algo):
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def unpack(zpath):
    """Unpack a zip next to itself, converting backslash paths and refusing paths that escape."""
    out = zpath.with_suffix("")
    with zipfile.ZipFile(zpath) as z:
        for info in z.infolist():
            rel = pathlib.PurePosixPath(info.filename.replace("\\", "/"))
            if rel.is_absolute() or ".." in rel.parts:
                raise ValueError(f"unsafe path in {zpath.name}: {info.filename}")
            target = out / rel
            if info.filename.endswith(("/", "\\")):
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(z.read(info))
    return out


def main(check_only=False):
    ok = True
    for ds, files in FILES.items():
        d = RAW / ds
        d.mkdir(parents=True, exist_ok=True)
        for name, url, md5 in files:
            p = d / name
            if not p.exists():
                if check_only or url is None:
                    print(f"MISSING  {ds}/{name}" + ("  (manual download; see docstring)" if url is None else ""))
                    ok = False
                    continue
                req = urllib.request.Request(url, headers=UA)
                with urllib.request.urlopen(req, timeout=120) as r:
                    p.write_bytes(r.read())
            if digest(p, "md5") != md5:
                print(f"BAD MD5  {ds}/{name}")
                ok = False
                continue
            print(f"OK       {ds}/{name}  sha256={digest(p, 'sha256')}")
            if p.suffix == ".zip" and not check_only and not p.with_suffix("").exists():
                print(f"         unpacked to {unpack(p).relative_to(RAW)}")
    return ok


if __name__ == "__main__":
    sys.exit(0 if main(check_only="--check" in sys.argv) else 1)
