CREATE TABLE IF NOT EXISTS users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    google_id VARCHAR(255) NULL,
    display_name VARCHAR(255) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS searches (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NULL,
    location VARCHAR(255) NOT NULL,
    price_max VARCHAR(50) NULL,
    query_text VARCHAR(255) NOT NULL,
    notes TEXT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS search_results (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    search_id BIGINT NOT NULL,
    title VARCHAR(255) NOT NULL,
    url TEXT NOT NULL,
    source VARCHAR(100) NOT NULL,
    price VARCHAR(50) NULL,
    location VARCHAR(255) NULL,
    description TEXT NULL,
    voucher_friendly TINYINT(1) DEFAULT 0,
    record_friendly TINYINT(1) DEFAULT 0,
    contact_name VARCHAR(255) NULL,
    contact_phone VARCHAR(50) NULL,
    contact_email VARCHAR(255) NULL,
    contact_method VARCHAR(100) NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS favorites (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    result_id BIGINT NOT NULL,
    notes TEXT NULL,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (result_id) REFERENCES search_results(id) ON DELETE CASCADE,
    UNIQUE KEY unique_favorite (user_id, result_id)
);

CREATE TABLE IF NOT EXISTS user_roles (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE,
    role VARCHAR(50) NOT NULL DEFAULT 'searcher',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS government_whitelist (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    gov_type VARCHAR(50),
    verified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS master_listings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    price VARCHAR(50),
    location VARCHAR(255) NOT NULL,
    description TEXT,
    url TEXT UNIQUE,
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    voucher_friendly TINYINT(1) DEFAULT 0,
    record_friendly TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_location (location),
    INDEX idx_active (is_active),
    INDEX idx_price (price),
    INDEX idx_voucher (voucher_friendly)
);

CREATE TABLE IF NOT EXISTS listing_sources (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    master_listing_id BIGINT NOT NULL,
    source VARCHAR(100) NOT NULL,
    source_listing_id BIGINT,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (master_listing_id) REFERENCES master_listings(id) ON DELETE CASCADE,
    UNIQUE KEY unique_source (master_listing_id, source)
);

CREATE TABLE IF NOT EXISTS area_tracking (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    area_name VARCHAR(255) NOT NULL UNIQUE,
    active TINYINT(1) DEFAULT 1,
    last_scrape TIMESTAMP,
    scrape_frequency_hours INT DEFAULT 24,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS manual_listings (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    lister_id BIGINT NOT NULL,
    master_listing_id BIGINT,
    title VARCHAR(255) NOT NULL,
    price VARCHAR(50),
    location VARCHAR(255) NOT NULL,
    description TEXT,
    contact_name VARCHAR(255),
    contact_phone VARCHAR(50),
    contact_email VARCHAR(255),
    voucher_friendly TINYINT(1) DEFAULT 0,
    record_friendly TINYINT(1) DEFAULT 0,
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (lister_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (master_listing_id) REFERENCES master_listings(id) ON DELETE SET NULL
);
