from sqlalchemy.ext.declarative import declarative_base

# Declarative base for models and alembic autogenerate
Base = declarative_base()

# Import models here so they are included in metadata for Alembic autogenerate
# NOTE: keep import order stable; add new models in modules under app.db.models
from app.db.models import user  # noqa: E402,F401
from app.db.models import role  # noqa: E402,F401
from app.db.models import patient  # noqa: E402,F401
from app.db.models import study  # noqa: E402,F401
from app.db.models import image  # noqa: E402,F401
from app.db.models import analysis_result  # noqa: E402,F401
from app.db.models import visualization  # noqa: E402,F401
from app.db.models import task  # noqa: E402,F401
from app.db.models import report  # noqa: E402,F401
from app.db.models import notification  # noqa: E402,F401
