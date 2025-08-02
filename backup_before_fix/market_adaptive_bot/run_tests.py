#!/usr/bin/env python3
"""
Comprehensive test runner for the market adaptive trading bot.
Supports different test modes and configurations.
"""
import os
import sys
import subprocess
import argparse
import time
from pathlib import Path


def run_command(command, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(command)}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print("✅ SUCCESS")
        if result.stdout:
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print("❌ FAILED")
        print(f"Error code: {e.returncode}")
        if e.stdout:
            print("Stdout:")
            print(e.stdout)
        if e.stderr:
            print("Stderr:")
            print(e.stderr)
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("🔍 Checking dependencies...")
    
    required_packages = [
        "pytest",
        "pytest-asyncio",
        "pytest-cov",
        "pytest-html",
        "pytest-xdist"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ Missing packages: {', '.join(missing_packages)}")
        print("Installing missing packages...")
        install_command = [sys.executable, "-m", "pip", "install"] + missing_packages
        if not run_command(install_command, "Installing missing test dependencies"):
            return False
    
    print("✅ All dependencies are available")
    return True


def run_unit_tests():
    """Run unit tests only."""
    print("\n🧪 Running Unit Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "unit",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "Unit Tests")


def run_integration_tests():
    """Run integration tests only."""
    print("\n🔗 Running Integration Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "integration",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "Integration Tests")


def run_ai_tests():
    """Run AI-related tests only."""
    print("\n🤖 Running AI Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "ai",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "AI Tests")


def run_risk_tests():
    """Run risk management tests only."""
    print("\n⚠️ Running Risk Management Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "risk",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "Risk Management Tests")


def run_notification_tests():
    """Run notification tests only."""
    print("\n📢 Running Notification Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "-m", "notification",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "Notification Tests")


def run_all_tests():
    """Run all tests."""
    print("\n🚀 Running All Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, "All Tests")


def run_tests_with_coverage():
    """Run tests with coverage report."""
    print("\n📊 Running Tests with Coverage")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "--cov=src",
        "--cov-report=html",
        "--cov-report=term-missing",
        "--cov-fail-under=80"
    ]
    
    return run_command(command, "Tests with Coverage")


def run_tests_with_html_report():
    """Run tests with HTML report."""
    print("\n📄 Running Tests with HTML Report")
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    html_report = f"test_report_{timestamp}.html"
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        f"--html={html_report}",
        "--self-contained-html"
    ]
    
    success = run_command(command, "Tests with HTML Report")
    
    if success and os.path.exists(html_report):
        print(f"📄 HTML report generated: {html_report}")
    
    return success


def run_tests_parallel():
    """Run tests in parallel."""
    print("\n⚡ Running Tests in Parallel")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-n", "auto",
        "--dist=loadfile"
    ]
    
    return run_command(command, "Parallel Tests")


def run_specific_test_file(test_file):
    """Run a specific test file."""
    print(f"\n🎯 Running Specific Test File: {test_file}")
    
    if not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        return False
    
    command = [
        sys.executable, "-m", "pytest",
        test_file,
        "-v",
        "--tb=short",
        "--strict-markers"
    ]
    
    return run_command(command, f"Specific Test File: {test_file}")


def run_specific_test_class(test_class):
    """Run a specific test class."""
    print(f"\n🎯 Running Specific Test Class: {test_class}")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-k", test_class
    ]
    
    return run_command(command, f"Specific Test Class: {test_class}")


def run_specific_test_method(test_method):
    """Run a specific test method."""
    print(f"\n🎯 Running Specific Test Method: {test_method}")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-k", test_method
    ]
    
    return run_command(command, f"Specific Test Method: {test_method}")


def run_edge_case_tests():
    """Run edge case tests only."""
    print("\n🔍 Running Edge Case Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-k", "edge"
    ]
    
    return run_command(command, "Edge Case Tests")


def run_fast_tests():
    """Run fast tests only (exclude slow tests)."""
    print("\n⚡ Running Fast Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-m", "not slow"
    ]
    
    return run_command(command, "Fast Tests")


def run_slow_tests():
    """Run slow tests only."""
    print("\n🐌 Running Slow Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--strict-markers",
        "-m", "slow"
    ]
    
    return run_command(command, "Slow Tests")


def list_available_tests():
    """List all available tests."""
    print("\n📋 Available Tests")
    
    command = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--collect-only",
        "-q"
    ]
    
    return run_command(command, "List Available Tests")


def main():
    """Main function to run tests based on command line arguments."""
    parser = argparse.ArgumentParser(
        description="Comprehensive test runner for the market adaptive trading bot",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_tests.py --all                    # Run all tests
  python run_tests.py --unit                   # Run unit tests only
  python run_tests.py --integration            # Run integration tests only
  python run_tests.py --ai                     # Run AI tests only
  python run_tests.py --risk                   # Run risk management tests only
  python run_tests.py --coverage               # Run tests with coverage
  python run_tests.py --html                   # Run tests with HTML report
  python run_tests.py --parallel               # Run tests in parallel
  python run_tests.py --file test_models.py    # Run specific test file
  python run_tests.py --class TestModels       # Run specific test class
  python run_tests.py --method test_rsi        # Run specific test method
  python run_tests.py --edge-cases             # Run edge case tests
  python run_tests.py --fast                   # Run fast tests only
  python run_tests.py --slow                   # Run slow tests only
  python run_tests.py --list                   # List all available tests
        """
    )
    
    # Test type options
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--ai", action="store_true", help="Run AI tests only")
    parser.add_argument("--risk", action="store_true", help="Run risk management tests only")
    parser.add_argument("--notification", action="store_true", help="Run notification tests only")
    
    # Report options
    parser.add_argument("--coverage", action="store_true", help="Run tests with coverage report")
    parser.add_argument("--html", action="store_true", help="Run tests with HTML report")
    parser.add_argument("--parallel", action="store_true", help="Run tests in parallel")
    
    # Specific test options
    parser.add_argument("--file", type=str, help="Run specific test file")
    parser.add_argument("--class", dest="test_class", type=str, help="Run specific test class")
    parser.add_argument("--method", type=str, help="Run specific test method")
    
    # Special test categories
    parser.add_argument("--edge-cases", action="store_true", help="Run edge case tests")
    parser.add_argument("--fast", action="store_true", help="Run fast tests only")
    parser.add_argument("--slow", action="store_true", help="Run slow tests only")
    
    # Utility options
    parser.add_argument("--list", action="store_true", help="List all available tests")
    parser.add_argument("--check-deps", action="store_true", help="Check dependencies only")
    
    args = parser.parse_args()
    
    # Change to the market_adaptive_bot directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    print("🧪 Market Adaptive Trading Bot - Test Runner")
    print("=" * 60)
    
    # Check dependencies first
    if not check_dependencies():
        print("❌ Failed to check/setup dependencies")
        return 1
    
    # If only checking dependencies, exit
    if args.check_deps:
        print("✅ Dependency check completed")
        return 0
    
    # Run tests based on arguments
    success = True
    
    if args.list:
        success = list_available_tests()
    elif args.all:
        success = run_all_tests()
    elif args.unit:
        success = run_unit_tests()
    elif args.integration:
        success = run_integration_tests()
    elif args.ai:
        success = run_ai_tests()
    elif args.risk:
        success = run_risk_tests()
    elif args.notification:
        success = run_notification_tests()
    elif args.coverage:
        success = run_tests_with_coverage()
    elif args.html:
        success = run_tests_with_html_report()
    elif args.parallel:
        success = run_tests_parallel()
    elif args.file:
        success = run_specific_test_file(args.file)
    elif args.test_class:
        success = run_specific_test_class(args.test_class)
    elif args.method:
        success = run_specific_test_method(args.method)
    elif args.edge_cases:
        success = run_edge_case_tests()
    elif args.fast:
        success = run_fast_tests()
    elif args.slow:
        success = run_slow_tests()
    else:
        # Default: run all tests
        print("No specific test type specified, running all tests...")
        success = run_all_tests()
    
    # Final summary
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests completed successfully!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 