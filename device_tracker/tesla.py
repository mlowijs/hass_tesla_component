"""
Support for Tesla location tracking.
For more details about this platform, please refer to the documentation
https://home-assistant.io/components/climate.tesla/
"""
import logging

from custom_components.tesla import (
    DATA_MANAGER, DOMAIN, PLATFORM_ID, TeslaDevice)

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [DOMAIN]

def setup_scanner(hass, config, see, discovery_info=None):
    tesla_data = hass.data[DOMAIN]
    data_manager = tesla_data[DATA_MANAGER]