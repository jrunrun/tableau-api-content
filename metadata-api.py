import requests
import json
import logging
from typing import Dict, Any, Optional
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

def get_tableau_token() -> str:
    """
    Get authentication token from Tableau using Connected App.
    
    Returns:
        str: Tableau REST API authentication token.
    """
    auth_config = ca_auth.load_config()
    jwt_token = ca_auth.generate_jwt_token(auth_config)
    auth_response = ca_auth.authenticate_with_tableau(jwt_token, auth_config)
    return auth_response['token']

def get_tableau_content(tableau_pod: str, token: str, query: str, variables: Dict[str, str], api_version: str) -> Dict[str, Any]:
    """
    Fetch content from Tableau Metadata API using GraphQL.
    
    Args:
        tableau_pod (str): Tableau pod URL
        token (str): Authentication token
        query (str): GraphQL query string
        variables (Dict[str, str]): Variables for the GraphQL query
        api_version (str): Tableau API version (not used in URL)
        
    Returns:
        Dict[str, Any]: Response content from the Tableau API
        
    Raises:
        requests.exceptions.RequestException: If the API request fails
        ValueError: If the response status code indicates an error
    """

    TABLEAU_METADATA_API = "metadata/graphql"

    tableau_url = f"https://{tableau_pod}/api/{TABLEAU_METADATA_API}"
    
    headers = {
        'X-tableau-auth': token,
        'Content-Type': 'application/json'
    }
    
    try:
        # Create a session with SSL verification disabled
        session = requests.Session()
        session.verify = False
        
        response = session.post(
            tableau_url,
            json={'query': query, 'variables': variables},
            headers=headers
        )
        
        response.raise_for_status()
        response_content = response.json()
        logger.info(f"Received status code: {response.status_code}")
        
        # Print the response content in a readable format
        print("\nResponse Content:")
        print(json.dumps(response_content, indent=2))
        
        return response_content
        
    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        if hasattr(e.response, 'status_code'):
            if e.response.status_code == 401:
                logger.error("Authentication failed")
            elif e.response.status_code == 500:
                logger.error("Pod error occurred")
        raise
    finally:
        session.close()

def main() -> None:
    """Main execution function."""
    try:
        config = load_config()
        token = get_tableau_token()
        
        query = """
        query tableauContent($tableau_site: String, $tableau_project_1: String, $tableau_project_2: String) {
            tableauSites(filter: {
                name: $tableau_site
            }) {
                name
                luid
                publishedDatasources(filter: {
                    projectNameWithin: [$tableau_project_1, $tableau_project_2]
                }) {
                    name
                    luid
                    projectName
                    isCertified
                    vizportalUrlId
                }
                workbooks(filter: {
                    projectNameWithin: [$tableau_project_1, $tableau_project_2]
                }) {
                    name
                    luid
                    createdAt
                    projectName
                    views {
                        name
                        path
                        luid
                        createdAt
                        __typename
                    }
                }
            }
        }
        """
        
        variables = {
            'tableau_site': config.site,
            'tableau_project_1': config.project_1,
            'tableau_project_2': config.project_2
        }
        
        content = get_tableau_content(config.pod, token, query, variables, config.api_version)
        return content
        
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        raise

if __name__ == "__main__":
    main()