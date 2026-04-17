CREATE TABLE IF NOT EXISTS customers (
  id VARCHAR(255) NOT NULL,
  user_id uuid NULL,
  billing_firstName VARCHAR(255) NULL,
  billing_lastName VARCHAR(255) NULL,
  billing_addressLine VARCHAR(1024) NULL,
  billing_city VARCHAR(255) NULL,
  billing_zipCode VARCHAR(20) NULL,
  billing_email VARCHAR(255) NULL,
  extended_internal TEXT NULL,
  extended_external TEXT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_customers_user_id (user_id),
  CONSTRAINT fk_customers_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;


CREATE TABLE IF NOT EXISTS languages (
  id VARCHAR(100) NOT NULL,
  user_id uuid NULL,
  iso VARCHAR(10) NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_languages_user_id (user_id),
  CONSTRAINT fk_languages_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;


CREATE TABLE IF NOT EXISTS orders (
  id VARCHAR(255) NOT NULL,
  user_id uuid NULL,
  totalItems INT NULL,
  total DECIMAL(18,4) NULL,
  currency_symbol VARCHAR(16) NULL,
  createdAt DATETIME NULL,
  customer_id VARCHAR(255) NULL,
  language_id VARCHAR(100) NULL,
  referrer VARCHAR(2048) NULL,
  -- Revenue leak analysis fields
  orderStatus VARCHAR(50) NULL DEFAULT 'completed',
  cancelledAt DATETIME NULL,
  -- Order flow analysis fields
  processed_at DATETIME NULL,
  fulfilled_at DATETIME NULL,
  cancelled_at DATETIME NULL,
  closed_at DATETIME NULL,
  fulfillment_status VARCHAR(50) NULL,
  tracking_number VARCHAR(255) NULL,
  carrier VARCHAR(100) NULL,
  shipping_address TEXT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_orders_user_id (user_id),
  CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

CREATE TABLE IF NOT EXISTS products (
  id VARCHAR(255) NOT NULL,
  user_id uuid NULL,
  product_name VARCHAR(255) NULL,
  subcategory_id VARCHAR(255) NULL,
  subcategory_name VARCHAR(255) NULL,
  maincategory_id VARCHAR(255) NULL,
  maincategory_name VARCHAR(255) NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_products_user_id (user_id),
  CONSTRAINT fk_products_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

CREATE TABLE IF NOT EXISTS product_categories (
  id VARCHAR(255) NOT NULL,
  user_id uuid NULL,
  path VARCHAR(1024) NULL,
  title VARCHAR(1024) NULL,
  createdAt DATETIME NULL,
  updatedAt DATETIME NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_product_categories_user_id (user_id),
  CONSTRAINT fk_product_categories_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;


CREATE TABLE IF NOT EXISTS order_lines (
  order_line_id VARCHAR(255) NOT NULL,
  user_id uuid NULL,
  order_id VARCHAR(255) NULL,
  product_id VARCHAR(255) NULL,
  product_title VARCHAR(1024) NULL,
  variant_title VARCHAR(1024) NULL,
  amount INT NULL,
  unit_revenue DECIMAL(18,4) NULL,
  unit_cost DECIMAL(18,4) NULL,
  stock_status VARCHAR(255) NULL,
  stock_amount VARCHAR(255) NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  KEY idx_order_lines_user_id (user_id),
  CONSTRAINT fk_order_lines_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

CREATE TABLE IF NOT EXISTS top_pairs (
  id BIGINT NOT NULL AUTO_INCREMENT,
  product_1 VARCHAR(255) NOT NULL,
  product_2 VARCHAR(255) NOT NULL,
  cooccurrence_count INT NULL,
  user_id uuid NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_top_pairs_user_id (user_id),
  CONSTRAINT fk_top_pairs_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

CREATE TABLE IF NOT EXISTS forecasts (
  id BIGINT NOT NULL AUTO_INCREMENT,
  date DATE NOT NULL,
  amount DECIMAL(18,4) NULL,
  is_forecast TINYINT(1) NULL,
  subcategory_name VARCHAR(255) NULL,
  user_id uuid NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_forecasts_date_group_user (date, subcategory_name, user_id),
  KEY idx_forecasts_user_id (user_id),
  CONSTRAINT fk_forecasts_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

CREATE TABLE IF NOT EXISTS ai_responses (
  id BIGINT NOT NULL AUTO_INCREMENT,
  ai_category_id VARCHAR(255) NULL,
  response_text TEXT NULL,
  user_id uuid NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_ai_responses_user_id (user_id),
  CONSTRAINT fk_ai_responses_user FOREIGN KEY (user_id) REFERENCES metlydk_main.users(id) ON DELETE SET NULL ON UPDATE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=latin1 COLLATE=latin1_danish_ci;

-- Additional indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_order_lines_order_id ON order_lines (order_id);
CREATE INDEX IF NOT EXISTS idx_order_lines_product_id ON order_lines (product_id);
CREATE INDEX IF NOT EXISTS idx_orders_createdAt ON orders (createdAt);
CREATE INDEX IF NOT EXISTS idx_ol_user_prod_order ON order_lines (user_id, product_id, order_id);