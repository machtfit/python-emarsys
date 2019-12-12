import pytest
import responses
from emarsys import Emarsys, EmarsysError
from freezegun import freeze_time


@freeze_time("2016-07-20T12:34:56")
def test_create_authentication_header(monkeypatch):
    # Chosen by fair dice roll.  Guaranteed to be random.
    monkeypatch.setattr('random.getrandbits', lambda x: 4)

    value = Emarsys('client_id', 'secret')._authentication_header_value()
    assert value == ('UsernameToken'
                     ' Username="client_id",'
                     ' PasswordDigest="NzVhOTg3Yjg2NTcyZmE1OWMwYzIxNWQ5ZDgyMzgxZWExOGI3NGFjZQ==",'
                     ' Nonce="a87ff679a2f3e71d9181a67b7542122c",'
                     ' Created="2016-07-20T12:34:56+00:00"')


def test_call_successful():
    with responses.RequestsMock() as r:
        r.add(r.POST, 'https://www1.emarsys.net/api/v2/contact', json={
            'replyCode': 0, 'replyText': 'OK', 'data': '',
        })

        Emarsys('client_id', 'secret').call('contact', 'POST', {})


def test_api_failure():
    with responses.RequestsMock() as r:
        r.add(r.POST, 'https://www1.emarsys.net/api/v2/contact', status=400, json={
            'replyCode': 2004, 'replyText': 'Invalid key field id: [id]', 'data': '',
        })

        with pytest.raises(EmarsysError) as err:
            Emarsys('client_id', 'secret').call('contact', 'POST', {})

        assert str(err.value) == 'EmarsysError(Invalid key field id: [id] (2004))'
