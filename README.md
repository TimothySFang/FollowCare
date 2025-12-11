# FollowCare

An Multi-Agent dental appointment follow-up system that automatically sends check-in messages to patients based on a recent patient treatment, analyzes their responses, assesses risk levels, flags risky cases for manual inspection and generates personalized care instructions.

## Features

- **AI-Powered Analysis**: Uses OpenAI GPT models to analyze patient responses
- **SMS Integration**: Send and receive SMS messages via Twilio
- **Risk Assessment**: Automatically assess patient risk levels based on symptoms
- **Streamlit Web Interface**: Interactive web app for managing patient follow-ups
- **Automated Workflow**: Complete workflow from check-in to care instructions

## Prerequisites

- Python 3.12 or higher
- OpenAI API key
- Twilio account with:
  - Account SID
  - Auth Token
  - Phone number (for sending/receiving SMS)
- ngrok account (for webhook tunneling - free tier works)

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd Automated-Appointment-Followup
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate

# On Windows:
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install from requirements.txt
pip install -r requirements.txt

# Or install individually:
# pip install openai flask streamlit twilio pyngrok python-dotenv requests
```

### 4. Get API Keys

#### OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Sign up or log in
3. Navigate to [API Keys](https://platform.openai.com/account/api-keys)
4. Click "Create new secret key"
5. Copy the key (it starts with `sk-proj-` or `sk-`)
6. **Important**: Save it immediately - you won't be able to see it again!

#### Twilio Credentials

1. Go to [Twilio Console](https://console.twilio.com/)
2. Sign up for a free account (or log in)
3. Get your **Account SID** from the dashboard
4. Get your **Auth Token** from the dashboard (click to reveal)
5. Get a **Phone Number**:
   - Go to Phone Numbers → Manage → Active Numbers
   - If you don't have one, buy a number (free trial includes credits)
   - Copy the phone number (include country code, e.g., `+1234567890`)

#### ngrok Setup

1. Sign up at [ngrok](https://ngrok.com/) (free account works)
2. Get your authtoken from the dashboard
3. Install ngrok (if not using pyngrok):
   ```bash
   # macOS
   brew install ngrok
   
   # Or download from https://ngrok.com/download
   ```
4. Authenticate (if using standalone ngrok):
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

### 5. Create `.env` File

Create a `.env` file in the project root directory:

```bash
touch .env
```

Open the `.env` file and add your credentials:

```env
# OpenAI API Key
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here

# Twilio Credentials
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

**Important Notes:**
- Replace all placeholder values with your actual credentials
- No quotes around values
- No spaces around the `=` sign
- The phone number must include country code (e.g., `+1` for US)

### 6. Configure Twilio Webhook

After starting the backend server (see below), you'll need to configure Twilio to send incoming messages to your webhook:

1. Start the `sms_webhook.py` server (see Running the Application)
2. Copy the ngrok URL that appears in the terminal (e.g., `https://xxxxx.ngrok-free.app`)
3. Go to [Twilio Console → Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming)
4. Click on your phone number
5. Scroll to "Messaging Configuration"
6. Under "A message comes in", set:
   - **Webhook URL**: `https://YOUR-NGROK-URL.ngrok-free.app/sms`
   - **HTTP Method**: `POST`
7. Click "Save"

**Note**: Every time you restart the webhook server, ngrok generates a new URL. You'll need to update the Twilio webhook URL each time.

## Running the Application

The application consists of two main components that need to run simultaneously:

### 1. Backend Webhook Server (SMS Handler)

This server receives incoming SMS messages from Twilio and saves them to `patient_responses.json`.

**Terminal 1 - Start the webhook server:**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the webhook server
python sms_webhook.py
```

You should see output like:
```
 * ngrok tunnel "https://xxxxx.ngrok-free.app" -> "http://127.0.0.1:5000"
 * Running on http://127.0.0.1:5000
```

**Important**: Copy the ngrok URL and update your Twilio webhook configuration (see step 6 above).

### 2. Streamlit Web Application

This is the main user interface for managing patient follow-ups.

**Terminal 2 - Start Streamlit:**

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run Streamlit
streamlit run streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Basic Workflow

1. **Create a Patient**:
   - In the Streamlit sidebar, fill in patient information
   - Click "Create/Update Patient"

2. **Generate Check-In Message**:
   - Go to the "Check-In Message" tab
   - Click "Generate Check-In Message"
   - Review the generated message
   - Click "Send SMS to Patient" (if phone number is provided)

3. **Receive Patient Response**:
   - Patient responds via SMS
   - Response is automatically saved by the webhook server
   - In Streamlit, go to "Patient Responses" tab
   - Click "Check for New Responses" or enable auto-refresh

4. **Analyze Response**:
   - The app can automatically analyze responses
   - Or manually analyze in the "Symptom Analysis" tab

5. **Review Risk Assessment**:
   - Check the "Risk Assessment" tab for risk level

6. **Generate Care Instructions**:
   - Review and send care instructions to the patient

7. **View Clinic Summary**:
   - See the complete summary for clinic records

### Command-Line Demo

You can also run a command-line demo:

```bash
python main.py
```

This runs a complete workflow with sample data.

## Project Structure

```
Automated-Appointment-Followup/
├── agents/              # AI agents for different tasks
│   ├── base_agent.py
│   ├── symptom_checkin.py
│   ├── response_analyzer.py
│   ├── risk_assessment.py
│   ├── care_instruction.py
│   └── summary.py
├── models/              # Data models
│   └── patient.py
├── services/            # External services
│   └── sms_service.py
├── config.py            # Configuration settings
├── main.py              # Command-line demo
├── streamlit_app.py     # Streamlit web application
├── sms_webhook.py       # Flask webhook server
├── patient_responses.json  # Patient response storage
└── .env                 # Environment variables (not in git)
```

## Troubleshooting

### API Key Issues

- **Error: "Incorrect API key provided"**
  - Check your `.env` file has the correct key
  - Make sure there are no quotes or spaces around the key
  - Verify the key is active at [OpenAI Platform](https://platform.openai.com/account/api-keys)

### Webhook Not Receiving Messages

- **Check if webhook server is running**: Look for the ngrok URL in terminal
- **Verify Twilio webhook URL**: Must match current ngrok URL + `/sms`
- **Check ngrok URL hasn't changed**: Restarting the server generates a new URL
- **Test webhook**: Visit `https://YOUR-NGROK-URL.ngrok-free.app/test-webhook` in browser

### Environment Variables Not Loading

- Make sure `.env` file is in the project root
- Verify `load_dotenv()` is called in your scripts
- Check for typos in variable names (case-sensitive)
- Restart your application after changing `.env`

### Port Already in Use

If port 5000 is already in use:
- Change port in `sms_webhook.py`: `app.run(port=5001)`
- Update ngrok connection: `ngrok.connect(5001)`
- Update Streamlit to use new port in API calls

## Development

### Adding New Agents

1. Create a new file in `agents/`
2. Inherit from `BaseAgent`
3. Implement the `process()` method
4. Add to imports in `streamlit_app.py` and `main.py`

### Testing

Test individual components:
```bash
# Test environment variables
python test_env.py

# Test API key loading
python test_key.py
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues or questions, please [open an issue](link-to-issues) or contact [your contact info].

