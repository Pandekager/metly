import os
import logging
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("metly")
from dotenv import load_dotenv
from src.scripts.db.populateDB import populateDB
from src.scripts.db.createDB import createTables
from src.scripts.db.enforceDataProtection import enforce_data_protection
from src.scripts.analysis.predictSales import predictSales
from src.scripts.analysis.consultAi import get_business_advice
from src.scripts.analysis.productAdvice import get_product_advice
from src.scripts.generateTestData import run_test_generation
import datetime


def main(test_data: bool = False, user_id: str | None = None):

    logger.info("Starting Metly Backend Operations")
    start_time = datetime.datetime.now()
    logger.info(f"start at {start_time.isoformat()}")

    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")

    # Handle test data generation
    if test_data:
        logger.info("Running test data generation")
        result = run_test_generation(products_count=20, orders_count=10)
        if result.get("status") == "success":
            logger.info("Test data generated successfully")
            # Sync to database if user_id provided
            if user_id:
                logger.info(f"Syncing test data to database for user: {user_id}")
                populateDB(db_usr, db_pwd, user_ids=[user_id])
        else:
            logger.error(f"Test data generation failed: {result.get('reason')}")
            raise RuntimeError(f"Test data generation failed: {result.get('reason')}")

        end_time = datetime.datetime.now()
        logger.info(
            f"complete at {end_time.isoformat()}, total time: {end_time - start_time}"
        )
        return

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

    logger.info("step 3 start: Enforcing data protection retention rules")
    enforce_data_protection(db_usr, db_pwd)
    logger.info(f"step 3 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 4 start: Running Sales Prediction Analysis")
    predictSales(db_usr, db_pwd)
    logger.info(f"step 4 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 5 start: Running AI Business Advice")
    get_business_advice(db_usr, db_pwd)
    logger.info(f"step 5 complete, elapsed: {datetime.datetime.now() - start_time}")

    logger.info("step 6 start: Running Product AI Analysis")
    get_product_advice(db_usr, db_pwd)
    logger.info(f"step 6 complete, elapsed: {datetime.datetime.now() - start_time}")

    end_time = datetime.datetime.now()
    logger.info(
        f"complete at {end_time.isoformat()}, total time: {end_time - start_time}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Metly Backend CLI")
    parser.add_argument(
        "--test-data",
        action="store_true",
        help="Generate test data instead of running full pipeline",
    )
    parser.add_argument(
        "--user",
        type=str,
        help="User ID to sync test data to database (requires --test-data)",
    )
    args = parser.parse_args()

    main(test_data=args.test_data, user_id=args.user)
