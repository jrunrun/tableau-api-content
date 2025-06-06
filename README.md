# tableau-api-content

This project provides Python utilities for interacting with the Tableau API, including both REST API and Metadata API functionality.

## Features

- Tableau Connected App authentication
- REST API integration for workbook retrieval
- Metadata API integration using GraphQL
- Environment-based configuration
- Comprehensive error handling and logging

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd tableau-api-content
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   # Using venv
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and fill in your actual values:
   - `CONNECTED_APP_CLIENT_ID`: Your Tableau Connected App client ID
   - `CONNECTED_APP_SECRET_KEY`: Your Connected App secret key
   - `CONNECTED_APP_SECRET_ID`: Your Connected App secret ID
   - `TABLEAU_USER`: Your Tableau user email
   - `TABLEAU_POD`: Your Tableau pod URL (e.g., 'your-pod.tableau.com')
   - `TABLEAU_SITE`: Your Tableau site name
   - `TABLEAU_PROJECT_1`: Primary project name to filter workbooks
   - `TABLEAU_PROJECT_2`: Secondary project name to filter workbooks
   - `TABLEAU_API_VERSION`: Tableau API version (e.g., '3.19')

3. Never commit your `.env` file to version control.

## Usage

### REST API

The REST API module (`rest-api.py`) provides functionality to retrieve workbooks from your Tableau server:

```python
from rest_api import load_config, get_tableau_auth, get_workbooks

# Load configuration
config = load_config()

# Get authentication token and site ID
token, site_id = get_tableau_auth()

# Retrieve workbooks
workbooks = get_workbooks(config, token, site_id)
```

### Metadata API

The Metadata API module (`metadata-api.py`) provides GraphQL-based access to Tableau metadata:

```python
from metadata_api import load_config, get_tableau_token, get_tableau_content

# Load configuration
config = load_config()

# Get authentication token
token = get_tableau_token()

# Define your GraphQL query and variables
query = """
query tableauContent($tableau_site: String, $tableau_project_1: String, $tableau_project_2: String) {
    tableauSites(filter: { name: $tableau_site }) {
        name
        luid
        workbooks(filter: { projectNameWithin: [$tableau_project_1, $tableau_project_2] }) {
            name
            luid
            projectName
        }
    }
}
"""

variables = {
    'tableau_site': config.site,
    'tableau_project_1': config.project_1,
    'tableau_project_2': config.project_2
}

# Get content
content = get_tableau_content(config.pod, token, query, variables, config.api_version)
```

## Error Handling

Both modules include comprehensive error handling:
- Authentication failures
- API request errors
- Configuration validation
- Response validation

All errors are logged with detailed context for debugging.

## Dependencies

The project uses the following dependencies (specified in `requirements.txt`):

- requests>=2.31.0: For making HTTP requests to Tableau APIs
- PyJWT>=2.8.0: For JWT token generation and validation
- python-dotenv>=1.0.0: For loading environment variables
- typing-extensions>=4.8.0: For enhanced type hints
- python-json-logger>=2.0.7: For structured JSON logging

To update dependencies to their latest compatible versions:
```bash
pip install --upgrade -r requirements.txt
```

To generate a new requirements.txt with exact versions:
```bash
pip freeze > requirements.txt
```

## Security Notes

1. SSL verification is disabled for development purposes. In production, you should:
   - Enable SSL verification
   - Use proper certificate validation
   - Implement proper token management

2. Authentication tokens are short-lived and should be refreshed as needed.

3. Never expose your Connected App credentials in code or version control.