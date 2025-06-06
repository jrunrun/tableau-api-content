# Steps:
# 1. Get the site ID and token from the auth response
# 2. Use the both site ID and token to get the content of the site

import requests
import json
import logging
import urllib.parse
from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
import os
from dotenv import load_dotenv
import importlib.util
import sys
import urllib3

# Suppress only the specific InsecureRequestWarning
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Dynamically import ca-auth.py as ca_auth
spec = importlib.util.spec_from_file_location("ca_auth", "ca-auth.py")
ca_auth = importlib.util.module_from_spec(spec)
sys.modules["ca_auth"] = ca_auth
spec.loader.exec_module(ca_auth)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TableauConfig:
    """Configuration class for Tableau API settings."""
    pod: str
    site: str
    project_1: str
    project_2: str
    api_version: str

def load_config() -> TableauConfig:
    """
    Load Tableau configuration from environment variables.
    
    Returns:
        TableauConfig: Configuration object containing Tableau settings.
        
    Raises:
        ValueError: If required environment variables are missing.
    """
    load_dotenv()
    
    required_vars = {
        'TABLEAU_POD': os.getenv('TABLEAU_POD'),
        'TABLEAU_SITE': os.getenv('TABLEAU_SITE'),
        'TABLEAU_PROJECT_1': os.getenv('TABLEAU_PROJECT_1'),
        'TABLEAU_PROJECT_2': os.getenv('TABLEAU_PROJECT_2'),
        'TABLEAU_API_VERSION': os.getenv('TABLEAU_API_VERSION')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
    
    return TableauConfig(
        pod=required_vars['TABLEAU_POD'],
        site=required_vars['TABLEAU_SITE'],
        project_1=required_vars['TABLEAU_PROJECT_1'],
        project_2=required_vars['TABLEAU_PROJECT_2'],
        api_version=required_vars['TABLEAU_API_VERSION']
    )

def get_tableau_auth() -> Tuple[str, str]:
    """
    Get authentication token and site ID from Tableau using Connected App.
    
    Returns:
        Tuple[str, str]: A tuple containing (token, site_id) from the authentication response.
    """
    auth_config = ca_auth.load_config()
    jwt_token = ca_auth.generate_jwt_token(auth_config)
    auth_response = ca_auth.authenticate_with_tableau(jwt_token, auth_config)
    return auth_response['token'], auth_response['site_id']

def get_workbooks(config: TableauConfig, token: str, site_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve workbooks from Tableau server for specified projects.

    Args:
        config (TableauConfig): Configuration data for Tableau API.
        token (str): Authentication token for Tableau API.
        site_id (str): Site ID (LUID) from authentication response.

    Returns:
        List[Dict[str, Any]]: List of workbook dictionaries containing workbook information.

    Raises:
        requests.exceptions.RequestException: If the API request fails.
        ValueError: If the response status code is not 200.
    """
    logger.info("Retrieving workbooks for site ID: %s", site_id)

    # Construct the API URL
    ts_url = f"https://{config.pod}/api/{config.api_version}/sites/{site_id}/workbooks"
    
    # Set up headers with authentication token
    headers = {
        'X-tableau-auth': token,
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }

    # Prepare project filter
    projects = f'[{config.project_1},{config.project_2}]'

    # Set up query parameters
    params = {
        'pageSize': '100',
        'pageNumber': '1',
        'filter': f'projectName:in:{projects}'
    }

    params_string = urllib.parse.urlencode(params)
    
    try:
        # Create a session with SSL verification disabled
        session = requests.Session()
        session.verify = False
        
        response = session.get(ts_url, headers=headers, params=params_string)
        response.raise_for_status()
        
        if response.status_code == 200:
            logger.info('Received status code: %s', response.status_code)
            resp = response.json()
            logger.info('Response content: %s', json.dumps(resp, indent=4))
            return resp['workbooks']['workbook']
        else:
            raise ValueError(f"Unexpected status code: {response.status_code}")
            
    except requests.exceptions.RequestException as e:
        logger.error("Failed to retrieve workbooks: %s", str(e))
        if hasattr(e, 'response') and e.response is not None:
            logger.error("Response status code: %s", e.response.status_code)
            logger.error("Response text: %s", e.response.text)
        raise
    finally:
        session.close()

def main() -> None:
    """Main execution function."""
    try:
        config = load_config()
        token, site_id = get_tableau_auth()
        
        workbooks = get_workbooks(config, token, site_id)
        logger.info("Retrieved %d workbooks", len(workbooks))
        
    except Exception as e:
        logger.error("Application error: %s", str(e))
        raise

if __name__ == "__main__":
    main()
