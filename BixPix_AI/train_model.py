# train_bixpix_xgb.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from xgboost import XGBClassifier
import joblib

def main():
    # Load & clean
    df = pd.read_csv("fight_data.csv").drop(columns=["fight_date"]).fillna(0)

    base_feats = [
        "height","weight","reach","age",
        "SLpM","Str_Acc","SApM","Str_Def",
        "TD_Avg","TD_Acc","TD_Def","Sub_Avg"
    ]
    for feat in base_feats:
        df[f"{feat}_diff"] = df[f"f1_{feat}"] - df[f"f2_{feat}"]

    diff_cols = [f"{feat}_diff" for feat in base_feats]

    # Build balanced dataset
    df["label"] = 1
    df_neg = df.copy()
    df_neg[diff_cols] *= -1
    df_neg["label"] = 0
    df_full = pd.concat([df, df_neg], ignore_index=True).sample(frac=1, random_state=42)

    X = df_full[diff_cols]
    y = df_full["label"]

    # Split (60/20/20)
    X_temp, X_test, y_temp, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=0.25, random_state=42, stratify=y_temp
    )

    # Initialize & fit
    model = XGBClassifier(
        objective="binary:logistic",
        eval_metric="logloss",
        eta=0.01,
        max_depth=6,
        subsample=0.8,
        colsample_bytree=0.8,
        use_label_encoder=False,
        early_stopping_rounds=50,
        seed=42
    )
    model.fit(
        X_train, y_train,
        eval_set=[(X_val, y_val)],
        verbose=True
    )

    # Evaluate
    y_proba = model.predict_proba(X_test)[:, 1]
    y_pred  = model.predict(X_test)

    print(f"\nTest Accuracy: {accuracy_score(y_test, y_pred):.2%}")
    print(f"Test ROC AUC:  {roc_auc_score(y_test, y_proba):.4f}\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred))

    # Feature importances by gain
    booster = model.get_booster()
    imp = booster.get_score(importance_type="gain")
    fi = (
        pd.DataFrame.from_dict(imp, orient="index", columns=["importance"])
          .rename_axis("feature")
          .reset_index()
          .sort_values("importance", ascending=False)
    )
    print("\nFeature importances (by gain):")
    print(fi.to_string(index=False))

    joblib.dump(model, "bixpix_xgb_model.pkl")
    fi.to_csv("feature_importances.csv", index=False)

if __name__ == "__main__":
    main()
