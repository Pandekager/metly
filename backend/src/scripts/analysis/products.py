from dotenv import load_dotenv
import os
import pandas as pd
from src.scripts.db.populateDB import connectDB
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import StandardScaler

# load .env
load_dotenv("./.env")
db_usr = os.getenv("DB_USR_ADMIN")
db_pwd = os.getenv("DB_PWD_ADMIN")

conn, df_users = connectDB(db_usr, db_pwd)


def predictSales(conn, df_users):

    # Loop over users
    for _, user in df_users.iterrows():

        sql = """
        SELECT product_id AS ID,
            product_title AS Navn,
            DATE(createdAt) AS DatoSolgt,
            COUNT(*) AS Antal
        FROM metlydk_main.order_lines ol
        JOIN orders o
        ON ol.order_id = o.id
        WHERE product_id IS NOT NULL
        AND ol.user_id = %(uid)s
        AND product_title NOT LIKE '%%TOLDTARIFNR%%'
        AND product_title NOT LIKE '%%TOLLTARIFF%%'
        GROUP BY product_id, DATE(createdAt)
        ORDER BY product_id, createdAt;
        """

        # prefer SQLAlchemy engine attached to the connection; fall back to raw conn
        engine = getattr(conn, "_sqlalchemy_engine", conn)
        df = pd.read_sql_query(sql, engine, params={"uid": user["id"]})
        df["Navn"] = (
            df["Navn"]
            .astype(str)
            .str.replace(r"(?i)<br\s*/?>", "-", regex=True)
            .str.replace(r"\s+-", " -", regex=True)
            .str.replace(r"(?<!\s)-", " -", regex=True)
            .str.strip()
        )

        df["DatoSolgt"] = pd.to_datetime(df["DatoSolgt"], errors="coerce")
        df["year"] = df["DatoSolgt"].dt.year.astype("Int64")
        df["month"] = df["DatoSolgt"].dt.month.astype("Int64")
        df["day"] = df["DatoSolgt"].dt.day.astype("Int64")

        # circular (sin/cos) representation so model knows wrap-around (e.g. month 12 -> month 1)
        month_f = df["month"].astype("float")
        day_f = df["day"].astype("float")

        # map 1..12 to angles on unit circle; NaNs remain NaN
        month_angle = 2 * np.pi * (month_f - 1) / 12.0
        df["month_sin"] = np.sin(month_angle)
        df["month_cos"] = np.cos(month_angle)

        # map 1..31 to angles for day-of-month wrap-around; NaNs remain NaN
        day_angle = 2 * np.pi * (day_f - 1) / 31.0
        df["day_sin"] = np.sin(day_angle)
        df["day_cos"] = np.cos(day_angle)

        # Normalise year/month/day to 0-1 range (keep NaN for missing values)
        for col in ["year"]:
            s = df[col].astype("float")
            if s.notna().any():
                minv = s.min(skipna=True)
                maxv = s.max(skipna=True)
                if pd.isna(minv) or pd.isna(maxv) or maxv == minv:
                    # if constant or no valid values, set normalized to 0.0 for valid entries
                    df[f"{col}_norm"] = s.where(s.notna(), other=np.nan).apply(
                        lambda v: 0.0 if not np.isnan(v) else np.nan
                    )
                else:
                    df[f"{col}_norm"] = (s - minv) / (maxv - minv)
            else:
                df[f"{col}_norm"] = np.nan

        # clustering -> derive categories, then train a KNN classifier to predict them

        feat_cols = [
            "Antal",
            "year_norm",
            "month_sin",
            "month_cos",
            "day_sin",
            "day_cos",
        ]
        # keep original index for assignment back into df
        feat = df[feat_cols].copy()

        # drop rows with missing features for clustering/training
        valid_mask = feat.notna().all(axis=1)
        if valid_mask.sum() < 2:
            # not enough data to cluster/classify
            df["category"] = -1
        else:
            X = feat[valid_mask].astype("float").values
            scaler = StandardScaler()
            Xs = scaler.fit_transform(X)

            n_samples = Xs.shape[0]
            max_k = min(20, n_samples - 1) if n_samples > 2 else 2
            best_score = -1.0

            # search for best number of clusters using silhouette score
            for k in range(2, max_k + 2):
                try:
                    km = KMeans(n_clusters=k, random_state=42, n_init=10)
                    labels = km.fit_predict(Xs)
                    # silhouette requires at least 2 clusters and less than n_samples
                    if len(set(labels)) < 2 or len(set(labels)) >= n_samples:
                        continue
                    score = silhouette_score(Xs, labels)
                    if score > best_score:
                        best_score = score
                        best_k = k
                        best_km = km
                except Exception:
                    # skip invalid k or failed fit
                    continue

            # assign cluster labels as categories for valid rows
            labels = best_km.predict(Xs)
            df["category"] = np.nan
            df.loc[valid_mask, "category"] = labels.astype(int)

        # For each KNN category, predict sales for the next 7 days
