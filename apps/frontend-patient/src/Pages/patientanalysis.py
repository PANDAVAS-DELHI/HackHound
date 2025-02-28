import streamlit as st
import pymongo
import pandas as pd
import plotly.express as px
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
postdiseases_collection = db["postdiseases"]
doctors_collection = db["doctors"]  

# Extract patientId from URL params
query_params = st.query_params
patient_id = query_params.get("patientId", "67ba9cb5ac2806f11fb2a66d")  

# Set page configuration
st.set_page_config(page_title="Patient Analytics", layout="wide")

# Dark Mode CSS
st.markdown(
    """
    <style>
        body { 
            background-color: #121212; 
            color: #E0E0E0; 
            font-family: 'Inter', sans-serif;
        }
        .block-container { 
            padding: 1.5rem 2.5rem; 
            max-width: 1200px;
            margin: 0 auto;
        }
        .stMetric { 
            background-color: #1E1E1E; 
            padding: 15px;
            border-radius: 8px; 
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
            border-left: 4px solid #BB86FC;
            margin-bottom: 10px;
        }
        .stMetric label { 
            font-size: 14px; 
            font-weight: 500; 
            color: #B0B0B0;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .stMetric div { 
            font-size: 26px; 
            font-weight: 600; 
            color: #BB86FC;
            margin-top: 5px;
        }
        h1 {
            color: #E0E0E0;
            font-weight: 600;
            font-size: 32px;
            margin-bottom: 20px;
            border-bottom: 1px solid #333;
            padding-bottom: 10px;
        }
        h3 {
            color: #B0B0B0;
            font-weight: 500;
            font-size: 20px;
            margin: 25px 0 15px 0;
        }
        .stPlotlyChart {
            background-color: #1E1E1E;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
            padding: 15px;
            margin-bottom: 25px;
        }
        .stWarning {
            background-color: #332A00;
            color: #FFC107;
            padding: 10px 15px;
            border-radius: 5px;
            font-weight: 500;
            border-left: 4px solid #FFC107;
        }
        .stError {
            background-color: #330000;
            color: #FF5252;
            padding: 10px 15px;
            border-radius: 5px;
            font-weight: 500;
            border-left: 4px solid #FF5252;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Title and Introduction
st.title("📊 Patient Analytics Dashboard")


# Function to fetch patient data
@st.cache_data
def fetch_patient_data(patient_id):
    try:
        patient_object_id = ObjectId(patient_id)
        data = list(postdiseases_collection.find({"patientId": patient_object_id}, {"_id": 0}))

        if not data:
            st.warning("⚠ No matching records found in MongoDB.")
            return None

        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"🚨 MongoDB Connection Error: {e}")
        return None

df = fetch_patient_data(patient_id)

if df is None or df.empty:
    st.warning("⚠ No data found for this patient.")
else:
    # Data Processing
    disease_count = {}
    severity_count = {"mild": 0, "moderate": 0, "severe": 0}
    doctor_count = {}  
    total_cases = 0

    for _, row in df.iterrows():
        diseases = row.get("disease", "Unknown").split(", ")  
        severity = row.get("severity", "Unknown")
        doctor_id = row.get("doctorId", "Unknown")

        for disease in diseases:
            disease_count[disease] = disease_count.get(disease, 0) + 1

        severity_count[severity] = severity_count.get(severity, 0) + 1
        doctor_count[doctor_id] = doctor_count.get(doctor_id, 0) + 1
        total_cases += 1

    # Most Common Disease
    most_common_disease = max(disease_count, key=disease_count.get, default="N/A")

    # Most Visited Doctor
    most_visited_doctor_id = max(doctor_count, key=doctor_count.get, default="N/A")
    most_visited_doctor_name = "Unknown Doctor"

    if most_visited_doctor_id != "N/A":
        doctor_info = doctors_collection.find_one({"_id": ObjectId(most_visited_doctor_id)}, {"fullName": 1})
        if doctor_info:
            most_visited_doctor_name = doctor_info.get("fullName", "Unknown Doctor")

    # Severity Percentage
    severity_percentage = {k: round((v / total_cases) * 100, 2) for k, v in severity_count.items() if total_cases > 0}

    # Display Metrics
    st.markdown("### Key Metrics")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Cases", total_cases)
    col2.metric("Unique Diseases", len(disease_count))
    col3.metric("Most Common Disease", most_common_disease)
    col4.metric("Severe Cases %", f"{severity_percentage.get('severe', 0)}%")
    col5.metric("Most Visited Doctor", most_visited_doctor_name)

    # Dark Mode Color Palettes
    dark_palette = ["#BB86FC", "#03DAC5", "#CF6679", "#3700B3", "#FF0266"]
    
    # Disease Distribution Chart
    st.markdown("### 📊 Disease Distribution")
    fig1 = px.bar(x=list(disease_count.keys()), y=list(disease_count.values()), color_discrete_sequence=dark_palette)
    fig1.update_layout(paper_bgcolor="#121212", plot_bgcolor="#1E1E1E", font_color="white")
    st.plotly_chart(fig1, use_container_width=True)

    # Severity Distribution
    st.markdown("### ⚠ Severity Distribution")
    fig2 = px.bar(x=list(severity_count.keys()), y=list(severity_count.values()), color_discrete_sequence=dark_palette)
    fig2.update_layout(paper_bgcolor="#121212", plot_bgcolor="#1E1E1E", font_color="white")
    st.plotly_chart(fig2, use_container_width=True)

    # Disease Pie Chart
    st.markdown("### 🍩 Disease Occurrence")
    fig3 = px.pie(names=list(disease_count.keys()), values=list(disease_count.values()), hole=0.4, color_discrete_sequence=dark_palette)
    fig3.update_layout(paper_bgcolor="#121212", font_color="white")
    st.plotly_chart(fig3, use_container_width=True)