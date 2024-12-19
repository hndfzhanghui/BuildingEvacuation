import numpy as np

class FireZone:
    def __init__(self, room_id, area):
        self.room_id = room_id
        self.area = area                  # 房间面积
        self.temperature = 20.0           # 初始温度(℃)
        self.smoke_density = 0.0          # 烟雾密度(0-1)
        self.is_on_fire = False           # 是否着火
        self.fire_duration = 0.0          # 火灾持续时间
        self.heat_release_rate = 0.0      # 热释放率(kW)
        
class FireModel:
    def __init__(self, building):
        self.building = building
        self.fire_zones = {}              # 存储每个房间的火灾状态
        self.fire_spread_rate = 0.05      # 火灾蔓延速率(m/s)
        self.smoke_spread_rate = 0.1      # 烟雾蔓延速率
        self.max_temperature = 800.0      # 最高温度(℃)
        self.initialized = False
        
    def initialize_fire(self, initial_room_id):
        """初始化火灾，设置初始着火点"""
        # 为每个房间创建FireZone
        for floor in self.building.floors.values():
            for i, room in enumerate(floor.rooms):
                # 计算房间面积
                room_area = self._calculate_room_area(room)
                zone = FireZone(f"room_{floor.floor_number}_{i+1}", room_area)
                self.fire_zones[f"room_{floor.floor_number}_{i+1}"] = zone
        
        # 设置初始着火点
        if initial_room_id in self.fire_zones:
            self.fire_zones[initial_room_id].is_on_fire = True
            self.fire_zones[initial_room_id].temperature = 200.0  # 初始火灾温度
            self.fire_zones[initial_room_id].smoke_density = 0.3  # 初始烟雾密度
        
        self.initialized = True
    
    def _calculate_room_area(self, room_coords):
        """计算房间面积"""
        # 使用多边形面积公式
        coords = np.array(room_coords)
        x = coords[:, 0]
        y = coords[:, 1]
        return 0.5 * np.abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    def update(self, dt):
        """更新火灾状态"""
        if not self.initialized:
            return
            
        for zone_id, zone in self.fire_zones.items():
            if zone.is_on_fire:
                # 更新火灾持续时间
                zone.fire_duration += dt
                
                # 更新温度
                target_temp = self.max_temperature
                zone.temperature = min(zone.temperature + 50 * dt, target_temp)
                
                # 更新烟雾密度
                zone.smoke_density = min(zone.smoke_density + self.smoke_spread_rate * dt, 1.0)
                
                # 更新热释放率 (使用简化的t-square火灾增长模型)
                alpha = 0.047  # 快速增长火灾
                zone.heat_release_rate = alpha * (zone.fire_duration ** 2)
                
                # 蔓延到相邻房间
                self._spread_fire(zone_id)
    
    def _spread_fire(self, zone_id):
        """处理火灾向相邻房间的蔓延"""
        # TODO: 实现火灾蔓延逻辑
        # 1. 确定相邻房间
        # 2. 根据门的位置和状态计算蔓延概率
        # 3. 更新相邻房间的火灾状态
        pass
    
    def get_zone_state(self, room_id):
        """获取指定房间的火灾状态"""
        if room_id in self.fire_zones:
            zone = self.fire_zones[room_id]
            return {
                'temperature': zone.temperature,
                'smoke_density': zone.smoke_density,
                'is_on_fire': zone.is_on_fire,
                'heat_release_rate': zone.heat_release_rate
            }
        return None 