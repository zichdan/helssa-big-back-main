# GitHub Copilot Instructions

## Project Context
This is a Voice Chat Application with React frontend and Flask backend that enables users to record audio, convert speech to text using OpenAI Whisper, and chat with AI assistants. The application supports Persian/Farsi language and is containerized with Docker.

## Code Generation Guidelines

### General Preferences
- Generate clean, readable, and maintainable code
- Include comprehensive error handling and validation
- Add meaningful comments for complex logic
- Follow established patterns in the codebase
- Prioritize security and performance

### Frontend (React) Guidelines
- Use functional components with hooks
- Implement proper loading and error states
- Add TypeScript interfaces for props and state
- Use modern React patterns (hooks, context, suspense)
- Include accessibility attributes (ARIA labels, semantic HTML)
- Support RTL (right-to-left) layout for Persian text
- Use CSS-in-JS or CSS modules for styling

### Backend (Flask) Guidelines
- Follow RESTful API conventions
- Implement proper request validation
- Use appropriate HTTP status codes
- Add comprehensive error handling
- Include type hints for function parameters
- Implement proper logging
- Add input sanitization and security measures

### Code Structure Preferences

#### React Components
```javascript
// Preferred component structure
import React, { useState, useEffect } from 'react';
import PropTypes from 'prop-types';

const ComponentName = ({ prop1, prop2, ...props }) => {
  const [state, setState] = useState(initialValue);
  
  useEffect(() => {
    // Side effects
  }, [dependencies]);

  const handleEvent = useCallback(() => {
    // Event handling logic
  }, [dependencies]);

  return (
    <div className="component-name" {...props}>
      {/* Component JSX */}
    </div>
  );
};

ComponentName.propTypes = {
  prop1: PropTypes.string.isRequired,
  prop2: PropTypes.number,
};

ComponentName.defaultProps = {
  prop2: 0,
};

export default ComponentName;
```

#### Flask Routes
```python
# Preferred route structure
from flask import Blueprint, request, jsonify
from marshmallow import Schema, fields, ValidationError
import logging

api = Blueprint('api', __name__)
logger = logging.getLogger(__name__)

class RequestSchema(Schema):
    field1 = fields.Str(required=True)
    field2 = fields.Int()

@api.route('/endpoint', methods=['POST'])
def endpoint_handler():
    """
    Endpoint description
    
    Returns:
        dict: Response data with status
    """
    try:
        schema = RequestSchema()
        data = schema.load(request.json)
        
        # Business logic here
        result = process_data(data)
        
        return jsonify({
            'data': result,
            'status': 'success'
        }), 200
        
    except ValidationError as e:
        logger.warning(f"Validation error: {e.messages}")
        return jsonify({
            'error': 'Invalid input data',
            'details': e.messages,
            'status': 'error'
        }), 400
        
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({
            'error': 'Internal server error',
            'status': 'error'
        }), 500
```

### Specific Features to Include

#### Audio Recording
- Always check for browser compatibility
- Implement proper microphone permissions handling
- Add visual feedback for recording state
- Handle different audio formats gracefully

#### API Integration
- Include retry logic for network requests
- Implement request timeout handling
- Add loading states for all async operations
- Cache responses when appropriate

#### Internationalization
- Support both English and Persian text
- Use proper RTL layout for Persian content
- Include fallback text for missing translations
- Handle mixed language content properly

### Security Considerations
- Validate all user inputs on both client and server
- Sanitize file uploads and limit file sizes
- Use HTTPS for all API communications
- Implement rate limiting for API endpoints
- Never expose sensitive information in client code
- Use environment variables for configuration

### Performance Optimizations
- Implement lazy loading for components
- Use React.memo for expensive components
- Optimize bundle sizes with code splitting
- Cache API responses appropriately
- Compress images and assets
- Use efficient data structures

### Testing Preferences
- Generate comprehensive test cases
- Include edge cases and error scenarios
- Test accessibility features
- Mock external dependencies
- Test with different browsers and devices

### Error Handling Patterns
```javascript
// Frontend error handling
const handleApiCall = async () => {
  try {
    setLoading(true);
    setError(null);
    
    const response = await apiCall();
    setData(response.data);
    
  } catch (error) {
    console.error('API call failed:', error);
    setError(error.message || 'An unexpected error occurred');
  } finally {
    setLoading(false);
  }
};
```

```python
# Backend error handling
def handle_request():
    try:
        # Process request
        result = process_data()
        return success_response(result)
        
    except ValidationError as e:
        return error_response('Validation failed', 400, e.messages)
    except APIError as e:
        return error_response(str(e), 500)
    except Exception as e:
        logger.exception("Unexpected error occurred")
        return error_response('Internal server error', 500)
```

### Documentation Standards
- Add docstrings for all functions and classes
- Include parameter types and return values
- Add usage examples for complex functions
- Document API endpoints with request/response examples
- Keep README files updated with new features

### Dependencies
- Prefer well-maintained, popular libraries
- Use specific version numbers in requirements
- Avoid unnecessary dependencies
- Consider bundle size impact for frontend packages
- Check for security vulnerabilities regularly

When generating code, always consider:
1. Code maintainability and readability
2. Error handling and edge cases
3. Performance implications
4. Security considerations
5. Testing requirements
6. Documentation needs
7. Accessibility compliance
8. Internationalization support