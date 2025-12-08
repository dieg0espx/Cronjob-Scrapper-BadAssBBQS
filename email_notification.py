#!/usr/bin/env python3
"""
Email notification module for BBQ scraper
Uses Resend API (HTTP-based, works on Railway)
"""

import os
import requests
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

RESEND_API_KEY = os.getenv('RESEND_API_KEY')
EMAIL_FROM = os.getenv('EMAIL_FROM', 'onboarding@resend.dev')  # Use your verified domain
EMAIL_TO = os.getenv('EMAIL_TO', 'tecnodael@gmail.com')


def send_scraping_notification(brands_scraped, stats, success_rate, failed_brands=None):
    """Send email notification after scraping is complete"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping email notification")
        return False

    try:
        day_name = datetime.now().strftime("%A")
        new_count = stats.get('new', 0)
        updated_count = stats.get('updated', 0)
        skipped_count = stats.get('skipped', 0)
        failed_count = stats.get('failed', 0)
        total_count = stats.get('total', 0)

        # Build HTML email
        html_body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .header {{ background-color: #2c3e50; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .summary {{ background-color: #ecf0f1; padding: 15px; border-radius: 5px; margin: 20px 0; }}
                .success {{ color: #27ae60; font-weight: bold; }}
                .stat-grid {{ display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin: 15px 0; }}
                .stat-box {{ background: white; padding: 15px; border-radius: 5px; text-align: center; }}
                .stat-number {{ font-size: 28px; font-weight: bold; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>BBQ Scraper Report</h1>
                <p>{day_name}, {datetime.now().strftime("%B %d, %Y")}</p>
            </div>
            <div class="content">
                <div class="summary">
                    <h2>Summary</h2>
                    <p><strong>Total Products:</strong> {total_count}</p>
                    <p><strong>Brands:</strong> {len(brands_scraped)}</p>
                    <p><strong>Success Rate:</strong> <span class="success">{success_rate:.1f}%</span></p>
                    <div class="stat-grid">
                        <div class="stat-box">
                            <div class="stat-number" style="color: #28a745;">{new_count}</div>
                            <div>New</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" style="color: #ffc107;">{updated_count}</div>
                            <div>Updated</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" style="color: #6c757d;">{skipped_count}</div>
                            <div>Skipped</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number" style="color: #dc3545;">{failed_count}</div>
                            <div>Failed</div>
                        </div>
                    </div>
                </div>
                <h3>Brands Scraped</h3>
                <ul>{"".join(f"<li>{b}</li>" for b in brands_scraped)}</ul>
                {f'<h3 style="color: #e74c3c;">Failed Brands</h3><ul>{"".join(f"<li>{b}</li>" for b in failed_brands)}</ul>' if failed_brands else ''}
            </div>
        </body>
        </html>
        """

        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': EMAIL_FROM,
                'to': [EMAIL_TO],
                'subject': f'BBQ Scraper Report - {datetime.now().strftime("%B %d, %Y")}',
                'html': html_body
            }
        )

        if response.status_code == 200:
            logger.info("Email notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send email: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


def send_error_notification(error_message):
    """Send email notification when scraping fails"""
    if not RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not set, skipping error notification")
        return False

    try:
        html_body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="background-color: #e74c3c; color: white; padding: 20px; text-align: center;">
                <h1>BBQ Scraper Error</h1>
                <p>{datetime.now().strftime("%B %d, %Y at %H:%M UTC")}</p>
            </div>
            <div style="padding: 20px;">
                <div style="background-color: #fee; border-left: 4px solid #e74c3c; padding: 15px;">
                    <h2>Error Details</h2>
                    <p>{error_message}</p>
                </div>
                <p>Check Railway logs for more details.</p>
            </div>
        </body>
        </html>
        """

        response = requests.post(
            'https://api.resend.com/emails',
            headers={
                'Authorization': f'Bearer {RESEND_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'from': EMAIL_FROM,
                'to': [EMAIL_TO],
                'subject': f'BBQ Scraper Error - {datetime.now().strftime("%B %d, %Y")}',
                'html': html_body
            }
        )

        if response.status_code == 200:
            logger.info("Error notification sent successfully")
            return True
        else:
            logger.error(f"Failed to send error email: {response.text}")
            return False

    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")
        return False
