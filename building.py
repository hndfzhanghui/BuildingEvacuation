# building.py

class Floor:
    def __init__(self, floor_number, width, length, capacity):
        self.floor_number = floor_number  # 楼层编号
        self.width = width                # 楼层宽度
        self.length = length              # 楼层长度
        self.capacity = capacity          # 楼层最大容纳人数
        self.current_people = 0           # 当前楼层人数
        self.main_exit = None            # 主出口位置（仅一楼有）
        
        self.rooms = []          # 房间边界
        self.doors = []          # 门的位置
        self.building_exit = []  # 建筑物出口（仅一楼有）
        self.obstacles = []      # 障碍物（圆形或线段）
    
    def set_main_exit(self, x, y):
        """设置主出口位置"""
        self.main_exit = (x, y)

class Stairs:
    def __init__(self, connecting_floors, capacity):
        """
        初始化楼梯
        connecting_floors: 连接的楼层列表，如 [1, 2] 表示连接一楼和二楼
        capacity: 楼梯最大容纳人数
        """
        self.connecting_floors = sorted(connecting_floors)  # 确保楼层号有序
        self.capacity = capacity          # 容量
        self.current_people = 0           # 当前人数
        self.flow_rate = 2                # 流量率
        self.passing_time = 3.0           # 通过楼梯所需时间(秒)
        
        # 楼梯的几何信息
        self.area = None                  # 楼梯区域多边形
        self.entries = {}                 # 各楼层入口位置 {floor_num: position}
        self.queue = []                   # 等待队列
    
    def initialize_geometry(self, area, entries):
        """初始化楼梯的几何信息"""
        self.area = area
        self.entries = entries
    
    def get_entry_position(self, floor):
        """获取指定楼层的入口位置"""
        return self.entries.get(floor)
    
    def get_exit_position(self, floor):
        """获取指定楼层的出口位置"""
        return self.entries.get(floor)
    
    def can_move_between(self, from_floor, to_floor):
        """检查是否可以在两个楼层间移动"""
        return (from_floor in self.connecting_floors and 
                to_floor in self.connecting_floors and 
                from_floor != to_floor)
    
    def get_next_floor(self, current_floor, direction='down'):
        """获取指定方向的下一个楼层"""
        if current_floor not in self.connecting_floors:
            return None
        
        idx = self.connecting_floors.index(current_floor)
        if direction == 'down' and idx > 0:
            return self.connecting_floors[idx - 1]
        elif direction == 'up' and idx < len(self.connecting_floors) - 1:
            return self.connecting_floors[idx + 1]
        return None
    
    def is_full(self):
        """检查楼梯是否已满"""
        return self.current_people >= self.capacity
    
    def enter(self, agent):
        """agent进入楼梯"""
        if not self.is_full():
            self.current_people += 1
            return True
        return False
    
    def exit(self, agent):
        """agent离开楼梯"""
        if self.current_people > 0:
            self.current_people -= 1
            return True
        return False

class Building:
    def __init__(self):
        self.floors = {}
        self.stairs = {}
        self.fire_model = None
    
    def add_floor(self, floor_number, width, length, capacity):
        """添加楼层"""
        self.floors[floor_number] = Floor(floor_number, width, length, capacity)
        
    def add_stairs(self, connecting_floors, capacity):
        """添加楼梯"""
        stairs = Stairs(connecting_floors, capacity)
        key = tuple(sorted(connecting_floors))
        self.stairs[key] = stairs
        return stairs
    
    def initialize_building(self):
        """初始化一个两层建筑物"""
        # 添加楼层
        self.add_floor(1, 50, 40, 200)
        self.add_floor(2, 50, 40, 200)
        
        # 添加并初始化楼梯
        stairs = self.add_stairs([1, 2], 50)  # 连接一楼和二楼的楼梯
        
        # 初始化楼梯几何信息
        stairs_area = [(25, 35), (35, 35), (35, 40), (25, 40), (25, 35)]
        stairs_entries = {
            1: (25, 37.5),  # 一楼入口/出口位置
            2: (35, 37.5)   # 二楼入口/出口位置
        }
        stairs.initialize_geometry(stairs_area, stairs_entries)
        
        # 保存楼梯信息用于可视化
        self.staircase = {
            "area": stairs_area,
            "entries": [
                {"floor": 1, "position": [(25, 35), (25, 40)]},
                {"floor": 2, "position": [(35, 35), (35, 40)]},
            ]
        }
        
        # 一楼布局
        self.floors[1].rooms = [
            [(0, 0), (20, 0), (20, 15), (0, 15), (0, 0)],  
            [(20, 0), (35, 0), (35, 15), (20, 15), (20, 0)],
            [(35, 0), (50, 0), (50, 40), (35, 40), (35, 0)],
        ]
        
        self.floors[1].doors = [
            [(17, 15), (19, 15)],
            [(21, 15), (23, 15)],
            [(35, 16), (35, 20)]
        ]
        
        self.floors[1].building_exit = [(0, 15), (0, 20)]
        
        self.floors[1].obstacles = [
            {"type": "circle", "params": (10, 30, 2)},
            {"type": "circle", "params": (20, 30, 2)},
            {"type": "line",   "params": [(25, 35), (35, 35)]}
        ]
        
        # 二楼布局
        self.floors[2].rooms = [
            [(0, 0), (20, 0), (20, 15), (0, 15), (0, 0)],
            [(20, 0), (35, 0), (35, 15), (20, 15), (20, 0)],
            [(35, 0), (50, 0), (50, 25), (35, 25), (35, 0)],
        ]
        
        self.floors[2].doors = [
            [(17, 15), (19, 15)],
            [(21, 15), (23, 15)],
            [(35, 16), (35, 20)]
        ]
        
        self.floors[2].obstacles = [
            {"type": "line", "params": [(0, 20), (25, 20)]},
            {"type": "line", "params": [(25, 20), (25, 40)]},
            {"type": "line", "params": [(25, 35), (35, 35)]}
        ]
        
        # 只设置一楼的主出口
        self.floors[1].set_main_exit(0, 17.5)
        
        # 初始化火灾模型
        from fire_smoke_growth import FireModel
        self.fire_model = FireModel(self)
        # 设置初始着火点（例如在room_1_1）
        self.fire_model.initialize_fire("room_1_1")