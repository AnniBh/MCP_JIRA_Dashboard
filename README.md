# MCP JIRA Dashboard

A Streamlit-based dashboard application that provides analytics and insights for MCP (Model Context Protocol) JIRA interactions.

## Features

- **Real-time Analytics**: Track JIRA issue creation, updates, and interactions
- **Automation Metrics**: Compare manual vs automated actions and their efficiency
- **Visual Insights**: Interactive charts and graphs showing time savings and productivity gains
- **Google Sheets Integration**: Connects to Google Sheets for data storage and retrieval

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Google Sheets Setup**:
   - Create a Google Service Account
   - Download the JSON credentials file
   - Update the filename in the code: `mcp-jira-dashboard-1b9f1dc8f477.json`

3. **Run the Application**:
   ```bash
   streamlit run mcp_jira_dashboard_app.py
   ```

## Usage

The dashboard provides three main tabs:

1. **Overview**: General analytics and metrics
2. **Comparison**: Manual vs automated actions analysis
3. **Raw Data**: Detailed data tables and tool usage statistics

## Configuration

- Update the Google Sheets URL in the code
- Modify the service account filename as needed
- Adjust chart parameters and thresholds as required

## Troubleshooting

If you encounter import errors, make sure all dependencies are installed:
```bash
pip install streamlit pandas matplotlib seaborn gspread gspread-dataframe
```

## Contributing

Feel free to submit issues and enhancement requests!
