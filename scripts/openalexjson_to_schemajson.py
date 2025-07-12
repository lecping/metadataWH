import json
import os
import shutil
from pathlib import Path
from typing import Dict, Any, List

def transform_to_schemaorg(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Transform OpenAlex work object to schema.org ScholarlyArticle format."""
    try:
        schema = {
            "@context": "https://schema.org",
            "@type": "ScholarlyArticle",
            "identifier": input_data["id"],
            "doi": input_data["doi"].replace("https://doi.org/", "") if input_data.get("doi") else None,
            "name": input_data["title"],
            "headline": input_data["display_name"],
            "datePublished": input_data["publication_date"],
            "copyrightYear": input_data["publication_year"],
            "inLanguage": input_data["language"],
            "isAccessibleForFree": input_data["open_access"]["is_oa"],
            "license": input_data["primary_location"]["license"] if input_data["primary_location"].get("license") else None,
            "isPartOf": {
                "@type": "Periodical",
                "name": input_data["primary_location"]["source"]["display_name"],
                "issn": input_data["primary_location"]["source"]["issn_l"],
                "publisher": {
                    "@type": "Organization",
                    "name": input_data["primary_location"]["source"]["host_organization_name"]
                }
            },
            "author": get_authors_info(input_data["authorships"]),
            "citationCount": input_data["cited_by_count"],
            "citation": [ref for ref in input_data["referenced_works"]],
            "funding": get_funding_info(input_data),
            "keywords": input_data.get("keywords", []),
            "about": get_concepts_info(input_data["concepts"]),
            "abstract": reconstruct_abstract(input_data.get("abstract_inverted_index")),
            "url": input_data["primary_location"]["landing_page_url"]
        }
        
        if input_data["open_access"]["is_oa"]:
            schema["encoding"] = {
                "@type": "MediaObject",
                "contentUrl": input_data["open_access"]["oa_url"],
                "encodingFormat": "text/html"
            }
        
        return {k: v for k, v in schema.items() if v is not None}
    except Exception as e:
        raise ValueError(f"Transformation failed: {str(e)}")

def get_authors_info(authorships: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform author information to schema.org format."""
    authors = []
    for author_data in authorships:
        author = {
            "@type": "Person",
            "identifier": author_data["author"]["id"],
            "name": author_data["author"]["display_name"],
            "givenName": author_data["raw_author_name"].split()[0],  # Simple extraction
            "familyName": author_data["raw_author_name"].split()[-1],  # Simple extraction
            "affiliation": get_affiliations_info(author_data["institutions"]),
            "sameAs": author_data["author"]["orcid"]
        }
        authors.append({k: v for k, v in author.items() if v is not None})
    return authors

def get_affiliations_info(institutions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform institution information to schema.org format."""
    return [
        {
            "@type": "Organization",
            "identifier": inst["id"],
            "name": inst["display_name"],
            "address": {
                "@type": "PostalAddress",
                "addressCountry": inst["country_code"]
            }
        }
        for inst in institutions
    ]

def get_concepts_info(concepts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Transform concepts to schema.org about property."""
    return [
        {
            "@type": "Thing",
            "identifier": concept["id"],
            "name": concept["display_name"],
            "sameAs": concept["wikidata"]
        }
        for concept in concepts
    ]

def get_funding_info(work_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract funding information if available."""
    if work_data.get("apc_paid"):
        return {
            "@type": "MonetaryGrant",
            "amount": {
                "@type": "MonetaryAmount",
                "value": work_data["apc_paid"]["value"],
                "currency": work_data["apc_paid"]["currency"]
            },
            "name": "Article Processing Charge"
        }
    return None

def reconstruct_abstract(inverted_index: Dict[str, Any]) -> str:
    """Reconstruct abstract from inverted index if available."""
    if not inverted_index:
        return None
    
    # Flatten the inverted index into words with their positions
    words = {}
    for word, positions in inverted_index.items():
        for pos in positions:
            words[pos] = word
    
    # Reconstruct the abstract in order
    if words:
        max_pos = max(words.keys())
        abstract = []
        for i in range(max_pos + 1):
            if i in words:
                abstract.append(words[i])
        return ' '.join(abstract)
    return None

def quarantine_file(input_path: str, quarantine_root: str, relative_path: str):
    """Move problematic file to quarantine folder maintaining structure."""
    quarantine_path = os.path.join(quarantine_root, relative_path)
    Path(quarantine_path).mkdir(parents=True, exist_ok=True)
    
    try:
        shutil.copy2(input_path, quarantine_path)
        print(f"Quarantined: {input_path} -> {quarantine_path}")
    except Exception as e:
        print(f"Failed to quarantine {input_path}: {str(e)}")

def process_all_json_files(input_root: str, output_root: str, quarantine_root: str):
    """
    Process all JSON files with quarantine functionality.
    """
    # Create root directories if they don't exist
    Path(output_root).mkdir(parents=True, exist_ok=True)
    Path(quarantine_root).mkdir(parents=True, exist_ok=True)
    
    for root, dirs, files in os.walk(input_root):
        relative_path = os.path.relpath(root, input_root)
        
        # Create corresponding output directory
        output_dir = os.path.join(output_root, relative_path)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        for filename in files:
            if filename.endswith('.json'):
                input_path = os.path.join(root, filename)
                output_path = os.path.join(output_dir, filename)
                
                try:
                    # Read and transform file
                    with open(input_path, 'r', encoding='utf-8') as f:
                        input_data = json.load(f)
                    
                    output_data = transform_to_schemaorg(input_data)
                    
                    # Write transformed file
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False)
                    
                    print(f"Processed: {input_path} -> {output_path}")
                
                except Exception as e:
                    print(f"Error processing {input_path}: {str(e)}")
                    # Copy to quarantine while maintaining folder structure
                    quarantine_file(input_path, quarantine_root, relative_path)

if __name__ == "__main__":
    # Configure your paths here
    import os
    input_root = os.path.abspath("../dataset/openalex")
    output_root = os.path.abspath("../dataset/schemaoutput")
    quarantine_root = os.path.abspath("../dataset/openalex_quarantine")
    #input_root = "C:/Users/lecpi/openalex"  
    #output_root = "C:/Users/lecpi/schemaoutput"
    #quarantine_root = "C:/Users/lecpi/openalex_quarantine" 
    
    # Process all files
    process_all_json_files(input_root, output_root, quarantine_root)
    print("Processing complete!")
    print(f"Output files in: {output_root}")
    print(f"Problematic files quarantined in: {quarantine_root}")