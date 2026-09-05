from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./research_nexus.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Paper(Base):
    __tablename__ = "papers"

    paper_id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    abstract = Column(String)
    authors = Column(String)
    publication_year = Column(Integer)
    doi = Column(String)
    citation_count = Column(Integer)
    keywords = Column(String)
    source = Column(String)
    full_text_available = Column(Boolean)

    concepts = relationship("PaperConcept", back_populates="paper")

class Concept(Base):
    __tablename__ = "concepts"

    concept_id = Column(Integer, primary_key=True, autoincrement=True)
    concept_name = Column(String, unique=True, nullable=False)
    concept_type = Column(String)

    papers = relationship("PaperConcept", back_populates="concept")

class PaperConcept(Base):
    __tablename__ = "paper_concepts"

    paper_id = Column(String, ForeignKey("papers.paper_id"), primary_key=True)
    concept_id = Column(Integer, ForeignKey("concepts.concept_id"), primary_key=True)

    paper = relationship("Paper", back_populates="concepts")
    concept = relationship("Concept", back_populates="papers")