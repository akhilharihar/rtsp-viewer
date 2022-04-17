# adapted from https://github.com/elsampsa/valkka-core/blob/master/python/valkka/onvif/base.py
# For renewal and unsubscribe to work, you'll need to patch wsdl/bindings/soap.py in zeep package
# reference https://github.com/mvantellingen/python-zeep/pull/1206/files

__all__ = ["Camera"]

from .globals import SERVICE_MAPPING 
from zeep.wsse.username import UsernameToken
from zeep import Settings, Client
from pathlib import PurePath
from urllib.parse import urlparse

ZEEP_SETTINGS = Settings()


class Service:
    def __init__(self, namespace:str, binding:str, wsdl_file_path:PurePath, xaddr: str, wsse:UsernameToken) -> None:
        self.zeep_client = Client(wsdl=str(wsdl_file_path), wsse=wsse, settings=ZEEP_SETTINGS)
        self.ws_client = self.zeep_client.create_service(f"{{{namespace}}}{binding}", xaddr)
    
    def __getattr__(self, name):
        def wrapper(*args, **kwargs):
            try:
                func = getattr(self.ws_client, name)
                return func(*args, **kwargs)
            except Exception as e:
                raise e
        return wrapper
             

class Camera:
    def __init__(self, usr:str, pwd: str, ip_addr: str, port: int = 80) -> None:
        self.wsse = UsernameToken(usr, pwd, use_digest=True)
        self.DEVICE_XADDR = f"http://{ip_addr}:{port}/onvif/device_service"
        self.__services = {}
        self.configure_default_services()
        self.pullpoint_details = None
    
    def configure_default_services(self) -> None:
        device_srv = Service(
            SERVICE_MAPPING["device"]["ns"],
            SERVICE_MAPPING["device"]["binding"],
            SERVICE_MAPPING["device"]["wsdl"],
            self.DEVICE_XADDR,
            self.wsse
        )

        device_srv = self.create_service("device", device_srv)

        result = device_srv.GetCapabilities()

        # TODO: Create wsdl services for Analytics,Imaging, PTZ 
        for xyz in ['Events','Media']:
            addr = result[xyz]["XAddr"]
            self.create_service(xyz.lower(), Service(
                SERVICE_MAPPING[xyz.lower()]["ns"],
                SERVICE_MAPPING[xyz.lower()]["binding"],
                SERVICE_MAPPING[xyz.lower()]["wsdl"],
                addr,
                self.wsse
            ))


    def create_service(self, name:str, srv_obj:Service=None) -> Service:
        if srv_obj:
            srv = srv_obj
            self.__services[name] = srv
        elif name in self.__services:
            srv = self.__services[name]
        else:
            raise NotImplementedError("Specified service is not implemented. Please pass srv_obj")
        return srv
    

    def setup_pullpoint_subscription(self, TerminationTime="PT1M", **kwargs):
        events = self.create_service("events")
        result = events.CreatePullPointSubscription(InitialTerminationTime=TerminationTime, **kwargs)
        addr = result.SubscriptionReference["Address"]["_value_1"]
        self.pullpoint_details = result
        self.create_service("pullpoint", Service(
            SERVICE_MAPPING["pullpoint"]["ns"],
            SERVICE_MAPPING["pullpoint"]["binding"],
            SERVICE_MAPPING["pullpoint"]["wsdl"],
            addr, self.wsse))
        self.create_service("subscription", Service(
            SERVICE_MAPPING["subscription"]["ns"],
            SERVICE_MAPPING["subscription"]["binding"],
            SERVICE_MAPPING["subscription"]["wsdl"],
            addr, self.wsse
        ))
    
    def pullpoint_cleanup(self):
        if "subscription" in self.__services:
            print("cleaning up subscription")
            self.__services["subscription"].Unsubscribe()
            print("cleaned up subscription")

    
    def stream_url(self, high_quality=True):
        media = self.create_service("media")
        profiles = media.GetProfiles()

        streamsetup = {
            "Stream": "RTP-Multicast",
            "Transport": {
                "Protocol": "TCP"
            }
        }

        token_num = 0

        if len(profiles) > 1:
            token_num = 0 if high_quality else 1

        token = profiles[token_num].token
        stream_point = media.GetStreamUri(StreamSetup=streamsetup, ProfileToken=token)
        unauthurl = urlparse(stream_point.Uri)
        return unauthurl._replace(netloc=f"{self.wsse.username}:{self.wsse.password}@{unauthurl.netloc}").geturl()
