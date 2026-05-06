#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <string>
#include <unordered_map>
#include <vector>

namespace py = pybind11;

// 用于存储空间锁的过期时间和绑定的工单包编号
struct LockInfo {
    long long expire_ts;
    std::string batch_id;
};

class ConvergenceEngine {
private:
    // L2: 设备级防抖锁 (Key: device_id_alert_type, Value: 过期时间戳)
    std::unordered_map<std::string, long long> active_locks;
    
    // L4: 优先级空间锁 (Key: building_channel, Value: LockInfo包含时间和包编号)
    std::unordered_map<std::string, LockInfo> spatial_locks;

    // 内部计数器，用于触发定期清理
    long long event_counter = 0;

    // 修复漏洞：过期锁定期清理机制 (Garbage Collection)，防止生产环境内存泄漏
    void cleanup_expired_locks(long long current_ts) {
        for (auto it = active_locks.begin(); it != active_locks.end(); ) {
            if (current_ts > it->second) {
                it = active_locks.erase(it);
            } else {
                ++it;
            }
        }
        for (auto it = spatial_locks.begin(); it != spatial_locks.end(); ) {
            if (current_ts > it->second.expire_ts) {
                it = spatial_locks.erase(it);
            } else {
                ++it;
            }
        }
    }
    
    // 内部处理单条逻辑的私有函数
    std::string process_single(const py::dict& ev, float conf_threshold) {
        std::string source = ev["source_type"].cast<std::string>();
        std::string device_id = ev["device_id"].cast<std::string>();
        std::string alert_type = ev["alert_type"].cast<std::string>();
        
        // 容错处理：确保 building 字段存在
        std::string building = ev.contains("building") && !ev["building"].is_none() 
            ? ev["building"].cast<std::string>() 
            : "Unknown";
            
        long long ts = ev["timestamp"].cast<long long>();

        // 触发过期锁清理 (每处理1000条事件扫描一次)
        event_counter++;
        if (event_counter % 1000 == 0) {
            cleanup_expired_locks(ts);
        }

        // 1. L1: 视觉低置信度清洗 (去除假阳性)
        if (source == "camera" && ev.contains("confidence") && !ev["confidence"].is_none()) {
            float conf = ev["confidence"].cast<float>();
            if (conf > 0.0f && conf < conf_threshold) {
                return "L1_DROP";
            }
        }

        // 2. L3: 计划性工单蓄水池 (已将 circuit_fault 和 sensor_fault 移出，让其走即时派发)
        if (alert_type == "stain_detected" || alert_type == "ev_illegal_parking" || 
            alert_type == "object_left" || alert_type == "lamp_failure" || 
            alert_type == "filter_clog" || alert_type == "maintenance_required" || 
            alert_type == "open_too_long") {       
            return "L3_POOL";
        }

        // 3. L2: 单点设备状态机去重 (拦截短时间的重复脉冲)
        std::string state_key = device_id + "_" + alert_type;
        if (active_locks.count(state_key) && ts < active_locks[state_key]) {
            return "L2_SUPPRESS";
        }

        // 4. L4: 多通道优先级时空聚合与打包追踪
        bool is_p0 = (alert_type == "stuck" || alert_type == "fire_detected" || 
                      alert_type == "smoke_detected" || alert_type == "pressure_low" || 
                      alert_type == "pressure_high" || alert_type == "fall_detected");
        
        bool is_p1 = (alert_type == "people_gathering" || alert_type == "climbing_detected" || alert_type == "co_elevated");
        
        std::string channel = is_p0 ? "P0" : (is_p1 ? "P1" : "P2");
        std::string spatial_key = building + "_" + channel;

        // 检查是否命中已有的空间打包工单
        if (spatial_locks.count(spatial_key) && ts < spatial_locks[spatial_key].expire_ts) {
            std::string existing_batch_id = spatial_locks[spatial_key].batch_id;
            return "L4_BATCHED into " + existing_batch_id;
        }

        // 5. 没有命中，生成全新的响应式工单
        
        // 【终极修复】彻底解耦 L2 (防抖) 与 L4 (打包) 的时间窗
        // L2锁：单个设备报同一个错，强行静默 4 小时(14400秒)，防止硬件损坏引发雪崩
        long long l2_lock_duration = 14400; 
        
        // L4锁：楼栋级打包窗。P2降至60秒仅吸收爆发并发，之后立刻放行
        long long l4_lock_duration = is_p0 ? 7200 : (is_p1 ? 1800 : 60); 
        
        std::string new_batch_id = "PKG-" + building + "-" + channel + "-" + std::to_string(ts);
        
        // 分别使用解耦后的时长上锁
        active_locks[state_key] = ts + l2_lock_duration;
        spatial_locks[spatial_key] = {ts + l4_lock_duration, new_batch_id};

        return "NEW_DISPATCH: " + new_batch_id;
    }

public:
    ConvergenceEngine() {}

    py::dict push_event(py::dict ev, float conf_threshold) {
        std::string action = process_single(ev, conf_threshold);
        py::dict res;
        res["action"] = action;
        return res;
    }

    py::dict process_stream(const std::vector<py::dict>& events, float conf_threshold) {
        long long l1 = 0, l2 = 0, l3 = 0, l4 = 0, disp = 0;
        
        for (const auto& ev : events) {
            std::string act = process_single(ev, conf_threshold);
            if (act == "L1_DROP") l1++;
            else if (act == "L2_SUPPRESS") l2++;
            else if (act == "L3_POOL") l3++;
            else if (act.find("L4_BATCHED") != std::string::npos) l4++;
            else if (act.find("NEW_DISPATCH") != std::string::npos) disp++;
        }
        
        py::dict res;
        res["total"] = (long long)events.size();
        res["l1_dropped"] = l1; 
        res["l2_suppressed"] = l2; 
        res["l3_pooled"] = l3; 
        res["l4_spatial_batched"] = l4; 
        res["dispatched"] = disp;
        return res;
    }
};

PYBIND11_MODULE(smart_scheduler, m) {
    m.doc() = "Smart Campus Dispatch Engine Core (Decoupled L2 & L4 version)";
    py::class_<ConvergenceEngine>(m, "ConvergenceEngine")
        .def(py::init<>())
        .def("push_event", &ConvergenceEngine::push_event)
        .def("process_stream", &ConvergenceEngine::process_stream);
}