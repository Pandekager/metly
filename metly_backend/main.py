import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metly")
from dotenv import load_dotenv
from src.scripts.db.populateDB import populateDB
from src.scripts.db.createDB import createTables
from src.scripts.analysis.predictSales import predictSales
from src.scripts.analysis.consultAi import get_business_advice
import datetime


def main():

    logger.info("Starting Metly Backend Operations")
    start_time = datetime.datetime.now()
    logger.info(f"start at {start_time.isoformat()}")

    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")

    logger.info("step 1 start: Creating Database Tables")
    createTables(db_usr, db_pwd)
    logger.info(f"step 1 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 2 start: Refresh Database with new data")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            populateDB(db_usr, db_pwd)
            break
        except Exception as e:
            if attempt < max_retries:
                logger.info(f"step 2 retry {attempt}: {e}")
            else:
                logger.info(f"step 2 failed: {e}")
                raise
    logger.info(f"step 2 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 3 start: Running Sales Prediction Analysis")
    predictSales(db_usr, db_pwd)
    logger.info(f"step 3 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 4 start: Running AI Business Advice")
    get_business_advice(db_usr, db_pwd)
    logger.info(f"step 4 complete, elapsed: {datetime.datetime.now() - start_time}")

    end_time = datetime.datetime.now()
    logger.info(
        f"complete at {end_time.isoformat()}, total time: {end_time - start_time}"
    )


if __name__ == "__main__":
    main()
