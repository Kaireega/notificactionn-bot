# OANDA API Setup Guide

## Problem
You're getting "Insufficient authorization to perform request" errors when trying to fetch candle data from the OANDA API.

## Solution

### Step 1: Get Your OANDA API Credentials

1. **Log into your OANDA account**
   - Go to https://www.oanda.com/
   - Sign in to your account

2. **Navigate to API Access**
   - Go to Account > API Access
   - Or visit: https://www.oanda.com/account/api-access

3. **Generate a new API key**
   - Click "Generate API Key"
   - Give it a descriptive name (e.g., "Trading Bot")
   - Copy the API key (it will look like: `vjyvjy683522416767b6aa4465f666f6b-7eda7211ed563893626f489acf155f06`)

4. **Get your Account ID**
   - In the same API Access section, you'll see your Account ID
   - It will look like: `897-001-23541205-098`

### Step 2: Configure Your Credentials

You have two options to configure your API credentials:

#### Option A: Use the config.env file (Recommended)

1. Edit the `config.env` file in the root directory:
```bash
nano config.env
```

2. Replace the placeholder values with your actual credentials:
```env
OANDA_API_KEY=your_actual_api_key_here
OANDA_ACCOUNT_ID=your_actual_account_id_here
OANDA_URL=https://api-fxpractice.oanda.com/v3
```

#### Option B: Set Environment Variables

```bash
export OANDA_API_KEY="your_actual_api_key_here"
export OANDA_ACCOUNT_ID="your_actual_account_id_here"
export OANDA_URL="https://api-fxpractice.oanda.com/v3"
```

### Step 3: Test Your Credentials

Run the test script to verify your credentials work:

```bash
python3 test_api_credentials.py
```

You should see output like:
```
🔍 Testing OANDA API credentials...
API URL: https://api-fxpractice.oanda.com/v3
Account ID: 887-001-23541205-876
API Key: a003d6835...acf155f06
--------------------------------------------------
Testing account access...
✅ Account access successful!

Testing account summary...
✅ Account summary retrieved successfully!
Account Name: Your Account Name
Account Currency: USD
Balance: 10000.0000

Testing instruments access...
✅ Retrieved 123 instruments
```

### Step 4: Run Your Application

Once the credentials are working, you can run your main application:

```bash
python3 main.py
```

## Troubleshooting

### Common Issues

1. **"Insufficient authorization" error**
   - Your API key is invalid or expired
   - Your account ID is incorrect
   - Your OANDA account doesn't have API access enabled

2. **"Account not found" error**
   - Check your Account ID
   - Make sure you're using the correct API URL (practice vs live)

3. **"Invalid API key" error**
   - Generate a new API key
   - Make sure you copied the entire key correctly

### API URLs

- **Practice Account**: `https://api-fxpractice.oanda.com/v3`
- **Live Account**: `https://api-fxtrade.oanda.com/v3`

### Getting Help

If you're still having issues:

1. Check the OANDA API documentation: https://developer.oanda.com/
2. Verify your account status in the OANDA dashboard
3. Contact OANDA support if your account has API access issues

## Security Notes

- Never commit your API credentials to version control
- The `config.env` file is already in `.gitignore` to prevent accidental commits
- Consider using a practice account for testing
- Regularly rotate your API keys for security 