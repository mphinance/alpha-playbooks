import os
import argparse
from playwright.sync_api import sync_playwright

def capture_report(ticker, output_format="png"):
    ticker_dir = f"reports/{ticker}"
    
    if not os.path.exists(ticker_dir):
        print(f"Error: Directory for {ticker} not found at {ticker_dir}")
        return
        
    html_files = [f for f in os.listdir(ticker_dir) if f.endswith('.html') and f != 'latest.html']
    if not html_files:
        print(f"Error: No HTML reports found in {ticker_dir}")
        return
        
    latest_html = sorted(html_files, reverse=True)[0]
    report_path = os.path.abspath(os.path.join(ticker_dir, latest_html))
    
    output_dir = f"reports/{ticker}/exports"
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f"{output_dir}/{ticker}_report.{output_format}"
    
    with sync_playwright() as p:
        # Launching browser
        browser = p.chromium.launch(headless=True)
        # Setting a large desktop viewport to ensure the dashboard renders fully
        page = browser.new_page(viewport={"width": 1920, "height": 1080})
        
        file_uri = f"file://{report_path}"
        print(f"Loading {file_uri}...")
        
        # Wait for the page to fully load and animations to finish
        page.goto(file_uri, wait_until="load")
        page.wait_for_timeout(2000) # Give charts a moment to render
        
        if output_format == "png":
            # Taking a full page screenshot ensures we get everything, even if it scrolls
            page.screenshot(path=output_file, full_page=True)
            print(f"Saved screenshot to: {output_file}")
        elif output_format == "pdf":
            # PDFs might break up the dashboard design, but print_background ensures colors are saved
            page.pdf(path=output_file, print_background=True, width="19.2in", height="10.8in")
            print(f"Saved PDF to: {output_file}")
        else:
            print("Unsupported format. Use 'png' or 'pdf'.")
            
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture HTML Report as Image or PDF")
    parser.add_argument("--ticker", type=str, required=True, help="Stock Ticker Symbol")
    parser.add_argument("--format", type=str, choices=["png", "pdf"], default="png", help="Output format: png or pdf")
    args = parser.parse_args()
    
    capture_report(args.ticker, args.format)
