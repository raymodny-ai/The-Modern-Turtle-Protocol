import Link from 'next/link'

export default function Home() {
  return (
    <div className="max-w-6xl mx-auto">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-turtle-700 to-turtle-900 rounded-2xl p-8 mb-8 text-white">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-4xl font-bold mb-4">
              🐢 现代海龟协议
            </h1>
            <p className="text-xl text-turtle-100 mb-6">
              基于波动率的量化交易风险管理系统
            </p>
            <div className="flex space-x-4">
              <Link
                href="/analyze"
                className="bg-white text-turtle-800 px-6 py-3 rounded-lg font-semibold hover:bg-turtle-100 transition-colors"
              >
                开始分析 →
              </Link>
              <Link
                href="/history"
                className="border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white/10 transition-colors"
              >
                查看历史
              </Link>
            </div>
          </div>
          <div className="hidden md:block text-8xl opacity-20">
            🐢
          </div>
        </div>
      </div>

      {/* 核心功能 */}
      <div className="grid md:grid-cols-3 gap-6 mb-8">
        <FeatureCard
          icon="📈"
          title="趋势跟踪信号"
          description="基于20日/10日价格通道的趋势突破识别，自动生成BUY/SELL/HOLD交易信号"
        />
        <FeatureCard
          icon="💰"
          title="动态头寸管理"
          description="根据账户净资产和资产波动率(N值)动态计算最优头寸规模，严格控制单笔1%风险"
        />
        <FeatureCard
          icon="🛡️"
          title="四重风险控制"
          description="单一市场、高关联市场、弱关联市场、单向总敞口四层熔断机制保护资金安全"
        />
      </div>

      {/* 海龟协议参数 */}
      <div className="bg-white rounded-xl shadow-md p-6 mb-8">
        <h2 className="text-2xl font-bold mb-4 text-gray-800">📋 海龟协议核心参数</h2>
        <div className="grid md:grid-cols-4 gap-4">
          <ParameterCard
            label="入场周期"
            value="20日"
            description="突破20日最高价入场"
          />
          <ParameterCard
            label="出场周期"
            value="10日"
            description="跌破10日最低价出场"
          />
          <ParameterCard
            label="风险敞口"
            value="1%"
            description="单笔交易最大亏损"
          />
          <ParameterCard
            label="N值周期"
            value="20日"
            description="ATR真实波幅计算"
          />
        </div>
      </div>

      {/* 快速链接 */}
      <div className="grid md:grid-cols-2 gap-6">
        <QuickLink
          title="📊 策略分析"
          description="输入股票代码，获取实时交易信号和头寸建议"
          href="/analyze"
        />
        <QuickLink
          title="📜 历史记录"
          description="查看历史分析记录和信号统计"
          href="/history"
        />
      </div>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: string; title: string; description: string }) {
  return (
    <div className="bg-white rounded-xl shadow-md p-6 card-hover">
      <div className="text-4xl mb-4">{icon}</div>
      <h3 className="text-xl font-semibold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function ParameterCard({ label, value, description }: { label: string; value: string; description: string }) {
  return (
    <div className="bg-turtle-50 rounded-lg p-4 border border-turtle-200">
      <div className="text-sm text-turtle-600 mb-1">{label}</div>
      <div className="text-2xl font-bold text-turtle-800">{value}</div>
      <div className="text-xs text-turtle-500 mt-1">{description}</div>
    </div>
  )
}

function QuickLink({ title, description, href }: { title: string; description: string; href: string }) {
  return (
    <Link
      href={href}
      className="block bg-white rounded-xl shadow-md p-6 card-hover border-2 border-transparent hover:border-turtle-500"
    >
      <h3 className="text-xl font-semibold mb-2 text-gray-800">{title}</h3>
      <p className="text-gray-600">{description}</p>
    </Link>
  )
}
