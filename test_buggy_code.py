#!/usr/bin/env python3
"""
Test script with various types of errors for Auto Debugger demonstration
Run with: python debug_cli.py test_buggy_code.py
"""

import math

def calculate_average(numbers):
    """Calculate average of a list of numbers"""
    total = sum(numbers)
    return total / len(numbers)  # Bug: Division by zero if empty list

def process_user_data(user_info):
    """Process user information"""
    name = user_info['name']  # Bug: May not exist
    age = int(user_info['age'])  # Bug: May not be convertible
    return f"User {name} is {age} years old"

def read_file_content(filename):
    """Read and return file content"""
    with open(filename, 'r') as f:  # Bug: File may not exist
        return f.read()

def calculate_circle_area(radius):
    """Calculate area of a circle"""
    if radius < 0:
        raise ValueError("Radius cannot be negative")
    return math.pi * radius ** 2

def main():
    print("=== Auto Debugger Test Cases ===")
    
    # Test Case 1: Division by zero
    print("\n1. Testing empty list average...")
    numbers = []
    try:
        avg = calculate_average(numbers)
        print(f"Average: {avg}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 2: Missing dictionary key
    print("\n2. Testing missing user data...")
    user_data = {'name': 'Alice'}  # Missing 'age' key
    try:
        result = process_user_data(user_data)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 3: File not found
    print("\n3. Testing file reading...")
    try:
        content = read_file_content('nonexistent_file.txt')
        print(f"Content: {content}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 4: Type conversion error
    print("\n4. Testing invalid age conversion...")
    user_data2 = {'name': 'Bob', 'age': 'not_a_number'}
    try:
        result = process_user_data(user_data2)
        print(result)
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Case 5: Custom exception
    print("\n5. Testing negative radius...")
    try:
        area = calculate_circle_area(-5)
        print(f"Area: {area}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()


# Additional buggy functions for testing

def buggy_list_access():
    """Bug: Index out of range"""
    my_list = [1, 2, 3]
    return my_list[10]  # Index error

def buggy_string_operation():
    """Bug: Calling method on None"""
    text = None
    return text.upper()  # AttributeError

def buggy_import():
    """Bug: Import error"""
    import non_existent_module  # ImportError
    return non_existent_module.some_function()

def buggy_recursion(n):
    """Bug: Infinite recursion (be careful with this one!)"""
    if n > 0:
        return buggy_recursion(n)  # Should be n-1
    return 1

# Uncomment any of these to test specific error types:
# print(buggy_list_access())
# print(buggy_string_operation()) 
# print(buggy_import())
# print(buggy_recursion(5))  # Warning: This will cause stack overflow!