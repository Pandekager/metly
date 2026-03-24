from dotenv import load_dotenv
import os
import pandas as pd
from src.scripts.db.populateDB import connectDB
import numpy as np

# load .env
load_dotenv("./.env")
db_usr = os.getenv("DB_USR_ADMIN")
db_pwd = os.getenv("DB_PWD_ADMIN")

conn, df_users = connectDB(db_usr, db_pwd)


def orderAnalysis(conn, df_users):

    # Loop over users
    for _, user in df_users.iterrows():

        sql = """
        SELECT *
        FROM metlydk_main.order_lines ol
        JOIN orders o
            ON ol.order_id = o.id
        WHERE 1=1
            AND product_id IS NOT NULL
            AND ol.user_id = %(uid)s;
        """

        # prefer SQLAlchemy engine attached to the connection; fall back to raw conn
        engine = getattr(conn, "_sqlalchemy_engine", conn)
        df = pd.read_sql_query(sql, engine, params={"uid": user["id"]})
        df = df[df["product_title"].str.contains("TOLDTARIFNR|TOLLTARIFF") == False]
        df["product_title"] = (
            df["product_title"]
            .astype(str)
            .str.replace(r"(?i)<br\s*/?>", "-", regex=True)
            .str.replace(r"\s+-", " -", regex=True)
            .str.replace(r"(?<!\s)-", " -", regex=True)
            .str.strip()
        )

        # Orders analysis
        if df.empty:
            continue

        # Unique products per order
        df_prod = df[["order_id", "product_title"]].drop_duplicates()

        # Binary order x product matrix
        basket = df_prod.assign(val=1).pivot_table(
            index="order_id", columns="product_title", values="val", fill_value=0
        )

        # Co-occurrence matrix: number of orders containing both products
        coocc = basket.T.dot(basket)

        # Keep only upper triangle to avoid duplicate pairs and remove self-cooccurrence
        mask = np.triu(np.ones(coocc.shape, dtype=bool), k=1)
        coocc_upper = coocc.where(mask)

        # Convert to long form and sort
        pairs = coocc_upper.stack().to_frame("count")
        pairs.index.set_names(["product_1", "product_2"], inplace=True)
        pairs = pairs.reset_index()
        pairs = pairs[pairs["product_1"].str.strip() != ""]
        pairs = pairs[pairs["product_2"].str.strip() != ""]

        top_pairs = (
            pairs[pairs["count"] > 0].sort_values("count", ascending=False).head(25)
        ).reset_index(drop=True)

        top_pairs["user_id"] = user["id"]

        if top_pairs is not None and not top_pairs.empty:
            print(f"  Inserting {len(top_pairs)} product pairs")

            def _sql_val(v):
                return None if pd.isna(v) else v

            data = [
                (
                    _sql_val(row.get("product_1")),
                    _sql_val(row.get("product_2")),
                    _sql_val(row.get("count")),
                    _sql_val(row.get("user_id")),
                )
                for _, row in top_pairs.iterrows()
            ]

            insert_sql = """
            INSERT INTO top_pairs (
                product_1, product_2, cooccurrence_count, user_id
            ) VALUES (%s, %s, %s, %s)
            """

            cursor = conn.cursor()
            cursor.executemany(insert_sql, data)
            conn.commit()
            cursor.close()
        else:
            print("  No product pairs to insert")
    return print("Order analysis completed")


if __name__ == "__main__":
    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")
    orderAnalysis(conn, df_users)
