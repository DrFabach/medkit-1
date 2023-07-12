import dataclasses
from medkit.io._doccano_utils import (
    DoccanoDocRelationExtraction,
    DoccanoDocTextClassification,
    DoccanoDocSeqLabeling,
    DoccanoEntity,
    DoccanoRelation,
    DoccanoEntityTuple,
)


@dataclasses.dataclass
class _MockClientConfig:
    column_text: str = "text"
    column_label: str = "label"


def test_doc_relation_extraction_from_dict():
    test_line = {
        "text": "medkit was created in 2022",
        "entities": [
            {"id": 0, "start_offset": 0, "end_offset": 6, "label": "ORG"},
            {"id": 1, "start_offset": 22, "end_offset": 26, "label": "DATE"},
        ],
        "relations": [{"id": 0, "from_id": 0, "to_id": 1, "type": "created_in"}],
        "custom_data": "phrase_0",
    }
    doc = DoccanoDocRelationExtraction.from_dict(
        test_line, client_config=_MockClientConfig()
    )
    assert len(doc.entities) == 2
    assert len(doc.relations) == 1

    entity = DoccanoEntity(id=0, start_offset=0, end_offset=6, label="ORG")
    assert entity in doc.entities
    relation = DoccanoRelation(id=0, from_id=0, to_id=1, type="created_in")
    assert relation in doc.relations
    # test with metadata import
    assert doc.metadata == dict(custom_data="phrase_0")


def test_doc_seq_labeling_from_dict():
    test_line = {
        "text": "medkit was created in 2022",
        "label": [(0, 6, "ORG"), (22, 26, "DATE")],
    }

    doc = DoccanoDocSeqLabeling.from_dict(test_line, client_config=_MockClientConfig())
    assert len(doc.entities) == 2
    entity = DoccanoEntityTuple(start_offset=0, end_offset=6, label="ORG")
    assert entity in doc.entities
    # test with metadata import,
    # there is no additional keys, so metadata should be empty
    assert doc.metadata == {}


def test_doc_text_classification_from_dict():
    test_line = {"text": "medkit was created in 2022", "label": ["header"]}
    doc = DoccanoDocTextClassification.from_dict(
        test_line, client_config=_MockClientConfig()
    )
    assert doc.label == "header"
    # test with metadata import,
    # there is no additional keys, so metadata should be empty
    assert doc.metadata == {}
