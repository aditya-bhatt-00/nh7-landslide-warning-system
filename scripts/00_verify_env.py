import geopandas as gpd
import rasterio
import shapely
import xgboost as xgb
import fastapi

print("--- Environment Verification ---")
print(f"GeoPandas Version : {gpd.__version__}")
print(f"Rasterio Version  : {rasterio.__version__}")
print(f"Shapely Version   : {shapely.__version__}")
print(f"XGBoost Version   : {xgb.__version__}")
print(f"FastAPI Version   : {fastapi.__version__}")
print("--------------------------------")
print("Environment successfully verified! Ready for Milestone 2.")