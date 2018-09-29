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
from homeassistant.helpers.event import track_time_interval

REQUIREMENTS = ['tesla_api==1.0.5']

DATA_MANAGER = 'data_manager'
DOMAIN = 'tesla'
PLATFORM_ID = 'tesla_{}'
VEHICLE_UPDATED = 'tesla_vehicle_updated'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=300): vol.All(
            cv.positive_int, vol.Clamp(min=300), cv.time_period)
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
    scan_interval = config.get(CONF_SCAN_INTERVAL)

    api_client = TeslaApiClient(email, password)

    try:
        vehicles = api_client.list_vehicles()
        data_manager = TeslaDataManager(hass, vehicles, scan_interval)

        hass.data[DOMAIN] = {
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
        discovery.load_platform(hass, platform, DOMAIN)

    return True

class TeslaDataManager:
    def __init__(self, hass, vehicles, scan_interval):
        self._hass = hass
        self._vehicles = vehicles
        self._data = {}

        for vehicle in vehicles:
            self._data[vehicle.vin] = {}

        self._update()
        track_time_interval(hass, self._update, scan_interval)

    def _update(self):
        for vehicle in self._vehicles:
            self.update_vehicle(vehicle)

    def update_vehicle(self, vehicle):
        from tesla_api import ApiError

        try:
            vehicle.wake_up()
            #self.update_charge(vehicle, False)
            self.update_climate(vehicle, False)
            #self.update_drive(vehicle, False)
            self.update_gui(vehicle, False)
            #self.update_state(vehicle, False)
            
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

            _LOGGER.debug('Updated data for {}'.format(vehicle.vin))
        except ApiError:
            self.update_vehicle(vehicle)
    
    def update_charge(self, vehicle, fire_event=True):
        from tesla_api import ApiError

        try:
            self._data[vehicle.vin]['charge'] = vehicle.charge.get_state()
        except ApiError:
            self.update_charge(vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

    def update_climate(self, vehicle, fire_event=True):
        from tesla_api import ApiError
        
        try:
            self._data[vehicle.vin]['climate'] = vehicle.climate.get_state()
        except ApiError:
            self.update_climate(vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

    def update_drive(self, vehicle, fire_event=True):
        from tesla_api import ApiError

        try:
            self._data[vehicle.vin]['drive'] = vehicle.get_drive_state()
        except ApiError:
            self.update_drive(vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

    def update_gui(self, vehicle, fire_event=True):
        from tesla_api import ApiError

        try:
            self._data[vehicle.vin]['gui'] = vehicle.get_gui_settings()
        except ApiError:
            self.update_gui(vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

    def update_state(self, vehicle, fire_event=True):
        from tesla_api import ApiError
        
        try:
            self._data[vehicle.vin]['state'] = vehicle.get_state()
        except ApiError:
            self.update_state(vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {'vin': vehicle.vin})

    @property
    def data(self):
        return self._data

    @property
    def vehicles(self):
        return self._vehicles