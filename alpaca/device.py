from enum import Enum
from threading import Lock
from datetime import datetime
from typing import List, Any
import dateutil.parser
import requests
import random
from alpaca.exceptions import *     # Sorry Python purists

API_VERSION = 1

class Device(object):
    """Common interface members across all ASCOM Alpaca devices."""

    def __init__(
        self,
        address: str,
        device_type: str,
        device_number: int,
        protocol: str
    ):
        """Initialize Device object.
        
        Attributes:
            address: Domain name or IP address of Alpaca server.
                Can also specify port number if needed.
            device_type: One of the recognised ASCOM device types
                e.g. telescope (must be lower case).
            device_number: Zero based device number as set on the server (0 to
                4294967295).
            protocol: Protocol (http vs https) used to communicate with Alpaca server.
            api_version: Alpaca API version.
            base_url: Basic URL to easily append with commands.

        Notes: Sets a random number for ClientID that lasts 

        """
        self.address = address
        self.device_type = device_type
        self.device_number = device_number
        self.api_version = API_VERSION
        self.base_url = "%s://%s/api/v%d/%s/%d" % (
            protocol,       # not needed later
            self.address,
            self.api_version,
            self.device_type,
            self.device_number
        )
    # ------------------------------------------------
    # CLASS VARIABLES - SHARED ACROSS DEVICE INSTANCES
    # ------------------------------------------------
    _client_id = random.randint(0, 65535)
    _client_trans_id = 1
    _ctid_lock = Lock()
    # ------------------------------------------------

    def Action(self, ActionName: str, *Parameters) -> str:
        """Invoke the specified device-specific custom action
        
        Args:
            ActionName: A name from :py:attr:`SupportedActions` that represents 
                the action to be carried out.
            *Parameters: List of required parameters or [] if none are required.

        Returns:
            String result of the action.

        Raises:
            NotImplementedException: If no actions at all are supported
            ActionNotImplementedException: If the driver does not support the requested
                ActionName. The supported action names are listed in 
                :py:attr:`SupportedActions`.
            NotConnectedException: If the device is not connected
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.


        """
        return self._put("action", Action=ActionName, Parameters=Parameters)["Value"]

    def CommandBlind(self, Command: str, Raw: bool) -> None:
        """Transmit an arbitrary string to the device and does not wait for a response.

        Args:
            Command: The literal command string to be transmitted.
            Raw: If true, command is transmitted 'as-is'.
                If false, then protocol framing characters may be added prior to
                transmission.

        Raises:
            NotImplementedException: If no actions at all are supported
            NotConnectedException: If the device is not connected
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.
                
        Attention:
            **Deprecated**, will most likely result in 
            :py:class:`~exceptions.NotImplementedException`


        """
        self._put("commandblind", Command=Command, Raw=Raw)

    def CommandBool(self, Command: str, Raw: bool) -> bool:
        """Transmit an arbitrary string to the device and wait for a boolean response.

        Returns:
            The True/False response from the command

        Args:
            Command: The literal command string to be transmitted.
            Raw: If true, command is transmitted 'as-is'.
                If false, then protocol framing characters may be added prior to
                transmission.

        Raises:
            NotImplementedException: If no actions at all are supported
            NotConnectedException: If the device is not connected
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.
                
        Attention:
            **Deprecated**, will most likely result in 
            :py:class:`~exceptions.NotImplementedException`

        """
        return self._put("commandbool", Command=Command, Raw=Raw)["Value"]

    def CommandString(self, Command: str, Raw: bool) -> str:
        """Transmit an arbitrary string to the device and wait for a string response.

        Returns:
            The string response from the command

        Args:
            Command: The literal command string to be transmitted.
            Raw: If true, command is transmitted 'as-is'.
                If false, then protocol framing characters may be added prior to
                transmission.

        Raises:
            NotImplementedException: If no actions at all are supported
            NotConnectedException: If the device is not connected
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.
                
        Attention:
            **Deprecated**, will most likely result in 
            :py:class:`~exceptions.NotImplementedException`

        """
        return self._put("commandstring", Command=Command, Raw=Raw)["Value"]

    @property
    def Connected(self) -> bool:
        """(Read/Write) Retrieve or set the connected state of the device.

        Set True to connect to the device hardware. Set False to disconnect 
        from the device hardware. You can also read the property to check 
        whether it is connected. This reports the current hardware state.
        See Notes below. 

        Raises:      
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.
        
        Notes:
            * The Connected property sets and reports the state of connection to 
              the device hardware. For a hub this means that Connected will be 
              True when the first driver connects and will only be set to False 
              when all drivers have disconnected. A second driver may find that 
              Connected is already True and setting Connected to False does not 
              report Connected as False. This is not an error because the physical 
              state is that the hardware connection is still True.
            * Multiple calls setting Connected to true or false will not cause 
              an error.
        
        """
        return self._get("connected")
    @Connected.setter
    def Connected(self, ConnectedState: bool):
        self._put("connected", Connected=ConnectedState)
    
    @property
    def Description(self) -> str:
        """Description of the **device** such as manufacturer and model number.

        Raises:
            NotConnectedException: If the device status is unavailable
            DriverException: If the device cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.

        Notes: 
            * This describes the *device*, not the driver. See the :py:attr:`DriverInfo`
              property for information on the ASCOM driver.
            * The description length will be a maximum of 64 characters so 
              that it can be used in FITS image headers, which are limited 
              to 80 characters including the header name.

        """
        return self._get("description")

    @property
    def DriverInfo(self) -> List[str]:
        """Descriptive and version information about the ASCOM **driver**

        Returns:
            Python list of strings (see Notes)
        
        Raises:
            DriverException: If the driver cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.

        Notes: 
            * This describes the *driver* not the device. See the :py:attr:`Description`
              property for information on the device itself
            * The return is a Python list of strings, the total length of which may be
              hundreds to thousands of characters long. It is intended to display 
              detailed information on the ASCOM (COM or Alpaca) driver, including 
              version and copyright data. . To get the driver version in a parse-able 
              string, use the :py:attr:`DriverVersion` property. 
       
        """
        return [i.strip() for i in self._get("driverinfo").split(",")]

    @property
    def DriverVersion(self) -> float:
        """String containing only the major and minor version of the *driver*.
        
        Raises:
            DriverException: If the driver cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.

        Notes:        
            * This must be in the form "n.n". It should not to be confused with the 
              :py:attr:`InterfaceVersion` property, which is the version of this 
              specification supported by the driver. 

        """
        return float(self._get("driverversion"))

    @property
    def InterfaceVersion(self) -> int:
        """ASCOM Device interface definition version that this device supports.
        
        Raises:
            DriverException: If the driver cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.

        Notes:        
            * This is a single integer indicating the version of this specific
              ASCOM universal interface definition. For example, for ICameraV3,
              this will be 3. It should not to be confused with the 
              :py:attr:`DriverVersion` property, which is the major.minor version
              of the driver for  this device. 
        
        """
        return int(self._get("interfaceversion"))
    
    @property
    def Name(self) -> str:
        """The short name of the *driver*, for display  purposes.
        
        Raises:
            DriverException: If the driver cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.
        
        """
        return self._get("name")

    @property
    def SupportedActions(self) -> List[str]:
        """The list of custom action names supported by this driver
        
        Returns:
            Python list of strings (see Notes)

        Raises:
            DriverException: If the driver cannot *successfully* complete the request. 
                This exception may be encountered on any call to the device.

        Notes:
            * This is an aid to client authors and testers who would otherwise have to 
              repeatedly poll the driver to determine its capabilities. Returned :py:meth:`Action()`
              names may be in mixed case to enhance presentation but the :py:meth:`Action(String, String)`
              method is case insensitive.
        
        """
        return self._get("supportedactions")

# ========================
# HTTP/JSON Communications
# ========================

    def _get(self, attribute: str, **data) -> str:
        """Send an HTTP GET request to an Alpaca server and check response for errors.

        Args:
            attribute (str): Attribute to get from server.
            **data: Data to send with request.
        
        """
        url = f"{self.base_url}/{attribute}"
        pdata = {
                "ClientTransactionID": f"{Device._client_trans_id}",
                "ClientID": f"{Device._client_id}" 
                }
        pdata.update(data)
        try:
            Device._ctid_lock.acquire()
            response = requests.get("%s/%s" % (self.base_url, attribute), params = pdata)
            Device._client_trans_id += 1
        finally:
            Device._ctid_lock.release()
        self.__check_error(response)
        return response.json()["Value"]

    def _put(self, attribute: str, **data) -> str:
        """Send an HTTP PUT request to an Alpaca server and check response for errors.

        Args:
            attribute (str): Attribute to put to server.
            **data: Data to send with request.
        
        """
        url = f"{self.base_url}/{attribute}"
        pdata = {
                "ClientTransactionID": f"{Device._client_trans_id}",
                "ClientID": f"{Device._client_id}" 
                }
        pdata.update(data)
        try:
            Device._ctid_lock.acquire()
            response = requests.put("%s/%s" % (self.base_url, attribute), data=pdata)
            Device._client_trans_id += 1
        finally:
            Device._ctid_lock.release()
        self.__check_error(response)
        return response.json()  # TODO Is this right? json()?

    def __check_error(self, response: requests.Response) -> None:
        """Alpaca exception handler (ASCOM exception types)

        Args:
            response (Response): Response from Alpaca server to check.

        Notes:
            Depending on the error number, the appropriate ASCOM exception type
            will be raised. See the ASCOM Alpaca API Reference for the reserved
            error codes and their corresponding exceptions.

        """
        if response.status_code in range(200, 204):
            j = response.json()
            n = j["ErrorNumber"]
            m = j["ErrorMessage"]
            if n != 0:
                if n == 0x0400:
                    raise NotImplementedException(n, m)
                elif n == 0x0401:
                    raise InvalidValueException(n, m)
                elif n == 0x0402:
                    raise ValueNotSetException(n, m)
                elif n == 0x0407:
                    raise NotConnectedException(n, m)
                elif n == 0x0408:
                    raise ParkedException(n, m)
                elif n == 0x0409:
                    raise SlavedException(n, m)
                elif n == 0x040B:
                    raise InvalidOperationException(n, m)
                elif n == 0x040c:
                    raise ActionNotImplementedException(n, m)
                elif n >= 0x500 and n <= 0xFFF:
                    raise DriverException(n, m)
                else: # unknown 0x400-0x4FF
                    raise UnknownAscomException(n, m)
        else:
            raise AlpacaRequestException(response.status_code, f"{response.text} (URL {response.url})")



