# Filter-Email

# Email Processing Scripts

This project provides two Python scripts:

1. `authenticate.py` - Authenticates a Gmail account using OAuth2 and fetches emails based on provided filters.
2. `perform_actions.py` - Performs actions like marking emails as read/unread, moving emails to trash/spam, etc., based on rules defined in a `rules.json` file.

OAuth2 Setup: Get Your Google Client Credentials

To enable OAuth2 authentication for accessing Gmail APIs, follow these steps:

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project or select an existing one.
3. Enable the **Gmail API**:
   - Go to **APIs & Services > Library**.
   - Search for "Gmail API" and enable it.
4. Set up the **OAuth consent screen**:
   - Choose **External** for user type.
   - Fill out the required fields (App name, support email, etc.).
   - Add scopes - It is under Data Access sub tab.
5. Create OAuth 2.0 credentials:
   - Go to **APIs & Services > Credentials**.
   - Click **+ Create Credentials > OAuth client ID**.
   - Choose **Desktop App** as application type.
   - Download the client secret json file.
6. Enter the correspinsing email account as a test user under `Audience` as a test user.

Make sure to include the following scopes when setting up OAuth:

1. https://www.googleapis.com/auth/gmail.readonly
2. https://www.googleapis.com/auth/gmail.modify
3. https://mail.google.com

Set Up Instructions:

1. Clone the Repository - git@github.com:SAGNICKMAJUMDAR/Filter-Email.git
2. Create a virtual environment - `python3 -m venv {name}`
3. Activate the virtual environment - `source {name}/bin/activate`  
4. Install PostgreSQL - run the follwing commands

```
  brew install postgresql@13
  brew services start postgresql@13
```
5. Start celery worker and celery beta for the back groung tasks to run

   ```
     celery -A {file_name} worker --loglevel=info
     celery -A {file_name} beat --loglevel=info
   ```

   `file_name - worker`

Run Authentication Script:

`python authenticate.py --help`

Example Usage:

`python authenticate.py --credentials client_secret.json --limit 10`

Run the Action Script:

`python perform_actions.py --help`

Example Usage:
`python perform_actions.py --rules rules.json --email user@example.com`

Project Requirements:

```
postgresql==13.21
sqlalchemy==1.4.0
psycopg2==2.9.10
psycopg2-binary==2.9.9
python-dotenv==1.1.0
google-api-python-client
google-auth-oauthlib
google-auth-httplib2
python-dateutil
celery
redis
```