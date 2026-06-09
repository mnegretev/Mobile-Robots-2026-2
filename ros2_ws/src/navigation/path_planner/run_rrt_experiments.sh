#!/bin/bash
#
# MOBILE ROBOTS - FI-UNAM, 2026-2
# RRT EXPERIMENTS AUTOMATION SCRIPT
#

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_ROOT=$(cd "${SCRIPT_DIR}/../../.." && pwd)

echo "======================================================================"
echo "RRT ALGORITHM AUTOMATED EXPERIMENTS"
echo "======================================================================"
echo ""
echo "Workspace: $WORKSPACE_ROOT"
echo ""

# Check if arguments provided
if [ "$1" == "help" ] || [ "$1" == "-h" ] || [ "$1" == "--help" ]; then
    echo "Usage: ./run_rrt_experiments.sh [command]"
    echo ""
    echo "Commands:"
    echo "  build       - Build/rebuild the path_planner package"
    echo "  run         - Run the automated experiments"
    echo "  analyze     - Analyze the latest results"
    echo "  clean       - Remove build artifacts"
    echo "  help        - Show this help message"
    echo ""
    echo "Example workflow:"
    echo "  ./run_rrt_experiments.sh build    # Build the package"
    echo "  ./run_rrt_experiments.sh run      # Run experiments (10-15 minutes typical)"
    echo "  ./run_rrt_experiments.sh analyze  # Analyze results"
    echo ""
    exit 0
fi

# Build command
if [ "$1" == "build" ] || [ "$1" == "" ]; then
    echo "Building path_planner package..."
    cd "$WORKSPACE_ROOT"
    colcon build --packages-select path_planner
    source install/setup.bash
    echo "✓ Build complete"
    echo ""
fi

# Run experiments
if [ "$1" == "run" ] || [ "$1" == "" ]; then
    echo "Starting RRT experiments..."
    echo ""
    echo "IMPORTANT: Make sure you have running in other terminals:"
    echo "  1. map_server or your ROS2 simulator with map service"
    echo "  2. cost_map node (will be started automatically if available)"
    echo "  3. rrt node (will be started automatically if available)"
    echo ""
    read -p "Press Enter to continue..."
    echo ""
    
    source "$WORKSPACE_ROOT/install/setup.bash"
    cd "$WORKSPACE_ROOT"
    
    # Try to find and run test_experiments
    if command -v ros2 &> /dev/null; then
        echo "Running experiments via ROS2..."
        ros2 run path_planner test_experiments
    else
        echo "ROS2 not found. Trying direct Python execution..."
        python3 "install/lib/python*/site-packages/path_planner/test_rrt_experiments.py"
    fi
fi

# Analyze results
if [ "$1" == "analyze" ]; then
    # Find the latest CSV file
    LATEST_CSV=$(find . -name "rrt_experiments_*.csv" -type f -printf '%T@ %p\n' | sort -rn | head -1 | cut -d' ' -f2-)
    
    if [ -z "$LATEST_CSV" ]; then
        echo "Error: No experiment results found!"
        echo "Please run './run_rrt_experiments.sh run' first"
        exit 1
    fi
    
    echo "Found results: $LATEST_CSV"
    echo ""
    echo "Analyzing results..."
    echo ""
    
    source "$WORKSPACE_ROOT/install/setup.bash"
    python3 "install/lib/python*/site-packages/path_planner/analyze_results.py" "$LATEST_CSV"
fi

# Clean command
if [ "$1" == "clean" ]; then
    echo "Cleaning build artifacts..."
    cd "$WORKSPACE_ROOT"
    rm -rf build install log
    echo "✓ Clean complete"
fi

echo ""
echo "======================================================================"
echo "Complete! Check the output above for results."
echo "======================================================================"
