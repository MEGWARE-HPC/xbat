import functools
from .models import User
from werkzeug.security import gen_salt
from flask import request, render_template, session, Blueprint, current_app as app
from shared import httpErrors
from backend.restapi.mod_oauth import authorization, CustomRevocationEndpoint, get_tokeninfo

bp = Blueprint("oauth", __name__, template_folder="templates")


def split_by_crlf(s):
    return [v for v in s.splitlines() if v]


def login_required(fn):

    @functools.wraps(fn)
    def wrapped_view(**kwargs):
        auth = request.authorization
        if not auth:
            return ('Unauthorized', 401, {
                'WWW-Authenticate': 'Basic realm="Login Required"'
            })

        return fn(**kwargs)

    return wrapped_view


@bp.route('/authorize', methods=['GET', 'POST'])
@login_required
def authorize():
    if not request.authorization or not request.authorization[
            "username"] or not request.authorization["password"]:
        raise httpErrors.Unauthorized()

    user = User.load_user(request.authorization["username"])

    if user is None or not user.is_active() or not user.check_password(
            request.authorization["password"]):
        raise httpErrors.Unauthorized()

    if request.method == "GET":

        if not request.args.get("client_id"):
            raise httpErrors.BadRequest()

        # create csrf token and store for POST request in session
        session["_csrf"] = gen_salt(60)

        # enable hidden scope input field to request all scopes if none selected in oauth request (e.g. in swagger ui)
        client_id = request.args.get("client_id")
        scopes = request.args.get("scope")
        if scopes is not None:
            scopes = scopes.split(" ")
        else:
            scopes = []

        data = {
            "request": {
                "client": {
                    "client_id": client_id,
                    "name": client_id
                },
            },
            "scopes": scopes,
            "_csrf": session["_csrf"]
        }

        app.logger.debug("Client '%s' asking for authorization", client_id)
        return render_template("client_authorize.html", **data)

    return authorization.create_authorization_response(grant_user=user)


@bp.route('/token', methods=['POST'])
def issue_token():
    return authorization.create_token_response()


@bp.route("/tokeninfo")
def tokeninfo():
    """Get allowed scopes for token"""
    try:
        _, access_token = request.headers["Authorization"].split()
    except KeyError:
        access_token = ""

    return get_tokeninfo(access_token)


@bp.route('/revoke', methods=['POST'])
def revoke_token():
    return authorization.create_endpoint_response(
        CustomRevocationEndpoint.ENDPOINT_NAME)
