import { useState } from 'react'

export default function App() {
  // 1. 定义页面的数据状态 (类似 Python 的全局变量，但修改它们会自动刷新 UI)
  const [metrics, setMetrics] = useState({ total: 33751, suppressed: 21456, dispatched: 12295, p0: 3 })
  const [alerts, setAlerts] = useState([
    { id: 1, time: '10:05:12', source: '烟感传感器', event: 'smoke_detected', loc: 'B1栋 负一楼', color: 'text-red-400' },
    { id: 2, time: '10:05:08', source: '视觉AI', event: 'ev_illegal_parking', loc: 'A3栋 门口', color: 'text-yellow-400' },
    { id: 3, time: '10:04:55', source: '门禁系统', event: 'door_offline', loc: 'C2栋 3楼', color: 'text-gray-400' },
  ])
  const [tickets, setTickets] = useState([
    { id: 'PKG-B1-P0-1005', priority: 'P0', loc: 'B1栋 负一楼', desc: '消防烟感触发，疑似火灾', agent: '张强 (保安)', time: '04:12' },
    { id: 'PKG-A3-P2-1002', priority: 'P2', loc: 'A3栋 门口', desc: '电动车违停清理', agent: 'Robot-B1 (机器人)', time: '12:45' },
  ])
  const [agents, setAgents] = useState([
    { name: '张强', role: '保安', status: '处理 P0 中', color: 'bg-red-500' },
    { name: '李师傅', role: '维修', status: '空闲 (Idle)', color: 'bg-green-500' },
    { name: 'Robot-B1', role: '保洁机器人', status: '执行 L3 巡检', color: 'bg-blue-500' },
    { name: '王大姐', role: '保洁', status: '空闲 (Idle)', color: 'bg-green-500' },
  ])

  // 模拟产生新告警的动作
  const simulateAlert = () => {
    setMetrics(prev => ({ ...prev, total: prev.total + 1, suppressed: prev.suppressed + 1 }))
    const newAlert = { id: Date.now(), time: new Date().toLocaleTimeString(), source: '温湿度传感器', event: 'flapping_signal', loc: '机房', color: 'text-gray-500' }
    setAlerts(prev => [newAlert, ...prev].slice(0, 8)) // 只保留最近8条
  }

  return (
    <div className="min-h-screen p-6 flex flex-col gap-6">
      {/* 头部：标题与核心指标 */}
      <header className="flex justify-between items-center border-b border-gray-700 pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-wider text-blue-400">星汇智慧园区</h1>
          <p className="text-gray-400 mt-1">数字孪生智能调度指挥舱 (Digital Twin Dashboard)</p>
        </div>
        <div className="flex gap-4">
          <MetricCard title="总接入告警" value={metrics.total} color="text-white" />
          <MetricCard title="L1-L3 漏斗拦截" value={metrics.suppressed} color="text-green-400" />
          <MetricCard title="实际生成工单" value={metrics.dispatched} color="text-blue-400" />
          <MetricCard title="P0 极危并发" value={metrics.p0} color="text-red-500" />
        </div>
      </header>

      {/* 动作区 */}
      <div className="flex gap-4">
        <button onClick={simulateAlert} className="bg-blue-600 hover:bg-blue-500 px-4 py-2 rounded font-bold transition">
          ⚡ 模拟接收传感器震荡 (L2 防抖)
        </button>
      </div>

      {/* 主体：三列品字型布局 */}
      <main className="grid grid-cols-12 gap-6 flex-1">
        
        {/* 左侧：原始告警瀑布流 */}
        <section className="col-span-3 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-xl font-bold border-b border-gray-700 pb-2 mb-4">📥 实时多源告警流</h2>
          <div className="flex flex-col gap-3">
            {alerts.map(a => (
              <div key={a.id} className="bg-gray-900 p-3 rounded text-sm border-l-4 border-gray-600">
                <div className="flex justify-between text-gray-400 mb-1">
                  <span>{a.time} | {a.source}</span>
                </div>
                <div className={`${a.color} font-mono font-bold`}>{a.event}</div>
                <div className="text-gray-300 mt-1">📍 {a.loc}</div>
              </div>
            ))}
          </div>
        </section>

        {/* 中间：核心调度沙盘 */}
        <section className="col-span-6 bg-gray-800 rounded-lg p-4 border border-gray-700 shadow-xl shadow-blue-900/20">
          <h2 className="text-xl font-bold border-b border-gray-700 pb-2 mb-4">🧠 核心约束派单队列 (SLA Tracking)</h2>
          <div className="flex flex-col gap-4">
            {tickets.map(t => (
              <div key={t.id} className="bg-gray-900 rounded p-4 border border-gray-700 relative overflow-hidden">
                {/* 紧急程度高亮条 */}
                <div className={`absolute top-0 left-0 w-1 h-full ${t.priority === 'P0' ? 'bg-red-500' : 'bg-blue-500'}`}></div>
                
                <div className="flex justify-between items-start ml-3">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className={`px-2 py-0.5 rounded text-xs font-bold ${t.priority === 'P0' ? 'bg-red-900 text-red-300' : 'bg-blue-900 text-blue-300'}`}>
                        {t.priority}
                      </span>
                      <span className="font-mono text-gray-400 text-sm">{t.id}</span>
                    </div>
                    <h3 className="font-bold text-lg">{t.desc}</h3>
                    <p className="text-gray-400 text-sm mt-1">📍 {t.loc}</p>
                  </div>
                  
                  {/* SLA 倒计时与执行人 */}
                  <div className="text-right">
                    <div className="text-2xl font-mono font-bold text-yellow-500 mb-1">{t.time}</div>
                    <div className="text-sm bg-gray-700 px-3 py-1 rounded-full text-gray-300">
                      🏃 {t.agent}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* 右侧：运力资源矩阵 */}
        <section className="col-span-3 bg-gray-800 rounded-lg p-4 border border-gray-700">
          <h2 className="text-xl font-bold border-b border-gray-700 pb-2 mb-4">👷 运力资源矩阵</h2>
          <div className="flex flex-col gap-3">
            {agents.map((ag, idx) => (
              <div key={idx} className="flex items-center justify-between bg-gray-900 p-3 rounded border border-gray-700">
                <div className="flex items-center gap-3">
                  {/* 状态指示灯 */}
                  <div className={`w-3 h-3 rounded-full ${ag.color} shadow-[0_0_8px_currentColor]`}></div>
                  <div>
                    <div className="font-bold">{ag.name}</div>
                    <div className="text-xs text-gray-400">{ag.role}</div>
                  </div>
                </div>
                <div className="text-sm text-gray-300">{ag.status}</div>
              </div>
            ))}
          </div>
        </section>

      </main>
    </div>
  )
}

// 顶部数字卡片组件
function MetricCard({ title, value, color }) {
  return (
    <div className="bg-gray-800 border border-gray-700 px-6 py-3 rounded-lg text-center min-w-[150px]">
      <div className="text-gray-400 text-sm mb-1">{title}</div>
      <div className={`text-3xl font-bold font-mono ${color}`}>{value}</div>
    </div>
  )
}