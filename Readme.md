# 🔧 Auto Debugger - AI-Powered Python Error Fixing

An intelligent system that automatically captures, analyzes, and fixes Python code errors using Large Language Models (LLMs). Just like GitHub Copilot, but specifically focused on debugging and error resolution.

## ✨ Features

- **🔍 Automatic Error Detection**: Captures runtime errors as they occur
- **📊 Smart Context Extraction**: Gathers relevant code context from stack traces
- **🤖 LLM-Powered Analysis**: Uses advanced AI models to understand and fix errors
- **🛡️ Safety First**: Creates backups and validates syntax before applying fixes
- **🎯 Multiple Interfaces**: CLI tool and Web UI for different workflows
- **📝 Detailed Reporting**: Provides fix explanations and replication steps

## Screenshots 


![Image](https://github.com/user-attachments/assets/7d1be92c-896a-4296-b703-0ab3b556e181)


![Image](https://github.com/user-attachments/assets/293853f5-b300-49e3-914b-5da32094380f)


![Image](https://github.com/user-attachments/assets/49c949ff-c4ae-4f99-84d3-af82addbf8ba)

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project files
# Install dependencies
pip install -r requirements.txt
```

### 2. Get OpenRouter API Key

1. Visit [OpenRouter.ai](https://openrouter.ai/)
2. Sign up for an account
3. Generate an API key
4. Set it as environment variable (optional):
   ```bash
   export OPENROUTER_API_KEY="your_api_key_here"
   ```

### 3. Usage Options

#### Option A: Command Line Interface

```bash
# Debug a specific Python file
python debug_cli.py buggy_script.py

# With custom API key
python debug_cli.py buggy_script.py --api-key YOUR_API_KEY

# With different model
python debug_cli.py buggy_script.py --model openai/gpt-4-turbo

# Auto-apply fixes (use with caution!)
python debug_cli.py buggy_script.py --auto-apply
```

#### Option B: Web Interface

```bash
# Start the web server
python debug_web_ui.py

# Open your browser to http://localhost:5000
# Enter your API key and start debugging!
```

## 📋 How It Works

1. **Error Capture**: The system runs your Python code and captures any exceptions
2. **Context Extraction**: Gathers relevant code from stack traces and surrounding lines
3. **LLM Analysis**: Sends error information and context to the chosen AI model
4. **Fix Generation**: AI provides detailed analysis, root cause, and code fixes
5. **Safe Application**: Creates backups and validates syntax before applying changes
6. **Verification**: You can test the fixed code immediately

## 🎯 Example Workflow

Let's say you have this buggy code:

```python
# buggy_script.py
def calculate_average(numbers):
    total = sum(numbers)
    return total / len(numbers)

numbers = []  # Empty list will cause ZeroDivisionError
result = calculate_average(numbers)
print(f"Average: {result}")
```

Running the auto-debugger:

```bash
python debug_cli.py buggy_script.py
```

**Output:**
```
🔍 Auto-debugging: buggy_script.py
🤖 Using model: anthropic/claude-3.5-sonnet
--------------------------------------------------

================================================================================
FIX ANALYSIS COMPLETE
================================================================================
Root Cause: Division by zero error when calculating average of empty list
Confidence: 95.0%

Analysis:
The error occurs because the function calculate_average() attempts to divide by 
len(numbers) when the list is empty, resulting in division by zero.

Fix Description:
Add a check for empty list before performing the calculation. Return 0 or None 
for empty lists, or raise a more descriptive error.

Replication Steps:
1. Create an empty list
2. Call calculate_average() with the empty list
3. The function will attempt len([]) which is 0, causing ZeroDivisionError

Files to be modified:
  - buggy_script.py

Apply this fix? (y/n/s=show changes): y

✅ Applied fixes to 1/1 files successfully!
💡 Try running 'python buggy_script.py' again
```

## 🔧 Configuration Options

### CLI Arguments

- `target_file`: Python file to debug (required)
- `--api-key`: OpenRouter API key (or use env var)
- `--model`: LLM model to use (default: claude-3.5-sonnet)
- `--auto-apply`: Skip confirmation and apply fixes automatically

### Supported Models

- `anthropic/claude-3.5-sonnet` (Recommended - best balance of speed/quality)
- `anthropic/claude-3-opus` (Highest quality, slower)
- `openai/gpt-4-turbo` (OpenAI's latest)
- `openai/gpt-3.5-turbo` (Faster, lower cost)

### Environment Variables

- `OPENROUTER_API_KEY`: Your OpenRouter API key

## 🛡️ Safety Features

### Automatic Backups
- Creates timestamped backups before applying any fixes
- Stored in `./code_backups/` directory
- Format: `filename.py.backup_YYYYMMDD_HHMMSS`

### Syntax Validation
- Validates Python syntax before applying fixes
- Prevents application of syntactically incorrect code
- Rollback capability if issues are detected

### User Confirmation
- Shows detailed analysis before applying fixes
- Option to preview changes before application
- Can decline fixes that seem risky

## 📁 Project Structure

```
auto-debugger/
├── error_analyzer.py      # Core debugging logic
├── debug_cli.py          # Command-line interface
├── debug_web_ui.py       # Web interface
├── requirements.txt      # Python dependencies
├── README.md            # This file
├── templates/           # Web UI templates (auto-created)
│   └── index.html
└── code_backups/        # Backup files (auto-created)
```

## 🎨 Web UI Features

The web interface provides:

- **💻 Code Editor**: Syntax-highlighted Python code input
- **⚙️ Model Selection**: Choose from different AI models
- **📊 Confidence Scoring**: Visual confidence indicators
- **🔄 Live Preview**: See fixes before applying them
- **📋 Step-by-Step**: Detailed replication instructions
- **🎯 One-Click Apply**: Apply fixes directly to the editor

## 🚨 Limitations & Considerations

### Current Limitations
- **Python Only**: Currently supports Python code only
- **Runtime Errors**: Focuses on runtime errors, not logic bugs
- **Context Size**: Limited by LLM context windows for very large codebases
- **API Costs**: Uses paid API services (though costs are typically low)

### Best Practices
- **Review Fixes**: Always review AI-generated fixes before applying
- **Test Thoroughly**: Test fixed code with various inputs
- **Version Control**: Use git or similar for additional backup
- **Start Small**: Begin with simple scripts before complex projects

## 🔬 Advanced Usage

### Custom Error Handling

You can integrate the debugger into your own error handling:

```python
from error_analyzer import AutoDebugger
import sys

# Initialize debugger
debugger = AutoDebugger("your_api_key")

try:
    # Your code here
    risky_function()
except Exception:
    # Capture and analyze the error
    exc_type, exc_value, exc_traceback = sys.exc_info()
    fix_suggestion = debugger.debug_exception(exc_type, exc_value, exc_traceback)
    
    # Handle the fix suggestion
    if fix_suggestion.confidence > 0.8:
        print("High confidence fix available!")
        # Apply automatically or prompt user
```

### Batch Processing

Process multiple files:

```bash
# Process all Python files in a directory
for file in *.py; do
    echo "Processing $file..."
    python debug_cli.py "$file"
done
```

## 🆘 Troubleshooting

### Common Issues

**API Key Issues**
- Ensure your OpenRouter API key is valid
- Check that you have sufficient credits
- Verify the key has access to your chosen model

**Import Errors**
- Install all requirements: `pip install -r requirements.txt`
- Use Python 3.7 or higher

**Permission Errors**
- Ensure write permissions for backup directory
- Check file permissions for target scripts

**Model Errors**
- Some models may be unavailable or require special access
- Try switching to `anthropic/claude-3.5-sonnet` as default

### Getting Help

If you encounter issues:

1. Check the error messages carefully
2. Verify your API key and model selection
3. Try with a simple test script first
4. Check the backup files if something goes wrong

## 🔮 Future Enhancements

Planned features:
- Support for more programming languages (JavaScript, Java, etc.)
- Integration with popular IDEs (VS Code, PyCharm)
- Advanced static analysis integration
- Team collaboration features
- Performance optimization suggestions
- Security vulnerability detection

---

**Happy Debugging! 🐛→✨**  