-- ==========================================================
-- AI-Based System Monitoring Database
-- Final Database Schema
-- ==========================================================

DROP TABLE IF EXISTS system_feature_windows CASCADE;
DROP TABLE IF EXISTS model_training_features CASCADE;
DROP TABLE IF EXISTS system_events CASCADE;

DROP TABLE IF EXISTS cpu_metrics CASCADE;
DROP TABLE IF EXISTS memory_metrics CASCADE;
DROP TABLE IF EXISTS disk_metrics CASCADE;
DROP TABLE IF EXISTS network_metrics CASCADE;
DROP TABLE IF EXISTS system_runtime_info CASCADE;

-------------------------------------------------------------
-- CPU Metrics
-------------------------------------------------------------

CREATE TABLE cpu_metrics (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    cpu_usage_percent DOUBLE PRECISION NOT NULL

);

-------------------------------------------------------------
-- Memory Metrics
-------------------------------------------------------------

CREATE TABLE memory_metrics (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    memory_percent DOUBLE PRECISION NOT NULL,

    swap_percent DOUBLE PRECISION NOT NULL

);

-------------------------------------------------------------
-- Disk Metrics
-------------------------------------------------------------

CREATE TABLE disk_metrics (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    disk_percent DOUBLE PRECISION NOT NULL,

    read_rate DOUBLE PRECISION NOT NULL,

    write_rate DOUBLE PRECISION NOT NULL

);

-------------------------------------------------------------
-- Network Metrics
-------------------------------------------------------------

CREATE TABLE network_metrics (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    bytes_sent BIGINT NOT NULL,

    bytes_received BIGINT NOT NULL,

    incoming_rate DOUBLE PRECISION NOT NULL,

    outgoing_rate DOUBLE PRECISION NOT NULL

);

-------------------------------------------------------------
-- Runtime Information
-------------------------------------------------------------

CREATE TABLE system_runtime_info (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    total_processes INT,

    running_processes INT,

    sleeping_processes INT,

    stopped_processes INT,

    zombie_processes INT,

    thread_count INT,

    load_avg_1 DOUBLE PRECISION,

    load_avg_5 DOUBLE PRECISION,

    load_avg_15 DOUBLE PRECISION

);

-------------------------------------------------------------
-- Raw ML Feature Table
-------------------------------------------------------------

CREATE TABLE model_training_features (

    id SERIAL PRIMARY KEY,

    host_id INT NOT NULL,

    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    cpu_usage DOUBLE PRECISION,

    memory_usage DOUBLE PRECISION,

    swap_usage DOUBLE PRECISION,

    disk_usage DOUBLE PRECISION,

    disk_read_rate DOUBLE PRECISION,

    disk_write_rate DOUBLE PRECISION,

    network_in BIGINT,

    network_out BIGINT,

    network_rate_in DOUBLE PRECISION,

    network_rate_out DOUBLE PRECISION,

    process_count INT,

    running_processes INT,

    sleeping_processes INT,

    zombie_processes INT,

    thread_count INT,

    load_1 DOUBLE PRECISION,

    load_5 DOUBLE PRECISION,

    load_15 DOUBLE PRECISION

);

-------------------------------------------------------------
-- Feature Windows
-------------------------------------------------------------

CREATE TABLE system_feature_windows (

    id SERIAL PRIMARY KEY,

    start_time TIMESTAMP,

    end_time TIMESTAMP,

    cpu_avg DOUBLE PRECISION,
    cpu_max DOUBLE PRECISION,
    cpu_min DOUBLE PRECISION,
    cpu_std DOUBLE PRECISION,
    cpu_range DOUBLE PRECISION,
    cpu_variance DOUBLE PRECISION,
    cpu_trend DOUBLE PRECISION,

    memory_avg DOUBLE PRECISION,
    memory_max DOUBLE PRECISION,
    memory_min DOUBLE PRECISION,
    memory_std DOUBLE PRECISION,
    memory_range DOUBLE PRECISION,
    memory_trend DOUBLE PRECISION,

    swap_avg DOUBLE PRECISION,
    swap_max DOUBLE PRECISION,
    swap_std DOUBLE PRECISION,
    swap_trend DOUBLE PRECISION,

    disk_avg DOUBLE PRECISION,
    disk_max DOUBLE PRECISION,
    disk_min DOUBLE PRECISION,
    disk_std DOUBLE PRECISION,
    disk_range DOUBLE PRECISION,
    disk_trend DOUBLE PRECISION,

    disk_read_avg DOUBLE PRECISION,
    disk_write_avg DOUBLE PRECISION,

    network_in_avg DOUBLE PRECISION,
    network_out_avg DOUBLE PRECISION,
    network_in_std DOUBLE PRECISION,
    network_out_std DOUBLE PRECISION,

    network_rate_in_avg DOUBLE PRECISION,
    network_rate_out_avg DOUBLE PRECISION,

    process_avg DOUBLE PRECISION,
    process_max DOUBLE PRECISION,
    process_min DOUBLE PRECISION,
    process_std DOUBLE PRECISION,

    running_process_avg DOUBLE PRECISION,
    sleeping_process_avg DOUBLE PRECISION,
    zombie_process_avg DOUBLE PRECISION,

    thread_avg DOUBLE PRECISION,

    hour_of_day INT,

    day_of_week INT,

    crash_label INT DEFAULT 0
);

CREATE UNIQUE INDEX unique_window
ON system_feature_windows(start_time,end_time);

-------------------------------------------------------------
-- Crash Events
-------------------------------------------------------------

CREATE TABLE system_events (

    id SERIAL PRIMARY KEY,

    event_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    event_type VARCHAR(100),

    description TEXT

);