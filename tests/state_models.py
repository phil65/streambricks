"""State models used by the tests (defined outside the app script so they survive reruns)."""

from __future__ import annotations

import streambricks as sb


class Counter(sb.State):
    value: int = 0
