import streamlit as st
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv
import plotly.graph_objects as go
import google.generativeai as genai

# Load environment variables & Configure AI
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

# Import our backend logic
from core.vcf_parser import parse_vcf, determine_phenotype
from core.llm_engine import generate_pharmacogenomic_report

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="PharmaGuard | AI", layout="wide", page_icon="🧬")

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .risk-badge { padding: 8px 16px; border-radius: 6px; font-weight: bold; color: white; display: inline-block; text-align: center; width: 100%; font-size: 1.2rem;}
    .bg-safe { background-color: #10b981; }
    .bg-adjust { background-color: #f59e0b; }
    .bg-toxic { background-color: #ef4444; }
    .bg-ineffective { background-color: #a855f7; }
    </style>
""", unsafe_allow_html=True)

st.title("🧬 PharmaGuard")
st.markdown("**Pharmacogenomic Risk Prediction System** | *Precision Medicine Algorithm*")
st.markdown("---")

# --- INITIALIZE SESSION STATE ---
if "analysis_results" not in st.session_state:
    st.session_state.analysis_results = None
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "I am your Clinical Copilot. Ask me any follow-up questions about this patient's pharmacogenomic profile."}]

# --- INPUT SECTION ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Patient Data Input")
    uploaded_file = st.file_uploader("Upload Patient VCF File (v4.2 format, max 5MB)", type=['vcf'])
    
    if uploaded_file:
        file_size = uploaded_file.size / (1024 * 1024)
        if file_size > 5.0:
            st.error("File exceeds 5MB limit.")
            uploaded_file = None
        else:
            st.success(f"File validated: {uploaded_file.name}")

with col2:
    st.subheader("2. Target Drug Selection")
    DRUG_GENE_MAP = {
        "CODEINE": "CYP2D6", "WARFARIN": "CYP2C9", "CLOPIDOGREL": "CYP2C19",
        "SIMVASTATIN": "SLCO1B1", "AZATHIOPRINE": "TPMT", "FLUOROURACIL": "DPYD"
    }
    target_drugs = st.multiselect(
        "Select target drugs for CPIC analysis (multiple allowed):",
        list(DRUG_GENE_MAP.keys()), default=["CODEINE"]
    )

st.markdown("---")

# --- EXECUTION ENGINE ---
if st.button("Generate AI Risk Assessment", type="primary", use_container_width=True):
    if not uploaded_file:
        st.warning("⚠️ Please upload a VCF file to proceed.")
    elif not target_drugs:
        st.warning("⚠️ Please select at least one drug.")
    elif not api_key:
        st.error("⚠️ API Key missing. Please check your .env file.")
    else:
        with st.spinner("Parsing genomic data and engaging AI reasoning engine..."):
            patient_id = f"PATIENT_{str(uuid.uuid4())[:8].upper()}"
            variants = parse_vcf(uploaded_file)
            
            results = []
            for target_drug in target_drugs:
                target_gene = DRUG_GENE_MAP[target_drug]
                try:
                    diplotype, phenotype = determine_phenotype(variants, target_gene)
                    report_json = generate_pharmacogenomic_report(
                        patient_id=patient_id, drug=target_drug, variants=variants,
                        target_gene=target_gene, diplotype=diplotype, phenotype=phenotype
                    )
                    report_json["timestamp"] = datetime.utcnow().isoformat() + "Z"
                    results.append({"drug": target_drug, "data": report_json})
                except Exception as e:
                    st.error(f"Error processing {target_drug}: {str(e)}")
            
            # Save results to session state so they don't disappear when chatting
            st.session_state.analysis_results = results
            st.session_state.messages = [{"role": "assistant", "content": "I am your Clinical Copilot. Ask me any follow-up questions about this patient's pharmacogenomic profile."}]

# --- RESULTS DASHBOARD ---
if st.session_state.analysis_results:
    for res in st.session_state.analysis_results:
        target_drug = res["drug"]
        report_json = res["data"]
        
        st.markdown(f"## 📊 Results for {target_drug}")
        res_col1, res_col2 = st.columns([1, 2])
        
        with res_col1:
            risk_label = report_json["risk_assessment"]["risk_label"]
            badge_class = "bg-safe" if risk_label == "Safe" else "bg-toxic" if risk_label == "Toxic" else "bg-ineffective" if risk_label == "Ineffective" else "bg-adjust"
            
            st.markdown(f"<div class='risk-badge {badge_class}'>{risk_label.upper()}</div>", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            
            # 🥇 KILLER FEATURE: VISUAL CONFIDENCE GAUGE
            conf_score = report_json['risk_assessment']['confidence_score'] * 100
            fig = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = conf_score,
                domain = {'x': [0, 1], 'y': [0, 1]},
                title = {'text': "AI Confidence", 'font': {'size': 18}},
                gauge = {
                    'axis': {'range': [None, 100]},
                    'bar': {'color': "#1e2d3d"},
                    'steps': [
                        {'range': [0, 50], 'color': "#ef4444"},
                        {'range': [50, 85], 'color': "#f59e0b"},
                        {'range': [85, 100], 'color': "#10b981"}
                    ]
                }
            ))
            fig.update_layout(height=220, margin=dict(l=10, r=10, t=40, b=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("### Genomic Profile")
            st.write(f"**Gene:** {report_json['pharmacogenomic_profile']['primary_gene']}")
            st.write(f"**Diplotype:** {report_json['pharmacogenomic_profile']['diplotype']}")
            st.write(f"**Phenotype:** {report_json['pharmacogenomic_profile']['phenotype']}")

        with res_col2:
            st.markdown("### Clinical Explanation (Explainable AI)")
            st.info(report_json["llm_generated_explanation"]["summary"])
            
            with st.expander("🔬 Biological Mechanism & Variants", expanded=True):
                st.write("**Mechanism:**", report_json["llm_generated_explanation"]["biological_mechanism"])
                
                # 🥈 KILLER FEATURE: LIVE dbSNP DATABASE LINKS
                st.write("**Detected Variants (dbSNP Links):**")
                variants_list = report_json['pharmacogenomic_profile']['detected_variants']
                if not variants_list:
                    st.write("- *No high-impact variants detected.*")
                for variant in variants_list:
                    rsid = variant.get('rsid', '')
                    if rsid.startswith("rs"):
                        st.markdown(f"- **[{rsid}](https://www.ncbi.nlm.nih.gov/snp/{rsid})** (Click to view in NIH database)")
                    else:
                        st.markdown(f"- {rsid}")
                
            with st.expander("📋 CPIC Dosing Recommendation", expanded=True):
                st.write("**Action:**", report_json["clinical_recommendation"]["action"])
                st.write("**Dosage Adjustment:**", report_json["clinical_recommendation"]["dosage_adjustment"])
                st.write("**Alternative Drugs:**", ", ".join(report_json["clinical_recommendation"]["alternative_drugs"]))

        st.subheader("Mandatory JSON Schema Output")
        st.json(report_json)
        st.download_button(
            label=f"Download Official JSON Report for {target_drug}",
            file_name=f"pharmaguard_{report_json['patient_id']}_{target_drug}.json",
            mime="application/json",
            data=json.dumps(report_json, indent=2),
            use_container_width=True,
            key=f"download_{target_drug}"
        )
        st.markdown("---")

    # 🥉 KILLER FEATURE: CLINICAL COPILOT CHAT
    st.subheader("💬 AI Clinical Copilot")
    st.caption("Ask follow-up questions about this specific patient's profile based on the uploaded data.")
    
    # Render chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat Input
    if prompt := st.chat_input("e.g., Why is codeine ineffective for a Poor Metabolizer?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Analyzing clinical context..."):
                # Pass the raw JSON data to the AI as context so it knows exactly who it is talking about
                context_data = json.dumps([r["data"] for r in st.session_state.analysis_results])
                system_prompt = f"You are a clinical pharmacogenomics assistant. Here is the patient's data: {context_data}. Answer the user's question concisely in 2-3 sentences based ON THIS DATA."
                
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(system_prompt + "\nQuestion: " + prompt)
                
                st.markdown(response.text)
                st.session_state.messages.append({"role": "assistant", "content": response.text})