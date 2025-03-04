# Developer Guide

This guide should help developers to understand the implementation, and maintain or extend it. The [structure section](#structure) section explains the overall structure. The [measurement subsystem](#measurement-subsystem) and [comparison subsystem](#comparison-subsystem) explain the individual subsystems. Finally how to add a new metric is explained in [this](#how-to-add-a-metric) section.
Generally most methods and classes include documentation that explains their purpose.

## Structure

The project is organized into several folders, each containing specific types of logic and functionality:

```
comparison/
    ...
measurement/
    ...
gui/
    comparison/
        ...
    measurement/
        ...
main.py
tests/
    ...
```

### Folder Descriptions

- **comparison/**: Contains the core logic for executing comparisons, managing comparison results, and handling comparison repositories.
- **measurement/**: Handles measurement data and related processing. It includes the import of measurements, preprocessing and storing.
- **gui/**: Implements the graphical user interface components for the application, it has two more subfolders each containing the gui dealing with the respective subsystem.
- **main.py**: Entry point for the application.
- **tests/**: Contains unit tests and test-related logic to ensure the correctness of the application.

## Measurement Subsystem

This section gives a brief overview of the measurement subsystem, which is located in the `./measurement` folder. The subsystem is split in three kinds of classes, data classes, service classes and repository classes.
![](./figures/Measurement%20Subsystem%20Data.png)
This Figure shows the data classes involved in the measurement subsystem.
- `Measurement`: Contains metadata of a measurement, like ID, name, and the channels which are associated with the `Measurement`.
- `Channel`: Contains channel metadata like name, pdu, and ID.
- `ChannelData`: Contains the actual SignalData of the `Channel`. There is a one to one relation to Channels, by both sharing the same ID. The split of `Channel` and `ChannelData` is done due to performance considerations.
- `MeasurementImportInfo`: Contains info necessary to import a measurement from a file. Mainly used to streamline communication between the GUI subsystem and thr import of measurements.

The next figure shows the service and repository classes involved in the subsystem.
![](./figures/Measurement%20Subsystem%20Services.png)

### Repository Classes:
- `MeasurementRegistry`: The repository responsible for the `Measurement`s. It is also used to initiate the import of measurements.
- `ChannelRepository`: Responsible for storing and retrieving `Channel`s.
- `ChannelDataRepository`: Responsible for storing and retrieving `ChannelData`.

### Service Classes:
- `ChannelGenerator`: Used for debugging purposes to generate synthetic signals which can be added to `Measurement`s.
- `MeasurementImporter`: The service responsible for importing a measurement from an MDF Signal logging file. It splits the measurement in chunks and uses the `ChunkImporter` for the actual import.
- `ChannelProcessor`: Responsible for processing channels, such as resampling to a defined sampling rate.
- `ChunkImporter`: Responsible for the import of measurement chunks.

## Comparison Subsystem
This section gives a brief overview of the comparison subsystem which is located in the `./comparison` folder. This subsystem as well is split in three types of classes: data, service, and repository classes.
![](./figures/Comparison%20Subsystem.png) This figure shows a graphical representation of the system. Small boxes indicate data classes, while large boxes represent services and repositories. In general, the `Comparison` holds all configuration for a comparison, which the `ComparisonExecutor` and `MultiComparisonExecutor` use to determine how to perform a comparison.
The `SyncProcessor` is used to determine `SyncBlocks` from reference points chosen by the user.
The `MetricRegistry` statically holds all implemented `Metrics`, such that the user can choose one of them and add them to the `Comparison`.
The `ComparisonResult` is then generated from the executors, can be viewed by the user, and saved using the `ComparisonRepository`.

## How to: Add a Metric

A very common extension to the tool might be the addition of a metric to the tool. To do that a new class extending the `Metric` class needs to be added.

For that, add the file `my_metric.py` to `./comparison/metrics/` with the content:

```python
from .signal_data import SignalData
from .metric import Metric

class MyMetric(Metric):

    def __call__(self, ref_channel: SignalData, eval_channel: SignalData) -> MetricResult:
        # Here comes the code that defines the metric
        return metric_result_you_calculated

    def __str__(self) -> str:
        return "My Metric" # Name that will be displayed in ComparisonResult
```

Then in the `./comparison/metrics/__init__.py`, add the `from .my_metric import MyMetric` import and the `"MyMetric"` to the `__all__` list. This allows the metric to be used outside of the comparison subsystem.

Finally, add the metric to the registry such that it can be used from the GUI. Therefore in the file `./comparison/metrics/metric_registry.py`, add:
```python
class MetricRegistry(QObject):
    def __init__(self):
        self.metrics = {
            ...
            "My Metric": MyMetric()
        }
```

With these steps, the newly implemented metric will be usable in the tool.