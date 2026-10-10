"""Small text helpers used alongside clamp."""


def pad_left(text, size, fill=" "):
    """Return `text` right-aligned in a field of `size` characters."""
    text = str(text)
    if len(text) >= size:
        return text
    return fill * (size - len(text)) + text


def join_words(words, sep=", "):
    """Join non-empty words with `sep`, skipping blanks."""
    kept = [w.strip() for w in words if w and w.strip()]
    return sep.join(kept)


def is_blank(text):
    """Return True when `text` is None or only whitespace."""
    return text is None or not str(text).strip()
