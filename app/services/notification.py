"""
通知预警模块
现代海龟协议 - 信号通知系统
"""

import asyncio
import aiosmtplib
from typing import List, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import httpx

from app.core.config import settings
from app.database.models import NotificationLog, SignalType as DBSignalType
from app.schemas.trading import SignalType
from sqlalchemy.orm import Session


class NotificationService:
    """
    通知服务
    
    功能:
    - 仅对BUY/SELL信号发送通知
    - 自动屏蔽HOLD信号
    - 支持SMTP邮件和Webhook
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.enabled = settings.NOTIFICATION_ENABLED
    
    async def send_signal_notification(
        self,
        ticker: str,
        signal: SignalType,
        signal_reason: str,
        current_price: float,
        n_value: float,
        recommended_units: float,
        position_size: float,
        analysis_id: int
    ) -> bool:
        """
        发送信号通知
        
        只对BUY/SELL信号发送通知，HOLD信号自动屏蔽
        修复: 为每种通知渠道分别创建独立的审计日志
        """
        # HOLD信号不发送通知
        if signal == SignalType.HOLD:
            return True
        
        # 构建通用消息
        message = self._build_message(
            ticker, signal, signal_reason, 
            current_price, n_value, 
            recommended_units, position_size
        )
        
        # 记录每种通知渠道的发送结果
        notification_logs = []
        email_success = False
        webhook_success = False
        
        try:
            # 1. 发送邮件通知
            if settings.SMTP_HOST and settings.SMTP_TO:
                email_log = NotificationLog(
                    analysis_id=analysis_id,
                    notification_type="EMAIL",
                    signal=DBSignalType(signal.value),
                    message=message
                )
                try:
                    await self._send_email(
                        ticker=ticker,
                        signal=signal,
                        current_price=current_price,
                        n_value=n_value,
                        recommended_units=recommended_units,
                        position_size=position_size,
                        signal_reason=signal_reason
                    )
                    email_log.status = "SENT"
                    email_log.sent_at = datetime.now()
                    email_success = True
                except Exception as e:
                    email_log.status = "FAILED"
                    email_log.error_message = str(e)
                    print(f"[NOTIFICATION] Email发送失败: {e}")
                notification_logs.append(email_log)
            
            # 2. 发送Webhook通知
            if settings.WEBHOOK_URL:
                webhook_log = NotificationLog(
                    analysis_id=analysis_id,
                    notification_type="WEBHOOK",
                    signal=DBSignalType(signal.value),
                    message=message
                )
                try:
                    await self._send_webhook(
                        ticker=ticker,
                        signal=signal,
                        current_price=current_price,
                        n_value=n_value,
                        recommended_units=recommended_units,
                        position_size=position_size
                    )
                    webhook_log.status = "SENT"
                    webhook_log.sent_at = datetime.now()
                    webhook_success = True
                except Exception as e:
                    webhook_log.status = "FAILED"
                    webhook_log.error_message = str(e)
                    print(f"[NOTIFICATION] Webhook发送失败: {e}")
                notification_logs.append(webhook_log)
            
            # 批量保存日志
            for log in notification_logs:
                self.db.add(log)
            self.db.commit()
            
            return email_success or webhook_success
            
        except Exception as e:
            for log in notification_logs:
                if log.status != "SENT":
                    log.status = "FAILED"
                    log.error_message = str(e)
                    self.db.add(log)
            self.db.commit()
            return False
    
    async def _send_email(
        self,
        ticker: str,
        signal: SignalType,
        current_price: float,
        n_value: float,
        recommended_units: float,
        position_size: float,
        signal_reason: str
    ) -> bool:
        """发送邮件通知"""
        if not all([settings.SMTP_HOST, settings.SMTP_USER, settings.SMTP_PASSWORD, settings.SMTP_TO]):
            return False
        
        # 构建邮件内容
        subject = f"【{signal.value}信号】{ticker} - ${current_price:.2f}"
        
        html_content = self._build_html_email(
            ticker=ticker,
            signal=signal,
            current_price=current_price,
            n_value=n_value,
            recommended_units=recommended_units,
            position_size=position_size,
            signal_reason=signal_reason
        )
        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = settings.SMTP_FROM or settings.SMTP_USER
        message["To"] = ", ".join(settings.SMTP_TO)
        
        # 添加HTML内容
        html_part = MIMEText(html_content, "html")
        message.attach(html_part)
        
        # 发送邮件
        try:
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER,
                password=settings.SMTP_PASSWORD,
                start_tls=True
            )
            return True
        except Exception as e:
            print(f"邮件发送失败: {e}")
            return False
    
    async def _send_webhook(
        self,
        ticker: str,
        signal: SignalType,
        current_price: float,
        n_value: float,
        recommended_units: float,
        position_size: float
    ) -> bool:
        """发送Webhook通知"""
        payload = {
            "event": "trading_signal",
            "ticker": ticker,
            "signal": signal.value,
            "current_price": current_price,
            "n_value": n_value,
            "recommended_units": recommended_units,
            "position_size": position_size,
            "timestamp": datetime.now().isoformat()
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    settings.WEBHOOK_URL,
                    json=payload,
                    timeout=10
                )
                return response.status_code == 200
        except Exception as e:
            print(f"Webhook发送失败: {e}")
            return False
    
    def _build_message(
        self,
        ticker: str,
        signal: SignalType,
        signal_reason: str,
        current_price: float,
        n_value: float,
        recommended_units: float,
        position_size: float
    ) -> str:
        """构建通知消息"""
        signal_emoji = "📈" if signal == SignalType.BUY else "📉"
        
        return f"""
{signal_emoji} {signal.value} 信号通知

资产: {ticker}
价格: ${current_price:.2f}
信号: {signal.value}
原因: {signal_reason}

波动率指标:
- N值: ${n_value:.2f}

头寸建议:
- 建议单位: {recommended_units:.2f}
- 建议股数: {position_size:.0f}

时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    def _build_html_email(
        self,
        ticker: str,
        signal: SignalType,
        current_price: float,
        n_value: float,
        recommended_units: float,
        position_size: float,
        signal_reason: str
    ) -> str:
        """构建HTML邮件模板"""
        bg_color = "#e8f5e9" if signal == SignalType.BUY else "#ffebee"
        signal_color = "#2e7d32" if signal == SignalType.BUY else "#c62828"
        
        template = Template("""
<!DOCTYPE html>
<html>
<head>
    <style>
        {% raw %}
        body { font-family: Arial, sans-serif; background-color: #f5f5f5; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .card { background-color: white; border-radius: 8px; padding: 30px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .header { background-color: """ + bg_color + """; padding: 20px; border-radius: 8px 8px 0 0; text-align: center; }
        .signal { font-size: 32px; font-weight: bold; color: """ + signal_color + """; margin: 10px 0; }
        .price { font-size: 24px; color: #333; }
        .content { padding: 20px; }
        .metric { display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; }
        .label { color: #666; }
        .value { font-weight: bold; color: #333; }
        .footer { text-align: center; padding: 20px; color: #999; font-size: 12px; }
        {% endraw %}
    </style>
</head>
<body>
    <div class="container">
        <div class="card">
            <div class="header">
                <div class="ticker">{{ ticker }}</div>
                <div class="signal">{{ signal.value }}</div>
                <div class="price">${{ "%.2f"|format(current_price) }}</div>
            </div>
            <div class="content">
                <p><strong>信号原因:</strong> {{ signal_reason }}</p>
                
                <h3>波动率指标</h3>
                <div class="metric">
                    <span class="label">N值 (ATR)</span>
                    <span class="value">${{ "%.2f"|format(n_value) }}</span>
                </div>
                
                <h3>头寸建议</h3>
                <div class="metric">
                    <span class="label">建议单位</span>
                    <span class="value">{{ "%.2f"|format(recommended_units) }}</span>
                </div>
                <div class="metric">
                    <span class="label">建议股数</span>
                    <span class="value">{{ "%.0f"|format(position_size) }}</span>
                </div>
            </div>
            <div class="footer">
                现代海龟协议量化交易系统<br>
                {{ timestamp }}
            </div>
        </div>
    </div>
</body>
</html>
        """)
        
        return template.render(
            ticker=ticker,
            signal=signal,
            current_price=current_price,
            n_value=n_value,
            recommended_units=recommended_units,
            position_size=position_size,
            signal_reason=signal_reason,
            bg_color=bg_color,
            signal_color=signal_color,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        )
