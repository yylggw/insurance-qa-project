from __002__extract_information.__000__生产者消费者模式抽取知识图谱数据 import extract_from_folder
from common.path_utils import get_file_path

extract_from_folder(get_file_path("__001__clawler/疾病"),
                    get_file_path("__002__extract_information/extract_disease_data.json"),
                    get_file_path("__002__extract_information/extract_disease_finetune_data.json"))
