"""Bound a number to a closed range, and describe ranges for messages."""


def clamp(value, lo, hi):
    """Return `value` limited to the closed range [lo, hi].

    Raises ValueError when the range is empty (lo > hi).
    """
    if lo > hi:
        raise ValueError("empty range: lo must not exceed hi")
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def width(lo, hi):
    """Return the number of integers in the closed range [lo, hi]."""
    if lo > hi:
        return 0
    return hi - lo + 1


def describe_range(lo, hi):
    """Return a short human-readable label for the closed range [lo, hi]."""
    if lo == hi:
        return "exactly %s" % lo
    label = "from %s to %s" % (lo, hi)
    return label + " (%d values)" % width(lo, hi)
