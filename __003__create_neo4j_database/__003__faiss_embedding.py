from common.neo4j_manager import neo4j_client
import pickle
import faiss
from common.embedding_model import embedding_model


def build_faiss_index(sentences, index_path="faiss.index", mapping_path="id2text.pkl"):
    """
    基于字符串列表构建 FAISS 索引并保存
    :param sentences: List[str] 输入的文本列表
    :param index_path: FAISS 索引保存路径
    :param mapping_path: id->原始文本映射保存路径
    """
    # 1. 加载预训练文本向量模型

    # 2. 生成向量
    embeddings = embedding_model.encode(sentences, convert_to_numpy=True, normalize_embeddings=True)
    # 3. 构建 FAISS 索引
    # embeddings 是二维 numpy 数组：[文本数量, 向量维度] 比如 1000 条文本，每条 768 维向量 → shape=(1000,768)，shape[1]=768。
    dim = embeddings.shape[1]
    # 调用 FAISS 库里面的 IndexFlatL2 类，实例化一个空的向量收纳容器（索引实例），只负责一件事：存向量、算 L2 距离、相似度检索。
    index = faiss.IndexFlatL2(dim)  # L2距离,欧式距离
    index.add(embeddings)           # 把所有向量放进上面创建的收纳箱（索引）里

    # 4. 保存索引
    faiss.write_index(index, index_path)        # write_index()是保存FAISS索引的函数(faiss自带的)

    # 5. 保存 id -> 原始文本 映射                   # 为什么做这一步呢？ 因为FAISS只存向量数字，不存原始文本！
    id2text = {i: s for i, s in enumerate(sentences)}
    with open(mapping_path, "wb") as f:
        pickle.dump(id2text, f)

    print(f"✅ 索引已保存到 {index_path}, 映射保存到 {mapping_path}")


# 获取所有节点名称
node_names = neo4j_client.get_all_node_names()

# 将节点进行向量化
build_faiss_index(node_names, index_path="nero4j_embedding_faiss.index",
                  mapping_path="nero4j_embedding_faiss_id2text.pkl")
