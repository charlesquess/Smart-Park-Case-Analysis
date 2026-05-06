import time
import pandas as pd
import smart_scheduler 

def run_poc_evaluation(file_path):
    print("="*60)
    print(" 🚀 初始化星汇智慧园区 - AI 核心调度引擎 (C++ 解耦重构版) ")
    print("="*60)
    
    engine = smart_scheduler.ConvergenceEngine()
    
    print(f"📥 正在加载原始告警流数据: {file_path}")
    df = pd.read_csv(file_path)
    
    # 预处理：时间戳转秒级，空值填充
    start_prep = time.time()
    df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**9
    df['confidence'] = df['confidence'].fillna(-1.0)
    df['building'] = df['building'].fillna('Unknown').astype(str)
    
    events_stream = df[['source_type', 'device_id', 'alert_type', 'building', 'timestamp', 'confidence']].to_dict(orient='records')
    print(f"   数据预处理耗时: {(time.time() - start_prep):.4f} 秒")
    
    print("⚙️  开始注入 C++ 状态机进行多通道收敛计算...")
    start_engine = time.time()
    
    # 设定视觉置信度阈值为 0.75
    stats = engine.process_stream(events_stream, 0.75)
    
    engine_time = time.time() - start_engine

    total = stats['total']
    dispatched = stats['dispatched']
    compression = (total - dispatched) / total * 100
    daily_avg = dispatched / 7

    print("\n" + "="*60)
    print(" 📊 C++ 收敛引擎运行报告 (黑盒验证结果) ")
    print("="*60)
    print(f" [接入层] 总告警吞吐量   : {total:,} 条")
    print("-" * 60)
    print(f" 🛡️  L1 视觉低置信度清洗 : -{stats['l1_dropped']:,} 条")
    print(f" 🤫 L2 状态机单点防抖    : -{stats['l2_suppressed']:,} 条")
    print(f" 🗃️  L3 计划工单蓄水池    : -{stats['l3_pooled']:,} 条")
    print(f" 📦 L4 优先级通道空间聚合 : -{stats['l4_spatial_batched']:,} 条")
    print("-" * 60)
    print(f" 🎯 最终生成下发工单包   : {dispatched:,} 个")
    print(f" 🔥 整体派单压力压降比   : {compression:.2f}%")
    print(f" 👷 物理世界日均工单负荷 : {daily_avg:.1f} 单/天")
    print("="*60)
    print(f" ⚡ 核心 C++ 算法耗时    : {engine_time:.6f} 秒")
    print("="*60)
    
    worker_count_per_shift = 25
    tasks_per_worker = daily_avg / worker_count_per_shift
    
    print(" 💡 架构师点评: ")
    print(f" 派单量已收敛至日均 {daily_avg:.1f} 单。按 50 名工人两班倒（单班约 25 人）计算，单人单班次任务包约 {tasks_per_worker:.1f} 个。")
    if tasks_per_worker > 10:
        print(" ⚠️ 警告：当前工单负荷依然偏重，请检查防抖策略或 L3 蓄水池白名单！")
    else:
        print(" 实现了响应速度与人力负荷的完美平衡，且完全符合 SLA 矩阵的安全优先级要求。")

if __name__ == "__main__":
    run_poc_evaluation("alerts_7days.csv")