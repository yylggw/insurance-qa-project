import json  # json数据处理库
# Literal: 字面量类型, 里边是多个值, 要求大模型生成的结果要从中选取一个
# Optional: 可选类型, 表示该参数可以为空
# Union: 联合类型, 表示该参数可以是多个类型中的一个
# List: 列表类型
from typing import Literal, Optional, Union, List  # 类型库

from langchain_core.output_parsers import JsonOutputParser  # json输出解析器
from langchain_core.prompts import PromptTemplate  # 提示词模板
from pydantic import BaseModel  # pydantic中定义数据模型, 继承了这个类以后, 数据就可以自动进行数据校验
from common.llm import my_llm  # 大模型
import os
# 在真实的生产环境下, 可能是多个服务器同时工作, 需要使用专门的消息队列中间件来进行任务的保存, 常见的消息队列中间件有kafka, RedditMQ, RocketMQ
import queue
import threading
from tqdm import tqdm

# ======================
# 枚举定义
# ======================
EntityType = Literal["PolicyDoc", "ReimburseRule", "Disease", "InsureType", "Medicine", "TreatItem", "Agency"]

RelationType = Literal[
    "STIPULATES",               # PolicyDoc → ReimburseRule（规定）
    "RESTRICTS_DISEASE",        # ReimburseRule → Disease（限制病种）
    "APPLIES_TO",               # ReimburseRule → InsureType（适用）
    "BELONGS_TO_SPECIAL_DISEASE",  # Disease → InsureType（属于慢特病）
    "CAN_USE",                  # Disease → Medicine / TreatItem（可使用）
    "EXECUTED_BY",              # TreatItem → Agency（执行机构）
    "INCLUDED_IN"               # Disease → PolicyDoc（纳入）
]


# ======================
# 属性定义
# ======================
class PolicyDocAttributes(BaseModel):
    """政策文件属性"""
    doc_code: Optional[str] = None          # 文件编号
    policy_type: Optional[str] = None       # 政策类型（药品目录/慢特病目录等）
    publish_org: Optional[str] = None       # 发布机构
    effective_date: Optional[str] = None    # 生效日期


class ReimburseRuleAttributes(BaseModel):
    """报销规则属性"""
    rule_type: Optional[str] = None         # 规则类型（门诊慢病/住院报销等）
    reimburse_ratio: Optional[str] = None   # 报销比例
    deductible: Optional[str] = None        # 起付线
    ceiling: Optional[str] = None           # 封顶线


class DiseaseAttributes(BaseModel):
    """疾病属性"""
    disease_code: Optional[str] = None      # ICD-10编码
    disease_name: Optional[str] = None      # 疾病名称
    is_special: Optional[bool] = None       # 是否慢特病


class InsureTypeAttributes(BaseModel):
    """参保类型属性"""
    insure_code: Optional[str] = None       # 参保类型代码
    target_group: Optional[str] = None      # 参保对象


class MedicineAttributes(BaseModel):
    """药品属性"""
    medicine_code: Optional[str] = None     # 药品代码
    insurance_class: Optional[str] = None   # 医保类别（甲类/乙类）


class TreatItemAttributes(BaseModel):
    """诊疗项目属性"""
    item_code: Optional[str] = None         # 项目代码
    item_category: Optional[str] = None     # 项目类别
    insurance_class: Optional[str] = None   # 医保类别


class AgencyAttributes(BaseModel):
    """经办机构属性"""
    agency_code: Optional[str] = None       # 机构代码
    region: Optional[str] = None            # 所属地区


# ======================
# 实体与关系结构
# ======================
class Entity(BaseModel):
    name: str
    type: EntityType
    attributes: Optional[Union[
        PolicyDocAttributes, ReimburseRuleAttributes, DiseaseAttributes,
        InsureTypeAttributes, MedicineAttributes, TreatItemAttributes, AgencyAttributes
    ]] = None


class Relation(BaseModel):
    subject: str
    subject_type: EntityType
    relation: RelationType
    object: str
    object_type: EntityType


class InsuranceKnowledgeGraph(BaseModel):
    entities: List[Entity]
    relations: List[Relation]


# 初始化解析器
parser = JsonOutputParser(pydantic_object=InsuranceKnowledgeGraph)

# 定义 Prompt
prompt = PromptTemplate(
    template=(
        "你是一个医保政策知识图谱抽取专家。请从以下文本中提取结构化知识：\n"
        "仅当文本中存在实体之间的明确关系时才进行抽取，例如：\n"
        "- 某政策文件规定了某报销规则\n"
        "- 某报销规则限制某病种、适用某参保类型\n"
        "- 某疾病可使用某药品或诊疗项目\n"
        "- 某疾病被纳入某政策文件\n"
        "- 某诊疗项目由某经办机构执行\n"
        "如果文本中未涉及实体之间的关系，请返回空结构：\n"
        "{{\"entities\": [], \"relations\": []}}\n\n"
        "【实体类型说明】\n"
        "- PolicyDoc：政策文件，如《国家基本医疗保险药品目录》《门诊慢特病保障方案》等\n"
        "- ReimburseRule：报销规则，如高血压门诊报销规则、冠心病住院报销规则等\n"
        "- Disease：疾病病种，如高血压、2型糖尿病、肺恶性肿瘤等\n"
        "- InsureType：参保类型，如职工基本医疗保险、城乡居民基本医疗保险、大病保险等\n"
        "- Medicine：药品，如阿莫西林、二甲双胍、奥希替尼等\n"
        "- TreatItem：诊疗项目，如血常规检查、血液透析、冠状动脉支架植入术等\n"
        "- Agency：经办机构，如北京市医疗保险事务管理中心等\n\n"
        "【关系类型说明】\n"
        "- STIPULATES：政策文件规定了某报销规则（PolicyDoc → ReimburseRule）\n"
        "- RESTRICTS_DISEASE：报销规则限制某病种（ReimburseRule → Disease）\n"
        "- APPLIES_TO：报销规则适用某参保类型（ReimburseRule → InsureType）\n"
        "- BELONGS_TO_SPECIAL_DISEASE：疾病属于某参保类型的慢特病（Disease → InsureType）\n"
        "- CAN_USE：疾病可使用某药品或诊疗项目（Disease → Medicine / TreatItem）\n"
        "- EXECUTED_BY：诊疗项目由某经办机构执行（TreatItem → Agency）\n"
        "- INCLUDED_IN：疾病被纳入某政策文件（Disease → PolicyDoc）\n\n"
        "请根据文本内容为对应实体补充属性字段，如果值为空则不必显示该键。\n"
        "所有输出必须严格符合以下 JSON 格式：\n"
        "{format_instructions}\n\n"
        "输入文本：{text}"
    ),
    input_variables=["text"],
    partial_variables={"format_instructions": parser.get_format_instructions()}
)


# ======================
# 主函数封装
# ======================
def extract_insurance_knowledge(text: str):
    chain = prompt | my_llm | parser
    return chain.invoke({"text": text})


def load_existing_results(save_path: str):
    """加载已存在的JSON结果，用于断点续跑"""
    if os.path.exists(save_path):
        with open(save_path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict) and "results" in data:
                    return data
            except json.JSONDecodeError:
                pass
    return {"results": []}


def save_results(data: dict, save_path: str):
    """将当前结果保存到JSON"""
    with open(save_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ======================
# 生产者消费者模式
# ======================
NUM_CONSUMERS = 5  # 消费者线程数
SENTINEL = None  # 队列结束标志


def producer(folder_path: str, to_process: list, task_queue: queue.Queue, pbar: tqdm):
    """
    生产者：遍历文件，读取内容，将任务放入队列
    """
    for filename in to_process:
        file_path = os.path.join(folder_path, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                text = f.read().strip()
            if not text:
                tqdm.write(f"⚠️ 文件为空：{filename}")
                pbar.update(1)
                continue
            task_queue.put((filename, text))
        except Exception as e:
            tqdm.write(f"❌ 读取失败：{filename}, 错误：{e}")
            pbar.update(1)

    # 放入哨兵值，通知消费者结束
    for _ in range(NUM_CONSUMERS):
        task_queue.put(SENTINEL)


def consumer(task_queue: queue.Queue, all_results: dict, finetune_data: list,
             save_path: str, finetune_save_path: str, lock: threading.Lock,
             pbar: tqdm, counter: dict):
    """
    消费者：从队列取任务，调用大模型抽取，保存结果
    """
    while True:
        item = task_queue.get()
        if item is SENTINEL:
            task_queue.task_done()
            break

        filename, text = item

        try:
            # 调用大模型抽取医保知识图谱
            result_dict = extract_insurance_knowledge(text)

            # 线程安全地保存结果
            with lock:
                record = {
                    "filename": filename,
                    "extract_dict": result_dict
                }
                all_results["results"].append(record)
                save_results(all_results, save_path)
                tqdm.write(f"✅ 已保存结果：{filename}")

                # 保存微调格式数据
                finetune_item = {
                    "instruction": "请从以下医保政策文本中抽取知识图谱结构，包括实体与关系。",
                    "input": text,
                    "output": json.dumps(
                        result_dict,
                        ensure_ascii=False,
                        indent=2
                    )
                }
                finetune_data.append(finetune_item)
                with open(finetune_save_path, "w", encoding="utf-8") as f:
                    json.dump(finetune_data, f, ensure_ascii=False, indent=2)
                tqdm.write(f"📘 已追加微调数据：{filename}")

                with counter["lock"]:
                    counter["success"] += 1
        except Exception as e:
            tqdm.write(f"❌ 处理失败：{filename}, 错误：{e}")
            with counter["lock"]:
                counter["fail"] += 1
        finally:
            pbar.update(1)
            task_queue.task_done()


def extract_from_folder(folder_path: str, save_path: str, finetune_save_path: str):
    """
    从文件夹中抽取医保政策知识图谱（生产者消费者模式）
    :param folder_path: 数据源文件夹
    :param save_path: 结果保存路径
    :param finetune_save_path: 微调数据保存路径
    :return:
    """
    # all_results表示的是已经跑出来的结果
    all_results = load_existing_results(save_path)
    # processed_files表示的是已经处理过的文件
    processed_files = {r["filename"] for r in all_results["results"]}

    # 用于存储微调数据
    finetune_data = []
    if os.path.exists(finetune_save_path):
        with open(finetune_save_path, "r", encoding="utf-8") as f:
            try:
                finetune_data = json.load(f)
            except json.JSONDecodeError:
                pass

    # txt_files文件夹中的所有文件
    txt_files = [f for f in os.listdir(folder_path) if f.endswith(".txt")]
    print(f"🔍 共发现 {len(txt_files)} 个文本文件。")

    # 过滤掉已处理的文件
    to_process = [f for f in txt_files if f not in processed_files]
    skipped = len(txt_files) - len(to_process)
    if skipped > 0:
        print(f"⏭ 跳过已处理文件：{skipped} 个")
    print(f"📝 待处理文件：{len(to_process)} 个，生产者1线程 + 消费者{NUM_CONSUMERS}线程。")

    if not to_process:
        print("没有需要处理的文件，已全部完成！")
        return

    # 创建任务队列
    task_queue = queue.Queue()
    # 线程锁，保护共享状态和文件写入
    lock = threading.Lock()
    # 计数器
    counter = {"success": 0, "fail": 0, "lock": threading.Lock()}

    print(f"\n开始抽取（生产者消费者模式，{NUM_CONSUMERS} 个消费者线程）...")

    with tqdm(total=len(to_process), desc="处理中...") as pbar:
        # 启动消费者线程
        consumers = []
        for i in range(NUM_CONSUMERS):
            t = threading.Thread(
                target=consumer,
                args=(task_queue, all_results, finetune_data, save_path,
                      finetune_save_path, lock, pbar, counter),
                name=f"consumer-{i+1}"
            )
            t.start()
            consumers.append(t)

        # 启动生产者线程
        producer_thread = threading.Thread(
            target=producer,
            args=(folder_path, to_process, task_queue, pbar),
            name="producer"
        )
        producer_thread.start()

        # 等待生产者完成
        producer_thread.join()
        # 等待所有消费者完成
        for t in consumers:
            t.join()

    print(f"\n🎯 处理完成，共抽取 {len(all_results['results'])} 个文件结果。"
          f"成功: {counter['success']}, 失败: {counter['fail']}")


if __name__ == '__main__':
    text = """
    《门诊慢特病病种范围及保障方案》（POL-2024-003）由国家医疗保障局于2024年2月20日发布，
    自2024年4月1日起施行。该方案将高血压（I10）、2型糖尿病（E11）、慢性阻塞性肺病（J44）、
    慢性肾脏病（N18）纳入门诊慢特病保障范围。

    其中，高血压门诊报销规则规定：职工基本医疗保险报销比例为70%，起付线200元，封顶线3000元；
    城乡居民基本医疗保险报销比例为60%，起付线200元，封顶线2000元。
    高血压患者可使用药品包括硝苯地平、氨氯地平、缬沙坦等。
    高血压属于职工基本医疗保险和城乡居民基本医疗保险的慢特病病种。

    糖尿病门诊报销规则规定：职工基本医疗保险报销比例为70%，起付线200元，封顶线3500元；
    城乡居民基本医疗保险报销比例为60%，起付线200元，封顶线2500元。
    糖尿病患者可使用药品包括二甲双胍、格列美脲、胰岛素等。
    糖尿病患者可使用诊疗项目包括血糖测定、糖化血红蛋白测定等。

    慢性肾脏病门诊特病报销规则：职工基本医疗保险报销比例90%，起付线0元，封顶线80000元。
    慢性肾脏病患者可使用诊疗项目包括血液透析、腹膜透析。
    上述诊疗项目由各地医疗保险事务管理中心负责执行。
    """
    result = extract_insurance_knowledge(text=text)
    print(result)