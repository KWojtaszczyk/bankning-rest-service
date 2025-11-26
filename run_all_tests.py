import pytest
import sys
import os
import time

# Run pytest and capture output
output_file = "full_project_test_results.txt"
start_time = time.time()

test_files = [
    "app/tests/test_auth.py",
    "app/tests/test_accounts.py",
    "app/tests/test_cards.py",
    "app/tests/test_transactions.py",
    "app/tests/test_statements.py",
    "app/tests/test_card_transactions.py"
]

with open(output_file, "w", encoding="utf-8") as f:
    sys.stdout = f
    sys.stderr = f
    
    print(f"Starting Full Project Test Suite at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    total_exit_code = 0
    
    for test_file in test_files:
        print(f"\nRunning {test_file}...")
        print("-" * 40)
        exit_code = pytest.main([test_file, "-v"])
        print(f"\nExit Code: {exit_code}")
        if exit_code != 0:
            total_exit_code = 1
            print(f"❌ TESTS FAILED in {test_file}")
        else:
            print(f"✅ TESTS PASSED in {test_file}")
        print("="*60)

    duration = time.time() - start_time
    print(f"\nTotal Duration: {duration:.2f} seconds")
    print(f"Overall Result: {'❌ FAILED' if total_exit_code != 0 else '✅ PASSED'}")

sys.stdout = sys.__stdout__
sys.stderr = sys.__stderr__

print(f"Full test suite completed. Results saved to {output_file}")
