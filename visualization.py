# visualization.py

import matplotlib.pyplot as plt
from matplotlib.patches import Circle
import numpy as np
from matplotlib.animation import FuncAnimation

def plot_building(building, show_grid=False):
    fig, ax = plt.subplots(1, 3, figsize=(30, 10))
    
    # 绘制一楼和二楼
    plot_floor(ax[0], building.floors[1], "1F Layout")
    plot_floor(ax[1], building.floors[2], "2F Layout")
    
    # 绘制楼梯
    plot_staircase(ax[2], building.staircase)
    
    # 在一楼和二楼图中标记楼梯位置
    for floor_num in [1, 2]:
        floor_idx = floor_num - 1
        for stairs in building.stairs.values():
            if floor_num in stairs.entries:
                x, y = stairs.get_entry_position(floor_num)
                ax[floor_idx].plot(x, y, 's', color='red', markersize=10, 
                                 label='Stair Entry/Exit' if 'Stair Entry/Exit' not in ax[floor_idx].get_legend_handles_labels()[1] else None)
    
    plt.tight_layout()
    plt.show()

def plot_floor(ax, floor, title, grid=None, show_grid=False):
    # 绘制房间边界
    for room in floor.rooms:
        x, y = zip(*room)
        ax.plot(x, y, 'b-', label='Wall' if 'Wall' not in ax.get_legend_handles_labels()[1] else None)
    
    # 绘制门
    for door in floor.doors:
        x, y = zip(*door)
        ax.plot(x, y, 'g-', linewidth=3, label='Door' if 'Door' not in ax.get_legend_handles_labels()[1] else None)
    
    # 绘制障碍物
    for obs in floor.obstacles:
        if obs["type"] == "circle":
            x, y, r = obs["params"]
            ax.add_patch(Circle((x, y), r, color='red', alpha=0.5,
                              label='Obstacle' if 'Obstacle' not in ax.get_legend_handles_labels()[1] else None))
        elif obs["type"] == "line":
            x, y = zip(*obs["params"])
            ax.plot(x, y, 'orange', linewidth=2, label='Obstacle Line' if 'Obstacle Line' not in ax.get_legend_handles_labels()[1] else None)
    
    # 绘制主出口（仅一楼）
    if floor.main_exit is not None:
        x, y = floor.main_exit
        ax.plot(x, y, 's', color='purple', markersize=10, label='Main Exit')
    
    # 绘制建筑物出口（仅一楼）
    if floor.building_exit:
        x, y = zip(*floor.building_exit)
        ax.plot(x, y, 'purple', linewidth=3, label='Building Exit')
    
    # 如果需要显示网格
    if show_grid and grid is not None:
        plot_grid(ax, grid)
    
    ax.set_title(title)
    ax.set_xlim(0, floor.width)
    ax.set_ylim(0, floor.length)
    ax.set_aspect('equal')
    ax.legend()

def plot_staircase(ax, staircase):
    x, y = zip(*staircase["area"])
    ax.plot(x, y, 'gray', linewidth=2, label='Staircase Area')
    
    for entry in staircase["entries"]:
        ex, ey = zip(*entry["position"])
        ax.plot(ex, ey, 'purple', linewidth=3, 
                label=f'Stair Entry ({entry["floor"]}F)' if f'Stair Entry ({entry["floor"]}F)' not in ax.get_legend_handles_labels()[1] else None)
    
    ax.set_title("Staircase Layout")
    ax.set_xlim(20, 40)
    ax.set_ylim(30, 45)
    ax.set_aspect('equal')
    ax.legend()

def plot_simulation(building, simulation):
    fig, ax = plt.subplots(1, 3, figsize=(30, 10))
    
    def update(frame):
        ax[0].clear()
        ax[1].clear()
        ax[2].clear()
        
        # 绘制一楼和二楼（添加网格显示）
        plot_floor(ax[0], building.floors[1], "1F Layout", 
                  grid=simulation.grids[1], show_grid=False)
        plot_floor(ax[1], building.floors[2], "2F Layout", 
                  grid=simulation.grids[2], show_grid=False)
        
        # 绘制楼梯区域
        plot_staircase(ax[2], building.staircase)
        
        # 先绘制所有agent的路径
        for agent in simulation.agents:
            if not agent.in_stairs:
                floor_idx = agent.floor - 1  # 确保在正确的楼层显示
                if agent.path:
                    path_points = [agent.position]
                    if agent.target is not None:
                        path_points.append(agent.target)
                    path_points.extend(agent.path)
                    path_points = np.array(path_points)
                    ax[floor_idx].plot(path_points[:, 0], path_points[:, 1], 
                                     '--', color='lightgray', alpha=0.5, linewidth=1)
        
        # 分别绘制在楼层中和在楼梯中的agent
        for agent in simulation.agents:
            if agent.in_stairs:
                # 在楼梯中的agent
                progress_ratio = 1.0 - (agent.stairs_progress / 3.0)
                pos = agent.stair_start_pos * (1 - progress_ratio) + agent.stair_end_pos * progress_ratio
                ax[2].plot(pos[0], pos[1], color='red', marker='o', markersize=5)
            else:
                # 在楼层中的agent
                floor_idx = agent.floor - 1
                color = 'yellow' if agent.target_type == 'stairs' else 'blue'
                ax[floor_idx].plot(agent.position[0], agent.position[1], 
                                 color=color, marker='o', markersize=5)
        
        # 更新模拟和统计信息
        if not simulation.is_evacuation_complete():
            simulation.update()
        
        stats = simulation.get_statistics()
        ax[0].set_title(f"Time: {stats['current_time']:.1f}s | "
                       f"Evacuated: {stats['evacuated_count']} | "
                       f"Remaining: {stats['remaining_count']}")
        ax[1].set_title(f"Avg Evacuation Time: {stats['average_evacuation_time']:.1f}s | "
                       f"Max Time: {stats['max_evacuation_time']:.1f}s")
        ax[2].set_title("Staircase Status")
        
        # 设置各子图的显示范围
        ax[0].set_xlim(0, building.floors[1].width)
        ax[0].set_ylim(0, building.floors[1].length)
        ax[1].set_xlim(0, building.floors[2].width)
        ax[1].set_ylim(0, building.floors[2].length)
        ax[2].set_xlim(20, 40)
        ax[2].set_ylim(30, 45)
        
        # 设置纵横比
        ax[0].set_aspect('equal')
        ax[1].set_aspect('equal')
        ax[2].set_aspect('equal')
        
        return ax
    
    anim = FuncAnimation(fig, update, frames=None, interval=50, blit=False)
    plt.tight_layout()
    plt.show()

def plot_grid(ax, grid, alpha=0.2):
    """绘制网格"""
    # 绘制网格线
    for i in range(grid.rows + 1):
        y = i * grid.cell_size
        ax.plot([0, grid.cols * grid.cell_size], [y, y], 
                'gray', alpha=alpha, linewidth=0.5)
    
    for j in range(grid.cols + 1):
        x = j * grid.cell_size
        ax.plot([x, x], [0, grid.rows * grid.cell_size], 
                'gray', alpha=alpha, linewidth=0.5)
    
    # 绘制障碍物网格
    obstacle_mask = grid.grid
    for i in range(grid.rows):
        for j in range(grid.cols):
            if obstacle_mask[i, j]:
                x = j * grid.cell_size
                y = i * grid.cell_size
                ax.add_patch(plt.Rectangle(
                    (x, y), 
                    grid.cell_size, 
                    grid.cell_size, 
                    facecolor='red', 
                    alpha=0.3
                ))