import ast
import traceback
import sys
import os
import json
import requests
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re


@dataclass
class ErrorInfo:
    """Container for error information"""
    error_type: str
    error_message: str
    file_path: str
    line_number: int
    function_name: str
    stack_trace: str
    surrounding_code: str
    relevant_files: List[str]


@dataclass
class FixSuggestion:
    """Container for fix suggestions from LLM"""
    analysis: str
    root_cause: str
    fix_description: str
    modified_code: str
    replication_steps: List[str]
    confidence: float
    file_changes: Dict[str, str]  # file_path -> new_content


class CodeContextExtractor:
    """Extracts relevant code context from error traces"""
    
    def __init__(self):
        self.context_lines = 10  # Lines to extract around error
    
    def extract_context(self, error_info: ErrorInfo) -> Dict[str, str]:
        """Extract code context from multiple files"""
        context = {}
        
        # Extract from main error file
        main_context = self._get_file_context(
            error_info.file_path, 
            error_info.line_number
        )
        if main_context:
            context[error_info.file_path] = main_context
        
        # Extract from related files in stack trace
        for file_path in error_info.relevant_files:
            if file_path != error_info.file_path and os.path.exists(file_path):
                file_context = self._get_full_file_content(file_path)
                if file_context:
                    context[file_path] = file_context
        
        return context
    
    def _get_file_context(self, file_path: str, line_number: int) -> Optional[str]:
        """Get context around specific line"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start = max(0, line_number - self.context_lines - 1)
            end = min(len(lines), line_number + self.context_lines)
            
            context_lines = []
            for i in range(start, end):
                marker = ">>> " if i == line_number - 1 else "    "
                context_lines.append(f"{marker}{i+1:4d}: {lines[i].rstrip()}")
            
            return "\n".join(context_lines)
        except Exception as e:
            return f"Error reading file: {e}"
    
    def _get_full_file_content(self, file_path: str) -> Optional[str]:
        """Get full file content for smaller files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Only include full content for smaller files
            line_count = len(content.splitlines())
            if line_count <= 100:
                return content
            else:
                return f"File too large ({line_count} lines), skipping full content"
        except Exception as e:
            return f"Error reading file: {e}"


class StackTraceParser:
    """Parses Python stack traces to extract relevant information"""
    
    def parse_error(self, exc_type, exc_value, exc_traceback) -> ErrorInfo:
        """Parse exception information into ErrorInfo object"""
        # Get stack trace as string
        stack_trace = ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        
        # Get the last frame (where error occurred)
        tb = exc_traceback
        while tb.tb_next:
            tb = tb.tb_next
        
        frame = tb.tb_frame
        file_path = frame.f_code.co_filename
        line_number = tb.tb_lineno
        function_name = frame.f_code.co_name
        
        # Extract relevant files from stack trace
        relevant_files = self._extract_files_from_traceback(exc_traceback)
        
        # Get surrounding code
        extractor = CodeContextExtractor()
        surrounding_code = extractor._get_file_context(file_path, line_number) or ""
        
        return ErrorInfo(
            error_type=exc_type.__name__,
            error_message=str(exc_value),
            file_path=file_path,
            line_number=line_number,
            function_name=function_name,
            stack_trace=stack_trace,
            surrounding_code=surrounding_code,
            relevant_files=relevant_files
        )
    
    def _extract_files_from_traceback(self, tb) -> List[str]:
        """Extract all file paths from traceback"""
        files = []
        while tb:
            file_path = tb.tb_frame.f_code.co_filename
            if file_path.endswith('.py') and not file_path.startswith('<'):
                files.append(file_path)
            tb = tb.tb_next
        return list(set(files))  # Remove duplicates


class LLMAnalyzer:
    """Handles LLM communication for error analysis and fix generation"""
    
    def __init__(self, api_key: str, model: str = "anthropic/claude-3.5-sonnet"):
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
    
    def analyze_and_fix(self, error_info: ErrorInfo, code_context: Dict[str, str]) -> FixSuggestion:
        """Send error to LLM for analysis and fix generation"""
        prompt = self._create_analysis_prompt(error_info, code_context)
        
        try:
            response = self._call_llm(prompt)
            return self._parse_llm_response(response, error_info)
        except Exception as e:
            return FixSuggestion(
                analysis=f"Error calling LLM: {e}",
                root_cause="Unable to analyze",
                fix_description="Manual investigation required",
                modified_code="",
                replication_steps=["Run the original code to reproduce"],
                confidence=0.0,
                file_changes={}
            )
    
    def _create_analysis_prompt(self, error_info: ErrorInfo, code_context: Dict[str, str]) -> str:
        """Create detailed prompt for LLM analysis"""
        context_str = ""
        for file_path, content in code_context.items():
            context_str += f"\n\n=== FILE: {file_path} ===\n{content}"
        
        prompt = f"""
You are an expert Python debugger. Analyze this error and provide a complete fix.

ERROR INFORMATION:
- Type: {error_info.error_type}
- Message: {error_info.error_message}
- File: {error_info.file_path}
- Line: {error_info.line_number}
- Function: {error_info.function_name}

STACK TRACE:
{error_info.stack_trace}

CODE CONTEXT:
{context_str}

Please provide your response in the following JSON format:
{{
    "analysis": "Detailed analysis of what went wrong",
    "root_cause": "The fundamental cause of the error",
    "fix_description": "Clear description of the fix",
    "confidence": 0.85,
    "replication_steps": [
        "Step 1 to reproduce the error",
        "Step 2...",
        "..."
    ],
    "file_changes": {{
        "/path/to/file.py": "complete fixed file content here"
    }}
}}

Focus on:
1. Understanding the root cause
2. Providing a working fix
3. Explaining why the fix works
4. Being specific about file changes needed

Ensure the fixed code is complete and syntactically correct.
"""
        return prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Make API call to OpenRouter"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 4000
        }
        
        response = requests.post(self.base_url, headers=headers, json=data)
        response.raise_for_status()
        
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    def _parse_llm_response(self, response: str, error_info: ErrorInfo) -> FixSuggestion:
        """Parse LLM response into FixSuggestion object"""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group()
                data = json.loads(json_str)
                
                return FixSuggestion(
                    analysis=data.get("analysis", "No analysis provided"),
                    root_cause=data.get("root_cause", "Unknown"),
                    fix_description=data.get("fix_description", "No fix description"),
                    modified_code="",  # Will be in file_changes
                    replication_steps=data.get("replication_steps", []),
                    confidence=float(data.get("confidence", 0.5)),
                    file_changes=data.get("file_changes", {})
                )
            else:
                # Fallback parsing
                return FixSuggestion(
                    analysis=response,
                    root_cause="Parsed from unstructured response",
                    fix_description="See analysis for details",
                    modified_code="",
                    replication_steps=["Manual analysis required"],
                    confidence=0.3,
                    file_changes={}
                )
        except Exception as e:
            return FixSuggestion(
                analysis=f"Error parsing LLM response: {e}\n\nRaw response:\n{response}",
                root_cause="Response parsing failed",
                fix_description="Manual intervention required",
                modified_code="",
                replication_steps=["Check LLM response manually"],
                confidence=0.0,
                file_changes={}
            )


class CodeFixer:
    """Handles applying fixes to source code files"""
    
    def __init__(self):
        self.backup_dir = Path("./code_backups")
        self.backup_dir.mkdir(exist_ok=True)
    
    def apply_fix(self, fix_suggestion: FixSuggestion, create_backup: bool = True) -> Dict[str, bool]:
        """Apply fix suggestions to files"""
        results = {}
        
        for file_path, new_content in fix_suggestion.file_changes.items():
            try:
                # Create backup if requested
                if create_backup and os.path.exists(file_path):
                    self._create_backup(file_path)
                
                # Validate syntax before applying
                if self._validate_python_syntax(new_content):
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    results[file_path] = True
                else:
                    results[file_path] = False
                    print(f"Syntax validation failed for {file_path}")
                    
            except Exception as e:
                results[file_path] = False
                print(f"Error applying fix to {file_path}: {e}")
        
        return results
    
    def _create_backup(self, file_path: str):
        """Create backup of original file"""
        import shutil
        from datetime import datetime
        
        file_name = os.path.basename(file_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_name}.backup_{timestamp}"
        backup_path = self.backup_dir / backup_name
        
        shutil.copy2(file_path, backup_path)
        print(f"Backup created: {backup_path}")
    
    def _validate_python_syntax(self, code: str) -> bool:
        """Validate Python syntax"""
        try:
            ast.parse(code)
            return True
        except SyntaxError:
            return False


class AutoDebugger:
    """Main class that orchestrates the debugging process"""
    
    def __init__(self, openrouter_api_key: str):
        self.parser = StackTraceParser()
        self.extractor = CodeContextExtractor()
        self.analyzer = LLMAnalyzer(openrouter_api_key)
        self.fixer = CodeFixer()
    
    def debug_exception(self, exc_type, exc_value, exc_traceback) -> FixSuggestion:
        """Main debugging workflow"""
        # Parse error information
        error_info = self.parser.parse_error(exc_type, exc_value, exc_traceback)
        
        # Extract code context
        code_context = self.extractor.extract_context(error_info)
        
        # Analyze with LLM
        fix_suggestion = self.analyzer.analyze_and_fix(error_info, code_context)
        
        return fix_suggestion
    
    def auto_fix_code(self, target_file: str) -> Optional[FixSuggestion]:
        """Run target file and attempt to fix any errors"""
        try:
            # Execute the target file and capture any exceptions
            with open(target_file, 'r') as f:
                code = f.read()
            
            # Execute in a controlled environment
            exec_globals = {'__name__': '__main__', '__file__': target_file}
            exec(code, exec_globals)
            
            print("Code executed successfully - no errors to fix!")
            return None
            
        except Exception as e:
            # Capture the exception and debug it
            exc_type, exc_value, exc_traceback = sys.exc_info()
            return self.debug_exception(exc_type, exc_value, exc_traceback)
    
    def apply_fix_with_confirmation(self, fix_suggestion: FixSuggestion) -> bool:
        """Apply fix after user confirmation"""
        print("\n" + "="*80)
        print("FIX ANALYSIS COMPLETE")
        print("="*80)
        print(f"Root Cause: {fix_suggestion.root_cause}")
        print(f"Confidence: {fix_suggestion.confidence:.1%}")
        print(f"\nAnalysis:\n{fix_suggestion.analysis}")
        print(f"\nFix Description:\n{fix_suggestion.fix_description}")
        
        if fix_suggestion.replication_steps:
            print(f"\nReplication Steps:")
            for i, step in enumerate(fix_suggestion.replication_steps, 1):
                print(f"{i}. {step}")
        
        if fix_suggestion.file_changes:
            print(f"\nFiles to be modified:")
            for file_path in fix_suggestion.file_changes.keys():
                print(f"  - {file_path}")
        
        # Get user confirmation
        while True:
            choice = input("\nApply this fix? (y/n/s=show changes): ").lower().strip()
            if choice == 'y':
                results = self.fixer.apply_fix(fix_suggestion)
                success_count = sum(results.values())
                total_count = len(results)
                print(f"\nApplied fixes to {success_count}/{total_count} files successfully!")
                return success_count == total_count
            elif choice == 'n':
                print("Fix not applied.")
                return False
            elif choice == 's':
                self._show_file_changes(fix_suggestion)
            else:
                print("Please enter 'y' for yes, 'n' for no, or 's' to show changes.")
    
    def _show_file_changes(self, fix_suggestion: FixSuggestion):
        """Show detailed file changes"""
        for file_path, new_content in fix_suggestion.file_changes.items():
            print(f"\n--- Changes for {file_path} ---")
            print(new_content[:1000])  # Show first 1000 chars
            if len(new_content) > 1000:
                print("... (truncated)")
            print("--- End of changes ---")