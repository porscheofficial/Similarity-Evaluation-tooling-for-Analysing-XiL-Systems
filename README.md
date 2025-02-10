# Similarity-Evaluation-tooling-for-Analysing-XiL-Systems
Similarity Evaluation tooling for Analysing XiL Systems

The Similarity-Evaluation-tooling-for-Analysing-XiL-Systems is a tooling that enables the comparison of MDF Signal-Logging measurements (.mf4). It supports preprocessing, synchronizing and comparing measurements, using various signal-similarity metrics.

## Contents
- Usage of the Tool (This README)
    - [Getting Started](#getting-started)
    - [Measurement Import](#measurement-import)
    - [Measurement Info](#measurement-info)
    - [Compare Measurements](#compare-measurements)
- [Developer Guide](./documentation/Developer%20Guide.md)

## Getting Started
The tool is developed using **python 3.11**, therefore python first needs to be installed. Furthermore, the tool relies on a set of python libraries specified [here](./requirements.txt).
To install all required packages, you can directly install them from the file by running:
```console
pip install -r ./requirements.txt
```
With python and the requirements installed, you can start the program using
```python
python main.py
```
> Note: The program might take a while to start, which is due to the initialization of the GUI library.

## Measurement Import
An MDF Signal logging (.mf4) measurement can be imported to the program by clicking `File > Import` in the menu bar. Select the file you want to import and press `Open`. A popup gives you options to filter constant signals, and signals with the same name. Furthermore, in the popup you can select the sampling rate at which all signals of the measurement should be resampled. A name mapping file can be selected as well, which can be used to rename signals while importing them, you can find more information about name mapping [here](./documentation/Name%20Mapping%20Guide.md). By clicking `Import` the measurement is imported, and appears in the `Measurements` list on the left as soon as the import is done.
> Note: Depending on the size of the measurement, import can take a while. The program has no visual indication of the progress, and only through the console, a progress can be identified.

> Note: It is not possible to import two measurements at the same time.

> Note: Only measurements with the same sampling rate can be compared to each other. Therefore it is useful to choose the same sampling rate for all imports.

## Measurement Info
To obtain information about an imported measurement, edit it, or compare it to another measurement, you can open a measurement by double-clicking on its name in the `Measurements` list.

### Overview
The measurement is opened as a tab on the right. In the tab general information about the measurement, such as length, number of signals, and sampling rate is shown. In the list, all contained signals are displayed, whose details can be viewed by double clicking on an item. To search for a signal, the Filter field can be used. If the signal names follow the scheme `.*::.*::<name>_XIX_<pdu>_XIX_<bus>`, only the name is displayed in the list, and the full name as well as pdu and bus, can be retrieved from the detailed view. Otherwise, the full name is shown in the list.

In the detailed signal view, a graphical representation of the signal can be found. If the signal contains a few discrete values, the import tries to assign a meaning to each value, which is displayed as well. If the MDF file however did not assign a meaning to each value, this field is omitted. By clicking `Show Description` a description for the signal is retrieved from the kmatrix if possible. [Here](./documentation/Kmatrix%20Guide.md) you can get more information about the kmatrix.

### Edit and Compare
The actions which can be performed on measurements can be found in a horizontal button list at the top of the measurement tab.
Measurements can be renamed and deleted, to keep an overview over all imported measurements. The `Create Mapping` option can be used to create a mapping file as described [here](./documentation/Name%20Mapping%20Guide.md). The `Add Signal` button can be used for debugging, where a new synthetic signal with a specific curve can be added to the measurement.

The `Compare` action initializes the comparison process, and opens a new tab in which the comparison is configured and executed.

## Compare Measurements

A comparison is initialized through the `Compare` action on a measurement. The first step of configuring a comparison is done by selecting the measurement to compare against. In the list, only measurements with equal sampling rates are shown.

> Note: The measurement on which the `Compare` action is triggered, serves as ground truth during the comparison. Non-symmetric metrics, will yield different results, depending on which measurement was selected as ground truth.

The comparison is separated in two stages: `Configure Comparison`, where the comparison is configured, synchronization and metric selection is performed, and `View Results`, where the metric results for each signal pair, and aggregated through the measurements can be viewed. From the latter, you can always go back to the former stage, by using the `back` button.

### Configure Comparison

The configure comparison stage allows you to perform four actions, select metric, synchronize, start comparison, and compare with multiple metrics.

- **Select Metric:** The metric used for the comparison is selected through the `Select Metric` dropdown. A set of metric is natively supported by the tool. [Here](./documentation/Developer%20Guide.md) you can see how an additional metric can be added to the tool.
- **Synchronize:** The measurements are synchronized according to reference values. Double click on a signal, to view the signal pair from both measurements. In blue, the signal from the ground truth measurement is shown, in orange the other. By choosing reference values for each measurement (upper field for ground truth, lower field for other measurement) and pressing `Synchronize`, the beginning of the synchronized measurement is set to the first time in the measurement, where the reference values are reached. Multiple synchronization frames can be selected by repeating the process. 
![Functionality of multiple synchronization frames](./documentation/figures/Frame%20Sync%20Method.png)
This figure shows how synchronization works, when several reference values are chosen for a HIL (Ground truth) and a SIL signal. Synchronization can also be configured across several signals, by choosing reference values there. The solid and dashed lines indicate each synchronization frame. By pressing `Reset Synchronization`, all frames are deleted, and synchronization can be configured again
> Note: Synchronization is always until the end of the measurement, there is no functionality to crop the end of a measurement.

> Note: If no synchronization is selected, the measurements are compared from the beginning to the end of the _shorter_ measurement.
- **Start Comparison**: By clicking `Start Comparison`, the selected metric and synchronization is applied to compare the measurements. Does not work if no metric is selected.
- **Compare with multiple metrics:** By clicking `Start Multiple`, the program lets you select multiple metrics to compare the measurements with. The selected metric from the dropdown becomes irrelevant, but the synchronization is applied for all metrics. Since for each comparison a new process is started, choosing to compare measurements with multiple metrics at once speeds up the comparison, compared to performing it with each metric individually.

> Note: Depending on the metric and the size of the measurement, execution might take a while. Check progress in the console.
### View Results

As soon as the comparison is done, the result is shown.
For each pair of signals, the similarity score between 0 and 1 is shown averaged over time of the measurement. A color code shows whether the value is closer to 1 or to 0. 
By double-clicking the signal, the detailed similarity score as well as the signals can be viewed. Additionally, metadata exposed by each metric can be displayed optionally.

On the bottom the averaged score over all signals can be viewed, and by pressing `Plot`, the averaged score can be viewed over time. By clicking `Save`, the result is saved using a chosen name, and can be viewed again at a later time. To view the comparison again, double-click it in the `Comparisons` tab on the left.

> Note: If the measurements upon which the comparison was executed are deleted, the results cannot be viewed anymore.
