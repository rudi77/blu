from sqlalchemy import Column, String, Text, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from ..config import get_settings
from typing import Optional

Base = declarative_base()

class Prompt(Base):
    __tablename__ = "prompts"
    
    doc_type = Column(String, primary_key=True)
    prompt_text = Column(Text, nullable=False)

class PromptStore:
    def __init__(self):
        settings = get_settings()
        self.engine = create_engine(settings.database_url)
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    
    async def store_prompt(self, doc_type: str, prompt: str) -> bool:
        session = self.Session()
        try:
            prompt_obj = Prompt(doc_type=doc_type, prompt_text=prompt)
            session.merge(prompt_obj)
            session.commit()
            return True
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
            
    async def get_prompt(self, doc_type: str) -> Optional[str]:
        session = self.Session()
        try:
            prompt = session.query(Prompt).filter_by(doc_type=doc_type).first()
            return prompt.prompt_text if prompt else None
        finally:
            session.close() 