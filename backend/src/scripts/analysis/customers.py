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


def customerSegmentation(conn, df_users):

    # Loop over users
    for _, user in df_users.iterrows():

        # Load customer data
        sql = """
        SELECT
            billing_email AS ID,
            billing_firstName AS Navn,
            currency_symbol,
            billing_zipCode AS Postnummer,
            SUM(totalItems) AS AntalVarer,
            CASE
                WHEN currency_symbol = 'DKK' THEN SUM(total)
                WHEN currency_symbol = 'EUR' THEN SUM(total) * 7.44
                WHEN currency_symbol = 'SEK' THEN SUM(total) * 0.68
                WHEN currency_symbol = 'NOK' THEN SUM(total) * 0.64
            END AS Beloeb,
            COUNT(createdAt) AS AntalOrdre	
        FROM orders
        JOIN customers
            ON orders.customer_id = customers.id
                WHERE billing_email IS NOT NULL
                AND orders.user_id = %(uid)s
        GROUP BY billing_email, billing_firstName, billing_zipCode, currency_symbol;
        """

        # prefer SQLAlchemy engine attached to the connection; fall back to raw conn
        engine = getattr(conn, "_sqlalchemy_engine", conn)
        df_customers = pd.read_sql_query(sql, engine, params={"uid": user["id"]})

        # Load name to gender
        name_gender = pd.read_csv("data/name_genders.csv")

        # Merge customer data with name_gender
        df_customers = df_customers.merge(
            name_gender, left_on="Navn", right_on="firstName", how="left"
        )

        # Fill missing gender values
        missing_gender = df_customers[df_customers["Gender"].isnull()]["Navn"].unique()

        # Convert the ndarray to a DataFrame before saving to CSV
        pd.DataFrame(missing_gender, columns=["Navn"]).to_csv(
            "data/missing_genders.csv", index=False
        )

        # Group by Postnummer and sum Beloeb, AntalVarer og AntalOrdre
        df_postnummer = (
            df_customers.groupby(["Postnummer", "currency_symbol"], dropna=False)[
                ["Beloeb", "AntalVarer", "AntalOrdre"]
            ]
            .sum()
            .reset_index()
        )

        # Add column with Beloeb / AntalOrdre, handle division by zero
        df_postnummer["BeloebPrOrdre"] = df_postnummer["Beloeb"] / df_postnummer[
            "AntalOrdre"
        ].replace(0, np.nan)
        df_postnummer["BeloebPrOrdre"] = df_postnummer["BeloebPrOrdre"].fillna(0)

        # Sort
        df_postnummer = df_postnummer.sort_values(
            by="Beloeb", ascending=False
        ).reset_index(drop=True)
