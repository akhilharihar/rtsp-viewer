__all__ = ["PACKAGE_DIR", "Gst", "GLib", "WSDL_DIR", "SERVICE_MAPPING"]

import pathlib
import gi
gi.require_version("Gst", "1.0")
gi.require_version("GLib", "2.0")
from gi.repository import Gst, GLib

PACKAGE_DIR = pathlib.PurePath(__file__).parent

WSDL_DIR = PACKAGE_DIR / "wsdl"

# TODO: Add mappings for Analytics,Imaging, PTZ
SERVICE_MAPPING = {
    "device": {
        "ns": "http://www.onvif.org/ver10/device/wsdl",
        "binding": "DeviceBinding",
        "wsdl": WSDL_DIR / "devicemgmt.wsdl"
    },
    "events": {
        "ns": "http://www.onvif.org/ver10/events/wsdl",
        "binding": "EventBinding",
        "wsdl": WSDL_DIR / "events.wsdl"
    },
    "media": {
        "ns": "http://www.onvif.org/ver10/media/wsdl",
        "binding": "MediaBinding",
        "wsdl": WSDL_DIR / "media.wsdl"
    },
    "pullpoint": {
        "ns": "http://www.onvif.org/ver10/events/wsdl",
        "binding": "PullPointSubscriptionBinding",
        "wsdl": WSDL_DIR / "events.wsdl"
    },
    "subscription" : {
        "ns": "http://www.onvif.org/ver10/events/wsdl",
        "binding": "SubscriptionManagerBinding",
        "wsdl": WSDL_DIR / "events.wsdl"
    }
}