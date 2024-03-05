from __future__ import annotations

__all__ = ["Attribute"]

import dataclasses
from typing import Any

from typing_extensions import Self

from medkit.core import dict_conv
from medkit.core.id import generate_id


@dataclasses.dataclass
class Attribute(dict_conv.SubclassMapping):
    """Medkit attribute, to be added to an annotation.

    Attributes
    ----------
    label: str
        The attribute label
    value: Any, optional
        The value of the attribute. Should be either simple built-in types (int,
        float, bool, str) or collections of these types (list, dict, tuple). If
        you need structured complex data you should create a subclass of
        `Attribute`.
    metadata: dict of str to Any
        The metadata of the attribute
    uid: str
        The identifier of the attribute
    """

    label: str
    value: Any | None
    metadata: dict[str, Any]
    uid: str

    def __init__(
        self,
        label: str,
        value: Any | None = None,
        metadata: dict[str, Any] | None = None,
        uid: str | None = None,
    ):
        if metadata is None:
            metadata = {}
        if uid is None:
            uid = generate_id()

        self.uid = uid
        self.label = label
        self.value = value
        self.metadata = metadata

    def __init_subclass__(cls):
        Attribute.register_subclass(cls)
        super().__init_subclass__()

    def to_dict(self) -> dict[str, Any]:
        attribute_dict = {
            "uid": self.uid,
            "label": self.label,
            "value": self.value,
            "metadata": self.metadata,
        }
        dict_conv.add_class_name_to_data_dict(self, attribute_dict)
        return attribute_dict

    def to_brat(self) -> Any | None:
        """Return a value compatible with the brat format."""
        return self.value

    def to_spacy(self) -> Any | None:
        """Return a value compatible with spaCy."""
        return self.value

    def copy(self) -> Attribute:
        """Create a copy of the attribute with a new identifier.

        This is used when we want to duplicate an existing attribute onto a
        different annotation.
        """
        return dataclasses.replace(self, uid=generate_id())

    @classmethod
    def from_dict(cls, attribute_dict: dict[str, Any]) -> Self:
        """Create an Attribute from a dict.

        Parameters
        ----------
        attribute_dict: dict of str to Any
            A dictionary from a serialized Attribute as generated by to_dict()
        """
        subclass = cls.get_subclass_for_data_dict(attribute_dict)
        if subclass is not None:
            return subclass.from_dict(attribute_dict)

        return cls(
            uid=attribute_dict["uid"],
            label=attribute_dict["label"],
            value=attribute_dict["value"],
            metadata=attribute_dict["metadata"],
        )
