from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    BOT_TOKEN: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        
    def get_db_url(self):
        return "mysql+asyncmy://%s:%s@%s:%s/%s" % (self.DB_USER, self.DB_PASSWORD, self.DB_HOST, self.DB_PORT, self.DB_NAME)

settings = Settings()