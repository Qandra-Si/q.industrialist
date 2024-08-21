"""Validates a given JWT token originating from the EVE SSO.

Prerequisites:
    * Have a Python 3 environment available to you (possibly by using a
      virtual environment: https://virtualenv.pypa.io/en/stable/)
    * Run pip install -r requirements.txt --user with this directory.
      or
      Run pip install -r requirements.txt with this directory as your root.

This can be run by doing

>>> python validate_jwt.py

and passing in a JWT token that you have retrieved from the EVE SSO.
"""
import sys

import requests
from jose import jwt
from jose.exceptions import ExpiredSignatureError, JWTError, JWTClaimsError


SSO_META_DATA_URL = "https://login.eveonline.com/.well-known/oauth-authorization-server"
JWK_ALGORITHM = "RS256"
JWK_ISSUERS = ("login.eveonline.com", "https://login.eveonline.com")
JWK_AUDIENCE = "EVE Online"

def validate_eve_jwt(jwt_token: str) -> dict:
    """Validate a JWT token retrieved from the EVE SSO.

    :param jwt_token: Aa JWT token originating from the EVE SSO
    :returns dict: the contents of the validated JWT token if there are no validation errors
    """

    # fetch JWKs URL from meta data endpoint
    res = requests.get(SSO_META_DATA_URL)
    res.raise_for_status()
    data = res.json()
    try:
        jwks_uri = data["jwks_uri"]
    except KeyError:
        raise RuntimeError(
            f"Invalid data received from the SSO meta data endpoint: {data}"
        ) from None

    # fetch JWKs from endpoint
    res = requests.get(jwks_uri)
    res.raise_for_status()
    data = res.json()
    try:
        jwk_sets = data["keys"]
    except KeyError as e:
        print("Something went wrong when retrieving the JWK set. The returned "
              "payload did not have the expected key {}. \nPayload returned "
              "from the SSO looks like: {}".format(e, data))
        sys.exit(1)

    jwk_set = [item for item in jwk_sets if item["alg"] == JWK_ALGORITHM].pop()

    try:
        return jwt.decode(
            token=jwt_token,
            key=jwk_set,
            algorithms=jwk_set["alg"],
            issuer=JWK_ISSUERS,
            audience=JWK_AUDIENCE,
        )
    except ExpiredSignatureError:
        print("The JWT token has expired")
        sys.exit(1)
    except JWTError as e:
        print(f"The JWT token was invalid: {e}")
        sys.exit(1)
    except JWTClaimsError as e:
        try:
            return jwt.decode(
                        jwt_token,
                        jwk_set,
                        algorithms=jwk_set["alg"],
                        issuer="https://login.eveonline.com"
                    )
        except JWTClaimsError as e:
            print("The issuer claim was not from login.eveonline.com or "
                  "https://login.eveonline.com: {}".format(str(e)))
            sys.exit(1)


def main():
    """Manually input a JWT token to be validated."""

    token = input("Enter an access token to validate: ")
    validated_jwt = validate_eve_jwt(token)

    print("\nThe contents of the access token are: {}".format(validated_jwt))


if __name__ == "__main__":
    main()
