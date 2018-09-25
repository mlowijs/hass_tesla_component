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

REQUIREMENTS = ['tesla_api==1.0.4']

DOMAIN = 'tesla'

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Optional(CONF_SCAN_INTERVAL, default=300):
            vol.All(cv.positive_int, vol.Clamp(min=300)),
    }),
}, extra=vol.ALLOW_EXTRA)

TESLA_COMPONENTS = [
    # 'climate'
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

        hass.data[DOMAIN] = {
            'vehicles': vehicles
        }

        _LOGGER.debug('Connected to the Tesla API, found {} vehicles.'.format(len(vehicles)))
    except AuthenticationError as ex:            
        _LOGGER.error(ex.message)
        return False
    except ApiError as ex:
        _LOGGER.error(ex.message)
        return False

    for component in TESLA_COMPONENTS:
        discovery.load_platform(hass, component, DOMAIN, hass_config=config)

    return True