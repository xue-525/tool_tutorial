"""Caption detection and parsing for paper figures."""
import re

CAPTION_PATTERNS = [
    re.compile(r"^\s*(Figure|Fig\.?|FIGURE)\s*([0-9]+(?:\.[0-9]+)?)\s*[:.。]\s*(.+)", re.IGNORECASE),
    re.compile(r"^\s*(Figure|Fig\.?|FIGURE)\s*([0-9]+(?:\.[0-9]+)?)\s+(.+)", re.IGNORECASE),
    re.compile(r"^\s*(图|圖)\s*([0-9]+(?:\.[0-9]+)?)\s*[:.。\s]\s*(.+)"),
]


def parse_caption(text):
    """Return (number, title) if text looks like a figure caption, else None."""
    text = text.strip().replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    for pat in CAPTION_PATTERNS:
        m = pat.match(text)
        if m:
            number = m.group(2)
            title = m.group(3).strip()
            # Trim title at first sentence boundary so filename stays short
            for sep in [". ", "。", "; "]:
                if sep in title:
                    title = title.split(sep, 1)[0]
                    break
            return number, title.strip(" .,;:")
    return None


def sanitize_filename(name, max_len=80):
    """Make a string safe to use as a filename across platforms."""
    name = re.sub(r"[\\/\:\*\?\"<>\|\n\r\t]", "", name)
    name = re.sub(r"\s+", "_", name).strip("_.")
    return name[:max_len] or "untitled"
