import streamlit as st
import json
import uuid
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables (API Key)
load_dotenv()

# Import our backend logic
from core.vcf_parser import parse_vcf, determine_phenotype
from core.llm_engine import generate_pharmacogenomic_report

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="Drugo | AI", layout="wide", page_icon="🧬")

# Custom CSS to make the UI look premium and clinical
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .risk-badge { padding: 8px 16px; border-radius: 6px; font-weight: bold; color: white; display: inline-block;}
    .bg-safe { background-color: #10b981; }
    .bg-adjust { background-color: #f59e0b; }
    .bg-toxic { background-color: #ef4444; }
    </style>
""", unsafe_allow_html=True)

st.title("🧬 Drugo")
st.markdown("**Pharmacogenomic Risk Prediction System** | *Precision Medicine Algorithm*")
st.markdown("---")

# --- INPUT SECTION ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("1. Patient Data Input")
    uploaded_file = st.file_uploader("Upload Patient VCF File (v4.2 format, max 5MB)", type=['vcf'])
    
    if uploaded_file:
        file_size = uploaded_file.size / (1024 * 1024)
        if file_size > 5.0:
            st.error("File exceeds 5MB limit. Please upload a smaller file.")
            uploaded_file = None
        else:
            st.success(f"File validated: {uploaded_file.name} ({file_size:.2f} MB)")

with col2:
    st.subheader("2. Target Drug Selection")
    # Mapping the 6 required drugs to their primary CPIC genes
    DRUG_GENE_MAP = {
        "CODEINE": "CYP2D6", 
        "WARFARIN": "CYP2C9", 
        "CLOPIDOGREL": "CYP2C19",
        "SIMVASTATIN": "SLCO1B1", 
        "AZATHIOPRINE": "TPMT", 
        "FLUOROURACIL": "DPYD"
    }
    
    target_drug = st.selectbox(
        "Select target drug for CPIC analysis:",
        list(DRUG_GENE_MAP.keys())
    )

st.markdown("---")

# --- EXECUTION ENGINE ---
if st.button("Generate AI Risk Assessment", type="primary", use_container_width=True):
    if not uploaded_file:
        st.warning("⚠️ Please upload a VCF file to proceed.")
    elif not os.getenv("GEMINI_API_KEY"):
        st.error("⚠️ API Key missing. Please check your .env file.")
    else:
        with st.spinner("Parsing genomic data and engaging AI reasoning engine..."):
            # Generate a mock patient ID
            patient_id = f"PATIENT_{str(uuid.uuid4())[:8].upper()}"
            target_gene = DRUG_GENE_MAP[target_drug]
            
            try:
                # 1. Parse the VCF
                variants = parse_vcf(uploaded_file)
                
                # 2. Determine Phenotype via CPIC Rules
                diplotype, phenotype = determine_phenotype(variants, target_gene)
                
                # 3. Call the LLM to generate the strict JSON report
                report_json = generate_pharmacogenomic_report(
                    patient_id=patient_id, 
                    drug=target_drug, 
                    variants=variants,
                    target_gene=target_gene,
                    diplotype=diplotype,
                    phenotype=phenotype
                )
                
                # Ensure timestamp matches current time
                report_json["timestamp"] = datetime.utcnow().isoformat() + "Z"
                
                # --- RESULTS DASHBOARD ---
                st.subheader("Clinical Assessment Results")
                
                res_col1, res_col2 = st.columns([1, 2])
                
                with res_col1:
                    risk_label = report_json["risk_assessment"]["risk_label"]
                    badge_class = "bg-safe" if risk_label == "Safe" else "bg-toxic" if risk_label in ["Toxic", "Ineffective"] else "bg-adjust"
                    
                    st.markdown("### Risk Level")
                    st.markdown(f"<div class='risk-badge {badge_class}'>{risk_label.upper()}</div>", unsafe_allow_html=True)
                    st.metric("AI Confidence Score", f"{report_json['risk_assessment']['confidence_score'] * 100:.1f}%")
                    
                    st.markdown("### Genomic Profile")
                    st.write(f"**Gene:** {report_json['pharmacogenomic_profile']['primary_gene']}")
                    st.write(f"**Diplotype:** {report_json['pharmacogenomic_profile']['diplotype']}")
                    st.write(f"**Phenotype:** {report_json['pharmacogenomic_profile']['phenotype']}")

                with res_col2:
                    st.markdown("### Clinical Explanation (Explainable AI)")
                    st.info(report_json["llm_generated_explanation"]["summary"])
                    
                    with st.expander("Biological Mechanism & Variant Citation", expanded=True):
                        st.write("**Mechanism:**", report_json["llm_generated_explanation"]["biological_mechanism"])
                        st.write("**Citation:**", report_json["llm_generated_explanation"]["variant_citation"])
                        
                    with st.expander("CPIC Dosing Recommendation", expanded=True):
                        st.write("**Action:**", report_json["clinical_recommendation"]["action"])
                        st.write("**Dosage Adjustment:**", report_json["clinical_recommendation"]["dosage_adjustment"])
                        st.write("**Alternative Drugs:**", ", ".join(report_json["clinical_recommendation"]["alternative_drugs"]))

                st.markdown("---")
                
                # --- MANDATORY JSON OUTPUT ---
                st.subheader("Mandatory JSON Schema Output")
                st.json(report_json)
                
                st.download_button(
                    label="Download Official JSON Report",
                    file_name=f"Drugo_{patient_id}.json",
                    mime="application/json",
                    data=json.dumps(report_json, indent=2),
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"System Error: {str(e)}")