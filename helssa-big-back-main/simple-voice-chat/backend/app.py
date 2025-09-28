from flask import Flask, request, jsonify
from flask_cors import CORS
import openai
import os
import tempfile
import requests
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)

# Configuration from environment variables
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
CHAT_API_URL = os.getenv('CHAT_API_URL', 'https://api.openai.com/v1/chat/completions')

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable is required")

openai.api_key = OPENAI_API_KEY

# Store chat history (in production, use a database)
chat_sessions = {}

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy", "service": "voice-chat-backend"})

@app.route('/api/speech-to-text', methods=['POST'])
def speech_to_text():
    """Convert speech to text using OpenAI Whisper API"""
    try:
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
        
        # Save the uploaded file temporarily
        filename = secure_filename(audio_file.filename)
        with tempfile.NamedTemporaryFile(delete=False, suffix='.webm') as temp_file:
            audio_file.save(temp_file.name)
            
            # Use OpenAI Whisper API
            with open(temp_file.name, 'rb') as audio:
                transcript = openai.Audio.transcribe("whisper-1", audio)
            
            # Clean up temp file
            os.unlink(temp_file.name)
            
        return jsonify({
            "text": transcript.text,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat with AI using text input"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', 'default')
        
        # Get or create chat session
        if session_id not in chat_sessions:
            chat_sessions[session_id] = []
        
        # Add user message to history
        chat_sessions[session_id].append({"role": "user", "content": user_message})
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": "شما یک دستیار هوشمند و مفید هستید. پاسخ‌های خود را به زبان فارسی ارائه دهید."}
        ] + chat_sessions[session_id]
        
        # Call OpenAI API
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Add AI response to history
        chat_sessions[session_id].append({"role": "assistant", "content": ai_response})
        
        # Keep only last 10 messages to avoid token limit
        if len(chat_sessions[session_id]) > 10:
            chat_sessions[session_id] = chat_sessions[session_id][-10:]
        
        return jsonify({
            "response": ai_response,
            "session_id": session_id,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/clear', methods=['POST'])
def clear_chat():
    """Clear chat history for a session"""
    try:
        data = request.get_json()
        session_id = data.get('session_id', 'default')
        
        if session_id in chat_sessions:
            chat_sessions[session_id] = []
        
        return jsonify({
            "message": "Chat history cleared",
            "session_id": session_id,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)