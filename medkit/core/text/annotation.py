from __future__ import annotations

__all__ = ["TextAnnotation", "Segment", "Entity", "Relation"]

import abc
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from medkit.core.annotation import Annotation, Attribute
from medkit.core.text import span_utils
from medkit.core.text.span import AnySpanType

if TYPE_CHECKING:
    from medkit.core.text.document import TextDocument


class TextAnnotation(Annotation):
    """Base abstract class for all text annotations"""

    @abc.abstractmethod
    def __init__(
        self,
        label: str,
        attrs: Optional[List[Attribute]] = None,
        ann_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        return super().__init__(
            label=label, attrs=attrs, ann_id=ann_id, metadata=metadata
        )


class Segment(TextAnnotation):
    def __init__(
        self,
        label: str,
        spans: List[AnySpanType],
        text: str,
        attrs: Optional[List[Attribute]] = None,
        ann_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a medkit segment

        Parameters
        ----------
        label: str
            The label for this annotation (e.g., SENTENCE)
        spans: List[Span]
            The annotation span
        text: str
            The annotation text
        attrs:
            The attributes of the segment
        ann_id: str, Optional
            The id of the annotation (if existing)
        metadata: dict[str, Any], Optional
            The metadata of the annotation
        """
        super().__init__(ann_id=ann_id, label=label, attrs=attrs, metadata=metadata)
        self.spans: List[AnySpanType] = spans
        self.text: str = text

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        spans = [s.to_dict() for s in self.spans]
        data.update(spans=spans, text=self.text)
        return data

    def get_snippet(self, doc: TextDocument, max_extend_length: int) -> str:
        """Return a portion of the original text contaning the annotation

        Parameters
        ----------
        doc:
            The document to which the annotation is attached

        max_extend_length:
            Maximum number of characters to use around the annotation

        Returns
        -------
        str:
            A portion of the text around the annotation
        """
        spans_normalized = span_utils.normalize_spans(self.spans)
        start = min(s.start for s in spans_normalized)
        end = max(s.end for s in spans_normalized)
        start_extended = max(start - max_extend_length // 2, 0)
        remaining_max_extend_length = max_extend_length - (start - start_extended)
        end_extended = min(end + remaining_max_extend_length, len(doc.text))
        return doc.text[start_extended:end_extended]

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, spans={self.spans!r}, text={self.text!r}"


class Entity(Segment):
    def __init__(
        self,
        label: str,
        spans: List[AnySpanType],
        text: str,
        attrs: Optional[List[Attribute]] = None,
        entity_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize a medkit text entity

        Parameters
        ----------
        label: str
            The entity label
        spans: List[Span]
            The entity span
        text: str
            The entity text
        attrs:
            The attributes of the entity
        entity_id: str, Optional
            The id of the entity (if existing)
        metadata: dict[str, Any], Optional
            The metadata of the entity
        """
        super().__init__(
            label=label,
            spans=spans,
            text=text,
            attrs=attrs,
            ann_id=entity_id,
            metadata=metadata,
        )


class Relation(TextAnnotation):
    def __init__(
        self,
        label: str,
        source_id: str,
        target_id: str,
        attrs: Optional[List[Attribute]] = None,
        rel_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the medkit relation

        Parameters
        ----------
        label: str
            The relation label
        source_id: str
            The id of the entity from which the relation is defined
        target_id: str
            The id of the entity to which the relation is defined
        attrs:
            The attributes of the relation
        rel_id: str, Optional
            The id of the relation (if existing)
        metadata: Dict[str, Any], Optional
            The metadata of the relation
        """
        super().__init__(ann_id=rel_id, label=label, attrs=attrs, metadata=metadata)
        self.source_id: str = source_id
        self.target_id: str = target_id

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update(source_id=self.source_id, target_id=self.target_id)
        return data

    def __repr__(self):
        annotation = super().__repr__()
        return f"{annotation}, source={self.source_id}, target_id={self.target_id}"
