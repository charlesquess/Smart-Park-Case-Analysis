1. 文件结构

* Design_Document/Delivery_item1：交付物 1：需求澄清清单
* Design_Document/Delivery_item2：交付物 2：系统设计文档主体
* Design_Document/Delivery_item3：交付物 3：对附录 A 的批判

* Delivery_item4/poc_main.py: 交付物4的主程序，基于命令行的数据流跑批验证入口，输出压缩比与日均负荷评估。
* Delivery_item4/smart_monitor.py：交付物4的可视化大屏程序，基于 PyQt6 的实时智能调度指挥中心可视化大屏（支持调速与实时拦截观测）以证明真实场景下流式数据处理的可行性。
* Delivery_item4/smart_scheduler.cp39-win_amd64.pyd：交付物4的核心C++调度算法编译产物，提供高性能的工单调度核心函数接口。
* requirements.txt：Python 外部依赖声明。

2. 环境依赖
- 请确保测试环境的 Python 版本=3.9，并安装requirements.txt中的依赖包。

3. 运行方式说明
- 执行黑盒跑批验证
运行验证脚本，系统将在一秒内吞吐 3.3 万条历史告警数据，并输出详尽的漏斗收敛报告：
```bash
python poc_main.py
```
- 启动可视化大屏
运行 UI 程序，直观观测 L1~L4 多级漏斗拦截与空间打包的动态过程：
```bash
python smart_monitor.py
```
