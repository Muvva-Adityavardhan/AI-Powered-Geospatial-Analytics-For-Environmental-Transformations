# map_generator.py
"""
Functions for Google Earth Engine (GEE) initialization and map generation.
"""
import os
import time
import ee
import geemap.foliumap as geemap
import geopandas as gpd

from config import (EE_PROJECT, SHAPEFILE_PATH, DYNAMIC_WORLD_CLASSES, LAND_COVER_LEGEND, LAND_COVER_CAPTION)
from utils import extract_metrics_from_query

# Initialize Earth Engine
try:
    ee.Initialize(project=EE_PROJECT)
except Exception:
    ee.Authenticate()
    ee.Initialize(project=EE_PROJECT)

def generate_map(states, year_dict, query, result_queue):
    try:
        shapefile_path = SHAPEFILE_PATH
        if not os.path.exists(shapefile_path):
            result_queue.put((None, f"Shapefile not found at {shapefile_path}", None))
            return

        gdf = gpd.read_file(shapefile_path)
        gdf["NAME_1"] = gdf["NAME_1"].str.title()
        state_geoms = {}
        for state in states:
            if not state:
                print("Skipping invalid state: None or empty")
                continue
            state_gdf = gdf[gdf["NAME_1"] == state]
            if state_gdf.empty:
                print(f"No geometry found for {state}")
                continue
            state_geoms[state] = ee.Geometry(state_gdf.geometry.iloc[0].__geo_interface__)

        m = geemap.Map(zoom=7, height=400)
        requested_metrics = extract_metrics_from_query(query)
        captions = []
        for state, geom in state_geoms.items():
            boundary = ee.Feature(geom, {"style": {"color": "black", "width": 2}})
            m.addLayer(boundary, {"style": "outline"}, f"{state} Boundary")

            year = year_dict[state][0] if isinstance(year_dict[state], list) else year_dict[state]
            if not year or not isinstance(year, str):
                print(f"Invalid year for {state}: {year}, using default 2024")
                year = "2024"

            start_date = f"{year}-01-01"
            end_date = f"{year}-12-31"
            s2_collection = None
            for attempt in range(3):
                try:
                    s2_collection = (
                        ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
                        .filterBounds(geom)
                        .filterDate(start_date, end_date)
                        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                        .sort("system:time_start", False)
                    )
                    size = s2_collection.size().getInfo()
                    if size > 0:
                        break
                    print(f"Attempt {attempt + 1}: No Sentinel-2 data for {state} {year}")
                    time.sleep(1)
                except Exception as e:
                    if attempt == 2:
                        print(f"Failed to fetch Sentinel-2 for {state} {year}: {str(e)}")
                        s2_collection = None
                        break
                    time.sleep(1)

            if not s2_collection or s2_collection.size().getInfo() == 0:
                print(f"No valid Sentinel-2 data for {state} {year}")
                continue

            s2 = s2_collection.mosaic().clip(geom) if s2_collection.size().getInfo() > 1 else s2_collection.first().clip(geom)
            
            if "NDVI" in requested_metrics:
                ndvi = s2.normalizedDifference(["B8", "B4"]).rename(f"NDVI_{state}")
                m.addLayer(ndvi, {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]}, f"NDVI ({state}, {year})")
            
            if "NBR" in requested_metrics:
                nbr = s2.normalizedDifference(["B8", "B12"]).rename(f"NBR_{state}")
                m.addLayer(nbr, {"min": -1, "max": 1, "palette": ["blue", "white", "red"]}, f"NBR ({state}, {year})")
            
            if "EVI" in requested_metrics:
                nir = s2.select("B8")
                red = s2.select("B4")
                blue = s2.select("B2")
                evi = nir.subtract(red).multiply(2.5).divide(
                    nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)
                ).rename(f"EVI_{state}")
                m.addLayer(evi, {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]}, f"EVI ({state}, {year})")
            
            if "NDMI" in requested_metrics:
                nir = s2.select("B8")
                swir1 = s2.select("B11")
                ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename(f"NDMI_{state}")
                m.addLayer(ndmi, {"min": -1, "max": 1, "palette": ["brown", "white", "blue"]}, f"NDMI ({state}, {year})")
            
            if "MNDWI" in requested_metrics:
                green = s2.select("B3")
                swir1 = s2.select("B11")
                mndwi = green.subtract(swir1).divide(green.add(swir1)).rename(f"MNDWI_{state}")
                m.addLayer(mndwi, {"min": -1, "max": 1, "palette": ["brown", "white", "blue"]}, f"MNDWI ({state}, {year})")
            
            if any(metric in DYNAMIC_WORLD_CLASSES for metric in requested_metrics):
                dw_collection = None
                for attempt in range(3):
                    try:
                        dw_collection = (
                            ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1")
                            .filterBounds(geom)
                            .filterDate(start_date, end_date)
                            .sort("system:time_start", False)
                        )
                        size = dw_collection.size().getInfo()
                        if size > 0:
                            break
                        print(f"Attempt {attempt + 1}: No Dynamic World data for {state} {year}")
                        time.sleep(1)
                    except Exception as e:
                        if attempt == 2:
                            print(f"Failed to fetch Dynamic World for {state} {year}: {str(e)}")
                            dw_collection = None
                            break
                        time.sleep(1)

                if dw_collection and dw_collection.size().getInfo() > 0:
                    land_cover = dw_collection.mosaic().clip(geom).select("label").rename(f"Land_Cover_{state}")
                    land_cover_viz = {
                        "min": 0,
                        "max": 8,
                        "palette": ["419BDF", "397D49", "88B053", "7A87C6", "E49635", "DFC35A", "C4281B", "A59B8F", "B39FE1"]
                    }
                    m.addLayer(land_cover, land_cover_viz, f"Land Cover ({state}, {year})")
                    m.add_legend(**LAND_COVER_LEGEND)
                    captions.append(LAND_COVER_CAPTION)
                else:
                    print(f"No valid Dynamic World data for {state} {year}")

        if state_geoms:
            m.centerObject(next(iter(state_geoms.values())), 7)
            result_queue.put((m, None, captions))
        else:
            result_queue.put((None, "No valid state geometries found", None))
    except Exception as e:
        result_queue.put((None, f"Map generation failed: {str(e)}", None))


def generate_comparative_maps(states, year_dict, query, requested_metrics, result_queue):
    try:
        # Log inputs for debugging
        print(f"Input states: {states}")
        print(f"Input year_dict: {year_dict}")

        # Pre-validate inputs
        valid_states = [s for s in states if s and isinstance(s, str)]
        if not valid_states:
            print("No valid states provided")
            result_queue.put((None, "No valid states provided", None))
            return

        cleaned_year_dict = {}
        for state in valid_states:
            years = year_dict.get(state, ["2024"])
            if not isinstance(years, list):
                years = [years]
            valid_years = []
            for y in years:
                try:
                    if y is None or not str(y).strip():
                        print(f"Skipping invalid year for {state}: {y}")
                        continue
                    y_int = int(y)
                    if 2015 <= y_int <= 2024:
                        valid_years.append(str(y_int))
                    else:
                        print(f"Year {y} out of valid range (2015-2024) for {state}")
                except (ValueError, TypeError):
                    print(f"Invalid year '{y}' for {state}, skipping")
            cleaned_year_dict[state] = sorted(set(valid_years)) if valid_years else ["2024"]
        
        print(f"Cleaned year_dict: {cleaned_year_dict}")

        shapefile_path = SHAPEFILE_PATH
        if not os.path.exists(shapefile_path):
            result_queue.put((None, f"Shapefile not found at {shapefile_path}", None))
            return

        gdf = gpd.read_file(shapefile_path)
        gdf["NAME_1"] = gdf["NAME_1"].str.title()
        state_geoms = {}
        for state in valid_states:
            state_gdf = gdf[gdf["NAME_1"] == state]
            if state_gdf.empty:
                print(f"No geometry found for {state}")
                continue
            state_geoms[state] = ee.Geometry(state_gdf.geometry.iloc[0].__geo_interface__)

        comparative_maps = []
        for state in state_geoms:
            years = cleaned_year_dict.get(state, ["2024"])
            if len(years) < 2:
                print(f"Skipping comparative map for {state}: only {len(years)} year(s) available")
                continue

            for year in years:
                print(f"Processing {state} {year}")
                if not year or not state:
                    print(f"Skipping map generation due to invalid state or year: state={state}, year={year}")
                    continue
                m = geemap.Map(zoom=7, height=400)
                captions = []
                boundary = ee.Feature(state_geoms[state], {"style": {"color": "black", "width": 2}})
                m.addLayer(boundary, {"style": "outline"}, f"{state} Boundary")

                start_date = f"{year}-01-01"
                end_date = f"{year}-12-31"
                s2_collection = None
                for attempt in range(3):
                    try:
                        s2_collection = (
                            ee.ImageCollection("COPERNICUS/S2_HARMONIZED")
                            .filterBounds(state_geoms[state])
                            .filterDate(start_date, end_date)
                            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 30))
                            .sort("system:time_start", False)
                        )
                        size = s2_collection.size().getInfo()
                        if size > 0:
                            break
                        print(f"Attempt {attempt + 1}: No Sentinel-2 data for {state} {year}")
                        time.sleep(1)
                    except Exception as e:
                        if attempt == 2:
                            print(f"Failed to fetch Sentinel-2 for {state} {year}: {str(e)}")
                            s2_collection = None
                            break
                        time.sleep(1)

                if not s2_collection or s2_collection.size().getInfo() == 0:
                    print(f"No valid Sentinel-2 data for {state} {year}")
                    continue

                s2 = s2_collection.mosaic().clip(state_geoms[state]) if s2_collection.size().getInfo() > 1 else s2_collection.first().clip(state_geoms[state])

                if "NDVI" in requested_metrics:
                    ndvi = s2.normalizedDifference(["B8", "B4"]).rename(f"NDVI_{state}_{year}")
                    m.addLayer(ndvi, {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]}, f"NDVI ({state}, {year})")
                if "NBR" in requested_metrics:
                    nbr = s2.normalizedDifference(["B8", "B12"]).rename(f"NBR_{state}_{year}")
                    m.addLayer(nbr, {"min": -1, "max": 1, "palette": ["blue", "white", "red"]}, f"NBR ({state}, {year})")
                if "EVI" in requested_metrics:
                    nir, red, blue = s2.select("B8"), s2.select("B4"), s2.select("B2")
                    evi = nir.subtract(red).multiply(2.5).divide(nir.add(red.multiply(6)).subtract(blue.multiply(7.5)).add(1)).rename(f"EVI_{state}_{year}")
                    m.addLayer(evi, {"min": 0, "max": 1, "palette": ["red", "yellow", "green"]}, f"EVI ({state}, {year})")
                if "NDMI" in requested_metrics:
                    nir, swir1 = s2.select("B8"), s2.select("B11")
                    ndmi = nir.subtract(swir1).divide(nir.add(swir1)).rename(f"NDMI_{state}_{year}")
                    m.addLayer(ndmi, {"min": -1, "max": 1, "palette": ["brown", "white", "blue"]}, f"NDMI ({state}, {year})")
                if "MNDWI" in requested_metrics:
                    green, swir1 = s2.select("B3"), s2.select("B11")
                    mndwi = green.subtract(swir1).divide(green.add(swir1)).rename(f"MNDWI_{state}_{year}")
                    m.addLayer(mndwi, {"min": -1, "max": 1, "palette": ["brown", "white", "blue"]}, f"MNDWI ({state}, {year})")
                if any(metric in DYNAMIC_WORLD_CLASSES for metric in requested_metrics):
                    dw_collection = None
                    for attempt in range(3):
                        try:
                            dw_collection = (ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterBounds(state_geoms[state]).filterDate(start_date, end_date).sort("system:time_start", False))
                            if dw_collection.size().getInfo() > 0: break
                            print(f"Attempt {attempt + 1}: No Dynamic World data for {state} {year}")
                            time.sleep(1)
                        except Exception as e:
                            if attempt == 2:
                                print(f"Failed to fetch Dynamic World for {state} {year}: {str(e)}")
                                dw_collection = None
                                break
                            time.sleep(1)
                    if dw_collection and dw_collection.size().getInfo() > 0:
                        land_cover = dw_collection.mosaic().clip(state_geoms[state]).select("label").rename(f"Land_Cover_{state}_{year}")
                        land_cover_viz = {"min": 0, "max": 8, "palette": ["419BDF", "397D49", "88B053", "7A87C6", "E49635", "DFC35A", "C4281B", "A59B8F", "B39FE1"]}
                        m.addLayer(land_cover, land_cover_viz, f"Land Cover ({state}, {year})")
                        m.add_legend(**LAND_COVER_LEGEND)
                        captions.append(LAND_COVER_CAPTION)
                    else:
                        print(f"No valid Dynamic World data for {state} {year}")
                m.centerObject(state_geoms[state], 7)
                comparative_maps.append({"state": state, "year": year, "map": m, "captions": captions})
                print(f"Generated comparative map for {state} {year}")

        if comparative_maps:
            result_queue.put((comparative_maps, None, None))
        else:
            result_queue.put((None, "No comparative maps generated: insufficient years or data", None))
    except Exception as e:
        result_queue.put((None, f"Comparative map generation failed: {str(e)}", None))
