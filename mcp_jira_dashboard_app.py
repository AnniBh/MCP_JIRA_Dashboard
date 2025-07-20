import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import json
import seaborn as sns
import gspread
from gspread_dataframe import get_as_dataframe

st.set_page_config(page_title="MCP JIRA Dashboard", layout="wide")

st.title("🚀 MCP-Enabled JIRA Issue Dashboard")

# Google Sheet setup
gc = gspread.service_account(filename='mcp-jira-dashboard-1b9f1dc8f477.json')
sh = gc.open_by_url('https://docs.google.com/spreadsheets/d/1-x7GffH5gy__uwLFlId0fDBzASZHJMWMXawi9JBakKs/edit?pli=1#gid=0')
worksheet = sh.get_worksheet(0)
df = get_as_dataframe(worksheet)
auto_df = get_as_dataframe(worksheet)
auto_df['source'] = 'automated'
df['source'] = 'automated'
auto_df.columns = auto_df.columns.str.strip()

# Sidebar controls
st.sidebar.header("⚙️ Controls")
manual_file = st.sidebar.file_uploader("Upload Manual JIRA Actions CSV", type="csv")
manual_df = pd.DataFrame()
if manual_file is not None:
    manual_df = pd.read_csv(manual_file)
    manual_df['timestamp'] = pd.to_datetime(manual_df['timestamp'], errors='coerce')
    manual_df['source'] = 'manual'
    manual_df.columns = manual_df.columns.str.strip().str.lower()
    manual_df = manual_df.rename(columns={
        'tool_used': 'tool_name',
        'user': 'name',
        'time_taken_sec': 'time_to_create'
    })
    manual_df['time_to_create'] = pd.to_numeric(manual_df['time_to_create'], errors='coerce').abs().round(2)
    keep_cols = ['timestamp', 'action_type', 'issue_key', 'name', 'tool_name', 'time_to_create', 'source']
    manual_df = manual_df[[col for col in keep_cols if col in manual_df.columns]]
    if 'response' not in manual_df.columns:
        manual_df['response'] = None
    st.sidebar.success("Manual CSV uploaded and processed.")
  
   



# After manual_df and auto_df are defined and loaded
common_cols = ["timestamp", "name", "response", "source", "tool_name", "time_to_create"]


# Parse response

def parse_response(row):
    try:
        return json.loads(row)
    except:
        return {}

def safe_get(data, field, subfield=None):
    if isinstance(data, dict):
        if subfield:
            return data.get(field, {}).get(subfield)
        return data.get(field)
    return None

for df_target in [df, auto_df]:
    df_target['parsed'] = df_target['response'].apply(parse_response)
    df_target['issue_key'] = df_target['parsed'].apply(lambda x: safe_get(x, 'key'))
    df_target['summary'] = df_target['parsed'].apply(lambda x: safe_get(x, 'summary'))
    df_target['status'] = df_target['parsed'].apply(lambda x: safe_get(x, 'status', 'name'))
    df_target['priority'] = df_target['parsed'].apply(lambda x: safe_get(x, 'priority', 'name'))
    df_target['created'] = pd.to_datetime(df_target['parsed'].apply(lambda x: safe_get(x, 'created')), errors='coerce')
    df_target['timestamp'] = pd.to_datetime(df_target['timestamp'], errors='coerce')
    if 'time_to_create' in df_target.columns:
        df_target['time_to_create'] = pd.to_numeric(df_target['time_to_create'], errors='coerce')
    else:
        df_target['time_to_create'] = None
    df_target['project'] = df_target['issue_key'].str.split('-').str[0]
    df_target['issue_type'] = df_target['parsed'].apply(lambda x: safe_get(x, 'issuetype', 'name'))
    df_target['reporter'] = df_target['parsed'].apply(lambda x: safe_get(x, 'reporter', 'displayName'))
    df_target['assignee'] = df_target['parsed'].apply(lambda x: safe_get(x, 'assignee', 'displayName'))
    df_target['labels'] = df_target['parsed'].apply(lambda x: safe_get(x, 'labels'))
    df_target['resolution'] = df_target['parsed'].apply(lambda x: safe_get(x, 'resolution', 'name'))
    df_target['resolution_date'] = pd.to_datetime(df_target['parsed'].apply(lambda x: safe_get(x, 'resolutiondate')), errors='coerce')


# KPI Summary
col1, col2, col3 = st.columns(3)
col1.metric("Total Interactions", len(df))
col2.metric("Unique Users", df['email'].nunique())
col3.metric("Tools Used", df['tool_name'].nunique())

# Tabs for Layout
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🔍 Comparison", "📋 Raw Data"])

with tab1:
    st.subheader("🗕️ Issues Created Over Time")
    issues_by_date = df[df['created'].notna()].groupby(df['created'].dt.date).size()
    st.line_chart(issues_by_date)

    st.subheader("📊 Priority Distribution by Project")
    filtered_df = df[df['project'].isin(['SCRUM', 'CLD'])]
    priority_counts = filtered_df.groupby(['project', 'priority']).size().unstack(fill_value=0)
    fig, ax = plt.subplots()
    priority_counts.plot(kind='bar', ax=ax)
    ax.set_ylabel('Number of Issues')
    ax.set_xlabel('Project')
    ax.set_title('Priority of Issues in SCRUM and CLD Projects')
    st.pyplot(fig)

    st.subheader("🛠️ Average Time to Create per Tool")
    tool_summary = df.groupby('tool_name')['time_to_create'].mean().sort_values()

    # Find the north star tool (fastest)
    north_star_tool = tool_summary.idxmin()
    north_star_value = tool_summary.min()

    # Horizontal bar plot with highlight
    fig, ax = plt.subplots(figsize=(8, 4))
    colors = ['gold' if t == north_star_tool else 'skyblue' for t in tool_summary.index]
    tool_summary.plot(kind='barh', color=colors, ax=ax)
    ax.set_xlabel('Avg Time to Create (sec)')
    ax.set_ylabel('Tool Name')
    ax.set_title('Average Time to Create by Tool')
    ax.invert_yaxis()
    for i, v in enumerate(tool_summary.values):
        ax.text(v, i, f'{v:.2f}', va='center', ha='left', fontsize=9)
    st.pyplot(fig)

    # Show the north star tool as a metric
    st.metric(label="North Star Tool (Fastest)", value=north_star_tool, delta=f"{north_star_value:.2f} sec")

    st.subheader("🛠️ Tool Leaderboard (by Avg Time to Create)")
    st.dataframe(tool_summary.reset_index().rename(columns={'time_to_create': 'Avg Time to Create (sec)'}))

    st.subheader(" User Efficiency")
    user_eff = df.groupby('email')['time_to_create'].mean().sort_values()
    fig2, ax2 = plt.subplots()
    user_eff.plot(kind='barh', color='green', ax=ax2)
    ax2.set_xlabel("Average Time to Create (seconds)")
    st.pyplot(fig2)

    st.subheader("📊 Distribution of Time to Create")
    fig3, ax3 = plt.subplots()
    sns.boxplot(data=df[df['time_to_create'].notna()], x='time_to_create', ax=ax3)
    ax3.set_title("Boxplot of Time to Create")
    st.pyplot(fig3)

    st.subheader("🔥 Daily Interaction Volume Heatmap")
    df['day'] = df['timestamp'].dt.date
    df['hour'] = df['timestamp'].dt.hour
    heatmap_data = df.groupby(['day', 'hour']).size().unstack(fill_value=0)
    fig4, ax4 = plt.subplots(figsize=(12, 6))
    sns.heatmap(heatmap_data, cmap="YlGnBu", linewidths=.5, ax=ax4)
    st.pyplot(fig4)

    doc_df = df[df['tool_name'].str.contains('confluence', case=False, na=False)]
    st.bar_chart(doc_df.groupby('source')['time_to_create'].mean())

    if 'nl_triggered' in df.columns:
        st.bar_chart(df.groupby('nl_triggered')['time_to_create'].mean())

    

with tab2:
    if not manual_df.empty:
        st.subheader("🔍 Manual vs Automated Actions Comparison")
        # Remove duplicate columns
        manual_df = manual_df.loc[:, ~manual_df.columns.duplicated()]
        auto_df = auto_df.loc[:, ~auto_df.columns.duplicated()]

        # Only use columns that exist in both DataFrames
        common_cols = ["timestamp", "name", "response", "source", "tool_name", "time_to_create"]
        manual_cols = [col for col in common_cols if col in manual_df.columns]
        auto_cols = [col for col in common_cols if col in auto_df.columns]
        cols_to_use = list(set(manual_cols) & set(auto_cols))

        manual_df = manual_df[cols_to_use]
        auto_df = auto_df[cols_to_use]

        combined_df = pd.concat([manual_df, auto_df], ignore_index=True)
        st.dataframe(combined_df)

        st.subheader("⏱️ Average Time Taken: Manual vs Automated Actions")
        fig_cmp, ax_cmp = plt.subplots()
        combined_df.groupby('source')['time_to_create'].mean().plot(kind='bar', ax=ax_cmp)
        ax_cmp.set_ylabel('Average Time Taken (seconds)')
        st.pyplot(fig_cmp)




with tab3:
    st.subheader("📋 Raw Log Data")
    st.dataframe(df[['timestamp', 'tool_name', 'issue_key', 'status', 'priority', 'created', 'time_to_create']])

    st.subheader("🧰 Tool Usage & Time Spent")
    tool_time_summary = df.groupby('tool_name')['time_to_create'].agg(['count', 'mean']).reset_index()
    tool_time_summary.columns = ['Tool Name', 'Usage Count', 'Avg Time to Create (s)']
    st.dataframe(tool_time_summary)

    fig_tool_count, ax_tool_count = plt.subplots()
    tool_time_summary.set_index("Tool Name")["Usage Count"].plot(kind="bar", color="skyblue", ax=ax_tool_count)
    ax_tool_count.set_ylabel("Number of Calls")
    st.pyplot(fig_tool_count)

    fig_tool_time, ax_tool_time = plt.subplots()
    tool_time_summary.set_index("Tool Name")["Avg Time to Create (s)"].dropna().plot(kind="bar", color="orange", ax=ax_tool_time)
    ax_tool_time.set_ylabel("Seconds")
    st.pyplot(fig_tool_time)

    st.bar_chart(df.groupby('source')['time_to_create'].mean())
