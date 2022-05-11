import pytest
import spacy
from spacy.tokens import Doc, Span as SpacySpan

from medkit.core import Attribute
from medkit.core.text import Span, Entity, Segment, TextDocument
from medkit.text.spacy import spacy_utils


@pytest.fixture(scope="module")
def nlp_spacy():
    return spacy.blank("en")


TEXT = (
    "The patient's father was prescribed Lisinopril because he was suffering from"
    " severe hypertension.\nThe patient is taking Levothyroxine"
)


def _get_doc():
    medkit_doc = TextDocument(text=TEXT)

    # entities
    ent_1 = Entity(
        label="medication", spans=[Span(36, 46)], text="Lisinopril", attrs=[]
    )
    medkit_doc.add_annotation(ent_1)

    ent_2_attr = Attribute(label="severity", value="high")
    ent_2 = Entity(
        label="disease", spans=[Span(84, 96)], text="hypertension", attrs=[ent_2_attr]
    )
    medkit_doc.add_annotation(ent_2)

    ent_3 = Entity(
        label="medication", spans=[Span(120, 133)], text="Levothyroxine", attrs=[]
    )
    medkit_doc.add_annotation(ent_3)

    # segments
    seg_1_attr = Attribute(label="family", value=True)
    seg_1 = Segment(
        label="PEOPLE",
        spans=[Span(0, 20)],
        text="The patient's father",
        attrs=[seg_1_attr],
    )
    medkit_doc.add_annotation(seg_1)

    seg_2_attr = Attribute(label="family", value=False)
    seg_2 = Segment(
        label="PEOPLE", spans=[Span(98, 109)], text="The patient", attrs=[seg_2_attr]
    )
    medkit_doc.add_annotation(seg_2)
    return medkit_doc


def _assert_spacy_doc(doc, raw_annotation):
    assert isinstance(doc, Doc)
    assert Doc.has_extension("medkit_id")
    assert doc._.get("medkit_id") == raw_annotation.id


# test medkit doc to spacy doc
def test_medkit_to_spacy_doc_without_anns(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=[],
        attrs=[],
        include_medkit_info=True,
    )
    # spacy doc was created and has the same ID as raw_ann
    _assert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    # no ents were transfered
    assert spacy_doc.ents == ()

    # test without medkit info
    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=[],
        attrs=[],
        include_medkit_info=False,
    )

    assert spacy_doc._.get("medkit_id") is None


def test_medkit_to_spacy_doc_selected_ents_list(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=["medication", "disease"],
        attrs=[],
        include_medkit_info=True,
    )
    # spacy doc was created and has the same ID as raw_ann
    _assert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    # ents were transfer, 2 for medication, 1 for disease
    assert len(spacy_doc.ents) == 3

    ents = [
        ent
        for label in ["medication", "disease"]
        for ent in medkit_doc.get_annotations_by_label(label)
    ]
    # guarantee the same order to compare
    doc_ents = sorted(spacy_doc.ents, key=lambda sp: sp.label)
    ents = sorted(ents, key=lambda sp: sp.label)

    # each entity created has the same id and label as its entity of origin
    assert all(
        ent_spacy._.get("medkit_id") == ent_medkit.id
        for ent_spacy, ent_medkit in zip(doc_ents, ents)
    )

    assert all(
        ent_spacy.label_ == ent_medkit.label
        for ent_spacy, ent_medkit in zip(doc_ents, ents)
    )

    # check disease spacy span
    disease_spacy_span = next(e for e in doc_ents if e.label_ == "disease")
    assert (disease_spacy_span.start_char, disease_spacy_span.end_char) == (84, 96)

    # test warning for labels
    with pytest.warns(UserWarning, match=r"No medkit annotations"):
        spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
            nlp=nlp_spacy,
            medkit_doc=medkit_doc,
            labels_anns=["person"],
            attrs=[],
            include_medkit_info=True,
        )


def test_medkit_to_spacy_doc_all_anns(nlp_spacy):
    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]

    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=None,
        attrs=[],
        include_medkit_info=True,
    )
    _assert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2


def test_medkit_to_spacy_doc_all_anns_family_attr(nlp_spacy):

    medkit_doc = _get_doc()
    raw_annotation = medkit_doc.get_annotations_by_label(medkit_doc.RAW_TEXT_LABEL)[0]
    spacy_doc = spacy_utils.build_spacy_doc_from_medkit_doc(
        nlp=nlp_spacy,
        medkit_doc=medkit_doc,
        labels_anns=None,
        attrs=["family"],
        include_medkit_info=True,
    )
    _assert_spacy_doc(spacy_doc, raw_annotation)
    assert spacy_doc.text == medkit_doc.text
    assert len(spacy_doc.ents) == 3
    assert len(spacy_doc.spans) == 1
    assert len(spacy_doc.spans["PEOPLE"]) == 2

    # testing attrs in spans
    assert SpacySpan.has_extension("family")
    assert isinstance(spacy_doc.spans["PEOPLE"][0]._.get("family"), bool)
    # entity is a span but family should be NONE
    assert spacy_doc.ents[0]._.get("family") is None


# test medkit segments to spacy doc
def test_medkit_segments_to_spacy_docs(nlp_spacy):
    medkit_doc = _get_doc()
    segments = medkit_doc.get_annotations_by_label("PEOPLE")
    spacy_docs = [
        spacy_utils.build_spacy_doc_from_medkit_segment(
            nlp=nlp_spacy, segment=ann, annotations=[], include_medkit_info=True
        )
        for ann in segments
    ]
    assert len(spacy_docs) == 2

    for doc, ann_source in zip(spacy_docs, segments):
        _assert_spacy_doc(doc, ann_source)

    # testing when 'include_medkit_info' is False
    spacy_docs = [
        spacy_utils.build_spacy_doc_from_medkit_segment(
            nlp=nlp_spacy, segment=ann, annotations=[], include_medkit_info=False
        )
        for ann in segments
    ]

    for doc in spacy_docs:
        # check if medkit id is not included
        assert doc._.get("medkit_id") is None
