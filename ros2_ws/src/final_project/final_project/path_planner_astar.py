#!/usr/bin/env python3
"""
A* Path Planner for mobile robot navigation
Implements A* algorithm with occupancy grid
"""

import heapq
import math
from typing import List, Tuple, Optional
import numpy as np

class Node:
    """Node in A* search tree"""
    def __init__(self, x: int, y: int, g: float = 0, h: float = 0):
        self.x = x
        self.y = y
        self.g = g  # Cost from start
        self.h = h  # Heuristic cost to goal
        self.parent = None
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return (self.g + self.h) < (other.g + other.h)
    
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    
    def __hash__(self):
        return hash((self.x, self.y))

class PathPlannerAStar:
    """A* pathfinding algorithm"""
    
    def __init__(self, grid_width: int, grid_height: int, resolution: float = 0.1):
        """
        Initialize A* planner
        
        Args:
            grid_width: Width of occupancy grid (cells)
            grid_height: Height of occupancy grid (cells)
            resolution: Cell size in meters (0.1m = 10cm)
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.resolution = resolution
        self.occupancy_grid = np.zeros((grid_height, grid_width), dtype=np.uint8)
    
    def set_obstacle(self, x: int, y: int):
        """Mark cell as obstacle"""
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.occupancy_grid[y, x] = 1
    
    def set_obstacles_from_map(self, obstacles: List[Tuple[float, float]], 
                                inflation_radius: float = 0.3):
        """
        Set obstacles from world coordinates
        
        Args:
            obstacles: List of (x, y) obstacle positions in meters
            inflation_radius: Inflate obstacles by this radius (meters)
        """
        inflation_cells = int(inflation_radius / self.resolution)
        
        for obs_x, obs_y in obstacles:
            # Convert to grid coordinates
            grid_x = int(obs_x / self.resolution)
            grid_y = int(obs_y / self.resolution)
            
            # Inflate obstacle
            for dx in range(-inflation_cells, inflation_cells + 1):
                for dy in range(-inflation_cells, inflation_cells + 1):
                    x = grid_x + dx
                    y = grid_y + dy
                    if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
                        self.occupancy_grid[y, x] = 1
    
    def heuristic(self, x1: int, y1: int, x2: int, y2: int) -> float:
        """Euclidean distance heuristic"""
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
    
    def get_neighbors(self, x: int, y: int) -> List[Tuple[int, int, float]]:
        """Get valid neighboring cells (8-connected with diagonal cost)"""
        neighbors = []
        
        # 8-connected neighbors: 4 cardinal + 4 diagonals
        moves = [
            (0, 1, 1.0),      # Up
            (1, 0, 1.0),      # Right
            (0, -1, 1.0),     # Down
            (-1, 0, 1.0),     # Left
            (1, 1, math.sqrt(2)),    # Diagonal
            (-1, 1, math.sqrt(2)),   # Diagonal
            (-1, -1, math.sqrt(2)),  # Diagonal
            (1, -1, math.sqrt(2)),   # Diagonal
        ]
        
        for dx, dy, cost in moves:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.grid_width and 0 <= ny < self.grid_height:
                if self.occupancy_grid[ny, nx] == 0:  # Not an obstacle
                    neighbors.append((nx, ny, cost))
        
        return neighbors
    
    def plan_path(self, start_x: float, start_y: float, 
                  goal_x: float, goal_y: float) -> Optional[List[Tuple[float, float]]]:
        """
        Plan path from start to goal using A*
        
        Args:
            start_x, start_y: Start position in meters
            goal_x, goal_y: Goal position in meters
        
        Returns:
            List of (x, y) positions in meters, or None if no path found
        """
        # Convert to grid coordinates
        start_grid_x = int(start_x / self.resolution)
        start_grid_y = int(start_y / self.resolution)
        goal_grid_x = int(goal_x / self.resolution)
        goal_grid_y = int(goal_y / self.resolution)
        
        # Clamp to grid
        start_grid_x = max(0, min(self.grid_width - 1, start_grid_x))
        start_grid_y = max(0, min(self.grid_height - 1, start_grid_y))
        goal_grid_x = max(0, min(self.grid_width - 1, goal_grid_x))
        goal_grid_y = max(0, min(self.grid_height - 1, goal_grid_y))
        
        # Check if start/goal are obstacles
        if (self.occupancy_grid[start_grid_y, start_grid_x] == 1 or
            self.occupancy_grid[goal_grid_y, goal_grid_x] == 1):
            return None
        
        # A* algorithm
        open_set = []
        closed_set = set()
        
        start_node = Node(start_grid_x, start_grid_y, 0, 
                         self.heuristic(start_grid_x, start_grid_y, 
                                       goal_grid_x, goal_grid_y))
        heapq.heappush(open_set, start_node)
        
        node_dict = {(start_grid_x, start_grid_y): start_node}
        
        while open_set:
            current = heapq.heappop(open_set)
            
            if (current.x, current.y) in closed_set:
                continue
            
            closed_set.add((current.x, current.y))
            
            # Goal reached
            if current.x == goal_grid_x and current.y == goal_grid_y:
                path = []
                node = current
                while node:
                    # Convert to world coordinates (center of cell)
                    world_x = (node.x + 0.5) * self.resolution
                    world_y = (node.y + 0.5) * self.resolution
                    path.append((world_x, world_y))
                    node = node.parent
                path.reverse()
                return path
            
            # Check neighbors
            for nx, ny, cost in self.get_neighbors(current.x, current.y):
                if (nx, ny) in closed_set:
                    continue
                
                g = current.g + cost
                h = self.heuristic(nx, ny, goal_grid_x, goal_grid_y)
                
                if (nx, ny) in node_dict:
                    neighbor = node_dict[(nx, ny)]
                    if g < neighbor.g:
                        neighbor.g = g
                        neighbor.parent = current
                else:
                    neighbor = Node(nx, ny, g, h)
                    neighbor.parent = current
                    node_dict[(nx, ny)] = neighbor
                    heapq.heappush(open_set, neighbor)
        
        # No path found
        return None
    
    def smooth_path(self, path: List[Tuple[float, float]], 
                   max_iterations: int = 100) -> List[Tuple[float, float]]:
        """
        Smooth path using line-of-sight optimization
        
        Args:
            path: Raw path from A*
            max_iterations: Maximum smoothing iterations
        
        Returns:
            Smoothed path with fewer waypoints
        """
        if len(path) <= 2:
            return path
        
        smoothed_path = [path[0]]
        current_idx = 0
        
        while current_idx < len(path) - 1:
            # Try to find the furthest point we can see
            furthest_idx = current_idx + 1
            for i in range(len(path) - 1, current_idx, -1):
                if self._line_of_sight(path[current_idx], path[i]):
                    furthest_idx = i
                    break
            
            if furthest_idx == current_idx + 1:
                smoothed_path.append(path[current_idx + 1])
                current_idx += 1
            else:
                smoothed_path.append(path[furthest_idx])
                current_idx = furthest_idx
        
        return smoothed_path
    
    def _line_of_sight(self, p1: Tuple[float, float], 
                      p2: Tuple[float, float], 
                      check_distance: float = 0.1) -> bool:
        """Check if line of sight exists between two points"""
        x1, y1 = p1
        x2, y2 = p2
        dx = x2 - x1
        dy = y2 - y1
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance < 1e-6:
            return True
        
        steps = int(distance / check_distance) + 1
        for i in range(steps + 1):
            t = i / max(steps, 1)
            x = x1 + t * dx
            y = y1 + t * dy
            grid_x = int(x / self.resolution)
            grid_y = int(y / self.resolution)
            
            if (grid_x < 0 or grid_x >= self.grid_width or
                grid_y < 0 or grid_y >= self.grid_height or
                self.occupancy_grid[grid_y, grid_x] == 1):
                return False
        
        return True
    
    def visualize_grid(self, path: Optional[List[Tuple[float, float]]] = None) -> str:
        """Generate ASCII visualization of grid and path"""
        grid_visual = [['.' for _ in range(self.grid_width)] for _ in range(self.grid_height)]
        
        # Mark obstacles
        for y in range(self.grid_height):
            for x in range(self.grid_width):
                if self.occupancy_grid[y, x] == 1:
                    grid_visual[y][x] = '#'
        
        # Mark path
        if path:
            for x, y in path:
                grid_x = int(x / self.resolution)
                grid_y = int(y / self.resolution)
                if 0 <= grid_x < self.grid_width and 0 <= grid_y < self.grid_height:
                    grid_visual[grid_y][grid_x] = '*'
        
        return '\n'.join(''.join(row) for row in grid_visual)
