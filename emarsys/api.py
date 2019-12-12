"""
Copyright 2012 42 Ventures Pte Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
import base64
import datetime
import hashlib
import random

import requests

from .errors import EmarsysError, error_dictionary

import json
import pytz


class Emarsys(object):
    """
    Emarsys REST API wrapper.
    """

    def __init__(self,
                 username,
                 secret_token,
                 base_uri="https://www1.emarsys.net/api/v2/",
                 timeout=None):
        """
        Initialises the Emarsys API wrapper object.
        """
        self._username = username
        self._secret_token = secret_token
        self._base_uri = base_uri
        self.timeout = timeout

    def __str__(self):
        return "Emarsys({base_uri})".format(base_uri=self._base_uri)

    def __repr__(self):
        return str(self)

    def call(self, uri, method, params=None):  # noqa
        """
        Send the API call request to the Emarsys server.
        uri: API method URI
        method: HTTP method
        params: parameters to construct payload when API calls are made with
                POST or PUT HTTP methods.
        """
        uri = self._base_uri + uri
        if params:
            params = json.dumps(params)
        headers = {"X-WSSE": self._authentication_header_value(),
                   "Content-Type": "application/json"}
        try:
            response = requests.request(method,
                                        uri,
                                        data=params,
                                        headers=headers,
                                        timeout=self.timeout)
        except Exception as e:
            raise EmarsysError(message=repr(e))

        try:
            result = json.loads(response.text)
        except ValueError as e:
            raise EmarsysError(
                message="HTTP {status_code}: {reason} [{uri}]".format(
                    status_code=response.status_code,
                    reason=response.reason,
                    uri=uri,
                ),
            )

        if not (isinstance(result, dict) and "replyCode" in result and
                "replyText" in result and "data" in result):
            message = "Unexpected response from Emarsys"
            if not response.ok:
                message = "{message} (HTTP {code})".format(
                    message=message,
                    code=response.status_code,
                )
            raise EmarsysError(message=message)

        if result.get("replyCode", 0) != 0:
            reply_code = str(result.get("replyCode", "0"))
            exception = error_dictionary.get(reply_code)
            if exception:
                raise exception(
                    message=result["replyText"],
                    code=result.get("replyCode", "0")
                )
            else:
                raise EmarsysError(
                    message=result["replyText"],
                    code=result.get("replyCode", "0")
                )

        return result["data"]

    def _authentication_header_value(self):
        now = datetime.datetime.now(tz=pytz.utc)
        created = now.replace(microsecond=0).isoformat()
        nonce = hashlib.md5(str(random.getrandbits(128)).encode()).hexdigest()
        password_digest = "".join((nonce, created, self._secret_token)).encode()
        password_digest = hashlib.sha1(password_digest).hexdigest().encode()
        password_digest = base64.b64encode(password_digest).decode('ascii')
        return ('UsernameToken Username="{username}", '
                'PasswordDigest="{password_digest}", Nonce="{nonce}", '
                'Created="{created}"').format(username=self._username,
                                              password_digest=password_digest,
                                              nonce=nonce,
                                              created=created)
