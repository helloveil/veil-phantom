"""
VeilPhantom — Verbal amount normalization.
Converts "twelve point five million dollars" → "$12.5M"
Converts "nine two zero one zero..." → "920101..."
"""

import re

_WORD_TO_NUM: dict[str, int] = {
    "zero": 0, "oh": 0, "one": 1, "two": 2, "three": 3, "four": 4,
    "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9,
    "ten": 10, "eleven": 11, "twelve": 12, "thirteen": 13,
    "fourteen": 14, "fifteen": 15, "sixteen": 16, "seventeen": 17,
    "eighteen": 18, "nineteen": 19, "twenty": 20, "thirty": 30,
    "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70,
    "eighty": 80, "ninety": 90, "hundred": 100,
}

_MULTIPLIERS: dict[str, str] = {
    "thousand": "K",
    "million": "M",
    "billion": "B",
}

_CURRENCY_WORDS = {"dollar", "dollars", "rand", "rands", "euro", "euros", "pound", "pounds"}
_CURRENCY_PREFIX = {
    "dollar": "$", "dollars": "$",
    "rand": "R", "rands": "R",
    "euro": "€", "euros": "€",
    "pound": "£", "pounds": "£",
}


def verbal_to_numeric(text: str) -> str:
    """Convert verbal amount like 'twelve point five million dollars' to '$12.5M'."""
    words = re.split(r"[\s-]+", text.strip().lower())

    # Strip currency words from end
    currency = "$"  # default
    while words and words[-1] in _CURRENCY_WORDS:
        currency = _CURRENCY_PREFIX.get(words[-1], "$")
        words.pop()

    # Strip currency prefix if first word is a currency
    if words and words[0] in ("$", "r"):
        currency = "R" if words[0] == "r" else "$"
        words.pop(0)

    # Find multiplier (thousand/million/billion)
    multiplier_suffix = ""
    if words and words[-1] in _MULTIPLIERS:
        multiplier_suffix = _MULTIPLIERS[words[-1]]
        words.pop()

    # Parse number words
    if not words:
        return text

    # Check for "point" (decimal)
    decimal_part = ""
    if "point" in words:
        idx = words.index("point")
        decimal_words = words[idx + 1:]
        words = words[:idx]
        decimal_digits = []
        for w in decimal_words:
            if w in _WORD_TO_NUM:
                decimal_digits.append(str(_WORD_TO_NUM[w]))
        if decimal_digits:
            decimal_part = "." + "".join(decimal_digits)

    # Parse integer part
    total = 0
    current = 0
    for w in words:
        if w == "and":
            continue
        val = _WORD_TO_NUM.get(w)
        if val is None:
            return text  # bail if we can't parse
        if val == 100:
            current = (current if current else 1) * 100
        elif val >= 20:
            current += val
        else:
            current += val

    total += current

    if total == 0 and not decimal_part:
        return text

    num_str = str(total) if total else "0"
    result = f"{currency}{num_str}{decimal_part}{multiplier_suffix}"
    return result


def verbal_digits_to_numeric(text: str) -> str:
    """Convert spoken digit sequence like 'nine two zero one zero...' to '92010...'."""
    words = re.split(r"[\s-]+", text.strip().lower())
    digits = []
    for w in words:
        val = _WORD_TO_NUM.get(w)
        if val is not None and 0 <= val <= 9:
            digits.append(str(val))
    return "".join(digits) if digits else text
