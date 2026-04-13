# Set OpenBLAS threads BEFORE any imports that might use it
import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"] = "1"

from dotenv import load_dotenv
import pandas as pd
from src.scripts.db.populateDB import connectDB
import numpy as np
import seaborn as sns
import time
from sqlalchemy.exc import OperationalError, DBAPIError
import logging
import json

try:
    import structlog
except Exception:
    structlog = None


def _configure_logger():
    """Configure a structured logger similar to `main.py`.

    Returns an adapter exposing `.info(event, **kwargs)` so callers can use the
    same structured logging calls regardless of underlying implementation.
    """

    class _LoggerAdapter:
        def __init__(self, std_logger=None, struct_logger=None, use_struct=False):
            self._std = std_logger
            self._struct = struct_logger
            self._use_struct = use_struct

        def info(self, event, *args, **kwargs):
            if self._use_struct and self._struct is not None:
                self._struct.info(event, *args, **kwargs)
            elif kwargs:
                self._std.info(f"{event} {kwargs}", *args)
            else:
                self._std.info(event, *args)

        def debug(self, event, *args, **kwargs):
            if self._use_struct and self._struct is not None:
                self._struct.debug(event, *args, **kwargs)
            elif kwargs:
                self._std.debug(f"{event} {kwargs}", *args)
            else:
                self._std.debug(event, *args)

        def warning(self, event, *args, **kwargs):
            if self._use_struct and self._struct is not None:
                return self._struct.warning(event, *args, **kwargs)
            if kwargs:
                try:
                    payload = json.dumps(kwargs, default=str)
                except Exception:
                    payload = str(kwargs)
                self._std.warning("%s %s", event, payload, *args)
            else:
                self._std.warning("%s", event, *args)

        def error(self, event, *args, **kwargs):
            if self._use_struct and self._struct is not None:
                return self._struct.error(event, *args, **kwargs)
            if kwargs:
                try:
                    payload = json.dumps(kwargs, default=str)
                except Exception:
                    payload = str(kwargs)
                self._std.error("%s %s", event, payload, *args)
            else:
                self._std.error("%s", event, *args)

        def exception(self, event, **kwargs):
            # log exception with stack trace when using std logger
            if self._use_struct and self._struct is not None:
                return self._struct.exception(event, **kwargs)
            if kwargs:
                try:
                    payload = json.dumps(kwargs, default=str)
                except Exception:
                    payload = str(kwargs)
                self._std.exception("%s %s", event, payload)
            else:
                self._std.exception("%s", event)

        def critical(self, event, **kwargs):
            if self._use_struct and self._struct is not None:
                return self._struct.critical(event, **kwargs)
            if kwargs:
                try:
                    payload = json.dumps(kwargs, default=str)
                except Exception:
                    payload = str(kwargs)
                self._std.critical("%s %s", event, payload)
            else:
                self._std.critical("%s", event)

    if structlog is not None:
        logging.basicConfig(level=logging.INFO, format="%(message)s")
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.stdlib.add_log_level,
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
            context_class=dict,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
        return _LoggerAdapter(
            struct_logger=structlog.get_logger("metly"), use_struct=True
        )

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    std_logger = logging.getLogger("metly")
    return _LoggerAdapter(std_logger=std_logger, use_struct=False)


# module-level logger configured like `main.py`
logger = _configure_logger()

sns.set_style("whitegrid")
from pathlib import Path
import matplotlib.pyplot as plt
import calendar


def _load_lightgbm():
    try:
        import lightgbm as lgb

        return lgb, None
    except Exception as exc:
        return None, exc


# helper to calculate MAPE
def calculate_mape(y_true, y_pred):
    """Calculate Mean Absolute Percentage Error.

    Returns MAPE as a percentage. Handles zero values by adding small epsilon.
    """
    y_true = np.array(y_true, dtype=float)
    y_pred = np.array(y_pred, dtype=float)

    # Filter out zero actual values to avoid division by zero
    mask = y_true != 0
    if not np.any(mask):
        return np.nan

    y_true_filtered = y_true[mask]
    y_pred_filtered = y_pred[mask]

    return np.mean(np.abs((y_true_filtered - y_pred_filtered) / y_true_filtered)) * 100


# helper to create supervised features with enhanced seasonality and trend features
def make_supervised(series: pd.Series, lags: int):
    """Create supervised learning features with comprehensive seasonality and trend indicators.

    Features include:
    - Recent lags (1 to lags days)
    - Seasonal lags (7, 14, 30, 90, 365 days ago)
    - Rolling averages (7, 14, 30 days)
    - Calendar features (day of week, month, week of year, day of month, quarter)
    - Trend and cyclical features
    """
    # Build all features in a dictionary to avoid DataFrame fragmentation
    features = {}

    # Start with the target variable
    features["y"] = series

    # Recent lags for short-term patterns
    for lag in range(1, lags + 1):
        features[f"lag_{lag}"] = series.shift(lag)

    # Seasonal lags for capturing weekly, monthly, and yearly patterns
    seasonal_lags = [7, 14, 30, 90]  # week, 2 weeks, month, quarter
    if len(series) >= 365:
        seasonal_lags.append(365)  # year ago
    for lag in seasonal_lags:
        if len(series) > lag:
            features[f"lag_seasonal_{lag}"] = series.shift(lag)

    # Rolling statistics for trend capture
    for window in [7, 14, 30]:
        if len(series) > window:
            features[f"rolling_mean_{window}"] = (
                series.shift(1).rolling(window=window, min_periods=1).mean()
            )
            features[f"rolling_std_{window}"] = (
                series.shift(1).rolling(window=window, min_periods=1).std().fillna(0)
            )

    # Calendar features for seasonality - extract once and reuse
    idx = series.index
    dayofweek = idx.dayofweek
    month = idx.month

    features["dayofweek"] = dayofweek
    features["dayofmonth"] = idx.day
    features["dayofyear"] = idx.dayofyear
    features["weekofyear"] = idx.isocalendar().week.astype(int)
    features["month"] = month
    features["quarter"] = idx.quarter
    features["isweekend"] = dayofweek.isin([5, 6]).astype(int)
    features["is_month_start"] = idx.is_month_start.astype(int)
    features["is_month_end"] = idx.is_month_end.astype(int)
    
    # Holiday and seasonal indicators for different product categories
    features["is_holiday_season"] = ((month == 11) | (month == 12)).astype(int)  # Black Friday, Christmas
    features["is_valentine"] = (month == 2).astype(int)  # Jewelry, gifts
    features["is_easter"] = ((month == 3) | (month == 4)).astype(int)  # Easter period
    features["is_summer"] = ((month >= 6) & (month <= 8)).astype(int)  # Summer products
    features["is_back_to_school"] = ((month == 8) | (month == 9)).astype(int)  # School supplies
    features["is_payday_week"] = ((idx.day >= 25) | (idx.day <= 5)).astype(int)  # End/start of month
    features["days_to_month_end"] = idx.days_in_month - idx.day

    # Trend features
    trend = (idx - idx[0]).days
    features["trend"] = trend
    features["trend_squared"] = trend**2

    # Cyclical encoding of day of week and month for smooth transitions
    features["dayofweek_sin"] = np.sin(2 * np.pi * dayofweek / 7)
    features["dayofweek_cos"] = np.cos(2 * np.pi * dayofweek / 7)
    features["month_sin"] = np.sin(2 * np.pi * month / 12)
    features["month_cos"] = np.cos(2 * np.pi * month / 12)

    # Create DataFrame from all features at once (much faster than adding columns iteratively)
    df = pd.DataFrame(features, index=idx)

    df = df.dropna()
    if df.empty:
        return pd.DataFrame(), pd.Series(dtype=float)

    # Collect all feature columns (exclude 'y')
    feature_cols = [col for col in df.columns if col != "y"]
    return df[feature_cols], df["y"]


def predictSales(db_usr, db_pwd, user_ids=None):
    lgb, lgb_import_error = _load_lightgbm()
    if lgb is None:
        logger.warning(
            "LightGBM unavailable, using fallback forecast logic only",
            error=str(lgb_import_error),
        )

    try:
        conn, df_users = connectDB(db_usr, db_pwd)

        if conn is None or df_users is None:
            logger.warning("Failed to connect to DB or retrieve users")
            logger.info("Retrying connection...")
            time.sleep(5)
            conn, df_users = connectDB(db_usr, db_pwd)
            if conn is None or df_users is None:
                logger.error("Retry failed: Unable to connect to DB or retrieve users")
                return
    except Exception as e:
        logger.error("Connection failed: %s", str(e))
        return

    def read_sql_with_retry(
        sql, conn_holder, params=None, max_retries=3, backoff=1, **kwargs
    ):
        """Run pd.read_sql_query with retries and reconnects.

        conn_holder should be a dict like {'conn': conn} so we can replace it on reconnect.
        Returns a DataFrame or raises the last exception.
        """
        last_exc = None
        for attempt in range(1, max_retries + 1):
            try:
                engine = getattr(conn_holder["conn"], "_sqlalchemy_engine", None)
                if engine is None:
                    # fallback: try using raw DB-API connection via pandas
                    logger.info(
                        "read_sql_with_retry: using raw DB-API connection for query"
                    )
                    return pd.read_sql_query(
                        sql, conn_holder["conn"], params=params, **kwargs
                    )

                # use a fresh connection from the engine to avoid using a stale pooled connection
                with engine.connect() as connection:
                    logger.debug(
                        "read_sql_with_retry: executing query using engine.connect()"
                    )
                    return pd.read_sql_query(sql, connection, params=params, **kwargs)

            except (OperationalError, DBAPIError) as e:
                last_exc = e
                msg = str(e)
                logger.warning(
                    "read_sql_with_retry attempt %d failed: %s", attempt, msg
                )

                # try to recover: dispose engine / close existing conn then reconnect
                try:
                    # close raw connection if available
                    try:
                        conn_holder["conn"].close()
                    except Exception:
                        pass
                    # attempt to recreate connection object using connectDB
                    logger.info(
                        "read_sql_with_retry: reconnecting to DB (attempt %d)",
                        attempt,
                    )
                    new_conn, _ = connectDB(db_usr, db_pwd)
                    conn_holder["conn"] = new_conn
                    # small pause before retrying
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue
                except Exception as reconnect_exc:
                    logger.error(
                        "read_sql_with_retry: reconnect attempt failed: %s",
                        str(reconnect_exc),
                    )
                    time.sleep(backoff * (2 ** (attempt - 1)))
                    continue

        # exhausted retries
        logger.error("read_sql_with_retry: all %d attempts failed", max_retries)
        if last_exc is not None:
            raise last_exc
        raise RuntimeError("read_sql_with_retry failed without exception")

    if user_ids:
        allowed_user_ids = {str(user_id) for user_id in user_ids}
        df_users = df_users[df_users["id"].astype(str).isin(allowed_user_ids)].copy()

    # Loop over users
    for _, user in df_users.iterrows():

        # user = df_users.iloc[0, :]

        logger.info("Processing user %s", user.get("id"))

        sql = """
            SELECT ol.user_id, p.subcategory_name, ol.product_title, ol.amount, ol.unit_revenue, ol.unit_cost, o.createdAt   
            FROM metlydk_main.order_lines ol
            JOIN orders o
                ON ol.order_id = o.id
            LEFT JOIN products p
                ON ol.product_id = p.id
            WHERE 1=1
                AND product_id IS NOT NULL
                AND ol.user_id = %(uid)s
                AND o.user_id = %(uid)s
                AND p.user_id = %(uid)s;
        """

        # Use robust read with retries and reconnect on failure
        conn_holder = {"conn": conn}
        try:
            df = read_sql_with_retry(
                sql,
                conn_holder,
                params={"uid": user["id"]},
                max_retries=4,
                backoff=2,
            )
            logger.info("Fetched %d order lines for user %s", len(df), user.get("id"))
        except Exception as e:
            logger.error("Query failed for user %s: %s", user.get("id"), str(e))
            # skip this user and continue
            continue

        # update local conn reference if helper reconnected
        conn = conn_holder["conn"]
        df = df[df["product_title"].str.contains("TOLDTARIFNR|TOLLTARIFF") == False]
        df["product_title"] = (
            df["product_title"]
            .astype(str)
            .str.replace(r"(?i)<br\s*/?>", "-", regex=True)
            .str.replace(r"\s+-", " -", regex=True)
            .str.replace(r"(?<!\s)-", " -", regex=True)
            .str.strip()
        )
        df["subcategory_name"] = (
            df["subcategory_name"]
            .astype(str)
            .str.strip()
            .replace(["", "nan", "None"], "Uden for kategori")
        )

        # Orders analysis
        if df.empty:
            logger.info("No rows returned for user; skipping %s", user.get("id"))
            continue

        # only keep rows with positive unit_revenue
        df_analysis = df[df["unit_revenue"] > 0].copy()

        # create date column
        df_analysis["date"] = pd.to_datetime(
            df_analysis["createdAt"], errors="coerce"
        ).dt.date

        # compute line revenue per order line and aggregate by group+date
        df_analysis["line_revenue"] = (
            df_analysis["amount"] * df_analysis["unit_revenue"]
        )

        # determine which numeric columns to aggregate
        sum_cols = [c for c in ("amount", "line_revenue") if c in df_analysis.columns]
        if not sum_cols:
            # nothing to aggregate for this user
            continue

        # ensure numeric columns are numeric and fill NaNs so sum works reliably
        df_analysis[sum_cols] = (
            df_analysis[sum_cols].apply(pd.to_numeric, errors="coerce").fillna(0)
        )

        # group by subcategory_name and date, summing the numeric columns
        grouped = df_analysis.groupby(["subcategory_name", "date"], as_index=False)[
            sum_cols
        ].sum()

        # ensure output directory exists
        out_dir = Path("plots")
        out_dir.mkdir(parents=True, exist_ok=True)

        # determine max date in data for filling missing days
        start_date = pd.to_datetime(f"{pd.Timestamp.now().year - 3}-01-01")
        end_date = pd.to_datetime(grouped["date"]).max()
        missing_idx = pd.date_range(start=start_date, end=end_date, freq="D")

        # Only include past 3 years
        grouped = grouped[grouped["date"] >= start_date.date()]

        # Collect all forecasts to insert in batch
        all_forecasts_to_insert = []

        # predict per subcategory_name
        for _, grp in enumerate(sorted(grouped["subcategory_name"].dropna().unique())):
            grp_df = grouped[grouped["subcategory_name"] == grp].sort_values("date")
            if grp_df.empty:
                continue

            if grp in [None, "48 timers leveringer"]:
                continue

            # If there are missing days up to max_date, create zero rows for them
            grp_df["date"] = pd.to_datetime(grp_df["date"])
            grp_df = missing_idx.to_frame(index=False, name="date").merge(
                grp_df, on="date", how="left"
            )
            grp_df[sum_cols] = grp_df[sum_cols].fillna(0)

            if grp_df["date"].max() < end_date:
                logger.warning(
                    "User %s subcategory %s has max date %s less than expected end date %s",
                    user["id"],
                    grp,
                    grp_df["date"].max(),
                    end_date,
                )

            # fig, ax = plt.subplots(figsize=(10, 4.5))
            # color = sns.color_palette("tab10")[int(_) % 10]
            # ax.plot(
            #     grp_df["date"],
            #     grp_df["amount"],
            #     linestyle="-",
            #     color=color,
            # )
            # ax.fill_between(grp_df["date"], grp_df["amount"], alpha=0.15, color=color)

            # ax.set_title(f"User {user['id']} — Units sold over time (subcategory {grp})")
            # ax.set_xlabel("Date")
            # ax.set_ylabel("Amount")
            # ax.grid(alpha=0.3)
            # fig.autofmt_xdate()

            # fname = out_dir / f"user_{user['id']}_subcategory_name_{_}.png"
            # plt.savefig(fname, dpi=150, bbox_inches="tight")
            # plt.close(fig)

            # Decision tree ensemble forecast with uncertainty (bagged decision trees)

            # prepare a daily time series index and fill missing days with 0
            grp_df = grp_df.copy()
            grp_df = grp_df.sort_values("date")
            ts = grp_df.set_index("date")["amount"].asfreq("D").fillna(0)

            # Forecasting parameters
            lags = 90  # Increased from 60 to capture more historical patterns
            # determine forecast horizon: remaining days in current month + days in next month
            last_date = grp_df["date"].max()
            if pd.isna(last_date):
                # fallback if no valid date
                forecast_periods = 30
            else:
                last_date = pd.to_datetime(last_date)
                y, m = last_date.year, last_date.month
                _, days_in_month = calendar.monthrange(y, m)
                remaining_current = days_in_month - last_date.day
                # next month/year
                nm = m + 1
                ny = y
                if nm == 13:
                    nm = 1
                    ny += 1
                _, days_next_month = calendar.monthrange(ny, nm)
                forecast_periods = int(max(1, remaining_current + days_next_month))

            X, y = make_supervised(ts, lags)

            # Calculate minimum required data points (lags + seasonal features + buffer)
            min_required = lags + 30  # 90 lags + 30 day buffer = 120 days minimum

            if X.empty or len(y) < min_required or lgb is None:
                logger.warning(
                    "User %s subcategory %s using fallback forecast. samples=%d required=%d lightgbm_available=%s",
                    user["id"],
                    grp,
                    len(y),
                    min_required,
                    lgb is not None,
                )

                # Improved fallback: linear trend extrapolation with realistic uncertainty
                last_30_days = ts.tail(min(30, len(ts)))

                if len(last_30_days) >= 7:
                    # Calculate simple linear trend from available data
                    days_numeric = np.arange(len(last_30_days))
                    values = last_30_days.to_numpy(dtype=float)

                    # Fit linear trend
                    if len(days_numeric) > 1 and np.std(values) > 0:
                        slope, intercept = np.polyfit(days_numeric, values, 1)
                        # Cap slope to prevent unrealistic growth
                        mean_val = np.mean(values)
                        slope = np.clip(slope, -mean_val * 0.1, mean_val * 0.1)
                    else:
                        slope = 0
                        intercept = np.mean(values) if len(values) > 0 else 0

                    # Generate forecast with trend
                    forecast_index = pd.date_range(
                        start=ts.index.max() + pd.Timedelta(days=1),
                        periods=forecast_periods,
                        freq="D",
                    )
                    future_days = np.arange(
                        len(last_30_days), len(last_30_days) + forecast_periods
                    )
                    forecast_values = slope * future_days + intercept
                    forecast_values = np.maximum(
                        forecast_values, 0
                    )  # Ensure non-negative

                    forecast_mean = pd.Series(forecast_values, index=forecast_index)

                    # Add uncertainty based on historical variance (wider for less data)
                    mean_val = np.mean(values)
                    historical_std = (
                        np.std(values) if len(values) > 1 else mean_val * 0.3
                    )
                    uncertainty_factor = (
                        2.0  # Conservative uncertainty for limited data
                    )
                    lower = forecast_mean - historical_std * uncertainty_factor
                    upper = forecast_mean + historical_std * uncertainty_factor
                    lower = np.maximum(lower, 0)  # Ensure non-negative bounds

                    # # Calculate MAPE on historical data using simple holdout
                    # if len(last_30_days) >= 14:
                    #     test_size = min(7, len(last_30_days) // 3)
                    #     train_vals = values[:-test_size]
                    #     test_vals = values[-test_size:]
                    #     train_days = days_numeric[:-test_size]
                    #     test_days = days_numeric[-test_size:]

                    #     # Fit on train
                    #     if len(train_days) > 1 and np.std(train_vals) > 0:
                    #         slope_train, intercept_train = np.polyfit(
                    #             train_days, train_vals, 1
                    #         )
                    #         mean_train = np.mean(train_vals)
                    #         slope_train = np.clip(
                    #             slope_train, -mean_train * 0.1, mean_train * 0.1
                    #         )
                    #     else:
                    #         slope_train = 0
                    #         intercept_train = (
                    #             np.mean(train_vals) if len(train_vals) > 0 else 0
                    #         )

                    #     # Predict on test
                    #     test_preds = slope_train * test_days + intercept_train
                    #     test_preds = np.maximum(test_preds, 0)
                    #     mape = calculate_mape(test_vals, test_preds)
                    # else:
                    #     mape = np.nan
                else:
                    # Very limited data: use median for sparse data (more robust than mean)
                    ts_nonzero = ts[ts > 0]
                    if len(ts_nonzero) > 0:
                        median_val = ts_nonzero.median()
                        mean_val = ts_nonzero.mean()
                        # Use lower of median and mean for conservative estimate
                        forecast_val = min(median_val, mean_val)
                    else:
                        # All zeros in history - predict zero
                        forecast_val = 0.0
                    
                    # For very sparse data, round to nearest integer
                    forecast_val = max(0, int(np.round(forecast_val)))
                    std_val = ts.dropna().std() if len(ts.dropna()) > 1 else forecast_val * 0.5

                    forecast_index = pd.date_range(
                        start=ts.index.max() + pd.Timedelta(days=1),
                        periods=forecast_periods,
                        freq="D",
                    )
                    forecast_mean = pd.Series(
                        [forecast_val] * forecast_periods, index=forecast_index
                    )
                    lower = pd.Series(
                        [max(0, int(forecast_val - std_val))] * forecast_periods,
                        index=forecast_index,
                    )
                    upper = pd.Series(
                        [int(forecast_val + std_val * 2)] * forecast_periods,
                        index=forecast_index,
                    )
                    mape = np.nan  # Not enough data for MAPE calculation
            else:
                # Use LightGBM which is memory-efficient and handles seasonality well
                # Train multiple models with bootstrapped samples for uncertainty estimation
                n_bootstrap = 15  # Number of bootstrap samples for uncertainty

                # LightGBM parameters - using defaults for better generalization with sparse data
                lgb_params = {
                    "objective": "regression",
                    "verbose": -1,
                    "num_threads": 1,  # Limit threads for memory efficiency
                }

                # Convert training data to numpy arrays
                X_np = X.to_numpy(dtype=float)
                y_np = y.to_numpy(dtype=float).ravel()
                
                # Safety check: if all labels are zero, predict zero for the future
                if y_np.sum() == 0:
                    logger.info(
                        "User %s subcategory %s has all zero sales in training data. Predicting zero.",
                        user["id"],
                        grp,
                    )
                    forecast_index = pd.date_range(
                        start=ts.index.max() + pd.Timedelta(days=1),
                        periods=forecast_periods,
                        freq="D",
                    )
                    forecast_mean = pd.Series([0] * forecast_periods, index=forecast_index)
                    lower = pd.Series([0] * forecast_periods, index=forecast_index)
                    upper = pd.Series([0] * forecast_periods, index=forecast_index)
                    continue
                
                # Check sparsity: if data is very sparse, use fewer iterations
                zero_ratio = np.sum(y_np == 0) / len(y_np)
                
                # Detect low-volume category (mean sales < 2 per day)
                mean_sales = np.mean(y_np)
                is_low_volume = mean_sales < 2.0
                if zero_ratio > 0.8:  # More than 80% zeros
                    num_boost_round = 50  # Fewer iterations for very sparse data
                elif zero_ratio > 0.6:  # 60-80% zeros
                    num_boost_round = 75
                else:
                    num_boost_round = 100  # Standard iterations

                # Bootstrap training for uncertainty estimation
                all_forecasts = np.zeros((n_bootstrap, forecast_periods), dtype=float)

                first_date = ts.index[0]
                n_samples = len(X_np)

                for i in range(n_bootstrap):
                    # Bootstrap sample
                    indices = np.random.choice(n_samples, size=n_samples, replace=True)
                    X_boot = X_np[indices]
                    y_boot = y_np[indices]

                    # Train LightGBM model with adaptive iterations
                    train_data = lgb.Dataset(X_boot, label=y_boot)
                    model = lgb.train(lgb_params, train_data, num_boost_round=num_boost_round)

                    # Multi-step forecast
                    hist = ts.copy()
                    preds = []

                    for h in range(forecast_periods):
                        next_date = hist.index.max() + pd.Timedelta(days=1)

                        # Reconstruct the full feature set for prediction
                        # Create a temporary series with the predicted values included
                        temp_series = hist.copy()
                        temp_series.loc[next_date] = 0  # placeholder

                        # Rebuild features using the same make_supervised function
                        X_temp, _ = make_supervised(temp_series, lags)

                        if not X_temp.empty:
                            # Get the last row (features for next_date)
                            X_next = X_temp.iloc[[-1]].to_numpy(dtype=float)
                            p = model.predict(
                                X_next, num_iteration=model.best_iteration
                            )[0]
                            p = max(0, p)  # Ensure non-negative predictions
                            
                            # For low-volume categories, add variability using Poisson-like distribution
                            if is_low_volume and p > 0:
                                # Sample from Poisson distribution to create natural 0/1/2 variation
                                # instead of flat predictions
                                p = float(np.random.poisson(lam=p))
                            
                            preds.append(float(p))
                            # Update history with prediction
                            hist.loc[next_date] = p
                        else:
                            # Fallback if feature creation fails
                            last_val = hist.iloc[-1] if len(hist) > 0 else 0.0
                            preds.append(float(last_val))
                            hist.loc[next_date] = last_val

                    all_forecasts[i, :] = preds

                forecast_index = pd.date_range(
                    start=ts.index.max() + pd.Timedelta(days=1),
                    periods=forecast_periods,
                    freq="D",
                )
                
                # For low-volume categories, use median instead of mean to preserve integer nature
                if is_low_volume:
                    forecast_mean = pd.Series(
                        np.median(all_forecasts, axis=0), index=forecast_index
                    )
                    # Round to nearest integer for low-volume categories
                    forecast_mean = forecast_mean.round()
                else:
                    forecast_mean = pd.Series(
                        all_forecasts.mean(axis=0), index=forecast_index
                    )
                
                lower = pd.Series(
                    np.percentile(all_forecasts, 10, axis=0), index=forecast_index
                )
                upper = pd.Series(
                    np.percentile(all_forecasts, 90, axis=0), index=forecast_index
                )

                # # Calculate MAPE using time-series cross-validation on historical data
                # # Use the last 30 days as test set for MAPE calculation
                # test_size = min(
                #     30, len(ts) // 5
                # )  # Use 20% or 30 days, whichever is smaller
                # if test_size >= 7:  # Need at least a week for meaningful test
                #     train_ts = ts.iloc[:-test_size]
                #     test_ts = ts.iloc[-test_size:]

                #     # Rebuild features for train/test split
                #     X_train, y_train = make_supervised(train_ts, lags)

                #     if not X_train.empty and len(y_train) >= min_required:
                #         # Train model on train set
                #         train_data = lgb.Dataset(
                #             X_train.to_numpy(dtype=float),
                #             label=y_train.to_numpy(dtype=float).ravel(),
                #         )
                #         eval_model = lgb.train(
                #             lgb_params, train_data, num_boost_round=100
                #         )

                #         # Forecast test period
                #         test_preds = []
                #         hist_test = train_ts.copy()

                #         for idx in test_ts.index:
                #             temp_series = hist_test.copy()
                #             temp_series.loc[idx] = 0
                #             X_temp, _ = make_supervised(temp_series, lags)

                #             if not X_temp.empty:
                #                 X_next = X_temp.iloc[[-1]].to_numpy(dtype=float)
                #                 p = eval_model.predict(
                #                     X_next, num_iteration=eval_model.best_iteration
                #                 )[0]
                #                 p = max(0, p)
                #                 test_preds.append(p)
                #                 hist_test.loc[idx] = p
                #             else:
                #                 test_preds.append(
                #                     hist_test.iloc[-1] if len(hist_test) > 0 else 0.0
                #                 )

                #         mape = calculate_mape(test_ts.values, np.array(test_preds))
                #     else:
                #         mape = np.nan
                # else:
                #     mape = np.nan

            # # plot observed and forecast with uncertainty band (5-95 percentile)
            # if X.empty or len(y) >= min_required:
            #     fig2, ax2 = plt.subplots(figsize=(10, 6))
            #     ax2.plot(ts.index, ts.values, label="Observed", color="tab:blue")
            #     ax2.plot(
            #         forecast_mean.index,
            #         forecast_mean.values,
            #         label="Forecast (mean)",
            #         color="tab:red",
            #     )
            #     ax2.fill_between(
            #         forecast_mean.index,
            #         lower.values,
            #         upper.values,
            #         color="pink",
            #         alpha=0.35,
            #         label="5–95% interval",
            #     )

            #     # Format title with MAPE if available
            #     if not np.isnan(mape):
            #         title = f"Forecast (LightGBM) — User {user['id']} group {grp}\nMAPE: {mape:.1f}%"
            #     else:
            #         title = f"Forecast (LightGBM) — User {user['id']} group {grp}\nMAPE: N/A (insufficient data)"

            #     ax2.set_title(title)
            #     ax2.set_xlabel("Date")
            #     ax2.set_ylabel("Sales")
            #     ax2.legend()
            #     fname = out_dir / f"user_{user['id']}_{grp}_MAPE_{mape:.1f}.png"
            #     fig2.autofmt_xdate()
            #     fig2.savefig(fname, dpi=150, bbox_inches="tight")
            #     plt.close(fig2)

            # save actuals (from Jan 1 last year) and forecasts to DB with a flag marking forecast vs actual
            last_year = pd.Timestamp.now().year - 1
            start_date = pd.to_datetime(f"{last_year}-01-01")

            # prepare observed series starting from start_date
            observed = ts[ts.index >= start_date]
            observed_df = pd.DataFrame(
                {"date": observed.index, "amount": observed.values}
            )
            observed_df["is_forecast"] = False

            # prepare forecast dataframe (forecast_mean is a pd.Series with DatetimeIndex)
            forecast_df = pd.DataFrame(
                {"date": forecast_mean.index, "amount": forecast_mean.values}
            )
            forecast_df["is_forecast"] = True

            # combine and only keep records from start_date onward (should already be true)
            to_insert = pd.concat([observed_df, forecast_df], ignore_index=True)
            to_insert = to_insert[to_insert["date"] >= start_date]
            to_insert["subcategory_name"] = grp
            to_insert["user_id"] = user["id"]

            if not to_insert.empty:
                all_forecasts_to_insert.append(to_insert)
            else:
                logger.info(
                    "No sales rows to insert for user %s group %s", user["id"], grp
                )

        # Now insert all forecasts in a transaction with proper error handling
        if all_forecasts_to_insert:
            combined_forecasts = pd.concat(all_forecasts_to_insert, ignore_index=True)
            # Ensure amount column exists and convert to integer
            if "amount" in combined_forecasts.columns:
                combined_forecasts["amount"] = (
                    pd.to_numeric(combined_forecasts["amount"], errors="coerce")
                    .fillna(0)
                    .apply(np.round)
                    .astype(int)
                )
            else:
                logger.error(
                    "Missing 'amount' column in combined forecasts for user %s",
                    user["id"],
                )
                continue

            try:
                # Begin transaction
                cursor = conn.cursor()

                # Delete existing forecast rows for this user
                dates = sorted(
                    {pd.to_datetime(d).date() for d in combined_forecasts["date"]}
                )
                if dates:
                    delete_sql = (
                        "DELETE FROM forecasts WHERE user_id = %s AND date >= %s"
                    )
                    cursor.execute(
                        delete_sql, (user["id"], dates[0].strftime("%Y-%m-%d"))
                    )
                    logger.info(
                        "Deleted existing forecast rows for user %s from date %s onward",
                        user["id"],
                        dates[0],
                    )

                # Insert new forecasts
                def _sql_val(v):
                    if pd.isna(v):
                        return None
                    if isinstance(v, (pd.Timestamp, pd.DatetimeIndex)):
                        return pd.to_datetime(v).strftime("%Y-%m-%d")
                    if isinstance(v, (np.integer, np.floating)):
                        return v.item()
                    return v

                data = [
                    (
                        _sql_val(user["id"]),
                        _sql_val(row["subcategory_name"]),
                        _sql_val(row["date"]),
                        _sql_val(row["amount"]),
                        _sql_val(bool(row["is_forecast"])),
                    )
                    for _, row in combined_forecasts.iterrows()
                ]

                insert_sql = """
                INSERT INTO forecasts (
                    user_id, subcategory_name, date, amount, is_forecast
                ) VALUES (%s, %s, %s, %s, %s)
                """

                cursor.executemany(insert_sql, data)
                conn.commit()

                logger.info(
                    "Successfully inserted %d forecast rows for user %s",
                    len(combined_forecasts),
                    user["id"],
                )

            except Exception as e:
                logger.error(
                    "Failed to insert forecasts for user %s: %s", user["id"], str(e)
                )
                try:
                    conn.rollback()
                    logger.info("Rolled back transaction for user %s", user["id"])
                except Exception as rollback_err:
                    logger.error(
                        "Rollback failed for user %s: %s", user["id"], str(rollback_err)
                    )
            finally:
                try:
                    cursor.close()
                except Exception:
                    pass
        else:
            logger.warning("No forecasts generated for user %s", user["id"])

    logger.info("Order analysis completed")
    return "Order analysis completed"


if __name__ == "__main__":
    # load .env
    load_dotenv("./.env")
    db_usr = os.getenv("DB_USR_ADMIN")
    db_pwd = os.getenv("DB_PWD_ADMIN")
    predictSales(db_usr, db_pwd)
