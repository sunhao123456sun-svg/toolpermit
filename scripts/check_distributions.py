"""Validate built wheel/sdist metadata and release-critical contents."""

from __future__ import annotations

import argparse
import tarfile
import zipfile
from pathlib import Path

from packaging.metadata import Metadata
from packaging.utils import parse_sdist_filename, parse_wheel_filename


def _arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", nargs="?", type=Path, default=Path("dist"))
    return parser.parse_args()


def check(directory: Path) -> None:
    wheels = tuple(directory.glob("*.whl"))
    sdists = tuple(directory.glob("*.tar.gz"))
    if len(wheels) != 1 or len(sdists) != 1:
        raise AssertionError("expected exactly one wheel and one .tar.gz sdist")
    wheel = wheels[0]
    sdist = sdists[0]
    wheel_name, wheel_version, _build, _tags = parse_wheel_filename(wheel.name)
    sdist_name, sdist_version = parse_sdist_filename(sdist.name)
    if wheel_name != "toolpermit" or sdist_name != "toolpermit":
        raise AssertionError("distribution name is not toolpermit")
    if wheel_version != sdist_version:
        raise AssertionError("wheel and sdist versions differ")

    with zipfile.ZipFile(wheel) as archive:
        names = set(archive.namelist())
        metadata_name = next(name for name in names if name.endswith(".dist-info/METADATA"))
        metadata = Metadata.from_email(archive.read(metadata_name), validate=True)
        for suffix in (
            "toolpermit/web/static/index.html",
            "toolpermit/web/static/app.css",
            "toolpermit/web/static/app.js",
            ".dist-info/licenses/LICENSE",
        ):
            if not any(name.endswith(suffix) for name in names):
                raise AssertionError(f"wheel is missing {suffix}")

    with tarfile.open(sdist) as archive:
        names = set(archive.getnames())
        metadata_member = next(name for name in names if name.endswith("/PKG-INFO"))
        extracted = archive.extractfile(metadata_member)
        if extracted is None:
            raise AssertionError("cannot read sdist PKG-INFO")
        sdist_metadata = Metadata.from_email(extracted.read(), validate=True)
        for suffix in (
            "docs/quickstart.md",
            "docs/assets/toolpermit-ui.jpg",
            "examples/demo_client.py",
            "SECURITY.md",
            "LICENSE",
        ):
            if not any(name.endswith(suffix) for name in names):
                raise AssertionError(f"sdist is missing {suffix}")

    for parsed in (metadata, sdist_metadata):
        if parsed.name != "toolpermit" or parsed.version != wheel_version:
            raise AssertionError("embedded metadata does not match the distribution filename")
        if parsed.requires_python != ">=3.11":
            raise AssertionError("unexpected Requires-Python metadata")
        if parsed.license_expression != "Apache-2.0":
            raise AssertionError("unexpected license expression")
    print(f"distribution metadata and contents: ok (toolpermit {wheel_version})")


def main() -> int:
    check(_arguments().directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
