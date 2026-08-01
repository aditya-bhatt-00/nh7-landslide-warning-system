import os
import json
import pickle
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import shap

# Set Directory Paths
PROCESSED_DIR = os.path.join("data", "processed")
MODELS_DIR = os.path.join("models")
os.makedirs(MODELS_DIR, exist_ok=True)

CSV_PATH = os.path.join(PROCESSED_DIR, "nh58_features.csv")
MODEL_SAVE_PATH = os.path.join(MODELS_DIR, "xgboost_landslide_model.pkl")
SHAP_SUMMARY_PLOT = os.path.join(MODELS_DIR, "shap_summary_plot.png")

def train_and_explain():
    print("=======================================================")
    print("      MILESTONE 4: XGBOOST TRAINING & SHAP ENGINE      ")
    print("=======================================================\n")

    # 1. Load Data
    df = pd.read_csv(CSV_PATH)
    print(f"[1/5] Loaded dataset with {len(df)} highway segments.")

    # 2. Define Synthetic Target Label for Base Topographic Hazard
    # Segment is High Hazard (1) if max_slope >= 32° AND dist_to_landslide <= 1500m
    # Otherwise Low Hazard (0)
    df['hazard_label'] = np.where(
        (df['max_slope_deg'] >= 32.0) & (df['dist_to_landslide_m'] <= 1500.0), 1, 0
    )

    feature_cols = [
        'mean_elevation_m',
        'mean_slope_deg',
        'max_slope_deg',
        'dist_to_river_m',
        'dist_to_landslide_m'
    ]

    X = df[feature_cols]
    y = df['hazard_label']

    print(f"      Hazard Class Breakdown: {dict(y.value_counts())}")

    # 3. Train / Test Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # 4. Initialize & Train XGBoost Model
    print("\n[2/5] Training XGBoost Classifier...")
    model = xgb.XGBClassifier(
        n_estimators=100,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        eval_metric='logloss'
    )
    model.fit(X_train, y_train)

    # 5. Evaluate Model
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    auc_score = roc_auc_score(y_test, y_prob)
    print(f"\n[3/5] Model Evaluation Results:")
    print(f"      • ROC-AUC Score: {auc_score:.4f}")
    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    # 6. SHAP Explainability Engine
    print("[4/5] Computing SHAP Explainability values...")
    explainer = shap.TreeExplainer(model)
    shap_values = explainer(X_test)

    # Save SHAP Summary Plot
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_test, show=False)
    plt.title("SHAP Feature Importance & Impact on Landslide Risk", fontsize=12, fontweight='bold')
    plt.tight_layout()
    plt.savefig(SHAP_SUMMARY_PLOT, dpi=300)
    plt.close()
    print(f"      Saved SHAP summary plot to: {SHAP_SUMMARY_PLOT}")

    # 7. Export Model Artifact
    print("\n[5/5] Exporting trained model artifact...")
    with open(MODEL_SAVE_PATH, 'wb') as f:
        pickle.dump(model, f)
    print(f"      Saved model binary to: {MODEL_SAVE_PATH}")
    
    print("\n=======================================================")
    print("            MILESTONE 4 TRAINING COMPLETE              ")
    print("=======================================================\n")

if __name__ == "__main__":
    train_and_explain()