# tableau-api-content

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
   - `TABLEAU_AUTH_URL`: Tableau authentication URL (default provided)
   - `TABLEAU_SITE_CONTENT_URL`: Your Tableau site content URL

3. Never commit your `.env` file to version control.