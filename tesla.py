"""
Support for Tesla cars.

For more details about this component, please refer to the documentation at
https://home-assistant.io/components/tesla/
"""
import logging
from datetime import timedelta
import voluptuous as vol

from homeassistant.const import (
    CONF_PASSWORD, CONF_SCAN_INTERVAL, CONF_USERNAME)
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import discovery
from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import (
    track_point_in_utc_time, track_time_interval)
from homeassistant.util import dt as dt_util

REQUIREMENTS = ['tesla_api==1.0.7']

ATTR_VIN = 'vin'
DATA_MANAGER = 'data_manager'
DOMAIN = 'tesla'
PLATFORM_ID = DOMAIN + '_{}'
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

SERVICE_SCHEMA = vol.Schema({
    vol.Required(ATTR_VIN): cv.string,
})

TESLA_PLATFORMS = ['climate', 'device_tracker', 'sensor', 'switch']

CONTROLS_SERVICES = ['flash_lights', 'honk_horn']

def setup(hass, base_config):
    """Set up of Tesla component."""
    from tesla_api import TeslaApiClient, AuthenticationError, ApiError

    config = base_config.get(DOMAIN)

    email = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    scan_interval = config.get(CONF_SCAN_INTERVAL)

    api_client = TeslaApiClient(email, password)

    try:
        _LOGGER.info('Initializing Tesla data manager')
        vehicles = api_client.list_vehicles()
        data_manager = TeslaDataManager(hass, vehicles, scan_interval)

        hass.data[DOMAIN] = {
            DATA_MANAGER: data_manager
        }

        _LOGGER.info('Tesla data manager intialized')
        _LOGGER.debug('Connected to the Tesla API, found %d vehicles.', len(vehicles))
    except AuthenticationError as ex:            
        _LOGGER.error(ex.message)
        return False
    except ApiError as ex:
        _LOGGER.error(ex.message)
        return False

    def execute_controls_service(call):
        vin = call.data.get(ATTR_VIN)
        vehicle = data_manager.get_vehicle(vin)

        if not vehicle:
            _LOGGER.error('No vehicle found with VIN %s', vin)
            return

        func = getattr(vehicle.controls, call.service)

        vehicle.wake_up()
        func()

    for service in CONTROLS_SERVICES:
        hass.services.register(DOMAIN, service, execute_controls_service,
            schema=SERVICE_SCHEMA)

    for platform in TESLA_PLATFORMS:
        discovery.load_platform(hass, platform, DOMAIN)

    return True

class TeslaDevice(Entity):
    def __init__(self, hass, data_manager, vehicle):
        self._data_manager = data_manager
        self._vehicle = vehicle
        self._data = None

        hass.bus.listen(VEHICLE_UPDATED, self._vehicle_updated)

    def _vehicle_updated(self, event):
        if event.data.get(ATTR_VIN) != self._vehicle.vin:
            return

        self.update()

        try:
            self.schedule_update_ha_state()
        except:
            pass

    def update(self):
        self._data = self._data_manager.data[self._vehicle.vin]

    def _schedule_update(self, update_action):
        track_point_in_utc_time(self.hass,
            lambda now: update_action(self._vehicle, True),
            dt_util.utcnow() + timedelta(seconds=5))

def update_wrapper(func):
    def wrapper(self, vehicle, fire_event):
        from tesla_api import ApiError

        try:
            func(self, vehicle, fire_event)
        except ApiError:
            wrapper(self, vehicle, fire_event)
            return

        if fire_event:
            self._hass.bus.fire(VEHICLE_UPDATED, {ATTR_VIN: vehicle.vin})

    return wrapper

"""TeslaDataManager will make sure we do not call the Tesla API too often."""
class TeslaDataManager:
    def __init__(self, hass, vehicles, scan_interval):
        self._hass = hass
        self._vehicles = vehicles
        self._data = {}

        for vehicle in vehicles:
            self._data[vehicle.vin] = {}

        self._update()
        track_time_interval(hass, lambda now: self._update(), scan_interval)

    def _update(self):
        for vehicle in self._vehicles:
            self.update_vehicle(vehicle)

    def update_vehicle(self, vehicle):
        from tesla_api import ApiError

        try:
            vehicle.wake_up()
            self.update_charge(vehicle, False)
            self.update_climate(vehicle, False)
            self.update_drive(vehicle, False)
            self.update_gui(vehicle, False)
            self.update_state(vehicle, False)
            
            self._hass.bus.fire(VEHICLE_UPDATED, {ATTR_VIN: vehicle.vin})

            _LOGGER.debug('Updated data for %s', vehicle.vin)
        except ApiError:
            self.update_vehicle(vehicle)
    
    @update_wrapper
    def update_charge(self, vehicle, fire_event=True):
        self._data[vehicle.vin]['charge'] = vehicle.charge.get_state()

    @update_wrapper
    def update_climate(self, vehicle, fire_event=True):
        self._data[vehicle.vin]['climate'] = vehicle.climate.get_state()

    @update_wrapper
    def update_drive(self, vehicle, fire_event=True):
        self._data[vehicle.vin]['drive'] = vehicle.get_drive_state()

    @update_wrapper
    def update_gui(self, vehicle, fire_event=True):
        self._data[vehicle.vin]['gui'] = vehicle.get_gui_settings()

    @update_wrapper
    def update_state(self, vehicle, fire_event=True):
        self._data[vehicle.vin]['state'] = vehicle.get_state()

    def get_vehicle(self, vin):
        return next((v for v in self.vehicles if v.vin == vin), None)

    @property
    def data(self):
        return self._data

    @property
    def vehicles(self):
        return self._vehicles