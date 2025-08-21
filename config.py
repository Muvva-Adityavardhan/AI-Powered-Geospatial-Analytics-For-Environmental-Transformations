# config.py
"""
Central configuration file for constants, API keys, file paths, and legends.
"""
import os
from dotenv import load_dotenv

load_dotenv()

# --- API Keys and Project Configuration ---
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
MISTRAL_API_URL = os.getenv("MISTRAL_API_URL")
EE_PROJECT = os.getenv("EE_PROJECT") 


# --- File and Folder Paths ---
CORPUS_FOLDER = "./CORPUS"
SHAPEFILE_PATH = "./SHAPE/gadm41_IND_1.shp"

# --- State to Corpus File Mapping ---
state_corpus_files = {
    "Andhra Pradesh": "Andhra Pradesh_training_corpus.txt",
    "Arunachal Pradesh": "Arunachal Pradesh_training_corpus.txt",
    "Assam": "Assam_training_corpus.txt",
    "Bihar": "Bihar_training_corpus.txt",
    "Chhattisgarh": "Chhattisgarh_training_corpus.txt",
    "Goa": "Goa_training_corpus.txt",
    "Gujarat": "Gujarat_training_corpus.txt",
    "Haryana": "Haryana_training_corpus.txt",
    "Himachal Pradesh": "Himachal Pradesh_training_corpus.txt",
    "Jharkhand": "Jharkhand_training_corpus.txt",
    "Karnataka": "Karnataka_training_corpus.txt",
    "Kerala": "Kerala_training_corpus.txt",
    "Madhya Pradesh": "Madhya Pradesh_training_corpus.txt",
    "Maharashtra": "Maharashtra_training_corpus.txt",
    "Manipur": "Manipur_training_corpus.txt",
    "Meghalaya": "Meghalaya_training_corpus.txt",
    "Mizoram": "Mizoram_training_corpus.txt",
    "Nagaland": "Nagaland_training_corpus.txt",
    "Odisha": "Odisha_training_corpus.txt",
    "Punjab": "Punjab_training_corpus.txt",
    "Rajasthan": "Rajasthan_training_corpus.txt",
    "Sikkim": "Sikkim_training_corpus.txt",
    "Tamil Nadu": "Tamil Nadu_training_corpus.txt",
    "Telangana": "Telangana_training_corpus.txt",
    "Tripura": "Tripura_training_corpus.txt",
    "Uttar Pradesh": "Uttar Pradesh_training_corpus.txt",
    "Uttarakhand": "Uttarakhand_training_corpus.txt",
    "West Bengal": "West Bengal_training_corpus.txt"
}

# --- Data Constants ---
DYNAMIC_WORLD_CLASSES = [
    "water", "trees", "grass", "flooded_vegetation", "crops",
    "shrub_and_scrub", "built", "bare", "snow_and_ice"
]

# --- Legend and Caption Definitions ---
LAND_COVER_LEGEND = {
    "title": "Land Cover Classes",
    "labels": ["Water", "Trees", "Grass", "Flooded Vegetation", "Crops", "Shrub and Scrub", "Built", "Bare", "Snow and Ice"],
    "colors": ["#419BDF", "#397D49", "#88B053", "#7A87C6", "#E49635", "#DFC35A", "#C4281B", "#A59B8F", "#B39FE1"]
}
LAND_COVER_CAPTION = (
    "Land Cover Color Mapping:\n- Blue (#419BDF): Water\n- Dark Green (#397D49): Trees\n- Light Green (#88B053): Grass\n- Purple (#7A87C6): Flooded Vegetation\n- Orange (#E49635): Crops\n- Yellow (#DFC35A): Shrub and Scrub\n- Red (#C4281B): Built\n- Gray (#A59B8F): Bare\n- Light Purple (#B39FE1): Snow and Ice"
)
NDVI_LEGEND = { "title": "NDVI (Vegetation Index)", "labels": ["Low (< 0.3)", "Moderate (0.3–0.6)", "High (> 0.6)"], "colors": ["red", "yellow", "green"] }
NDVI_CAPTION = ( "NDVI Color Mapping:\n- Red: Low NDVI (< 0.3)\n- Yellow: Moderate NDVI (0.3–0.6)\n- Green: High NDVI (> 0.6)" )
EVI_LEGEND = { "title": "EVI (Enhanced Vegetation Index)", "labels": ["Low (< 0.3)", "Moderate (0.3–0.6)", "High (> 0.6)"], "colors": ["red", "yellow", "green"] }
EVI_CAPTION = ( "EVI Color Mapping:\n- Red: Low EVI (< 0.3)\n- Yellow: Moderate EVI (0.3–0.6)\n- Green: High EVI (> 0.6)" )
NBR_LEGEND = { "title": "NBR (Burn Ratio)", "labels": ["Low (< -0.3)", "Neutral (-0.3 to 0.3)", "High (> 0.3)"], "colors": ["red", "white", "blue"] }
NBR_CAPTION = ( "NBR Color Mapping:\n- Red: Low NBR (< -0.3)\n- White: Neutral NBR (-0.3 to 0.3)\n- Blue: High NBR (> 0.3)" )
NDMI_LEGEND = { "title": "NDMI (Moisture Index)", "labels": ["Low (< -0.2)", "Neutral (-0.2 to 0.2)", "High (> 0.2)"], "colors": ["brown", "white", "blue"] }
NDMI_CAPTION = ( "NDMI Color Mapping:\n- Brown: Low NDMI (< -0.2)\n- White: Neutral NDMI (-0.2 to 0.2)\n- Blue: High NDMI (> 0.2)" )
MNDWI_LEGEND = { "title": "MNDWI (Water Index)", "labels": ["Low (< -0.2)", "Neutral (-0.2 to 0.2)", "High (> 0.2)"], "colors": ["brown", "white", "blue"] }
MNDWI_CAPTION = ( "MNDWI Color Mapping:\n- Brown: Low MNDWI (< -0.2)\n- White: Neutral MNDWI (-0.2 to 0.2)\n- Blue: High MNDWI (> 0.2)" )
