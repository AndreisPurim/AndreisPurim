#!/usr/bin/env python3
"""
Hillfort is a filesystem-first personal organization system. Files and
directories are the source of truth; metadata, databases, and indexes are
optional. Information exists in either the Yard (active work) or the Keep
(archive).

The Yard is organized into weekly workspaces. Active files survive by being
carried forward from one week to the next, while abandoned files naturally
become stale. GTD, PARA, Zettelkasten, and similar methodologies may be
used within a workspace, but time is the primary organizing principle.

The Keep is a time-oriented archive for completed and historical material.
Hillfort's central operation is migration: objects move through weekly
workspaces while active and eventually into the archive when preserved.
The filesystem itself records what is active, what has become stale, and
what has been retained over time.
"""

import argparse
import datetime
import json
import pathlib
import re
import shutil
import textwrap


APP_NAME = "fort"
CONFIG_DIR = ".fort"
CONFIG_FILE = "config.json"
INSTALLED_SCRIPT = "hfort.py"
WEEK_TEMPLATE = "week_template.md"
WEEK_RE = re.compile(r"^\d{2}w\d{2}$")
BRACKET_TIME_RE = re.compile(r"^\[(?P<time>[^\]]*)\]\s*(?P<rest>.*)$")
LOOSE_TIME_RE = re.compile(r"^(?P<time>\d{1,2})(?:h)?\s+(?P<rest>.*)$", re.IGNORECASE)
TAG_RE = re.compile(r"^[A-Za-z0-9_]{1,8}$")
TEMP_PATTERNS = (
    re.compile(r"^~\$"),
    re.compile(r".*\.tmp$", re.IGNORECASE),
    re.compile(r".*\.part$", re.IGNORECASE),
    re.compile(r".*\.crdownload$", re.IGNORECASE),
    re.compile(r".*\.bkp$", re.IGNORECASE),
)
BAD_DOWNLOAD_SUFFIXES = {
    ".exe",
    ".msi",
    ".dll",
    ".sys",
    ".ini",
    ".cfg",
    ".log",
    ".tmp",
    ".crdownload",
    ".part",
}
CAPTURABLE_SUFFIXES = {
    ".pdf",
    ".docx",
    ".xlsx",
    ".pptx",
    ".md",
    ".txt",
    ".csv",
    ".tex",
    ".png",
    ".jpg",
    ".jpeg",
    ".svg",
    ".webp",
    ".json",
    ".yaml",
    ".yml",
    ".xml",
    ".zip",
    ".py",
    ".js",
    ".sh",
    ".ipynb",
}
ROOT_ALLOWED_FILES = {"BRAIN.md", "README.md", "TODAY.md", "fort.py"}
ROOT_ALLOWED_DIRS = {CONFIG_DIR, "yard", "keep"}
WEEK_CATEGORIES = ("inbox", "projects", "areas", "resources", "notes", "scratch")
WEEK_CONTROL_FILES = ("week.md", "today.md")
STUB_SUFFIX = ".hf-stub"
IMPORT_MANIFEST = ".hillfort-import"


def current_week_name(day=None):
    day = day or datetime.date.today()
    iso = day.isocalendar()
    return f"{iso.year % 100:02d}w{iso.week:02d}"


def parse_week_name(name):
    if not WEEK_RE.fullmatch(name):
        raise ValueError(f"Invalid week name: {name}")
    year = 2000 + int(name[:2])
    week = int(name[3:])
    return datetime.date.fromisocalendar(year, week, 1)


def next_week_name(name):
    return current_week_name(parse_week_name(name) + datetime.timedelta(days=7))


def timestamp():
    return datetime.datetime.now().replace(microsecond=0).isoformat()


def timestamp_slug():
    return datetime.datetime.now().strftime("%Y%m%d-%H%M")


def semester_name(day=None):
    day = day or datetime.date.today()
    half = 1 if day.month <= 6 else 2
    return f"{day.year % 100:02d}s{half}"


def clean_name(name):
    stem = name.strip().lower()
    stem = re.sub(r"\s+", "_", stem)
    stem = re.sub(r"[^a-z0-9._-]+", "_", stem)
    stem = re.sub(r"_+", "_", stem)
    stem = stem.strip("._-")
    return stem or "untitled"


def is_clean_name(name):
    return bool(re.fullmatch(r"[a-z0-9._-]+", name)) and not name.startswith(".")


def config_path(root):
    return root / CONFIG_DIR / CONFIG_FILE


def read_config(root):
    path = config_path(root)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def write_config(root):
    cfg = {
        "version": 2,
        "yard_dir": "yard",
        "keep_dir": "keep",
        "week_template": f"{CONFIG_DIR}/{WEEK_TEMPLATE}",
        "week_categories": list(WEEK_CATEGORIES),
        "chaos_zones": ["~/Desktop", "~/Downloads", "~/Documents"],
    }
    path = config_path(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def find_root(start):
    here = start.resolve()
    for candidate in (here, *here.parents):
        if config_path(candidate).exists():
            return candidate
    return None


def script_root():
    script = pathlib.Path(__file__).resolve()
    if script.parent.name != CONFIG_DIR:
        return None
    root = script.parent.parent
    if config_path(root).exists():
        return root
    return None


def require_root(args):
    if args.root:
        root = pathlib.Path(args.root).expanduser().resolve()
    else:
        root = find_root(pathlib.Path.cwd()) or script_root()
    if not root or not config_path(root).exists():
        raise SystemExit(
            "No fort root found. Run `python fort.py init [path]` first, "
            "run commands from inside a fort, use the .fort-installed hfort shortcut, "
            "or pass `--root PATH`."
        )
    return root


def week_dir(root, name=None):
    return root / "yard" / (name or current_week_name())


def template_text():
    week = current_week_name()
    return textwrap.dedent(
        f"""\
        # {week}

        ## Projects

        - [__h] ____ | 

        ## Areas

        - [__h] ____ | 

        ## Resources

        - [__h] ____ | 

        ## At work

        - [__h] ____ | 

        ## At home

        - [__h] ____ | 

        ## Waiting

        - [__h] WAIT | 

        ## Notes

        """
    )


def today_text():
    return textwrap.dedent(
        f"""\
        # Today - {datetime.date.today().isoformat()}

        ## Focus

        - [__h] ____ | 

        ## Scratch

        """
    )


def brain_text():
    return textwrap.dedent(
        """\
        # Brain

        ## Now

        ## Thinking

        ## Sleeping

        ## Areas

        ## Done
        """
    )


def readme_text():
    return textwrap.dedent(
        """\
        # Fort

        Fort is a minimal filesystem for time-bound workspaces and low-friction organization.

        - `yard/YYwWW/` is the weekly messy workspace.
        - `yard/YYwWW/projects/` is for active projects with defined outcomes.
        - `yard/YYwWW/areas/` is for ongoing responsibilities.
        - `yard/YYwWW/resources/` is for active reference material.
        - `yard/YYwWW/notes/` is for working knowledge notes.
        - `yard/YYwWW/scratch/` is for temporary working material.
        - `yard/YYwWW/week.md` is the weekly whiteboard.
        - `yard/YYwWW/today.md` is the daily scratch/control file.
        - `yard/YYwWW/inbox/` is the capture bucket for unprocessed material.
        - `keep/YYYY/` is for long-term time-bound archive material.
        - `keep/_intake/YYYY/` is for preserved, unprocessed dumps.

        The files are the system. The script only helps with setup and transitions.
        """
    )


def install_managed_script(root):
    source = pathlib.Path(__file__).resolve()
    target = root / CONFIG_DIR / INSTALLED_SCRIPT
    if source != target:
        shutil.copy2(source, target)
    target.chmod(0o755)
    return target


def shortcut_hint(installed_script):
    bin_dir = pathlib.Path.home() / ".local" / "bin"
    link = bin_dir / "hfort"
    return textwrap.dedent(
        f"""\
        To run fort as `hfort` from anywhere:

          mkdir -p {bin_dir}
          ln -sf {installed_script} {link}

        Then make sure `{bin_dir}` is in your PATH.
        """
    ).rstrip()


def ensure_week(root, name=None):
    target = week_dir(root, name)
    target.mkdir(parents=True, exist_ok=True)
    for category in WEEK_CATEGORIES:
        (target / category).mkdir(exist_ok=True)
    week_md = target / "week.md"
    if not week_md.exists():
        template = root / CONFIG_DIR / WEEK_TEMPLATE
        if template.exists():
            text = template.read_text(encoding="utf-8")
            text = re.sub(r"^# \d{2}w\d{2}", f"# {target.name}", text, count=1, flags=re.MULTILINE)
        else:
            text = template_text().replace(f"# {current_week_name()}", f"# {target.name}", 1)
        week_md.write_text(text, encoding="utf-8")
    today_md = target / "today.md"
    if not today_md.exists():
        today_md.write_text(today_text(), encoding="utf-8")
    return target


def iter_week_dirs(root):
    yard = root / "yard"
    if not yard.exists():
        return []
    weeks = [p for p in yard.iterdir() if p.is_dir() and WEEK_RE.fullmatch(p.name)]
    return sorted(weeks, key=lambda p: p.name)


def latest_week(root):
    weeks = iter_week_dirs(root)
    if not weeks:
        return ensure_week(root)
    return weeks[-1]


def current_week(root):
    names = [current_week_name()]
    names.extend(week.name for week in iter_week_dirs(root))
    return ensure_week(root, max(names))


def resolve_existing_path(root, value):
    raw = pathlib.Path(value).expanduser()
    candidates = []
    if raw.is_absolute():
        candidates.append(raw)
    else:
        candidates.extend([pathlib.Path.cwd() / raw, root / raw])
    for candidate in candidates:
        resolved = candidate.resolve()
        if resolved.exists():
            return resolved
    raise SystemExit(f"Path does not exist: {value}")


def relative_to_root(root, path):
    try:
        return path.resolve().relative_to(root)
    except ValueError:
        return None


def category_for_yard_path(root, path):
    rel = relative_to_root(root, path)
    if not rel or len(rel.parts) < 3 or rel.parts[0] != "yard" or not WEEK_RE.fullmatch(rel.parts[1]):
        return None
    return rel.parts[2] if rel.parts[2] in WEEK_CATEGORIES else None


def is_in_yard_week(root, path):
    rel = relative_to_root(root, path)
    return bool(rel and len(rel.parts) >= 2 and rel.parts[0] == "yard" and WEEK_RE.fullmatch(rel.parts[1]))


def conflict_destination(path):
    if not path.exists():
        return path
    stamp = timestamp_slug()
    if path.is_dir() or not path.suffix:
        candidate = path.with_name(f"{path.name}.conflict-{stamp}")
    else:
        candidate = path.with_name(f"{path.stem}.conflict-{stamp}{path.suffix}")
    return unique_destination(candidate)


def stub_path_for(path):
    return path.with_name(f"{path.name}{STUB_SUFFIX}")


def write_stub(root, source, dest, status):
    stub = stub_path_for(source)
    stub = unique_destination(stub)
    from_rel = relative_to_root(root, source) or source
    to_rel = relative_to_root(root, dest) or dest
    time_key = "archived-at" if status == "archived" else "carried-at"
    stub.write_text(
        textwrap.dedent(
            f"""\
            hillfort-stub-version: 1
            status: {status}
            from: {from_rel}
            to: {to_rel}
            {time_key}: {timestamp()}
            """
        ),
        encoding="utf-8",
    )
    return stub


def normalize_task_line(line):
    if not line.lstrip().startswith("-"):
        return line
    content = line.strip()[1:].strip()
    if not content:
        return line.rstrip()

    raw_time = "__h"
    bracket_match = BRACKET_TIME_RE.match(content)
    if bracket_match:
        raw_time = bracket_match.group("time")
        content = bracket_match.group("rest").strip()
    else:
        loose_match = LOOSE_TIME_RE.match(content)
        if loose_match:
            raw_time = loose_match.group("time")
            content = loose_match.group("rest").strip()

    if "|" in content:
        before, desc = content.split("|", 1)
        raw_tag = before.strip() or "____"
        desc = desc.strip()
    else:
        parts = content.split(None, 1)
        if len(parts) == 2 and TAG_RE.fullmatch(parts[0]):
            raw_tag = parts[0]
            desc = parts[1].strip()
        else:
            raw_tag = "____"
            desc = content

    raw_time = raw_time.strip().lower()
    digits = re.search(r"\d{1,2}", raw_time)
    if raw_time in {"", "__", "__h", "h"}:
        time = "__h"
    elif digits:
        time = f"{int(digits.group(0)):02d}h"
    else:
        time = "__h"

    raw_tag = raw_tag.strip().upper()
    raw_tag = re.sub(r"[^A-Z0-9_]", "", raw_tag)
    if not raw_tag:
        raw_tag = "____"
    tag = raw_tag[:4].ljust(4, "_")
    return f"- [{time}] {tag} | {desc}".rstrip()


def resolve_week_md(root, target):
    if target:
        path = pathlib.Path(target).expanduser()
        if path.is_file():
            return path.resolve()
        if WEEK_RE.fullmatch(target):
            return root / "yard" / target / "week.md"
        return (root / "yard" / target / "week.md").resolve()
    return current_week(root) / "week.md"


def command_init(args):
    root = pathlib.Path(args.path or ".").expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    (root / CONFIG_DIR).mkdir(exist_ok=True)
    (root / "yard").mkdir(exist_ok=True)
    (root / "keep" / str(datetime.date.today().year)).mkdir(parents=True, exist_ok=True)
    (root / "keep" / "_intake" / str(datetime.date.today().year)).mkdir(parents=True, exist_ok=True)

    write_config(root)
    template = root / CONFIG_DIR / WEEK_TEMPLATE
    if not template.exists():
        template.write_text(template_text(), encoding="utf-8")
    brain = root / "BRAIN.md"
    if not brain.exists():
        brain.write_text(brain_text(), encoding="utf-8")
    readme = root / "README.md"
    if not readme.exists():
        readme.write_text(readme_text(), encoding="utf-8")
    week = ensure_week(root)
    installed_script = install_managed_script(root)
    print(f"Initialized fort at {root}")
    print(f"Current week: {week.relative_to(root)}")
    print(f"Installed script: {installed_script.relative_to(root)}")
    print()
    print(shortcut_hint(installed_script))


def command_current(args):
    root = require_root(args)
    print(current_week(root))


def move_with_stub(root, source, dest, status):
    source = source.resolve()
    dest = conflict_destination(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(dest))
    stub = write_stub(root, source, dest, status)
    return dest, stub


def destination_for_carry(root, source, target_week=None):
    target_week = target_week or current_week(root)
    rel = relative_to_root(root, source)
    if not rel or len(rel.parts) < 2 or rel.parts[0] != "yard" or not WEEK_RE.fullmatch(rel.parts[1]):
        raise SystemExit("carry expects an item from a yard week, for example yard/26w21/projects/thesis")
    if rel.parts[1] == target_week.name:
        raise SystemExit(f"Already in current target week: {source}")
    if len(rel.parts) >= 3 and rel.parts[2] in WEEK_CATEGORIES:
        return target_week.joinpath(*rel.parts[2:])
    return target_week / "inbox" / source.name


def command_carry(args):
    root = require_root(args)
    source = resolve_existing_path(root, args.path)
    dest = destination_for_carry(root, source)
    moved, stub = move_with_stub(root, source, dest, "carried")
    print(f"Carried {relative_to_root(root, source) or source} -> {relative_to_root(root, moved) or moved}")
    print(f"Stub: {relative_to_root(root, stub) or stub}")


def command_newweek(args):
    root = require_root(args)
    items = list(args.items)
    weeks = iter_week_dirs(root)
    if not args.week and items and WEEK_RE.fullmatch(items[0]):
        args.week = items.pop(0)
    if args.week:
        name = args.week
    elif weeks:
        name = next_week_name(weeks[-1].name)
    else:
        name = current_week_name()
    if not WEEK_RE.fullmatch(name):
        raise SystemExit("Week must use YYwWW format, for example 26w18.")
    week = ensure_week(root, name)
    carried = []
    for item in items:
        source = resolve_existing_path(root, item)
        dest = destination_for_carry(root, source, week)
        moved, stub = move_with_stub(root, source, dest, "carried")
        carried.append((source, moved, stub))
    weeks = [p for p in iter_week_dirs(root) if p.name < name]
    if weeks:
        inbox = weeks[-1] / "inbox"
        leftovers = sorted(p for p in inbox.iterdir()) if inbox.exists() else []
    else:
        leftovers = []
    print(f"Ready: {week.relative_to(root)}")
    for source, moved, stub in carried:
        print(f"Carried {relative_to_root(root, source) or source} -> {relative_to_root(root, moved) or moved}")
        print(f"Stub: {relative_to_root(root, stub) or stub}")
    if leftovers:
        print(f"Previous inbox has {len(leftovers)} item(s) to process:")
        for item in leftovers[:12]:
            print(f"  - {item.name}")
        if len(leftovers) > 12:
            print(f"  ... and {len(leftovers) - 12} more")


def stale_items(root):
    current = current_week(root)
    for week in iter_week_dirs(root):
        if week.name >= current.name:
            continue
        for category in WEEK_CATEGORIES:
            category_dir = week / category
            if not category_dir.exists():
                continue
            for item in sorted(category_dir.iterdir(), key=lambda p: p.name.lower()):
                if item.name.endswith(STUB_SUFFIX):
                    continue
                yield week, category, item


def command_stale(args):
    root = require_root(args)
    grouped = {}
    for week, category, item in stale_items(root):
        grouped.setdefault(week.name, {}).setdefault(category, []).append(item)
    if not grouped:
        print("No stale yard items found.")
        return
    for week_name in sorted(grouped):
        print(f"{week_name}:")
        for category in WEEK_CATEGORIES:
            items = grouped[week_name].get(category, [])
            if not items:
                continue
            print(f"  {category}:")
            for item in items:
                print(f"    - {item.relative_to(root)}")


def command_archive(args):
    root = require_root(args)
    source = resolve_existing_path(root, args.path)
    if not is_in_yard_week(root, source):
        raise SystemExit("archive expects an item from yard/YYwWW")
    year = args.year or str(datetime.date.today().year)
    if not re.fullmatch(r"\d{4}", year):
        raise SystemExit("--year must use YYYY format")
    dest_dir = root / "keep" / year
    dest = dest_dir / clean_name(source.name)
    moved, stub = move_with_stub(root, source, dest, "archived")
    print(f"Archived {relative_to_root(root, source) or source} -> {relative_to_root(root, moved) or moved}")
    print(f"Stub: {relative_to_root(root, stub) or stub}")


def intake_destination(root, source, day=None):
    day = day or datetime.date.today()
    base_name = f"{day.isoformat()}-{clean_name(source.name)}"
    intake = root / "keep" / "_intake" / str(day.year)
    intake.mkdir(parents=True, exist_ok=True)
    candidate = intake / base_name
    if not candidate.exists():
        return candidate
    for number in range(2, 1000):
        candidate = intake / f"{base_name}-{number}"
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not find a unique intake destination for {source}")


def write_import_manifest(dest, source, mode):
    manifest = dest / IMPORT_MANIFEST
    manifest.write_text(
        textwrap.dedent(
            f"""\
            hillfort-import-version: 1
            imported-at: {timestamp()}
            source-path: {source}
            mode: {mode}
            status: unprocessed
            """
        ),
        encoding="utf-8",
    )
    return manifest


def command_dump(args):
    root = require_root(args)
    source = resolve_existing_path(root, args.path)
    dest = intake_destination(root, source)
    if args.copy:
        if source.is_dir():
            shutil.copytree(source, dest)
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, dest / source.name)
        mode = "copy"
    else:
        if source.is_dir():
            shutil.move(str(source), str(dest))
        else:
            dest.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(dest / source.name))
        mode = "move"
    manifest = write_import_manifest(dest, source, mode)
    print(f"Imported dump ({mode}) -> {relative_to_root(root, dest) or dest}")
    print(f"Manifest: {relative_to_root(root, manifest) or manifest}")


def command_intake_list(args):
    root = require_root(args)
    intake = root / "keep" / "_intake"
    if not intake.exists():
        print("No intake area found.")
        return
    found = []
    for item in sorted(intake.glob("*/*"), key=lambda p: str(p.relative_to(intake))):
        if not item.is_dir():
            continue
        manifest = item / IMPORT_MANIFEST
        status = "unknown"
        if manifest.exists():
            for line in manifest.read_text(encoding="utf-8").splitlines():
                if line.startswith("status:"):
                    status = line.split(":", 1)[1].strip()
                    break
        if status == "unprocessed" or args.all:
            found.append((item, status))
    if not found:
        print("No unprocessed intake dumps found.")
        return
    for item, status in found:
        print(f"{item.relative_to(root)} [{status}]")


def collect_week_tasks(week_md):
    if not week_md.exists():
        raise SystemExit(f"No week.md found at {week_md}")
    lines = []
    section = None
    for raw in week_md.read_text(encoding="utf-8").splitlines():
        stripped = raw.strip()
        if stripped.startswith("## "):
            section = stripped.removeprefix("## ").strip()
        elif stripped.startswith("-"):
            normalized = normalize_task_line(raw)
            if "|" in normalized:
                lines.append((section or "Tasks", normalized))
    return lines


def command_today(args):
    root = require_root(args)
    week_md = resolve_week_md(root, args.week)
    tasks = collect_week_tasks(week_md)
    today = datetime.date.today().isoformat()
    out = [f"# Today - {today}", "", f"From `{week_md.relative_to(root)}`", ""]
    if not tasks:
        out.append("No tasks found.")
    else:
        current = None
        for section, task in tasks:
            if section != current:
                if current is not None and out[-1] != "":
                    out.append("")
                current = section
                out.extend([f"## {section}", ""])
            out.append(task)
        out.append("")
    text = "\n".join(out)
    if args.write:
        target = week_md.parent / "today.md"
        target.write_text(text + "\n", encoding="utf-8")
        print(f"Wrote {target.relative_to(root)}")
    else:
        print(text)


def command_status(args):
    root = require_root(args)
    weeks = iter_week_dirs(root)
    current = current_week(root)
    inbox = current / "inbox"
    inbox_count = len(list(inbox.iterdir())) if inbox.exists() else 0
    archive = root / "keep" / str(datetime.date.today().year)
    intake = root / "keep" / "_intake" / str(datetime.date.today().year)
    print(f"Fort root: {root}")
    print(f"Current week: {current.name}")
    print(f"Current inbox: {inbox_count} item(s)")
    print(f"Year archive: {archive.relative_to(root)} {'ok' if archive.exists() else 'missing'}")
    print(f"Intake area: {intake.relative_to(root)} {'ok' if intake.exists() else 'missing'}")
    if weeks:
        print("Latest weeks:")
        for week in weeks[-5:]:
            marker = "*" if week == current else "-"
            print(f"  {marker} {week.name}")
    else:
        print("Latest weeks: none")


def command_format(args):
    root = require_root(args)
    week_md = resolve_week_md(root, args.week)
    if not week_md.exists():
        raise SystemExit(f"No week.md found at {week_md}")
    old = week_md.read_text(encoding="utf-8")
    new = "\n".join(normalize_task_line(line) for line in old.splitlines()) + "\n"
    if new == old:
        print(f"Already formatted: {week_md.relative_to(root)}")
        return
    week_md.write_text(new, encoding="utf-8")
    print(f"Formatted {week_md.relative_to(root)}")


def lint_root(root, issues):
    for item in root.iterdir():
        if item.name.startswith(".") and item.name not in {CONFIG_DIR, ".git", ".gitignore"}:
            issues.append(("WARN", item, "hidden root item"))
        if item.is_file() and item.name not in ROOT_ALLOWED_FILES and item.name != ".gitignore":
            issues.append(("ERROR", item, "unexpected root file"))
        if item.is_dir() and item.name not in ROOT_ALLOWED_DIRS and item.name != ".git":
            issues.append(("WARN", item, "unexpected root directory"))


def lint_tree(root, issues):
    yard = root / "yard"
    if not yard.exists():
        issues.append(("ERROR", yard, "missing yard directory"))
    else:
        for child in yard.iterdir():
            if child.is_dir() and not WEEK_RE.fullmatch(child.name):
                issues.append(("ERROR", child, "yard folder is not YYwWW"))
            if child.is_dir() and WEEK_RE.fullmatch(child.name):
                for category in WEEK_CATEGORIES:
                    if not (child / category).is_dir():
                        issues.append(("ERROR", child / category, "missing weekly category directory"))
                for filename in WEEK_CONTROL_FILES:
                    if not (child / filename).exists():
                        issues.append(("ERROR", child / filename, f"missing {filename}"))

    for path in root.rglob("*"):
        rel_parts = path.relative_to(root).parts
        if CONFIG_DIR in rel_parts or ".git" in rel_parts:
            continue
        if path.name.startswith(".") and path.name not in {".gitkeep", ".gitignore"}:
            issues.append(("WARN", path, "hidden file or folder"))
        if not is_clean_name(path.name) and path.name not in {"BRAIN.md", "README.md", "TODAY.md"}:
            issues.append(("WARN", path, "non-conforming name"))
        if path.is_file():
            if any(pattern.match(path.name) for pattern in TEMP_PATTERNS):
                issues.append(("ERROR", path, "temporary file"))
            try:
                size = path.stat().st_size
            except OSError:
                size = 0
            if "yard" in rel_parts and size > 10 * 1024 * 1024:
                issues.append(("WARN", path, "large file in yard"))
            if size > 50 * 1024 * 1024:
                issues.append(("INFO", path, "very large file"))


def command_lint(args):
    root = require_root(args)
    issues = []
    lint_root(root, issues)
    lint_tree(root, issues)
    if not issues:
        print("No lint issues found.")
        return
    severity_order = {"ERROR": 0, "WARN": 1, "INFO": 2}
    for sev, path, message in sorted(issues, key=lambda x: (severity_order[x[0]], str(x[1]))):
        try:
            shown = path.relative_to(root)
        except ValueError:
            shown = path
        print(f"{sev}: {shown}: {message}")
    if any(sev == "ERROR" for sev, _, _ in issues):
        raise SystemExit(1)


def patrol_candidates(root):
    cfg = read_config(root)
    zones = cfg.get("chaos_zones", ["~/Desktop", "~/Downloads", "~/Documents"])
    now = datetime.datetime.now()
    for raw_zone in zones:
        zone = pathlib.Path(raw_zone).expanduser()
        if not zone.exists() or not zone.is_dir():
            continue
        for item in sorted(zone.iterdir(), key=lambda p: p.name.lower()):
            if item.name.startswith(".") or item.name in {"desktop.ini", "Thumbs.db", ".DS_Store"}:
                continue
            if any(pattern.match(item.name) for pattern in TEMP_PATTERNS):
                continue
            suffix = item.suffix.lower()
            if suffix in BAD_DOWNLOAD_SUFFIXES:
                continue
            try:
                modified = datetime.datetime.fromtimestamp(item.stat().st_mtime)
            except OSError:
                continue
            if now - modified < datetime.timedelta(hours=1):
                continue
            if item.is_dir():
                yield zone, item, "folder"
            elif suffix in CAPTURABLE_SUFFIXES:
                yield zone, item, "capturable"
            else:
                yield zone, item, "unknown"


def command_patrol(args):
    root = require_root(args)
    items = list(patrol_candidates(root))
    if not items:
        print("No patrol candidates found.")
        return
    print("Patrol report:")
    current_zone = None
    for zone, item, kind in items:
        if zone != current_zone:
            current_zone = zone
            print(f"\n{zone}:")
        print(f"  - {item.name} [{kind}]")
    print("\nReport only. V1 patrol does not move files.")


def unique_destination(path):
    if not path.exists():
        return path
    base = path.with_suffix("")
    suffix = path.suffix
    for number in range(2, 1000):
        candidate = pathlib.Path(f"{base}_{number}{suffix}")
        if not candidate.exists():
            return candidate
    raise SystemExit(f"Could not find a unique destination for {path}")


def command_keep(args):
    root = require_root(args)
    src = pathlib.Path(args.src).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Source does not exist: {src}")
    year = getattr(args, "year", None) or str(datetime.date.today().year)
    dest_dir = root / "keep" / year
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = unique_destination(dest_dir / clean_name(src.name))
    shutil.move(str(src), str(dest))
    if is_in_yard_week(root, src):
        stub = write_stub(root, src, dest, "archived")
        print(f"Stub: {relative_to_root(root, stub) or stub}")
    print(f"Kept {src} -> {dest}")


def build_parser():
    parser = argparse.ArgumentParser(
        prog="fort.py",
        description="Bootstrap and manage a plain-files fort.",
    )
    parser.add_argument(
        "--root",
        help="Fort root. If omitted, search upward for .fort/config.json, then infer from an installed .fort script.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("init", help="Create a fort filesystem.")
    p.add_argument("path", nargs="?", help="Target fort root. Defaults to current directory.")
    p.set_defaults(func=command_init)

    p = sub.add_parser("current", help="Print the current week folder path.")
    p.set_defaults(func=command_current)

    for name in ("new-week", "newweek", "roll"):
        p = sub.add_parser(name, help="Create the next weekly yard and optionally carry items into it.")
        p.add_argument("items", nargs="*", help="Older yard items to carry into the new week.")
        p.add_argument("--week", help="Explicit YYwWW target. Defaults to the week after the latest yard week.")
        p.set_defaults(func=command_newweek)

    p = sub.add_parser("carry", help="Move an older yard item into the current week and leave a stub.")
    p.add_argument("path", help="Yard item to carry, for example yard/26w21/projects/thesis.")
    p.set_defaults(func=command_carry)

    p = sub.add_parser("stale", help="List older yard items that were not carried forward.")
    p.set_defaults(func=command_stale)

    p = sub.add_parser("archive", help="Move a yard item into keep/YYYY and leave a stub.")
    p.add_argument("path", help="Yard item to archive.")
    p.add_argument("--year", help="Archive year, YYYY. Defaults to the current year.")
    p.set_defaults(func=command_archive)

    for name in ("dump", "import-dump"):
        p = sub.add_parser(name, help="Move or copy a messy folder into keep/_intake/YYYY.")
        p.add_argument("path", help="Folder or file to import into intake.")
        p.add_argument("--copy", action="store_true", help="Copy instead of moving.")
        p.set_defaults(func=command_dump)

    p = sub.add_parser("intake-list", help="List unprocessed dump folders in keep/_intake.")
    p.add_argument("--all", action="store_true", help="Show all intake folders, not only unprocessed ones.")
    p.set_defaults(func=command_intake_list)

    p = sub.add_parser("today", help="Print or write a lightweight daily view.")
    p.add_argument("week", nargs="?", help="Optional YYwWW or week.md path.")
    p.add_argument("--write", action="store_true", help="Write TODAY.md instead of printing.")
    p.set_defaults(func=command_today)

    p = sub.add_parser("status", help="Show fort status.")
    p.set_defaults(func=command_status)

    p = sub.add_parser("format", help="Normalize one week.md.")
    p.add_argument("week", nargs="?", help="Optional YYwWW or week.md path.")
    p.set_defaults(func=command_format)

    p = sub.add_parser("lint", help="Report filesystem issues.")
    p.set_defaults(func=command_lint)

    p = sub.add_parser("patrol", help="Report files in chaos zones that could be captured.")
    p.add_argument("--dry-run", action="store_true", help="Accepted for clarity; patrol is report-only in V1.")
    p.set_defaults(func=command_patrol)

    p = sub.add_parser("keep", help="Move a file or folder into keep/YYYY.")
    p.add_argument("src", help="File or folder to preserve.")
    p.add_argument("--year", help="Archive year, YYYY. Defaults to the current year.")
    p.set_defaults(func=command_keep)
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()
