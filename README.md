# 🧬 Drugoo
**AI-Powered Pharmacogenomic Risk Intelligence**
*Built for the RIFT 2026 Hackathon (HealthTech Track)*

![Python](https://img.shields.io/badge/Python-3.11%2B-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-Native_UI-FF4B4B)
![Gemini AI](https://img.shields.io/badge/Gemini_2.5_Flash-Explainable_AI-8E75B2)



## 📌 The Problem
Adverse drug reactions (ADRs) are a leading cause of death globally. Standardized "one-size-fits-all" prescribing ignores critical patient-specific genetic variations in drug metabolism. While genomic data (VCF files) exists, clinicians lack rapid, automated tools to translate complex variants into actionable, bedside dosing decisions.

## 💡 The Solution: Drugoo
Drugoo is a full-stack precision medicine application that acts as a digital clinical geneticist. By ingesting raw patient genomic data (VCF v4.2 files), Drugoo cross-references the patient's diplotype against CPIC (Clinical Pharmacogenetics Implementation Consortium) guidelines and uses Google's Gemini AI to generate an explainable, risk-stratified clinical dashboard in seconds.

## 🚀 Features
* **Automated VCF Parsing:** Instantly extracts high-impact pharmacogenomic variants (`GENE`, `STAR`, `RS` tags) for the 6 most critical genes (CYP2D6, CYP2C19, CYP2C9, SLCO1B1, TPMT, DPYD).
* **Explainable AI Engine:** Forces Gemini 2.5 Flash using Pydantic Structured Outputs to return strict JSON, summarizing the exact biological mechanism behind the drug-gene interaction.
* **💬 AI Clinical Copilot:** A context-aware chatbot built into the dashboard allowing clinicians to ask real-time follow-up questions about the patient's specific metabolic profile.
* **🔗 Live dbSNP Evidence:** Automatically links detected patient variants (rsIDs) directly to the NIH dbSNP database for instant clinical verification.
* **Dynamic Risk Stratification:** Translates complex diplotypes into visual, color-coded clinical labels (Safe, Adjust Dosage, Toxic, Ineffective) accompanied by a dynamic Plotly confidence gauge.
* **Batch Processing:** Evaluate multiple high-risk medications simultaneously (e.g., Codeine, Warfarin, Clopidogrel, Simvastatin) against the patient's genome.

## 🛠️ Technical Architecture
* **Frontend:** Streamlit with native custom theming (`config.toml`) for a premium, responsive dark-mode UI.
* **Backend:** Python-based genomic parser and CPIC rule-matching engine.
* **AI Engine:** Google Generative AI SDK (Gemini 2.5 Flash).
* **Data Visualization:** Plotly Graph Objects.
* **Deployment:** Streamlit Community Cloud.

## 💻 Running Locally

### 1. Clone the Repository
```bash
git clone [https://github.com/YourUsername/drugoo.git](https://github.com/YourUsername/drugoo.git)
cd drugoo
