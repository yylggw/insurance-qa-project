from common.neo4j_manager import neo4j_client
from common.path_utils import get_file_path

# 导出 Neo4j 数据库中所有元数据（标签、关系、三元组、属性、统计信息）
output_path = get_file_path("__003__create_neo4j_database/insurance_metadata.json")
neo4j_client.export_metadata_to_json(output_path)
