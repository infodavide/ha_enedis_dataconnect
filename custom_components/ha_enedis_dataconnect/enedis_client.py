#!/usr/bin/python3
# -*- coding: utf-8-
"""
The Enedis data-connect client
"""
import json
import logging
from typing import Any
import validators
from homeassistant import exceptions
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


class InvalidAccess(exceptions.HomeAssistantError):
    """
    Error to indicate that token or PDL are not authorized
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
        _LOGGER.debug('{}\n{}\n{}\n{}\n{}\n'.format(
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
        _LOGGER.debug('{}\n{}\n{}\n{}\n{}\n'.format(
            '-----------RESPONSE START-----------',
            str(resp.status_code) + ' ' + resp.url,
            '\n'.join('{}: {}'.format(k, v) for k, v in resp.cookies.items()),
            resp.text,
            '-----------RESPONSE STOP-----------',
        ))
        # pylint: enable=logging-format-interpolation,consider-using-f-string

    # noinspection PyTypeChecker
    def __init__(self, pdl: str, client_id: str, client_secret: str, redirect_uri: str):
        """
        The constructor
        :param pdl: the PDL identifier
        :param client_id: the client identifier
        :param client_secret: the client secret
        :param redirect_uri: the redirection URI
        """
        _LOGGER.debug("Building client...")
        self._pdl: str = pdl
        self._client_id: str = client_id
        self._client_secret: str = client_secret
        if redirect_uri is None or len(redirect_uri) == 0:
            self._redirect_uri = redirect_uri
        else:
            self._redirect_uri: str = DEFAULT_REDIRECT_URI
        self._token_data: dict[str, Any] = None

    def __del__(self):
        """
        Destructor
        """
        self.close()

    # noinspection PyTypeChecker
    def close(self):
        """
        Close the client
        """
        if not self.is_connected():
            return
        _LOGGER.debug("Closing client...")
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
            'client_secret': self._client_secret,
            'token': token
        }
        # Forge and print request
        req = Request("POST", ENDPOINT_TOKEN_URL + 'revoke', headers=req_headers, params=req_params, data=req_data)
        prepared_req = req.prepare()
        http_session: Session = Session()
        EnedisClient._log_request(prepared_req)
        resp: Response = None
        try:
            resp = http_session.send(prepared_req)
            EnedisClient._log_response(resp)
        finally:
            self._token_data = None
            if resp:
                resp.close()

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

    @property
    def get_client_secret(self) -> str:
        """
        Get the client secret
        :return: the secret
        """
        return self._client_secret

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
        if self._redirect_uri is None or not validators.url(self._redirect_uri):
            raise InvalidUrl
        if self._client_id is None or not validators.length(self._client_id, min=1, max=128):
            raise InvalidClientId
        if self._client_secret is None or not validators.length(self._client_secret, min=1, max=128):
            raise InvalidClientSecret
        _LOGGER.debug("Connection client...")
        req_headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        req_params = {
            'redirect_uri': self._redirect_uri,
        }
        req_data = {
            'grant_type': 'client_credentials',
            'client_id': self._client_id,
            'client_secret': self._client_secret
        }
        req: Request = Request("POST", ENDPOINT_TOKEN_URL + 'token', headers=req_headers, params=req_params, data=req_data)
        prepared_req: PreparedRequest = req.prepare()
        http_session: Session = Session()
        EnedisClient._log_request(prepared_req)
        resp: Response = None
        try:
            resp = http_session.send(prepared_req)
            EnedisClient._log_response(resp)
            if resp.status_code != 200:
                raise InvalidAccess
            self._token_data = json.loads(resp.text)
        finally:
            if resp:
                resp.close()
