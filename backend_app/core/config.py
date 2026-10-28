from pydantic_settings import BaseSettings, SettingsConfigDict
# Name of the settings class and env should be same
class Settings(BaseSettings):

    PROJECT_NAME:str = "USER MANAGEMENT SYSTEM"
    VERSION:str= "1.0.0"

    
    MONGO_URL :str="mongodb://localhost:27017/"
    DATABASE_NAME:str="backend_db"


    SECRET_KEY:str = "i_am_king"

    ALGORITHM :str = 'HS256'
    ACCESS_TOKEN_EXPIRE_TIME:int = 30
    GROQ_API_KEY: str = ""


    model_config = SettingsConfigDict(
        env_file = ".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )



settings = Settings()