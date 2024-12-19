# pathfinding.py

import numpy as np
from queue import PriorityQueue

class Grid:
    def __init__(self, width: int, length: int, cell_size: float = 0.5):
        self.cell_size = cell_size
        self.cols = int(width / cell_size)
        self.rows = int(length / cell_size)
        self.grid = np.zeros((self.rows, self.cols), dtype=bool)  # False为可走，True为障碍
        self.doors = []
        
    def world_to_grid(self, x: float, y: float):
        return (int(y / self.cell_size), int(x / self.cell_size))
    
    def grid_to_world(self, row: int, col: int):
        return (col * self.cell_size + self.cell_size/2, 
                row * self.cell_size + self.cell_size/2)
    
    def add_wall(self, start, end):
        # 使用Bresenham算法画线并标记为障碍
        r0, c0 = self.world_to_grid(*start)
        r1, c1 = self.world_to_grid(*end)
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if (r0 < r1) else -1
        sc = 1 if (c0 < c1) else -1
        err = dr - dc
        r, c = r0, c0
        while True:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                self.grid[r, c] = True
            if r == r1 and c == c1:
                break
            e2 = 2*err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc
    
    def add_circle_obstacle(self, center, radius):
        center_row, center_col = self.world_to_grid(*center)
        radius_cells = int(radius / self.cell_size)
        
        rows, cols = np.ogrid[:self.rows, :self.cols]
        distances = np.sqrt((rows - center_row)**2 + (cols - center_col)**2)
        mask = distances <= radius_cells

        self.grid[mask] = True


        # for r in range(max(0, center_row - radius_cells), 
        #                min(self.rows, center_row + radius_cells + 1)):
        #     for c in range(max(0, center_col - radius_cells), 
        #                    min(self.cols, center_col + radius_cells + 1)):
        #         if (r - center_row)**2 + (c - center_col)**2 <= radius_cells**2:
        #             if 0 <= r < self.rows and 0 <= c < self.cols:
        #                 self.grid[r, c] = True
    
    def add_door(self, start, end):
        # 使用Bresenham算法标记门所在线段为可通行（False），同时存储门坐标
        r0, c0 = self.world_to_grid(*start)
        r1, c1 = self.world_to_grid(*end)
        dr = abs(r1 - r0)
        dc = abs(c1 - c0)
        sr = 1 if (r0 < r1) else -1
        sc = 1 if (c0 < c1) else -1
        err = dr - dc
        r, c = r0, c0
        door_cells = []
        while True:
            if 0 <= r < self.rows and 0 <= c < self.cols:
                # 门所在位置应为可通行
                self.grid[r, c] = False
                door_cells.append((r, c))
            if r == r1 and c == c1:
                break
            e2 = 2*err
            if e2 > -dc:
                err -= dc
                r += sr
            if e2 < dr:
                err += dr
                c += sc
        self.doors.append((door_cells[0], door_cells[-1]))
    
    def is_door(self, pos):
        # 可根据需要使用，但当前简化不强制走门才可跨障碍
        # 保留这个函数以防以后扩展
        for (dstart, dend) in self.doors:
            if (min(dstart[0], dend[0]) <= pos[0] <= max(dstart[0], dend[0]) and
                min(dstart[1], dend[1]) <= pos[1] <= max(dstart[1], dend[1])):
                return True
        return False

def heuristic(a, b):
    return abs(a[0]-b[0]) + abs(a[1]-b[1])

def get_neighbors(pos, grid: Grid):
    neighbors = []
    directions = [(0,1),(1,0),(0,-1),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
    for dr, dc in directions:
        nr, nc = pos[0]+dr, pos[1]+dc
        if 0 <= nr < grid.rows and 0 <= nc < grid.cols:
            # 如果下一个格子是障碍就跳过
            if grid.grid[nr, nc]:
                continue
            neighbors.append((nr, nc))
    return neighbors

def a_star(start, goal, grid: Grid):
    start_grid = grid.world_to_grid(*start)
    goal_grid = grid.world_to_grid(*goal)
    
    frontier = PriorityQueue()
    frontier.put((0, start_grid))
    came_from = {start_grid: None}
    cost_so_far = {start_grid: 0}
    
    while not frontier.empty():
        current = frontier.get()[1]
        
        if current == goal_grid:
            break
        
        for next_pos in get_neighbors(current, grid):
            new_cost = cost_so_far[current] + 1
            if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
                cost_so_far[next_pos] = new_cost
                priority = new_cost + heuristic(goal_grid, next_pos)
                frontier.put((priority, next_pos))
                came_from[next_pos] = current
    
    if goal_grid not in came_from:
        # 无路径
        return []
    
    path = []
    cur = goal_grid
    while cur is not None:
        path.append(grid.grid_to_world(*cur))
        cur = came_from[cur]
    return list(reversed(path))

# def a_star(start, goal, grid: Grid):
#     start_grid = grid.world_to_grid(*start)
#     goal_grid = grid.world_to_grid(*goal)
#
#     frontier = PriorityQueue()
#     frontier.put((0, start_grid))
#     came_from = {start_grid: None}
#     cost_so_far = {start_grid: 0}
#
#     while not frontier.empty():
#         _, current = frontier.get()
#
#         if current == goal_grid:
#             break
#
#         neighbors = get_neighbors(current, grid)
#         for next_pos in neighbors:
#             new_cost = cost_so_far[current] + 1
#             if next_pos not in cost_so_far or new_cost < cost_so_far[next_pos]:
#                 cost_so_far[next_pos] = new_cost
#                 priority = new_cost + heuristic(goal_grid, next_pos)
#                 frontier.put((priority, next_pos))
#                 came_from[next_pos] = current
#
#     if goal_grid not in came_from:
#         return []
#
#     path = []
#     cur = goal_grid
#     while cur is not None:
#         path.append(grid.grid_to_world(*cur))
#         cur = came_from[cur]
#     return list(reversed(path))