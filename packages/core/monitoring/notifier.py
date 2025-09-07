import asyncio
import json
from typing import Dict, List, Optional
from datetime import datetime
import aiohttp
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
import os

from .monitor import Alert, AlertSeverity

class NotificationChannel:
    """Base notification channel"""
    async def send(self, alert: Alert):
        raise NotImplementedError

class WebhookChannel(NotificationChannel):
    """Send alerts via webhook (Discord, Slack, etc.)"""
    
    def __init__(self, webhook_url: str, channel_type: str = "discord"):
        self.webhook_url = webhook_url
        self.channel_type = channel_type
    
    async def send(self, alert: Alert):
        """Send alert to webhook"""
        if self.channel_type == "discord":
            payload = self._format_discord(alert)
        elif self.channel_type == "slack":
            payload = self._format_slack(alert)
        else:
            payload = {"text": f"{alert.title}: {alert.message}"}
        
        async with aiohttp.ClientSession() as session:
            async with session.post(self.webhook_url, json=payload) as response:
                if response.status != 200:
                    print(f"Failed to send webhook: {response.status}")
    
    def _format_discord(self, alert: Alert) -> Dict:
        """Format alert for Discord"""
        color = {
            AlertSeverity.INFO: 0x00FF00,
            AlertSeverity.WARNING: 0xFFFF00,
            AlertSeverity.ERROR: 0xFF9900,
            AlertSeverity.CRITICAL: 0xFF0000
        }.get(alert.severity, 0x808080)
        
        return {
            "embeds": [{
                "title": f"{alert.severity.value.upper()}: {alert.title}",
                "description": alert.message,
                "color": color,
                "timestamp": alert.timestamp.isoformat(),
                "fields": [
                    {"name": "Source", "value": alert.source, "inline": True},
                    {"name": "Time", "value": alert.timestamp.strftime("%H:%M:%S"), "inline": True}
                ]
            }]
        }
    
    def _format_slack(self, alert: Alert) -> Dict:
        """Format alert for Slack"""
        emoji = {
            AlertSeverity.INFO: ":information_source:",
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.ERROR: ":x:",
            AlertSeverity.CRITICAL: ":rotating_light:"
        }.get(alert.severity, ":bell:")
        
        return {
            "text": f"{emoji} *{alert.title}*\n{alert.message}\n_Source: {alert.source}_"
        }

class EmailChannel(NotificationChannel):
    """Send alerts via email"""
    
    def __init__(self, smtp_host: str, smtp_port: int, username: str, password: str, 
                 from_email: str, to_emails: List[str]):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    async def send(self, alert: Alert):
        """Send alert via email"""
        msg = MIMEMultipart()
        msg['From'] = self.from_email
        msg['To'] = ', '.join(self.to_emails)
        msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
        
        body = f"""
        Alert: {alert.title}
        Severity: {alert.severity.value.upper()}
        Source: {alert.source}
        Time: {alert.timestamp}
        
        Message:
        {alert.message}
        
        Metadata:
        {json.dumps(alert.metadata, indent=2) if alert.metadata else "None"}
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        try:
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
        except Exception as e:
            print(f"Failed to send email: {e}")

class SMSChannel(NotificationChannel):
    """Send alerts via SMS (using Twilio)"""
    
    def __init__(self, account_sid: str, auth_token: str, from_number: str, to_numbers: List[str]):
        self.account_sid = account_sid
        self.auth_token = auth_token
        self.from_number = from_number
        self.to_numbers = to_numbers
        self.api_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
    
    async def send(self, alert: Alert):
        """Send alert via SMS"""
        # Only send SMS for critical alerts
        if alert.severity != AlertSeverity.CRITICAL:
            return
        
        message = f"{alert.severity.value.upper()}: {alert.title}\n{alert.message[:100]}"
        
        auth = aiohttp.BasicAuth(self.account_sid, self.auth_token)
        
        async with aiohttp.ClientSession(auth=auth) as session:
            for to_number in self.to_numbers:
                data = {
                    'From': self.from_number,
                    'To': to_number,
                    'Body': message
                }
                async with session.post(self.api_url, data=data) as response:
                    if response.status != 201:
                        print(f"Failed to send SMS to {to_number}: {response.status}")

class AlertNotifier:
    """Manages alert notifications across multiple channels"""
    
    def __init__(self):
        self.channels: List[NotificationChannel] = []
        self.severity_filters = {}
    
    def add_channel(self, channel: NotificationChannel, min_severity: AlertSeverity = AlertSeverity.INFO):
        """Add a notification channel with optional severity filter"""
        self.channels.append(channel)
        self.severity_filters[channel] = min_severity
    
    async def notify(self, alert: Alert):
        """Send alert to all appropriate channels"""
        tasks = []
        
        for channel in self.channels:
            min_severity = self.severity_filters.get(channel, AlertSeverity.INFO)
            
            # Check if alert severity meets channel requirements
            severity_order = [AlertSeverity.INFO, AlertSeverity.WARNING, 
                            AlertSeverity.ERROR, AlertSeverity.CRITICAL]
            
            if severity_order.index(alert.severity) >= severity_order.index(min_severity):
                tasks.append(channel.send(alert))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)