#!/usr/bin/env python3
"""
CLI interface for the Auto Debugger
Usage: python debug_cli.py [target_file] [--api-key YOUR_KEY]
"""

import argparse
import os
import sys
from pathlib import Path
from error_analyzer import AutoDebugger


def load_api_key():
    """Load API key from environment or prompt user"""
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        api_key = input("Enter your OpenRouter API key: ").strip()
        if not api_key:
            print("Error: API key is required")
            sys.exit(1)
    return api_key


def main():
    parser = argparse.ArgumentParser(
        description="Automatically debug and fix Python code errors",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python debug_cli.py buggy_script.py
  python debug_cli.py buggy_script.py --api-key YOUR_KEY_HERE
  
Environment Variables:
  OPENROUTER_API_KEY - Your OpenRouter API key
        """
    )
    
    parser.add_argument(
        'target_file', 
        help='Python file to debug and fix'
    )
    
    parser.add_argument(
        '--api-key', 
        help='OpenRouter API key (can also use OPENROUTER_API_KEY env var)'
    )
    
    parser.add_argument(
        '--model',
        default='anthropic/claude-3.5-sonnet',
        help='LLM model to use (default: anthropic/claude-3.5-sonnet)'
    )
    
    parser.add_argument(
        '--auto-apply',
        action='store_true',
        help='Automatically apply fixes without confirmation (dangerous!)'
    )
    
    args = parser.parse_args()
    
    # Validate target file
    if not os.path.exists(args.target_file):
        print(f"Error: File '{args.target_file}' not found")
        sys.exit(1)
    
    if not args.target_file.endswith('.py'):
        print(f"Warning: '{args.target_file}' doesn't appear to be a Python file")
    
    # Get API key
    api_key = args.api_key or load_api_key()
    
    print(f"🔍 Auto-debugging: {args.target_file}")
    print(f"🤖 Using model: {args.model}")
    print("-" * 50)
    
    try:
        # Initialize debugger
        debugger = AutoDebugger(api_key)
        debugger.analyzer.model = args.model
        
        # Run auto-fix
        fix_suggestion = debugger.auto_fix_code(args.target_file)
        
        if fix_suggestion is None:
            print("✅ No errors found! Your code ran successfully.")
            return
        
        # Apply fix based on user preference
        if args.auto_apply:
            print("⚠️  Auto-applying fix without confirmation...")
            results = debugger.fixer.apply_fix(fix_suggestion)
            success_count = sum(results.values())
            total_count = len(results)
            print(f"✅ Applied fixes to {success_count}/{total_count} files!")
        else:
            success = debugger.apply_fix_with_confirmation(fix_suggestion)
            if success:
                print("✅ Fix applied successfully!")
                print(f"💡 Try running '{sys.executable} {args.target_file}' again")
            else:
                print("❌ Fix not applied")
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()