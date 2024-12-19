# main.py

from building import Building
from evacuation import EvacuationSimulation
from visualization import plot_building, plot_simulation

def main():
    # 创建并初始化建筑物
    building = Building()
    building.initialize_building()
    
    # # 显示初始建筑物布局（包含网格）
    # plot_building(building, show_grid=False)
    
    # 创建疏散模拟
    simulation = EvacuationSimulation(building)
    
    # 设置初始人数分布
    simulation.initialize_agents({
        1: 20,  # 一楼20人
        2: 30   # 二楼30人
    })
    
    # 运行模拟
    plot_simulation(building, simulation)

if __name__ == "__main__":
    main()