# 建筑物疏散模拟系统

这是一个基于Python的建筑物疏散模拟系统，用于模拟多层建筑物中的人员疏散过程。系统考虑了火灾、烟雾等危险因素的影响，并实现了智能寻路算法来模拟人员的疏散行为。

## 功能特点

- 多层建筑物模拟（当前支持两层建筑）
- 基于A*算法的智能寻路
- 火灾和烟雾扩散模拟
- 人群行为模拟（包括避障、拥挤等）
- 实时可视化显示
- 疏散数据统计和分析

## 安装要求

1. Python 3.8+
2. 安装依赖包：
```bash
pip install -r requirements.txt
```

## 使用方法

1. 克隆项目到本地：
```bash
git clone [repository-url]
cd BuildingEvacuation
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 运行模拟：
```bash
python main.py
```

## 项目结构

- `main.py`: 主程序入口
- `building.py`: 建筑物模型定义
- `evacuation.py`: 疏散模拟核心逻辑
- `pathfinding.py`: A*寻路算法实现
- `visualization.py`: 可视化模块
- `fire_smoke_growth.py`: 火灾和烟雾模拟

## 配置说明

- 可以在 `building.py` 中修改建筑物的布局和参数
- 在 `evacuation.py` 中可以调整人员的行为参数
- 火灾模拟参数可在 `fire_smoke_growth.py` 中配置

## 贡献指南

欢迎提交问题和改进建议。如果您想贡献代码，请：

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的改动 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件 