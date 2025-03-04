import json
from logging import getLogger
import os
from typing import Self
from measurement.channel.channel_data_repository import ChannelDataRepository
from measurement.channel.channel_repository import ChannelRepository

from .measurement import Measurement
from .measurement_import import MeasurementImportInfo, MeasurementImporter

from PySide6.QtCore import QObject, Signal, QThread, Slot, QMetaType
import PySide6.QtCore as core


class MeasurementRegistry(QObject):
    """
    MeasurementRegistry class manages the registry of measurements.
    Attributes:
        initialized (bool): Indicates whether the MeasurementRegistry has been initialized.
        measurements_updated (Signal): Signal emitted when measurements are updated.
        measurements (list[Measurement]): List of measurements.
    Methods:
        _load(self) -> list[LazyMeasurement]: Loads measurements from files.
        load_measurement(self, filename: str) -> None: Loads a measurement from a file.
        import_file(self, info: MeasurementImportInfo) -> None: Imports a measurement file.
        handle_measurement_imported(self, measurement: Measurement) -> None: Handles the imported measurement.
        get_measurement(self, id: str) -> Measurement: Retrieves a measurement by its ID.
    """

    initialized = False
    measurements_updated = Signal()

    measurements: list[Measurement]
    measurement_importer: MeasurementImporter

    def __new__(cls) -> Self:
        if not hasattr(cls, 'instance'):
            cls.instance = super(MeasurementRegistry, cls).__new__(cls)
        return cls.instance

    def __init__(self) -> None:
        if not self.initialized:
            super().__init__()
            self.initialized = True
            self.measurement_importer = None
            self.importer_thread = QThread()

            self.imported_files_location = os.getcwd() + "/measurements/measurements"
            self.measurements: list[Measurement] = []
            self._load()
            self.logger = getLogger(__name__)

    def _load(self):
        if not os.path.exists(self.imported_files_location):
            self.logger.info(
                f"Imported Files Location ({self.imported_files_location}) does not exist yet. Creating it now")
            os.makedirs(self.imported_files_location)

        for _, _, files in os.walk(self.imported_files_location):
            for filename in files:
                if not filename.endswith(".json"):
                    self.logger.warning(
                        f"Found {filename}, which is not a valid measurement file")
                    continue
                self.load_measurement(os.path.join(
                    self.imported_files_location, filename))

    def load_measurement(self, filename: str) -> None:
        """
        Loads a measurement from a file. This function is mainly used by the measurement registry to load all measurements from the measurements folder. The measurement needs to be in JSON format.
        Use with care, and note that the measurement will not be loaded automatically at the next start of the application.
        Args:
            filename (str): The path to the measurement file.
        Note:
            The measurement file needs to be in JSON format.
            Does not return the measurement, but adds it to the measurements list.
        """
        file = json.load(open(filename, "r"))
        measurement = Measurement.from_dict(file)

        self.measurements.append(measurement)
        self.measurements_updated.emit()

    def save_measurement(self, measurement: Measurement) -> None:
        """
        Saves a measurement to a JSON file in the imported files location.
        Previously saved measurements will be overwritten.
        Args:
            measurement (Measurement): The measurement object to be saved.
        Emits:
            measurements_updated: Signal emitted after successful save operation.
        Note:
            The measurement should be contained in the registry, to make sure the measurements_updated signal is used correctly.
        """

        filename = f"{self.imported_files_location}/{measurement.id}.json"
        with open(filename, "w") as file:
            json.dump(measurement.to_dict(), file, indent=4)

        self.measurements_updated.emit()

    def import_file(self, info: MeasurementImportInfo) -> None:
        """
        Import a measurement file using a separate thread.
        This method initiates the import process for a measurement file. It creates a
        MeasurementImporter instance and moves it to a dedicated thread to prevent blocking
        the main thread during import.
        Args:
            info (MeasurementImportInfo): Contains the information needed for importing the
                measurement file, including the filename and other import parameters.
        Notes:
            - If an import is already running, the method will log a warning and return without
              starting another import
            - The import process is asynchronous and the results are handled through the
              handle_measurement_imported slot when complete
            - Does **not** return the measurement object, but emits the measurements_updated signal
        """

        self.logger.info(f"Importing file {info.filename}")

        if self.importer_thread.isRunning():
            self.logger.warning(
                "Importer thread is still running. Wait for it to finish before importing another file")
            return
        self.measurement_importer = MeasurementImporter(info)
        self.measurement_importer.moveToThread(self.importer_thread)
        self.measurement_importer.measurementImported.connect(
            self.handle_measurement_imported)
        self.importer_thread.start()

        core.QMetaObject.invokeMethod(
            self.measurement_importer,
            "import_measurement",
            core.Qt.QueuedConnection)

    @Slot(Measurement)
    def handle_measurement_imported(self, measurement: Measurement) -> None:
        """Not for external use. Handles the imported measurement and saves it to the registry."""
        self.measurements.append(measurement)
        self.measurements_updated.emit()
        if self.importer_thread.isRunning():
            self.importer_thread.quit()
            self.measurement_importer.deleteLater()

        self.measurement_importer = None

        self.save_measurement(measurement)

    def add_measurement(self, measurement: Measurement) -> None:
        """
        Adds a measurement to the registry. The measurement will be saved to a JSON file in the imported files location.
        Useful for adding synthetic measurements or measurements that are not loaded from files.
        Args:
            measurement (Measurement): The measurement object to be added.
        Emits:
            measurements_updated: Signal emitted after successful addition.
        """
        if self.has(measurement.id):
            self.logger.warning(
                f"Measurement with id:{measurement.id} already exists, overwriting it")
            self.measurements.remove(self.get(measurement.id))

        self.measurements.append(measurement)
        self.measurements_updated.emit()
        self.save_measurement(measurement)

    def get(self, id: str) -> Measurement:
        for measurement in self.measurements:
            if measurement.id == id:
                return measurement
        raise ValueError(f"Measurement with id:{id} does not exist")

    def get_by_name(self, name: str) -> Measurement:
        for measurement in self.measurements:
            if measurement.name == name:
                return measurement
        raise ValueError(f"Measurement with name:{name} does not exist")

    def has(self, id: str) -> bool:
        for measurement in self.measurements:
            if measurement.id == id:
                return True
        return False

    def has_by_name(self, name: str) -> bool:
        for measurement in self.measurements:
            if measurement.name == name:
                return True
        return False

    def delete(self, id: str) -> None:
        for measurement in self.measurements:
            if measurement.id == id:
                repo = ChannelRepository()
                data_repo = ChannelDataRepository()
                channels = map(lambda x: x.id, measurement.channels)
                channels = set(map(repo.parse_group_id, channels))
                for channel in channels:
                    repo.delete_group(channel)
                    data_repo.delete_group(channel)

                self.measurements.remove(measurement)
                os.remove(f"{self.imported_files_location}/{id}.json")
                self.measurements_updated.emit()
                return
        raise ValueError(f"Measurement with id:{id} does not exist")
