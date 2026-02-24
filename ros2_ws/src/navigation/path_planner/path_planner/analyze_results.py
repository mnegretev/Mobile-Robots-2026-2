#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# RRT RESULTS ANALYZER
#
# This script reads the CSV from experiments and generates formatted tables
#

import csv
import sys
from pathlib import Path
from collections import defaultdict

def load_results(csv_file):
    """Load results from CSV file"""
    results = []
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append(row)
    return results

def print_table_by_goal_and_epsilon(results):
    """Print table: Goals vs Epsilon values"""
    print("\n" + "="*100)
    print("TABLE 1: Success Rate and Execution Time by Goal and Epsilon")
    print("="*100)
    
    # Group by goal and epsilon
    grouped = defaultdict(lambda: defaultdict(list))
    for row in results:
        goal_key = f"({row['Start X']}, {row['Start Y']}) → ({row['Goal X']}, {row['Goal Y']})"
        eps = float(row['Epsilon'])
        grouped[goal_key][eps].append(row)
    
    # Print header
    epsilons = sorted(set(float(row['Epsilon']) for row in results))
    header = "Goal" + " " * 50
    for eps in epsilons:
        header += f"  ε={eps:4.1f}  "
    header += "\n" + "-" * 100
    print(header)
    
    # Print rows
    for goal in sorted(grouped.keys()):
        row_data = goal[:50].ljust(50)
        for eps in epsilons:
            if eps in grouped[goal]:
                tests = grouped[goal][eps]
                success = sum(1 for t in tests if t['Success'].lower() == 'true')
                total = len(tests)
                rate = (success / total * 100) if total > 0 else 0
                avg_time = sum(float(t['Time (ms)']) for t in tests if t['Success'].lower() == 'true') / success if success > 0 else 0
                row_data += f" {success}/{total} ({rate:5.1f}%) [{avg_time:6.2f}ms] "
            else:
                row_data += "       -        "
        print(row_data)
    print()

def print_table_by_goal_and_n(results):
    """Print table: Goals vs N values"""
    print("\n" + "="*100)
    print("TABLE 2: Success Rate and Execution Time by Goal and Max N")
    print("="*100)
    
    # Group by goal and max_n
    grouped = defaultdict(lambda: defaultdict(list))
    for row in results:
        goal_key = f"({row['Start X']}, {row['Start Y']}) → ({row['Goal X']}, {row['Goal Y']})"
        max_n = int(row['Max N'])
        grouped[goal_key][max_n].append(row)
    
    # Print header
    max_ns = sorted(set(int(row['Max N']) for row in results))
    header = "Goal" + " " * 50
    for n in max_ns:
        header += f"    N={n:5d}    "
    header += "\n" + "-" * 100
    print(header)
    
    # Print rows
    for goal in sorted(grouped.keys()):
        row_data = goal[:50].ljust(50)
        for n in max_ns:
            if n in grouped[goal]:
                tests = grouped[goal][n]
                success = sum(1 for t in tests if t['Success'].lower() == 'true')
                total = len(tests)
                rate = (success / total * 100) if total > 0 else 0
                avg_time = sum(float(t['Time (ms)']) for t in tests if t['Success'].lower() == 'true') / success if success > 0 else 0
                row_data += f" {success}/{total} ({rate:5.1f}%) [{avg_time:6.2f}ms] "
            else:
                row_data += "       -        "
        print(row_data)
    print()

def print_table_detailed(results):
    """Print detailed table with all experiments"""
    print("\n" + "="*130)
    print("TABLE 3: Detailed Results of All Experiments")
    print("="*130)
    
    header = (
        "Start (X, Y)      | Goal (X, Y)       | Epsilon | Max N | Success | Time (ms) | Path Length\n"
        + "-" * 130
    )
    print(header)
    
    for row in results:
        line = (
            f"{row['Start X']:>7} {row['Start Y']:>7} | "
            f"{row['Goal X']:>7} {row['Goal Y']:>7} | "
            f"{float(row['Epsilon']):>7.1f} | "
            f"{int(row['Max N']):>5} | "
            f"{str(row['Success']):>7} | "
            f"{float(row['Time (ms)']):>9.2f} | "
            f"{int(row['Path Length']):>11}"
        )
        print(line)
    print()

def print_statistics(results):
    """Print overall statistics"""
    print("\n" + "="*100)
    print("STATISTICS")
    print("="*100)
    
    total_tests = len(results)
    successful = sum(1 for r in results if r['Success'].lower() == 'true')
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    times = [float(r['Time (ms)']) for r in results if r['Success'].lower() == 'true']
    
    print(f"\nTotal Experiments: {total_tests}")
    print(f"Successful: {successful}/{total_tests} ({success_rate:.1f}%)")
    if times:
        print(f"Average Execution Time: {sum(times)/len(times):.2f} ms")
        print(f"Min Execution Time: {min(times):.2f} ms")
        print(f"Max Execution Time: {max(times):.2f} ms")
    
    # By epsilon
    print("\nSuccess Rate by Epsilon:")
    epsilons = sorted(set(float(r['Epsilon']) for r in results))
    for eps in epsilons:
        eps_results = [r for r in results if float(r['Epsilon']) == eps]
        eps_success = sum(1 for r in eps_results if r['Success'].lower() == 'true')
        eps_rate = (eps_success / len(eps_results) * 100) if len(eps_results) > 0 else 0
        print(f"  ε={eps:4.1f}: {eps_success:3d}/{len(eps_results):3d} ({eps_rate:5.1f}%)")
    
    # By N
    print("\nSuccess Rate by Max N:")
    max_ns = sorted(set(int(r['Max N']) for r in results))
    for n in max_ns:
        n_results = [r for r in results if int(r['Max N']) == n]
        n_success = sum(1 for r in n_results if r['Success'].lower() == 'true')
        n_rate = (n_success / len(n_results) * 100) if len(n_results) > 0 else 0
        n_times = [float(r['Time (ms)']) for r in n_results if r['Success'].lower() == 'true']
        avg_time = sum(n_times) / len(n_times) if n_times else 0
        print(f"  N={n:5d}: {n_success:3d}/{len(n_results):3d} ({n_rate:5.1f}%), Avg Time={avg_time:6.2f}ms")
    
    print()

def convert_to_markdown(results):
    """Convert results to Markdown table format"""
    print("\n" + "="*100)
    print("MARKDOWN FORMAT (for your document)")
    print("="*100)
    
    print("\n### Summary Statistics\n")
    total_tests = len(results)
    successful = sum(1 for r in results if r['Success'].lower() == 'true')
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Total Experiments | {total_tests} |")
    print(f"| Successful | {successful}/{total_tests} ({success_rate:.1f}%) |")
    
    times = [float(r['Time (ms)']) for r in results if r['Success'].lower() == 'true']
    if times:
        print(f"| Avg Execution Time | {sum(times)/len(times):.2f} ms |")
        print(f"| Min Execution Time | {min(times):.2f} ms |")
        print(f"| Max Execution Time | {max(times):.2f} ms |")
    
    print("\n### Results by Epsilon\n")
    print("| Epsilon | Success | Total | Rate |")
    print("|---------|---------|-------|------|")
    epsilons = sorted(set(float(r['Epsilon']) for r in results))
    for eps in epsilons:
        eps_results = [r for r in results if float(r['Epsilon']) == eps]
        eps_success = sum(1 for r in eps_results if r['Success'].lower() == 'true')
        eps_rate = (eps_success / len(eps_results) * 100) if len(eps_results) > 0 else 0
        print(f"| {eps:.1f} | {eps_success} | {len(eps_results)} | {eps_rate:.1f}% |")
    
    print("\n### Results by Max N\n")
    print("| Max N | Success | Total | Rate | Avg Time (ms) |")
    print("|-------|---------|-------|------|---------------|")
    max_ns = sorted(set(int(r['Max N']) for r in results))
    for n in max_ns:
        n_results = [r for r in results if int(r['Max N']) == n]
        n_success = sum(1 for r in n_results if r['Success'].lower() == 'true')
        n_rate = (n_success / len(n_results) * 100) if len(n_results) > 0 else 0
        n_times = [float(r['Time (ms)']) for r in n_results if r['Success'].lower() == 'true']
        avg_time = sum(n_times) / len(n_times) if n_times else 0
        print(f"| {n} | {n_success} | {len(n_results)} | {n_rate:.1f}% | {avg_time:.2f} |")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_results.py <csv_file>")
        print("\nExample:")
        print("  python analyze_results.py rrt_experiments_20260224_123456.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    
    if not Path(csv_file).exists():
        print(f"Error: File '{csv_file}' not found!")
        sys.exit(1)
    
    print(f"Loading results from: {csv_file}")
    results = load_results(csv_file)
    print(f"Loaded {len(results)} experiment results.\n")
    
    # Print all tables
    print_statistics(results)
    print_table_detailed(results)
    print_table_by_goal_and_epsilon(results)
    print_table_by_goal_and_n(results)
    convert_to_markdown(results)

if __name__ == '__main__':
    main()
