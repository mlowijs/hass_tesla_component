"""
Support for Tesla cars.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tesla/
"""
import logging

import voluptuous as vol

from homeassistant.const import (
    CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery

REQUIREMENTS = ['tesla_api==1.0.5']

DATA_MANAGER = 'data_manager'
DOMAIN = 'tesla'
PLATFORM_ID = 'tesla_{}'
VEHICLE_UPDATED = 'tesla_vehicle_updated'
VEHICLES = 'vehicles'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=300):
            vol.All(cv.positive_int, vol.Clamp(min=10)),
    }),
}, extra=vol.ALLOW_EXTRA)

TESLA_PLATFORMS = [
    'climate'
]

def setup(hass, base_config):
    """Set up of Tesla component."""
    from tesla_api import TeslaApiClient, AuthenticationError, ApiError

    config = base_config.get(DOMAIN)

    email = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)

    api_client = TeslaApiClient(email, password)

    try:
        vehicles = api_client.list_vehicles()
        data_manager = TeslaDataManager(hass, vehicles)

        hass.data[DOMAIN] = {
            VEHICLES: vehicles,
            DATA_MANAGER: data_manager
        }

        _LOGGER.debug('Connected to the Tesla API, found {} vehicles.'.format(len(vehicles)))
    except AuthenticationError as ex:            
        _LOGGER.error(ex.message)
        return False
    except ApiError as ex:
        _LOGGER.error(ex.message)
        return False

    for platform in TESLA_PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN, discovered={CONF_SCAN_INTERVAL: config.get(CONF_SCAN_INTERVAL)})

    return True

class TeslaDataManager:
    def __init__(self, hass, vehicles):
        self._hass = hass
        self._vehicles = vehicles
        self._data = {}

        self.update()

    def update(self):
        for vehicle in self._vehicles:
            vehicle.wake_up()
            self.update_vehicle(vehicle)

    def update_vehicle(self, vehicle):
        data = {
            'charge': vehicle.charge.get_state(),
            'climate': vehicle.climate.get_state(),
            'drive': vehicle.get_drive_state(),
            'gui': vehicle.get_gui_settings(),
            'vehicle': vehicle.get_state()
        }
        
        self._data[vehicle.vin] = data
        self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

        _LOGGER.debug('Updated data for {}'.format(vehicle.vin))

    @property
    def data(self):
        return self._data
        