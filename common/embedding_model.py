from sentence_transformers import SentenceTransformer   # 是一个用于生成句子嵌入的库
from common.config import Config

conf = Config()

embedding_model = SentenceTransformer(conf.EMBEDDING_MODEL_PATH)