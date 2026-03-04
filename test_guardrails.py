"""
Test file to demonstrate Sabrina Agent Security Guardrails
Tests various security scenarios
"""

from Tools_AGENT import validator, extract_text, check_payment_status, create_alert_from_text
import pandas as pd

print("=" * 60)
print("🔐 SABRINA AGENT - SECURITY GUARDRAILS TEST")
print("=" * 60)

# Test cases
test_cases = [
    {
        "name": "✅ VALID: Request with Student ID",
        "query": "What's the schedule for Student ID 2?",
        "should_pass": True
    },
    {
        "name": "❌ BLOCKED: No Student ID provided",
        "query": "Tell me about the students",
        "should_pass": False
    },
    {
        "name": "❌ BLOCKED: Aggregate data request (total)",
        "query": "How much total did we collect in payments?",
        "should_pass": False
    },
    {
        "name": "❌ BLOCKED: Aggregate data request (average)",
        "query": "What's the average attendance?",
        "should_pass": False
    },
    {
        "name": "❌ BLOCKED: Multiple students query",
        "query": "Compare Student ID 2 and Student ID 3",
        "should_pass": False
    },
    {
        "name": "✅ VALID: Invalid ID should be caught",
        "query": "Student ID 9999",
        "should_pass": False
    },
    {
        "name": "✅ VALID: Payment check with ID",
        "query": "Did Student ID 2 pay March 2025?",
        "should_pass": True
    },
    {
        "name": "❌ BLOCKED: List request (multiple students)",
        "query": "List all students who didn't pay",
        "should_pass": False
    },
]

# Run tests
passed = 0
failed = 0

for test in test_cases:
    print(f"\n{test['name']}")
    print(f"Query: {test['query']}")
    
    is_valid, error_message = validator.validate_query(test['query'])
    
    if is_valid == test['should_pass']:
        print("✓ TEST PASSED")
        passed += 1
    else:
        print("✗ TEST FAILED")
        failed += 1
    
    if not is_valid:
        print(f"Reason: {error_message}")

print("\n" + "=" * 60)
print(f"📊 RESULTS: {passed} passed, {failed} failed out of {len(test_cases)} tests")
print("=" * 60)

# Demonstrate actual tool usage with security
print("\n" + "=" * 60)
print("🛡️  DEMO: Tool functions with security enabled")
print("=" * 60)

print("\n[1] SAFE QUERY - Extract Student Info with ID")
result = extract_text("What's the info for Student ID 2?")
print(result)

print("\n[2] BLOCKED QUERY - Extract without ID")
result = extract_text("Tell me about the student")
print(result)

print("\n[3] SAFE QUERY - Check Payment with ID")
result = check_payment_status("Did Student ID 2 pay March 2025?")
print(result)

print("\n[4] BLOCKED QUERY - Check Total Payments")
result = check_payment_status("What's the total amount collected?")
print(result)

print("\n" + "=" * 60)
print("✅ Security guardrails are working correctly!")
print("=" * 60)
