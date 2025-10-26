#!/usr/bin/env python3
"""
Analytics dashboard routes for ViamigoTravelAI
Serves the comprehensive analytics interface
"""

from flask import Blueprint, render_template_string, send_from_directory
import os

# Create blueprint
analytics_dashboard_bp = Blueprint('analytics_dashboard', __name__)


@analytics_dashboard_bp.route('/analytics')
def analytics_dashboard():
    """Serve the analytics dashboard"""
    try:
        # Read the analytics dashboard HTML file
        dashboard_path = os.path.join(os.path.dirname(
            __file__), 'static', 'analytics_dashboard.html')

        with open(dashboard_path, 'r', encoding='utf-8') as f:
            dashboard_html = f.read()

        return dashboard_html

    except Exception as e:
        return f"<h1>Analytics Dashboard Error</h1><p>Could not load dashboard: {e}</p>", 500


@analytics_dashboard_bp.route('/analytics/demo')
def analytics_demo():
    """Demo page with quick access to analytics"""
    demo_html = """
    <!DOCTYPE html>
    <html lang="it">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>ViamigoTravelAI - Analytics Demo</title>
        <style>
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                margin: 0;
                padding: 20px;
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .demo-container {
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 20px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
                max-width: 600px;
            }
            h1 {
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 2.5em;
            }
            p {
                color: #718096;
                font-size: 1.1em;
                margin-bottom: 30px;
                line-height: 1.6;
            }
            .btn {
                display: inline-block;
                padding: 15px 30px;
                background: linear-gradient(135deg, #667eea, #764ba2);
                color: white;
                text-decoration: none;
                border-radius: 10px;
                font-weight: 600;
                font-size: 1.1em;
                transition: all 0.3s ease;
                margin: 10px;
            }
            .btn:hover {
                transform: translateY(-3px);
                box-shadow: 0 15px 30px rgba(102, 126, 234, 0.3);
            }
            .features {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin: 30px 0;
            }
            .feature {
                background: #f8fafc;
                padding: 20px;
                border-radius: 12px;
                border: 1px solid #e2e8f0;
            }
            .feature h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            .feature p {
                color: #718096;
                font-size: 0.9em;
                margin: 0;
            }
        </style>
    </head>
    <body>
        <div class="demo-container">
            <h1>🚀 Analytics Dashboard</h1>
            <p>Benvenuto nel sistema di analisi avanzata per ViamigoTravelAI. 
               Esplora pattern di viaggio, raccomandazioni stagionali, ottimizzazione budget e insights utenti 
               per 9,930+ luoghi in 56 città italiane.</p>
            
            <div class="features">
                <div class="feature">
                    <h3>📊 Pattern di Viaggio</h3>
                    <p>Analisi comportamentale e route popolari</p>
                </div>
                <div class="feature">
                    <h3>🌤️ Raccomandazioni Stagionali</h3>
                    <p>AI-powered per meteo, folla e prezzi</p>
                </div>
                <div class="feature">
                    <h3>💰 Budget Optimization</h3>
                    <p>ML per allocazione intelligente risorse</p>
                </div>
                <div class="feature">
                    <h3>🧠 User Insights</h3>
                    <p>Segmentazione e personalizzazione</p>
                </div>
            </div>
            
            <a href="/analytics" class="btn">🚀 Apri Dashboard Completo</a>
            <a href="/" class="btn">🏠 Torna alla Homepage</a>
        </div>
    </body>
    </html>
    """
    return demo_html
