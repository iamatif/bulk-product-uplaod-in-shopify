# Shopify 10k Bulk Product Uploader (GraphQL API)

This tool allows you to upload 10,000+ products to Shopify without using any paid apps. It uses Python to convert Excel data into JSONL and triggers Shopify's **GraphQL Bulk Operations API**.

## 1. File Name: requirements.txt

- **pandas**
- **requests**
- **openpyxl**

## 2. File Name: main.py

- Copy and paste that code of main.py file

## 3: Place your products.xlsx in the same folder as main.py.

**Run the script:**
- Bash
- python main.py

## ✨ Features
- **Auto-Variants:** Creates combinations of Colors & Sizes automatically.
- **Media Support:** Handles multiple Images and Video URLs.
- **Metafields:** Syncs Short Description, Gender, and Materials.
- **HTML Friendly:** Supports complex product descriptions.

## 🛠️ Setup
1. **API Key:** Create a Custom App in Shopify Admin > Settings > Apps > Develop Apps. 
2. **Permissions:** Grant `write_products`, `write_files`, and `write_metafields`.
3. **Token:** Copy the Admin API Access Token into `main.py`.

## 📦 How to Use
1. Prepare `products.xlsx` with columns: `Title, Handle, Long_Description, Vendor, Type, Tags, Colors, Sizes, Price, Images, Video, Short_Description, Gender, Materials_Care`.
2. Install dependencies: `pip install pandas requests openpyxl`.
3. Run: `python main.py`.

## ⚠️ Limits
Shopify throttles uploads to 1,000 variants per 24h once you hit 50k total variants.


