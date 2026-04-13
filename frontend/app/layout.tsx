import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: '现代海龟协议 - 量化交易系统',
  description: '基于Python与微服务架构的自动化量化交易系统',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-gray-50">
        <div className="flex flex-col min-h-screen">
          {/* 顶部导航 */}
          <header className="bg-turtle-800 text-white shadow-lg">
            <div className="container mx-auto px-4 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <span className="text-3xl">🐢</span>
                  <div>
                    <h1 className="text-xl font-bold">现代海龟协议</h1>
                    <p className="text-xs text-turtle-200">量化交易系统</p>
                  </div>
                </div>
                <nav className="flex items-center space-x-6">
                  <a href="/analyze" className="hover:text-turtle-300 transition-colors">
                    📊 分析
                  </a>
                  <a href="/history" className="hover:text-turtle-300 transition-colors">
                    📜 历史
                  </a>
                  <a href="/positions" className="hover:text-turtle-300 transition-colors">
                    💼 持仓
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* 主内容区 */}
          <main className="flex-1 container mx-auto px-4 py-6">
            {children}
          </main>

          {/* 页脚 */}
          <footer className="bg-gray-800 text-gray-400 py-6 mt-8">
            <div className="container mx-auto px-4 text-center">
              <p className="text-sm">
                现代海龟协议量化交易系统 v1.0.0 | 基于趋势跟踪的风险管理系统
              </p>
              <p className="text-xs mt-2">
                遵循经典海龟交易法则 · 纪律胜于预测
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}
