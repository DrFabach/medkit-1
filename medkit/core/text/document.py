from __future__ import annotations

__all__ = ["TextDocument"]

import dataclasses
import random
import uuid
from typing import Any, ClassVar, Dict, List, Optional
from typing_extensions import Self

from medkit.core import dict_conv
from medkit.core.id import generate_id
from medkit.core.text.annotation import TextAnnotation, Segment
from medkit.core.text.annotation_container import TextAnnotationContainer
from medkit.core.text.span import Span


@dataclasses.dataclass(init=False)
class TextDocument(dict_conv.SubclassMapping):
    """
    Document holding text annotations

    Annotations must be subclasses of `TextAnnotation`.

    Attributes
    ----------
    uid:
        Unique identifier of the document.
    text:
        Full document text.
    anns:
        Annotations of the document. Stored in an
        :class:`~.TextAnnotationContainer` but can be passed as a list at init.
    metadata:
        Document metadata.
    raw_segment:
        Auto-generated segment containing the full unprocessed document text. To
        get the raw text as an annotation to pass to processing operations:

        >>> doc = TextDocument(text="hello")
        >>> raw_text = doc.anns.get(label=TextDocument.RAW_LABEL)[0]
    """

    RAW_LABEL: ClassVar[str] = "RAW_TEXT"

    uid: str
    anns: TextAnnotationContainer
    metadata: Dict[str, Any]
    raw_segment: Segment

    def __init__(
        self,
        text: str,
        anns: Optional[List[TextAnnotation]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        uid: Optional[str] = None,
    ):
        if anns is None:
            anns = []
        if metadata is None:
            metadata = {}
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self.metadata = metadata

        # auto-generated raw segment to hold the text
        self.raw_segment = self._generate_raw_segment(text, uid)

        self.anns = TextAnnotationContainer(
            doc_id=self.uid, raw_segment=self.raw_segment
        )
        for ann in anns:
            self.anns.add(ann)

    @classmethod
    def _generate_raw_segment(cls, text: str, doc_id: str) -> Segment:
        # generate deterministic uuid based on document uid
        # so that the annotation uid is the same if the doc uid is the same
        rng = random.Random(doc_id)
        uid = str(uuid.UUID(int=rng.getrandbits(128)))

        return Segment(
            label=cls.RAW_LABEL,
            spans=[Span(0, len(text))],
            text=text,
            uid=uid,
        )

    @property
    def text(self) -> str:
        return self.raw_segment.text

    def __init_subclass__(cls):
        TextDocument.register_subclass(cls)
        super().__init_subclass__()

    def to_dict(self, with_anns: bool = True) -> Dict[str, Any]:
        doc_dict = dict(
            uid=self.uid,
            text=self.text,
            metadata=self.metadata,
        )
        if with_anns:
            doc_dict["anns"] = [a.to_dict() for a in self.anns]

        dict_conv.add_class_name_to_data_dict(self, doc_dict)
        return doc_dict

    @classmethod
    def from_dict(cls, doc_dict: Dict[str, Any]) -> Self:
        """
        Creates a TextDocument from a dict

        Parameters
        ----------
        doc_dict: dict
            A dictionary from a serialized TextDocument as generated by to_dict()
        """

        if not dict_conv.has_same_from_dict(cls, TextDocument):
            # if class method is not the same as the TextDocument one
            # (e.g., when subclassing with an overriding method)
            subclass = cls.get_subclass_for_data_dict(doc_dict)
            if subclass is not None:
                return subclass.from_dict(doc_dict)

        anns = [TextAnnotation.from_dict(a) for a in doc_dict.get("anns", [])]
        return cls(
            uid=doc_dict["uid"],
            text=doc_dict["text"],
            anns=anns,
            metadata=doc_dict["metadata"],
        )
