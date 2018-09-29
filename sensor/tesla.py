"""
Support for various Tesla sensors.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.tesla/
"""
import logging

from custom_components.tesla import (
    DATA_MANAGER, DOMAIN, PLATFORM_ID, TeslaDevice, VEHICLE_UPDATED)
from homeassistant.components.sensor import (
    SensorDevice)
from homeassistant.helpers.entity import Entity


_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

def setup_platform(hass, config, add_entities, discovery_info):
    """Set up the Tesla climate platform."""
    tesla_data = hass.data[DOMAIN]

class TeslaSensorDevice(TeslaDevice, Entity):
    def __init__(self):
        pass