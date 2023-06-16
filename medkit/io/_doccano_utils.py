import dataclasses
from typing import Any, Dict, List

from typing_extensions import Self


@dataclasses.dataclass()
class DoccanoEntity:
    id: int
    start_offset: int
    end_offset: int
    label: str


@dataclasses.dataclass()
class DoccanoEntityTuple:
    start_offset: int
    end_offset: int
    label: str


@dataclasses.dataclass()
class DoccanoRelation:
    id: int
    from_id: int
    to_id: int
    type: str


@dataclasses.dataclass()
class DoccanoDocRelationExtraction:
    id: int
    text: str
    entities: Dict[str, DoccanoEntity]
    relations: Dict[str, DoccanoRelation]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(cls, doc_line: Dict[str, Any], column_text: str) -> Self:
        id = doc_line.get("id", None)
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        entities = dict()
        relations = dict()

        for ann in doc_line["entities"]:
            entity = DoccanoEntity(**ann)
            entities[entity.id] = entity

        for ann in doc_line["relations"]:
            relation = DoccanoRelation(**ann)
            relations[relation.id] = relation

        return cls(
            text=text, id=id, entities=entities, relations=relations, metadata=metadata
        )


@dataclasses.dataclass()
class DoccanoDocSeqLabeling:
    text: str
    entities: List[DoccanoEntityTuple]
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(
        cls, doc_line: Dict[str, Any], column_text: str, column_label: str
    ) -> Self:
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        entities = [DoccanoEntityTuple(*ann) for ann in doc_line[column_label]]
        return cls(text=text, entities=entities, metadata=metadata)


@dataclasses.dataclass()
class DoccanoDocTextClassification:
    text: str
    label: str
    metadata: Dict[str, Any]

    @classmethod
    def from_dict(
        cls, doc_line: Dict[str, Any], column_text: str, column_label: str
    ) -> Self:
        text = doc_line[column_text]
        metadata = doc_line.get("metadata", {})
        return cls(text=text, label=doc_line[column_label][0], metadata=metadata)
