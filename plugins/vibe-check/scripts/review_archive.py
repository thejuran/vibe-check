"""No-clobber archive moves for the Finalize close-out.

Rule: archive names are unique, keep the phase, and never overwrite. A second
close-out on the same day gets a `-N` suffix instead of replacing the first
archive, for the prior REVIEW.md report (`REVIEW-<phase>-<date>[-N].md`), an
unstamped report (`REVIEW-unstamped-<date>[-N].md`) and the review state file
(`<state>.json.archived-<date>[-N]`).

The move is os.link (which fails when the target exists) followed by
os.unlink of the source, so an existing archive can never be replaced even if
another process creates the chosen name between selection and move.

Some filesystems have no hard links (exFAT/FAT drives, SMB shares, many FUSE
mounts): os.link raises an OSError other than FileExistsError there. The move
then falls back to a copy that is just as no-clobber: the target is created
with O_CREAT|O_EXCL (it fails when the name exists, and the next free name is
tried), the bytes are written and fsynced, and the copy is read back and
compared before the source is removed. A copy that does not match is removed
again and the source is left in place.

If the source cannot be removed after the archive name was claimed, the
archive name is released again (the second link or the copy is removed), so
exactly one live copy remains and a retry is safe. If that also fails, the
error names both paths. Every failure leaves the source where it was.

Forward migration (`migrate`) moves a previous-format state out of the older
plugin's reach. The old file is copied to the current-format location, the copy
is verified byte for byte, and only then is the old file archived, no-clobber,
as `<key>.json.migrated-format-53[-N]` next to where it was. An older plugin's
resolver builds only `<key>.json`, so it no longer finds the review, and the
archive is the recoverable original. Retrying after any interruption is safe:
an existing current-format file is never copied over (the one exception is a
truncated copy left by an interrupted migration, which is a strict prefix of
the old file and so holds nothing the old file lacks), and the old file leaves
its place only through the no-clobber archive move.

CLI (prints the archived path on success; `migrate` prints one line when it
did something and nothing when there was nothing to migrate):
  review_archive.py review-md --phase P [--dir .turingmind] [--date YYYY-MM-DD]
  review_archive.py unstamped [--dir .turingmind] [--date YYYY-MM-DD]
  review_archive.py state --state-file F [--date YYYY-MM-DD]
  review_archive.py migrate --legacy OLD --current NEW
Exit 0 = archived; 1 = source missing or the move failed (the source is left
in place, and stderr says so); 2 = usage error.
The date defaults to the local date, matching `$(date +%Y-%m-%d)`.
"""

import argparse
import datetime
import os
import sys

PHASE_CHARS = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789._-")
UNKNOWN_PHASE = "unknown"
MAX_ATTEMPTS = 1000
# Equals ".migrated-" + statepath.FORMAT_SUBDIR (a test pins the two together).
MIGRATED_SUFFIX = ".migrated-format-53"


def safe_phase(raw):
    """The phase id when it matches ^[A-Za-z0-9._-]+$, else 'unknown'."""
    if isinstance(raw, str) and raw and all(c in PHASE_CHARS for c in raw):
        return raw
    return UNKNOWN_PHASE


def archive_name(dir_, base, suffix):
    """First free name among base+suffix, base-2+suffix, base-3+suffix, ..."""
    name = base + suffix
    n = 2
    while os.path.lexists(os.path.join(dir_, name)):
        name = "%s-%d%s" % (base, n, suffix)
        n += 1
    return name


def _write_all(fd, data):
    """os.write until every byte is written; returns the count written."""
    view = memoryview(data)
    total = 0
    while total < len(data):
        n = os.write(fd, view[total:])
        if n <= 0:
            break
        total += n
    return total


def _copy_no_clobber(src, target):
    """Copy src to a NEW file at target, for filesystems without hard links.

    Raises FileExistsError when target exists (never overwritten). On any
    other failure the partial copy is removed and the error propagates; src
    is never touched.
    """
    with open(src, "rb") as fh:
        data = fh.read()
    mode = os.stat(src).st_mode & 0o777
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY
                 | getattr(os, "O_BINARY", 0), mode)
    try:
        try:
            _write_all(fd, data)
            os.fsync(fd)
        finally:
            os.close(fd)
        with open(target, "rb") as fh:
            if fh.read() != data:
                raise OSError("the archive copy %s does not match %s"
                              % (target, src))
    except BaseException:
        try:
            os.unlink(target)
        except OSError:
            pass
        raise


def _place(src, target):
    """Claim target as a second name for src's bytes; never overwrites."""
    try:
        os.link(src, target)
    except FileExistsError:
        raise
    except OSError:
        # No hard links on this filesystem: exclusive-create copy instead.
        _copy_no_clobber(src, target)


def _release(target, src, cause):
    """The source could not be removed: give the archive name back so that
    exactly one live copy remains, then raise."""
    try:
        os.unlink(target)
    except OSError as exc:
        raise OSError(
            "archived %s as %s but could not remove the source (%s), and could "
            "not remove the archive again (%s): both files exist; keep %s and "
            "delete %s by hand" % (src, target, cause, exc, src, target))
    raise OSError("could not remove %s after archiving it (%s); the archive was "
                  "removed again" % (src, cause))


def archive(src, dir_, base, suffix):
    """Move src into dir_ under a free archive name; return the final path.

    Raises FileNotFoundError when src is missing, FileExistsError when no
    free name could be claimed, and OSError when the move failed. Never
    overwrites an existing file; on every failure src is left in place.
    """
    if not os.path.isfile(src):
        raise FileNotFoundError("no file to archive: %s" % src)
    os.makedirs(dir_, exist_ok=True)
    for _ in range(MAX_ATTEMPTS):
        target = os.path.join(dir_, archive_name(dir_, base, suffix))
        try:
            _place(src, target)
        except FileExistsError:
            continue  # claimed by someone else since selection: pick again
        break
    else:
        raise FileExistsError("no free archive name for %s" % base)
    try:
        os.unlink(src)
    except OSError as exc:
        _release(target, src, exc)
    return target


def _strict_prefix(head_path, whole_path):
    """True iff head_path's bytes are a strict prefix of whole_path's."""
    with open(head_path, "rb") as fh:
        head = fh.read()
    with open(whole_path, "rb") as fh:
        whole = fh.read()
    return len(head) < len(whole) and whole.startswith(head)


def _closed_under_current(current):
    """True iff the current-format state for this key was archived by a
    close-out (`<current>.archived-<date>[-N]` exists)."""
    dir_ = os.path.dirname(current) or "."
    prefix = os.path.basename(current) + ".archived-"
    try:
        names = os.listdir(dir_)
    except FileNotFoundError:
        return False
    return any(n.startswith(prefix) for n in names)


def _bring_forward(legacy, current):
    """Make sure the current-format file exists; True iff it was copied now.

    An existing current-format file is kept as it is, unless it is a strict
    prefix of the old file (a copy cut short by an interruption), which is
    replaced by a verified copy. A review that was already closed under the
    current format is never brought back.
    """
    if os.path.lexists(current):
        if not _strict_prefix(current, legacy):
            return False
        os.unlink(current)  # a truncated copy: everything in it is in legacy
    elif _closed_under_current(current):
        return False
    os.makedirs(os.path.dirname(current) or ".", exist_ok=True)
    _copy_no_clobber(legacy, current)
    return True


def migrate(legacy, current):
    """Forward-migrate `legacy` to `current`; a one-line report, or None when
    there is nothing to migrate.

    Order: copy, verify, then archive the old file no-clobber. Raises OSError
    on failure; the old file is then still in place, and `current`, if it
    exists, is a verified copy or the untouched current-format state.
    """
    if not os.path.isfile(legacy):
        return None
    copied = _bring_forward(legacy, current)
    target = archive(legacy, os.path.dirname(legacy) or ".",
                     os.path.basename(legacy) + MIGRATED_SUFFIX, "")
    if copied:
        return ("state migrated forward to %s; the previous file was archived "
                "as %s" % (current, target))
    if os.path.lexists(current):
        return ("the previous-format state was archived as %s; the "
                "current-format state %s is used" % (target, current))
    return ("the previous-format state was archived as %s; this review was "
            "already closed in the current format, so it was not copied"
            % target)


def _date_arg(value):
    try:
        parsed = datetime.datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    if len(value) != 10 or parsed.strftime("%Y-%m-%d") != value:
        raise argparse.ArgumentTypeError("date must be YYYY-MM-DD")
    return value


class _Parser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write("review_archive: %s\n" % message)
        raise SystemExit(2)


def _parse(argv):
    parser = _Parser(prog="review_archive.py")
    sub = parser.add_subparsers(dest="cmd")
    p_r = sub.add_parser("review-md")
    p_r.add_argument("--phase", required=True)
    p_r.add_argument("--dir", default=".turingmind")
    p_r.add_argument("--date", type=_date_arg, default=None)
    p_u = sub.add_parser("unstamped")
    p_u.add_argument("--dir", default=".turingmind")
    p_u.add_argument("--date", type=_date_arg, default=None)
    p_s = sub.add_parser("state")
    p_s.add_argument("--state-file", required=True)
    p_s.add_argument("--date", type=_date_arg, default=None)
    p_m = sub.add_parser("migrate")
    p_m.add_argument("--legacy", required=True)
    p_m.add_argument("--current", required=True)
    return parser, parser.parse_args(argv)


def main(argv):
    try:
        parser, args = _parse(argv)
    except SystemExit:
        return 2  # usage error -> fail closed, never exit 0
    if not args.cmd:
        parser.print_usage(sys.stderr)
        return 2
    if args.cmd == "migrate":
        try:
            report = migrate(args.legacy, args.current)
        except OSError as exc:
            sys.stderr.write(
                "review_archive: migration stopped: %s; %s was left in place%s\n"
                % (exc, args.legacy,
                   " and %s was kept" % args.current
                   if os.path.lexists(args.current) else ""))
            return 1
        if report:
            sys.stdout.write(report + "\n")
        return 0
    date = args.date or datetime.date.today().strftime("%Y-%m-%d")
    if args.cmd == "review-md":
        src = os.path.join(args.dir, "REVIEW.md")
        dir_, base, suffix = args.dir, "REVIEW-%s-%s" % (
            safe_phase(args.phase), date), ".md"
    elif args.cmd == "unstamped":
        src = os.path.join(args.dir, "REVIEW.md")
        dir_, base, suffix = args.dir, "REVIEW-unstamped-%s" % date, ".md"
    else:
        src = args.state_file
        dir_ = os.path.dirname(src) or "."
        base, suffix = "%s.archived-%s" % (os.path.basename(src), date), ""
    try:
        target = archive(src, dir_, base, suffix)
    except OSError as exc:
        sys.stderr.write("review_archive: could not archive %s: %s; %s was left "
                         "in place\n" % (src, exc, src))
        return 1
    sys.stdout.write(target + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
