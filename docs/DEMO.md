# Run and present the interactive dashboard

**[Open the live browser demo](https://aradhanasingh3136-stack.github.io/Smart-Switch-Performance-and-Reporting-Automation/)**

The `reports/dashboard.png` file is a static preview. Use the GitHub Pages link above for the working dashboard with filters, charts, device exploration and CSV exports.

## A three-minute interview demonstration

1. Open the live link. Introduce the scope: 60 synthetic switches, 10 homes and 90 days. Overall results should show 91,867 commands, 98.01% success, 614.4 ms P95 and 99.21% heartbeat delivery.
2. Select **Firmware regression**. The report filters to firmware 1.1.0 and its observed dates. Success drops to 91.70%. Show the failure mix and explain the injected regression; this is synthetic data, not a causal real-world finding.
3. Select **Home connectivity incident**. The selected dates surround the simulated outage in HOME003. Hover over the daily chart, inspect heartbeat delivery and explain why expected heartbeats preserve the denominator.
4. Click **Reset**. Choose a different home or date range yourself. Cards, charts and the device explorer recalculate. Search a device or room, sort a table column and use the pagination controls.
5. Open **Estimated energy** from the sidebar. Explain the difference between a load/runtime estimate, an assumed baseline and measured savings. The demo does not claim measured electricity savings.
6. Click **Export selection** to download the selected daily metrics as CSV.
7. Open **View source**, then **Actions** to show the Python/SQL pipeline, its automated tests, browser-to-SQL metric reconciliation and deployment workflow.

## What runs where

- **Python and SQLite** validate and transform the data during a local run or a GitHub Actions build.
- **GitHub Pages** serves the HTML, CSS, JavaScript and validated data export.
- **Your browser** calculates selected pooled rates, exact nearest-rank P95, firmware summaries, heartbeat delivery and modeled energy. Filtering is a real calculation over the exported data.
- **Power BI** is a separate native report in `powerbi/`. This web demo should be described as a JavaScript dashboard, not as a Power BI Service deployment.
- **Synthetic data** represents a fixed historical demonstration. It is not a feed from live switches.

GitHub Pages hosts static files; it does not run a Python server for each visitor. The interaction is implemented in JavaScript. See [GitHub's explanation of Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages).

## Run locally on your Mac

```bash
cd "/Users/aradhana/Documents/GitHub/Smart Switch Performance and Reporting Automation"
python3 run.py
python3 scripts/serve_dashboard.py
```

Open `http://127.0.0.1:8765/` in a browser. Keep the terminal open. Press Ctrl+C to stop the preview. Opening `web/index.html` directly as a file cannot reliably load its data/module files; use the local server.

## Rebuild and publish from GitHub

Every push to `main` triggers **Publish interactive dashboard**. The workflow regenerates synthetic data, runs the 12 Python tests, reconciles browser metrics with raw SQL for eight selections, verifies 14 reproducible exports and deploys the `web/` folder to Pages.

To run it during an interview while signed in as the repository owner, open the repository's **Actions** tab, select **Publish interactive dashboard**, choose **Run workflow**, keep branch **main**, and run it. Wait for the build and deploy jobs to succeed, then refresh the live link. The fixed seed reproduces the same dataset; it does not fabricate new current-day data.

If deployment fails, inspect the failed step in Actions. Do not present an old PNG or a successful local run as proof of a successful hosted deployment.

## Source files

- `src/web_report.py`: compact data export from the validated SQL facts.
- `web/index.html`, `web/styles.css`: dashboard structure and presentation.
- `web/app.mjs`: controls, chart rendering, table interaction and CSV downloads.
- `web/model.mjs`: filter and metric calculations, shared with reconciliation checks.
- `scripts/check_web_dashboard.py`, `scripts/check_web_dashboard.mjs`: independent SQL comparisons.
- `.github/workflows/dashboard.yml`: rebuild, checks and Pages deployment.
