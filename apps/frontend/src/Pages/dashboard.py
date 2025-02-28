import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
mongourl = "mongodb+srv://mukeshpaliwal:4IFhHJmDCAhPwMMm@firstdb.5oexb.mongodb.net/HealthCareCMS"

# Check if MongoDB URL is provided
if not mongourl:
    st.error("MONGO_URL not found! Check your .env file.")
    st.stop()

# Connect to MongoDB
client = MongoClient(mongourl)
db = client["HealthCareCMS"]
collection = db["postdiseases"]

# Extract doctorId from URL params
query_params = st.query_params
doctor_id = query_params.get("doctorId")

# Page configuration
st.set_page_config(
    page_title="Disease Analytics",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Clean, minimalist styling
st.markdown("""
    <style>
        /* Clean slate - remove default Streamlit styling */
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
            max-width: 95%;
        }
        
        /* Typography */
        h1, h2, h3, h4 {
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 300;
            color: #333;
        }
        
        /* Dashboard header */
        .header {
            margin-bottom: 1.2rem;
            border-bottom: 1px solid #f0f0f0;
            padding-bottom: 1rem;
        }
        
        /* KPI metrics */
        .metric-container {
            background-color: white;
            border-radius: 8px;
            padding: 1.2rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            margin-bottom: 1.2rem;
            transition: all 0.3s ease;
        }
        
        .metric-container:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
            transform: translateY(-2px);
        }
        
        .metric-value {
            font-size: 28px;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 0.2rem;
        }
        
        .metric-label {
            font-size: 12px;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        /* Chart containers */
        .chart-container {
            background-color: white;
            border-radius: 8px;
            padding: 1.5rem;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
            margin-bottom: 1.2rem;
            transition: all 0.3s ease;
        }
        
        .chart-container:hover {
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .chart-title {
            font-size: 16px;
            color: #2c3e50;
            font-weight: 500;
            margin-bottom: 0.8rem;
        }
        
        /* Footer */
        .footer {
            color: #95a5a6;
            font-size: 11px;
            text-align: center;
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid #f0f0f0;
        }
    </style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
    <div class="header">
        <h1 style="font-size: 26px; margin-bottom: 0.2rem;">Disease Analytics</h1>
        <p style="color: #7f8c8d; font-size: 14px; margin: 0;">Doctor ID: {}</p>
    </div>
""".format(doctor_id), unsafe_allow_html=True)

@st.cache_data
def fetch_data(doctor_id):
    try:
        doctor_object_id = ObjectId(doctor_id)
        data = list(collection.find({"doctorId": doctor_object_id}, {"_id": 0}))
        return pd.DataFrame(data) if data else None
    except:
        st.error("Invalid Doctor ID format or MongoDB Connection Error.")
        return None

# Fetch data silently
df = fetch_data(doctor_id)

if df is None or df.empty:
    st.warning("No data found for this doctor.")
else:
    disease_count = df["disease"].value_counts().to_dict()
    severity_count = df["severity"].value_counts().to_dict()
    total_cases = len(df)
    most_common_disease = max(disease_count, key=disease_count.get, default="N/A")
    severity_percentage = {k: round((v / total_cases) * 100, 2) for k, v in severity_count.items() if total_cases > 0}
    
    # KPI Metrics in a clean row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-value">{}</div>
                <div class="metric-label">Total Cases</div>
            </div>
        """.format(total_cases), unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-value">{}</div>
                <div class="metric-label">Unique Diseases</div>
            </div>
        """.format(len(disease_count)), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-value" style="font-size: 22px;">{}</div>
                <div class="metric-label">Most Common</div>
            </div>
        """.format(most_common_disease), unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
            <div class="metric-container">
                <div class="metric-value">{}</div>
                <div class="metric-label">Severe Cases</div>
            </div>
        """.format(f"{severity_percentage.get('severe', 0)}%"), unsafe_allow_html=True)
    
    # First row of charts
    col1, col2 = st.columns(2)
    
    # Create a sorted disease dataframe for better visualization
    disease_df = pd.DataFrame({
        'disease': list(disease_count.keys()),
        'count': list(disease_count.values())
    }).sort_values('count', ascending=False)
    
    # Define a modern color palette
    modern_colors = ["#3A86FF", "#4361EE", "#4A57E6", "#5E60CE", "#7209B7", "#B5179E", "#F72585"]
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Disease Distribution</div>', unsafe_allow_html=True)
        
        # Create a more modern, trendy bar chart using plotly graph objects
        fig1 = go.Figure()
        
        # Add a bar trace with gradient color
        fig1.add_trace(go.Bar(
            x=disease_df['disease'],
            y=disease_df['count'],
            text=disease_df['count'],
            textposition='auto',
            marker=dict(
                color=disease_df['count'],
                colorscale='Blues',
                opacity=0.9,
                line=dict(width=0)
            ),
            hoverinfo='x+y',
            hovertemplate='<b>%{x}</b><br>Cases: %{y}<extra></extra>'
        ))
        
        # Update layout for a more modern look
        fig1.update_layout(
            margin=dict(l=10, r=10, t=10, b=60),
            xaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title=None,
                tickangle=-45
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='#f0f0f0',
                showline=False,
                zeroline=False,
                title=None
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            showlegend=False,
            height=300,
            bargap=0.15
        )
        
        st.plotly_chart(fig1, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Severity Distribution</div>', unsafe_allow_html=True)
        
        # Create a more visually appealing pie chart
        fig2 = px.pie(
            names=list(severity_count.keys()),
            values=list(severity_count.values()),
            hole=0.6,
            color_discrete_sequence=["#3A86FF", "#4CC9F0", "#4361EE"]
        )
        
        fig2.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=-0.15, 
                xanchor="center", 
                x=0.5,
                font=dict(size=12)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=300
        )
        
        fig2.update_traces(
            textposition='outside', 
            textinfo='percent+label',
            marker=dict(line=dict(color='white', width=2))
        )
        
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Second row of charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Severity Levels</div>', unsafe_allow_html=True)
        
        # Create a horizontal bar chart for severity
        severity_df = pd.DataFrame({
            'severity': list(severity_count.keys()),
            'count': list(severity_count.values())
        }).sort_values('count', ascending=True)
        
        # Color mapping for severity
        severity_colors = {
            'mild': '#4CC9F0',
            'moderate': '#4361EE',
            'severe': '#3A0CA3'
        }
        
        color_list = [severity_colors.get(s, '#3A86FF') for s in severity_df['severity']]
        
        fig3 = go.Figure()
        
        fig3.add_trace(go.Bar(
            y=severity_df['severity'],
            x=severity_df['count'],
            text=severity_df['count'],
            textposition='auto',
            orientation='h',
            marker=dict(
                color=color_list,
                line=dict(width=0)
            ),
            hovertemplate='<b>%{y}</b><br>Cases: %{x}<extra></extra>'
        ))
        
        fig3.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            xaxis=dict(
                showgrid=True,
                gridcolor='#f0f0f0',
                showline=False,
                zeroline=False,
                title=None
            ),
            yaxis=dict(
                showgrid=False,
                showline=False,
                zeroline=False,
                title=None
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=300,
            bargap=0.2
        )
        
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="chart-container">', unsafe_allow_html=True)
        st.markdown('<div class="chart-title">Disease Distribution</div>', unsafe_allow_html=True)
        
        # Create a modern donut chart with thicker segments
        fig4 = go.Figure()
        
        # Get top 5 diseases for better visualization
        top_diseases = disease_df.head(5)
        other_count = disease_df['count'].sum() - top_diseases['count'].sum()
        
        if other_count > 0:
            top_diseases = pd.concat([
                top_diseases, 
                pd.DataFrame({'disease': ['Other'], 'count': [other_count]})
            ])
        
        fig4 = go.Figure(data=[go.Pie(
            labels=top_diseases['disease'],
            values=top_diseases['count'],
            hole=0.6,
            textinfo='percent',
            textposition='outside',
            marker=dict(
                colors=modern_colors[:len(top_diseases)],
                line=dict(color='white', width=2)
            ),
            hoverinfo='label+percent+value',
            hovertemplate='<b>%{label}</b><br>%{percent}<br>Cases: %{value}<extra></extra>'
        )])
        
        fig4.update_layout(
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=True,
            legend=dict(
                orientation="h", 
                yanchor="bottom", 
                y=-0.15, 
                xanchor="center", 
                x=0.5,
                font=dict(size=11)
            ),
            plot_bgcolor='white',
            paper_bgcolor='white',
            height=300,
            annotations=[dict(
                text='Disease<br>Distribution',
                x=0.5, y=0.5,
                font_size=12,
                showarrow=False
            )]
        )
        
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Footer
    st.markdown("""
        <div class="footer">
            Dashboard updated: {} • HealthCareCMS
        </div>
    """.format(pd.Timestamp.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)