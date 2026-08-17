import pandas as pd
import json
import requests
import os

# =============================================================================
# CONFIGURATION SECTION
# Replace the placeholders with your actual Shopify store details.
# =============================================================================
SHOP_NAME = "your-store-name.myshopify.com"
API_TOKEN = "shpat_xxxxxxxxxxxxxxxxxxxxxxxx"  # Your Admin API Access Token
EXCEL_FILE = "products.xlsx"                    # Name of your source Excel file
API_VERSION = "2024-04"                         # Supported Shopify API Version
# =============================================================================

# Global Headers for Shopify API Authentication
HEADERS = {
    "X-Shopify-Access-Token": API_TOKEN,
    "Content-Type": "application/json"
}

def excel_to_jsonl(input_file):
    """
    Reads the Excel file and converts each row into a JSONL format 
    compatible with Shopify's Bulk Operation API.
    """
    print(f"📖 Reading {input_file} and preparing data...")
    
    # Load Excel data using pandas
    df = pd.read_excel(input_file)
    output_file = "bulk_data.jsonl"
    
    with open(output_file, "w", encoding="utf-8") as f:
        for _, row in df.iterrows():
            # 1. GENERATE VARIANTS
            # Splits Colors and Sizes from comma-separated strings to create combinations
            colors = str(row['Colors']).split(',') if pd.notna(row['Colors']) else ['Default']
            sizes = str(row['Sizes']).split(',') if pd.notna(row['Sizes']) else ['Default']
            
            variants = []
            for color in colors:
                for size in sizes:
                    variants.append({
                        "options": [color.strip(), size.strip()],
                        "price": str(row['Price']),
                        "sku": f"{row['Handle']}-{color.strip()[:1].upper()}-{size.strip().upper()}"
                    })

            # 2. CONSTRUCT MEDIA ARRAY
            # Maps Image URLs and Video URLs to the correct mediaContentType
            media = []
            if pd.notna(row['Images']):
                for img in str(row['Images']).split(','):
                    media.append({
                        "mediaContentType": "IMAGE", 
                        "originalSource": img.strip()
                    })
            
            if pd.notna(row['Video']):
                media.append({
                    "mediaContentType": "VIDEO", 
                    "originalSource": str(row['Video']).strip()
                })

            # 3. CONSTRUCT THE PRODUCT INPUT OBJECT
            # This follows the 'productCreate' mutation structure
            product_input = {
                "input": {
                    "title": row['Title'],
                    "handle": row['Handle'],
                    "descriptionHtml": row['Long_Description'],
                    "vendor": row['Vendor'],
                    "productType": row['Type'],
                    "tags": str(row['Tags']).split(',') if pd.notna(row['Tags']) else [],
                    "options": ["Color", "Size"],
                    "variants": variants,
                    "metafields": [
                        {
                            "namespace": "custom", 
                            "key": "short_description", 
                            "value": str(row['Short_Description']), 
                            "type": "single_line_text_field"
                        },
                        {
                            "namespace": "custom", 
                            "key": "gender", 
                            "value": str(row['Gender']), 
                            "type": "single_line_text_field"
                        },
                        {
                            "namespace": "custom", 
                            "key": "materials_care", 
                            "value": str(row['Materials_Care']), 
                            "type": "multi_line_text_field"
                        }
                    ],
                    "media": media
                }
            }
            
            # Write the object as a single line in the JSONL file
            f.write(json.dumps(product_input) + "\n")
            
    print(f"✅ Conversion complete: {output_file} created.")
    return output_file

def trigger_bulk_upload(jsonl_file):
    """
    Executes the 3-step process to trigger a Shopify Bulk Operation.
    """
    # STEP 1: Create a Staged Upload URL
    # We ask Shopify for a temporary location to upload our JSONL file.
    staged_query = """
    mutation stagedUploadsCreate($input: [StagedUploadInput!]!) {
      stagedUploadsCreate(input: $input) {
        stagedTargets {
          url
          parameters { name value }
        }
      }
    }
    """
    staged_vars = {
        "input": [{
            "resource": "BULK_MUTATION_VARIABLES",
            "filename": jsonl_file,
            "mimeType": "text/jsonl",
            "httpMethod": "POST"
        }]
    }
    
    print("🛰️ Requesting upload URL from Shopify...")
    response = requests.post(
        f"https://{SHOP_NAME}/admin/api/{API_VERSION}/graphql.json", 
        json={"query": staged_query, "variables": staged_vars}, 
        headers=HEADERS
    )
    
    target_data = response.json()['data']['stagedUploadsCreate']['stagedTargets'][0]
    upload_url = target_data['url']
    params = {p['name']: p['value'] for p in target_data['parameters']}
    
    # STEP 2: Upload the JSONL File
    # We push the actual file to the temporary URL provided by Shopify.
    print("📤 Uploading JSONL file to Shopify's storage...")
    with open(jsonl_file, 'rb') as f:
        upload_response = requests.post(upload_url, data=params, files={'file': f})
    
    if upload_response.status_code != 201:
        print(f"❌ Upload failed with status {upload_response.status_code}")
        return

    # STEP 3: Run the Bulk Mutation
    # We tell Shopify to start processing the uploaded file.
    print("⚡ Triggering the Bulk Mutation engine...")
    bulk_query = """
    mutation bulkOperationRunMutation($mutation: String!, $stagedUploadPath: String!) {
      bulkOperationRunMutation(mutation: $mutation, stagedUploadPath: $stagedUploadPath) {
        bulkOperation { id status }
        userErrors { message }
      }
    }
    """
    
    # The actual mutation Shopify will run for every line in the JSONL
    product_mutation = """
    mutation productCreate($input: ProductInput!) {
      productCreate(input: $input) {
        product { id }
        userErrors { field message }
      }
    }
    """
    
    bulk_vars = {
        "mutation": product_mutation,
        "stagedUploadPath": params['key']
    }
    
    final_response = requests.post(
        f"https://{SHOP_NAME}/admin/api/{API_VERSION}/graphql.json", 
        json={"query": bulk_query, "variables": bulk_vars}, 
        headers=HEADERS
    )
    
    print("🏁 Success! Shopify is now processing your 10,000 products.")
    print("Status:", final_response.json())

# =============================================================================
# MAIN EXECUTION BLOCK
# =============================================================================
if __name__ == "__main__":
    # Check if Excel file exists before starting
    if os.path.exists(EXCEL_FILE):
        # 1. Convert Excel to JSONL
        jsonl_path = excel_to_jsonl(EXCEL_FILE)
        
        # 2. Upload and Trigger
        trigger_bulk_upload(jsonl_path)
    else:
        print(f"❌ File Not Found: Please ensure '{EXCEL_FILE}' is in this folder.")
