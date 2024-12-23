# main.py

from building import Building
from evacuation import EvacuationSimulation
from visualization import plot_building, plot_simulation
import argparse
import json

class SimulationConfig:
    def __init__(self):
        # 建筑物参数
        self.building_config = {
            "num_floors": 2,
            "floor_width": 50,
            "floor_length": 40,
            "floor_height": 3.0,
            "room_capacity": 200
        }
        
        # 火灾参数
        self.fire_config = {
            "initial_fires": [
                {
                    "room_id": "room_1_1",
                    "position": (10, 7.5),
                    "start_time": 0.0,
                    "growth_rate": 0.47,
                    "max_hrr": 50000.0
                }
            ],
            "fire_spread_enabled": True,
            "max_temperature": 800.0
        }
        
        # 疏散参数
        self.evacuation_config = {
            "initial_occupants": {
                1: 20,  # 一楼20人
                2: 20   # 二楼20人
            },
            "agent_speed": 2.0,
            "agent_radius": 0.5,
            "personal_space": 1.0
        }
        
        # 模拟参数
        self.simulation_config = {
            "time_step": 0.1,
            "max_simulation_time": 600,  # 10分钟
            "visualization_interval": 0.05
        }
    
    @classmethod
    def from_json(cls, json_file):
        """从JSON文件加载配置"""
        config = cls()
        with open(json_file, 'r') as f:
            data = json.load(f)
            for key, value in data.items():
                if hasattr(config, key):
                    setattr(config, key, value)
        return config
    
    def save_to_json(self, json_file):
        """保存配置到JSON文件"""
        config_dict = {
            "building_config": self.building_config,
            "fire_config": self.fire_config,
            "evacuation_config": self.evacuation_config,
            "simulation_config": self.simulation_config
        }
        with open(json_file, 'w') as f:
            json.dump(config_dict, f, indent=4)

def setup_fire_sources(building, fire_config):
    """设置火源"""
    for fire_info in fire_config["initial_fires"]:
        building.fire_model.add_fire_source(
            fire_info["room_id"],
            fire_info["position"],
            fire_info["start_time"]
        )
        # 设置火源参数
        fire_source = building.fire_model.fire_sources[-1]
        fire_source.growth_rate = fire_info.get("growth_rate", 0.47)
        fire_source.max_hrr = fire_info.get("max_hrr", 5000.0)

def initialize_simulation(config):
    """初始化模拟"""
    # 创建并初始化建筑物
    building = Building()
    building.initialize_building()
    
    # 设置火源
    setup_fire_sources(building, config.fire_config)
    
    # 创建疏散模拟
    simulation = EvacuationSimulation(building)
    
    # 设置初始人数分布
    simulation.initialize_agents(config.evacuation_config["initial_occupants"])
    
    # 设置疏散参数
    for agent in simulation.agents:
        agent.desired_speed = config.evacuation_config["agent_speed"]
        agent.radius = config.evacuation_config["agent_radius"]
        agent.personal_space = config.evacuation_config["personal_space"]
    
    return building, simulation

def print_smoke_zone_connections(building):
    """打印所有smoke_zone之间的连接关系"""
    print("\n=== Smoke Zone 连接关系 ===")
    connections_printed = set()
    
    for floor_num in building.floors:
        print(f"\n第{floor_num}层:")
        for conn in building.fire_model.zone_connections:
            zone1_id = conn.zone1.room_id
            zone2_id = conn.zone2.room_id
            
            # 避免重复打印
            conn_key = tuple(sorted([zone1_id, zone2_id]))
            if conn_key in connections_printed:
                continue
            
            # 检查是否涉及当前楼层
            if (zone1_id.startswith(f"room_{floor_num}") or 
                zone2_id.startswith(f"room_{floor_num}")):
                
                connections_printed.add(conn_key)
                
                # 获取连接详情
                pos = conn.geometry['position']
                width = conn.geometry.get('width', 0)
                height = conn.geometry.get('height', 0)
                
                print(f"  {zone1_id} <-> {zone2_id}:")
                print(f"    类型: {conn.connection_type}")
                print(f"    位置: ({pos[0]:.1f}, {pos[1]:.1f})")
                print(f"    尺寸: {width:.1f}m x {height:.1f}m")

def run_simulation(building, simulation, config):
    """运行模拟"""
    # 打印连接关系
    print_smoke_zone_connections(building)
    
    # # 显示初始建筑物布局
    # plot_building(building, show_grid=False)
    
    # 运行动态模拟
    plot_simulation(building, simulation)

def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='建筑物疏散模拟')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--save-config', type=str, help='保存默认配置到文件')
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    # 创建配置
    if args.config:
        config = SimulationConfig.from_json(args.config)
    else:
        config = SimulationConfig()
    
    # 保存默认配置
    if args.save_config:
        config.save_to_json(args.save_config)
        print(f"配置已保存到: {args.save_config}")
        return
    
    # 初始化并运行模拟
    building, simulation = initialize_simulation(config)
    run_simulation(building, simulation, config)

if __name__ == "__main__":
    main()