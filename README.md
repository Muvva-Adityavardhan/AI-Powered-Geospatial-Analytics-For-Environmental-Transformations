# AI-Powered-Geospatial-Analytics-for-Environmental-Transformations

📖 If you use this project in your research, please cite it as described in the [CITATION.cff](CITATION.cff) file.

This repository contains the source code for a Mini Project developed. The project, titled **"AI-Powered Geospatial Analytics for Environmental Transformations"**, integrates advanced large language models (LLMs) like Mistral-saba and Gemini with Google Earth Engine (GEE) to monitor and analyze environmental changes across India from 2015 to 2025.

The system enables users to query environmental metrics (e.g., NDVI, NBR, EVI, MNDWI, land cover) in natural language, generating detailed reports, interactive visualizations (bar charts, pie charts, line graphs), and geospatial maps. Built with a Streamlit-based web interface, it democratizes access to geospatial insights for researchers, policymakers, and environmentalists without requiring GIS expertise.

---

## Table of Contents
- [Project Overview](#project-overview)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Results](#results)
- [System Architecture](#system-architecture)
- [Installation](#installation)
- [Usage](#usage)

---

## Project Overview
India faces rapid environmental changes due to urbanization, industrial growth, and climate phenomena. Traditional GIS tools, while powerful, are often manual, time-consuming, and require specialized knowledge. This project addresses these challenges by developing an intelligent, scalable, and user-friendly platform that combines:
- **Natural Language Processing (NLP)**: Powered by Mistral-saba for data retrieval and Gemini for generating detailed analytical reports.
- **Geospatial Analysis**: Leverages Google Earth Engine to process Sentinel-2 and Dynamic World datasets for environmental metrics.
- **Visualization**: Automatically generates interactive charts (using Plotly) and geospatial maps (via GEE).
- **User Interface**: A Streamlit-based web app with a conversational chatbot, supporting light/dark themes and chat history persistence.

The system processes queries like "How has forest cover evolved in Telangana over the past five years?" or "Compare land cover changes in Kerala and Telangana in 2023," delivering actionable insights through reports, graphs, and maps.

---

## Features
- **Natural Language Queries**: Users can input queries in plain English (e.g., "Land cover for Kerala 2023").
- **Environmental Metrics**: Supports NDVI, NBR, EVI, NDMI, MNDWI, and land cover classification.
- **Data Sources**: Integrates Sentinel-2 imagery and Dynamic World datasets via Google Earth Engine.
- **Visualizations**: Generates bar charts, pie charts, and line graphs using Plotly for temporal and spatial trends.
- **Geospatial Maps**: Produces interactive maps with dynamic layers for metrics like vegetation, water, and land cover.
- **Scalable Architecture**: Handles multi-state, multi-year queries with robust error handling and retry mechanisms.
- **User-Friendly Interface**: Streamlit-based UI with a chatbot, theme customization, and chat history management.
- **No Fine-Tuning Required**: Leverages pre-trained LLMs for efficient deployment.

---

## Technologies Used
- **Programming Language**: Python
- **Libraries**:
  - Geospatial: `ee` (Google Earth Engine), `geemap`, `geopandas`
  - Data Processing: `numpy`, `pandas`
  - Visualization: `plotly`
  - Web Framework: `streamlit`
  - API Interaction: `requests`
  - Concurrency: `threading`, `queue`
- **APIs**:
  - Mistral-saba API (for data retrieval)
  - Google Generative AI (Gemini) API (for report generation)
- **IDEs**: Visual Studio Code, Google Colab, Jupyter Notebook
- **Datasets**:
  - Sentinel-2 (COPERNICUS/S2_HARMONIZED)
  - Dynamic World (GOOGLE/DYNAMICWORLD/V1)
  - GADM shapefiles for Indian state boundaries
- **Hardware Requirements**:
  - Processor: i5 or above
  - RAM: Minimum 8GB
  - Stable internet connection (10 Mbps or higher)

---

## Results

The system was tested with various queries to validate its functionality and accuracy in processing environmental data. Below are key results showcasing the system's ability to generate textual reports, interactive visualizations, and geospatial maps:

- **Chatbot Interface**: The Streamlit-based UI provides a conversational chatbot for users to input natural language queries and view responses, including reports and visualizations.  
  ![Chatbot UI](screenshots/chatbot_ui.png)

- **Generated Report**: Comprehensive textual reports are generated using the Gemini API, summarizing environmental metrics like NDVI, NBR, or land cover for user-specified states and years.  
  ![Generated Report](screenshots/generated_report.png)

- **GEE Maps**: Interactive maps from Google Earth Engine display environmental metrics (e.g., NDVI, MNDWI) and land cover classifications, clipped to state boundaries.  
  ![GEE Map](screenshots/gee_map.png)
  ![Land Cover Classification](screenshots/land_cover_classification.png)

- **Visualizations**: The system produces interactive Plotly charts, including bar graphs, pie charts, and line graphs, to illustrate trends and distributions of environmental metrics.  
  ![Bar Graph](screenshots/bar_graph.png)
  ![Pie Chart](screenshots/pie_chart.png)
  ![Line Graph](screenshots/line_graph.png)

These results demonstrate the system's capability to handle complex queries, deliver actionable insights, and visualize geospatial data effectively.

---

## System Architecture
The application follows a modular, multi-stage architecture to process user requests:
1.  **UI Layer (Streamlit)**: Captures user input via a chat interface.
2.  **Parsing & Orchestration**: The main `main.py` module uses utility functions to extract keywords (states, years, metrics) from the query.
3.  **Data Retrieval (Mistral)**: A call is made to the Mistral-saba API to parse numerical data from the pre-compiled text-based `CORPUS` files.
4.  **Report Generation (Gemini)**: The extracted data is sent to the Gemini API to generate a qualitative, descriptive report.
5.  **Visualization (Plotly)**: The numerical data is used to create interactive charts.
6.  **Mapping (GEE)**: A separate thread generates geospatial maps using Google Earth Engine, ensuring the UI remains responsive.

---

## Installation
Follow these steps to set up the project locally.

### 1. Prerequisites
- Python 3.8 or higher.
- A Google account authenticated with Google Earth Engine.
- API keys for **Mistral** and **Google AI (Gemini)**.

### 2. Clone the Repository
Clone this repository to your local machine.
```bash
git clone https://github.com/Muvva-Adityavardhan/AI-Powered-Geospatial-Analytics-For-Environmental-Transformations.git
cd AI-Powered-Geospatial-Analytics-for-Environmental-Transformations
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
You need to provide your secret API keys to the application.

- Create a file named `.env` in the root directory of the project.
- Add your API keys to this file in the following format:

```plaintext
# .env file
MISTRAL_API_KEY="your_mistral_api_key_here"
GEMINI_API_KEY="your_gemini_api_key_here"
MISTRAL_API_URL="your_mistral_api_url_here"
EE-PROJECT="your_gee_project_id"
```

### 5. Google Earth Engine Authentication
The first time you run the application, you may need to authenticate with Google Earth Engine. Run the following command in your terminal and follow the on-screen instructions to sign in with your Google account.
```bash
earthengine authenticate
```

## Usage
Once the installation is complete, you can run the Streamlit application with a single command:
```bash
streamlit run main.py
```

## 📫 Feel Free to Contact Me
I would love to listen to your ideas...
[![LinkedIn](https://img.shields.io/badge/LinkedIn-blue?style=flat&logo=linkedin)](https://www.linkedin.com/in/madityavardhan/)
