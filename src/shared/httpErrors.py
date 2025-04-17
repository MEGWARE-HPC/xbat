from werkzeug.exceptions import BadRequest, HTTPException, NotFound, Forbidden, Unauthorized, InternalServerError
# from connexion.exceptions import OAuthProblem


class OAuthLoginError(HTTPException):
    code = 401
    description = 'Could not authenticate user against authentication provider'
    name = "LoginError"


class OAuthLoginGrantError(HTTPException):
    code = 401
    description = 'Invalid credentials'
    name = "LoginGrantError"


class OAuthTokenNotFound(HTTPException):
    code = 401
    description = 'Invalid or expired access token'
    name = "LoginTokenError"
