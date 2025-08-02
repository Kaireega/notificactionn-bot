#!/usr/bin/env python3
"""
Comprehensive Test Runner - Executes all test suites and generates reports
"""
import os
import sys
import time
import json
import subprocess
from datetime import datetime
from pathlib import Path
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description):
    """Run a command and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    start_time = time.time()
    try:
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            cwd=project_root,
            timeout=300  # 5 minute timeout
        )
        end_time = time.time()
        
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode,
            'duration': end_time - start_time
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': 'Command timed out after 5 minutes',
            'returncode': -1,
            'duration': 300
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1,
            'duration': 0
        }


def run_api_tests():
    """Run API connectivity tests."""
    return run_command(
        ['python', 'run_api_tests.py'],
        'API Connectivity Tests'
    )


def run_integration_tests():
    """Run integration tests."""
    return run_command(
        ['python', '-m', 'pytest', 'tests/test_integration.py', '-v'],
        'Integration Tests'
    )


def run_edge_case_tests():
    """Run edge case tests."""
    return run_command(
        ['python', '-m', 'pytest', 'tests/test_edge_cases.py', '-v'],
        'Edge Case Tests'
    )


def run_performance_tests():
    """Run performance tests."""
    return run_command(
        ['python', '-m', 'pytest', 'tests/test_performance.py', '-v'],
        'Performance Tests'
    )


def run_legacy_tests():
    """Run legacy system tests."""
    # Test legacy bot
    bot_test = run_command(
        ['python', 'run_bot.py', '--test-mode'],
        'Legacy Bot Tests'
    )
    
    # Test stream bot
    stream_test = run_command(
        ['python', '-c', 'from stream_bot.stream_bot import run_bot; run_bot()'],
        'Stream Bot Tests'
    )
    
    return {
        'bot_test': bot_test,
        'stream_test': stream_test,
        'success': bot_test['success'] and stream_test['success']
    }


def run_simulation_tests():
    """Run simulation and backtesting tests."""
    return run_command(
        ['python', '-m', 'pytest', 'simulation/', '-v'],
        'Simulation Tests'
    )


def run_exploration_tests():
    """Run exploration notebook tests."""
    # Convert notebooks to Python and run
    notebooks = [
        'exploration/api_test.ipynb',
        'exploration/Data Test.ipynb',
        'exploration/candle_patterns_test.ipynb'
    ]
    
    results = {}
    for notebook in notebooks:
        if os.path.exists(notebook):
            result = run_command(
                ['jupyter', 'nbconvert', '--to', 'python', notebook],
                f'Convert {notebook}'
            )
            if result['success']:
                py_file = notebook.replace('.ipynb', '.py')
                if os.path.exists(py_file):
                    test_result = run_command(
                        ['python', py_file],
                        f'Run {notebook}'
                    )
                    results[notebook] = test_result
                else:
                    results[notebook] = {
                        'success': False,
                        'stderr': f'Python file {py_file} not created'
                    }
            else:
                results[notebook] = result
    
    return results


def run_database_tests():
    """Run database connectivity and operation tests."""
    return run_command(
        ['python', '-c', 'from db.db import DataDB; d = DataDB(); d.test_connection()'],
        'Database Tests'
    )


def run_web_server_tests():
    """Run web server tests."""
    # Test server startup
    server_test = run_command(
        ['python', '-c', 'from server import app; print("Server imports successfully")'],
        'Web Server Import Test'
    )
    
    # Test API endpoints (if server is running)
    api_test = run_command(
        ['curl', '-f', 'http://localhost:5000/api/test'],
        'Web API Endpoint Test'
    )
    
    return {
        'server_test': server_test,
        'api_test': api_test,
        'success': server_test['success']
    }


def generate_test_report(results):
    """Generate comprehensive test report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'summary': {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        },
        'details': results,
        'recommendations': []
    }
    
    # Calculate summary
    for test_name, result in results.items():
        if isinstance(result, dict) and 'success' in result:
            report['summary']['total_tests'] += 1
            if result['success']:
                report['summary']['passed'] += 1
            else:
                report['summary']['failed'] += 1
                report['recommendations'].append(f"Fix {test_name}")
    
    # Generate recommendations
    if report['summary']['failed'] > 0:
        report['recommendations'].append("Review failed tests and fix critical issues")
    
    if report['summary']['passed'] == 0:
        report['recommendations'].append("No tests passed - check test environment setup")
    
    return report


def save_report(report, output_file):
    """Save test report to file."""
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\nTest report saved to: {output_file}")


def print_report_summary(report):
    """Print test report summary."""
    print(f"\n{'='*80}")
    print("COMPREHENSIVE TEST REPORT")
    print(f"{'='*80}")
    print(f"Timestamp: {report['timestamp']}")
    print(f"Total Tests: {report['summary']['total_tests']}")
    print(f"Passed: {report['summary']['passed']}")
    print(f"Failed: {report['summary']['failed']}")
    print(f"Success Rate: {(report['summary']['passed'] / max(report['summary']['total_tests'], 1)) * 100:.1f}%")
    
    if report['recommendations']:
        print(f"\nRecommendations:")
        for rec in report['recommendations']:
            print(f"  - {rec}")
    
    print(f"\nDetailed results:")
    for test_name, result in report['details'].items():
        status = "✅ PASS" if result.get('success', False) else "❌ FAIL"
        duration = f"{result.get('duration', 0):.2f}s"
        print(f"  {test_name}: {status} ({duration})")
        
        if not result.get('success', False) and result.get('stderr'):
            print(f"    Error: {result['stderr'][:100]}...")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description='Run comprehensive tests for the trading bot system')
    parser.add_argument('--output', '-o', default='test_report.json', 
                       help='Output file for test report (default: test_report.json)')
    parser.add_argument('--skip', '-s', nargs='+', 
                       help='Skip specific test categories')
    parser.add_argument('--only', nargs='+', 
                       help='Run only specific test categories')
    
    args = parser.parse_args()
    
    print("Starting Comprehensive Test Suite")
    print(f"Project Root: {project_root}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Define all test categories
    test_categories = {
        'api_tests': run_api_tests,
        'integration_tests': run_integration_tests,
        'edge_case_tests': run_edge_case_tests,
        'performance_tests': run_performance_tests,
        'legacy_tests': run_legacy_tests,
        'simulation_tests': run_simulation_tests,
        'exploration_tests': run_exploration_tests,
        'database_tests': run_database_tests,
        'web_server_tests': run_web_server_tests
    }
    
    # Filter test categories based on arguments
    if args.only:
        test_categories = {k: v for k, v in test_categories.items() if k in args.only}
    
    if args.skip:
        test_categories = {k: v for k, v in test_categories.items() if k not in args.skip}
    
    # Run tests
    results = {}
    for category_name, test_function in test_categories.items():
        print(f"\nRunning {category_name}...")
        try:
            results[category_name] = test_function()
        except Exception as e:
            results[category_name] = {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'returncode': -1,
                'duration': 0
            }
    
    # Generate and save report
    report = generate_test_report(results)
    save_report(report, args.output)
    print_report_summary(report)
    
    # Exit with appropriate code
    if report['summary']['failed'] > 0:
        print(f"\n❌ Tests completed with {report['summary']['failed']} failures")
        sys.exit(1)
    else:
        print(f"\n✅ All tests passed!")
        sys.exit(0)


if __name__ == "__main__":
    main() 