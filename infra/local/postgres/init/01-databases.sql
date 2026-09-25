-- Runs once when the postgres volume is created
-- Extra databases for tools and for the integration tests
CREATE DATABASE dagster;
CREATE DATABASE keycloak;
CREATE DATABASE chatbot_test;

-- Read only role for the Grafana dashboards, local password only
-- Migration 0002 grants it the reporting schema
CREATE ROLE grafana_reader LOGIN PASSWORD 'grafana-reader';

\c chatbot
CREATE EXTENSION IF NOT EXISTS vector;

\c chatbot_test
CREATE EXTENSION IF NOT EXISTS vector;
