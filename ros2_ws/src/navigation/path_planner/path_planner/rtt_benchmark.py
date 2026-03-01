#!/usr/bin/env python3
#
# Standalone RRT Benchmark Runner
# Run from terminal with command-line parameters
#

import sys
import argparse
import rclpy
from rrt import RRTNode

def main():
    parser = argparse.ArgumentParser(
        description='Run RRT benchmarks with different parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 rtt_benchmark.py --starts "0,0" "5,5" --goals "10,10" "15,15" --epsilons 0.5 1.0 --attempts 500 1000 --trials 3

  python3 rtt_benchmark.py --starts "0,0" --goals "5,2" "10,4" "7.5,3.6" "3,-3" --epsilons 0.2 0.3 0.4 0.5 --attempts 500 1000 1500 2000 --trials 5
        """)

    parser.add_argument('--starts', nargs='+', default=['0,0'],
                        help='Start points as "x,y" (default: "0,0")')
    parser.add_argument('--goals', nargs='+', default=['5,2'],
                        help='Goal points as "x,y" (default: "5,2")')
    parser.add_argument('--epsilons', nargs='+', type=float, default=[0.2, 0.3, 0.4, 0.5],
                        help='Epsilon values to test (default: 0.2 0.3 0.4 0.5)')
    parser.add_argument('--attempts', nargs='+', type=int, default=[500, 1000, 1500, 2000],
                        help='Max attempts values to test (default: 500 1000 1500 2000)')
    parser.add_argument('--trials', type=int, default=5,
                        help='Number of trials per configuration (default: 5)')

    args = parser.parse_args()

    # Parse start points
    start_points = []
    for start_str in args.starts:
        try:
            x, y = map(float, start_str.split(','))
            start_points.append((x, y))
        except ValueError:
            print(f"Error parsing start point: {start_str}")
            sys.exit(1)

    # Parse goal points
    goal_points = []
    for goal_str in args.goals:
        try:
            x, y = map(float, goal_str.split(','))
            goal_points.append((x, y))
        except ValueError:
            print(f"Error parsing goal point: {goal_str}")
            sys.exit(1)

    print("=" * 80)
    print("RRT BENCHMARK RUNNER")
    print("=" * 80)
    print(f"Start points: {start_points}")
    print(f"Goal points: {goal_points}")
    print(f"Epsilons: {args.epsilons}")
    print(f"Max attempts: {args.attempts}")
    print(f"Trials per config: {args.trials}")
    print("=" * 80)

    # Initialize ROS2
    rclpy.init(args=None)

    # Create RRT node
    print("\nInitializing RRT node...")
    rrt_node = RRTNode()

    # Run benchmark
    print("Running benchmarks...\n")
    try:
        results = rrt_node.benchmark_rrt(
            start_points=start_points,
            goal_points=goal_points,
            epsilons=args.epsilons,
            max_attempts_list=args.attempts,
            num_trials=args.trials
        )
        print("\n" + "=" * 80)
        print(f"Benchmark complete! Total trials: {len(results)}")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user")
    finally:
        rrt_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
