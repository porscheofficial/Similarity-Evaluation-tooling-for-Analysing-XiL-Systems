# Name Mapping
If two measurements contain different names for the same signal, these measurements can only be compared by renaming the names to be equal.
For renaming, a name mapping file can be selected during the import process, this file is required to be a comma separated .csv file with two columns: `Channel`, `Mapped Channel`. During import, whenever a signal with a name contained in `Channel` is found, it is renamed to the corresponding `Mapped Channel`. 

> Note: The name mapping file can also be used to filter signals. If it is selected, only signals with names contained in the file are imported, all other signals are filtered out.

To create the file, you have two options: Manual creation, and the `Create Mapping` option in a measurement. For manual creation, you can just create a .csv file with the names as described above. The `Create Mapping` action on measurements, allows you to create a mapping for one measurement to names of another.
First you select the measurement whose signal names you want to map, and click `Create Mapping`. In the popup you select a measurement which already contains the names to which you want to map. The popup now iterates through all signals of the first selected measurement, allowing you to search for a corresponding signal in the other measurement, to which the first signal should be renamed. Double-Click the signal to select it, and press `Use Selected Channel` to move on to the next signal. If no matching signal can be found, press `Skip Channel`.

As soon as all signals are matched, the mapping is saved at `./channel_mapping_<current time>.csv`, and the window can be closed.