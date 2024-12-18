import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
from building import Building

def generate_smoke_grid(rooms, grid_size, smoke_factor=0.5):
    """
    根据实际房间几何形状生成烟雾分布
    """
    smoke_grid = np.zeros((grid_size, grid_size, grid_size))
    
    for room_name, room in rooms.items():
        # 根据上层质量生成烟雾浓度
        concentration = smoke_factor * (room["m_upper"] / (room["m_upper"] + room["m_lower"] + 1e-6))
        concentration = np.clip(concentration, 0, 1)
        
        # 根据房间的实际位置分配烟雾
        vertices = room["geometry"]
        x_min = min(v[0] for v in vertices)
        x_max = max(v[0] for v in vertices)
        y_min = min(v[1] for v in vertices)
        y_max = max(v[1] for v in vertices)
        
        # 将实际坐标映射到网格坐标
        x_start = int(x_min * grid_size / 50)
        x_end = int(x_max * grid_size / 50)
        y_start = int(y_min * grid_size / 40)
        y_end = int(y_max * grid_size / 40)
        
        if "1F" in room_name:
            z_range = slice(0, grid_size//2)
        elif "2F" in room_name:
            z_range = slice(grid_size//2, grid_size)
        else:  # Stairs
            z_range = slice(0, grid_size)
            
        smoke_grid[x_start:x_end, y_start:y_end, z_range] += concentration
    
    return np.clip(smoke_grid, 0, 1)

def visualize_smoke(smoke_grid, rooms, t, fig=None, axes=None):
    """
    使用 Matplotlib 的体积渲染显示三维烟雾分布。
    - smoke_grid: 三维烟雾浓度网格
    - rooms: 房间数据
    - t: 当前时间步
    - fig: 图形对象
    - axes: 子图对象列表
    """
    if fig is None or axes is None:
        fig = plt.figure(figsize=(15, 8))
        axes = [
            fig.add_subplot(231, projection='3d'),  # 烟雾分布
            fig.add_subplot(232),                   # 温度变化
            fig.add_subplot(233),                   # 分界面高度
            fig.add_subplot(234),                   # 上层质量
            fig.add_subplot(235),                   # 下层质量
            fig.add_subplot(236)                    # 其他参数
        ]
        plt.ion()  # 开启交互模式
    
    # 清除之前的图形
    for ax in axes:
        ax.clear()
    
    # 1. 烟雾分布图
    x, y, z = np.indices(smoke_grid.shape)
    colors = np.empty(smoke_grid.shape + (4,), dtype=float)
    colors[..., 0] = smoke_grid  # 红色分量
    colors[..., 1] = smoke_grid * 0.5  # 绿色分量
    colors[..., 2] = smoke_grid * 0.5  # 蓝色分量
    colors[..., 3] = smoke_grid * 0.8  # 透明度
    
    axes[0].voxels(smoke_grid, facecolors=colors, edgecolor=None)
    axes[0].set_title(f"Smoke Distribution (t={t}s)")
    
    # 2. 温度变化图
    for room_name, room in rooms.items():
        axes[1].plot([room["T_upper"]], [t], 'ro', label=f"{room_name}_upper")
        axes[1].plot([room["T_lower"]], [t], 'bo', label=f"{room_name}_lower")
    axes[1].set_title("Temperature")
    axes[1].set_xlabel("Temperature (K)")
    axes[1].set_ylabel("Time (s)")
    
    # 3. 分界面高度图
    for room_name, room in rooms.items():
        axes[2].plot([room["h_interface"]], [t], 'go', label=room_name)
    axes[2].set_title("Interface Height")
    axes[2].set_xlabel("Height (m)")
    axes[2].set_ylabel("Time (s)")
    
    # 4. 上层质量图
    for room_name, room in rooms.items():
        axes[3].plot([room["m_upper"]], [t], 'mo', label=room_name)
    axes[3].set_title("Upper Layer Mass")
    axes[3].set_xlabel("Mass (kg)")
    axes[3].set_ylabel("Time (s)")
    
    # 5. 下层质量图
    for room_name, room in rooms.items():
        axes[4].plot([room["m_lower"]], [t], 'ko', label=room_name)
    axes[4].set_title("Lower Layer Mass")
    axes[4].set_xlabel("Mass (kg)")
    axes[4].set_ylabel("Time (s)")
    
    # 添加图例（仅在开始时添加一次）
    if t == 0:
        for ax in axes[1:]:
            ax.legend()
    
    plt.tight_layout()
    plt.draw()
    plt.pause(0.01)  # 短暂暂停以更新显示
    
    return fig, axes

def initialize_scene():
    """
    根据building.py中的建筑物信息初始化场景
    """
    # 创建建筑物实例
    building = Building()
    building.initialize_building()
    
    # 根据building中的房间信息初始化rooms
    rooms = {}
    
    # 一楼房间
    for i, room in enumerate(building.floors[1].rooms):
        room_name = f"1F_Room{i+1}"
        area = calculate_room_area(room)  # 计算房间面积
        rooms[room_name] = {
            "name": room_name,
            "T_upper": 300,
            "T_lower": 293,
            "m_upper": 0,
            "m_lower": 1.2 * area * 3,  # 使用实际房间面积
            "h_interface": 3,
            "geometry": room,  # 保存房间几何信息
            "connected_rooms": []  # 相邻房间列表
        }
    
    # 二楼房间
    for i, room in enumerate(building.floors[2].rooms):
        room_name = f"2F_Room{i+1}"
        area = calculate_room_area(room)
        rooms[room_name] = {
            "name": room_name,
            "T_upper": 300,
            "T_lower": 293,
            "m_upper": 0,
            "m_lower": 1.2 * area * 3,
            "h_interface": 3,
            "geometry": room,
            "connected_rooms": []
        }
    
    # 楼梯
    stair_area = calculate_room_area(building.staircase["area"])
    rooms["Stairs"] = {
        "name": "Stairs",
        "T_upper": 300,
        "T_lower": 293,
        "m_upper": 0,
        "m_lower": 1.2 * stair_area * 3,
        "h_interface": 3,
        "geometry": building.staircase["area"],
        "connected_rooms": []
    }
    
    # 设置房间连接关系
    # 根据门的位置确定相邻房间
    setup_room_connections(rooms, building)
    
    # 初始火源设置在1F_Room1
    fire_source = {"room": "1F_Room1", "HRR": 50000}
    
    return rooms, fire_source

def calculate_room_area(vertices):
    """
    计算多边形房间的面积
    """
    area = 0
    for i in range(len(vertices)-1):
        x1, y1 = vertices[i]
        x2, y2 = vertices[i+1]
        area += x1*y2 - x2*y1
    return abs(area) / 2

def setup_room_connections(rooms, building):
    """
    根据门的位置设置房间的连接关系
    """
    # 设置一楼房间之间的连接
    for i, door in enumerate(building.floors[1].doors):
        if i < len(building.floors[1].rooms) - 1:
            room1 = f"1F_Room{i+1}"
            room2 = f"1F_Room{i+2}"
            rooms[room1]["connected_rooms"].append(room2)
            rooms[room2]["connected_rooms"].append(room1)
    
    # 设置二楼房间之间的连接
    for i, door in enumerate(building.floors[2].doors):
        if i < len(building.floors[2].rooms) - 1:
            room1 = f"2F_Room{i+1}"
            room2 = f"2F_Room{i+2}"
            rooms[room1]["connected_rooms"].append(room2)
            rooms[room2]["connected_rooms"].append(room1)
    
    # 设置楼梯与相邻房间的连接
    rooms["Stairs"]["connected_rooms"].extend(["1F_Room1", "2F_Room1"])
    rooms["1F_Room1"]["connected_rooms"].append("Stairs")
    rooms["2F_Room1"]["connected_rooms"].append("Stairs")

def update_room_state(room, fire, dt, c_p, A_floor, C_d, vent_area):
    """
    更新单个房间的状态（质量守恒、能量守恒、分界面高度）。
    """
    # 参数验证
    if room["T_upper"] < room["T_lower"]:
        raise ValueError(f"Upper layer temperature cannot be lower than lower layer: {room['name']}")

    # 火灾产生的烟气质量和热量
    if fire["room"] == room["name"]:
        Q_fire = fire["HRR"]
        m_fire = Q_fire / (c_p * (room["T_upper"] - room["T_lower"] + 1e-3))
    else:
        Q_fire = 0
        m_fire = 0

    # 通风口的流量
    vent_flow = max(0, C_d * vent_area * ((room["T_upper"] - room["T_lower"]) / 1.2) ** 0.5)

    # 质量守恒
    room["m_upper"] = max(0, room["m_upper"] + (m_fire - vent_flow) * dt)
    room["m_lower"] = max(0, room["m_lower"] - (m_fire - vent_flow) * dt)

    # 能量守恒
    if room["m_upper"] > 0:
        room["T_upper"] += (Q_fire - c_p * vent_flow * (room["T_upper"] - room["T_lower"])) / (room["m_upper"] * c_p + 1e-3) * dt
    if room["m_lower"] > 0:
        room["T_lower"] -= (Q_fire - c_p * vent_flow * (room["T_upper"] - room["T_lower"])) / (room["m_lower"] * c_p + 1e-3) * dt

    # 分界面高度
    room["h_interface"] = max(0, min(room["m_lower"] / (1.2 * A_floor), 3))

    return room

def transfer_between_rooms(room_from, room_to, transfer_coeff, dt):
    """
    模拟不同房间之间的烟气和热量传递。
    """
    # 计算上层温度差和流量
    delta_T = room_from["T_upper"] - room_to["T_upper"]
    transfer_mass = transfer_coeff * delta_T * dt  # 质量流动量

    # 更新质量
    room_from["m_upper"] -= transfer_mass
    room_to["m_upper"] += transfer_mass

    # 更新能量
    energy_transfer = transfer_mass * (room_from["T_upper"] - room_to["T_upper"])
    room_from["T_upper"] -= energy_transfer / (room_from["m_upper"] + 1e-3)
    room_to["T_upper"] += energy_transfer / (room_to["m_upper"] + 1e-3)

    return room_from, room_to

def export_results(results, filename):
    """
    导出模拟结果到CSV文件
    """
    data = []
    for room_name, room_data in results.items():
        for t in range(len(room_data["h_interface"])):
            data.append({
                "time": t,
                "room": room_name,
                "h_interface": room_data["h_interface"][t],
                "T_upper": room_data["T_upper"][t],
                "T_lower": room_data["T_lower"][t]
            })
    
    df = pd.DataFrame(data)
    df.to_csv(filename, index=False)

# 模型参数
c_p = 1000  # 空气比热 (J/kg.K)
vent_area = 1.0  # 通风口面积 (m^2)
C_d = 0.6  # 排气系数
transfer_coeff = 0.01  # 房间间传递系数
dt = 1  # 时间步长 (s)
time = np.arange(0, 300, dt)  # 模拟5分钟
grid_size = 10  # 每个房间划分的网格大小

# 初始化场景
rooms, fire_source = initialize_scene()

# 存储结果
results = {room: {"h_interface": [], "T_upper": [], "T_lower": []} for room in rooms}

# 初始化图形对象
fig = None
axes = None

# 仿真循环
for t in time:
    # 更新单个房间状态
    for room_name, room in rooms.items():
        rooms[room_name] = update_room_state(room, fire_source, dt, c_p, 50, C_d, vent_area)

    # 模拟房间间传递
    rooms["1F_Room1"], rooms["1F_Room2"] = transfer_between_rooms(
        rooms["1F_Room1"], rooms["1F_Room2"], transfer_coeff, dt
    )

    # 保存结果
    for room_name, room in rooms.items():
        results[room_name]["h_interface"].append(room["h_interface"])
        results[room_name]["T_upper"].append(room["T_upper"])
        results[room_name]["T_lower"].append(room["T_lower"])
    
    # 生成三维网格并可视化
    smoke_grid = generate_smoke_grid(rooms, grid_size)
    fig, axes = visualize_smoke(smoke_grid, rooms, t, fig, axes)

plt.ioff()  # 关闭交互模式
plt.show()  # 显示最终结果

# 导出结果
export_results(results, "results.csv")

