# Claude AI Assistant Instructions

## Project Overview
You are working on a Voice Chat Application that combines React frontend with Flask backend. The application enables users to record audio, convert speech to text using OpenAI Whisper API, and engage in conversations with AI assistants. The project supports Persian/Farsi language and is containerized with Docker for easy deployment.

## Core Architecture
- **Frontend**: React 18 with modern hooks, RTL support for Persian
- **Backend**: Flask with OpenAI API integration
- **AI Services**: OpenAI Whisper for STT, GPT-3.5-turbo for chat
- **Containerization**: Docker and docker-compose
- **Languages**: Persian/Farsi and English support

## Code Generation Principles

### 1. Code Quality Standards
- Write self-documenting, clean code
- Implement comprehensive error handling
- Add meaningful comments for complex logic
- Follow established patterns in the codebase
- Prioritize maintainability and readability

### 2. Security-First Approach
- Validate all inputs on both client and server sides
- Sanitize user data before processing
- Use environment variables for sensitive configuration
- Implement proper CORS and security headers
- Never expose API keys or secrets in client code

### 3. Performance Considerations
- Implement efficient state management
- Use lazy loading and code splitting
- Optimize API calls with proper caching
- Handle large file uploads gracefully
- Monitor and optimize bundle sizes

### 4. Accessibility & Internationalization
- Ensure full keyboard navigation support
- Implement proper ARIA labels and semantic HTML
- Support RTL (right-to-left) text for Persian
- Provide fallback content for screen readers
- Test with multiple browsers and devices

## Specific Implementation Guidelines

### React Frontend Best Practices

#### Component Structure
```jsx
import React, { useState, useEffect, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * Component description
 * @param {Object} props - Component props
 * @param {string} props.required - Required prop description
 */
const ComponentName = ({ required, optional = defaultValue }) => {
  const [state, setState] = useState(initialValue);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleAction = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      // Implementation
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [dependencies]);

  return (
    <div className="component-name" role="region" aria-label="Component description">
      {error && <div className="error" role="alert">{error}</div>}
      {/* Component content */}
    </div>
  );
};

ComponentName.propTypes = {
  required: PropTypes.string.isRequired,
  optional: PropTypes.string,
};

export default ComponentName;
```

#### State Management
- Use `useState` for local component state
- Implement `useCallback` for event handlers
- Use `useEffect` with proper dependency arrays
- Consider Context API for global state
- Implement proper cleanup in effects

#### Audio Recording Implementation
```jsx
const useAudioRecording = () => {
  const [isRecording, setIsRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const mediaRecorderRef = useRef(null);

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: { echoCancellation: true, noiseSuppression: true } 
      });
      
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      });
      
      mediaRecorderRef.current = mediaRecorder;
      // Implementation continues...
    } catch (error) {
      throw new Error(`Microphone access denied: ${error.message}`);
    }
  }, []);

  return { isRecording, audioBlob, startRecording, stopRecording };
};
```

### Flask Backend Best Practices

#### Route Structure
```python
from flask import Blueprint, request, jsonify, current_app
from marshmallow import Schema, fields, ValidationError
from werkzeug.exceptions import BadRequest
import logging

logger = logging.getLogger(__name__)

class AudioUploadSchema(Schema):
    """Schema for audio upload validation"""
    session_id = fields.Str(missing='default')
    
class ChatMessageSchema(Schema):
    """Schema for chat message validation"""
    message = fields.Str(required=True, validate=lambda x: len(x.strip()) > 0)
    session_id = fields.Str(missing='default')

@api.route('/speech-to-text', methods=['POST'])
def speech_to_text():
    """
    Convert uploaded audio to text using OpenAI Whisper
    
    Returns:
        JSON response with transcribed text or error message
    """
    try:
        # Validate request
        if 'audio' not in request.files:
            raise BadRequest('No audio file provided')
            
        audio_file = request.files['audio']
        if not audio_file.filename:
            raise BadRequest('No audio file selected')
        
        # Validate form data
        schema = AudioUploadSchema()
        form_data = schema.load(request.form)
        
        # Process audio
        result = process_audio_file(audio_file)
        
        logger.info(f"Successfully transcribed audio for session: {form_data['session_id']}")
        
        return jsonify({
            'text': result['text'],
            'confidence': result.get('confidence'),
            'status': 'success'
        }), 200
        
    except BadRequest as e:
        logger.warning(f"Bad request: {str(e)}")
        return jsonify({
            'error': str(e),
            'status': 'error'
        }), 400
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.messages}")
        return jsonify({
            'error': 'Invalid request data',
            'details': e.messages,
            'status': 'error'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error in speech-to-text: {str(e)}", exc_info=True)
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500
```

#### Error Handling Patterns
```python
class APIError(Exception):
    """Custom API exception"""
    def __init__(self, message, status_code=500, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

def handle_openai_error(func):
    """Decorator for handling OpenAI API errors"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except openai.error.RateLimitError:
            raise APIError("Rate limit exceeded", 429)
        except openai.error.InvalidRequestError as e:
            raise APIError(f"Invalid request: {str(e)}", 400)
        except openai.error.APIError as e:
            raise APIError(f"OpenAI API error: {str(e)}", 502)
    return wrapper
```

## Development Workflow

### 1. Feature Development Process
1. **Analysis**: Understand requirements and edge cases
2. **Design**: Plan component structure and API endpoints
3. **Implementation**: Write code following established patterns
4. **Testing**: Create comprehensive test cases
5. **Documentation**: Update relevant documentation
6. **Review**: Ensure code quality and security standards

### 2. Testing Strategy
```javascript
// Frontend testing example
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { rest } from 'msw';
import { setupServer } from 'msw/node';
import VoiceChatComponent from './VoiceChatComponent';

const server = setupServer(
  rest.post('/api/speech-to-text', (req, res, ctx) => {
    return res(ctx.json({ text: 'مرحبا', status: 'success' }));
  })
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

test('should handle audio recording and transcription', async () => {
  render(<VoiceChatComponent />);
  
  const recordButton = screen.getByText(/شروع ضبط/i);
  fireEvent.click(recordButton);
  
  await waitFor(() => {
    expect(screen.getByText(/در حال ضبط/i)).toBeInTheDocument();
  });
});
```

```python
# Backend testing example
import pytest
from unittest.mock import patch, MagicMock
from app import create_app

@pytest.fixture
def client():
    app = create_app({'TESTING': True})
    with app.test_client() as client:
        yield client

def test_speech_to_text_success(client):
    """Test successful speech to text conversion"""
    with patch('app.routes.openai.Audio.transcribe') as mock_transcribe:
        mock_transcribe.return_value.text = 'مرحبا'
        
        response = client.post('/api/speech-to-text', 
                             data={'audio': (io.BytesIO(b'fake audio'), 'test.wav')})
        
        assert response.status_code == 200
        assert response.json['status'] == 'success'
        assert 'مرحبا' in response.json['text']
```

### 3. Debugging Guidelines
- Use meaningful log messages with context
- Implement proper error boundaries in React
- Add request/response logging for API calls
- Use browser dev tools for frontend debugging
- Implement health check endpoints

### 4. Performance Monitoring
```javascript
// Performance monitoring example
const usePerformanceMonitoring = () => {
  useEffect(() => {
    // Monitor component mount time
    const startTime = performance.now();
    
    return () => {
      const endTime = performance.now();
      console.log(`Component lifecycle time: ${endTime - startTime}ms`);
    };
  }, []);
};
```

## Persian/Farsi Language Support

### 1. Text Direction and Layout
```css
.rtl-container {
  direction: rtl;
  text-align: right;
}

.mixed-content {
  unicode-bidi: plaintext;
}
```

### 2. Font and Typography
- Use system fonts that support Persian characters
- Implement proper line spacing for Persian text
- Handle mixed English/Persian content gracefully

### 3. Input Validation
```python
import re

def validate_persian_text(text):
    """Validate Persian text input"""
    # Allow Persian, Arabic, English, numbers, and common punctuation
    pattern = r'^[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\w\s\.,!?;:\-()]+$'
    return re.match(pattern, text) is not None
```

## Deployment and Production

### 1. Environment Configuration
```yaml
# docker-compose.prod.yml
version: '3.8'
services:
  backend:
    environment:
      - FLASK_ENV=production
      - LOG_LEVEL=INFO
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

### 2. Security Headers
```python
from flask_talisman import Talisman

def configure_security(app):
    Talisman(app, {
        'force_https': True,
        'strict_transport_security': True,
        'content_security_policy': {
            'default-src': "'self'",
            'script-src': "'self' 'unsafe-inline'",
            'style-src': "'self' 'unsafe-inline'",
        }
    })
```

## Common Patterns and Solutions

### 1. File Upload Handling
```python
ALLOWED_EXTENSIONS = {'wav', 'mp3', 'webm', 'm4a'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_audio_file(file):
    """Validate uploaded audio file"""
    if not file or not file.filename:
        raise ValidationError("No file provided")
    
    if not allowed_file(file.filename):
        raise ValidationError("Invalid file type")
    
    # Check file size
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    
    if size > MAX_FILE_SIZE:
        raise ValidationError("File too large")
    
    return True
```

### 2. Session Management
```python
from functools import wraps
from flask import session

def require_session(f):
    """Decorator to ensure valid session"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.json.get('session_id', 'default')
        if not is_valid_session(session_id):
            return jsonify({'error': 'Invalid session'}), 401
        return f(*args, **kwargs)
    return decorated_function
```

When working on this project, always consider:
- User experience and accessibility
- Security implications of each feature
- Performance impact on both client and server
- Proper error handling and user feedback
- Cross-browser compatibility
- Persian language support requirements
- Scalability and maintainability