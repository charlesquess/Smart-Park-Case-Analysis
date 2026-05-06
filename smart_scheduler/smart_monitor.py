import sys
import pandas as pd
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, 
    QHBoxLayout, QTableWidget, QTableWidgetItem, 
    QLabel, QHeaderView, QFrame, QPushButton, QSlider, QProgressBar
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QColor, QFont

import smart_scheduler

class SimulationThread(QThread):
    """
    仿真线程：支持动态调速、暂停、恢复与优雅退出
    """
    event_out = pyqtSignal(dict, dict)  
    stats_out = pyqtSignal(dict)
    progress_out = pyqtSignal(int) # 新增：进度条信号

    def __init__(self, df: pd.DataFrame, speed_ms: int = 100):
        super().__init__()
        self.df = df
        self.total_rows = len(df)
        self.speed_ms = speed_ms
        self.engine = smart_scheduler.ConvergenceEngine()
        self.stats = {
            "total": 0, "dispatched": 0, "batched": 0, 
            "pooled": 0, "filtered": 0
        }
        self._run_flag = True
        self._is_paused = False

    def stop(self):
        self._run_flag = False

    def pause(self):
        self._is_paused = True

    def resume(self):
        self._is_paused = False

    def set_speed(self, ms: int):
        self.speed_ms = ms

    def run(self):
        for idx, row in self.df.iterrows():
            if not self._run_flag:
                break
            
            # 暂停态自旋等待
            while self._is_paused:
                if not self._run_flag: return
                self.msleep(50)
            
            ev = row.to_dict()
            res = self.engine.push_event(ev, 0.75)
            action = res["action"]
            
            self.stats["total"] += 1
            if "NEW_DISPATCH" in action: self.stats["dispatched"] += 1
            elif "BATCHED" in action: self.stats["batched"] += 1
            elif "POOL" in action: self.stats["pooled"] += 1
            else: self.stats["filtered"] += 1
                
            self.event_out.emit(ev, res)
            self.stats_out.emit(self.stats)
            
            # 发送进度百分比
            progress_percent = int((self.stats["total"] / self.total_rows) * 100)
            self.progress_out.emit(progress_percent)
            
            self.msleep(self.speed_ms)

class CampusMonitor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("星汇智慧园区 - 实时智能调度指挥中心 (高可用重构版)")
        self.resize(1200, 850)
        self.setStyleSheet("background-color: #f4f7f6;")

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 1. 顶部仪表盘
        self.setup_dashboard(main_layout)
        
        # 2. 播控台 (新增进度条)
        self.setup_controls(main_layout)

        # 3. 中部实时监控表
        self.setup_table(main_layout)

        # 加载数据并启动
        self.load_and_start()

    def setup_dashboard(self, layout):
        dash_frame = QFrame()
        dash_frame.setStyleSheet("background-color: white; border-radius: 10px; border: 1px solid #ddd;")
        dash_layout = QHBoxLayout(dash_frame)
        
        self.stat_labels = {}
        metrics = [
            ("总接入告警", "total", "#2c3e50"),
            ("独立强派单", "dispatched", "#e74c3c"),
            ("空间内打包", "batched", "#3498db"),
            ("计划性池化", "pooled", "#16a085"),
            ("系统收敛率", "ratio", "#8e44ad") # 更新语义
        ]
        
        for name, key, color in metrics:
            box = QVBoxLayout()
            title = QLabel(name)
            title.setStyleSheet(f"color: {color}; font-weight: bold; border: none; font-size: 14px;")
            val = QLabel("0")
            val.setStyleSheet(f"font-size: 28px; color: {color}; font-weight: bold; border: none;")
            box.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)
            box.addWidget(val, alignment=Qt.AlignmentFlag.AlignCenter)
            self.stat_labels[key] = val
            dash_layout.addLayout(box)
        
        layout.addWidget(dash_frame)

    def setup_controls(self, layout):
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(5, 5, 5, 5)

        self.btn_pause = QPushButton("暂停仿真")
        self.btn_pause.setFixedSize(120, 35)
        self.btn_pause.setStyleSheet("background-color: #f39c12; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_pause.clicked.connect(self.pause_sim)

        self.btn_resume = QPushButton("继续仿真")
        self.btn_resume.setFixedSize(120, 35)
        self.btn_resume.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; border-radius: 5px;")
        self.btn_resume.clicked.connect(self.resume_sim)
        self.btn_resume.setEnabled(False)

        speed_label = QLabel("仿真速度:")
        speed_label.setStyleSheet("font-weight: bold; color: #7f8c8d;")
        
        self.speed_slider = QSlider(Qt.Orientation.Horizontal)
        self.speed_slider.setRange(1, 300)
        self.speed_slider.setValue(10) # 默认速度调快，方便演示
        self.speed_slider.setInvertedAppearance(True)
        self.speed_slider.setFixedWidth(150)
        self.speed_slider.valueChanged.connect(self.change_speed)
        
        # 新增：进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("处理进度: %p%")
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #bbb; border-radius: 5px; text-align: center; font-weight: bold; }
            QProgressBar::chunk { background-color: #3498db; width: 20px; }
        """)

        control_layout.addWidget(self.btn_pause)
        control_layout.addWidget(self.btn_resume)
        control_layout.addWidget(speed_label)
        control_layout.addWidget(self.speed_slider)
        control_layout.addSpacing(20)
        control_layout.addWidget(self.progress_bar)

        layout.addWidget(control_frame)

    def setup_table(self, layout):
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["时间戳", "触发位置", "设备与事件类型", "引擎调度决策", "归属工单包 (Batch ID)"])
        self.table.setStyleSheet("background-color: white; gridline-color: #eee; font-size: 13px;")
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.table)

    def load_and_start(self):
        try:
            df = pd.read_csv("alerts_7days.csv")
            # 与 poc_main.py 保持绝对一致的数据预处理
            df['timestamp_str'] = df['timestamp']
            df['timestamp'] = pd.to_datetime(df['timestamp']).astype('int64') // 10**9
            df['building'] = df['building'].fillna("Unknown")
            df['floor'] = df['floor'].fillna("-")
            df['confidence'] = df['confidence'].fillna(-1.0)
            
            self.thread = SimulationThread(df, speed_ms=10) # 默认极速模式 10ms
            self.thread.event_out.connect(self.update_row)
            self.thread.stats_out.connect(self.update_stats)
            self.thread.progress_out.connect(self.update_progress) # 连接进度条
            self.thread.start()
        except Exception as e:
            print(f"数据加载失败: {e}")

    def pause_sim(self):
        self.thread.pause()
        self.btn_pause.setEnabled(False)
        self.btn_resume.setEnabled(True)
        self.setStyleSheet("background-color: #ffeaa7;")

    def resume_sim(self):
        self.thread.resume()
        self.btn_pause.setEnabled(True)
        self.btn_resume.setEnabled(False)
        self.setStyleSheet("background-color: #f4f7f6;")

    def change_speed(self):
        self.thread.set_speed(self.speed_slider.value())

    def update_progress(self, percent):
        self.progress_bar.setValue(percent)

    def update_row(self, ev, res):
        row_idx = self.table.rowCount()
        self.table.insertRow(row_idx)
        
        self.table.setItem(row_idx, 0, QTableWidgetItem(ev['timestamp_str']))
        self.table.setItem(row_idx, 1, QTableWidgetItem(f"{ev['building']}栋 {ev['floor']}层"))
        self.table.setItem(row_idx, 2, QTableWidgetItem(f"{ev['device_type']}: {ev['alert_type']}"))
        
        action_str = res["action"]
        batch_id = "-"
        
        decision_item = QTableWidgetItem()
        id_item = QTableWidgetItem()

        # 用 replace 实现防御性解析
        if "NEW_DISPATCH" in action_str:
            batch_id = action_str.replace("NEW_DISPATCH: ", "")
            decision_item.setText("强打断发起新派单")
            decision_item.setForeground(QColor("#e74c3c"))
            decision_item.setFont(QFont("Microsoft YaHei", 10, QFont.Weight.Bold))
            id_item.setText(batch_id)
            id_item.setFont(QFont("Consolas", 10, QFont.Weight.Bold))
        
        elif "L4_BATCHED" in action_str:
            batch_id = action_str.replace("L4_BATCHED into ", "")
            decision_item.setText("同空间顺路打包")
            decision_item.setForeground(QColor("#3498db"))
            id_item.setText(batch_id)
            id_item.setForeground(QColor("#3498db"))
        
        elif "L3_POOL" in action_str:
            decision_item.setText("压入巡检池(不派单)")
            decision_item.setForeground(QColor("#16a085"))
        
        else:
            decision_item.setText("置信度/震荡静默")
            decision_item.setForeground(QColor("#bdc3c7"))

        self.table.setItem(row_idx, 3, decision_item)
        self.table.setItem(row_idx, 4, id_item)
        
        self.table.scrollToBottom()
        # 控制驻留行数，防止内存爆炸卡死界面
        if row_idx > 150: self.table.removeRow(0)

    def update_stats(self, stats):
        self.stat_labels["total"].setText(f"{stats['total']:,}")
        self.stat_labels["dispatched"].setText(f"{stats['dispatched']:,}")
        self.stat_labels["batched"].setText(f"{stats['batched']:,}")
        self.stat_labels["pooled"].setText(f"{stats['pooled']:,}")
        
        ratio = (1 - stats['dispatched'] / max(stats['total'], 1)) * 100
        self.stat_labels["ratio"].setText(f"{ratio:.1f}%")

    # 关闭事件，实现线程的优雅安全退出
    def closeEvent(self, event):
        if hasattr(self, 'thread') and self.thread.isRunning():
            self.thread.stop()
            self.thread.wait() # 阻塞主线程，直到子线程安全退出 C++ 状态机
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CampusMonitor()
    window.show()
    sys.exit(app.exec())