"""Numeric provenance — the deterministic core of the data-integrity guardrail.

Principle: every business figure the agent reports (budget, spend, revenue, ROAS, forecast,
worksheet split) must originate from a successful platform tool result. This module tracks
the set of numbers the platform (and the user) actually produced this session — the
*ledger* — and checks a model-generated text against it. Numbers with no provenance are
*ungrounded*: fabricated, extrapolated, or "manually calculated" by the LLM.

Two kinds of provenance (review 2026-09-03, #3/#4 and the derived-figures decision):

* **Direct.** The figure (or its 2-significant-figure rounding, so "1.2M" for 1,234,567
  survives) is in the ledger.
* **Derived.** The figure is arithmetic the platform's own numbers determine: the total of
  a numeric column or list in one tool result, the sum or difference of two figures FROM
  THE SAME tool result, or a share, change or multiplier of two such figures. Derived
  matches are held to the claim's written precision (an amount needs 6 figures) and the
  ledger can name the derivation, so an accepted figure is still traceable to platform
  data. Anything else — a number no platform figures explain — stays ungrounded.

  Operands come from one result, never from the session-wide pool (review 2026-09-05,
  H1): over a few hundred unrelated bases, ``a ± b`` explained almost any fabricated
  amount (measured ~69% at 300 bases, ~100% at 800).

Small values are exempt (counts, months, percentages up to 200%, years): the guardrail
targets business magnitudes, not "3 channels". Percentages above 200% are checked like
any figure (they are uplift claims), and can be grounded by derivation. Multipliers are
NOT exempt (review 2026-09-05, H4): ROAS and mROAS live at 1-20x, exactly where a
fabricated "4.2x" would otherwise pass unchecked.
"""

from __future__ import annotations

import re
from bisect import bisect_left, insort
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from math import isfinite, ulp
from typing import Any

# Values at or below this are treated as bookkeeping (counts, weeks, percentages ≤ 200%),
# not business figures. Years are exempted separately.
_SMALL_VALUE_EXEMPT = 200.0
#: Largest integer treated as a period count for the amount / count derivation
#: (~10 years of days). A larger integer is an amount, never a divisor.
_COUNT_MAX = 3660
_YEAR_RANGE = (1900.0, 2100.0)
_SIG_FIGS = 2  # the loosest a claim is ever matched at; also the dedupe key for reports
# A claim is checked at the precision it was written with, floored and capped: "₹4.8M" at
# 2 significant figures, "₹4,836,800.98" at 6. Checking every claim at 2 let roughly half
# of random fabricated magnitudes through a session-sized ledger (review #20), and at 3
# the pairwise derivations were vacuous over a series-heavy result (83% measured).
_PRECISION_FLOOR = 2
_PRECISION_CAP = 6
# A derivation is checked by recomputing the missing operand from the claim. An amount is
# matched against every pair of bases, so a claim written with few figures ("about ₹9M
# more") is the difference of almost any pair: exact arithmetic on platform figures is
# written in full, and that is what derives. A ratio or share is matched against single
# bases and needs less. A rounded restatement of a figure grounded elsewhere in the same
# text ("₹1,647,753.31 (≈ ₹1.65M)") is accepted as that figure.
# (percentages: any two named figures whose ratio lies between 2 and 10 make one, so a
# 3-figure percentage over 200% derived from almost anything; 4 figures are needed)
# An amount needs 6 (review 2026-09-05, H1: at 5 the pairwise pool derived 99.8% of
# random 6-figure fabrications; the gate was looser than the claims it checked).
#: How much coarser than the claim's own rounding an operand's rounding may be for the rounded-key match in
#: ``_Source.has``: an operand up to about ten times the claim's size.
_KEY_SPAN = 10.0
_DERIVED_MIN_PRECISION = {"amount": 6, "percent": 6, "multiplier": 3}
_LEDGER_CAP = 5000  # per-session ledger size guard
#: Freed in one eviction. The rebuild it costs is O(what the session still holds), so evicting one result at a time
#: rebuilt on nearly every read; a slab makes the eviction rare and the recording cost flat (2026-09-20).
_EVICTION_SLAB = 2000
_PRECISIONS = range(_PRECISION_FLOOR, _PRECISION_CAP + 1)
# Named figures kept for pairwise derivation, across the whole session. Small on purpose
# (review 2026-09-05, H1): the pool is what a fabrication has to collide with, and every
# extra base is another chance. Series points never enter it; totals and means go first.
_BASE_CAP = 300
#: Group totals kept per session. They are cheap (tens per result) but must never crowd the ledger itself.
_GROUP_CAP = 2000

_SUFFIX = {
    "k": 1e3, "thousand": 1e3,
    "m": 1e6, "mn": 1e6, "mm": 1e6, "million": 1e6,
    "b": 1e9, "bn": 1e9, "billion": 1e9,
    "lakh": 1e5, "lakhs": 1e5, "lac": 1e5, "lacs": 1e5,
    "crore": 1e7, "crores": 1e7, "cr": 1e7,
}

#: The units a drawn compact figure is written in (``harness_core.figures.UNITS``).
_COMPACT_SUFFIXES = frozenset({"k", "m", "b"})

# ISO dates are matched first so their parts don't leak in as standalone numbers.
_DATE_RE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
# Groupings the model is told to use follow the workspace currency: 3,38,451.71 (Indian),
# 1,234,567.89 (Western), 250.000,00 (European), 250 000 (spaces), plus 1.5e6.
_NUM_RE = re.compile(
    r"(?P<currency>[$€£₹]\s?)?"
    # A figure starts and ends at a word boundary: digits inside an id such as
    # ``…579ddc3e7500`` are not numbers (``3e7500`` read as scientific notation is inf).
    r"(?<![A-Za-z0-9_])"
    r"(?P<num>"
    r"\d{1,2}(?:,\d{2})+,\d{3}(?:\.\d+)?"  # Indian grouping
    r"|\d{1,3}(?:,\d{3})+(?:\.\d+)?"  # Western grouping
    r"|\d{1,3}(?:\.\d{3})+,\d+"  # European grouping with comma decimals
    r"|\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?:[.,]\d+)?"  # space-grouped
    r"|\d+(?:\.\d+)?[eE][+-]?\d+"  # scientific notation
    r"|\d+\.\d+|\d+)"
    r"\s*(?P<suffix>lakhs?\b|lacs?\b|crores?\b|cr\b|thousand\b|million\b|billion\b"
    r"|mm\b|mn\b|bn\b|[kKmMbB]\b)?"
    r"\s*(?P<pct>%)?(?P<mult>x\b)?"
    r"(?![A-Za-z0-9_])",
    re.IGNORECASE,
)
_GROUP_SEP_RE = re.compile(r"[ \u00a0\u202f]")
# Identifiers: one unbroken run of 12+ letters/digits/hyphens/underscores holding both a
# letter and a digit (UUIDs, thread ids, hashes). Their digit segments (``-013b-``,
# ``-8316-``) are not claims; a range such as ``500-600`` has no letter and stays one.
_ID_RE = re.compile(
    r"(?<![A-Za-z0-9_])(?=[A-Za-z0-9_-]*[A-Za-z])(?=[A-Za-z0-9_-]*\d)[A-Za-z0-9_-]{12,}"
    r"(?![A-Za-z0-9_])"
)


def _without_identifiers(text: str) -> str:
    return _ID_RE.sub(" ", _DATE_RE.sub(" ", text or ""))


@dataclass(frozen=True)
class Figure:
    """One number claimed in a text: its value, what kind of claim it is, and the raw
    token it was written as."""

    value: float
    kind: str  # "amount" | "percent" | "multiplier"
    raw: str
    precision: int = _PRECISION_FLOOR  # figures as written, trailing zeros included
    loose: int = _PRECISION_FLOOR  # figures without trailing zeros: a rounding's precision
    #: Where the figure sits in the text it was read from, so a claim can be read together with the words around it
    #: (the named-ratio rule below). -1 when the figure did not come from a text scan.
    start: int = -1


def _round_sig(value: float, sig: int = _SIG_FIGS) -> float:
    """Round to ``sig`` significant figures (0 stays 0; non-finite maps to 0 — inf/nan
    are never business figures and must not crash the guardrail's before_model hook)."""
    from math import floor, isfinite, log10

    if value == 0 or not isfinite(value):
        return 0.0
    return round(value, -floor(log10(abs(value))) + (sig - 1))


def _parse_num(raw: str) -> float | None:
    """The numeric value of one ``_NUM_RE`` ``num`` group, whatever its grouping."""
    token = raw.strip()
    try:
        if re.fullmatch(r"\d{1,3}(?:\.\d{3})+,\d+", token):  # European
            return float(token.replace(".", "").replace(",", "."))
        if _GROUP_SEP_RE.search(token):  # space-grouped, "," or "." decimals
            token = _GROUP_SEP_RE.sub("", token).replace(",", ".")
            return float(token)
        return float(token.replace(",", ""))  # Indian / Western / plain / scientific
    except ValueError:  # pragma: no cover - the regex guarantees a parseable token
        return None


def _figure_of(m: re.Match[str]) -> Figure | None:
    value = _parse_num(m.group("num"))
    if value is None:
        return None
    suffix = (m.group("suffix") or "").lower()
    value *= _SUFFIX.get(suffix, 1.0)
    if m.group("pct"):
        kind = "percent"
    elif m.group("mult") and not suffix:
        kind = "multiplier"
    else:
        kind = "amount"
    precision = _written_precision(m.group("num"))
    # A compact figure written with decimals ("$108.00K", "$1.00M") is drawn with exactly two decimals of its unit
    # (docs/specs/figure-style.md), so its trailing zeros are figures: it restates only a value that rounds to it at
    # the precision it is written with. Prose without decimals ("$108K", "$1M") still restates loosely.
    compact = suffix in _COMPACT_SUFFIXES and "." in m.group("num")
    return Figure(value=value, kind=kind, raw=m.group(0).strip(),
                  precision=precision, loose=precision if compact else precision_of(value),
                  start=m.start())


def _written_precision(token: str) -> int:
    """Significant figures as written: the digits of the mantissa without leading zeros,
    trailing zeros included ("200,000" is exact, "0.2M" is not), floored and capped."""
    digits = re.sub(r"\D", "", re.split(r"[eE]", token)[0]).lstrip("0")
    return max(_PRECISION_FLOOR, min(_PRECISION_CAP, len(digits)))


def _half_unit(value: float, p: int) -> float:
    """Half a unit of the last of ``p`` significant figures of ``value``: the rounding
    error a claim written at that precision may carry."""
    from math import floor, log10
    if value == 0 or not isfinite(value):
        return 0.0
    return 0.5 * 10 ** (floor(log10(abs(value))) - p + 1)


def precision_of(value: float) -> int:
    """Significant figures a value carries, floored and capped: trailing zeros do not
    count (4,836,800 → 5; 4.8M → 2), decimals do (920,067.24 → 8 → cap 6)."""
    if not isfinite(value) or value == 0:
        return _PRECISION_FLOOR
    digits = re.sub(r"\D", "", f"{abs(value):.10g}".split("e")[0]).strip("0")
    return max(_PRECISION_FLOOR, min(_PRECISION_CAP, len(digits)))


def extract_figures(text: str) -> list[Figure]:
    """Every number claimed in ``text`` with its kind; ISO dates are skipped."""
    out: list[Figure] = []
    for m in _NUM_RE.finditer(_without_identifiers(text)):
        fig = _figure_of(m)
        if fig is not None and isfinite(fig.value):  # 1e999 is a typo, not a claim
            out.append(fig)
    return out


# -- the member's numbers (owner decision 2026-09-30, option A; read by a model since 2026-10-01) ----------- #
# A tool argument is grounded when the member's own operation on a platform figure gives it. The numbers the member
# said reach the ledger typed (percent, multiplier, amount) with the direction their words give them (+, -, =, or
# none), read from the member's message by a small model (`mia.guardrails.member_numbers`), never by a word list:
# a phrasing a regex never saw was a refusal, and English only (owner, 2026-10-01). This module keeps the digit
# grammar alone (`_NUM_RE`): the ground check that a number the reader returns was written in the member's words,
# and the fallback when the reader is unavailable (digits as written, no direction).
MEMBER_KINDS = ("percent", "multiplier", "amount")
MEMBER_DIRECTIONS = ("+", "-", "=", "")
#: The operations a member states between a platform figure ``b`` and their number ``u``, BY WHAT THE NUMBER IS and
#: the direction of its words: a percentage moves the base by or to a share of it, a multiple scales it, an amount
#: adds to or takes from it. The label, the operation, and the operation solved for the base: the inverse finds the
#: candidate bases with one sorted search (never a product over every base); the forward form then reproduces the
#: argument at six figures, which is the check (solving for the base amplifies the argument's own rounding). ``None``
#: when the pair has no base. A ratio of the two (u / b) is a multiplier, exempt under 200 like every multiplier
#: argument, so no operation produces one (review 2026-10-01). This table is the whole algebra of a single-step
#: change, not a list of cases: anything outside it is refused, as before.
_MEMBER_OPERATIONS: dict[str, tuple[tuple[str, str, Any, Any], ...]] = {
    "percent": (
        ("+", "{b} × (1 + {u}%)", lambda b, u: b * (1 + u / 100), lambda v, u: v / (1 + u / 100) if u > -100 else None),
        ("-", "{b} × (1 - {u}%)", lambda b, u: b * (1 - u / 100), lambda v, u: v / (1 - u / 100) if u < 100 else None),
        ("=", "{b} × {u}%", lambda b, u: b * u / 100, lambda v, u: v * 100 / u if u else None),
    ),
    "multiplier": (
        ("+", "{b} × {u}", lambda b, u: b * u, lambda v, u: v / u if u else None),
        ("-", "{b} / {u}", lambda b, u: b / u, lambda v, u: v * u if u else None),
    ),
    "amount": (
        ("+", "{b} + {u}", lambda b, u: b + u, lambda v, u: v - u),
        ("-", "{b} - {u}", lambda b, u: b - u, lambda v, u: v + u),
    ),
}
#: Which operations a direction allows: "cut by 20%" never admits the increase (review 2026-10-01); a share ("at 80%
#: of") is the share; a multiple keeps both ways (a "half" is a cut said as a multiple); no direction keeps all.
_DIRECTION_ALLOWS = {"+": {"+", "="}, "-": {"-"}, "=": {"="}, "": {"+", "-", "="}}
#: How far from the solved base a candidate is looked for, relative: the argument's rounding, amplified by the
#: operation. The forward check decides; this only bounds the search.
_BASE_SEARCH = 1e-3
#: The member's numbers a ledger keeps: the newest, a re-said number moving to the front. One ask is one or two
#: numbers; admission grows with every number kept (measured 2026-10-01: 40 kept admitted 10% of fabrications).
_MEMBER_NUMBERS_CAP = 8


def member_numbers(text: str) -> list[tuple[float, str, str]]:
    """The numbers written as DIGITS in the member's words, typed by their own suffix ("20%" a percent, "2x" a
    multiplier, "$1.2M" and "1.5 lakh" amounts), with no direction: the fallback when the reader is unavailable.
    A bare small integer or a year ("3 channels", "Q3 2026") is a count or a date, never a change; ISO dates and
    identifiers are not numbers."""
    return [(fig.value, fig.kind, "") for fig in extract_figures(_without_identifiers(text))
            if isfinite(fig.value) and (fig.kind != "amount" or not _is_exempt(fig.value))]


def _g(value: float) -> str:
    return f"{value:.10g}"


#: How far after a multiplier its explanation may sit ("7.66x (computed as A / B)"). One clause, not one paragraph:
#: far enough for the parenthetical the models actually write, short enough that the next sentence's figures are not
#: read as this claim's operands.
_RATIO_WINDOW = 120
#: The shapes an answer writes a ratio in. Both operands are captured; the divider carries the claim.
_RATIO_DIVIDER_RE = re.compile(r"\s*(?:/|÷|\bdivided by\b|\bover\b)\s*", re.IGNORECASE)


def _is_pairwise(why: str) -> bool:
    """True when a provenance string is a pairwise DERIVATION (``a / b``) rather than a figure the result carries.

    ``explain`` answers "ledger", "exempt" or a named total for a figure that is in a result; only the pairwise
    derivations read as an arithmetic expression, and only those are the named-ratio rule's business.
    """
    return " / " in why and not why.startswith(("sum(", "mean(", "restates "))


def _named_ratio_operands(masked: str, fig: Figure) -> tuple[float, float] | None:
    """The two figures ``masked`` presents as the operands of the multiplier at ``fig``, or ``None`` when it does not
    explain itself. Read from the identifier-masked text, so the offsets match ``extract_figures``."""
    window = masked[fig.start + len(fig.raw): fig.start + len(fig.raw) + _RATIO_WINDOW]
    stop = min((i for i in (window.find(". "), window.find("\n")) if i >= 0), default=-1)
    if stop >= 0:
        window = window[:stop]
    figures = [f for f in extract_figures(window) if f.kind == "amount"]
    if len(figures) < 2:
        return None
    first, second = figures[0], figures[1]
    between = window[first.start + len(first.raw): second.start]
    if not _RATIO_DIVIDER_RE.fullmatch(between):
        return None
    return first.value, second.value


def extract_numbers(text: str) -> list[float]:
    """All amounts and multipliers claimed in ``text``, suffix-expanded ($1.2M → 1200000.0).

    Percentages and ISO dates are dropped here (the ledger checks percentages above 200%
    separately through ``extract_figures``).
    """
    return [f.value for f in extract_figures(text) if f.kind != "percent"]


def redact_figures(text: str, placeholder: str = "[a figure]") -> str:
    """Replace business-magnitude numbers in ``text`` with ``placeholder``, leaving
    percentages, years, and small bookkeeping values intact. Used to neutralise
    harness-authored text (e.g. verifier issue bullets) before it re-enters a session,
    so a figure the harness merely *names* cannot acquire provenance in the ledger."""

    protected = [(m.start(), m.end()) for m in _ID_RE.finditer(text or "")]

    def _sub(m: re.Match[str]) -> str:
        if any(a <= m.start() < b for a, b in protected):
            return m.group(0)
        fig = _figure_of(m)
        # Multipliers are never exempt (H4): a "4.2x" in harness-authored or reasoning
        # text is as much a claim as an amount.
        if fig is None or fig.kind == "percent" or (fig.kind == "amount" and _is_exempt(fig.value)):
            return m.group(0)
        whole = m.group(0)
        return placeholder + whole[len(whole.rstrip()):]  # keep the trailing whitespace

    return _NUM_RE.sub(_sub, text or "")


def redact_values(text: str, values: Iterable[float], placeholder: str = "[unverified]") -> str:
    """Replace only the figures in ``text`` whose value matches one of ``values``, leaving
    every other figure and all prose intact. Used to hand back a report with just its
    unverifiable figures hidden, rather than withholding the whole thing (review
    2026-09-04): no ungrounded number reaches the user, but the grounded ones still do.

    A figure is matched at ITS OWN written precision: a grounded ₹1,234,567 next to an
    invented ₹1,250,000 stays (they differ at 6 figures), while "₹1.25M" restating the
    invented one goes (they agree at 3). Matching everything at 2 figures hid any grounded
    figure within ~1.5% of an ungrounded one (review 2026-09-05)."""
    targets = [float(v) for v in values]
    if not targets:
        return text or ""
    protected = [(m.start(), m.end()) for m in _ID_RE.finditer(text or "")]

    def _sub(m: re.Match[str]) -> str:
        if any(a <= m.start() < b for a, b in protected):
            return m.group(0)
        fig = _figure_of(m)
        if fig is None or not any(_close(fig.value, t, fig.loose) for t in targets):
            return m.group(0)
        whole = m.group(0)
        return placeholder + whole[len(whole.rstrip()):]  # keep the trailing whitespace

    return _NUM_RE.sub(_sub, text or "")


def collect_numbers(data: Any, _depth: int = 0) -> Iterable[float]:
    """Recursively yield every numeric value in a tool result (dict/list/scalars).

    Numeric *strings* count too — platform ids and CSV-ish fields arrive as strings, and the
    LLM may echo them as numbers.
    """
    for _, value, _ in _numbers_with_depth(data, _depth):
        yield value


def _numbers_with_depth(data: Any, _depth: int = 0,
                        _point: bool = False) -> Iterator[tuple[int, float, bool]]:
    """``collect_numbers`` with, per value, its nesting depth and whether it is a point of a
    numeric array (a time series) rather than a named field. Named fields are the figures
    an answer derives from; series points are data and only ground themselves."""
    if _depth > 12:
        return
    if isinstance(data, bool):
        return
    if isinstance(data, (int, float)):
        yield _depth, float(data), _point
    elif isinstance(data, str):
        for value in extract_numbers(data):
            yield _depth, value, _point
    elif isinstance(data, dict):
        for v in data.values():
            yield from _numbers_with_depth(v, _depth + 1, False)
    elif isinstance(data, (list, tuple)):
        for v in data:
            yield from _numbers_with_depth(v, _depth + 1, True)


#: The keys a result names an amount's currency by: a row's own (``currency``) or a block's (``currency_code``).
_CURRENCY_KEYS = ("currency", "currency_code")


#: The currency of a row that names none while rows beside it do: unknown, so it combines with no named one.
UNKNOWN_CURRENCY = "?"


#: Currency values that name none: an amount so labelled is in an unknown currency.
_NO_CURRENCY = frozenset({"UNKNOWN", "N/A", "NA", "NONE", "NULL", "-"})


def _currency(row: dict, inherited: str | None = None) -> str | None:
    """The currency a dict's amounts are in: its own key, else the one it sits under; None when nothing names one,
    ``UNKNOWN_CURRENCY`` when the key says it is not known."""
    for key in _CURRENCY_KEYS:
        value = row.get(key)
        if isinstance(value, str) and value.strip():
            code = value.strip().upper()
            return UNKNOWN_CURRENCY if code in _NO_CURRENCY else code
    return inherited


_IDENTIFIER_RE = re.compile(r"\s*\d{9,}\s*")


def _one_currency(rows: list[dict], inherited: str | None = None) -> tuple[bool, str | None]:
    """Whether ``rows`` are in one currency, and which: every row names the same one, or none names any. Rows some of
    which name a currency and some none, or two currencies, are not: a total of them adds amounts that do not add."""
    named = {_currency(r, inherited) for r in rows}
    if len(named) == 1 and UNKNOWN_CURRENCY not in named:
        return True, named.pop()
    return False, None


def _numbers_with_currency(data: Any, _depth: int = 0, _point: bool = False, _tag: str | None = None
                           ) -> Iterator[tuple[int, float, bool, str | None]]:
    """``_numbers_with_depth`` with, per value, the currency the dict it sits in names (or the one above it): two
    figures in different currencies are never combined."""
    if _depth > 12 or isinstance(data, bool):
        return
    if isinstance(data, (int, float)):
        yield _depth, float(data), _point, _tag
    elif isinstance(data, str):
        # a string of nine or more digits and nothing else is an identifier (an ad id, an account id): it grounds an
        # echo of itself, never a derivation; at an amount's size (an IDR or KRW figure) it would derive one
        ident = bool(_IDENTIFIER_RE.fullmatch(data))
        for value in extract_numbers(data):
            yield _depth, value, _point or ident, _tag
    elif isinstance(data, dict):
        tag = _currency(data, _tag)
        for v in data.values():
            yield from _numbers_with_currency(v, _depth + 1, False, tag)
    elif isinstance(data, (list, tuple)):
        # a row naming no currency among rows that name theirs is in an unknown one
        named = any(isinstance(v, dict) and _currency(v) for v in data)
        for v in data:
            tag = UNKNOWN_CURRENCY if named and isinstance(v, dict) and not _currency(v, _tag) else _tag
            yield from _numbers_with_currency(v, _depth + 1, True, tag)


def _named_numbers_with_currency(data: Any, _depth: int = 0, _tag: str | None = None
                                 ) -> Iterator[tuple[str, float, str | None]]:
    """``_named_numbers`` with, per field, the currency its dict names (or the one above it)."""
    if _depth > 8 or isinstance(data, bool):
        return
    if isinstance(data, dict):
        tag = _currency(data, _tag)
        for k, v in data.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)) and isfinite(float(v)):
                yield str(k), float(v), tag
            else:
                yield from _named_numbers_with_currency(v, _depth + 1, tag)
    elif isinstance(data, (list, tuple)):
        named = any(isinstance(v, dict) and _currency(v) for v in data)
        for v in data:
            if isinstance(v, (dict, list, tuple)):
                tag = UNKNOWN_CURRENCY if named and isinstance(v, dict) and not _currency(v, _tag) else _tag
                yield from _named_numbers_with_currency(v, _depth + 1, tag)


def _named_numbers(data: Any, _depth: int = 0) -> Iterator[tuple[str, float]]:
    """``(leaf key, value)`` for every named numeric field of a result, dicts inside lists
    included (a channel row's ``i_revenue``), series points excluded (they have no name)."""
    if _depth > 8 or isinstance(data, bool):
        return
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(v, bool):
                continue
            if isinstance(v, (int, float)) and isfinite(float(v)):
                yield str(k), float(v)
            else:
                yield from _named_numbers(v, _depth + 1)
    elif isinstance(data, (list, tuple)):
        for v in data:
            if isinstance(v, (dict, list, tuple)):
                yield from _named_numbers(v, _depth + 1)


def mark_values(text: str, values: Iterable[float], marker: str = "*") -> str:
    """Append ``marker`` to every figure in ``text`` whose value matches one of ``values``
    at its own written precision (the DERIVED class, E13); everything else is untouched."""
    targets = [float(v) for v in values]
    if not targets:
        return text or ""
    protected = [(m.start(), m.end()) for m in _ID_RE.finditer(text or "")]

    def _sub(m: re.Match[str]) -> str:
        if any(a <= m.start() < b for a, b in protected):
            return m.group(0)
        fig = _figure_of(m)
        if fig is None or not any(_close(fig.value, t, fig.loose) for t in targets):
            return m.group(0)
        whole = m.group(0)
        body = whole.rstrip()
        return body + marker + whole[len(body):]

    return _NUM_RE.sub(_sub, text or "")


def _sum_and_mean(label: str, numbers: list[float]) -> Iterator[tuple[str, float]]:
    """A column of two or more finite values determines its total and its mean. A column
    holding inf/nan (a platform sentinel) determines nothing: inf would ground any figure
    that parses to inf and nan grounds nothing anyway."""
    if len(numbers) >= 2 and all(isfinite(v) for v in numbers):
        yield f"sum({label})", sum(numbers)
        yield f"mean({label})", sum(numbers) / len(numbers)


#: A group is a value of a categorical field the rows themselves carry (``channel``, ``week_start``). Bounded so a
#: wide result cannot turn into a large pool of totals: a field with more values than this is an id, not a grouping,
#: and one value covering every row is the column total, already yielded.
_GROUP_KEY_MAX_VALUES = 24
#: Rows scanned for groups in one array. Past this the arrays are series, where a group is a point, not a total.
_GROUP_ROWS_MAX = 2000


#: What makes two group totals comparable: one array, one grouping field, one numeric column, one currency. Two totals
#: of the same family differ only in WHICH group they sum, which is what "compare X with Y" asks for; totals of two
#: families are not like for like and never combine (PRD turn-aee40cdf, owner 2026-09-20), nor do two currencies'.
GroupFamily = tuple[str, str, str, str | None]


def _group_totals(rows: list[dict], numeric_keys: set[str], path: str, inherited: str | None = None
                  ) -> Iterator[tuple[str, float, GroupFamily]]:
    """The sum of one numeric field over the rows sharing one value of a categorical field, for every such field and
    value (owner, 2026-09-18). A table keyed by week and channel says what each channel and each week add up to, and
    an answer that reports either is reporting the platform's own arithmetic, not its own.

    Deliberately narrow: groups come from the data's own keys (never an arbitrary subset), a group of one row adds
    nothing the row did not already ground, means are not yielded (a group mean is not a figure results carry), and
    the totals ground themselves only - `NumberLedger.add_from` keeps them out of the pairwise base pool.
    """
    if len(rows) > _GROUP_ROWS_MAX:
        return
    group_keys = {k for row in rows for k, v in row.items() if isinstance(v, str) and v}
    for group_key in sorted(group_keys):
        values = {row[group_key] for row in rows if isinstance(row.get(group_key), str)}
        if len(values) > _GROUP_KEY_MAX_VALUES or len(values) < 2:
            continue  # an id per row, or one value covering the whole column (already a total)
        for value in sorted(values):
            members = [row for row in rows if row.get(group_key) == value]
            if len(members) < 2:
                continue
            single, currency = _one_currency(members, inherited)
            if not single:
                continue  # its rows' amounts are in more than one currency: they add to no figure
            for key in sorted(numeric_keys):
                column = [float(m[key]) for m in members
                          if isinstance(m.get(key), (int, float)) and not isinstance(m.get(key), bool)]
                if len(column) < 2:
                    continue
                yield (f"sum({path}[{group_key}={value}].{key})", sum(column), (path, group_key, key, currency))


def grouped_totals(data: Any, _path: str = "", _depth: int = 0) -> Iterator[tuple[str, float]]:
    """Every group total in a result: the sum of one numeric field over the rows that share one value of a
    categorical field of the same rows. See :func:`grouped_totals_with_family` for the same walk with the family
    each total belongs to."""
    for label, total, _family in grouped_totals_with_family(data, _path, _depth):
        yield label, total


def grouped_totals_with_family(data: Any, _path: str = "", _depth: int = 0, _tag: str | None = None
                               ) -> Iterator[tuple[str, float, GroupFamily]]:
    """Every group total in a result, walked like {@link derived_totals}, each with its :data:`GroupFamily`."""
    if _depth > 12 or isinstance(data, (bool, str, int, float)) or data is None:
        return
    if isinstance(data, dict):
        tag = _currency(data, _tag)
        for key, value in data.items():
            yield from grouped_totals_with_family(value, f"{_path}.{key}" if _path else str(key), _depth + 1, tag)
        return
    if isinstance(data, (list, tuple)):
        rows = [d for d in data if isinstance(d, dict)]
        if len(rows) >= 2:
            numeric = {k for d in rows for k, v in d.items()
                       if isinstance(v, (int, float)) and not isinstance(v, bool)}
            yield from _group_totals(rows, numeric, _path or "list", _tag)
        for i, item in enumerate(data):
            if isinstance(item, (dict, list, tuple)):
                yield from grouped_totals_with_family(item, f"{_path}[{i}]", _depth + 1, _tag)


def derived_totals(data: Any, _path: str = "", _depth: int = 0) -> Iterator[tuple[str, float]]:
    """Totals and means the platform's own structure determines: the sum and the mean of
    every numeric list and of every numeric column across a list of dicts
    (``channels[].spend``). Labelled by path so an accepted figure can be explained. A column
    over rows in more than one currency determines nothing (``_one_currency``)."""
    for label, total, _currency_of in _derived_totals(data, _path, _depth):
        yield label, total


def _derived_totals(data: Any, _path: str = "", _depth: int = 0, _tag: str | None = None
                    ) -> Iterator[tuple[str, float, str | None]]:
    """``derived_totals`` with the currency each total is in."""
    if _depth > 12 or isinstance(data, (bool, str, int, float)) or data is None:
        return
    if isinstance(data, dict):
        tag = _currency(data, _tag)
        for key, value in data.items():
            yield from _derived_totals(value, f"{_path}.{key}" if _path else str(key), _depth + 1, tag)
        return
    if isinstance(data, (list, tuple)):
        numbers = [float(v) for v in data if isinstance(v, (int, float)) and not isinstance(v, bool)]
        for label, total in _sum_and_mean(f"{_path or 'list'}[]", numbers):
            yield label, total, _tag
        dicts = [d for d in data if isinstance(d, dict)]
        single, currency = _one_currency(dicts, _tag)
        if len(dicts) >= 2 and single:
            keys = {k for d in dicts for k, v in d.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool)}
            for key in sorted(keys):
                column = [float(d[key]) for d in dicts
                          if isinstance(d.get(key), (int, float)) and not isinstance(d.get(key), bool)]
                for label, total in _sum_and_mean(f"{_path or 'list'}[].{key}", column):
                    yield label, total, currency
        for i, item in enumerate(data):
            if isinstance(item, (dict, list, tuple)):
                yield from _derived_totals(item, f"{_path}[{i}]", _depth + 1, _tag)


def _is_exempt(value: float) -> bool:
    if abs(value) <= _SMALL_VALUE_EXEMPT:
        return True
    return _YEAR_RANGE[0] <= value <= _YEAR_RANGE[1] and float(value).is_integer()


def _close(candidate: float, target: float, sig: int) -> bool:
    return _round_sig(candidate, sig) == _round_sig(target, sig)


class _Source:
    """The named figures ONE tool result (or user message) carries: the only pool a
    pairwise derivation may draw its operands from (review 2026-09-05, H1). Two figures
    the platform returned together are what an answer legitimately combines; two from
    different calls agreeing with a claim is coincidence, and over a session-wide pool
    that coincidence was near-certain."""

    __slots__ = ("bases", "sorted_bases", "bases_at", "base_currencies", "counts", "named", "named_currency", "kind",
                 "group_families", "values", "operands")

    def __init__(self, kind: str = "") -> None:
        #: Group totals of this result by family (array, grouping field, column): the totals a COMPARISON may draw
        #: its two operands from. Only families with two or more totals are kept - one total compares with nothing.
        self.group_families: dict[GroupFamily, list[tuple[str, float]]] = {}
        #: What this source is ("result:<tool>", "user-text", ...); cross-result
        #: derivation (E13, DR-15) draws operands from tool-result sources only.
        self.kind = kind
        #: Named numeric fields of a result (leaf key -> value, first seen), the operands a
        #: DERIVED figure may combine across results by the same name.
        self.named: dict[str, float] = {}
        #: The currency each named field was first seen in (None: named none).
        self.named_currency: dict[str, str | None] = {}
        #: Every number this result contributed to the ledger, in order. Kept so the oldest result's values can be
        #: handed back when the session's bound is reached (2026-09-20) - without it the NEWEST result was dropped.
        self.values: list[float] = []
        self.bases: list[float] = []  # distinct business magnitudes, insertion order
        #: Every figure eligible as a base (a business magnitude, never a series point), before the session-wide
        #: pairwise cap: what the member's own operation may start from (option A, 2026-09-30). Cleared with
        #: ``values`` on eviction.
        self.operands: list[float] = []
        self.sorted_bases: list[float] = []  # the same, sorted, for tolerance lookups
        #: Per precision, each base's rounded key -> the currencies it was seen in (None: named none).
        self.bases_at: dict[int, dict[float, set[str | None]]] = {p: {} for p in _PRECISIONS}
        #: Each base -> the currencies it was seen in: an amount combines only with one in its own currency, or with
        #: one that names none.
        self.base_currencies: dict[float, set[str | None]] = {}
        # Integer counts seen in the data (days, weeks, months, channel counts): the
        # divisors a per-period average is a platform figure divided by (review
        # 2026-09-04). Bounded to a plausible period range so a spend that happens to be
        # a round integer is not treated as a count.
        self.counts: set[int] = set()

    def has(self, x: float, p: int, tol: float, currencies: set[str | None] | None = None) -> bool:
        """A base equals ``x`` at ``p`` figures, or lies within ``tol`` of it: the operand
        recomputed from a rounded claim carries half a unit of the claim's last digit. With
        ``currencies`` (the other operand's), only a base in one of them, or either naming
        none, counts: amounts in two currencies combine to no figure."""
        if not isfinite(x) or x == 0:
            return False
        x = abs(x)
        if ulp(x) > tol:
            return False  # a float this large cannot hold the claim's last digit: a - v is a again, for any v
        # the rounded key compares the operand at the CLAIM's precision, which is only an operand's precision while the
        # operand is near the claim's size: rounded at seven figures, two platform ids (1.2e17) are one key, and their
        # difference "derived" any amount below the rounding unit. A far larger operand matches within the claim's own
        # half unit below, or not at all.
        seen = self.bases_at[p].get(_round_sig(x, p)) if _half_unit(x, p) <= tol * _KEY_SPAN else None
        if seen is not None and _combines(seen, currencies):
            return True
        i = bisect_left(self.sorted_bases, x - tol)
        while i < len(self.sorted_bases) and self.sorted_bases[i] <= x + tol:
            if _combines(self.base_currencies.get(self.sorted_bases[i], {None}), currencies):
                return True
            i += 1
        return False


def _named_currencies(seen: set[str | None]) -> set[str | None]:
    """The currencies a figure was seen in, an untagged sighting dropped when a tagged one exists: an echo of an
    amount in a list that names no currency is that amount, in its own currency."""
    named = seen - {None}
    return named if named else seen


def _combines(seen: set[str | None], other: set[str | None] | None) -> bool:
    """Two operands may combine: no constraint, either names no currency, or they share one. An unknown currency
    (``UNKNOWN_CURRENCY``) is shared with nothing, so it combines only with an operand naming none."""
    if other is None:
        return True
    seen, other = _named_currencies(seen), _named_currencies(other)
    if None in seen or None in other:
        return True
    return bool((seen & other) - {UNKNOWN_CURRENCY})


class NumberLedger:
    """Session-scoped set of grounded numbers, plus the platform-determined totals and,
    per source, the base figures pairwise derivation may combine. A claim is matched at
    the precision it was written with (``precision_of``), so "₹4.8M" matches loosely and
    "₹4,836,800.98" exactly to 6 figures.

    Serialises to a plain ``list[float]`` so it can live in ADK session state and survive
    across turns/process restarts (derivation data is rebuilt from the same sources).
    """

    _PRECISIONS = _PRECISIONS

    def __init__(self, values: Iterable[float] = ()) -> None:
        self._exact: set[float] = set()
        self._values_at: dict[int, set[float]] = {p: set() for p in self._PRECISIONS}
        self._totals: list[tuple[str, float]] = []  # (label, total) from tool results
        self._sources: list[_Source] = []  # one per add_from call
        self._n_bases = 0  # across every source, capped at _BASE_CAP
        self._held = 0  # values the surviving sources hold, tracked for the eviction slab
        #: Group totals by their 6-figure key -> the derivation that names the group (2026-09-18).
        self._groups: dict[float, str] = {}
        #: The numbers the member said, in order of saying (``add_member_text``): the operands a tool argument may
        #: combine with a platform figure (option A, 2026-09-30).
        self._member: list[tuple[float, str]] = []
        #: Every platform operand the session still holds, sorted, for the input class's base search; rebuilt when
        #: an operand is added or evicted. The pairwise base pool (300, the newest results') is too narrow for a base
        #: read several calls ago; every figure is too wide (a curve's points admitted 2% of fabrications over a
        #: session, measured 2026-10-01).
        self._platform_sorted: list[float] | None = None
        self._source = self._open_source()
        for v in values:
            self._add_value(float(v))

    def _open_source(self, kind: str = "") -> _Source:
        self._source = _Source(kind)
        self._sources.append(self._source)
        return self._source

    @property
    def _values(self) -> set[float]:  # 2-sig-fig view, kept for reports and tests
        return self._values_at[_SIG_FIGS]

    def add_from(self, data: Any, kind: str = "") -> None:
        """Record every number found in a tool result / user message, and the totals its
        structure determines. Each call is one SOURCE: its figures may be combined with
        each other by pairwise derivation, never with another call's. ``kind`` names the
        source; a ``result:<tool>`` source also keeps its named fields for the cross-result
        DERIVED class (E13)."""
        self._open_source(kind)
        if kind.startswith("result:"):
            for name, v, currency in _named_numbers_with_currency(data):
                if name not in self._source.named:
                    self._source.named[name] = v
                    self._source.named_currency[name] = currency
        # Bases are capped, so the figures most worth deriving from go in first: the
        # totals and means a result determines, then its named fields, shallow first.
        # Points of a numeric array (a time series) ground themselves only.
        for label, total, currency in _derived_totals(data):
            self._totals.append((label, total))
            self._add_value(total)
            self._add_base(total, currency)
        for _, v, point, currency in sorted(_numbers_with_currency(data), key=lambda item: item[0]):
            if len(self._exact) >= _LEDGER_CAP and not self._evict_oldest_values():
                break  # everything in the ledger is already this result's own
            self._add_value(v)
            if not point:
                self._add_base(v, currency)
        # A group's total (one channel's rows, one week's rows) is recorded LAST and apart (review 2026-09-18): the
        # result's own cells take the ledger's room first, group totals never join the pairwise base pool, and they
        # ground a claim only when it is written in full - they sit in the aggregate band, where a rounded
        # fabrication ("about $2.9M") would otherwise collide with one.
        family_of_source: dict[GroupFamily, list[tuple[str, float]]] = {}
        for label, total, family in grouped_totals_with_family(data):
            if len(self._groups) >= _GROUP_CAP:
                break
            if not isfinite(total) or _is_exempt(total):
                continue
            self._groups.setdefault(_round_sig(total, _PRECISION_CAP), label)
            family_of_source.setdefault(family, []).append((label, total))
        # Two totals of one family are the same column summed over two of the data's own groups, so their difference
        # (and their combined total) is the platform's arithmetic exactly as each total is. Kept per SOURCE, because
        # pairwise provenance never crosses tool results (H1), and per family, because totals of two different
        # columns or two different groupings are not like for like.
        self._source.group_families = {f: t for f, t in family_of_source.items() if len(t) >= 2}

    def _add_value(self, v: float) -> None:
        if not isfinite(v):
            return
        self._source.values.append(v)
        self._held += 1
        self._record_value(v)

    def _record_value(self, v: float) -> None:
        """Put ``v`` into the ledger's sets. Split from :meth:`_add_value` so a rebuild after an eviction can replay
        the surviving results without recording them as contributed a second time."""
        self._exact.add(v)
        av = abs(v)
        if 2 <= av <= _COUNT_MAX and av == int(av):
            self._source.counts.add(int(av))
        for p, keys in self._values_at.items():
            keys.add(_round_sig(v, p))
            # Grounding a figure also grounds obvious presentational derivatives the LLM
            # is allowed to produce: sign-flipped deltas.
            keys.add(_round_sig(-v, p))

    def _evict_oldest_values(self) -> bool:
        """Give the OLDEST result's values back to the ledger's bound. True when something was freed.

        The bound stays where the review put it: it guards memory, and a wider value set is a wider target for a
        rounded claim. What changes is who gives way. Before this the result being READ was the one dropped, so past
        the bound a figure the platform had just returned could not be quoted at all - the guardrail's worst failure,
        because it hides true figures rather than admitting false ones.
        """
        freed = False
        for src in self._sources:
            if src is self._source or not src.values:
                continue
            freed = True
            self._held -= len(src.values)
            src.values.clear()
            src.operands.clear()
            self._platform_sorted = None
            # Free a whole slab at once. One eviction costs a rebuild, so freeing a single result's worth would
            # rebuild again a moment later: measured, evicting one at a time made a 120-result session 18x slower
            # to record (4.6s against 0.26s), and the ledger is rebuilt on every model request.
            if self._held <= _LEDGER_CAP - _EVICTION_SLAB:
                break
        if freed:
            self._rebuild_values()
        return freed

    def _rebuild_values(self) -> None:
        """Replay the surviving results into the ledger's sets. Called only on an eviction, which is rare, and the
        sets are bounded by `_LEDGER_CAP`, so the cost is a walk over what the session still holds.

        `counts` is per source (a divisor must come from the same result as the amount), so each source's is cleared
        and refilled from its own values, never pooled.
        """
        self._exact = set()
        self._values_at = {p: set() for p in self._PRECISIONS}
        self._held = sum(len(src.values) for src in self._sources)
        current = self._source
        try:
            for src in self._sources:
                src.counts.clear()
                self._source = src
                for value in src.values:
                    self._record_value(value)
        finally:
            self._source = current

    def _evict_oldest_bases(self) -> bool:
        """Free the pool by dropping the OLDEST result's operands. True when something was freed.

        The cap is what makes the pairwise rule safe (H1), so it does not move; what moves is whose figures occupy
        it. Without this the pool fills once and every later result derives nothing, which reads to a member as the
        same question answered twice, hidden the second time (audit, 2026-09-20). The current source is never
        evicted - a result must always be able to derive from its own figures.
        """
        for src in self._sources:
            if src is self._source or not src.bases:
                continue
            self._n_bases -= len(src.bases)
            src.bases.clear()
            src.sorted_bases.clear()
            src.base_currencies.clear()
            for keys in src.bases_at.values():
                keys.clear()
            return True
        return False

    def _add_base(self, v: float, currency: str | None = None) -> None:
        src = self._source
        key = _round_sig(v, _PRECISION_CAP)
        if isfinite(v) and not _is_exempt(v) and key in src.bases_at[_PRECISION_CAP]:
            # the same figure seen again, perhaps in another currency: it combines with that currency's too
            known = next((b for b in src.base_currencies if _round_sig(b, _PRECISION_CAP) == _round_sig(abs(v), _PRECISION_CAP)),
                         None)
            if known is not None:
                src.base_currencies[known].add(currency)
                for p, keys in src.bases_at.items():
                    keys.setdefault(_round_sig(v, p), set()).add(currency)
                    keys.setdefault(_round_sig(-v, p), set()).add(currency)
            return
        if isfinite(v) and not _is_exempt(v):
            src.operands.append(abs(v))
            self._platform_sorted = None
            if self._n_bases >= _BASE_CAP and (not src.kind.startswith("result:") or not self._evict_oldest_bases()):
                # A full pool: a result evicts the oldest result's pool for its own figures (or keeps the ones it
                # has when the pool is all its own); a member message or the model's prose never evicts (2026-10-01:
                # one amount the member said emptied the pool of the report before it, and every derived figure of
                # that report turned to [unverified]).
                return
            self._n_bases += 1
            src.bases.append(abs(v))
            insort(src.sorted_bases, abs(v))
            src.base_currencies.setdefault(abs(v), set()).add(currency)
            for p, keys in src.bases_at.items():
                keys.setdefault(_round_sig(v, p), set()).add(currency)
                keys.setdefault(_round_sig(-v, p), set()).add(currency)

    # -- provenance ------------------------------------------------------------------ #

    def explain(self, value: float, kind: str = "amount", precision: int | None = None,
                loose: int | None = None, *, ratio_search: bool = False) -> str | None:
        """Why ``value`` is grounded: ``"exempt"``, ``"ledger"``, a named total, or the
        pairwise derivation that produces it. ``None`` when nothing does.

        ``precision`` is the figures the claim was written with (trailing zeros included)
        and gates derivation; ``loose`` drops the trailing zeros and is the precision at
        which the claim may restate a ledger figure ("₹340,000" for 338,451.71). Both
        default to what the value itself shows.

        ``ratio_search`` asks whether SOME pair of one result divides to ``value``. It is off for anything checking a
        model's prose: with a few hundred bases every value in the 1-20x band is reachable, so it accepted up to 100%
        of fabricated ROAS values (audit, 2026-09-20). It stays available to a caller weighing a figure it produced
        itself against one read - `mia.agents.finding_explainer._in_read`, where a row survives only when one read
        carries every figure in it, so the search is a question about that read rather than a proof of a claim."""
        p = max(_PRECISION_FLOOR, min(_PRECISION_CAP, precision or precision_of(value)))
        lp = max(_PRECISION_FLOOR, min(p, loose or precision_of(value)))
        if kind == "percent":
            if abs(value) <= _SMALL_VALUE_EXEMPT:
                return "exempt"
            # A percentage a result CARRIES is grounded by that, exactly as an amount or a multiplier in the ledger
            # is. Until 2026-09-20 this branch went straight to the derivation, so a platform figure could only be
            # grounded by a derivation that happened to land on it: STG turn-785b916a returned every channel's
            # `headroom`, and the answer showed Amazon's (a coincidental percent change hit 680.6) and hid Google's
            # 886.6 as `[unverified]`. Percentages share the value pool with amounts, so this also grounds a claim
            # that collides with an unrelated field - the standard multipliers have been held to since H4, and the
            # smaller of the two holes.
            if _round_sig(value, lp) in self._values_at[lp]:
                return "ledger"
            return self._explain_percent(value, p)
        if kind == "multiplier":
            # ROAS / mROAS live at 1-20x, inside the small-value band; treating them as
            # bookkeeping let a fabricated "4.2x" through unchecked (review 2026-09-05,
            # H4). A multiplier is grounded like an amount: a platform figure as written,
            # or the ratio of two figures from one result. Never exempt.
            if _round_sig(value, lp) in self._values_at[lp]:
                return "ledger"
            # No blind search. Asking "does SOME pair of this result divide to the claim" accepted up to 100% of
            # fabricated ROAS values against a real result (audit, 2026-09-20: 300 bases cover the whole 1-20x band
            # at three significant figures). A multiplier is grounded when the result carries it, or when the answer
            # names the pair that produces it - `_check_named_ratios`, which grants provenance from the text.
            return self._explain_ratio(value, p) if ratio_search else None
        if _is_exempt(value):
            return "exempt"
        if _round_sig(value, lp) in self._values_at[lp]:
            for label, total in self._totals:
                if _close(value, total, lp):
                    return label
            return "ledger"
        if p >= _PRECISION_CAP:
            group = self._groups.get(_round_sig(value, _PRECISION_CAP))
            if group is not None:
                return group
        return self._explain_amount(value, p)

    # Every pairwise derivation searches ONE source at a time: both operands come from
    # the same tool result (review 2026-09-05, H1).

    def _explain_amount(self, value: float, p: int) -> str | None:
        if p < _DERIVED_MIN_PRECISION["amount"]:
            return None
        v = abs(value)
        tol = _half_unit(v, p)
        for src in self._sources:
            for a in src.bases:
                cur = src.base_currencies.get(a)
                if v > a and src.has(v - a, p, tol, cur):
                    return f"{a:g} + {v - a:g}"
                if a > v and src.has(a - v, p, tol, cur):
                    return f"{a:g} - {a - v:g}"
            # A per-period average is a platform amount divided by a count the data
            # carries (baseline_total_revenue / baseline_days, a monthly figure / its
            # days). The divisor must be a count SEEN in the same result, not any
            # integer, so this cannot ground an arbitrary target by choosing a
            # denominator (review 2026-09-04).
            for n in src.counts:
                if src.has(v * n, p, tol * n):
                    return f"{v * n:g} / {n}"
        return self._explain_compared_groups(value, p)

    def _explain_compared_groups(self, value: float, p: int) -> str | None:
        """The difference (or combined total) of two group totals of ONE family: "Google Search spent X more than
        YouTube" over a result that carries a row per campaign (PRD turn-aee40cdf, owner 2026-09-20).

        Each operand is already the platform's own arithmetic (`grouped_totals`); what was missing was permission to
        compare two of them. Held to the same bar as a group total itself - the claim must be written in full - and
        to the same narrowness as every pairwise rule: one source, one family, the data's own groups. A family holds
        at most `_GROUP_KEY_MAX_VALUES` totals, so this searches tens of pairs, not the hundreds a wide base pool
        would.
        """
        if p < _PRECISION_CAP:  # the aggregate band: a rounded claim would collide with a real roll-up
            return None
        v = abs(value)
        tol = _half_unit(v, p)
        for src in self._sources:
            for totals in src.group_families.values():
                for i, (label_a, a) in enumerate(totals):
                    for label_b, b in totals[i + 1:]:
                        if abs(abs(a - b) - v) <= tol:
                            return f"{label_a} - {label_b}"
                        if abs((a + b) - v) <= tol:
                            return f"{label_a} + {label_b}"
        return None

    def _explain_ratio(self, value: float, p: int) -> str | None:
        if value <= 0 or p < _DERIVED_MIN_PRECISION["multiplier"]:
            return None
        rel = _half_unit(value, p) / value
        for src in self._sources:
            for b in src.bases:
                if src.has(value * b, p, value * b * rel, src.base_currencies.get(b)):
                    return f"{value * b:g} / {b:g}"
        return None

    def _explain_percent(self, value: float, p: int) -> str | None:
        if p < _DERIVED_MIN_PRECISION["percent"]:
            return None
        r = value / 100.0
        tol_r = _half_unit(value, p) / 100.0  # absolute tolerance on the ratio itself
        for src in self._sources:
            for b in src.bases:
                cur = src.base_currencies.get(b)
                if src.has(r * b, p, tol_r * b, cur):
                    return f"{r * b:g} / {b:g} as %"
                if src.has((1.0 + r) * b, p, tol_r * b, cur):
                    return f"change from {b:g} to {(1.0 + r) * b:g}"
        return None

    def cross_derivation(self, value: float, precision: int | None = None) -> str | None:
        """The DERIVED class (E13, DR-15): ``value`` as the sum of one named field over every
        tool result that carries it (at least two), or the difference of that field between
        two results. Operands are cited by field and tool. ``None`` when nothing matches.
        Narrow on purpose: same name only, tool results only, amounts only."""
        p = max(_PRECISION_FLOOR, min(_PRECISION_CAP, precision or precision_of(value)))
        if p < _DERIVED_MIN_PRECISION["amount"] or not isfinite(value) or _is_exempt(value):
            return None
        v = abs(value)
        tol = _half_unit(v, p)
        by_name: dict[str, list[tuple[float, str, str | None]]] = {}
        for src in self._sources:
            if not src.kind.startswith("result:"):
                continue
            for name, x in src.named.items():
                if isfinite(x) and not _is_exempt(x):
                    by_name.setdefault(name, []).append((x, src.kind[len("result:"):], src.named_currency.get(name)))
        for name, entries in by_name.items():
            if len(entries) < 2:
                continue
            # amounts in two currencies, or in one nobody named beside a named one, add to no figure
            if all(_combines({ca}, {cb}) for i, (_, _, ca) in enumerate(entries) for _, _, cb in entries[i + 1:]):
                total = sum(x for x, _, _ in entries)
                if abs(total - v) <= tol:
                    tools = sorted({t for _, t, _ in entries})
                    return (f"sum of `{name}` over {len(entries)} tool results "
                            f"({', '.join(tools)})")
            for i, (a, ta, ca) in enumerate(entries):
                for b, tb, cb in entries[i + 1:]:
                    if _combines({ca}, {cb}) and abs(abs(a - b) - v) <= tol:
                        return (f"difference of `{name}` between two tool results "
                                f"({ta}: {a:,.2f}; {tb}: {b:,.2f})")
        return None

    def _check_named_ratios(self, masked: str, out: list[tuple[Figure, str | None]]) -> None:
        """A multiplier the text explains must be produced by the pair it names (owner, 2026-09-20).

        PRD turn-aee40cdf logged ``accepted 7.66 as derived (1.09807e+07 / 1.43351e+06)`` for a sentence that said
        the ROAS was ``$29,468,433.10 / $3,845,225.66``. A multiplier is matched at three significant figures, so in
        a result carrying hundreds of numbers some pair divides to almost any small value: ``_explain_ratio`` was
        answering "some pair produces this" while the claim on screen was "THIS pair produces this".

        So when a ratio is written out, those operands decide it: they must divide to the claim, and each must be
        grounded in its own right. A ratio the text does not explain keeps the old search - narrowing that is its
        own decision, recorded as open.
        """
        for i, (fig, why) in enumerate(out):
            if fig.kind != "multiplier" or fig.start < 0:
                continue
            # Only ever narrows a DERIVATION. A multiplier the result itself carries stays grounded however the
            # answer explains it: rounding the operands in the prose ("7.66x, that is $29.5M / $3.8M") must not
            # redact a figure the platform returned (review, 2026-09-20).
            if why is not None and not _is_pairwise(why):
                continue
            pair = _named_ratio_operands(masked, fig)
            if pair is None:
                continue
            numerator, denominator = pair
            quotient = numerator / denominator if denominator else None
            proven = (quotient is not None
                      and abs(quotient - fig.value) <= _half_unit(abs(fig.value), fig.precision)
                      and self.explain(numerator) is not None
                      and self.explain(denominator) is not None)
            out[i] = (fig, f"{numerator:g} / {denominator:g}" if proven else None)

    def is_grounded(self, value: float, precision: int | None = None) -> bool:
        """True when ``value`` has provenance, direct or derived."""
        return self.explain(value, precision=precision) is not None

    # -- the member's operations on a platform figure (option A, 2026-09-30) ---------- #

    def add_member_numbers(self, items: Iterable[tuple[float, str, str]]) -> None:
        """Record the numbers the member said, each ``(value, kind, direction)``: what a tool argument may be
        derived WITH. Only the member's own words go here (the plugin decides which text is the member's and reads
        it); an item of an unknown kind or direction, a non-finite value or an exempt amount is dropped."""
        for value, kind, direction in items:
            if kind not in MEMBER_KINDS or direction not in MEMBER_DIRECTIONS or not isfinite(value):
                continue
            if kind == "amount" and _is_exempt(value):
                continue
            item = (float(value), kind, direction)
            if item in self._member:
                self._member.remove(item)  # re-said: the newest again
            self._member.append(item)
        del self._member[:-_MEMBER_NUMBERS_CAP]

    def add_member_text(self, text: str) -> None:
        """The numbers written as digits in ``text``, no direction (:func:`member_numbers`): the fallback."""
        self.add_member_numbers(member_numbers(text))

    def explain_input(self, value: float, kind: str = "amount", precision: int | None = None) -> str | None:
        """Why a TOOL ARGUMENT is grounded: everything :meth:`explain` accepts, else the member's own operation on
        a platform figure that gives it ("664585.62 × (1 + 20%)"), else ``None``.

        The operation's base is a figure a platform result carries, or an amount the member said; the operand is a
        number the member said, and what it is (a percentage, a multiple, an amount) decides the operations tried;
        the argument is matched at six figures (an argument is a float, with no written precision to match at), so a
        budget the model rounded is not the member's change and is refused. The model may do the arithmetic; code
        reproduces it, and a slip is refused as before. Never a base the model wrote itself (model-text).
        """
        why = self.explain(value, kind, precision)
        if why is not None or not self._member or not isfinite(value) or value == 0:
            return why
        p = _PRECISION_CAP
        for u, u_kind, direction in reversed(self._member):  # the newest number first
            allowed = _DIRECTION_ALLOWS[direction] if u_kind != "multiplier" else {"+", "-"}
            for op_dir, label, forward, inverse in _MEMBER_OPERATIONS[u_kind]:
                if op_dir not in allowed:
                    continue
                try:
                    b = inverse(value, u)
                except (ZeroDivisionError, OverflowError):
                    b = None
                if b is None or not isfinite(b) or b <= 0:
                    continue
                for x in self._candidate_bases(b):
                    try:
                        got = forward(x, u)
                        # six figures, with half a unit of the last for a value that sits on a rounding boundary
                        if _close(got, value, p) or abs(got - value) <= _half_unit(value, p):
                            return label.format(b=_g(x), u=_g(u))
                    except (ZeroDivisionError, OverflowError):
                        continue
        return None

    def _candidate_bases(self, b: float) -> Iterator[float]:
        """The member's amounts and the platform operands within ``_BASE_SEARCH`` of ``b``, nearest first."""
        lo, hi = b * (1 - _BASE_SEARCH), b * (1 + _BASE_SEARCH)
        found = [x for x, kind, _direction in self._member if kind == "amount" and lo <= x <= hi]
        if self._platform_sorted is None:
            self._platform_sorted = sorted({v for src in self._sources if src.kind.startswith("result:")
                                            for v in src.operands})
        values = self._platform_sorted
        i = bisect_left(values, lo)
        while i < len(values) and values[i] <= hi:
            found.append(values[i])
            i += 1
        yield from sorted(set(found), key=lambda x: abs(x - b))

    def explained(self, text: str) -> list[tuple[Figure, str | None]]:
        """Every figure in ``text`` with its provenance. A figure with none that is a
        rounding of a grounded figure of the same kind in the same text is a restatement
        of it and inherits its provenance."""
        figs = extract_figures(text)
        out = [(fig, self.explain(fig.value, fig.kind, fig.precision, fig.loose)) for fig in figs]
        self._check_named_ratios(_without_identifiers(text), out)
        grounded = [fig for fig, why in out if why is not None]
        for i, (fig, why) in enumerate(out):
            if why is not None:
                continue
            for g in grounded:
                if (g.kind == fig.kind and abs(g.value) >= abs(fig.value) * 0.5
                        and _round_sig(g.value, fig.loose) == _round_sig(fig.value, fig.loose)):
                    out[i] = (fig, f"restates {g.raw}")
                    break
        return out

    def find_ungrounded(self, text: str) -> list[float]:
        """Claimed business figures in ``text`` with no provenance, deduped by exact
        value, order kept. Exact, not 2-figure: ``redact_values`` matches each figure at
        its own precision, so two ungrounded near-twins (₹1,250,000 and ₹1,240,000) must
        both be listed or the second would survive redaction."""
        seen: set[float] = set()
        out: list[float] = []
        for fig, why in self.explained(text):
            if why is not None:
                continue
            if fig.value not in seen:
                seen.add(fig.value)
                out.append(fig.value)
        return out

    def derivations(self, text: str) -> list[tuple[float, str]]:
        """Figures in ``text`` that are grounded by derivation only, with the derivation —
        for the log, so an accepted computed figure is auditable."""
        out: list[tuple[float, str]] = []
        seen: set[float] = set()
        for fig, why in self.explained(text):
            if why in (None, "exempt", "ledger") or why.startswith("restates "):
                continue
            key = _round_sig(fig.value)
            if key not in seen:
                seen.add(key)
                out.append((fig.value, why))
        return out

    def audit(self, text: str) -> dict[str, int]:
        """How the figures in ``text`` are grounded, as counts by kind of provenance:
        ``ledger`` (direct), ``total`` (a platform-determined total or mean), ``derived``
        (pairwise arithmetic), ``restated`` (a rounding of another figure in the text),
        ``exempt``, ``ungrounded``. Zero counts are omitted."""
        counts: dict[str, int] = {}
        for _, why in self.explained(text):
            if why is None:
                kind = "ungrounded"
            elif why in ("ledger", "exempt"):
                kind = why
            elif why.startswith("restates "):
                kind = "restated"
            elif why.startswith(("sum(", "mean(")):
                kind = "total"
            else:
                kind = "derived"
            counts[kind] = counts.get(kind, 0) + 1
        return counts

    def dump(self) -> list[float]:
        return sorted(self._exact)

    @classmethod
    def load(cls, values: Any) -> NumberLedger:
        if isinstance(values, (list, tuple)):
            return cls(float(v) for v in values if isinstance(v, (int, float)))
        return cls()


def where_written(text: str, value: float, width: int = 90) -> str:
    """The line a figure sat on, with the figure itself already replaced: names WHICH figure
    without repeating a number nobody can stand behind."""
    for _, line in locate_ungrounded(text, [value]):
        if line:
            shown = redact_values(line, [value]).strip()
            return shown if len(shown) <= width else shown[: width - 3].rstrip() + "..."
    return "a figure"


def locate_ungrounded(text: str, values: Iterable[float]) -> list[tuple[float, str]]:
    """Pair each ungrounded value with the line it appears on.

    Knowing a report contained "8.16e+04" says nothing about which cell produced it. The
    line does: a "Month | Channel" row and a "Total Budget" row are different bugs with
    different fixes, and without this the only way to tell them apart is to guess.
    """
    lines = (text or "").splitlines()
    located: list[tuple[float, str]] = []
    for value in values:
        target = _round_sig(value)
        hit = ""
        for line in lines:
            if any(_round_sig(n) == target for n in extract_numbers(line)):
                hit = " ".join(line.split())[:160]
                break
        located.append((value, hit))
    return located
