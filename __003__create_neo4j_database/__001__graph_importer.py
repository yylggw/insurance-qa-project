import csv

from common.neo4j_manager import neo4j_client
from common.path_utils import get_file_path
from tqdm import tqdm


# ======================
# 医保知识图谱导入逻辑
# 从 __000__data 提取的 CSV 文件导入实体和关系到 Neo4j
# ======================
class InsuranceGraphImporter:
    BATCH_SIZE = 500  # 批量导入大小

    def __init__(self, neo4j_client):
        self.neo4j_client = neo4j_client

    # ---------- 通用工具方法 ----------

    def _batch_merge_entities(self, label, entities):
        """批量 MERGE 实体节点，带 tqdm 进度条"""
        for i in tqdm(range(0, len(entities), self.BATCH_SIZE),
                      desc=f"  实体[{label}]"):
            batch = entities[i:i + self.BATCH_SIZE]
            queries = []
            for ent in batch:
                name = ent["name"]
                attrs = ent.get("attributes", {})
                if attrs:
                    set_clause = ", ".join([f"n.{k} = ${k}" for k in attrs])
                    cypher = (f"MERGE (n:{label} {{name: $name}}) SET {set_clause}",
                              {"name": name, **attrs})
                else:
                    cypher = (f"MERGE (n:{label} {{name: $name}})", {"name": name})
                queries.append(cypher)
            self.neo4j_client.run_multiple_cypher(queries)

    def _batch_merge_relations(self, rel_type, subject_label, object_label, relations):
        """批量 MERGE 关系，带 tqdm 进度条"""
        for i in tqdm(range(0, len(relations), self.BATCH_SIZE),
                      desc=f"  关系[{rel_type}]"):
            batch = relations[i:i + self.BATCH_SIZE]
            queries = []
            for rel in batch:
                cypher = (
                    f"MATCH (a:{subject_label} {{name: $subject}}), "
                    f"(b:{object_label} {{name: $object}}) "
                    f"MERGE (a)-[r:{rel_type}]->(b)",
                    {"subject": rel["subject"], "object": rel["object"]}
                )
                queries.append(cypher)
            self.neo4j_client.run_multiple_cypher(queries)

    # ---------- 各类实体导入方法 ----------

    def import_agency(self):
        """导入经办机构"""
        csv_path = get_file_path("__001__clawler/agency.csv")
        entities = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entities.append({
                    "name": row["经办机构名称"],
                    "attributes": {
                        "agency_code": row["经办机构代码"],
                        "level": row["机构级别"],
                        "agency_type": row["机构类型"],
                        "region": row["所属地区"],
                        "phone": row["联系电话"],
                        "address": row["地址"],
                    }
                })
        self._batch_merge_entities("Agency", entities)
        print(f"  ✅ Agency 导入完成，共 {len(entities)} 条")

    def import_policy_doc(self):
        """导入政策文件"""
        csv_path = get_file_path("__001__clawler/policy_doc.csv")
        entities = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entities.append({
                    "name": row["政策文件名称"],
                    "attributes": {
                        "doc_code": row["政策文件代码"],
                        "policy_type": row["政策类型"],
                        "publish_org": row["发布机构"],
                        "publish_date": row["发布日期"],
                        "effective_date": row["生效日期"],
                        "status": row["状态"],
                        "remark": row.get("备注", ""),
                    }
                })
        self._batch_merge_entities("PolicyDoc", entities)
        print(f"  ✅ PolicyDoc 导入完成，共 {len(entities)} 条")

    def import_insure_type(self):
        """导入参保类型"""
        csv_path = get_file_path("__001__clawler/insure_type.csv")
        entities = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entities.append({
                    "name": row["参保类型名称"],
                    "attributes": {
                        "insure_code": row["参保类型代码"],
                        "target_group": row["参保对象"],
                        "payment_method": row["缴费方式"],
                        "benefit_type": row["待遇类型"],
                        "remark": row.get("备注", ""),
                    }
                })
        self._batch_merge_entities("InsureType", entities)
        print(f"  ✅ InsureType 导入完成，共 {len(entities)} 条")

    def import_disease(self):
        """导入疾病（ICD-10）"""
        csv_path = get_file_path("__001__clawler/disease_full_data.csv")
        entities = []
        seen_names = set()
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                diag_code = row.get("诊断代码", "").strip()
                diag_name = row.get("诊断名称", "").strip()
                if not diag_code or not diag_name:
                    continue
                if diag_code == "诊断代码":
                    continue
                unique_key = f"{diag_code}_{diag_name}"
                if unique_key in seen_names:
                    continue
                seen_names.add(unique_key)
                entities.append({
                    "name": diag_name,
                    "attributes": {
                        "disease_code": diag_code,
                        "category_code": row.get("类目代码", "").strip(),
                        "category_name": row.get("类目名称", "").strip(),
                        "sub_category_code": row.get("亚目代码", "").strip(),
                        "sub_category_name": row.get("亚目名称", "").strip(),
                        "chapter": row.get("章", "").strip(),
                        "chapter_code_range": row.get("章代码范围", "").strip(),
                        "chapter_name": row.get("章的名称", "").strip(),
                    }
                })
        self._batch_merge_entities("Disease", entities)
        print(f"  ✅ Disease 导入完成，共 {len(entities)} 条")

    def import_treat_item(self):
        """导入诊疗项目"""
        csv_path = get_file_path("__001__clawler/treat_item.csv")
        entities = []
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                entities.append({
                    "name": row["诊疗项目名称"],
                    "attributes": {
                        "item_code": row["诊疗项目代码"],
                        "item_category": row["项目类别"],
                        "unit": row.get("计价单位", ""),
                        "insurance_class": row["医保类别"],
                        "price_limit": row.get("限价标准", ""),
                        "remark": row.get("备注", ""),
                    }
                })
        self._batch_merge_entities("TreatItem", entities)
        print(f"  ✅ TreatItem 导入完成，共 {len(entities)} 条")

    def import_medicine(self):
        """导入药品（跳过第2-3行元数据行，第1行为表头）"""
        csv_path = get_file_path("__001__clawler/medicine_full_data.csv")
        entities = []
        seen_codes = set()
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            header = next(f)  # 第1行是表头
            next(f)  # 跳过第2行（数据库更新说明）
            next(f)  # 跳过第3行（次要表头）
            reader = csv.DictReader(f, fieldnames=header.strip().split(","))
            for row in reader:
                medicine_code = row.get("药品代码", "").strip()
                medicine_name = row.get("注册名称", "").strip()
                if not medicine_code or not medicine_name:
                    continue
                if medicine_code in seen_codes:
                    continue
                seen_codes.add(medicine_code)
                entities.append({
                    "name": medicine_name,
                    "attributes": {
                        "medicine_code": medicine_code,
                        "dosage_form": row.get("注册剂型", "").strip(),
                        "spec": row.get("注册规格", "").strip(),
                        "manufacturer": row.get("药品企业", "").strip(),
                        "approval_number": row.get("批准文号", "").strip(),
                        "insurance_class": row.get("甲乙类", "").strip(),
                    }
                })
        self._batch_merge_entities("Medicine", entities)
        print(f"  ✅ Medicine 导入完成，共 {len(entities)} 条")

    def import_reimburse_rule(self):
        """导入报销规则，并创建关系"""
        csv_path = get_file_path("__001__clawler/reimburse_rule.csv")

        rule_entities = []
        disease_entities = []
        relations_stipulates = []
        relations_restricts = []
        relations_applies = []
        seen_diseases = set()

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rule_name = row["规则名称"].strip()
                rule_code = row["规则编号"].strip()
                policy_name = row["对应政策文件"].strip()
                disease_name = row["限制病种名称"].strip()
                disease_code = row["限制病种代码"].strip()
                insure_type_name = row["适用参保类型"].strip()

                rule_entities.append({
                    "name": rule_name,
                    "attributes": {
                        "rule_code": rule_code,
                        "rule_type": row["规则类型"].strip(),
                        "reimburse_ratio": row["报销比例"].strip(),
                        "deductible": row["起付线"].strip(),
                        "ceiling": row["封顶线"].strip(),
                        "remark": row.get("备注", "").strip(),
                    }
                })

                if disease_name and disease_name not in seen_diseases:
                    seen_diseases.add(disease_name)
                    attrs = {}
                    if disease_code:
                        attrs["disease_code"] = disease_code
                    disease_entities.append({"name": disease_name, "attributes": attrs})

                if policy_name:
                    relations_stipulates.append({
                        "subject": policy_name, "object": rule_name,
                    })
                if disease_name:
                    relations_restricts.append({
                        "subject": rule_name, "object": disease_name,
                    })
                if insure_type_name:
                    relations_applies.append({
                        "subject": rule_name, "object": insure_type_name,
                    })

        self._batch_merge_entities("ReimburseRule", rule_entities)
        print(f"  ✅ ReimburseRule 导入完成，共 {len(rule_entities)} 条")

        if disease_entities:
            self._batch_merge_entities("Disease", disease_entities)
            print(f"  ✅ Disease(报销规则补充) 导入完成，共 {len(disease_entities)} 条")

        if relations_stipulates:
            self._batch_merge_relations("STIPULATES", "PolicyDoc", "ReimburseRule",
                                        relations_stipulates)
            print(f"  ✅ STIPULATES 关系导入完成，共 {len(relations_stipulates)} 条")

        if relations_restricts:
            self._batch_merge_relations("RESTRICTS_DISEASE", "ReimburseRule", "Disease",
                                        relations_restricts)
            print(f"  ✅ RESTRICTS_DISEASE 关系导入完成，共 {len(relations_restricts)} 条")

        if relations_applies:
            self._batch_merge_relations("APPLIES_TO", "ReimburseRule", "InsureType",
                                        relations_applies)
            print(f"  ✅ APPLIES_TO 关系导入完成，共 {len(relations_applies)} 条")

    def import_extra_relations(self):
        """导入补充关系（慢特病、可使用药品/诊疗项目、执行机构、纳入政策）"""
        csv_path = get_file_path("__001__clawler/graph_extra_relations.csv")

        relations_by_type = {}  # {(rel_type, subject_label, object_label): [relations]}
        nodes_to_ensure = set()  # {(label, name)}

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rel_type = row["关系类型"].strip()
                subject_label = row["主体类型"].strip()
                subject_name = row["主体名称"].strip()
                object_label = row["客体类型"].strip()
                object_name = row["客体名称"].strip()

                key = (rel_type, subject_label, object_label)
                if key not in relations_by_type:
                    relations_by_type[key] = []
                relations_by_type[key].append({
                    "subject": subject_name,
                    "object": object_name
                })
                nodes_to_ensure.add((subject_label, subject_name))
                nodes_to_ensure.add((object_label, object_name))

        # 先确保所有引用的节点存在（不存在则自动创建）
        ensure_queries = []
        for label, name in nodes_to_ensure:
            ensure_queries.append(
                (f"MERGE (n:{label} {{name: $name}})", {"name": name})
            )
        self.neo4j_client.run_multiple_cypher(ensure_queries)
        print(f"  ✅ 已确保 {len(nodes_to_ensure)} 个引用节点存在")

        # 再创建关系
        # 再创建关系
        for (rel_type, subject_label, object_label), relations in relations_by_type.items():
            self._batch_merge_relations(rel_type, subject_label, object_label, relations)
            print(f"  ✅ {rel_type} ({subject_label}→{object_label}) 关系导入完成，共 {len(relations)} 条")

    # ---------- 总入口 ----------

    def import_all(self):
        """按顺序导入所有实体和关系"""
        steps = [
            ("经办机构 (Agency)", self.import_agency),
            ("政策文件 (PolicyDoc)", self.import_policy_doc),
            ("参保类型 (InsureType)", self.import_insure_type),
            ("疾病 (Disease)", self.import_disease),
            ("诊疗项目 (TreatItem)", self.import_treat_item),
            ("药品 (Medicine)", self.import_medicine),
            ("报销规则 (ReimburseRule) + 关系", self.import_reimburse_rule),
            ("补充关系 (慢特病/可使用/执行机构/纳入)", self.import_extra_relations),
        ]

        for step_name, step_func in steps:
            print(f"\n{'=' * 50}")
            print(f"📂 正在导入: {step_name}")
            print(f"{'=' * 50}")
            try:
                step_func()
            except Exception as e:
                print(f"❌ 导入 {step_name} 时出错: {e}")
                continue

        print(f"\n{'=' * 50}")
        print("✅ 所有医保知识图谱数据已成功导入 Neo4j 数据库！")
        print(f"{'=' * 50}")


if __name__ == "__main__":
    importer = InsuranceGraphImporter(neo4j_client)
    importer.import_all()
