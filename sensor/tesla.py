"""
Support for various Tesla sensors.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.tesla/
"""
import logging

from custom_components.tesla import (
    DATA_MANAGER, DOMAIN, PLATFORM_ID, TeslaDevice, VEHICLE_UPDATED)
from homeassistant.const import (DEVICE_CLASS_BATTERY, LENGTH_KILOMETERS)
from homeassistant.helpers.entity import Entity

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]
SENSOR_ID = PLATFORM_ID + '_{}'

def setup_platform(hass, config, add_entities, discovery_info):
    """Set up the Tesla climate platform."""
    tesla_data = hass.data[DOMAIN]
    data_manager = tesla_data[DATA_MANAGER]

    all_sensors = []

    # Battery sensors
    battery_level_getter = lambda data: data['charge']['battery_level']
    all_sensors.extend([TeslaSensorDevice(hass, data_manager, vehicle, 'soc',
                                          '%', DEVICE_CLASS_BATTERY,
                                          battery_level_getter)
                        for vehicle in tesla_data[DATA_MANAGER].vehicles])

    # Range sensors
    range_getter = lambda data: round(data['charge']['battery_range'])
    all_sensors.extend([TeslaSensorDevice(hass, data_manager, vehicle, 'range',
                                          LENGTH_KILOMETERS, None,
                                          range_getter)
                        for vehicle in tesla_data[DATA_MANAGER].vehicles])

    add_entities(all_sensors, True)

class TeslaSensorDevice(TeslaDevice, Entity):
    def __init__(self, hass, data_manager, vehicle, measured_value,
                 unit_of_measurement, device_class, state_getter):
        super().__init__(hass, data_manager, vehicle)

        self._measured_value = measured_value
        self._device_class = device_class
        self._state_getter = state_getter
        self._unit_of_measurement = unit_of_measurement

        _LOGGER.debug('Created ''{}'' sensor device for {}.'.format(
            measured_value, vehicle.vin))

    @property
    def name(self):
        return SENSOR_ID.format(self._vehicle.vin, self._measured_value)

    @property
    def device_class(self):
        return self._device_class

    @property
    def state(self):
        return self._state_getter(self._data)

    @property
    def unit_of_measurement(self):
        return self._unit_of_measurement