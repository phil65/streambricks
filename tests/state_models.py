"""State models used by the tests (defined outside the app script so they survive reruns)."""

import streambricks as sb


class Counter(sb.State):
    value: int = 0
