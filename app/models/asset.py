from sqlalchemy import Column, String, JSON, LargeBinary, Integer
from app.models import Base


class Asset(Base):
    """Asset model for storing metadata about D&D assets"""
    __tablename__ = "assets"

    id = Column(String, primary_key=True)  # e.g., "fa-goblin-warrior-01"
    name = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    asset_type = Column(String, nullable=False)  # token, map, prop, etc.
    tags = Column(JSON)  # List of tags for searching
    source = Column(String, nullable=False)  # forgotten_adventures, caeora
    dimensions = Column(JSON)  # {width, height}
    attribution = Column(String)
    embedding = Column(LargeBinary)  # For semantic search

    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "file_path": self.file_path,
            "type": self.asset_type,
            "tags": self.tags or [],
            "source": self.source,
            "dimensions": self.dimensions,
            "attribution": self.attribution
        }
