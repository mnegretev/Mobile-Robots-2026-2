#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# ALGORITHM COMPARISON: RRT vs A*
#
# This script compares RRT and A* algorithm performance
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

def print_rrt_summary(rrt_results):
    """Print RRT summary statistics"""
    print("\n" + "="*100)
    print("RRT ALGORITHM - SUMMARY STATISTICS")
    print("="*100)
    
    total_tests = len(rrt_results)
    successful = sum(1 for r in rrt_results if r['Success'].lower() == 'true')
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    times = [float(r['Time (ms)']) for r in rrt_results if r['Success'].lower() == 'true']
    
    print(f"\nTotal Experiments: {total_tests}")
    print(f"Successful: {successful}/{total_tests} ({success_rate:.1f}%)")
    if times:
        print(f"Average Execution Time: {sum(times)/len(times):.2f} ms")
        print(f"Min Execution Time: {min(times):.2f} ms")
        print(f"Max Execution Time: {max(times):.2f} ms")
    
    print("\nSuccess Rate by Epsilon:")
    epsilons = sorted(set(float(r['Epsilon']) for r in rrt_results))
    for eps in epsilons:
        eps_results = [r for r in rrt_results if float(r['Epsilon']) == eps]
        eps_success = sum(1 for r in eps_results if r['Success'].lower() == 'true')
        eps_rate = (eps_success / len(eps_results) * 100) if len(eps_results) > 0 else 0
        print(f"  ε={eps:4.1f}: {eps_success:3d}/{len(eps_results):3d} ({eps_rate:5.1f}%)")
    
    print("\nSuccess Rate by Max N:")
    max_ns = sorted(set(int(r['Max N']) for r in rrt_results))
    for n in max_ns:
        n_results = [r for r in rrt_results if int(r['Max N']) == n]
        n_success = sum(1 for r in n_results if r['Success'].lower() == 'true')
        n_rate = (n_success / len(n_results) * 100) if len(n_results) > 0 else 0
        n_times = [float(r['Time (ms)']) for r in n_results if r['Success'].lower() == 'true']
        avg_time = sum(n_times) / len(n_times) if n_times else 0
        print(f"  N={n:5d}: {n_success:3d}/{len(n_results):3d} ({n_rate:5.1f}%), Avg Time={avg_time:6.2f}ms")

def print_astar_summary(astar_results):
    """Print A* summary statistics"""
    print("\n" + "="*100)
    print("A* ALGORITHM - SUMMARY STATISTICS")
    print("="*100)
    
    total_tests = len(astar_results)
    successful = sum(1 for r in astar_results if r['Success'].lower() == 'true')
    success_rate = (successful / total_tests * 100) if total_tests > 0 else 0
    
    times = [float(r['Time (ms)']) for r in astar_results if r['Success'].lower() == 'true']
    
    print(f"\nTotal Experiments: {total_tests}")
    print(f"Successful: {successful}/{total_tests} ({success_rate:.1f}%)")
    if times:
        print(f"Average Execution Time: {sum(times)/len(times):.2f} ms")
        print(f"Min Execution Time: {min(times):.2f} ms")
        print(f"Max Execution Time: {max(times):.2f} ms")
    
    # By cost radius
    print("\nSuccess Rate by Cost Radius:")
    cost_radii = sorted(set(float(r['Cost Radius']) for r in astar_results))
    for rad in cost_radii:
        rad_results = [r for r in astar_results if float(r['Cost Radius']) == rad]
        rad_success = sum(1 for r in rad_results if r['Success'].lower() == 'true')
        rad_rate = (rad_success / len(rad_results) * 100) if len(rad_results) > 0 else 0
        print(f"  rad={rad:4.1f}: {rad_success:3d}/{len(rad_results):3d} ({rad_rate:5.1f}%)")
    
    # With/without diagonals
    print("\nSuccess Rate by Diagonals:")
    for use_diag in [False, True]:
        diag_str = str(use_diag)
        diag_results = [r for r in astar_results if r['Use Diagonals'].lower() == diag_str.lower()]
        if diag_results:
            diag_success = sum(1 for r in diag_results if r['Success'].lower() == 'true')
            diag_rate = (diag_success / len(diag_results) * 100) if len(diag_results) > 0 else 0
            diag_times = [float(r['Time (ms)']) for r in diag_results if r['Success'].lower() == 'true']
            avg_time = sum(diag_times) / len(diag_times) if diag_times else 0
            diag_label = "WITH" if use_diag else "WITHOUT"
            print(f"  {diag_label} diagonals: {diag_success:3d}/{len(diag_results):3d} ({diag_rate:5.1f}%), Avg Time={avg_time:6.2f}ms")

def print_comparison_table(rrt_results, astar_results):
    """Print comparison table by goal"""
    print("\n" + "="*120)
    print("COMPARISON TABLE: RRT vs A* BY GOAL")
    print("="*120)
    
    # Extract unique goals
    rrt_goals = set()
    for r in rrt_results:
        goal_key = (float(r['Start X']), float(r['Start Y']), float(r['Goal X']), float(r['Goal Y']))
        rrt_goals.add(goal_key)
    
    print("\n{:<40} | {:<20} | {:<20} | {:<20}".format("Goal", "RRT Success %", "A* Success %", "RRT Avg Time (ms)"))
    print("-" * 120)
    
    for goal in sorted(rrt_goals):
        sx, sy, gx, gy = goal
        goal_str = f"({sx:.1f},{sy:.1f})->({gx:.1f},{gy:.1f})"
        
        # RRT stats for this goal
        rrt_goal_results = [r for r in rrt_results 
                           if float(r['Start X']) == sx and float(r['Start Y']) == sy 
                           and float(r['Goal X']) == gx and float(r['Goal Y']) == gy]
        rrt_success = sum(1 for r in rrt_goal_results if r['Success'].lower() == 'true')
        rrt_rate = (rrt_success / len(rrt_goal_results) * 100) if rrt_goal_results else 0
        rrt_times = [float(r['Time (ms)']) for r in rrt_goal_results if r['Success'].lower() == 'true']
        rrt_avg_time = sum(rrt_times) / len(rrt_times) if rrt_times else 0
        
        # A* stats for this goal
        astar_goal_results = [r for r in astar_results 
                             if float(r['Start X']) == sx and float(r['Start Y']) == sy 
                             and float(r['Goal X']) == gx and float(r['Goal Y']) == gy]
        astar_success = sum(1 for r in astar_goal_results if r['Success'].lower() == 'true')
        astar_rate = (astar_success / len(astar_goal_results) * 100) if astar_goal_results else 0
        astar_times = [float(r['Time (ms)']) for r in astar_goal_results if r['Success'].lower() == 'true']
        astar_avg_time = sum(astar_times) / len(astar_times) if astar_times else 0
        
        print("{:<40} | {:<20} | {:<20} | {:<20}".format(
            goal_str,
            f"{rrt_rate:.1f}% ({rrt_success}/{len(rrt_goal_results)})",
            f"{astar_rate:.1f}% ({astar_success}/{len(astar_goal_results)})",
            f"{rrt_avg_time:.2f}"
        ))

def print_markdown_comparison(rrt_results, astar_results):
    """Print comparison in Markdown format"""
    print("\n" + "="*120)
    print("MARKDOWN FORMAT - FOR YOUR DOCUMENT")
    print("="*120)
    
    print("\n## Comparison Table: RRT vs A*\n")
    print("| Metric | RRT | A* | Winner |")
    print("|--------|-----|----|----|")
    
    # Overall success rate
    rrt_success = sum(1 for r in rrt_results if r['Success'].lower() == 'true')
    astar_success = sum(1 for r in astar_results if r['Success'].lower() == 'true')
    rrt_rate = (rrt_success / len(rrt_results) * 100) if rrt_results else 0
    astar_rate = (astar_success / len(astar_results) * 100) if astar_results else 0
    winner = "RRT" if rrt_rate > astar_rate else "A*" if astar_rate > rrt_rate else "Tie"
    print(f"| Success Rate | {rrt_rate:.1f}% | {astar_rate:.1f}% | {winner} |")
    
    # Average time
    rrt_times = [float(r['Time (ms)']) for r in rrt_results if r['Success'].lower() == 'true']
    astar_times = [float(r['Time (ms)']) for r in astar_results if r['Success'].lower() == 'true']
    rrt_avg = sum(rrt_times) / len(rrt_times) if rrt_times else float('inf')
    astar_avg = sum(astar_times) / len(astar_times) if astar_times else float('inf')
    winner = "A*" if astar_avg < rrt_avg else "RRT" if rrt_avg < astar_avg else "Tie"
    print(f"| Avg Execution Time | {rrt_avg:.2f} ms | {astar_avg:.2f} ms | {winner} |")
    
    # Min/Max
    rrt_min = min(rrt_times) if rrt_times else 0
    astar_min = min(astar_times) if astar_times else 0
    print(f"| Min Execution Time | {rrt_min:.2f} ms | {astar_min:.2f} ms | {'A*' if astar_min < rrt_min else 'RRT'} |")
    
    rrt_max = max(rrt_times) if rrt_times else 0
    astar_max = max(astar_times) if astar_times else 0
    print(f"| Max Execution Time | {rrt_max:.2f} ms | {astar_max:.2f} ms | {'A*' if astar_max < rrt_max else 'RRT'} |")

def main():
    if len(sys.argv) < 3:
        print("Usage: python compare_algorithms.py <rrt_csv> <astar_csv>")
        print("\nExample:")
        print("  python compare_algorithms.py rrt_experiments_20260224_012246.csv astar_experiments_20260303_120000.csv")
        sys.exit(1)
    
    rrt_csv = sys.argv[1]
    astar_csv = sys.argv[2]
    
    if not Path(rrt_csv).exists():
        print(f"Error: RRT CSV file '{rrt_csv}' not found!")
        sys.exit(1)
    
    if not Path(astar_csv).exists():
        print(f"Error: A* CSV file '{astar_csv}' not found!")
        sys.exit(1)
    
    print(f"Loading RRT results from: {rrt_csv}")
    rrt_results = load_results(rrt_csv)
    print(f"Loaded {len(rrt_results)} RRT experiment results.\n")
    
    print(f"Loading A* results from: {astar_csv}")
    astar_results = load_results(astar_csv)
    print(f"Loaded {len(astar_results)} A* experiment results.\n")
    
    # Print individual summaries
    print_rrt_summary(rrt_results)
    print_astar_summary(astar_results)
    
    # Print comparison
    print_comparison_table(rrt_results, astar_results)
    print_markdown_comparison(rrt_results, astar_results)

if __name__ == '__main__':
    main()
