"""
DIA Voice API - A compassionate voice therapy API powered by Gemini AI.

This file provides a complete voice-based therapeutic assistant for mental wellness support.
"""
import os
import sys
import json
import time
import base64
import asyncio
import logging
import concurrent.futures
import traceback
from threading import Thread, Lock
from typing import Dict, Any, Optional, List

# Flask imports
from flask import Flask, jsonify, render_template_string, request
from flask_cors import CORS
from flask_sock import Sock

# Google Gemini imports
from google import genai
try:
    from google.genai import types
    TYPES_AVAILABLE = True
except ImportError:
    TYPES_AVAILABLE = False

# WebSocket handling
import websockets
from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ==== Configuration Settings ====

# API Key should be set as an environment variable
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    logger.warning("No GEMINI_API_KEY found in environment variables!")

# Audio settings
FORMAT = 16  # 16-bit PCM
CHANNELS = 1  # Mono
SEND_SAMPLE_RATE = 16000
RECEIVE_SAMPLE_RATE = 24000
CHUNK_SIZE = 1024
MODEL = "models/gemini-2.0-flash-live-001"

# Connection settings
CONNECTION_TIMEOUT = 30.0
MAX_RETRIES = 3
RETRY_DELAY = 1.0
PORT = int(os.getenv("PORT", 5000))

# Vercel compatibility check
IN_VERCEL = 'VERCEL' in os.environ or 'AWS_LAMBDA_FUNCTION_NAME' in os.environ

# System prompt for Gemini
SYSTEM_INSTRUCTION = """
You are DIA, a compassionate and empathetic virtual therapist designed to offer conversational support, reflective guidance, and emotional validation. Your primary role is to engage in gentle, non-judgmental, and mentally safe conversations.

You are NOT a medical professional, but you can provide support, perspective, and helpful coping strategies in areas like stress, anxiety, overthinking, self-esteem, relationships, loneliness, life purpose, and emotional burnout.

## Behavioral Guidelines:
- Always speak in a calm, soothing, and emotionally supportive tone.
- Avoid giving absolute answers or diagnoses. Instead, encourage self-reflection.
- Use inclusive and non-harmful language. Never assume identity, background, or beliefs.
- Avoid controversial, political, or religious opinions unless asked, and respond with sensitivity.
- If a user is in distress or hints at self-harm or suicidal thoughts, gently encourage them to seek help from a real mental health professional or helpline.
- You can ask gentle follow-up questions like "Would you like to talk more about that?" or "How has that been affecting you lately?"

## Communication Style:
- Use simple, comforting, and emotionally intelligent language.
- Give examples of grounding techniques, journaling prompts, or mindfulness tips when appropriate.
- Avoid triggering or emotionally charged phrases. Prioritize psychological safety above all.
- Show empathy. Phrases like:
  - "That sounds really tough. I'm here to listen."
  - "It's okay to feel this way. You're not alone."
  - "You've shown a lot of strength by sharing that."

## Output Format:
- Always reply with warmth and without judgment.
- If unsure, offer neutral responses that affirm the user's emotions and invite further sharing.

## Ethics & Safety:
- Never store, recall, or reference past personal user data.
- Do not offer medical, legal, or crisis advice.
- Avoid jokes, sarcasm, or anything that could be misinterpreted as dismissive or harmful.
- Always promote emotional resilience, self-acceptance, and seeking human support when needed.

You are a caring voice that supports mental wellness, not a replacement for therapy.

Begin each interaction with compassion. Your words may be the only support someone receives today.
Wait for user to speak and then give response
"""

# HTML template for the home page 
HOME_PAGE_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DIA Voice Therapy API</title>
    <style>
        body {
            font-family: 'Arial', sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
            line-height: 1.6;
            color: #333;
            background-color: #fefefe;
        }
        h1 {
            color: #6366f1;
            border-bottom: 3px solid #6366f1;
            padding-bottom: 10px;
            text-align: center;
        }
        h2 {
            color: #8b5cf6;
            margin-top: 30px;
        }
        h3 {
            color: #a855f7;
            margin-top: 25px;
        }
        .endpoint {
            background: #f8faff;
            border-left: 6px solid #8b5cf6;
            padding: 1rem;
            margin: 1rem 0;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .method {
            font-weight: bold;
            background: #6366f1;
            color: white;
            padding: 0.3rem 0.6rem;
            border-radius: 6px;
            display: inline-block;
        }
        pre {
            background: #f1f5f9;
            padding: 1rem;
            border-radius: 6px;
            overflow: auto;
            max-height: 400px;
            font-size: 14px;
            border: 1px solid #e2e8f0;
        }
        code {
            font-family: 'Consolas', 'Monaco', monospace;
            background: #e0e7ff;
            padding: 3px 6px;
            border-radius: 4px;
            color: #5b21b6;
        }
        .intro {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 12px;
            margin: 2rem 0;
            text-align: center;
        }
        .intro h2 {
            color: white;
            margin-top: 0;
        }
        .tabs {
            display: flex;
            border-bottom: 1px solid #e2e8f0;
            margin-top: 15px;
        }
        .tab {
            padding: 8px 16px;
            cursor: pointer;
            background: #f1f5f9;
            border: 1px solid #e2e8f0;
            border-bottom: none;
            border-radius: 4px 4px 0 0;
            margin-right: 4px;
        }
        .tab.active {
            background: #fff;
            font-weight: bold;
            border-bottom: 1px solid #fff;
            margin-bottom: -1px;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        footer {
            margin-top: 50px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            text-align: center;
            font-size: 0.9em;
            color: #64748b;
        }
    </style>
</head>
<body>
    <h1>🌸 DIA Voice Therapy API</h1>
    
    <div class="intro">
        <h2>Compassionate AI-Powered Voice Therapy</h2>
        <p>A safe space for emotional support, reflective guidance, and mental wellness through voice interactions. DIA Therapist provides empathetic conversations using advanced AI technology.</p>
    </div>
    
    <h2>🤝 About DIA Therapist</h2>
    <p>DIA Therapist is an empathetic virtual therapist designed to offer conversational support and emotional validation. While not a replacement for professional therapy, DIA provides:</p>
    <ul>
        <li><strong>Emotional Support:</strong> Non-judgmental listening and validation</li>
        <li><strong>Coping Strategies:</strong> Practical techniques for stress, anxiety, and emotional challenges</li>
        <li><strong>Reflective Guidance:</strong> Gentle questions to promote self-awareness</li>
        <li><strong>Mental Wellness:</strong> Mindfulness tips and grounding techniques</li>
    </ul>
    
    <div style="background: #fef3c7; border-left: 4px solid #f59e0b; padding: 1rem; margin: 1rem 0; border-radius: 4px;">
        <strong>⚠️ Important:</strong> DIA Therapist is not a replacement for professional mental health care. If you're experiencing severe distress or having thoughts of self-harm, please contact a mental health professional or crisis helpline immediately.
    </div>
    
    <h2>API Endpoints</h2>
    
    <div class="endpoint">
        <span class="method">POST</span> <code>{{ base_url }}/start_voice</code>
        <p>Initiates a new voice session with the AI and returns WebSocket connection details.</p>
        <h3>Response:</h3>
        <pre>{
  "status": "started",
  "websocket": {
    "url": "wss://diavoice.onrender.com/audio-stream",
    "protocol": "audio-stream"
  }
}</pre>
    </div>
    
    <div class="endpoint">
        <span class="method">POST</span> <code>{{ base_url }}/terminate_voice</code>
        <p>Terminates an active voice session and cleans up all resources.</p>
        <h3>Response:</h3>
        <pre>{
  "status": "terminated"
}</pre>
    </div>
    
    <div class="endpoint">
        <span class="method">GET</span> <code>{{ base_url }}/status</code>
        <p>Gets the current API status and version information.</p>
        <h3>Response:</h3>
        <pre>{
  "status": "ok",
  "vercel": false,
  "version": "1.0.0"
}</pre>
    </div>

    <h2>🎯 Using the API</h2>
    <p>The typical workflow for connecting to DIA Therapist is:</p>
    <ol>
        <li>Call <code>/start_voice</code> to begin a therapy session</li>
        <li>Connect to the returned WebSocket URL</li>
        <li>Start speaking - your voice will be processed in real-time</li>
        <li>Receive compassionate audio responses from DIA Therapist</li>
        <li>Call <code>/terminate_voice</code> when you're ready to end the session</li>
    </ol>

    <h2>🎙️ Audio Specifications</h2>
    <p>The API expects the following audio specifications for optimal performance:</p>
    <ul>
        <li><strong>Format:</strong> 16-bit PCM</li>
        <li><strong>Channels:</strong> 1 (Mono)</li>
        <li><strong>Sample Rate:</strong> 16000 Hz (sending), 24000 Hz (receiving)</li>
        <li><strong>Encoding:</strong> Base64 for WebSocket transmission</li>
    </ul>

    <h2>💻 Code Examples</h2>
    
    <div class="tabs">
        <div class="tab active" onclick="switchTab(event, 'js')">JavaScript</div>
        <div class="tab" onclick="switchTab(event, 'python')">Python</div>
        <div class="tab" onclick="switchTab(event, 'curl')">cURL</div>
    </div>
    
    <div id="js" class="tab-content active">
        <h3>JavaScript Example</h3>
        <pre>// API endpoint
const API_URL = 'https://diavoice.onrender.com';
let websocket = null;

// Step 1: Start a therapy session
async function startTherapySession() {
  const response = await fetch(`${API_URL}/start_voice`, {
    method: 'POST'
  });
  const data = await response.json();
  
  // Step 2: Connect to the WebSocket with the returned URL
  websocket = new WebSocket(data.websocket.url);
  
  // Step 3: Set up WebSocket event handlers
  websocket.onopen = () => {
    console.log('Connected to DIA Therapist');
    // Get microphone access and start the conversation
    startMicrophone();
  };
  
  websocket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    if (message.type === 'audio') {
      // Play the therapeutic response
      playTherapistResponse(message.data);
    }
  };
}

// Step 4: End the therapy session
async function endTherapySession() {
  if (websocket) websocket.close();
  
  await fetch(`${API_URL}/terminate_voice`, {
    method: 'POST'
  });
  console.log('Therapy session ended');
}</pre>
    </div>
    
    <div id="python" class="tab-content">
        <h3>Python Example</h3>
        <pre>import requests
import websocket
import json
import base64

# API endpoint
API_URL = "https://diavoice.onrender.com"

# Step 1: Start a therapy session
def start_therapy_session():
    response = requests.post(f"{API_URL}/start_voice")
    data = response.json()
    ws_url = data["websocket"]["url"]
    
    # Step 2: Connect to WebSocket
    ws = websocket.create_connection(ws_url)
    print("Connected to DIA Therapist")
    return ws

# Step 3: Send audio data for therapy
def send_audio_to_therapist(ws, audio_data):
    # Convert audio data to base64
    encoded = base64.b64encode(audio_data).decode('utf-8')
    
    # Send to WebSocket
    ws.send(json.dumps({
        "type": "audio",
        "format": "audio/pcm",
        "data": encoded
    }))

# Step 4: Receive therapeutic responses
def receive_therapist_response(ws):
    response = ws.recv()
    data = json.loads(response)
    if data.get("type") == "audio":
        # Process therapeutic audio response
        audio_bytes = base64.b64decode(data["data"])
        # Play the therapeutic response...
        return audio_bytes
    return None

# Step 5: End the therapy session
def end_therapy_session(ws):
    ws.close()
    requests.post(f"{API_URL}/terminate_voice")
    print("Therapy session ended")</pre>
    </div>
    
    <div id="curl" class="tab-content">
        <h3>cURL Examples</h3>
        <pre># Check API status
curl -X GET https://diavoice.onrender.com/status

# Start a therapy session
curl -X POST https://diavoice.onrender.com/start_voice

# Terminate a therapy session
curl -X POST https://diavoice.onrender.com/terminate_voice</pre>
        <p>Note: cURL can only be used for the HTTP endpoints, not for the WebSocket connections which require a WebSocket client.</p>
    </div>
    
    <h2>🛡️ Privacy & Safety</h2>
    <p>DIA Therapist prioritizes your mental wellness and privacy:</p>
    <ul>
        <li><strong>No Data Storage:</strong> Conversations are not stored or recalled</li>
        <li><strong>Confidential:</strong> Each session is private and independent</li>
        <li><strong>Safe Space:</strong> Non-judgmental, inclusive environment</li>
        <li><strong>Crisis Support:</strong> Guided to professional help when needed</li>
    </ul>

    <h2>⚠️ Error Handling</h2>
    <p>The API uses standard HTTP status codes for errors:</p>
    <ul>
        <li><strong>200 OK:</strong> The request succeeded</li>
        <li><strong>400 Bad Request:</strong> Missing or invalid parameters</li>
        <li><strong>401 Unauthorized:</strong> Authentication failed or required</li>
        <li><strong>500 Internal Server Error:</strong> Server-side error</li>
    </ul>

    <h2>📊 Rate Limits</h2>
    <p>To ensure quality therapeutic interactions:</p>
    <ul>
        <li>Maximum of 20 requests per minute per client</li>
        <li>Maximum of 3 concurrent therapy sessions per API key</li>
        <li>Sessions automatically timeout after 60 minutes of inactivity</li>
    </ul>
    
    <footer>
        <p>🍉DIA Voice Therapy🍉</p>
        <p><small>Remember: You are worthy of care, support, and healing. 🌸</small></p>
    </footer>
    
    <script>
        function switchTab(event, tabId) {
            // Hide all tab content
            const tabContents = document.getElementsByClassName('tab-content');
            for (let i = 0; i < tabContents.length; i++) {
                tabContents[i].classList.remove('active');
            }
            
            // Remove active class from all tabs
            const tabs = document.getElementsByClassName('tab');
            for (let i = 0; i < tabs.length; i++) {
                tabs[i].classList.remove('active');
            }
            
            // Show the selected tab content and mark the tab as active
            document.getElementById(tabId).classList.add('active');
            event.currentTarget.classList.add('active');
        }
    </script>
</body>
</html>
"""


# ==== Helper Functions ====

async def run_in_thread(func, *args, **kwargs):
    """Run a function in a separate thread and await its result."""
    loop = asyncio.get_event_loop()
    with concurrent.futures.ThreadPoolExecutor() as pool:
        return await loop.run_in_executor(pool, lambda: func(*args, **kwargs))

def create_wav_header(data_length, sample_rate=24000, channels=1, sample_width=2):
    """Create a WAV header for raw audio data."""
    # RIFF header
    header = bytearray()
    header.extend(b'RIFF')
    header.extend((data_length + 36).to_bytes(4, 'little'))  # 36 + data_length
    header.extend(b'WAVE')
    
    # fmt chunk
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, 'little'))  # Chunk size: 16 for PCM
    header.extend((1).to_bytes(2, 'little'))   # Audio format: 1 for PCM
    header.extend(channels.to_bytes(2, 'little'))  # Channels
    header.extend(sample_rate.to_bytes(4, 'little'))  # Sample rate
    
    # Byte rate: SampleRate * NumChannels * BitsPerSample/8
    byte_rate = sample_rate * channels * sample_width
    header.extend(byte_rate.to_bytes(4, 'little'))
    
    # Block align: NumChannels * BitsPerSample/8
    block_align = channels * sample_width
    header.extend(block_align.to_bytes(2, 'little'))
    
    # Bits per sample
    bits_per_sample = sample_width * 8
    header.extend(bits_per_sample.to_bytes(2, 'little'))
    
    # Data chunk
    header.extend(b'data')
    header.extend(data_length.to_bytes(4, 'little'))
    
    return header


# ==== Gemini Configuration ====

def get_live_connect_config(voice_name="Puck"):
    """Create and return a configuration for Gemini API."""
    # Check if we have the types module available
    if TYPES_AVAILABLE:
        # Use the types module to create LiveConnectConfig
        live_connect_config = types.LiveConnectConfig(
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice_name)
                )
            ),
            system_instruction=types.Content(
                parts=[types.Part.from_text(text=SYSTEM_INSTRUCTION)],
                role="user"
            ),
        )
    else:
        # Fallback to dictionary structure if types not available
        live_connect_config = {
            "response_modalities": ["audio"],
            "speech_config": {
                "voice_config": {
                    "prebuilt_voice_config": {"voice_name": voice_name}
                }
            },
            "system_instruction": {
                "parts": [{"text": SYSTEM_INSTRUCTION}],
                "role": "user"
            }
        }

    # Return a complete config compatible with our processor.py
    return {
        "model": MODEL,
        "live_connect_config": live_connect_config,
        "history": [],
        "generation_config": {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192
        },
        "safety_settings": [
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT", 
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    }


# ==== Audio Processing Class ====

class AudioLoop:
    """
    Handles real-time audio streaming with the Gemini API.
    
    This class manages sending audio data to the Gemini API and 
    receiving responses, handling the two-way communication.
    """
    
    def __init__(self, client):
        """Initialize the AudioLoop with a Gemini client."""
        self.client = client
        self.session = None
        self.is_running = False
        self.audio_in_queue = asyncio.Queue()
        self.out_queue = asyncio.Queue()
        self._processing_task = None
        
        # Check if we're running in a serverless environment
        self.is_serverless = os.environ.get('VERCEL') == '1'

    async def connect_with_retry(self, config: Dict[str, Any], max_retries: int = 3) -> bool:
        """Attempt to connect to the Gemini API with retries."""
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Connecting to Gemini API (attempt {retry_count + 1})")
                
                # Use the live.connect approach
                self._session_ctx = self.client.aio.live.connect(
                    model=config["model"],
                    config=config["live_connect_config"]
                )
                
                # Enter the context
                self.session = await self._session_ctx.__aenter__()
                self.is_running = True
                
                logger.info("Successfully connected to Gemini API")
                return True
                
            except Exception as e:
                logger.error(f"Connection attempt {retry_count + 1} failed: {str(e)}")
                retry_count += 1
                await asyncio.sleep(1)  # Wait before retrying
        
        logger.error("Failed to connect to Gemini API after maximum retries")
        return False
    
    async def stop(self):
        """Stop all audio processing and close connections."""
        logger.info("Stopping audio processing")
        self.is_running = False
        
        # Give tasks time to notice the running flag change
        await asyncio.sleep(0.5)
        
        if hasattr(self, '_session_ctx') and self._session_ctx and self.session:
            try:
                logger.info("Closing Gemini API session")
                # Use the context manager exit method to properly close the session
                await self._session_ctx.__aexit__(None, None, None)
                logger.info("Gemini API session closed successfully")
            except Exception as e:
                logger.error(f"Error closing session: {str(e)}")
            finally:
                self.session = None
                self._session_ctx = None

        self._clear_queues()
        logger.info("Audio processing stopped completely")

    def _clear_queues(self):
        """Clear any pending items from queues."""
        for queue in [self.audio_in_queue, self.out_queue]:
            if queue:
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except:
                        pass

    async def send_realtime(self):
        """Send audio data from the out_queue to the Gemini API in real-time."""
        try:
            if not self.session or not self.is_running:
                raise ValueError("Session not initialized or not running")
            
            while self.is_running:
                if not self.out_queue.empty():
                    content = await self.out_queue.get()
                    
                    if content:
                        # Send the audio content to the Gemini API using the proper method
                        await self.session.send(input=content)
                
                await asyncio.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Error in send_realtime: {str(e)}")
            self.is_running = False

    async def receive_audio(self):
        """Receive audio responses from the Gemini API and put them in the audio_in_queue."""
        try:
            if not self.session or not self.is_running:
                raise ValueError("Session not initialized or not running")
            
            # Continuously receive responses while the loop is running
            while self.is_running:
                try:
                    # Use the turn-based approach
                    turn = self.session.receive()
                    async for response in turn:
                        if data := response.data:
                            await self.audio_in_queue.put(data)
                except asyncio.CancelledError:
                    logger.info("Receive audio operation cancelled")
                    break
                except Exception as e:
                    logger.error(f"Error receiving audio response: {str(e)}")
                    if "timeout" in str(e).lower():
                        await asyncio.sleep(1)  # Brief pause before retry
                        continue
                    break
                
                await asyncio.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Error in receive_audio: {str(e)}")
            self.is_running = False

    async def listen_audio(self):
        """Process audio input from WebSocket clients."""
        # In serverless mode, we just keep the task alive
        if self.is_serverless:
            logger.info("Audio capture handled via WebSocket connections")
            while self.is_running:
                await asyncio.sleep(0.5)  # Keep the task alive
            return
            
        try:
            # Keep the method running while the audio loop is active
            while self.is_running:
                # Audio data is passed to self.out_queue by the WebSocket handler
                await asyncio.sleep(0.5)  # Just sleep to keep the task alive
                
        except asyncio.CancelledError:
            logger.info("Listen audio task cancelled")
        except Exception as e:
            logger.error(f"Error in listen_audio: {str(e)}")

    async def play_audio(self):
        """Stream audio responses to connected WebSocket clients."""
        try:
            logger.info("Starting audio playback via WebSockets")
            
            # Get access to active WebSocket clients from the global variable
            global ws_clients
            
            while self.is_running:
                if not self.audio_in_queue.empty():
                    audio_data = await self.audio_in_queue.get()
                    
                    if audio_data and ws_clients:
                        try:
                            # Add WAV header to the raw audio data
                            sample_rate = RECEIVE_SAMPLE_RATE
                            channels = 1  # Mono
                            sample_width = 2  # 16-bit audio
                            
                            # Create WAV header
                            wav_header = create_wav_header(
                                len(audio_data), 
                                sample_rate=sample_rate,
                                channels=channels, 
                                sample_width=sample_width
                            )
                            
                            # Combine header with audio data
                            wav_data = wav_header + audio_data
                            
                            # Send the audio data to all connected clients
                            encoded_audio = base64.b64encode(wav_data).decode('utf-8');
                            message = json.dumps({
                                "type": "audio",
                                "format": "audio/wav",
                                "data": encoded_audio
                            })
                            
                            # Send to all connected clients
                            for ws in list(ws_clients):
                                try:
                                    ws.send(message)
                                except Exception as e:
                                    logger.error(f"Error sending audio to client: {str(e)}")
                        
                        except Exception as e:
                            logger.error(f"Error preparing audio data: {str(e)}")
                
                await asyncio.sleep(0.01)  # Small sleep to prevent CPU hogging
                
        except Exception as e:
            logger.error(f"Error in play_audio: {str(e)}")
            logger.error(traceback.format_exc())

    async def run(self, config):
        """Start the main audio processing loop."""
        try:
            await self.connect_with_retry(config)
            if not self.session:
                raise Exception("Failed to establish session")

            # Create tasks
            tasks = [
                asyncio.create_task(self.send_realtime()),
                asyncio.create_task(self.listen_audio()),
                asyncio.create_task(self.receive_audio()),
                asyncio.create_task(self.play_audio())
            ]
            
            # Wait for all tasks to complete or cancel
            self._stop_event = asyncio.Event()
            await self._stop_event.wait()
            
            # Cancel all tasks when done
            for task in tasks:
                if not task.done():
                    task.cancel()
            
            await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Error in run: {str(e)}")
            logger.error(traceback.format_exc())
        finally:
            self.is_running = False
            await self.stop()


# ==== Flask Application Setup ====

# Global variables for managing state
audio_loop = None
audio_thread = None
session_lock = Lock()
ws_clients = set()

def create_gemini_client():
    """Create and configure the Gemini API client."""
    return genai.Client(
        http_options={
            "api_version": "v1beta",
            "timeout": CONNECTION_TIMEOUT,
        },
        api_key=API_KEY,
    )

def create_audio_loop():
    """Create a new AudioLoop instance."""
    if IN_VERCEL:
        logger.info("Limited audio functionality in serverless environment")
        return None
        
    client = create_gemini_client()
    return AudioLoop(client)

def run_async_task(coro_func, *args, **kwargs):
    """Run an async function in a new event loop safely."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro_func(*args, **kwargs))
    finally:
        loop.close()

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app, resources={r"/*": {"origins": "*", "supports_credentials": True}})
    
    # Initialize WebSocket support
    sock = Sock(app)
    
    # Store the Gemini configuration in app config
    app.config['GEMINI_CONFIG'] = get_live_connect_config()
    
    # === Routes ===
    
    @app.route('/')
    def home():
        """Home page with API documentation."""
        # Get the base URL from the request
        if request.headers.get('X-Forwarded-Host'):
            # For Vercel and other proxy setups
            proto = request.headers.get('X-Forwarded-Proto', 'https')
            host = request.headers.get('X-Forwarded-Host')
            base_url = f"{proto}://{host}"
        else:
            # For local development
            base_url = f"{request.scheme}://{request.host}"
            
        return render_template_string(
            HOME_PAGE_TEMPLATE,
            base_url=base_url
        )
    
    @sock.route('/audio-stream')
    def audio_stream_socket(ws):
        """WebSocket handler for audio streaming."""
        global audio_loop
        global ws_clients
        
        logger.info("New WebSocket client connected for therapy session")
        
        # Add the WebSocket to our clients set
        ws_clients.add(ws)
        
        try:
            # Check if we have an active audio loop
            if not audio_loop or not audio_loop.is_running:
                logger.warning("Client connected but no active therapy session. Starting one.")
                
                # Start a therapy session if none exists
                if not audio_loop:
                    audio_loop = create_audio_loop()
                    
                    # Start the audio loop in a new thread
                    global audio_thread
                    audio_thread = Thread(
                        target=lambda: run_async_task(audio_loop.run, app.config['GEMINI_CONFIG']),
                        daemon=True
                    )
                    audio_thread.start()
            
            # Process WebSocket messages
            while True:
                message = ws.receive()
                
                if message:
                    try:
                        # Try to parse as JSON
                        data = json.loads(message)
                        
                        if data.get("type") == "audio":
                            # Decode base64 audio data
                            audio_bytes = base64.b64decode(data["data"])
                            
                            if audio_loop and audio_loop.is_running:
                                asyncio.run(audio_loop.out_queue.put({
                                    "data": audio_bytes,
                                    "mime_type": data.get("format", "audio/pcm")
                                }))
                        
                        elif data.get("type") == "control":
                            # Handle control messages
                            if data.get("command") == "stop":
                                logger.info("Client requested therapy session stop")
                                if audio_loop:
                                    asyncio.run(audio_loop.stop())
                    except json.JSONDecodeError:
                        # If not JSON, treat as raw audio data
                        if audio_loop and audio_loop.is_running:
                            asyncio.run(audio_loop.out_queue.put({
                                "data": message,
                                "mime_type": "audio/pcm"
                            }))
        except Exception as e:
            logger.error(f"WebSocket error: {str(e)}")
        finally:
            if ws in ws_clients:
                ws_clients.remove(ws)
            logger.info("WebSocket client disconnected")
    
    @app.route('/start_voice', methods=['POST', 'OPTIONS'])
    def start_voice():
        """Start voice therapy session with DIA Therapist."""
        global audio_loop
        global audio_thread
        
        # Handle CORS preflight request
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Methods'] = 'POST'
            return response
            
        if IN_VERCEL:
            return jsonify({
                "status": "started",
                "vercel": True,
                "info": "Limited functionality in serverless environment."
            })
        
        with session_lock:
            # If there's an existing session, terminate it first
            if audio_loop:
                try:
                    run_async_task(audio_loop.stop)
                    logger.info("Existing therapy session terminated before starting new one")
                    
                    # Wait for the thread to finish
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join(timeout=2.0)
                        
                except Exception as e:
                    logger.error(f"Error terminating existing voice service: {str(e)}")
                finally:
                    # Force cleanup of resources
                    audio_loop = None
                    audio_thread = None
                    # Small delay to ensure clean startup
                    time.sleep(0.5)
            
            try:
                # Create a new audio loop
                audio_loop = create_audio_loop()
                
                # Start the audio loop in a new thread
                audio_thread = Thread(
                    target=lambda: run_async_task(audio_loop.run, app.config['GEMINI_CONFIG']),
                    daemon=True
                )
                audio_thread.start()
                
                logger.info("Therapy session started")
                
                # Return WebSocket info in the response
                return jsonify({
                    "status": "started",
                    "websocket": {
                        "url": f"wss://{request.host}/audio-stream" if request.is_secure else f"ws://{request.host}/audio-stream",
                        "protocol": "audio-stream"
                    }
                })
            except Exception as e:
                logger.error(f"Error starting voice service: {str(e)}")
                return jsonify({"status": "error", "message": str(e)})

    @app.route('/terminate_voice', methods=['POST', 'OPTIONS'])
    def terminate_voice():
        """Completely stop the therapy session and clean up resources."""
        global audio_loop
        global audio_thread
        global ws_clients
        
        # Handle CORS preflight request
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Methods'] = 'POST'
            return response
            
        if IN_VERCEL:
            return jsonify({"status": "terminated", "vercel": True})
        
        with session_lock:
            if audio_loop:
                try:
                    # Stop the audio loop
                    run_async_task(audio_loop.stop)
                    logger.info("Therapy session terminated")
                    
                    # Wait for the thread to finish
                    if audio_thread and audio_thread.is_alive():
                        audio_thread.join(timeout=2.0)
                        
                    # Close any active WebSocket connections
                    for ws in list(ws_clients):
                        try:
                            ws.close()
                        except:
                            pass
                    ws_clients.clear()
                        
                except Exception as e:
                    logger.error(f"Error terminating voice service: {str(e)}")
                finally:
                    # Clean up resources
                    audio_loop = None
                    audio_thread = None
            
        return jsonify({"status": "terminated"})

    @app.route('/status')
    def status():
        """Get the status of the API."""
        return jsonify({
            "status": "ok",
            "vercel": IN_VERCEL,
            "version": "1.0.0"
        })
    
    return app


# Entry point for Vercel deployment
app = create_app()

# Run the app if executed directly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT, debug=True)
