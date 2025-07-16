# Google Sheets Setup Guide

## Prerequisites
1. A Google account
2. Your attendance tracking spreadsheet in Google Sheets

## Step 1: Get Your Spreadsheet ID

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID_HERE/edit`
3. Copy the ID (the long string between `/d/` and `/edit`)
4. Update `config/config.json`:
   ```json
   "spreadsheet_id": "paste-your-id-here"
   ```

## Step 2: Enable Google Sheets API

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing one)
3. Click "Enable APIs and Services"
4. Search for "Google Sheets API"
5. Click on it and press "Enable"

## Step 3: Create Credentials

1. In the Google Cloud Console, go to "Credentials"
2. Click "+ CREATE CREDENTIALS" → "OAuth client ID"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" (unless using G Suite)
   - Fill in required fields (app name, email)
   - Add your email as a test user
4. Back in credentials, create OAuth client ID:
   - Application type: "Desktop app"
   - Name: "TP NFC Attendance"
5. Download the credentials JSON file
6. Save it as `config/credentials.json` in your project

## Step 4: Spreadsheet Format

Your Google Sheet should have these columns:
- **A**: originalid (number)
- **B**: firstname (text)
- **C**: lastname (text)
- **D**: reception (check-in time or X)
- **E**: lio (check-in time or X)
- **F**: juntos (check-in time or X)
- **G**: experimental (check-in time or X)
- **H**: unvrs (check-in time or X)

Example:
```
originalid | firstname | lastname | reception | lio | juntos | experimental | unvrs
1001       | John      | Doe      |           |     |        |              |
1002       | Jane      | Smith    |           |     |        |              |
```

## Step 5: Test Connection

Run: `test_sheets.bat`

On first run, it will:
1. Open your browser for Google authentication
2. Ask you to sign in and authorize the app
3. Create a token file for future use

## Troubleshooting

**"Credentials file not found"**
- Make sure `config/credentials.json` exists
- Check the path in config.json

**"Access blocked: This app's request is invalid"**
- Add yourself as a test user in OAuth consent screen
- Make sure the app is in "Testing" status

**"No data found in spreadsheet"**
- Check that your sheet has the correct column headers
- Verify the sheet name in config.json (default: "Sheet1")