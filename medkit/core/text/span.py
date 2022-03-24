__all__ = [
    "Span",
    "ModifiedSpan",
    "AnySpanType",
]

import dataclasses
from typing import List, NamedTuple, Union


class Span(NamedTuple):
    """
    Slice of text extracted from the original text

    Attributes
    ----------
    start: int
        Index of the first character in the original text
    end: int
        Index of the last character in the original text, plus one
    """

    start: int
    end: int

    @property
    def length(self):
        return self.end - self.start


@dataclasses.dataclass
class ModifiedSpan:
    """
    Slice of text not present in the original text

    Attributes
    ----------
    length:
        Number of characters
    replaced_spans:
        Slices of the original text that this span is replacing
    """

    length: int
    replaced_spans: List[Span]


AnySpanType = Union[Span, ModifiedSpan]
