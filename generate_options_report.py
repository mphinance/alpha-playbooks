import json
import os
import argparse
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
from generate_playbook_report import update_index, generate_html

def update_dashboard(target_dest="docs/index.html"):
    """Generate the dynamic dashboard with the ticker list."""
    print(f"Updating dynamic dashboard at {target_dest}...")
    try:
        env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('dashboard_template.html')
        
        tickers = []
        reports_dir = 'reports'
        if os.path.exists(reports_dir):
            for ticker in sorted(os.listdir(reports_dir)):
                if os.path.isdir(os.path.join(reports_dir, ticker)):
                    tickers.append(ticker)
        
        html = template.render(
            tickers=tickers,
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M")
        )
        
        os.makedirs(os.path.dirname(target_dest), exist_ok=True)
        with open(target_dest, 'w') as f:
            f.write(html)
        print(f"Dashboard updated: {target_dest}")
    except Exception as e:
        print(f"Error updating dashboard: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Options Playbook Report")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    parser.add_argument('--template', type=str, default='options_template.html', help='Jinja template file')
    args = parser.parse_args()

    ticker_dir = f"reports/{args.ticker}"
    latest_json = f"{ticker_dir}/latest.json"
    latest_series = f"{ticker_dir}/latest_series.json"

    if not os.path.exists(latest_json):
        print(f"Error: No data found for {args.ticker}. Run fetch script first.")
        return

    with open(latest_json, 'r') as f:
        data = json.load(f)

    if os.path.exists(latest_series):
        with open(latest_series, 'r') as f:
            series_data = json.load(f)
            data['chart_data'] = series_data.get('chart_data', [])
            data['ema_data'] = series_data.get('ema_data', {})
    else:
        data['chart_data'] = []
        data['ema_data'] = {}

    html_path = generate_html(data, args.template)
    if html_path:
        print(f"HTML Report saved to: {html_path}")
        
    update_index()
    update_index(target_dest="index.html")
    update_dashboard()

if __name__ == "__main__":
    main()
