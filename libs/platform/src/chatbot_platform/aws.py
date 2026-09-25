"""AWS adapters for phase 2. Stub owned by Lane A, implement it at milestone M5.

What already works on AWS without changes
S3ObjectStore talks to Amazon S3 when s3_endpoint_url is empty.
Registry and PgServingIndex talk to RDS Postgres with pgvector through database_url.

What to build here
open_glue_catalog returns a PyIceberg GlueCatalog with the warehouse on S3. It replaces open_catalog
in lake.py when a new setting catalog_type equals glue. Keep the table definitions in lake.TABLES.
Credentials come from the task role, never from settings.
Athena for analytics goes into query_engine.py, not here.

How to test
Add an integration test marked integration that runs only when AWS credentials are present.
"""

from pyiceberg.catalog import Catalog

from chatbot_platform.settings import PlatformSettings


def open_glue_catalog(settings: PlatformSettings) -> Catalog:
    raise NotImplementedError("Glue catalog is a phase 2 task, see the module docstring")
