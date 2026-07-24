from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.session import get_db


DatabaseSession = Annotated[Session, Depends(get_db)]

# TODO: Add current-user, current-library, and role authorization dependencies.
