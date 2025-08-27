import os, json, base64
def save_html_report(res: dict, out_dir: str):
    eq_png = os.path.join(out_dir, "equity_curve.png")
    metrics = res["metrics"]
    b64 = ""
    if os.path.exists(eq_png):
        b64 = base64.b64encode(open(eq_png, "rb").read()).decode()
    html = f"""
    <html><body>
    <h1>Portfolio Backtest Report</h1>
    <pre>{json.dumps(metrics, indent=2)}</pre>
    {'<img src="data:image/png;base64,' + b64 + '"/>' if b64 else ''}
    </body></html>
    """
    with open(os.path.join(out_dir, "report.html"), "w") as f:
        f.write(html)
