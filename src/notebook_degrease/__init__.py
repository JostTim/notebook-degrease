import json, re
from pathlib import Path
from shutil import copy2, rmtree

from os import PathLike

from typing import Any

EXCLUDE_LIST = [
    "*.venv*",
    "*.ipynb_checkpoints*",
    "*.git*",
    "*.pickle",
    "*.svg",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.tif",
    "*.avi",
    "*.mp4",
    "*.xlsx",
    "*.xls",
    "*.mmap",
    "*.hd5",
    "*.hdf5",
    "*.log",
]
DEGREASED_TYPES = ["image/png", "image/svg"]
EXCLUDE_GIT_REMOVAL = ".git"


def printcolor(text: Any, color="black", **kwargs):

    escape = "\N{ESC}["
    foreground = "3"
    endbit = "m"

    colors = {
        "black": foreground + "0",
        "red": foreground + "1",
        "green": foreground + "2",
        "yellow": foreground + "3",
        "blue": foreground + "4",
        "cyan": foreground + "6",
        None: "0",
    }
    colors = {k: escape + str(v) + endbit for k, v in colors.items()}

    text = colors[color] + str(text) + colors[None]
    print(text, **kwargs)


def print_excluded_object(item: Any):
    printcolor("🙅 Excluded ", "cyan", end="")
    printcolor(item, "blue")


def remove_outputs_from_notebook(input_path: PathLike, output_path: PathLike):

    input_path = Path(input_path).resolve()

    with open(input_path, "r", encoding="utf-8") as f:
        notebook = json.load(f)

    for cell in notebook.get("cells", []):
        if cell.get("cell_type") == "code":
            cell["outputs"] = [
                output for output in cell.get("outputs", []) if not must_degrease(output.get("data", {}))
            ]

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(notebook, f, indent=1)


def regexpize(pattern_string: str):
    pattern_string = pattern_string.replace("\\", "/").replace(".", r"\.").replace("*", ".*")
    pattern_string = "^" + pattern_string + "$"
    return pattern_string


def must_degrease(data: dict):
    return any([degrease_type in data.keys() for degrease_type in DEGREASED_TYPES])


def exclude(input):
    return any([pattern.match(str(input)) for pattern in PATTERNS])


PATTERNS = [re.compile(regexpize(exclusion)) for exclusion in EXCLUDE_LIST]


def cleanup_destination(copy_destination: PathLike):

    copy_destination = Path(copy_destination).resolve()
    for root, dirs, files in copy_destination.walk():

        if str(root.relative_to(copy_destination)).startswith(EXCLUDE_GIT_REMOVAL):
            continue

        for dir in dirs:
            path = root / dir
            rmtree(path, ignore_errors=True)

        for file in files:
            path = root / file
            path.unlink(missing_ok=True)

    printcolor("✨ Finished cleaning directory ", "green", end="")
    printcolor(copy_destination, "blue")


def copy_package(package_source: PathLike, copy_destination: PathLike):

    package_source = Path(package_source).resolve()
    copy_destination = Path(copy_destination).resolve()

    degrease_count = 0

    for root, dirs, files in package_source.walk():

        if exclude(root.relative_to(package_source)):
            print_excluded_object(root.relative_to(package_source))
            continue

        for dir in dirs:
            source = root / dir
            if exclude(source.relative_to(package_source)):
                print_excluded_object(source.relative_to(package_source))
                continue
            relative = source.relative_to(package_source)
            destination = copy_destination / relative

            destination.mkdir(parents=True, exist_ok=True)

        for file in files:
            source = root / file
            if exclude(source.relative_to(package_source)):
                print_excluded_object(source.relative_to(package_source))
                continue
            relative = source.relative_to(package_source)
            destination = copy_destination / relative
            if source.name.endswith(".ipynb"):
                remove_outputs_from_notebook(source, destination)
                degrease_count += 1
            else:
                copy2(source, destination)

    printcolor("✅ Finished copying directory ", "green", end="")
    printcolor(str(package_source), "blue", end="")
    printcolor(" into ", "green", end="")
    printcolor(str(copy_destination), "blue")

    printcolor("🪶  Degreased ", "green", end="")
    printcolor(degrease_count, "yellow", end="")
    printcolor(" notebook files (.ipynb) in total.", "green")


def degrease():

    from argparse import ArgumentParser

    parser = ArgumentParser()
    parser.add_argument("-s", "--source")
    parser.add_argument("-d", "--dest")

    args = parser.parse_args()

    if args.source.endswith(".ipynb"):
        remove_outputs_from_notebook(args.source, args.dest)
    else:
        cleanup_destination(args.dest)
        copy_package(args.source, args.dest)
