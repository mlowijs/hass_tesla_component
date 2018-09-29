"""
Support for various Tesla switches.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.tesla/
"""
import logging

from custom_components.tesla import (
    DATA_MANAGER, DOMAIN, PLATFORM_ID, TeslaDevice)
from homeassistant.const import (DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_TEMPERATURE, LENGTH_KILOMETERS, LENGTH_MILES, TEMP_CELSIUS,
    TEMP_FAHRENHEIT)
from homeassistant.components.switch import SwitchDevice

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]
SWITCH_ID = PLATFORM_ID + '_{}'

def setup_platform(hass, config, add_entities, discovery_info):
    """Set up the Tesla sensor platform."""
    tesla_data = hass.data[DOMAIN]
    data_manager = tesla_data[DATA_MANAGER]

    all_switches = [TeslaChargingSwitch(hass, data_manager, vehicle)
                    for vehicle in data_manager.vehicles]

    add_entities(all_switches, True)

class TeslaChargingSwitch(TeslaDevice, SwitchDevice):
    def __init__(self, hass, data_manager, vehicle):
        super().__init__(hass, data_manager, vehicle)

        _LOGGER.debug('Created charging switch device for {}.'.format(
            vehicle.vin))

    def turn_on(self):
        from tesla_api import ApiError

        try:
            self._vehicle.wake_up()
            self._vehicle.charge.start_charging()
            self._data_manager.update_charge(self._vehicle)

            _LOGGER.debug('Turned charging switch on for {}.'.format(
                self._vehicle.vin))
        except ApiError:
            self.turn_on()

    def turn_off(self):
        from tesla_api import ApiError

        try:
            self._vehicle.wake_up()
            self._vehicle.charge.stop_charging()
            self._data_manager.update_charge(self._vehicle)

            _LOGGER.debug('Turned charging switch off for {}.'.format(
                self._vehicle.vin))
        except ApiError:
            self.turn_off()

    @property
    def should_poll(self):
        return False

    @property
    def is_on(self):
        return self._data['charge']['charging_state'] != 'Stopped'

    @property
    def name(self):
        return SWITCH_ID.format(self._vehicle.vin, 'charging')