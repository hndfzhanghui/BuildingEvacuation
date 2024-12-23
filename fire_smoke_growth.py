# fire_smoke_growth.py

# 还存在的问题
# TODO：烟雾超过1m，才应该到其他屋子
# TODO：cool layer温度不应该那么快就上升到50度
# TODO：hot layer的温度应该上升的更快
# TODO：目前的计算核心逻辑还有问题

import numpy as np

class FireSource:
    def __init__(self, position, room, start_time=0.0):
        self.position = np.array(position)      # 火源位置
        self.room = room                        # 所属房间
        self.start_time = start_time           # 起火时间
        self.heat_release_rate = 0.0           # 热释放率(kW)
        self.smoke_production_rate = 0.0       # 烟气产生率(kg/s)
        self.plume_temperature = 20.0          # 火羽温度(℃)
        self.active = False                    # 火源是否活跃
        
        # 火灾增长参数
        self.growth_rate = 0.19               # α-t²火灾增长率 (kW/s²)，超快速增长
        self.max_hrr = 3000.0                 # 最大热释放率(kW)
        self.smoke_yield = 0.2                # 烟气产率(kg/kg)
        self.fire_duration = 0.0              # 火灾持续时间
        
    def update(self, current_time):
        """更新火源状态"""
        if current_time >= self.start_time:
            if not self.active:
                self.active = True
                self.fire_duration = 0.0
            else:
                self.fire_duration = current_time - self.start_time
            
            # 基础热释放率（α-t²模型）
            base_hrr = min(
                self.growth_rate * (self.fire_duration ** 2),
                self.max_hrr
            )
            
            # 考虑通风限制
            available_oxygen = self._calculate_available_oxygen()
            ventilation_factor = min(1.0, available_oxygen / self._required_oxygen(base_hrr))
            
            # 最终热释放率
            self.heat_release_rate = base_hrr * ventilation_factor
            
            # 估算烟气产生率 (基于热释放率)
            # 假设每千瓦热量产生0.1kg烟气
            self.smoke_production_rate = self.heat_release_rate * self.smoke_yield / 1000
            
            # 估算火羽温度（基于热释放率）
            # 使用McCaffrey火羽温度关系式的简化版本
            self.plume_temperature = 20 + (self.heat_release_rate ** 0.4)
            
            return True
        return False
    
    def _calculate_available_oxygen(self):
        """估算可用氧气量"""
        # 简化计算，基于房间体积和开口面积
        room_volume = self.room.volume
        total_vent_area = sum(conn.geometry['width'] * conn.geometry['height'] 
                            for conn in self.room.connections.values())
        return room_volume * 0.21 + total_vent_area * 0.5  # kg/s，简化估算
    
    def _required_oxygen(self, hrr):
        """计算指定热释放率所需的氧气量"""
        return hrr * 0.13 / 1000  # 每kW火灾大约需要0.13kg/s的氧气

class SmokeZone:
    def __init__(self, boundary_points, room_id):
        self.boundary_points = boundary_points
        self.room_id = room_id
        self.connections = {}              # {zone_id: ZoneConnection}
        self.smoke_height = 0.0            # 烟层厚度(m)
        self.hot_layer_temp = 20.0         # 热层温度(℃)
        self.cold_layer_temp = 20.0        # 冷层温度(℃)
        self.interface_height = 3.0        # 冷热层界面高度(m)
        self.pressure = 101325             # 压力(Pa)
        self.fire_sources = []             # 区域内的火源列表
        self.total_smoke_volume = 0.0    # 累计烟雾体积(m³)
        
        # 计算房间体积和面积
        self.floor_area = self._calculate_area()
        self.height = 3.0                  # 房间高度(m)
        self.volume = self.floor_area * self.height
        
    def _calculate_area(self):
        """计算多边形面积"""
        points = np.array(self.boundary_points)
        x = points[:, 0]
        y = points[:, 1]
        return 0.5 * abs(np.dot(x, np.roll(y, 1)) - np.dot(y, np.roll(x, 1)))
    
    def add_fire_source(self, fire_source):
        """添加火源"""
        fire_source.room = self  # 确保火源知道它属于哪个房间
        self.fire_sources.append(fire_source)
    
    def _calculate_air_properties(self, temperature):
        """计算给定温度下的空气属性"""
        T = temperature + 273.15  # 转换为开尔文
        # 理想气体定律计算密度
        rho = 1.2 * (293 / T)  
        # 空气比热容的简化温度相关性
        cp = 1.005 + 0.00004 * (T - 293)  # kJ/kg·K
        return rho, cp

    def update_zone_model(self, time_step, current_time):
        """更新区域的两区模型参数"""
        total_heat_release = 0.0
        total_smoke_production = 0.0
        
        # 计算所有活跃火源的总效果
        for source in self.fire_sources:
            if source.update(current_time):
                total_heat_release += source.heat_release_rate
                total_smoke_production += source.smoke_production_rate
        
        if total_heat_release > 0:
            # 调整烟气扩散速率
            smoke_density = 0.5  # 降低烟气密度以加快扩散
            new_smoke_volume = (total_smoke_production * time_step) / smoke_density
            delta_height = new_smoke_volume / self.floor_area
            
            # 限制单次更新的最大变化量
            max_delta = 0.1  # 每次最多变化0.1米
            delta_height = min(delta_height, max_delta)
                                
            rho_air_hot, cp_air_hot = self._calculate_air_properties(self.hot_layer_temp)
            rho_air_cold, cp_air_cold = self._calculate_air_properties(self.cold_layer_temp)

            # 确保烟层厚度在合理范围内
            MIN_SMOKE_HEIGHT = 0.05  # 最小5cm
            self.smoke_height = min(self.height, max(MIN_SMOKE_HEIGHT, 
                                                   self.smoke_height + delta_height))
            
            # 更新热层温度
            if self.smoke_height > 0:
                hot_layer_volume = self.floor_area * self.smoke_height
                cold_layer_volume = self.floor_area * (self.height - self.smoke_height)
                
                # 计算层间热传递
                heat_transfer_coeff = 0.1  # W/m²·K
                interface_area = self.floor_area
                Q_transfer = heat_transfer_coeff * interface_area * \
                            (self.hot_layer_temp - self.cold_layer_temp) * time_step
                
                # 热层和冷层的质量
                mass_hot_layer = hot_layer_volume * rho_air_hot
                mass_cold_layer = cold_layer_volume * rho_air_cold
                
                if mass_hot_layer > 0 and mass_cold_layer > 0:
                    # 计算火源导致的温度变化
                    energy_input = total_heat_release * time_step
                    delta_T_fire = energy_input / (cp_air_hot * mass_hot_layer)
                    
                    # 限制火源导致的温度变化
                    MAX_TEMP_CHANGE = 100  # 每步最大温度变化100°C
                    delta_T_fire = min(MAX_TEMP_CHANGE, delta_T_fire)
                    
                    # 计算传热导致的温度变化
                    delta_T_hot = -Q_transfer / (cp_air_hot * mass_hot_layer)
                    delta_T_cold = Q_transfer / (cp_air_cold * mass_cold_layer)
                    
                    # 限制传热导致的温度变化
                    delta_T_hot = max(-MAX_TEMP_CHANGE, delta_T_hot)
                    delta_T_cold = min(MAX_TEMP_CHANGE, delta_T_cold)
                    
                    # 更新温度，确保在合理范围内
                    MIN_TEMP = 20.0
                    MAX_HOT_TEMP = 800.0
                    MAX_COLD_TEMP = 50.0
                    
                    # 热层最终温度
                    new_hot_temp = self.hot_layer_temp + delta_T_fire + delta_T_hot
                    self.hot_layer_temp = min(MAX_HOT_TEMP, max(MIN_TEMP, new_hot_temp))
                    
                    # 冷层最终温度
                    new_cold_temp = self.cold_layer_temp + delta_T_cold
                    self.cold_layer_temp = min(MAX_COLD_TEMP, max(MIN_TEMP, new_cold_temp))
                
                # 更新界面高度
                self.interface_height = self.height - self.smoke_height

class ZoneConnection:
    def __init__(self, zone1, zone2, connection_type, geometry):
        self.zone1 = zone1
        self.zone2 = zone2
        self.connection_type = connection_type
        self.geometry = geometry
        self.flow_rate = 0.0
    
    def calculate_flow_rate(self, time_step):
        """计算烟气流动速率"""
        # 获取连接区域的几何参数
        height = self.geometry.get('height', 2.0)
        width = self.geometry.get('width', 1.0)
        
        # 添加流动触发条件
        min_smoke_height = 0.1  # 最小烟层高度
        min_temp_diff = 50.0    # 最小温度差
        
        # 检查源区域是否有足够的烟层和温度差
        if (self.zone1.height - self.zone1.interface_height) > min_smoke_height and \
           (self.zone1.hot_layer_temp - self.zone1.cold_layer_temp) > min_temp_diff:
            # 计算压力差
            rho_cold = 1.2  # kg/m³
            g = 9.81       # m/s²
            
            # 考虑温度差导致的浮力
            T1 = self.zone1.hot_layer_temp + 273.15
            T2 = self.zone2.cold_layer_temp + 273.15
            rho1 = rho_cold * 293 / T1
            rho2 = rho_cold * 293 / T2
            
            # 计算压力差
            delta_p = g * (rho2 - rho1) * (self.zone1.height - self.zone1.interface_height)
            
            # 计算流量
            if abs(delta_p) > 0.1:
                flow_coefficient = 0.6
                effective_height = min(height, 
                                    self.zone1.height - self.zone1.interface_height)
                effective_area = width * effective_height
                
                self.flow_rate = flow_coefficient * effective_area * \
                                np.sqrt(2 * abs(delta_p) / rho_cold)
                if delta_p < 0:
                    self.flow_rate = -self.flow_rate
                    
                # 限制流量（确保接收房间不会超过源房间）
                if self.flow_rate > 0:
                    source_zone = self.zone1
                    target_zone = self.zone2
                else:
                    source_zone = self.zone2
                    target_zone = self.zone1
                    
                source_smoke_height = source_zone.height - source_zone.interface_height
                target_smoke_height = target_zone.height - target_zone.interface_height
                
                if target_smoke_height >= source_smoke_height:
                    self.flow_rate = 0.0
            else:
                self.flow_rate = 0.0
        else:
            self.flow_rate = 0.0

class FireModel:
    def __init__(self, building):
        self.building = building
        self.smoke_zones = {}
        self.zone_connections = []
        self.fire_sources = []
        self._current_time = 0.0  # 添加时间跟踪
        
    def add_fire_source(self, room_id, position, start_time=0.0):
        """添加火源"""
        if room_id in self.smoke_zones:
            zone = self.smoke_zones[room_id]
            fire_source = FireSource(position, zone, start_time)  # 传入zone作为room
            self.fire_sources.append(fire_source)
            zone.add_fire_source(fire_source)
            return fire_source
        return None
    
    def initialize_fire(self, initial_room_id):
        """初始化火灾和烟气区域"""
        # 初始化所有烟气区域
        for floor_num in self.building.floors:
            floor = self.building.floors[floor_num]
            for i, room in enumerate(floor.rooms):
                room_id = f"room_{floor_num}_{i+1}"
                self.smoke_zones[room_id] = SmokeZone(room, room_id)
        
        # 建立区域间的连接
        self._setup_connections()
        
        # 添加初始火源
        if initial_room_id in self.smoke_zones:
            room = self.smoke_zones[initial_room_id]
            center = np.mean(room.boundary_points, axis=0)
            self.add_fire_source(initial_room_id, center)
    
    def _setup_connections(self):
        """建立区域间的连接关系"""
        # 设置同一层相邻房间的连接
        for floor_num in self.building.floors:
            floor = self.building.floors[floor_num]
            for j, door in enumerate(floor.doors):
                room1_id = f"room_{floor_num}_{j+1}"
                room2_id = f"room_{floor_num}_{j+2}"
                if room1_id in self.smoke_zones and room2_id in self.smoke_zones:
                    self._add_connection(room1_id, room2_id, 'door', door)
        
        # 设置楼层间的连接
        for stairs in self.building.stairs.values():
            self._add_stair_connections(stairs)
    
    def _add_connection(self, room1_id, room2_id, conn_type, geometry):
        """添加两个区域之间的连接"""
        if room1_id in self.smoke_zones and room2_id in self.smoke_zones:
            conn = ZoneConnection(
                self.smoke_zones[room1_id],
                self.smoke_zones[room2_id],
                conn_type,
                {'width': 2.0, 'height': 2.0, 'position': geometry[0]}
            )
            self.zone_connections.append(conn)
    
    def _add_stair_connections(self, stairs):
        """添加楼梯连接"""
        for i in range(len(stairs.connecting_floors)-1):
            floor1 = stairs.connecting_floors[i]
            floor2 = stairs.connecting_floors[i+1]
            room1_id = f"room_{floor1}_3"
            room2_id = f"room_{floor2}_3"
            if room1_id in self.smoke_zones and room2_id in self.smoke_zones:
                geometry = {'width': 2.0, 'height': 3.0, 'position': stairs.get_entry_position(floor1)}
                conn = ZoneConnection(
                    self.smoke_zones[room1_id],
                    self.smoke_zones[room2_id],
                    'stair',
                    geometry
                )
                self.zone_connections.append(conn)
    
    def print_smoke_status(self):
        """打印烟气状态信息"""
        print(f"\n时间: {self._current_time:.1f}秒")
        
        # 1. 打印每个房间的状态
        for zone_id, zone in self.smoke_zones.items():
            if len(zone.fire_sources) > 0 or zone.hot_layer_temp > 20.0:  # 打印所有受影响房间
                print(f"\n房间 {zone_id}:")
                print(f"  热层高度: {zone.height - zone.interface_height:.3f} m")
                print(f"  热层温度: {zone.hot_layer_temp:.1f} °C")
                print(f"  冷层温度: {zone.cold_layer_temp:.1f} °C")
                print(f"  房间高度占比: {((zone.height - zone.interface_height)/zone.height)*100:.1f}%")
        
        # 2. 打印连接处的流动状态
        print("\n流动状态:")
        for conn in self.zone_connections:
            if abs(conn.flow_rate) > 0.001:  # 只打印有显著流动的连接
                print(f"\n{conn.zone1.room_id} <-> {conn.zone2.room_id}:")
                print(f"  流量: {conn.flow_rate:.3f} m³/s")
                print(f"  方向: {'从1到2' if conn.flow_rate > 0 else '从2到1'}")
                # 打印压力差和温度差
                delta_p = conn.zone1.pressure - conn.zone2.pressure
                delta_T = conn.zone1.hot_layer_temp - conn.zone2.hot_layer_temp
                print(f"  压力差: {delta_p:.2f} Pa")
                print(f"  温度差: {delta_T:.1f} °C")
    
    def update(self, time_step):
        """更新火灾和烟气状态"""
        # 更新当前时间
        self._current_time += time_step
        
        # 1. 更新每个区域的状态
        for zone in self.smoke_zones.values():
            zone.update_zone_model(time_step, self._current_time)
        
        # 2. 计算区域间的烟气流动
        for conn in self.zone_connections:
            conn.calculate_flow_rate(time_step)
        
        # 3. 更新烟气分布
        for conn in self.zone_connections:
            if conn.flow_rate > 0:
                # 计算流动的烟气体积
                smoke_volume = conn.flow_rate * time_step
                # 考虑房间面积对烟层高度的影响
                delta_height1 = smoke_volume / conn.zone1.floor_area
                delta_height2 = smoke_volume / conn.zone2.floor_area
                
                # 更新烟层高度
                conn.zone1.smoke_height = max(0.0, conn.zone1.smoke_height - delta_height1)
                conn.zone2.smoke_height = min(conn.zone2.height, conn.zone2.smoke_height + delta_height2)
            else:
                # 反向流动
                smoke_volume = abs(conn.flow_rate) * time_step
                delta_height1 = smoke_volume / conn.zone1.floor_area
                delta_height2 = smoke_volume / conn.zone2.floor_area
                
                conn.zone1.smoke_height = min(conn.zone1.height, conn.zone1.smoke_height + delta_height1)
                conn.zone2.smoke_height = max(0.0, conn.zone2.smoke_height - delta_height2)
            
            # 更新界面高度
            conn.zone1.interface_height = conn.zone1.height - conn.zone1.smoke_height
            conn.zone2.interface_height = conn.zone2.height - conn.zone2.smoke_height
        
        # 4. 打印状态信息
        self.print_smoke_status()
    
    def get_zone_state(self, room_id):
        """获取指定房间的火灾和烟气状态"""
        if room_id in self.smoke_zones:
            zone = self.smoke_zones[room_id]
            return {
                'temperature': zone.hot_layer_temp,
                'smoke_height': zone.smoke_height,
                'is_on_fire': len(zone.fire_sources) > 0,
                'heat_release_rate': sum(source.heat_release_rate for source in zone.fire_sources),
                'interface_height': zone.interface_height,
                'cold_layer_temp': zone.cold_layer_temp
            }
        return None