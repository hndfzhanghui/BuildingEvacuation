# evacuation.py

import numpy as np
from pathfinding import Grid, a_star

# 设置检测距离
DETECT_DISTANCE = 2.0

class Agent:
    def __init__(self, x, y, floor):
        self.position = np.array([x, y])  # 当前位置 (x, y)
        self.velocity = np.zeros(2)       # 当前速度
        self.desired_speed = 2          # 理想速度 (m/s)
        self.floor = floor                # 当前所在楼层
        self.path = []                    # 计算好的路径 (由A*算法生成)
        self.target = None                # 当前目标点 (路径中的下一个点)
        self.radius = 0.5                 # Agent的半径 (用于避碰)
        self.evacuated = False            # 是否已经逃生
        self.evacuation_time = None       # 逃生所需时间
        self.target_type = None           # 目标类型：'stairs'（楼梯）或 'exit'（出口）
        self.in_stairs = False            # 是否正在通过楼梯
        self.stairs_progress = 0.0        # 楼梯通行进度 (秒)
        self.stair_start_pos = None       # 楼梯的起始位置
        self.stair_end_pos = None         # 楼梯的结束位置
        self.current_stairs = None        # 当前使用的楼梯对象
        self.move_direction = None        # 移动方向：'up' 或 'down'
        self.personal_space = 1.0         # 添加个人空间参数
        self.max_repulsion = 5.0          # 最大排斥力

class EvacuationSimulation:
    def __init__(self, building):
        self.building = building           # 建筑物对象，包含楼层信息
        self.agents = []                   # 所有疏散人员
        self.time = 0                      # 当前时间 (秒)
        self.dt = 0.1                      # 每个时间步的长度 (秒)
        self.grids = {}                    # 每层楼的网格 (用于A*寻路)
        self.evacuated_count = 0           # 已逃生人数
        self.evacuation_times = []         # 记录每个逃生人员的逃生时间
        self.stairs_capacity = 10          # 楼梯同时容纳的人数 (未实际使用)
        self.stairs_queue = {}             # 每层楼的楼梯队列 (未实际使用)
        self._initialize_grids()           # 初始化网格和楼梯队列
    
    def _initialize_grids(self):
        """初始化每层楼的网格"""
        for floor_num, floor in self.building.floors.items():
            grid = Grid(floor.width, floor.length)
            
            # 将房间的多边形边界作为墙壁处理
            for room in floor.rooms:
                for i in range(len(room)-1):
                    grid.add_wall(room[i], room[i+1])
            
            # 添加门
            for door in floor.doors:
                grid.add_door(door[0], door[1])
            
            # 添加障碍物
            for obs in floor.obstacles:
                if obs["type"] == "circle":
                    x, y, r = obs["params"]
                    grid.add_circle_obstacle((x, y), r)
                elif obs["type"] == "line":
                    start, end = obs["params"]
                    grid.add_wall(start, end)
            
            self.grids[floor_num] = grid
    
    def initialize_agents(self, floor_populations):
        """初始化各楼层的人员"""
        for floor_num, population in floor_populations.items():
            floor = self.building.floors[floor_num]
            for _ in range(population):
                room_idx = np.random.choice(len(floor.rooms))
                x, y = self._random_position_in_room(floor.rooms[room_idx])
                self.agents.append(Agent(x, y, floor_num))
    
    def _random_position_in_room(self, room):
        points = np.array(room)
        min_x, min_y = np.min(points, axis=0)
        max_x, max_y = np.max(points, axis=0)
        return (
            np.random.uniform(min_x + 0.5, max_x - 0.5),
            np.random.uniform(min_y + 0.5, max_y - 0.5)
        )
    
    def find_path(self, agent):
        floor = self.building.floors[agent.floor]
        grid = self.grids[agent.floor]
        
        # 如果不在一楼且还没有到达出口
        if agent.floor != 1 and agent.target_type != 'exit':
            # 确定移动方向
            direction = 'down' if agent.floor > 1 else 'up'
            agent.target_type = 'stairs'
            
            # 获取连接当前楼层的楼梯
            for stairs_key, stairs in self.building.stairs.items():
                if agent.floor in stairs_key:
                    next_floor = stairs.get_next_floor(agent.floor, direction)
                    if next_floor is not None:
                        stair_pos = stairs.get_entry_position(agent.floor)
                        if stair_pos is None:
                            continue
                        
                        path = a_star(tuple(agent.position), stair_pos, grid)
                        if path:
                            agent.path = path
                            agent.target = np.array(agent.path.pop(0))
                            agent.current_stairs = stairs
                            agent.move_direction = direction
                            return
            agent.target = None
        else:
            # 在一楼，寻找到主出口的路径
            agent.target_type = 'exit'
            if floor.main_exit is None:
                agent.target = None
                return
            
            path = a_star(tuple(agent.position), floor.main_exit, grid)
            if path:
                agent.path = path
                agent.target = np.array(agent.path.pop(0))
            else:
                agent.target = None
    
    def update(self):
        """更新一个时间步"""
        self.time += self.dt
        for agent in self.agents:
            # 移除条件判断，让所有没有目标的agent都尝试寻路
            if agent.target is None:
                self.find_path(agent)
            
            self._update_agent_position(agent)
        
        self.remove_escaped_agents()
    
    def _update_agent_position(self, agent):
        # 如果正在楼梯中
        if agent.in_stairs:
            agent.stairs_progress -= self.dt
            if agent.stairs_progress <= 0:
                if agent.current_stairs is None:
                    return
                
                # 完成楼梯移动
                agent.current_stairs.exit(agent)
                next_floor = agent.current_stairs.get_next_floor(agent.floor, agent.move_direction)
                if next_floor is None:
                    return
                
                agent.floor = next_floor
                agent.in_stairs = False
                agent.path = []
                agent.target = None
                agent.target_type = 'exit' if agent.floor == 1 else 'stairs'
                
                # 重置agent的位置到楼梯出口
                exit_pos = agent.current_stairs.get_exit_position(agent.floor)
                if exit_pos is not None:
                    agent.position = np.array(exit_pos)
                    self.find_path(agent)
                return
            
            return

        # 没有目标则不移动
        if agent.target is None:
            self.find_path(agent)
            return

        # 计算到目标点的距离
        distance = np.linalg.norm(agent.target - agent.position)
        
        # 简化到达判定
        if distance < 0.5:  # 降低到达判定距离
            if agent.target_type == 'stairs' and not agent.in_stairs:
                # 重新获取当前楼层的楼梯对象
                for stairs_key, stairs in self.building.stairs.items():
                    if agent.floor in stairs_key:
                        stair_pos = stairs.get_entry_position(agent.floor)
                        if stair_pos is not None:
                            dist_to_stairs = np.linalg.norm(agent.position - np.array(stair_pos))
                            if dist_to_stairs < DETECT_DISTANCE:  # 确认确实在楼梯入口
                                agent.current_stairs = stairs
                                if stairs.enter(agent):
                                    agent.in_stairs = True
                                    agent.stairs_progress = stairs.passing_time
                                    agent.stair_start_pos = agent.position.copy()
                                    
                                    next_floor = stairs.get_next_floor(agent.floor, agent.move_direction)
                                    if next_floor is not None:
                                        exit_pos = stairs.get_exit_position(next_floor)
                                        if exit_pos is not None:
                                            agent.stair_end_pos = np.array(exit_pos)
                                            return
            
                # 如果还没到达楼梯入口或无法进入楼梯，继续移动
                if agent.path:
                    agent.target = np.array(agent.path.pop(0))
                else:
                    # 重新寻路到楼梯
                    self.find_path(agent)
                return
            
            # 如果还有路径点，继续移动
            if agent.path:
                agent.target = np.array(agent.path.pop(0))
            else:
                agent.target = None
                self.find_path(agent)
            return

        # 计算移动方向和速度
        direction = agent.target - agent.position
        dist = np.linalg.norm(direction)
        if dist > 0:
            desired_velocity = (direction / dist) * agent.desired_speed
        else:
            desired_velocity = np.zeros(2)
        
        # 避碰
        actual_velocity = self._avoid_collisions(agent, desired_velocity)
        
        # 更新位置
        agent.velocity = actual_velocity
        agent.position += agent.velocity * self.dt

    def _avoid_collisions(self, agent, desired_velocity):
        # 当前代理的位置和楼层
        position = agent.position
        floor_agents = [other for other in self.agents if other.floor == agent.floor and other is not agent]
    
        if not floor_agents:
            return desired_velocity
    
        # 所有其他代理的位置矩阵
        other_positions = np.array([other.position for other in floor_agents])
    
        # 计算所有其他代理到当前代理的距离向量和距离
        diff = other_positions - position
        distances = np.linalg.norm(diff, axis=1)
    
        # 排斥力计算：距离小于一定范围时产生作用
        min_distances = agent.radius * 2
        mask = distances < min_distances  # 只考虑近距离的代理人
        if not np.any(mask):
            return desired_velocity
    
        repulsion_forces = np.zeros_like(diff)
        repulsion_forces[mask] = diff[mask] / (distances[mask][:, None] + 1e-6)
    
        # 总排斥力
        total_repulsion = np.sum(repulsion_forces, axis=0) * 0.5
        velocity = desired_velocity - total_repulsion
    
        # 限制速度
        speed = np.linalg.norm(velocity)
        if speed > agent.desired_speed:
            velocity = velocity / speed * agent.desired_speed
    
        return velocity

    def is_evacuation_complete(self):
        return len(self.agents) == 0

    def remove_escaped_agents(self):
        """简单地检查和移除已经逃生的agents"""
        escaped = []
        for agent in self.agents:
            if agent.floor == 1 and not agent.evacuated:
                main_exit = self.building.floors[1].main_exit
                if main_exit is not None:
                    dist = np.linalg.norm(agent.position - np.array(main_exit))
                    if dist < 2.0:  # 增大逃生判定距离
                        agent.evacuated = True
                        agent.evacuation_time = self.time
                        self.evacuation_times.append(self.time)
                        escaped.append(agent)
                        self.evacuated_count += 1
        
        for agent in escaped:
            self.agents.remove(agent)
        
        return len(escaped)

    def get_statistics(self):
        stats = {
            'current_time': self.time,
            'evacuated_count': self.evacuated_count,
            'remaining_count': len(self.agents),
            'average_evacuation_time': np.mean(self.evacuation_times) if self.evacuation_times else 0,
            'max_evacuation_time': np.max(self.evacuation_times) if self.evacuation_times else 0,
        }
        return stats