"""
Support for various Tesla sensors.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.tesla/
"""
import logging

from custom_components.tesla import (
    DATA_MANAGER, DOMAIN, PLATFORM_ID, TeslaDevice, VEHICLE_UPDATED)
from homeassistant.const import (DEVICE_CLASS_BATTERY, LENGTH_KILOMETERS,
    LENGTH_MILES)
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
    all_sensors.extend([TeslaBatterySensorDevice(hass, data_manager, vehicle)
                        for vehicle in tesla_data[DATA_MANAGER].vehicles])

    # Range sensors
    all_sensors.extend([TeslaRangeSensorDevice(hass, data_manager, vehicle)
                        for vehicle in tesla_data[DATA_MANAGER].vehicles])

    add_entities(all_sensors, True)

class TeslaSensorDevice(TeslaDevice, Entity):
    def __init__(self, hass, data_manager, vehicle, measured_value):
        super().__init__(hass, data_manager, vehicle)

        self._measured_value = measured_value

        _LOGGER.debug('Created ''{}'' sensor device for {}.'.format(
            measured_value, vehicle.vin))

    @property
    def name(self):
        return SENSOR_ID.format(self._vehicle.vin, self._measured_value)

class TeslaBatterySensorDevice(TeslaSensorDevice):
    def __init__(self, hass, data_manager, vehicle):
        super().__init__(hass, data_manager, vehicle, 'soc')

    @property
    def state(self):
        return self._data['charge']['battery_level']

    @property
    def unit_of_measurement(self):
        return '%'

    @property
    def device_class(self):
        return DEVICE_CLASS_BATTERY

class TeslaRangeSensorDevice(TeslaSensorDevice):
    def __init__(self, hass, data_manager, vehicle):
        super().__init__(hass, data_manager, vehicle, 'range')

    @property
    def state(self):
        return round(self._data['charge']['battery_range'])

    @property
    def unit_of_measurement(self):
        return LENGTH_KILOMETERS if self._data['gui']['gui_distance_units'] == 'km/hr' else LENGTH_MILES