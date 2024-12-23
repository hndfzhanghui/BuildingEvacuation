# visualization.py

import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap

def plot_smoke_layer(ax, smoke_zone, title):
    """绘制单个烟雾区域"""
    # 创建多边形
    poly = Polygon(
        smoke_zone.boundary_points,
        facecolor='white',
        edgecolor='black',
        alpha=smoke_zone.smoke_height / 3.0,  # 3.0是房间高度
        linewidth=1
    )
    ax.add_patch(poly)

def plot_building(building, show_grid=False):
    """绘制建筑物布局，包括烟雾分布"""
    fig, ax = plt.subplots(1, 5, figsize=(25, 5))
    
    # 绘制一楼和二楼的平面图
    plot_floor(ax[0], building.floors[1], "1F Layout")
    plot_floor(ax[1], building.floors[2], "2F Layout")
    
    # 绘制楼梯
    plot_staircase(ax[2], building.staircase)
    
    # 绘制一楼和二楼的烟雾分布
    plot_smoke_distribution(ax[3], building, 1, "1F Smoke Distribution")
    plot_smoke_distribution(ax[4], building, 2, "2F Smoke Distribution")
    
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

def plot_smoke_distribution(ax, building, floor_num, title):
    """绘制某一层的烟雾分布"""
    # 设置坐标轴范围
    ax.set_xlim(-5, 55)
    ax.set_ylim(-5, 45)
    ax.set_aspect('equal')
    ax.set_title(title)
    
    # 获取该层所有的烟雾区域
    for room_id, zone in building.fire_model.smoke_zones.items():
        if room_id.startswith(f"room_{floor_num}"):
            # 计算颜色（基于烟层厚度）
            smoke_ratio = zone.smoke_height / 3.0  # 3.0是房间高度
            color = str(1 - smoke_ratio)  # 从白色(1)到黑色(0)
            
            # 创建多边形
            poly = Polygon(
                zone.boundary_points,
                facecolor=color,
                edgecolor='black',
                alpha=0.7,
                linewidth=1
            )
            ax.add_patch(poly)
            
            # 如果房间着火，添加火源标记
            if len(zone.fire_sources) > 0:
                center = np.mean(zone.boundary_points, axis=0)
                ax.plot(center[0], center[1], 'r*', markersize=15, label='Fire Source')
            
            # 添加烟层厚度文本
            center = np.mean(zone.boundary_points, axis=0)
            ax.text(center[0], center[1], f'{smoke_ratio:.2f}\n{room_id}', 
                   ha='center', va='center', color='red' if smoke_ratio > 0.5 else 'blue')
    
    # 绘制区域间的连接关系
    connections_drawn = set()  # 用于跟踪已绘制的连接
    for conn in building.fire_model.zone_connections:
        zone1_id = conn.zone1.room_id
        zone2_id = conn.zone2.room_id
        
        # 检查是否是当前楼层的连接
        if (zone1_id.startswith(f"room_{floor_num}") or 
            zone2_id.startswith(f"room_{floor_num}")):
            
            # 避免重复绘制
            conn_key = tuple(sorted([zone1_id, zone2_id]))
            if conn_key in connections_drawn:
                continue
            connections_drawn.add(conn_key)
            
            # 获取连接位置
            pos = conn.geometry['position']
            
            # 绘制连接标记
            if conn.connection_type == 'door':
                # 绘制门的连接
                ax.plot(pos[0], pos[1], 'go', markersize=8)
                ax.text(pos[0], pos[1]+1, f'Door\n{zone1_id}<->{zone2_id}', 
                       ha='center', va='bottom', fontsize=8)
            elif conn.connection_type == 'stair':
                # 绘制楼梯的连接
                ax.plot(pos[0], pos[1], 'b^', markersize=8)
                ax.text(pos[0], pos[1]+1, f'Stair\n{zone1_id}<->{zone2_id}', 
                       ha='center', va='bottom', fontsize=8)

def plot_simulation(building, simulation):
    """动态模拟显示"""
    fig, ax = plt.subplots(1, 5, figsize=(25, 5))
    
    def update(frame):
        # 使用相同的时间步长
        current_time = simulation.dt * frame
        
        # 同步火灾模型时间
        building.fire_model._current_time = current_time
        building.fire_model.update(simulation.dt)
        
        # 更新疏散状态
        if not simulation.is_evacuation_complete():
            simulation.update()
        
        # 3. 清除所有子图
        for a in ax:
            a.clear()
        
        # 4. 绘制更新后的状态
        plot_floor(ax[0], building.floors[1], "1F Layout", 
                  grid=simulation.grids[1], show_grid=False)
        plot_floor(ax[1], building.floors[2], "2F Layout", 
                  grid=simulation.grids[2], show_grid=False)
        plot_staircase(ax[2], building.staircase)
        plot_smoke_distribution(ax[3], building, 1, "1F Smoke Distribution")
        plot_smoke_distribution(ax[4], building, 2, "2F Smoke Distribution")
        
        # 5. 绘制agent
        for agent in simulation.agents:
            if not agent.in_stairs:
                floor_idx = agent.floor - 1
                if agent.path:
                    path_points = [agent.position]
                    if agent.target is not None:
                        path_points.append(agent.target)
                    path_points.extend(agent.path)
                    path_points = np.array(path_points)
                    ax[floor_idx].plot(path_points[:, 0], path_points[:, 1], 
                                     '--', color='lightgray', alpha=0.5, linewidth=1)
                
                color = 'yellow' if agent.target_type == 'stairs' else 'blue'
                ax[floor_idx].plot(agent.position[0], agent.position[1], 
                                 color=color, marker='o', markersize=5)
            else:
                progress_ratio = 1.0 - (agent.stairs_progress / 3.0)
                pos = agent.stair_start_pos * (1 - progress_ratio) + agent.stair_end_pos * progress_ratio
                ax[2].plot(pos[0], pos[1], color='red', marker='o', markersize=5)
        
        # 6. 添加统计信息
        stats = simulation.get_statistics()
        info_text = f'Time: {stats["current_time"]:.1f}s\n'
        info_text += f'Evacuated: {stats["evacuated_count"]}\n'
        info_text += f'Remaining: {stats["remaining_count"]}\n'
        info_text += f'Fire Time: {building.fire_model._current_time:.1f}s'
        ax[0].text(0.02, 0.98, info_text, transform=ax[0].transAxes, 
                  verticalalignment='top', fontsize=8)
        
        # 7. 设置所有子图的范围
        for a in ax:
            a.set_xlim(-5, 55)
            a.set_ylim(-5, 45)
            a.set_aspect('equal')
    
    # 创建动画，减小interval以提高更新频率
    anim = FuncAnimation(fig, update, frames=None, interval=100, blit=False)
    plt.tight_layout()
    plt.show()

def plot_floor(ax, floor, title, grid=None, show_grid=False):
    """绘制单层平面图"""
    ax.set_xlim(-5, 55)
    ax.set_ylim(-5, 45)
    ax.set_aspect('equal')
    ax.set_title(title)
    
    # 绘制房间
    for room in floor.rooms:
        ax.plot([x for x, y in room], [y for x, y in room], 'k-')
    
    # 绘制门
    for door in floor.doors:
        ax.plot([x for x, y in door], [y for x, y in door], 'g-', linewidth=2)
    
    # 绘制建筑物出口
    if floor.building_exit:
        ax.plot([x for x, y in floor.building_exit], 
                [y for x, y in floor.building_exit], 'r-', linewidth=3)
    
    # 绘制障碍物
    for obs in floor.obstacles:
        if obs["type"] == "circle":
            x, y, r = obs["params"]
            circle = Circle((x, y), r, fill=False)
            ax.add_patch(circle)
        elif obs["type"] == "line":
            start, end = obs["params"]
            ax.plot([start[0], end[0]], [start[1], end[1]], 'k-')
    
    # 如果提供了网格且需要显示
    if grid is not None and show_grid:
        for r in range(grid.rows):
            for c in range(grid.cols):
                if grid.grid[r, c]:
                    pos = grid.grid_to_world(r, c)
                    ax.plot(pos[0], pos[1], 'r.')

def plot_staircase(ax, staircase):
    """绘制楼梯区域"""
    ax.set_xlim(-5, 55)
    ax.set_ylim(-5, 45)
    ax.set_aspect('equal')
    ax.set_title("Staircase")
    
    # 绘制楼梯区域
    ax.plot([x for x, y in staircase["area"]], 
            [y for x, y in staircase["area"]], 'k-')
    
    # 绘制各层入口
    for entry in staircase["entries"]:
        floor = entry["floor"]
        position = entry["position"]
        ax.plot([x for x, y in position], [y for x, y in position], 
                'g-', label=f'Floor {floor} Entry')
    
    ax.legend()