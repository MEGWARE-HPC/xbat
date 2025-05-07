import secrets
import time
import pam
import bcrypt
from authlib.oauth2.rfc6749 import scope_to_list, list_to_scope
from flask import current_app as app
from shared.mongodb import MongoDB
from shared.auth import encrypt_pw, old_sha1_check
from shared.helpers import filter_dict
from backend.restapi.auth.ipa import IPAConnection
from backend.restapi.auth.ldap import LDAPConnection

AUTHENTICATION_PROVIDER = app.config["CONFIG"]["authentication"]["provider"]

ipa = IPAConnection()
ldap = LDAPConnection()
db = MongoDB()


class User():

    def __init__(self,
                 user_name,
                 user_type,
                 password,
                 uidnumber=None,
                 gidnumber=None,
                 homedirectory=None,
                 blocked=False,
                 last_login=None,
                 _id=""):
        self._id = _id
        self.user_name = user_name
        self.user_type = user_type
        self.uidnumber = uidnumber
        self.gidnumber = gidnumber
        self.homedirectory = homedirectory
        self.password = password
        self.blocked = blocked
        self.last_login = last_login
        self.whitelisted = self.check_whitelist()

    def check_whitelist(self):
        # admin is excempted from whitelist
        if self.user_type == "admin" or (app.config["DEMO_MODE"]
                                         and self.user_type == "demo"):
            return True

        appSettings = db.getOne("settings", {})

        if appSettings is not None:
            if "whitelist" in appSettings and appSettings[
                    "whitelist"] is not None and appSettings["whitelist"][
                        "enabled"]:
                if not (self.user_name in appSettings["whitelist"]["users"]):
                    app.logger.warning(
                        "Attempted access from non-whitelist user '%s'",
                        self.user_name)
                    return False
        return True

    def insert(self):
        result = db.insertOne(
            "users", filter_dict(self.__dict__, ["_id", "whitelisted"]))
        if result.acknowledged:
            self._id = result.inserted_id
            return result.inserted_id
        return None

    def update(self):
        result = db.replaceOne(
            "users", {"_id": self._id},
            filter_dict(self.__dict__, ["_id", "whitelisted"]))
        return result.acknowledged

    def check_password(self, password):
        if self.password and (self.user_type == "admin" or
                              (app.config["DEMO_MODE"]
                               and self.user_type == "demo")):
            # changed hashing from sha1 to bcrypt -> rehash password if needed
            if self.password.startswith('*'):
                if old_sha1_check(password, self.password):
                    new_hash = encrypt_pw(password)
                    self.password = new_hash
                    self.update()
                    return True
                return False
            # bcrypt is already in use, verify as usual
            return bcrypt.checkpw(password.encode('utf-8'),
                                  self.password.encode('utf-8'))

        if AUTHENTICATION_PROVIDER == "ipa":
            return ipa.auth_user(self.user_name, password)
        elif AUTHENTICATION_PROVIDER == "pam":
            return pam.authenticate(self.user_name, password)
        elif AUTHENTICATION_PROVIDER == "ldap":
            return ldap.auth_user(self.user_name, password)

        app.logger.warning("Failed authenticate user '%s' via %s",
                           self.user_name, AUTHENTICATION_PROVIDER.upper())
        return False

    def delete(self):
        return db.deleteOne("users", {"user_name": self.user_name})

    def is_active(self):
        return not self.blocked and self.whitelisted

    def get_user_id(self):
        return self._id

    def get_user_name(self):
        return self.user_name

    @staticmethod
    def load_user(user_name):
        user = db.getOne("users", {"user_name": user_name})
        return None if user is None else User(
            **filter_dict(user, ["whitelisted"]))

    @staticmethod
    def load_user_by_uid(uid):
        user = db.getOne("users", {"uid": str(uid)})
        return None if user is None else User(
            **filter_dict(user, ["whitelisted"]))


class Client():
    grant_types = ["password", "client_credentials"]
    token_endpoint_auth_method = ["none", "client_secret_basic"]

    DEFAULT_REDIRECT_URIS = [
        "http://localhost:7000/api/v1/ui/oauth2-redirect.html",
        "http://127.0.0.1:7000/api/v1/ui/oauth2-redirect.html",
        "https://localhost:7000/api/v1/ui/oauth2-redirect.html",
        "https://127.0.0.1:7000/api/v1/ui/oauth2-redirect.html"
    ]

    DEFAULT_RESPONSE_TYPES = ["token"]

    def __init__(self,
                 client_id,
                 name="",
                 _id="",
                 client_secret="",
                 default_scopes=[],
                 user={},
                 redirect_uris=[],
                 default_redirect_uri="",
                 client_id_issued_at=0,
                 response_types=[]):
        self._id = _id
        self.name = name
        self.client_id = client_id
        self.client_secret = client_secret
        self.default_scopes = default_scopes
        self.user = user
        self.default_redirect_uri = default_redirect_uri
        self.client_id_issued_at = client_id_issued_at or time.time()
        self.response_types = response_types or self.DEFAULT_RESPONSE_TYPES

        if self.is_frontend_client():
            self.redirect_uris = []
        else:
            if len(redirect_uris):
                self.redirect_uris = redirect_uris if isinstance(
                    redirect_uris, list) else redirect_uris.split()
            else:
                self.redirect_uris = self.DEFAULT_REDIRECT_URIS

    @property
    def client_info(self):
        return dict(
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_id_issued_at=self.client_id_issued_at,
        )

    @property
    def grand_types(self):
        return self.grant_types

    def is_frontend_client(self):
        return self.client_id.startswith("wf_")

    def get_client_id(self):
        return self.client_id

    def get_default_redirect_uri(self):
        if self.redirect_uris:
            return self.redirect_uris[0]

    def get_allowed_scope(self, scope):
        if not scope:
            return ''
        allowed = set(self.scope.split())
        scopes = scope_to_list(scope)
        return list_to_scope([s for s in scopes if s in allowed])

    def check_redirect_uri(self, redirect_uri):
        return redirect_uri in self.redirect_uris

    def check_client_secret(self, client_secret):
        return secrets.compare_digest(self.client_secret, client_secret)

    def check_endpoint_auth_method(self, method, endpoint):
        if endpoint == 'token':
            return method in self.token_endpoint_auth_method
        return True

    def check_response_type(self, response_type):
        return response_type in self.response_types

    def check_grant_type(self, grant_type):
        return grant_type in self.grant_types

    def insert(self):
        data = filter_dict(self.__dict__, ["_id", "user"])
        data["redirect_uris"] = " ".join(data["redirect_uris"])
        result = db.insertOne("clients", data)
        if result.acknowledged:
            self._id = result.inserted_id
            return result.inserted_id
        return None

    @staticmethod
    def load_client(client_id):
        client = db.getOne("clients", {"client_id": client_id})
        if client is None:
            return None
        return Client(**client)

    @staticmethod
    def load_clients(client_id):
        clients = [
            c for c in db.getMany("clients", {"client_id": client_id})
            if c is not None
        ]
        return [Client(**c) for c in clients]


class Token():

    def __init__(self,
                 client_id,
                 user_id,
                 token_type,
                 access_token,
                 _id="",
                 refresh_token="",
                 scope="",
                 issued_at=None,
                 access_token_revoked_at=0,
                 refresh_token_revoked_at=0,
                 expires_in=86400,
                 revoked=False):
        self._id = _id
        self.client_id = client_id
        self.user_id = user_id
        self.token_type = token_type
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.scope = scope
        self.issued_at = issued_at or time.time()
        self.access_token_revoked_at = access_token_revoked_at
        self.refresh_token_revoked_at = refresh_token_revoked_at
        self.expires_in = expires_in
        self.revoked = revoked

    def check_client(self, client):
        return self.client_id == client.get_client_id()

    def is_refresh_token_active(self):
        return self.refresh_token and not self.is_revoked(
        ) and not self.is_expired()

    def is_access_token_active(self):
        return self.access_token and not self.is_revoked(
        ) and not self.is_expired()

    def get_scope(self):
        return self.scope

    def get_expires_in(self):
        return self.expires_in

    def is_revoked(self):
        return self.revoked or self.access_token_revoked_at or self.refresh_token_revoked_at

    def is_expired(self):
        if not self.expires_in:
            return False
        expires_at = self.issued_at + self.expires_in
        return expires_at < time.time()

    def insert(self):
        result = db.insertOne("tokens", filter_dict(self.__dict__, ["_id"]))
        if result.acknowledged:
            self._id = result.inserted_id
            return result.inserted_id
        return None

    @staticmethod
    def load_token(access_token=None, refresh_token=None):
        token = None
        if access_token:
            token = db.getOne("tokens", {"access_token": access_token})
        elif refresh_token:
            token = db.getOne("tokens", {"refresh_token": refresh_token})
        return Token(**token) if token is not None else None

    def revoke(self):
        # do not revoke token of demo accounts as this would lead to a logout of all users
        if app.config["DEMO_MODE"]:
            user = User.load_user(self.user_id)
            if user and user.user_type == "demo":
                return

        timestamp = time.time()
        self.revoked = True
        self.access_token_revoked_at = timestamp
        self.refresh_token_revoked_at = timestamp
        db.replaceOne("tokens", {"_id": self._id}, self.__dict__)
