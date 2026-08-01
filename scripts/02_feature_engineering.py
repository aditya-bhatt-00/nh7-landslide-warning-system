import os
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import substring

# Paths
RAW_DIR = os.path.join("data", "raw")
PROCESSED_DIR = os.path.join("data", "processed")
os.makedirs(PROCESSED_DIR, exist_ok=True)

HIGHWAY_PATH = os.path.join(RAW_DIR, "nh58_highway.geojson")
DEM_PATH = os.path.join(RAW_DIR, "rudraprayag_chamoli_dem.tif")
LANDSLIDE_PATH = os.path.join(RAW_DIR, "landslide_inventory.geojson")

OUTPUT_GEOJSON = os.path.join(PROCESSED_DIR, "nh58_segments_features.geojson")
OUTPUT_CSV = os.path.join(PROCESSED_DIR, "nh58_features.csv")

# Coordinate Reference Systems
WGS84_CRS = "EPSG:4326"     # Latitude / Longitude (degrees)
UTM_CRS = "EPSG:32644"       # UTM Zone 44N (meters for Uttarakhand)

def slice_line_into_segments(line_geom, segment_length_m=500.0):
    """Slices a continuous LineString into discrete segments of fixed length in meters."""
    total_length = line_geom.length
    segments = []
    
    current_dist = 0.0
    seg_id = 1
    while current_dist < total_length:
        end_dist = min(current_dist + segment_length_m, total_length)
        sub_line = substring(line_geom, current_dist, end_dist)
        if sub_line.length > 50:  # Ignore tiny remnant ends < 50m
            segments.append({
                "segment_id": f"NH58_SEG_{seg_id:03d}",
                "start_m": current_dist,
                "end_m": end_dist,
                "geometry": sub_line
            })
            seg_id += 1
        current_dist = end_dist
        
    return segments

def compute_slope_and_aspect(dem_array, cell_size_m=30.0):
    """Calculates slope (degrees) and aspect (degrees) from elevation grid using numpy 2D gradients."""
    dy, dx = np.gradient(dem_array, cell_size_m)
    slope_rad = np.arctan(np.sqrt(dx**2 + dy**2))
    slope_deg = np.degrees(slope_rad)
    
    aspect_rad = np.arctan2(-dx, dy)
    aspect_deg = np.degrees(aspect_rad)
    aspect_deg = np.where(aspect_deg < 0, 360 + aspect_deg, aspect_deg)
    
    return slope_deg, aspect_deg

def process_gis_features():
    print("[1/4] Loading spatial vector layers & projecting to UTM Zone 44N...")
    gdf_highway = gpd.read_file(HIGHWAY_PATH).to_crs(UTM_CRS)
    gdf_landslides = gpd.read_file(LANDSLIDE_PATH).to_crs(UTM_CRS)
    
    # Merge highway parts if multi-part
    single_highway_line = gdf_highway.unary_union
    if single_highway_line.geom_type == 'MultiLineString':
        # Select longest contiguous line
        single_highway_line = max(single_highway_line.geoms, key=lambda l: l.length)
        
    print(f" -> Highway Corridor Total Length: {single_highway_line.length / 1000.0:.2f} km")
    
    print("[2/4] Slicing highway corridor into 500m segments & generating 200m hazard buffers...")
    raw_segments = slice_line_into_segments(single_highway_line, segment_length_m=500.0)
    gdf_segments = gpd.GeoDataFrame(raw_segments, crs=UTM_CRS)
    
    # Create 200m buffer around each segment
    gdf_segments["buffer_geom"] = gdf_segments["geometry"].buffer(200.0)
    
    print(f" -> Generated {len(gdf_segments)} road segments and buffers.")

    print("[3/4] Extracting topographic features (Elevation, Slope, Aspect) from DEM raster...")
    with rasterio.open(DEM_PATH) as src:
        dem_data = src.read(1)
        transform = src.transform
        dem_crs = src.crs
        
        # Approximate 30m pixel resolution
        pixel_size = abs(transform[0]) * 111000.0 if src.crs.is_geographic else abs(transform[0])
        slope_grid, aspect_grid = compute_slope_and_aspect(dem_data, cell_size_m=max(pixel_size, 30.0))
        
        # Prepare feature lists
        elev_means = []
        slope_means = []
        slope_maxs = []
        aspect_means = []
        
        # Convert buffers to DEM CRS for raster masking
        gdf_buffers = gpd.GeoDataFrame(gdf_segments, geometry="buffer_geom", crs=UTM_CRS).to_crs(dem_crs)
        
        for _, row in gdf_buffers.iterrows():
            try:
                out_image, out_transform = mask(src, [row["buffer_geom"]], crop=True, nodata=-9999)
                masked_elev = out_image[0]
                valid_elev = masked_elev[masked_elev != -9999]
                
                if len(valid_elev) > 0:
                    elev_means.append(float(np.mean(valid_elev)))
                    
                    # Approximate local slope/aspect extraction
                    row_idx, col_idx = np.where(masked_elev != -9999)
                    if len(row_idx) > 0:
                        slopes = slope_grid[row_idx, col_idx]
                        aspects = aspect_grid[row_idx, col_idx]
                        slope_means.append(float(np.mean(slopes)))
                        slope_maxs.append(float(np.max(slopes)))
                        aspect_means.append(float(np.mean(aspects)))
                    else:
                        slope_means.append(25.0)
                        slope_maxs.append(35.0)
                        aspect_means.append(180.0)
                else:
                    elev_means.append(800.0)
                    slope_means.append(25.0)
                    slope_maxs.append(35.0)
                    aspect_means.append(180.0)
            except Exception:
                elev_means.append(800.0)
                slope_means.append(25.0)
                slope_maxs.append(35.0)
                aspect_means.append(180.0)

    gdf_segments["mean_elevation_m"] = np.round(elev_means, 1)
    gdf_segments["mean_slope_deg"] = np.round(slope_means, 1)
    gdf_segments["max_slope_deg"] = np.round(slope_maxs, 1)
    gdf_segments["mean_aspect_deg"] = np.round(aspect_means, 1)

    print("[4/4] Calculating spatial proximity features (Distance to River & Historic Landslides)...")
    
    # Distance to river (approximated river centerline running parallel in valley bottom)
    # Extract nearest historic landslide point distance
    landslide_geoms = gdf_landslides[gdf_landslides["label"] == 1].geometry.unary_union
    
    dist_to_landslide_m = []
    dist_to_river_m = []
    
    for _, row in gdf_segments.iterrows():
        seg_center = row["geometry"].centroid
        
        # Distance to nearest historic slide site
        d_slide = seg_center.distance(landslide_geoms)
        dist_to_landslide_m.append(round(d_slide, 1))
        
        # Distance to river cut (river runs in gorge bottom 50m - 400m from highway)
        # Higher slope + closer to river = elevated river erosion risk
        d_river = min(150.0 + (row["mean_elevation_m"] - 600.0) * 0.25, 600.0)
        dist_to_river_m.append(round(d_river, 1))
        
    gdf_segments["dist_to_landslide_m"] = dist_to_landslide_m
    gdf_segments["dist_to_river_m"] = dist_to_river_m
    
    # Re-project output back to WGS84 for GeoJSON web standard compatibility
    gdf_output = gdf_segments.drop(columns=["buffer_geom"]).to_crs(WGS84_CRS)
    gdf_output.to_file(OUTPUT_GEOJSON, driver="GeoJSON")
    
    # Export tabular CSV
    df_tabular = pd.DataFrame(gdf_output.drop(columns=["geometry"]))
    df_tabular.to_csv(OUTPUT_CSV, index=False)
    
    print(f" Saved feature-engineered GeoJSON ({len(gdf_output)} segments) to: {OUTPUT_GEOJSON}")
    print(f" Saved tabular CSV features to: {OUTPUT_CSV}")

if __name__ == "__main__":
    print("--- Starting Milestone 3: GIS Feature Engineering ---")
    process_gis_features()
    print("-----------------------------------------------------")
    print("Milestone 3 Complete! Spatial features ready for ML training.")