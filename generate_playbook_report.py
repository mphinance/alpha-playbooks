import json
import os
import argparse
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape

def generate_html(data, template_name='hud_template.html'):
    """Generate the final HTML report using Jinja2."""
    try:
        env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template(template_name)
        
        context = data.copy()
        context['ticker_first'] = data['ticker'][0] if data['ticker'] else '?'
        context['raw_json_data'] = json.dumps(data)
        context['chart_data_json'] = json.dumps(data.get('chart_data', []))
        context['ema_data_json'] = json.dumps(data.get('ema_data', {}))
        
        html = template.render(**context)
        
        ticker_dir = f"reports/{data['ticker']}"
        os.makedirs(ticker_dir, exist_ok=True)
        
        out_html = f"{ticker_dir}/{datetime.now().strftime('%Y-%m-%d')}.html"
        with open(out_html, 'w') as f:
            f.write(html)
        return out_html
    except Exception as e:
        print(f"Template Rendering Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def update_index(target_dest=None):
    """Scan reports directory and generate an index.html archive page."""
    print(f"Updating reports index at {target_dest or 'default'}...")
    try:
        env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        template = env.get_template('index_template.html')
        
        archive = {}
        reports_dir = 'reports'
        if not os.path.exists(reports_dir):
            return
            
        total_reports = 0
        for ticker in sorted(os.listdir(reports_dir)):
            ticker_path = os.path.join(reports_dir, ticker)
            if os.path.isdir(ticker_path):
                ticker_reports = []
                for f in sorted(os.listdir(ticker_path), reverse=True):
                    if f.endswith('.html') and f != 'index.html' and f != 'latest.html':
                        date_str = f.replace('.html', '')
                        ticker_reports.append({
                            "filename": f,
                            "date": date_str
                        })
                        total_reports += 1
                if ticker_reports:
                    archive[ticker] = ticker_reports
        
        is_root = target_dest and 'reports' not in target_dest
        reports_root = "" if not is_root else "/alpha/reports/"
        portal_path = "../docs/index.html" if not is_root else "/alpha/docs/index.html"

        html = template.render(
            archive=archive,
            total_reports=total_reports,
            total_tickers=len(archive),
            last_updated=datetime.now().strftime("%Y-%m-%d %H:%M"),
            reports_root=reports_root,
            portal_path=portal_path
        )
        
        out_path = target_dest if target_dest else os.path.join(reports_dir, 'index.html')
        with open(out_path, 'w') as f:
            f.write(html)
        print(f"Archive Index updated: {out_path}")
    except Exception as e:
        print(f"Error updating index: {e}")

def main():
    parser = argparse.ArgumentParser(description="Generate Playbook Report")
    parser.add_argument('--ticker', type=str, required=True, help='Stock Ticker Symbol')
    parser.add_argument('--template', type=str, default='hud_template.html', help='Jinja template file')
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

if __name__ == "__main__":
    main()
