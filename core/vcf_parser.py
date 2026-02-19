import re

# The 6 critical genes required by the hackathon
TARGET_GENES = {"CYP2D6", "CYP2C19", "CYP2C9", "SLCO1B1", "TPMT", "DPYD"}

def parse_vcf(file_bytes):
    """
    Parses a VCF file and extracts relevant pharmacogenomic variants.
    """
    # Streamlit passes files as bytes, so we decode them to text
    decoded_file = file_bytes.getvalue().decode("utf-8").splitlines()
    variants = []
    
    for line in decoded_file:
        # Skip VCF header lines
        if line.startswith("#"):
            continue
            
        columns = line.split("\t")
        if len(columns) < 8:
            continue
            
        info_column = columns[7]
        
        # Extract tags using regular expressions
        gene_match = re.search(r'GENE=([^;]+)', info_column)
        star_match = re.search(r'STAR=([^;]+)', info_column)
        rs_match = re.search(r'RS=([^;]+)', info_column)
        
        # Only keep variants that have all three tags and match our target genes
        if gene_match and star_match and rs_match:
            gene = gene_match.group(1).upper()
            if gene in TARGET_GENES:
                variants.append({
                    "gene": gene,
                    "star_allele": star_match.group(1),
                    "rsid": rs_match.group(1),
                    "chromosome": columns[0],
                    "position": columns[1]
                })
                
    return variants

def determine_phenotype(variants, primary_gene):
    """
    Maps the extracted star alleles to a standard CPIC phenotype.
    """
    gene_variants = [v for v in variants if v["gene"] == primary_gene]
    
    if not gene_variants:
        return "*1/*1", "Normal Metabolizer (NM)"
        
    # Grab the first detected star allele and assume heterozygous with *1 for the prototype
    star = gene_variants[0]["star_allele"]
    diplotype = f"*1/{star}"
    
    # CPIC phenotype routing based on common star alleles
    if "2" in star or "3" in star:
        phenotype = "Poor Metabolizer (PM)"
    elif "17" in star:
        phenotype = "Ultrarapid Metabolizer (URM)"
    else:
        phenotype = "Intermediate Metabolizer (IM)"
        
    return diplotype, phenotype