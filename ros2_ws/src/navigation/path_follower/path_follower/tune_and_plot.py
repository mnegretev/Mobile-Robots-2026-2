"""Tune and compare Pure Pursuit vs Stanley controllers.

This script runs a simple kinematic simulation (differential drive) following a given 2D path
and performs a grid search over controller parameters to identify which values minimize
tracking error.

It also provides helpers to plot the "desired" path vs the "actual" executed trajectory.

Usage:
  python3 tune_and_plot.py --mode tune
  python3 tune_and_plot.py --mode plot --data-file <path/to/data.txt> --path-file <path/to/desired_path.txt>

Note: This script does NOT require ROS. It is intended for offline experimentation.
"""

from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Trajectory:
    x: np.ndarray
    y: np.ndarray
    theta: np.ndarray


def generate_test_path() -> np.ndarray:
    """Generate a representative 2D path (a smooth S-curve followed by a straight segment)."""
    # Create an S-shaped path in the plane
    t = np.linspace(0.0, 1.0, 200)
    x = 5.0 * t
    y = 2.0 * np.sin(2.0 * math.pi * t)
    # Append a straight segment to the end
    x2 = np.linspace(x[-1], x[-1] + 2.0, 50)
    y2 = np.full_like(x2, y[-1])
    return np.vstack([np.concatenate([x, x2]), np.concatenate([y, y2])]).T


def wrap_to_pi(angle: float) -> float:
    """Normalize angle to (-pi, pi]."""
    return (angle + math.pi) % (2 * math.pi) - math.pi


def simulate_differential_drive(
    path: np.ndarray,
    control_fn,
    dt: float = 0.05,
    max_steps: int = 8000,
    tol: float = 0.1,
) -> Tuple[Trajectory, np.ndarray]:
    """Simulate a differential-drive robot following a path using `control_fn`.

    Args:
        path: Nx2 array of [x, y] points.
        control_fn: Callable(robot_x, robot_y, robot_theta) -> (v, w)
        dt: time step.
        max_steps: maximum number of steps to simulate.
        tol: distance to final goal at which the simulation terminates.

    Returns:
        (trajectory, errors) where errors is the distance to the nearest path point at each step.
    """

    x = 0.0
    y = 0.0
    theta = 0.0

    xs = []
    ys = []
    thetas = []
    errors = []

    goal = path[-1]

    for step in range(max_steps):
        dx = goal[0] - x
        dy = goal[1] - y
        dist_to_goal = math.hypot(dx, dy)
        if dist_to_goal < tol:
            break

        v, w = control_fn(x, y, theta)
        # clamp speeds to reasonable values (should already be done by controller)
        v = float(np.clip(v, -1.0, 1.0))
        w = float(np.clip(w, -2.0, 2.0))

        # simple unicycle integration
        x += v * math.cos(theta) * dt
        y += v * math.sin(theta) * dt
        theta = wrap_to_pi(theta + w * dt)

        xs.append(x)
        ys.append(y)
        thetas.append(theta)

        # distance to closest point on path (approximate by sampling)
        dists = np.hypot(path[:, 0] - x, path[:, 1] - y)
        errors.append(float(np.min(dists)))

    return Trajectory(np.array(xs), np.array(ys), np.array(thetas)), np.array(errors)


def stanley_control_factory(
    path: np.ndarray, Kd: float, Ka: float, v_max: float, w_max: float
):
    """Returns a function that computes Stanley control (v,w) given robot state."""

    def nearest_point_and_angle(rx: float, ry: float) -> Tuple[float, float, float]:
        P = np.vstack([path[:, 0], path[:, 1]]).T
        Pr = np.array([rx, ry])
        distances = np.linalg.norm(P - Pr, axis=1)
        i = int(np.argmin(distances))
        i_next = min(i + 1, len(P) - 1)
        i_prev = max(i - 1, 0)
        Pi = P[i]
        Pn = P[i_next]
        Pp = P[i_prev]
        theta_i = math.atan2(Pn[1] - Pp[1], Pn[0] - Pp[0])
        return float(Pi[0]), float(Pi[1]), float(theta_i)

    def control(rx: float, ry: float, ra: float):
        xi, yi, theta_i = nearest_point_and_angle(rx, ry)
        theta_e = (theta_i - math.atan2(ry - yi, rx - xi) + math.pi) % (2 * math.pi) - math.pi
        et = math.hypot(rx - xi, ry - yi) * np.sign(theta_e)
        alpha = (theta_i - ra + math.pi) % (2 * math.pi) - math.pi
        v = v_max * math.exp(-5.0 * (et ** 2 + alpha ** 2))
        w = Ka * alpha + Kd * et
        w = float(np.clip(w, -w_max, w_max))
        return float(v), float(w)

    return control


def pure_pursuit_control_factory(
    path: np.ndarray, alpha: float, beta: float, v_max: float, w_max: float
):
    """Returns a function that computes Pure Pursuit control (v,w) given robot state."""

    idx = 0
    goal = path[idx]

    def control(rx: float, ry: float, ra: float):
        nonlocal idx, goal
        # switch goal if close enough, but never go past end
        if np.hypot(goal[0] - rx, goal[1] - ry) < 0.3 and idx < len(path) - 1:
            idx += 1
            goal = path[idx]

        error_a = math.atan2(goal[1] - ry, goal[0] - rx) - ra
        error_a = wrap_to_pi(error_a)

        v = v_max * math.exp(-error_a * error_a / alpha) if alpha > 0 else v_max
        w = w_max * (2.0 / (1.0 + math.exp(-error_a / beta)) - 1.0) if beta > 0 else 0.0
        return float(v), float(w)

    return control


def evaluate_controller(
    name: str,
    path: np.ndarray,
    control_factory,
    param_grid: List[Tuple[Tuple[float, float], Tuple[float, float]]],
    v_max: float = 0.8,
    w_max: float = 1.0,
):
    """Evaluate a controller over a parameter grid.

    param_grid is a list of ((p1,p2), (p3,p4)) representing search ranges.
    Returns a sorted list of results (lower mean error is better).
    """

    results = []

    for (v1, v2), (v3, v4) in param_grid:
        # create grid for first and second coefficients
        for p1 in np.linspace(v1, v2, 5):
            for p2 in np.linspace(v3, v4, 5):
                control = control_factory(path, p1, p2, v_max, w_max)
                traj, errors = simulate_differential_drive(path, control)
                mean_err = float(np.mean(errors)) if len(errors) > 0 else float('inf')
                final_error = float(np.hypot(path[-1, 0] - traj.x[-1], path[-1, 1] - traj.y[-1])) if len(traj.x) > 0 else float('inf')
                results.append({
                    'controller': name,
                    'p1': p1,
                    'p2': p2,
                    'mean_error': mean_err,
                    'final_error': final_error,
                    'steps': len(traj.x),
                })
    # sort by mean_error then final_error
    results.sort(key=lambda r: (r['mean_error'], r['final_error']))
    return results


def save_csv(filepath: str, header: List[str], rows: List[List[float]]):
    with open(filepath, 'w') as f:
        f.write(','.join(header) + '\n')
        for r in rows:
            f.write(','.join(str(x) for x in r) + '\n')


def plot_trajectory(path: np.ndarray, trajectory: Trajectory, out_file: str):
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        raise RuntimeError('matplotlib is required for plotting. Install it with `pip install matplotlib`.')

    plt.figure(figsize=(6, 5))
    plt.plot(path[:, 0], path[:, 1], 'k--', label='Desired path')
    plt.plot(trajectory.x, trajectory.y, 'b-', label='Actual trajectory')
    plt.scatter([path[0, 0], path[-1, 0]], [path[0, 1], path[-1, 1]], c=['green', 'red'], label='Start/Goal')
    plt.gca().set_aspect('equal', 'box')
    plt.legend()
    plt.grid(True)
    plt.xlabel('x (m)')
    plt.ylabel('y (m)')
    plt.title('Path Following Comparison')
    plt.tight_layout()
    plt.savefig(out_file)
    plt.close()


def main():
    parser = argparse.ArgumentParser(description='Tune path following controllers.')
    parser.add_argument(
        '--mode', choices=['tune', 'plot'], default='tune', help='Mode to run: tune (grid search) or plot (from files).'
    )
    parser.add_argument('--output-dir', default='.', help='Directory to save results.')
    parser.add_argument('--data-file', default=None, help='Data file with executed trajectory (for plot mode).')
    parser.add_argument('--path-file', default=None, help='Desired path file (for plot mode).')
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    path = generate_test_path()

    if args.mode == 'tune':
        # Tune each controller independently
        print('Tuning controllers against a common test path...')

        # Pure pursuit param grid (alpha, beta)
        pp_results = evaluate_controller(
            'pure_pursuit',
            path,
            pure_pursuit_control_factory,
            param_grid=[((0.05, 2.0), (0.05, 2.0))],
        )

        # Stanley param grid (Kd, Ka)
        st_results = evaluate_controller(
            'stanley',
            path,
            stanley_control_factory,
            param_grid=[((0.1, 5.0), (0.1, 5.0))],
        )

        # Save top results
        save_csv(
            os.path.join(args.output_dir, 'pure_pursuit_tuning.csv'),
            ['alpha', 'beta', 'mean_error', 'final_error', 'steps'],
            [[r['p1'], r['p2'], r['mean_error'], r['final_error'], r['steps']] for r in pp_results[:20]],
        )
        save_csv(
            os.path.join(args.output_dir, 'stanley_tuning.csv'),
            ['Kd', 'Ka', 'mean_error', 'final_error', 'steps'],
            [[r['p1'], r['p2'], r['mean_error'], r['final_error'], r['steps']] for r in st_results[:20]],
        )

        print('Top 5 Pure Pursuit results:')
        for r in pp_results[:5]:
            print(r)
        print('\nTop 5 Stanley results:')
        for r in st_results[:5]:
            print(r)

        # Plot best trajectories
        best_pp = pp_results[0]
        best_st = st_results[0]

        traj_pp, _ = simulate_differential_drive(
            path,
            pure_pursuit_control_factory(path, best_pp['p1'], best_pp['p2'], 0.8, 1.0),
        )
        traj_st, _ = simulate_differential_drive(
            path,
            stanley_control_factory(path, best_st['p1'], best_st['p2'], 0.8, 1.0),
        )

        plot_trajectory(path, traj_pp, os.path.join(args.output_dir, 'best_pure_pursuit.png'))
        plot_trajectory(path, traj_st, os.path.join(args.output_dir, 'best_stanley.png'))

        print(f"Saved top result plots to {args.output_dir}")
        print('Done tuning.')

    else:
        # Plot from provided files
        if args.data_file is None or args.path_file is None:
            raise SystemExit('Both --data-file and --path-file must be provided in plot mode.')

        # parse data file (assumes either 5 or 7 columns)
        data = np.loadtxt(args.data_file, delimiter=',')
        if data.ndim == 1:
            data = data.reshape(1, -1)

        if data.shape[1] == 5:
            # stanley: x, y, theta, v, w
            actual = Trajectory(x=data[:, 0], y=data[:, 1], theta=data[:, 2])
        else:
            # pure pursuit: x, y, theta, goal_x, goal_y, v, w
            actual = Trajectory(x=data[:, 0], y=data[:, 1], theta=data[:, 2])

        desired = np.loadtxt(args.path_file, delimiter=',')
        plot_trajectory(desired, actual, os.path.join(args.output_dir, 'tracked_vs_desired.png'))
        print(f'Plot saved to {os.path.join(args.output_dir, "tracked_vs_desired.png")}')


if __name__ == '__main__':
    main()
