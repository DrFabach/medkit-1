__all__ = ["BratInputConverter"]
from pathlib import Path
from typing import Optional, Tuple, Union, ValuesView, List
import warnings

from smart_open import open

from medkit.core import (
    Collection,
    Attribute,
    InputConverter,
    Store,
    OperationDescription,
    ProvBuilder,
    generate_id,
)
from medkit.core.text import TextDocument, Entity, Relation, Span
from medkit.core.text.annotation import Segment
import medkit.io._brat_utils as brat_utils

TEXT_EXT = ".txt"
ANN_EXT = ".ann"
ANN_CONF_FILE = "annotation.conf"


class BratInputConverter(InputConverter):
    """Class in charge of converting brat annotations"""

    def __init__(self, store: Optional[Store] = None, id: Optional[str] = None):
        if id is None:
            id = generate_id()

        self.id: str = id
        self.store: Optional[Store] = store

        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        return OperationDescription(id=self.id, name=self.__class__.__name__)

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def load(
        self,
        dir_path: Union[str, Path],
        ann_ext: str = ANN_EXT,
        text_ext: str = TEXT_EXT,
    ) -> Collection:
        """
        Create a Collection of TextDocuments from a folder containting text files
        and associated brat annotations files.

        Parameters
        ----------
        dir_path:
            The path to the directory containing the text files and the annotation
            files (.ann)
        ann_ext:
            The extension of the brat annotation file (e.g. .ann)
        text_ext:
            The extension of the text file (e.g. .txt)

        Returns
        -------
        Collection
            The collection of TextDocuments
        """
        documents = list()
        dir_path = Path(dir_path)

        # find all base paths with at least a corresponding text or ann file
        base_paths = set()
        for ann_path in sorted(dir_path.glob("*" + ann_ext)):
            base_paths.add(dir_path / ann_path.stem)
        for text_path in sorted(dir_path.glob("*" + text_ext)):
            base_paths.add(dir_path / text_path.stem)

        # load doc for each base_path
        for base_path in sorted(base_paths):
            text_path = base_path.with_suffix(text_ext)
            if not text_path.exists():
                text_path = None
            ann_path = base_path.with_suffix(ann_ext)
            if not ann_path.exists():
                ann_path = None
            doc = self._load_doc(ann_path=ann_path, text_path=text_path)
            documents.append(doc)

        if not documents:
            warnings.warn(f"Didn't load any document from dir {dir_path}")

        return Collection(documents)

    def _load_doc(
        self, ann_path: Optional[Path] = None, text_path: Optional[Path] = None
    ) -> TextDocument:
        """
        Create a TextDocument from text file and its associated annotation file (.ann)

        Parameters
        ----------
        text_path:
            The path to the text document file.
        ann_path:
            The path to the brat annotation file.

        Returns
        -------
        TextDocument
            The document containing the text and the annotations
        """
        assert ann_path is not None or text_path is not None

        metadata = dict()
        if text_path is not None:
            metadata.update(path_to_text=text_path)
            with open(text_path, encoding="utf-8") as text_file:
                text = text_file.read()
        else:
            text = None

        if ann_path is not None:
            metadata.update(path_to_ann=ann_path)
            anns = self._load_anns(ann_path)
        else:
            anns = []

        doc = TextDocument(text=text, metadata=metadata, store=self.store)
        for ann in anns:
            doc.add_annotation(ann)

        return doc

    def _load_anns(self, ann_path: Path) -> ValuesView[Union[Entity, Relation]]:
        brat_doc = brat_utils.parse_file(ann_path)
        anns_by_brat_id = dict()

        # First convert entities, then relations, finally attributes
        # because new annotation id is needed
        for brat_entity in brat_doc.entities.values():
            entity = Entity(
                label=brat_entity.type,
                spans=[Span(*brat_span) for brat_span in brat_entity.span],
                text=brat_entity.text,
                metadata=dict(brat_id=brat_entity.id),
            )
            anns_by_brat_id[brat_entity.id] = entity
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    entity, self.description, source_data_items=[]
                )

        for brat_relation in brat_doc.relations.values():
            relation = Relation(
                label=brat_relation.type,
                source_id=anns_by_brat_id[brat_relation.subj].id,
                target_id=anns_by_brat_id[brat_relation.obj].id,
                metadata=dict(brat_id=brat_relation.id),
            )
            anns_by_brat_id[brat_relation.id] = relation
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    relation, self.description, source_data_items=[]
                )

        for brat_attribute in brat_doc.attributes.values():
            attribute = Attribute(
                label=brat_attribute.type,
                value=brat_attribute.value,
                metadata=dict(brat_id=brat_attribute.id),
            )
            anns_by_brat_id[brat_attribute.target].attrs.append(attribute)
            if self._prov_builder is not None:
                self._prov_builder.add_prov(
                    attribute, self.description, source_data_items=[]
                )

        return anns_by_brat_id.values()


class BratOutputConverter:
    """Class in charge of converting a list/Collection of TextDocuments into a
    list of brat annotations files"""

    def __init__(
        self,
        label_anns: Optional[List[str]] = None,
        attrs: Optional[List[str]] = None,
        keep_segments: bool = False,
        op_id: Optional[str] = None,
    ):
        self.label_anns = label_anns
        self.attrs = attrs
        self.keep_segments = keep_segments
        self.op_id: str = op_id
        self._prov_builder: Optional[ProvBuilder] = None

    @property
    def description(self) -> OperationDescription:
        return OperationDescription(id=self.op_id, name=self.__class__.__name__)

    def set_prov_builder(self, prov_builder: ProvBuilder):
        self._prov_builder = prov_builder

    def convert(
        self,
        medkit_docs: Union[List[TextDocument], Collection],
        output_path: Union[str, Path],
    ):
        """Convert a collection of TextDocuments into a brat collection
        For each collection or list of documents, a folder is created with
        the txt and ann files."""

        if isinstance(medkit_docs, Collection):
            medkit_docs = [
                medkit_doc
                for medkit_doc in medkit_docs.documents
                if isinstance(medkit_doc, TextDocument)
            ]

        output_path = Path(output_path)
        output_path.mkdir(parents=True, exist_ok=True)

        for medkit_doc in medkit_docs:
            doc_id = medkit_doc.id

            if medkit_doc.text is not None:
                text_path = output_path / f"{doc_id}{TEXT_EXT}"
                with text_path.open("w", encoding="utf-8") as file:
                    file.write(medkit_doc.text)
                    file.close()

            entities, relations, attrs = self._get_anns_from_medkit_doc(medkit_doc)
            brat_str = self._create_brat_from_anns(entities, relations, attrs)
            ann_path = output_path / f"{doc_id}{ANN_EXT}"
            with ann_path.open("w", encoding="utf-8") as file:
                file.write(brat_str)
                file.close()

        # WIP: generate annotation_conf file
        ann_conf = self._generate_annotation_conf(entities)
        conf_path = output_path / ANN_CONF_FILE
        with conf_path.open("w", encoding="utf-8") as file:
            file.write(ann_conf)
            file.close()

    def _get_anns_from_medkit_doc(
        self, medkit_doc: TextDocument
    ) -> Tuple[List[Entity], List[Relation], List[str]]:
        """Return selected annotations from a medkit document.
        `attrs` is a list of attribute labels to include for each
         entity/segment or relation found
        """
        annotations = medkit_doc.get_annotations()

        if self.label_anns is not None:
            # filter annotations by label
            annotations = [ann for ann in annotations if ann.label in self.label_anns]

        if self.label_anns and annotations == []:
            # labels_anns were a list but none of the annotations
            # had a label of interest
            labels_str = ",".join(self.label_anns)
            warnings.warn(
                "No medkit annotations were included because none have"
                f" '{labels_str}' as label."
            )

        if self.attrs is None:
            # include all atributes
            attrs = set(attr.label for ann in annotations for attr in ann.attrs)

        segments = []
        relations = []
        for ann in annotations:
            if isinstance(ann, Entity):
                segments.append(ann)
            elif isinstance(ann, Segment) and self.keep_segments:
                # In brat only entities exists, in some cases
                # a medkit document could include segments
                # that may be exported as entities
                segments.append(ann)
            elif isinstance(ann, Relation):
                relations.append(ann)

        return segments, relations, attrs

    def _create_brat_from_anns(
        self, segments: List[Segment], relations: List[Relation], attrs: List[str]
    ):
        brat_annotations = ""
        nb_segment, nb_relation, nb_attribute = 1, 1, 1
        brat_id_by_segment_id = dict()

        # First convert segments then relations including its attributes
        for medkit_segment in segments:
            brat_id, brat_entity = brat_utils._get_brat_from_segment(
                medkit_segment, nb_segment
            )
            brat_id_by_segment_id[medkit_segment.id] = brat_id
            brat_annotations += brat_entity
            nb_segment += 1
            # include selected attributes
            for attr in medkit_segment.attrs:
                if attr.label in attrs:
                    attrs_brat = brat_utils._get_brat_from_attribute(
                        attr, nb_attribute, target_brat_id=brat_id
                    )
                    nb_attribute += 1
                    brat_annotations += attrs_brat

        for medkit_relation in relations:
            brat_id, relation_brat = brat_utils._get_brat_from_relation(
                medkit_relation, nb_relation, brat_id_by_segment_id
            )
            brat_annotations += relation_brat
            nb_relation += 1
            # include selected attributes
            # Note: it seems that brat does not support attributes for relations
            for attr in medkit_relation.attrs:
                if attr.label in attrs:
                    attrs_brat = brat_utils._get_brat_from_attribute(
                        attr, nb_attribute, target_brat_id=brat_id
                    )
                    nb_attribute += 1
                    brat_annotations += attrs_brat

        return brat_annotations

    def _generate_annotation_conf(
        self,
        entities,
    ):
        """WIP: Generate a annotation configuration file for brat
        Its divided into [entities],[relations],[events] (not supported in medkit)
        and [attributes]"""
        annotation_conf = (
            "# Text-based definitions of entity types, relation types\n"
            "# and attributes. Generate using medkit from HeKa project"
        )

        annotation_conf += "\n[entities]\n\n"
        entity_section = "\n".join(set(ent.label.replace(" ", "_") for ent in entities))
        annotation_conf += entity_section

        annotation_conf += "\n[relations]\n\n"
        # enable overlap between entities
        annotation_conf += "<OVERLAP> 	Arg1:<ENTITY>, Arg2:<ENTITY>, <OVL-TYPE>:<ANY>"

        annotation_conf += "\n[attributes]\n\n"
        annotation_conf += "\n[events]\n\n"

        return annotation_conf
