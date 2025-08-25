#!/usr/bin/env python3
"""
Show exact Railway environment variables needed
"""

print("🚀 RAILWAY ENVIRONMENT VARIABLES NEEDED")
print("="*60)
print("Go to Railway dashboard → Your project → Variables tab")
print("Add these EXACT variables:")
print("="*60)

vars_needed = {
    'EMAIL_ADDRESS': 'papykabukanyi@gmail.com',
    'EMAIL_PASSWORD': 'cksxfqaymfdkkfis',
    'EMAIL_RECIPIENTS': 'papykabukanyi@gmail.com,hoopstar385@gmail.com',
    'SMTP_SERVER': 'smtp.gmail.com',
    'SMTP_PORT': '587',
    'PROFIT_THRESHOLD': '50',
    'CHECK_INTERVAL': '300',
    'STOCKX_API_KEY': '54Ae6PJ6sQ1Bn9dinWl3FaHIsHlNlMqQ4vt1tvB6',
    'STOCKX_CLIENT_ID': '3VYAJs2pNikwozDG9WM1EAis87LkkZY6',
    'STOCKX_CLIENT_SECRET': 'TRppZPRMfrTxCZ21baEZ0M3EVg2MufvxELMoENlH5lVGvtDLGUsBZ88ZYF14_HEj',
    'STOCKX_COOKIE': '_px3=31ab0e98ac9a6a9c83aa54dd4f3c1af81ec12022e6c7ba51c8ebe29ab41adebb:0YvX/kfn9FGn44SVFZoIc9x4+E+d2YOEVnwEp9A9lRoMBcD3S/FQ9i5YrX+lSW4sBB0fGUKtBOFB7ioJ9vClMA==:1000:QyM+W0i9yjHwlJw+Wy6UPFVvNIo8zAKJYiKrB/p2s8FZNk5M7xjdGW9IEoQUv1yaBXzJU4v1wZGa9OXObOZ0HNSNBs0xctXsaWGcuHYQ8AJwpnC05E92l1FZ8usDLrIJJZKvQZ44Reo59o7EK9WqRr8MYC2jbE5CQCVFMVNV+Zo='
}

for name, value in vars_needed.items():
    print(f"{name}={value}")

print("="*60)
print("After adding all variables, redeploy the service!")
print("The bot will then work properly! 🚀")
