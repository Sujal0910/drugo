import os
import json
import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List

# --- STRICT SCHEMA DEFINITIONS ---
# This mathematically forces the LLM to output the EXACT format required to win

class VariantDef(BaseModel):
    rsid: str

class PharmacoProfile(BaseModel):
    primary_gene: str
    diplotype: str
    phenotype: str = Field(description="Must be PM, IM, NM, RM, URM, or Unknown")
    detected_variants: List[VariantDef]

class RiskAssessment(BaseModel):
    risk_label: str = Field(description="Must be Safe, Adjust Dosage, Toxic, Ineffective, or Unknown")
    confidence_score: float
    severity: str = Field(description="Must be none, low, moderate, high, or critical")

class ClinicalRecommendation(BaseModel):
    action: str
    dosage_adjustment: str
    alternative_drugs: List[str]

class LLMExplanation(BaseModel):
    summary: str
    biological_mechanism: str
    variant_citation: str

class QualityMetrics(BaseModel):
    vcf_parsing_success: bool

class PharmaGuardReport(BaseModel):
    patient_id: str
    drug: str
    timestamp: str
    risk_assessment: RiskAssessment
    pharmacogenomic_profile: PharmacoProfile
    clinical_recommendation: ClinicalRecommendation
    llm_generated_explanation: LLMExplanation
    quality_metrics: QualityMetrics

# --- LLM EXECUTION ---
def generate_pharmacogenomic_report(patient_id: str, drug: str, variants: list, target_gene: str, diplotype: str, phenotype: str) -> dict:
    # Pulls your free API key from the .env file
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    
    # gemini-1.5-flash is blazingly fast and free
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Act as an expert Pharmacogenomic AI and Clinical Geneticist.
    Analyze the following patient data according to strict CPIC guidelines.
    
    Patient ID: {patient_id}
    Target Drug: {drug}
    Target Gene: {target_gene}
    Detected Diplotype: {diplotype}
    Phenotype: {phenotype}
    Raw Variants: {json.dumps(variants)}
    
    Generate a precise clinical risk assessment, actionable recommendations, and a detailed biological explanation citing the specific variants. 
    You must output valid JSON strictly conforming to the requested schema.
    """
    
    # Force the LLM to output our exact Pydantic schema
    response = model.generate_content(
        prompt,
        generation_config=genai.GenerationConfig(
            response_mime_type="application/json",
            response_schema=PharmaGuardReport
        )
    )
    
    return json.loads(response.text)