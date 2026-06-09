#!/usr/bin/env python3
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# RRT ALGORITHM AUTOMATED TESTS
#
# This script automatically tests the RRT algorithm with different
# parameters and records the results in a CSV file
#

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from nav_msgs.srv import GetPlan
import csv
import time
from datetime import datetime

class RRTExperimenter(Node):
    def __init__(self):
        super().__init__("rrt_experimenter")
        self.get_logger().info("Initializing RRT Experimenter...")
        
        # Wait for the RRT service
        self.clt_plan = self.create_client(GetPlan, '/path_planning/plan_path')
        self.get_logger().info("Waiting for path planning service...")
        while not self.clt_plan.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for path planning service...')
        self.get_logger().info("Path planning service is available!")
        
        # Create CSV file for results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.csv_filename = f"rrt_experiments_{timestamp}.csv"
        self.csv_file = open(self.csv_filename, 'w', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        self.csv_writer.writerow([
            'Start X', 'Start Y', 'Goal X', 'Goal Y', 
            'Epsilon', 'Max N', 'Success', 'Time (ms)', 'Path Length'
        ])
        
        self.get_logger().info(f"Results will be saved to: {self.csv_filename}")

    def run_experiments(self):
        """Run all experiments with different parameters"""
        
        # Define test parameters
        test_goals = [
            ([0.0, 0.0], [5.0, 5.0]),
            ([0.0, 0.0], [8.0, 3.0]),
            ([0.0, 0.0], [3.0, 8.0]),
            ([2.0, 2.0], [7.0, 7.0]),
        ]
        
        epsilon_values = [0.3, 0.5, 1.0, 1.5]
        max_n_values = [100, 500, 1000, 5000]
        
        total_tests = len(test_goals) * len(epsilon_values) * len(max_n_values)
        current_test = 0
        
        self.get_logger().info(f"Starting {total_tests} experiments...")
        
        for goal_idx, (start, goal) in enumerate(test_goals):
            for eps in epsilon_values:
                for max_n in max_n_values:
                    current_test += 1
                    sx, sy = start
                    gx, gy = goal
                    
                    self.get_logger().info(
                        f"Test {current_test}/{total_tests}: "
                        f"Start({sx}, {sy}) -> Goal({gx}, {gy}), "
                        f"ε={eps}, N={max_n}"
                    )
                    
                    # Create request
                    request = GetPlan.Request()
                    request.start = PoseStamped()
                    request.start.pose.position.x = sx
                    request.start.pose.position.y = sy
                    request.goal = PoseStamped()
                    request.goal.pose.position.x = gx
                    request.goal.pose.position.y = gy
                    
                    # Set parameters
                    self.set_parameters_method(eps, max_n)
                    
                    # Call service
                    start_time = time.time()
                    future = self.clt_plan.call_async(request)
                    rclpy.spin_until_future_complete(self, future)
                    end_time = time.time()
                    
                    # Process response
                    try:
                        response = future.result()
                        success = len(response.plan.poses) > 0
                        elapsed_ms = (end_time - start_time) * 1000
                        path_length = len(response.plan.poses)
                        
                        self.csv_writer.writerow([
                            sx, sy, gx, gy,
                            eps, max_n,
                            success, f"{elapsed_ms:.2f}", path_length
                        ])
                        self.csv_file.flush()
                        
                        result_str = "✓" if success else "✗"
                        self.get_logger().info(
                            f"  Result {result_str}: Time={elapsed_ms:.2f}ms, "
                            f"Path length={path_length}"
                        )
                    except Exception as e:
                        self.get_logger().error(f"  Error: {e}")
                        self.csv_writer.writerow([
                            sx, sy, gx, gy,
                            eps, max_n,
                            False, "ERROR", 0
                        ])
                        self.csv_file.flush()
        
        self.csv_file.close()
        self.get_logger().info(f"\nAll experiments completed!")
        self.get_logger().info(f"Results saved to: {self.csv_filename}")
        
        # Print summary
        self.print_summary()

    def set_parameters_method(self, epsilon, max_n):
        """Update parameters dynamically"""
        # Note: This requires the parameters to be declared in the RRT node
        # For now, we'll use ros2 param set command via subprocess
        import subprocess
        subprocess.run([
            'ros2', 'param', 'set', '/rrt_node', 'epsilon', str(epsilon)
        ], capture_output=True)
        subprocess.run([
            'ros2', 'param', 'set', '/rrt_node', 'max_n', str(max_n)
        ], capture_output=True)
        
        # Give a moment for parameters to update
        time.sleep(0.1)

    def print_summary(self):
        """Print summary of results"""
        try:
            import pandas as pd
            df = pd.read_csv(self.csv_filename)
            
            self.get_logger().info("\n" + "="*80)
            self.get_logger().info("SUMMARY OF EXPERIMENTS")
            self.get_logger().info("="*80)
            
            # Overall statistics
            success_count = df['Success'].sum()
            total_count = len(df)
            success_rate = (success_count / total_count) * 100
            
            self.get_logger().info(f"\nOverall Success Rate: {success_rate:.1f}% ({success_count}/{total_count})")
            self.get_logger().info(f"Average Time: {df['Time (ms)'].mean():.2f}ms")
            self.get_logger().info(f"Min Time: {df[df['Success']==True]['Time (ms)'].min():.2f}ms")
            self.get_logger().info(f"Max Time: {df[df['Success']==True]['Time (ms)'].max():.2f}ms")
            
            # Per epsilon statistics
            self.get_logger().info("\n" + "-"*80)
            self.get_logger().info("Success Rate by Epsilon:")
            for eps in sorted(df['Epsilon'].unique()):
                eps_df = df[df['Epsilon'] == eps]
                eps_success = (eps_df['Success'].sum() / len(eps_df)) * 100
                self.get_logger().info(f"  ε={eps}: {eps_success:.1f}%")
            
            # Per max_n statistics
            self.get_logger().info("\nSuccess Rate by Max N:")
            for max_n in sorted(df['Max N'].unique()):
                n_df = df[df['Max N'] == max_n]
                n_success = (n_df['Success'].sum() / len(n_df)) * 100
                avg_time = n_df[n_df['Success']==True]['Time (ms)'].mean()
                self.get_logger().info(f"  N={max_n}: {n_success:.1f}%, Avg Time={avg_time:.2f}ms")
            
            self.get_logger().info("="*80 + "\n")
            
        except ImportError:
            self.get_logger().warn("pandas not installed. Skipping summary.")


def main(args=None):
    rclpy.init(args=args)
    experimenter = RRTExperimenter()
    experimenter.run_experiments()
    experimenter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
