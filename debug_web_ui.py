#!/usr/bin/env python3
"""
Web UI for the Auto Debugger using Flask
Run with: python debug_web_ui.py
"""

from flask import Flask, render_template, request, jsonify, session
import os
import tempfile
import uuid
from pathlib import Path
import traceback
from error_analyzer import AutoDebugger

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Global debugger instance (will be initialized when API key is provided)
debugger = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/set-api-key', methods=['POST'])
def set_api_key():
    global debugger
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        model = data.get('model', 'deepseek/deepseek-chat-v3-0324:free')
        
        if not api_key:
            return jsonify({'success': False, 'error': 'API key is required'})
        
        # Initialize debugger
        debugger = AutoDebugger(api_key)
        debugger.analyzer.model = model
        
        session['api_key_set'] = True
        return jsonify({'success': True})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/debug-code', methods=['POST'])
def debug_code():
    global debugger
    
    if not debugger:
        return jsonify({'success': False, 'error': 'API key not set'})
    
    try:
        data = request.get_json()
        code = data.get('code', '')
        filename = data.get('filename', 'temp_script.py')
        
        if not code.strip():
            return jsonify({'success': False, 'error': 'No code provided'})
        
        # Create temporary file
        temp_dir = Path(tempfile.gettempdir()) / 'auto_debugger'
        temp_dir.mkdir(exist_ok=True)
        
        temp_file = temp_dir / f"{uuid.uuid4().hex}_{filename}"
        temp_file.write_text(code, encoding='utf-8')
        
        try:
            # Run auto-fix
            fix_suggestion = debugger.auto_fix_code(str(temp_file))
            
            if fix_suggestion is None:
                return jsonify({
                    'success': True,
                    'no_errors': True,
                    'message': 'Code executed successfully - no errors found!'
                })
            
            # Return fix suggestion
            return jsonify({
                'success': True,
                'no_errors': False,
                'fix': {
                    'analysis': fix_suggestion.analysis,
                    'root_cause': fix_suggestion.root_cause,
                    'fix_description': fix_suggestion.fix_description,
                    'confidence': fix_suggestion.confidence,
                    'replication_steps': fix_suggestion.replication_steps,
                    'file_changes': fix_suggestion.file_changes
                }
            })
        
        finally:
            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error debugging code: {str(e)}'
        })


@app.route('/api/apply-fix', methods=['POST'])
def apply_fix():
    global debugger
    
    if not debugger:
        return jsonify({'success': False, 'error': 'API key not set'})
    
    try:
        data = request.get_json()
        original_code = data.get('original_code', '')
        fixed_code = data.get('fixed_code', '')
        filename = data.get('filename', 'fixed_script.py')
        
        # For web UI, we'll return the fixed code instead of modifying files
        # In a real implementation, you might want to save to a specific location
        
        return jsonify({
            'success': True,
            'message': 'Fix applied successfully!',
            'fixed_code': fixed_code
        })
    
    except Exception as e:
        return jsonify({
            'success': False, 
            'error': f'Error applying fix: {str(e)}'
        })


@app.route('/api/run-code', methods=['POST'])
def run_code():
    try:
        data = request.get_json()
        code = data.get('code', '')
        filename = data.get('filename', 'temp_script.py')
        if not code.strip():
            return jsonify({'success': False, 'error': 'No code provided'})
        temp_dir = Path(tempfile.gettempdir()) / 'auto_debugger'
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / f"{uuid.uuid4().hex}_{filename}"
        temp_file.write_text(code, encoding='utf-8')
        import subprocess
        import re
        try:
            result = subprocess.run(
                ['python', str(temp_file)],
                capture_output=True, text=True, timeout=10
            )
            output = result.stdout
            error = result.stderr
            error_file = None
            error_line = None
            # Parse stacktrace for file and line
            if error:
                # Look for the last 'File ...' line
                matches = list(re.finditer(r'File "([^"]+)", line (\d+)', error))
                if matches:
                    last = matches[-1]
                    error_file = last.group(1)
                    error_line = int(last.group(2))
            return jsonify({
                'success': True,
                'output': output,
                'error': error,
                'error_file': error_file,
                'error_line': error_line
            })
        finally:
            if temp_file.exists():
                temp_file.unlink()
    except Exception as e:
        return jsonify({'success': False, 'error': f'Error running code: {str(e)}'})


# Create templates directory and HTML template
def create_template():
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)
    
    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Auto Debugger</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            padding: 2rem;
            width: 90%;
            max-width: 1200px;
            max-height: 90vh;
            overflow: auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: #666;
            font-size: 1.1rem;
        }
        
        .setup-section {
            background: #f8f9fa;
            padding: 1.5rem;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        
        .form-group {
            margin-bottom: 1rem;
        }
        
        label {
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #333;
        }
        
        input[type="text"], input[type="password"], select, textarea {
            width: 100%;
            padding: 0.75rem;
            border: 2px solid #e1e5e9;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus, input[type="password"]:focus, select:focus, textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        textarea {
            resize: vertical;
            min-height: 200px;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
        }
        
        .results {
            margin-top: 2rem;
            padding: 1.5rem;
            background: #f8f9fa;
            border-radius: 10px;
            display: none;
        }
        
        .success {
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }
        
        .error {
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }
        
        .fix-section {
            margin-top: 1rem;
            padding: 1rem;
            background: white;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        
        .confidence-bar {
            width: 100%;
            height: 20px;
            background: #e9ecef;
            border-radius: 10px;
            overflow: hidden;
            margin: 0.5rem 0;
        }
        
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #28a745, #ffc107, #dc3545);
            transition: width 0.3s;
        }
        
        .code-block {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 8px;
            padding: 1rem;
            margin: 1rem 0;
            font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
            white-space: pre-wrap;
            overflow-x: auto;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255,255,255,.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .step-list {
            list-style: none;
            padding-left: 0;
        }
        
        .step-list li {
            padding: 0.5rem 0;
            border-bottom: 1px solid #eee;
        }
        
        .step-list li:before {
            content: "→ ";
            color: #667eea;
            font-weight: bold;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔧 Auto Debugger</h1>
            <p>Automatically analyze and fix Python code errors using AI</p>
        </div>
        
        <div class="setup-section">
            <h3>Configuration</h3>
            <div class="form-group">
                <label for="apiKey">OpenRouter API Key:</label>
                <input type="password" id="apiKey" placeholder="Enter your OpenRouter API key">
            </div>
            <div class="form-group">
                <label for="model">Model ID (e.g. deepseek/deepseek-chat-v3-0324:free, anthropic/claude-3.5-sonnet):</label>
                <input type="text" id="model" placeholder="deepseek/deepseek-chat-v3-0324:free" value="deepseek/deepseek-chat-v3-0324:free">
            </div>
            <button class="btn" onclick="setApiKey()">Set Configuration</button>
        </div>
        
        <div class="form-group">
            <label for="filename">Filename (optional):</label>
            <input type="text" id="filename" placeholder="script.py" value="debug_test.py">
        </div>
        
        <div class="form-group">
            <label for="code">Python Code to Debug:</label>
            <textarea id="code" placeholder="Paste your Python code here...">
# Example code with an error
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)

# This will cause a ZeroDivisionError
numbers = []
result = calculate_average(numbers)
print(f"Average: {result}")
</textarea>
        </div>
        
        <button class="btn" onclick="runCode()" id="runBtn">▶️ Run Code</button>
        <button class="btn" onclick="debugCode()" id="debugBtn">
            🔍 Debug Code
        </button>
        
        <div id="runResults" class="results" style="display:none;"></div>
        <div id="results" class="results">
            <!-- Results will be displayed here -->
        </div>
    </div>
    
    <script>
        let currentFix = null;
        let fixedCodeList = [];
        
        async function setApiKey() {
            const apiKey = document.getElementById('apiKey').value;
            const model = document.getElementById('model').value;
            
            if (!apiKey.trim()) {
                showError('Please enter your OpenRouter API key');
                return;
            }
            
            try {
                const response = await fetch('/api/set-api-key', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        api_key: apiKey,
                        model: model
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showSuccess('Configuration set successfully! You can now debug code.');
                } else {
                    showError('Error: ' + data.error);
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            }
        }
        
        async function debugCode() {
            const code = document.getElementById('code').value;
            const filename = document.getElementById('filename').value || 'debug_test.py';
            const debugBtn = document.getElementById('debugBtn');
            
            if (!code.trim()) {
                showError('Please enter some Python code to debug');
                return;
            }
            
            // Show loading state
            debugBtn.innerHTML = '<span class="loading"></span> Debugging...';
            debugBtn.disabled = true;
            
            try {
                const response = await fetch('/api/debug-code', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        code: code,
                        filename: filename
                    })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    if (data.no_errors) {
                        showSuccess(data.message);
                    } else {
                        showFixResults(data.fix);
                        currentFix = data.fix;
                    }
                } else {
                    showError('Error: ' + data.error);
                }
            } catch (error) {
                showError('Network error: ' + error.message);
            } finally {
                // Reset button
                debugBtn.innerHTML = '🔍 Debug Code';
                debugBtn.disabled = false;
            }
        }
        
        async function runCode() {
            const code = document.getElementById('code').value;
            const filename = document.getElementById('filename').value || 'debug_test.py';
            const runBtn = document.getElementById('runBtn');
            const runResults = document.getElementById('runResults');
            if (!code.trim()) {
                showRunError('Please enter some Python code to run');
                return;
            }
            runBtn.innerHTML = '<span class="loading"></span> Running...';
            runBtn.disabled = true;
            runResults.style.display = 'block';
            runResults.className = 'results';
            runResults.innerHTML = '';
            try {
                const response = await fetch('/api/run-code', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ code: code, filename: filename })
                });
                const data = await response.json();
                if (data.success) {
                    let output = data.output ? `<pre>${escapeHtml(data.output)}</pre>` : '';
                    let error = data.error ? `<pre style="color:#b00;">${escapeHtml(data.error)}</pre>` : '';
                    let errorLoc = '';
                    if (data.error_file && data.error_line) {
                        errorLoc = `<div style="color:#ff8c00; font-weight:bold;">Error in <span style="text-decoration:underline;">${escapeHtml(data.error_file)}</span> at line <span style="text-decoration:underline;">${data.error_line}</span></div>`;
                    }
                    runResults.innerHTML = `<h3>▶️ Code Output</h3>${output}${errorLoc}${error}`;
                } else {
                    showRunError('Error: ' + data.error);
                }
            } catch (error) {
                showRunError('Network error: ' + error.message);
            } finally {
                runBtn.innerHTML = '▶️ Run Code';
                runBtn.disabled = false;
            }
        }
        
        function showRunError(message) {
            const runResults = document.getElementById('runResults');
            runResults.className = 'results error';
            runResults.style.display = 'block';
            runResults.innerHTML = `<h3>❌ Error</h3><p>${message}</p>`;
        }
        
        function showSuccess(message) {
            const results = document.getElementById('results');
            results.className = 'results success';
            results.style.display = 'block';
            results.innerHTML = `
                <h3>✅ Success</h3>
                <p>${message}</p>
            `;
        }
        
        function showError(message) {
            const results = document.getElementById('results');
            results.className = 'results error';
            results.style.display = 'block';
            results.innerHTML = `
                <h3>❌ Error</h3>
                <p>${message}</p>
            `;
        }
        
        function showFixResults(fix) {
            const results = document.getElementById('results');
            results.className = 'results';
            results.style.display = 'block';
            fixedCodeList = [];
            const confidencePercent = Math.round(fix.confidence * 100);
            const confidenceColor = fix.confidence > 0.7 ? '#28a745' : fix.confidence > 0.4 ? '#ffc107' : '#dc3545';
            
            let replicationSteps = '';
            if (fix.replication_steps && fix.replication_steps.length > 0) {
                replicationSteps = `
                    <h4>🔄 How to Reproduce:</h4>
                    <ul class="step-list">
                        ${fix.replication_steps.map(step => `<li>${step}</li>`).join('')}
                    </ul>
                `;
            }
            
            let fixedCode = '';
            if (fix.file_changes) {
                const fileChanges = Object.entries(fix.file_changes);
                if (fileChanges.length > 0) {
                    fixedCode = `
                        <h4>🔧 Fixed Code:</h4>
                        ${fileChanges.map(([filename, code], idx) => {
                            fixedCodeList[idx] = code;
                            return `
                                <div class="fix-section">
                                    <strong>File: ${filename}</strong>
                                    <div class="code-block">${escapeHtml(code)}</div>
                                    <button class="btn" onclick="applyFixToEditor(${idx})">
                                        Apply Fix to Editor
                                    </button>
                                </div>
                            `;
                        }).join('')}
                    `;
                }
            }
            
            results.innerHTML = `
                <h3>🔍 Analysis Complete</h3>
                
                <div class="fix-section">
                    <h4>🎯 Root Cause:</h4>
                    <p>${fix.root_cause}</p>
                </div>
                
                <div class="fix-section">
                    <h4>📊 Confidence Level:</h4>
                    <div class="confidence-bar">
                        <div class="confidence-fill" style="width: ${confidencePercent}%; background-color: ${confidenceColor}"></div>
                    </div>
                    <p>${confidencePercent}% confident in this analysis</p>
                </div>
                
                <div class="fix-section">
                    <h4>📝 Detailed Analysis:</h4>
                    <p>${fix.analysis}</p>
                </div>
                
                <div class="fix-section">
                    <h4>💡 Fix Description:</h4>
                    <p>${fix.fix_description}</p>
                </div>
                
                ${replicationSteps}
                ${fixedCode}
            `;
        }
        
        function applyFixToEditor(idx) {
            document.getElementById('code').value = fixedCodeList[idx];
            showSuccess('Fixed code has been applied to the editor! You can now test it.');
        }
        
        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }
        
        function unescapeHtml(text) {
            const div = document.createElement('div');
            div.innerHTML = text;
            return div.textContent;
        }
    </script>
</body>
</html>'''
    
    template_file = templates_dir / 'index.html'
    template_file.write_text(html_content, encoding='utf-8')
    print(f"Created template: {template_file}")


if __name__ == '__main__':
    # Always (re)create the template on startup
    create_template()
    
    print("🚀 Starting Auto Debugger Web UI...")
    print("📝 Navigate to http://localhost:5000 to use the interface")
    print("🔑 You'll need an OpenRouter API key to use the service")
    print("💡 Example keys can be obtained from: https://openrouter.ai/")
    
    app.run(debug=True, host='0.0.0.0', port=5000)