import os
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import folium
from folium.plugins import MarkerCluster

# Paths
PROCESSED_DIR = os.path.join("data", "processed")
CSV_PATH = os.path.join(PROCESSED_DIR, "nh58_features.csv")
GEOJSON_PATH = os.path.join(PROCESSED_DIR, "nh58_segments_features.geojson")
LANDSLIDE_PATH = os.path.join("data", "raw", "landslide_inventory.geojson")

EDA_MAP_PATH = os.path.join(PROCESSED_DIR, "nh58_eda_map.html")

def analyze_tabular_features():
    print("\n=======================================================")
    print("      DATA STORY: NH-58 HIGHWAY CORRIDOR FEATURES      ")
    print("=======================================================")
    
    df = pd.read_csv(CSV_PATH)
    
    print(f"\n1. CORRIDOR OVERVIEW:")
    print(f"   • Total Analyzed Road Segments : {len(df)}")
    print(f"   • Corridor Coverage Length     : {len(df) * 0.5:.1f} km")
    
    print(f"\n2. TOPOGRAPHIC ELEVATION & SLOPE SUMMARY:")
    print(f"   • Elevation Range              : {df['mean_elevation_m'].min():.1f}m to {df['mean_elevation_m'].max():.1f}m")
    print(f"   • Average Corridor Slope       : {df['mean_slope_deg'].mean():.1f}°")
    print(f"   • Maximum Observed Slope       : {df['max_slope_deg'].max():.1f}°")
    
    # Identify high-risk segments based on slope criteria (>35 degrees)
    steep_segments = df[df['max_slope_deg'] >= 35.0]
    print(f"\n3. HIGH-HAZARD GEOMORPHIC STEEP ZONES:")
    print(f"   • Segments with Slope >= 35°   : {len(steep_segments)} of {len(df)} ({len(steep_segments)/len(df)*100:.1f}%)")
    
    # Identify segments close to historic landslide zones (<1000 meters)
    near_slides = df[df['dist_to_landslide_m'] <= 1000.0]
    print(f"\n4. HISTORIC PROXIMITY HAZARD ZONES:")
    print(f"   • Segments within 1km of Slides: {len(near_slides)} of {len(df)} ({len(near_slides)/len(df)*100:.1f}%)")
    
    # Print Top 5 Most Topographically Vulnerable Segments
    print(f"\n5. TOP 5 MOST VULNERABLE ROAD SEGMENTS (Highest Slope & Closest to Known Slides):")
    vulnerable = df.sort_values(by=['dist_to_landslide_m', 'max_slope_deg'], ascending=[True, False]).head(5)
    for idx, row in vulnerable.iterrows():
        print(f"   • [{row['segment_id']}] Elev: {row['mean_elevation_m']}m | Mean Slope: {row['mean_slope_deg']}° | Max Slope: {row['max_slope_deg']}° | Dist to Landslide: {row['dist_to_landslide_m']}m")
        
    print("=======================================================\n")

def generate_interactive_eda_map():
    print("[1/2] Loading spatial GeoJSON data for interactive map...")
    gdf_segments = gpd.read_file(GEOJSON_PATH)
    gdf_landslides = gpd.read_file(LANDSLIDE_PATH)
    
    # Calculate center point for initial map view (Rudraprayag / Karnaprayag corridor center)
    center_lat = 30.28
    center_lon = 79.15
    
    # Create Folium Map with Satellite OpenStreetMap tile layers
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")
    
    # Add alternative CartoDB dark layer for high-contrast geospatial visualization
    folium.TileLayer('CartoDB dark_matter', name="Dark Mode Map").add_to(m)
    
    print("[2/2] Color-coding road segments by topographic slope severity...")
    
    # Function to color-code road segments based on max slope angle
    def get_color(slope):
        if slope >= 38.0:
            return '#dc2626'  # Dark Red (Extreme Slope)
        elif slope >= 30.0:
            return '#f59e0b'  # Orange (Moderate-High Slope)
        elif slope >= 22.0:
            return '#eab308'  # Yellow (Moderate Slope)
        else:
            return '#16a34a'  # Green (Gentle Slope)

    # Plot Each 500m Road Segment on Map
    for _, row in gdf_segments.iterrows():
        geom = row['geometry']
        max_slope = row['max_slope_deg']
        seg_id = row['segment_id']
        elev = row['mean_elevation_m']
        dist_slide = row['dist_to_landslide_m']
        dist_river = row['dist_to_river_m']
        
        color = get_color(max_slope)
        
        # Convert Shapely LineString geometry to lat/lon list for Folium
        coords = [(pt[1], pt[0]) for pt in geom.coords]
        
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; width: 220px;">
            <h4 style="margin:0 0 8px 0; color:#1e293b;">{seg_id}</h4>
            <table style="width:100%; font-size:12px; border-collapse:collapse;">
                <tr><td><b>Elevation:</b></td><td>{elev} m</td></tr>
                <tr><td><b>Mean Slope:</b></td><td>{row['mean_slope_deg']}°</td></tr>
                <tr><td><b>Max Slope:</b></td><td><b>{max_slope}°</b></td></tr>
                <tr><td><b>Dist to River:</b></td><td>{dist_river} m</td></tr>
                <tr><td><b>Dist to Slide:</b></td><td>{dist_slide} m</td></tr>
            </table>
        </div>
        """
        
        folium.PolyLine(
            locations=coords,
            weight=6,
            color=color,
            opacity=0.85,
            popup=folium.Popup(popup_html, max_width=250),
            tooltip=f"{seg_id} (Max Slope: {max_slope}°)"
        ).add_to(m)
        
    # Plot Historic Landslide Marker Points
    landslide_group = folium.FeatureGroup(name="Historic Landslide Sites").add_to(m)
    for _, row in gdf_landslides.iterrows():
        point = row['geometry']
        loc_name = row.get('location', 'Historic Landslide Site')
        label = row.get('label', 1)
        
        if label == 1:
            folium.Marker(
                location=[point.y, point.x],
                popup=f"<b>Slide Zone:</b> {loc_name}",
                tooltip=f"Slide Zone: {loc_name}",
                icon=folium.Icon(color="red", icon="warning-sign")
            ).add_to(landslide_group)
            
    folium.LayerControl().add_to(m)
    
    m.save(EDA_MAP_PATH)
    print(f" Generated Interactive EDA Web Map: {EDA_MAP_PATH}")
    print("   (Double-click or open this HTML file in your web browser to explore your data!)")

if __name__ == "__main__":
    analyze_tabular_features()
    generate_interactive_eda_map()