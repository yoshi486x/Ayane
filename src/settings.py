import functools
import os
import dotenv


class Settings:
    config = dotenv.load_dotenv(".env")
    engine_path: str = os.getenv("ENGINE_PATH")
    if engine_path is None:
        print("Please set ENGINE_PATH environment variable.")
        # exit(1)
    kifu_path: str = os.getenv("KIFU_PATH")

@functools.lru_cache()
def get_settings():
    return Settings()