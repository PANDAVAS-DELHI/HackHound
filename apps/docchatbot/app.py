import streamlit as st
import google.generativeai as genai
from pymongo import MongoClient
from bson import ObjectId
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to MongoDB
mongourl = os.getenv("MONGO_URL")
client = MongoClient(mongourl)
db = client["HealthCareCMS"]
prescriptions_collection = db["prescirptions"]
medications_collection = db["medications"]
treatments_collection = db["treatments"]
postdiseases_collection = db["postdiseases"]

# Gemini API Configuration
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-2.0-flash')

# Extract patient ID from URL params
query_params = st.query_params
patient_id = query_params.get("patientId")

# Custom Styling for Better UI
st.markdown(
    """
    <style>
    body {
        background-color: #f0f4f8;
    }
    .container {
        max-width: 600px;
        height: 800px;
        margin: auto;
        background: #fff;
        border-radius: 10px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        padding: 20px;
    }
    .header {
        background-color: #3B9ab8;
        color: white;
        text-align: center;
        padding: 15px;
        border-radius: 8px;
        font-size: 22px;
        font-weight: bold;
    }
    .message {
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 10px;
        max-width: 85%;
        word-wrap: break-word;
        font-size: 16px;
    }
    .user-message {
        background-color: #e9ecef;
        align-self: flex-end;
        text-align: right;
    }
    .bot-message {
        background-color: #3B9ab8;
        color: white;
        text-align: left;
    }
    .button-container {
        text-align: center;
        margin-top: 15px;
    }
    .retrieve-btn {
        background-color: #3B9ab8;
        color: white;
        padding: 12px;
        border-radius: 8px;
        font-size: 18px;
        width: 100%;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s ease;
    }
    .retrieve-btn:hover {
        background-color: #357ab7; /* Adjusted hover color to match theme */
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Chatbot Container
st.markdown("<div class='header'>Patient Medical Records Retriever</div>", unsafe_allow_html=True)

# Retrieve Patient Summary Button
st.markdown("<div class='button-container'>", unsafe_allow_html=True)
if st.button("Retrieve Patient Summary"):
    try:
        patient_obj_id = ObjectId(patient_id)

        # Fetch prescriptions
        prescriptions = list(prescriptions_collection.find({"patientId": patient_obj_id}))

        if not prescriptions:
            st.warning("No prescriptions found for this patient.")
        else:
            summary_data = []
            all_medications = {}

            for pres in prescriptions:
                prescription_id = pres["_id"]
                doctor_name = pres["doctorName"]
                patient_name = pres["patientName"]

                # Fetch medications
                medications = list(medications_collection.find({"prescriptionId": prescription_id}))

                # Fetch treatments (Treatment Plan & Advice)
                treatment_plan_doc = treatments_collection.find_one({"prescriptionId": prescription_id})
                treatment_plan = treatment_plan_doc["content"] if treatment_plan_doc else "No treatment plan available."

                # Fetch disease and severity
                disease_doc = postdiseases_collection.find_one({"prescriptionId": prescription_id})
                disease = disease_doc["disease"].title() if disease_doc else "Unknown Disease"
                severity = disease_doc["severity"].capitalize() if disease_doc else "Unknown Severity"

                # Extract relevant medication details
                meds_list = []
                for med in medications:
                    med_info = f"{med['medication']} ({med['dose']}{med['doseUnit']}, {med['duration']} {med['durationUnit']}, {med['mealStatus']})"
                    meds_list.append(med_info)

                    # Track medication frequency
                    if med["medication"] in all_medications:
                        all_medications[med["medication"]]["count"] += 1
                    else:
                        all_medications[med["medication"]] = {"info": med_info, "count": 1}

                summary_data.append({
                    "doctor": doctor_name,
                    "prescriptionId": str(prescription_id),
                    "disease": disease,
                    "severity": severity,
                    "medications": meds_list,
                    "treatmentPlan": treatment_plan
                })

            # **Prepare prescription summary**
            prescription_details = "\n\n".join(
                f"Doctor {d['doctor']} diagnosed **{d['disease']} ({d['severity']})** and prescribed:\n" +
                "\n".join(f"- {med}" for med in d["medications"]) +
                f"\n\n**Treatment Plan & Advice:**\n{d['treatmentPlan']}"
                for d in summary_data
            )

            # **Summarize common medications**
            medication_trends = "\n".join(
                f"- {med}: {data['info']} (Prescribed {data['count']} times)"
                for med, data in all_medications.items()
            )

            # **Doctor-friendly AI Summary Prompt**
            prompt = f"""
            Patient: {patient_name}
            
            Prescription history:
            {prescription_details}

            Commonly prescribed medications:
            {medication_trends}

            Generate a **concise, professional summary** for a doctor. 
            Highlight key conditions, medication trends, and treatment patterns.
            Keep it **short and to the point**.

            Additionally, create a table listing all prescribed medications, including:
            - Medication Name
            - Dosage
            - Frequency
            - Duration
            - Meal Status
            """

            # Gemini API call
            try:
                response = model.generate_content(prompt)
                summary = response.text
            except Exception as e:
                st.error(f"Error calling Gemini API: {e}")
                summary = "Failed to generate summary due to an error."

            # **Display Summary**
            st.subheader("AI-Generated Medical Summary by Gemini")
            st.write(summary)

    except Exception as e:
        st.error(f"An error occurred: {e}")

st.markdown("</div>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)
