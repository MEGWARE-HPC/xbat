import pam
from authlib.integrations.flask_oauth2 import AuthorizationServer
from authlib.oauth2.rfc6749 import grants
from authlib.oauth2.rfc7009 import RevocationEndpoint
from flask import request, current_app as app
from shared import httpErrors
from shared.mongodb import MongoDB
from shared.helpers import get_entry_string
from shared.date import get_current_datetime
from backend.restapi.auth.ipa import IPAConnection
from backend.restapi.auth.ldap import LDAPConnection
from backend.restapi.auth.models import Client, Token, User
from backend.restapi.grpc_client import XbatCtldRpcClient

AUTHENTICATION_PROVIDER = app.config["CONFIG"]["authentication"]["provider"]

ipa = IPAConnection()
ldap = LDAPConnection()
db = MongoDB()
rpcClient = XbatCtldRpcClient()


def get_tokeninfo(access_token):
    """
    Get allowed scopes for token.
    Returns None is invalid, revoked or expired, which triggers an OAuthResponseProblem

    :param access_token: access token.
    :return: dictionary with scopes and client id or None
    """
    token = Token.load_token(access_token=access_token)
    if not token or not token.is_access_token_active():
        return None
    return {"scopes": token.scope, "client_id": token.client_id}


class CustomRevocationEndpoint(RevocationEndpoint):
    """Token revocation endpoint"""
    CLIENT_AUTH_METHODS = ["none", "client_secret_basic"]

    def query_token(self, token, token_type_hint):
        if token_type_hint == "access_token":
            return Token.load_token(access_token=token)
        else:
            return Token.load_token(refresh_token=token)

    def revoke_token(self, token, request):
        token.revoke()


class PasswordGrant(grants.ResourceOwnerPasswordCredentialsGrant):
    """Password grant for token endpoint"""
    # TODO Check why password grant does not support token_endpoint_auth_method "none" by default
    # TODO Check if PKCE is required
    TOKEN_ENDPOINT_AUTH_METHODS = ["none", "client_secret_basic"]

    def authenticate_user(self, username, password):
        user = User.load_user(username)
        if user is not None and user.check_password(password):
            user.last_login = get_current_datetime()
            user.update()
            return user
        raise httpErrors.OAuthLoginGrantError()


def validate_client(client_id):
    """
    Validates user based on blacklist/whitelist and credentials with external authorization provider.

    Will insert and update users and register client if not present.
    """

    if client_id == "xbatd":
        return True

    form = request.form.to_dict()
    username = form["username"]
    password = form["password"]

    user = User.load_user(username)

    # admin and demo are already checked by query_client
    # and must not be imported by external authentication system
    # since they are internal accounts
    if user is not None and (user.user_type == "admin" or
                             (app.config["DEMO_MODE"]
                              and user.user_type == "demo")):
        return True

    # user found but blocked
    if user is not None and not user.is_active():
        app.logger.warning("Blocked user '%s' login request", username)
        raise httpErrors.OAuthLoginError()

    user_info = None

    if AUTHENTICATION_PROVIDER == "ipa":
        info = ipa.get_user(user=username, password=password)
        if info is not None:
            user_info = info["result"]
        else:
            app.logger.error("Authentication against IPA failed for user '%s'",
                             username)

    elif AUTHENTICATION_PROVIDER == "ldap":
        authenticated = ldap.auth_user(user=username, password=password)
        if authenticated:
            # ldap does not provide user details
            user_info = rpcClient.get_user_info(username)
        else:
            app.logger.error(
                "Authentication against LDAP failed for user '%s'", username)

    elif AUTHENTICATION_PROVIDER == "pam":
        if pam.authenticate(username, password, print_failure_messages=True):
            user_info = rpcClient.get_user_info(username)
        else:
            app.logger.error("Authentication against PAM failed for user '%s'",
                             username)

    # TODO raise proper error according to reason (invalid password, blocked etc.)
    if user_info is None or not bool(user_info) or not (
            "uidnumber" in user_info
    ) or not ("gidnumber" in user_info) or not ("homedirectory" in user_info):
        raise httpErrors.OAuthLoginError()

    uid = get_entry_string(user_info["uidnumber"])
    gid = get_entry_string(user_info["uidnumber"])
    homedirectory = get_entry_string(user_info["homedirectory"])

    if user is None:
        # Some authentication providers check the username in a case-insensitive way.
        # This may lead to multiple users with the same UID but different usernames e.g. "user", "User", "uSer".
        # Therefore we need to check if the UID already exists in the database.
        # Warning: this does not account for UID changes in the external authentication system.
        user_by_uid = User.load_user_by_uid(uid)

        if user_by_uid is None:
            user = User(user_name=username,
                        password="",
                        user_type="user",
                        uidnumber=uid,
                        gidnumber=gid,
                        homedirectory=homedirectory)
            if user.insert() is None:
                app.logger.error("Could not create new user '%s' in database",
                                 username)
                raise httpErrors.InternalServerError()
        else:
            app.logger.error("User '%s' already exists with UID '%s' as '%s'",
                             username, uid, user_by_uid.user_name)
            raise httpErrors.OAuthLoginError(
                "User with the same UID already exists under a different username. Please contact your administrator."
            )
    else:
        # always set uidnumber/gidnumber in case it changed
        user.uidnumber = uid
        user.gidnumber = gid
        user.homedirectory = homedirectory
        if not user.update():
            app.logger.error("Could not update user '%s' in database",
                             username)
            raise httpErrors.InternalServerError()

    # create separate clients for frontend and swagger
    client_ids = [form["client_id"]]
    if form["client_id"].startswith("wf_"):
        client_ids.append(form["client_id"][3:])

    for client_id in client_ids:
        client = Client.load_client(client_id)
        if client is None:
            app.logger.debug("Registering client '%s' for user '%s'",
                             client_id, user.user_name)
            client = Client(client_id=client_id,
                            name=user.user_name,
                            default_scopes=" ".join(
                                app.config["security_roles"]["user"]))

            if client.insert() is None:
                app.logger.error(
                    "Could not register client '%s' for user '%s'", client_id,
                    user.user_name)
                raise httpErrors.InternalServerError()

    return True


def query_client(client_id):
    """
    Returns matching client for client_id after validation with external authorization provider.
    
    :param client_id: client identifier
    :return: Client
    """

    # perform validation only on token endpoint as query_client is also called on revocation
    # TODO check with /oauth/authorize
    if request.path == "/oauth/token" and not validate_client(client_id):
        return None
    return Client.load_client(client_id)


def save_token(token_data, request):
    """
    Store new token in database.
    
    :param token_data: token information
    :param request: client request
    """

    if request.user is None and request.client is None: return

    Token(client_id=request.client.client_id,
          user_id=request.user.get_user_id() if request.user else None,
          **token_data,
          scope=request.client.default_scopes).insert()


app.config['OAUTH2_TOKEN_EXPIRES_IN'] = {
    'implicit': 3600,  # 1 hour
    'password': 86400,  # 1 day
    'client_credentials': 900,  # 15 minutes
    'refresh_token': 604800  # 1 week
}

authorization = AuthorizationServer(query_client=query_client,
                                    save_token=save_token)


def config_oauth(app):
    """
    Initializes and configures the OAuth authorization.

    Refresh token and introspection endpoint not supported. Token scope validation
    performed by connexion.
    
    :param app: flask application
    """

    authorization.init_app(app)

    # general authentication
    authorization.register_grant(PasswordGrant)
    # for swagger UI
    authorization.register_grant(grants.ImplicitGrant)
    # for xbatd
    authorization.register_grant(grants.ClientCredentialsGrant)

    authorization.register_endpoint(CustomRevocationEndpoint)
