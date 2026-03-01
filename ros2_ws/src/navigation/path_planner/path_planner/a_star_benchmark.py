import sys
import argparse
import rclpy
from a_star import AStarNode

def main():
    parser = argparse.ArgumentParser(
        description='Run A* benchmarks with different parameters',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python3 a_star_benchmark.py --starts "0,0" "5,5" --goals "10,10" "15,15" --diagonals True False --trials 3 
  python3 a_star_benchmark.py --starts "0,0" --goals "5,2" "10,4" "7.5,3.6" "3,-3" --trials 5
        """)
    
    parser.add_argument('--starts', nargs='+', default=['0,0'],
                        help='Start points as "x,y" (default: "0,0")')
    parser.add_argument('--goals', nargs='+', default=['5,2'],
                        help='Goal points as "x,y" (default: "5,2")')
    parser.add_argument('--diagonals', nargs='+', type=bool, default=[True, False],
                        help='Whether to allow diagonal movements (default: True False)')
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
    print("A* BENCHMARK RUNNER")
    print("=" * 80)
    print(f"Start points: {start_points}")
    print(f"Goal points: {goal_points}")
    print(f"Diagonals: {args.diagonals}")
    print(f"Trials per config: {args.trials}")
    print("=" * 80)
    # Initialize ROS2 node
    rclpy.init()
    # Create A* node
    print("\nInitializing A* node...")
    a_star_node = AStarNode()
    # Run benchmarks
    print("\nRunning benchmarks...")
    try:
        results = a_star_node.run_benchmarks(start_points, 
                                            goal_points, 
                                            args.diagonals, 
                                            args.trials)
        print("\n" + "=" * 80)
        print(f"Benchmark complete! Total trials: {len(results)}")
        print("=" * 80)
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
    finally:
        a_star_node.destroy_node()
        rclpy.shutdown()
        
if __name__ == '__main__':
    main()
    