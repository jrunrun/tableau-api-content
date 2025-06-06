import jwt
import datetime
import uuid
import requests
import os
import logging
from typing import Dict, Any
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config() -> Dict[str, str]:
    """
    Load configuration for Tableau Connected App authentication from environment variables.

    Returns:
        Dict[str, str]: Dictionary containing configuration values.

    Raises:
        ValueError: If any required environment variable is missing.
    """
    load_dotenv()
    required_vars = {
        'CONNECTED_APP_CLIENT_ID': os.getenv('CONNECTED_APP_CLIENT_ID'),
        'CONNECTED_APP_SECRET': os.getenv('CONNECTED_APP_SECRET'),
        'CONNECTED_APP_SECRET_ID': os.getenv('CONNECTED_APP_SECRET_ID'),
        'TABLEAU_USER': os.getenv('TABLEAU_USER'),
        'TABLEAU_POD': os.getenv('TABLEAU_POD'),
        'TABLEAU_API_VERSION': os.getenv('TABLEAU_API_VERSION'),
        'TABLEAU_SITE': os.getenv('TABLEAU_SITE')
    }
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    return required_vars

def generate_jwt_token(config: Dict[str, str]) -> str:
    """
    Generate a JWT token for Tableau Connected App authentication.

    Args:
        config (Dict[str, str]): Configuration dictionary.

    Returns:
        str: Encoded JWT token.
    """
    now = datetime.datetime.utcnow()
    payload = {
        "iss": config['CONNECTED_APP_CLIENT_ID'],
        "exp": now + datetime.timedelta(minutes=5),
        "iat": now,
        "jti": str(uuid.uuid4()),
        "aud": "tableau",
        "sub": config['TABLEAU_USER'],
        "scp": [
            "tableau:views:embed",
            "tableau:insights:embed",
            "tableau:content:read"
        ]
    }
    headers = {
        'kid': config['CONNECTED_APP_SECRET_ID'],
        'iss': config['CONNECTED_APP_CLIENT_ID'],
        'typ': 'JWT'
    }
    token = jwt.encode(
        payload,
        config['CONNECTED_APP_SECRET'],
        algorithm="HS256",
        headers=headers
    )
    return token

def authenticate_with_tableau(jwt_token: str, config: Dict[str, str]) -> str:
    """
    Authenticate with Tableau REST API using a JWT token.

    Args:
        jwt_token (str): JWT token for authentication.
        config (Dict[str, str]): Configuration dictionary.

    Returns:
        str: Tableau REST API authentication token.

    Raises:
        requests.exceptions.RequestException: If the authentication request fails.
        KeyError: If the expected token is not found in the response.
    """

    AUTH_ENDPOINT = "auth/signin"

    payload = {
        "credentials": {
            "jwt": jwt_token,
            "site": {
                "contentUrl": config['TABLEAU_SITE']
            }
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }   


    tableau_auth_url = f"https://{config['TABLEAU_POD']}/api/{config['TABLEAU_API_VERSION']}/{AUTH_ENDPOINT}"

    response = requests.post(tableau_auth_url, headers=headers, json=payload)
    response.raise_for_status()
    response_data = response.json()
    return response_data['credentials']['token']

def main() -> None:
    """
    Main function to authenticate with Tableau using a Connected App and print the REST API token.
    """
    try:
        config = load_config()
        jwt_token = generate_jwt_token(config)
        tableau_rest_api_token = authenticate_with_tableau(jwt_token, config)
        logger.info(f"JWT Token: {jwt_token}")
        logger.info(f"Tableau REST API Token: {tableau_rest_api_token}")
    except ValueError as ve:
        logger.error(f"Configuration error: {ve}")
    except requests.exceptions.RequestException as re:
        logger.error(f"Error making request: {str(re)}")
        if hasattr(re, 'response') and re.response is not None:
            logger.error(f"Response Status Code: {re.response.status_code}")
            logger.error(f"Response Text: {re.response.text}")
    except KeyError as ke:
        logger.error(f"Unexpected response structure, missing key: {ke}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()

