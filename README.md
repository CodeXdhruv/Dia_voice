# 🌸 DIA Voice Therapy API

A compassionate AI-powered voice therapy service that provides emotional support, reflective guidance, and mental wellness conversations through real-time voice interactions.

## Features

- **🎙️ Real-time Voice Therapy**: Live conversations with DIA Therapist
- **💜 Empathetic AI**: Specially trained for mental wellness support
- **🔒 Privacy-First**: No conversation storage or data persistence
- **🌐 WebSocket-Based**: Low-latency real-time audio streaming
- **📱 Cross-Platform**: Works on web, mobile, and desktop applications

## What DIA Therapist Offers

- **Emotional Support**: Non-judgmental listening and validation
- **Coping Strategies**: Practical techniques for stress, anxiety, and emotional challenges
- **Reflective Guidance**: Gentle questions to promote self-awareness
- **Mental Wellness**: Mindfulness tips and grounding techniques
- **Crisis Awareness**: Guides users to professional help when needed

## Quick Start

### Prerequisites

1. **Gemini API Key**: Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
2. **Python 3.8+**: Make sure Python is installed
3. **Git**: For cloning the repository

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <your-repo-url>
   cd diavoice-api
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set environment variables**:
   ```bash
   # Windows
   set GEMINI_API_KEY=your_gemini_api_key_here
   set PORT=5000
   
   # Linux/Mac
   export GEMINI_API_KEY=your_gemini_api_key_here
   export PORT=5000
   ```

4. **Run the application**:
   ```bash
   python app.py
   ```

5. **Test the API**:
   - Open your browser to `http://localhost:5000`
   - Use the test client at `test_client.html`

## API Endpoints

### `POST /start_voice`
Initiates a new therapy session and returns WebSocket connection details.

**Response:**
```json
{
  "status": "started",
  "websocket": {
    "url": "wss://your-domain.com/audio-stream",
    "protocol": "audio-stream"
  }
}
```

### `POST /terminate_voice`
Terminates an active therapy session and cleans up resources.

**Response:**
```json
{
  "status": "terminated"
}
```

### `GET /status`
Returns API health status and version information.

**Response:**
```json
{
  "status": "ok",
  "vercel": false,
  "version": "1.0.0"
}
```

### WebSocket `/audio-stream`
Real-time audio streaming endpoint for voice communication.

**Message Format:**
```json
{
  "type": "audio",
  "format": "audio/pcm",
  "data": "base64_encoded_audio_data"
}
```

## Deployment Guide

### Option 1: Render (Recommended for Free Tier)

1. **Create a Render account** at [render.com](https://render.com)

2. **Create a new Web Service**:
   - Connect your GitHub repository
   - Choose "Web Service"
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `python app.py`

3. **Set environment variables**:
   - `GEMINI_API_KEY`: Your Gemini API key
   - `PORT`: Will be automatically set by Render

4. **Deploy**:
   - Click "Create Web Service"
   - Render will automatically deploy your app
   - Your API will be available at `https://diavoice.onrender.com`

### Option 2: Railway (Fast & Easy)

1. **Create a Railway account** at [railway.app](https://railway.app)

2. **Deploy from GitHub**:
   - Click "New Project"
   - Choose "Deploy from GitHub repo"
   - Select your repository

3. **Set environment variables**:
   - Go to your project settings
   - Add `GEMINI_API_KEY` with your API key

4. **Deploy**:
   - Railway will automatically detect Python and deploy
   - Your API will be available at the provided Railway URL

### Option 3: Heroku (Classic Option)

1. **Create a Heroku account** and install Heroku CLI

2. **Create a new Heroku app**:
   ```bash
   heroku create diavoice-therapy
   ```

3. **Set environment variables**:
   ```bash
   heroku config:set GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Deploy**:
   ```bash
   git add .
   git commit -m "Deploy DIA Voice Therapy API"
   git push heroku main
   ```

### Custom Domain Setup

Once deployed, you can:
1. Purchase a domain like `diavoice.com`
2. Configure DNS to point to your deployment
3. Update SSL certificates for HTTPS
4. Update WebSocket URLs to use your custom domain

## Step-by-Step Deployment Instructions

### For Beginners:

1. **Get Your API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Sign in with your Google account
   - Click "Create API Key"
   - Copy the key (keep it safe!)

2. **Prepare Your Code**:
   ```bash
   # Create a new folder
   mkdir diavoice-api
   cd diavoice-api
   
   # Copy your app.py, requirements.txt, and test_client.html files here
   ```

3. **Deploy to Render** (Free Option):
   - Create GitHub repository with your code
   - Go to [render.com](https://render.com) and sign up
   - Click "New +" → "Web Service"
   - Connect to your GitHub repo
   - Set these values:
     - Name: `diavoice`
     - Build Command: `pip install -r requirements.txt`
     - Start Command: `python app.py`
   - Add environment variable: `GEMINI_API_KEY` = your API key
   - Click "Create Web Service"

4. **Test Your Deployment**:
   - Wait for deployment to complete
   - Visit your Render URL (e.g., `https://diavoice.onrender.com`)
   - Open the test client and try a conversation

## Configuration

### Audio Settings
- **Format**: 16-bit PCM
- **Channels**: 1 (Mono)
- **Sample Rate**: 16000 Hz (input), 24000 Hz (output)
- **Encoding**: Base64 for WebSocket transmission

### Environment Variables
- `GEMINI_API_KEY`: Your Google Gemini API key (required)
- `PORT`: Server port (optional, defaults to 5000)
- `VERCEL`: Automatically set in Vercel deployments

## Usage Examples

### JavaScript Client
```javascript
const API_URL = 'https://diavoice.onrender.com';

// Start therapy session
const response = await fetch(`${API_URL}/start_voice`, {
  method: 'POST'
});
const data = await response.json();

// Connect to WebSocket
const websocket = new WebSocket(data.websocket.url);
websocket.onopen = () => console.log('Connected to DIA Therapist');
```

### Python Client
```python
import requests
import websocket

# Start session
response = requests.post('https://diavoice.onrender.com/start_voice')
data = response.json()

# Connect to WebSocket
ws = websocket.create_connection(data['websocket']['url'])
print("Connected to DIA Therapist")
```

## Security & Privacy

- **No Data Storage**: Conversations are not stored or logged
- **Encrypted Connections**: All communications use HTTPS/WSS
- **API Key Security**: Environment variables protect sensitive keys
- **CORS Enabled**: Configurable cross-origin resource sharing
- **Rate Limiting**: Built-in protection against abuse

## Crisis Support

DIA Therapist is trained to recognize signs of distress and will:
- Gently encourage seeking professional help
- Provide crisis helpline information when appropriate
- Maintain a supportive, non-judgmental tone
- Never store or recall sensitive personal information

## Important Disclaimers

⚠️ **DIA Therapist is not a replacement for professional mental health care**

- This service provides supportive conversations, not medical advice
- For severe distress or mental health crises, please contact:
  - National Suicide Prevention Lifeline: 988 (US)
  - Crisis Text Line: Text HOME to 741741
  - Your local emergency services: 911
  - A qualified mental health professional

## Troubleshooting

### Common Issues

1. **"WebSocket connection failed"**:
   - Check if your deployment is running
   - Verify the WebSocket URL is correct
   - Ensure your browser supports WebSocket

2. **"API key error"**:
   - Verify your Gemini API key is correct
   - Check that the environment variable is set
   - Make sure the API key has proper permissions

3. **"Microphone not working"**:
   - Allow microphone permissions in your browser
   - Check your device's audio settings
   - Try refreshing the page

4. **"No audio response"**:
   - Check your internet connection
   - Verify the API is responding
   - Look at browser console for errors

## Support

For technical support or questions about the API:
- Create an issue in this repository
- Check the API documentation at your deployed URL
- Review the test client for implementation examples

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---

Made with 💜 for mental wellness | DIA Voice Therapy

*Remember: You are worthy of care, support, and healing. 🌸*
