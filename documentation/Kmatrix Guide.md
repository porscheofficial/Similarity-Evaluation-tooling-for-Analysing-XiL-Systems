# kmatrix

The kmatrix is used in the tool, to retrieve the descriptions for the signals. It is not natively part of the tool and needs to be added manually. 

> Note: The tool works without kmatrix, but no descriptions for signals will be viewable.

The tool expects the description file to be located at `./kmatrix/kmatrix.csv`. This .csv file should consist of three columns `Signal`, `Bus`, and `Description`.
The `Signal` column contains the short name of the signal, for which the description is given. The `Bus` defines on which bus the signal was captured, to potentially give different descriptions for the same signal on different busses. The `Description` then defines the description.
> Note: The .csv is semi-colon separated, therefore no semi-colons should be contained in the descriptions. Use parentheses to make multi-line descriptions possible. 