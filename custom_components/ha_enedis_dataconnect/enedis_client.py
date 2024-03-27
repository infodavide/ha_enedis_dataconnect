#!/usr/bin/python3
# -*- coding: utf-8-
"""
The Enedis data-connect client
"""
import base64
import json
import logging
import re
from threading import RLock
from typing import Any
from homeassistant import exceptions
from homeassistant.core import HomeAssistant
from requests import PreparedRequest, Session, Request, Response

from .constants import ENDPOINT_TOKEN_URL, DEFAULT_REDIRECT_URI

_LOGGER = logging.getLogger(__name__)


class InvalidClientId(exceptions.HomeAssistantError):
    """
    Error to indicate that PDL is invalid
    """


class InvalidClientSecret(exceptions.HomeAssistantError):
    """
    Error to indicate that PDL is invalid
    """


class InvalidPdl(exceptions.HomeAssistantError):
    """
    Error to indicate that PDL is invalid
    """


class InvalidUrl(exceptions.HomeAssistantError):
    """
    Error to indicate that URL is invalid
    """


class InvalidToken(exceptions.HomeAssistantError):
    """
    Error to indicate that token is invalid
    """


class InvalidScanInterval(exceptions.HomeAssistantError):
    """
    Error to indicate that scan interval is invalid
    """


class InvalidPeakHourCost(exceptions.HomeAssistantError):
    """
    Error to indicate that cost of a peak hour is invalid
    """


class InvalidAccess(exceptions.HomeAssistantError):
    """
    Error to indicate that token or PDL are not authorized
    """


class ApiConnectionError(exceptions.HomeAssistantError):
    """
    Error to indicate that connection failed
    """


class EnedisClient:
    """
    The Enedis data-connect client
    """

    @staticmethod
    def _log_request(req: PreparedRequest) -> None:
        """
        Log the HTTP request
        :param req: the request
        """
        # pylint: disable=logging-format-interpolation,consider-using-f-string
        _LOGGER.debug('\n{}\n{}\n{}\n{}\n{}\n'.format(
            '-----------REQUEST START-----------',
            req.method + ' ' + req.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in req.headers.items()),
            req.body,
            '-----------REQUEST STOP-----------',
        ))
        # pylint: enable=logging-format-interpolation,consider-using-f-string

    @staticmethod
    def _log_response(resp: Response) -> None:
        """
        Log the response
        :param resp:  the response
        """
        # pylint: disable=logging-format-interpolation,consider-using-f-string
        _LOGGER.debug('\n{}\n{}\n{}\n{}\n{}\n'.format(
            '-----------RESPONSE START-----------',
            str(resp.status_code) + ' ' + resp.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in resp.cookies.items()),
            resp.text,
            '-----------RESPONSE STOP-----------',
        ))
        # pylint: enable=logging-format-interpolation,consider-using-f-string

    @staticmethod
    def _send_with_result(prepared_req: PreparedRequest) -> dict[str, Any]:
        """
        Send returning data
        :param prepared_req: the prepared request
        :return: the data
        """
        EnedisClient._log_request(prepared_req)
        http_session: Session = Session()
        # noinspection PyTypeChecker
        resp: Response = None
        try:
            resp = http_session.send(prepared_req)
            EnedisClient._log_response(resp)
            if resp.status_code != 200:
                raise InvalidAccess
            return json.loads(resp.text)
        except Exception as e:
            raise ApiConnectionError(e) from e
        finally:
            if resp:
                resp.close()

    @staticmethod
    def _send_without_result(prepared_req: PreparedRequest) -> None:
        """
        Send without returning data
        :param prepared_req: the prepared request
        """
        EnedisClient._log_request(prepared_req)
        http_session: Session = Session()
        # noinspection PyTypeChecker
        resp: Response = None
        # noinspection PyBroadException
        try:
            resp = http_session.send(prepared_req)
            EnedisClient._log_response(resp)
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("An error occurred while closing the client")
        finally:
            if resp:
                resp.close()

    # noinspection PyTypeChecker
    def __init__(self, hass: HomeAssistant, pdl: str, client_id: str, client_secret: str, redirect_uri: str):
        """
        The constructor
        :param hass: the home assistant instance
        :param pdl: the PDL identifier
        :param client_id: the client identifier
        :param client_secret: the client secret
        :param redirect_uri: the redirection URI
        """
        _LOGGER.debug("Building the client with: PDL: %s, Client identifier: %s, redirect URL: %s and secret: %s", pdl, client_id, redirect_uri, re.sub(r'.', '*', client_secret))
        if pdl is None or not re.match("\\d{14}", pdl):
            raise InvalidPdl
        if redirect_uri is None or not re.match('^(http|https):.*$', redirect_uri):  # Note that validators.url does not validate URL with localhost or some special characters
            raise InvalidUrl
        if client_id is None or len(client_id) <= 0 or len(client_id) > 128:
            raise InvalidClientId
        if client_secret is None or len(client_secret) <= 0 or len(client_secret) > 128:
            raise InvalidClientSecret
        self._hass: HomeAssistant = hass
        self._lock: RLock = RLock()
        self._pdl: str = pdl
        self._client_id: str = client_id
        self._client_secret: bytes = base64.b64encode(client_secret.encode('utf-8'))
        self._redirect_uri: str = DEFAULT_REDIRECT_URI
        if redirect_uri is not None and len(redirect_uri) > 0:
            self._redirect_uri = redirect_uri
        self._token_data: dict[str, Any] = None

    def __del__(self):
        """
        Destructor
        """
        self._hass.async_add_executor_job(self.close)

    # noinspection PyTypeChecker
    def close(self):
        """
        Close the client
        """
        if not self.is_connected():
            _LOGGER.debug("Client already disconnected")
            return
        _LOGGER.info("Closing client...")
        token_type: str = self._token_data['token_type']
        token: str = self._token_data['access_token']
        req_headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': token_type + ' ' + token
        }
        req_params = {
        }
        req_data = {
            'client_id': self._client_id,
            'client_secret':  self._get_client_secret(),
            'token': token
        }
        # Forge and print request
        req = Request("POST", ENDPOINT_TOKEN_URL + 'revoke', headers=req_headers, params=req_params, data=req_data)
        prepared_req = req.prepare()
        with self._lock:
            EnedisClient._send_without_result(prepared_req)
            self._token_data = None

    @property
    def get_pdl(self) -> str:
        """
        Get the PDL identifier
        :return: the PDL identifier
        """
        return self._pdl

    @property
    def get_client_id(self) -> str:
        """
        Get the client identifier
        :return: the identifier
        """
        return self._client_id

    def get_hass(self) -> HomeAssistant:
        """
        Return the home assistant instance
        :return: the home assistant instance
        """
        return self._hass

    def _get_client_secret(self) -> str | None:  # pylint: disable=unsupported-binary-operation
        """
        Get the client secret
        :return: the secret
        """
        if self._client_secret is None:
            return None
        return base64.b64decode(self._client_secret).decode('utf-8')

    @property
    def get_token_data(self) -> dict[str, Any]:
        """
        Get the current token data
        :return: the data
        """
        return self._token_data

    def is_connected(self) -> bool:
        """
        Return true if the connection has been initialized
        :return:
        :rtype:
        """
        return self._token_data is not None and len(self._token_data) > 0

    # noinspection PyTypeChecker
    def connect(self) -> None:
        """
        Connect the client
        """
        if self.is_connected():
            _LOGGER.debug("Client already connected")
            return
        _LOGGER.info("Connecting client...")
        req_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        req_params = {
            'redirect_uri': self._redirect_uri,
        }
        req_data = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._get_client_secret()
        }
        req: Request = Request("POST", ENDPOINT_TOKEN_URL + 'token', headers=req_headers, params=req_params, data=req_data)
        prepared_req: PreparedRequest = req.prepare()
        with self._lock:
            self._token_data = EnedisClient._send_with_result(prepared_req)
            _LOGGER.debug("Token data is: %s", self._token_data)

    def update_data(self) -> None:
        """
        Retrieves the data
        """
        _LOGGER.debug("Updating the data...")
