#!/usr/bin/env python3
"""
Email notification module for BBQ scraper
Sends email notifications after scraping is complete
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

# Email configuration from environment variables
EMAIL_FROM = os.getenv('EMAIL_FROM', 'noreplybadassbbqs@gmail.com')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')
EMAIL_TO = os.getenv('EMAIL_TO', 'noreplybadassbbqs@gmail.com')
SMTP_SERVER = 'smtp.gmail.com'
SMTP_PORT = 587


def send_scraping_notification(brands_scraped, total_products, success_rate, failed_brands=None):
    """
    Send email notification after scraping is complete

    Args:
        brands_scraped: List of brand names that were scraped
        total_products: Total number of products scraped
        success_rate: Success rate percentage (0-100)
        failed_brands: List of brands that failed (optional)
    """
    if not EMAIL_PASSWORD:
        logger.warning("EMAIL_PASSWORD not set, skipping email notification")
        return False

    try:
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'BBQ Scraper Report - {datetime.now().strftime("%B %d, %Y")}'
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        # Get day of week
        day_name = datetime.now().strftime("%A")

        # Create HTML body
        html_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                }}
                .summary {{
                    background-color: #ecf0f1;
                    padding: 15px;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .brands {{
                    background-color: #fff;
                    border-left: 4px solid #3498db;
                    padding: 15px;
                    margin: 15px 0;
                }}
                .success {{
                    color: #27ae60;
                    font-weight: bold;
                }}
                .warning {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .footer {{
                    text-align: center;
                    padding: 20px;
                    color: #7f8c8d;
                    font-size: 12px;
                }}
                ul {{
                    list-style-type: none;
                    padding: 0;
                }}
                li {{
                    padding: 5px 0;
                    padding-left: 20px;
                }}
                li:before {{
                    content: "✓ ";
                    color: #27ae60;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🔥 BBQ Scraper Daily Report</h1>
                <p>{day_name}, {datetime.now().strftime("%B %d, %Y")}</p>
            </div>

            <div class="content">
                <div class="summary">
                    <h2>📊 Summary</h2>
                    <p><strong>Total Products Scraped:</strong> {total_products}</p>
                    <p><strong>Brands Processed:</strong> {len(brands_scraped)}</p>
                    <p><strong>Success Rate:</strong> <span class="success">{success_rate:.1f}%</span></p>
                </div>

                <div class="brands">
                    <h2>🏷️ Brands Scraped Today</h2>
                    <ul>
        """

        # Add each brand to the list
        for brand in brands_scraped:
            html_body += f"                        <li>{brand}</li>\n"

        html_body += """
                    </ul>
                </div>
        """

        # Add failed brands section if any
        if failed_brands and len(failed_brands) > 0:
            html_body += """
                <div class="brands" style="border-left-color: #e74c3c;">
                    <h2 class="warning">⚠️ Failed Brands</h2>
                    <ul>
            """
            for brand in failed_brands:
                html_body += f"                        <li style='color: #e74c3c;'>{brand}</li>\n"
            html_body += """
                    </ul>
                </div>
            """

        html_body += f"""
                <div class="summary">
                    <h3>📅 Next Scheduled Run</h3>
                    <p>Tomorrow at midnight UTC</p>
                    <p><em>The scraper runs daily, processing 3 brands per day across the week.</em></p>
                </div>
            </div>

            <div class="footer">
                <p>This is an automated message from the BBQ Scraper system.</p>
                <p>Powered by Railway & Supabase</p>
            </div>
        </body>
        </html>
        """

        # Create plain text version
        text_body = f"""
BBQ SCRAPER DAILY REPORT
{day_name}, {datetime.now().strftime("%B %d, %Y")}

SUMMARY
-------
Total Products Scraped: {total_products}
Brands Processed: {len(brands_scraped)}
Success Rate: {success_rate:.1f}%

BRANDS SCRAPED TODAY
--------------------
"""
        for brand in brands_scraped:
            text_body += f"✓ {brand}\n"

        if failed_brands and len(failed_brands) > 0:
            text_body += "\nFAILED BRANDS\n-------------\n"
            for brand in failed_brands:
                text_body += f"✗ {brand}\n"

        text_body += """
NEXT SCHEDULED RUN
------------------
Tomorrow at midnight UTC

---
This is an automated message from the BBQ Scraper system.
Powered by Railway & Supabase
        """

        # Attach both HTML and plain text versions
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        # Send email
        logger.info(f"Sending email notification to {EMAIL_TO}...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("✓ Email notification sent successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to send email notification: {e}")
        return False


def send_error_notification(error_message):
    """
    Send email notification when scraping fails completely

    Args:
        error_message: The error message to include
    """
    if not EMAIL_PASSWORD:
        logger.warning("EMAIL_PASSWORD not set, skipping error notification")
        return False

    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f'⚠️ BBQ Scraper Error - {datetime.now().strftime("%B %d, %Y")}'
        msg['From'] = EMAIL_FROM
        msg['To'] = EMAIL_TO

        html_body = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background-color: #e74c3c;
                    color: white;
                    padding: 20px;
                    text-align: center;
                }}
                .content {{
                    padding: 20px;
                }}
                .error {{
                    background-color: #fee;
                    border-left: 4px solid #e74c3c;
                    padding: 15px;
                    margin: 15px 0;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>⚠️ BBQ Scraper Error</h1>
                <p>{datetime.now().strftime("%B %d, %Y at %H:%M UTC")}</p>
            </div>

            <div class="content">
                <div class="error">
                    <h2>Error Details</h2>
                    <p>{error_message}</p>
                </div>

                <p>Please check the Railway logs for more details.</p>
            </div>
        </body>
        </html>
        """

        text_body = f"""
BBQ SCRAPER ERROR
{datetime.now().strftime("%B %d, %Y at %H:%M UTC")}

ERROR DETAILS
-------------
{error_message}

Please check the Railway logs for more details.
        """

        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        msg.attach(part1)
        msg.attach(part2)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)

        logger.info("✓ Error notification sent successfully")
        return True

    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")
        return False
