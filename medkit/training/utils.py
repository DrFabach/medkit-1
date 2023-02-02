from __future__ import annotations

from collections import OrderedDict
from typing import Any, Dict, List, Union
from typing_extensions import Protocol, runtime_checkable

import torch


class BatchData(OrderedDict):
    """A BatchData pack data allowing both column and row access"""

    def __getitem__(self, index: int) -> Dict[str, Union[List[Any], torch.Tensor]]:
        if isinstance(index, str):
            inner_dict = {key: values for (key, values) in self.items()}
            return inner_dict[index]
        return {key: values[index] for key, values in self.items()}

    def __getattr__(self, name: str) -> Union[List[Any], torch.Tensor]:
        if name in self.keys():
            return self[name]
        else:
            raise AttributeError(f"Object has not attribute '{name}'")

    def __setattr__(self, name, values):
        if name in self.keys() and values is not None:
            super().__setitem__(name, values)
        super().__setattr__(name, values)

    def __setitem__(self, key, values):
        super().__setitem__(key, values)
        super().__setattr__(key, values)

    def to_device(self, device: torch.device) -> BatchData:
        """
        Ensure that Tensors in the BatchData object are on the specified `device`

        Parameters
        ----------
        device:
            A `torch.device` object representing the device on which tensors
            will be allocated.

        Returns
        -------
        BatchData
            A new object with the tensors on the proper device.
        """
        inner_batch = BatchData()
        for key, value in self.items():
            if isinstance(value, torch.Tensor):
                inner_batch[key] = value.to(device)
            else:
                inner_batch[key] = value
        return inner_batch


@runtime_checkable
class MetricsCalculator(Protocol):
    "A MetricsCalculator is the base protocol to compute metrics in training"

    def prepare_batch(
        self, model_output: BatchData, input_batch: BatchData
    ) -> Dict[str, List[any]]:
        """Prepare a batch of data to compute the metrics

        Parameters
        ----------
        model_output: BatchData
            Output data after a model forward pass.
        input_batch: BatchData
            Preprocessed input batch

        Returns
        -------
        Dict[str, List[any]]
            A dictionary with the required data to calculate the metric
        """
        pass

    def compute(self, all_data: Dict[str, List[any]]) -> Dict[str, float]:
        """Compute metrics using 'all_data'

        Parameters
        ----------
        all_data: Dict[str, List[any]]
            A dictionary to compute the metrics.
            i.e. A dictionary with a list of 'references' and a list of 'predictions'.

        Returns
        -------
        Dict[str, float]
            A dictionary with the results
        """
        pass
