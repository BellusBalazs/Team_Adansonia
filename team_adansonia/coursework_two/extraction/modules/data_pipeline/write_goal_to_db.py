import datetime
from team_adansonia.coursework_two.extraction.modules.mongo_db.company_data import connect_to_mongo
# 导入 goal_extractor 中的函数
from team_adansonia.coursework_two.extraction.modules.data_pipeline.goal_extractor import extract_goals_by_page, call_deepseek_find_goals

def write_goal_to_db(symbol: str, company_name: str, goals_text: str):
    """
    将提取的公司目标写入 MongoDB 数据库。

    Args:
        symbol (str): 公司的股票代码。
        company_name (str): 公司的名称。
        goals_text (str): 从报告中提取的目标文本。
    """
    mongo_client = connect_to_mongo()
    if mongo_client:
        db = mongo_client["csr_reports"]  # 使用数据库名称
        companies_collection = db["companies"]  # 使用集合名称

        try:
            result = companies_collection.update_one(
                {"symbol": symbol},  # 根据公司符号查找
                {
                    "$set": {
                        "emission_goals": goals_text,  # 设置 emission_goals 字段
                        "updated_at": datetime.datetime.utcnow()  # 更新时间戳
                    }
                }
            )
            if result.modified_count > 0:
                print(f"✅ Successfully updated goals for {company_name} ({symbol}) in the database.")
            elif result.matched_count > 0:
                print(f"⚠️ Goals for {company_name} ({symbol}) were already up to date.")
            else:
                print(f"⚠️ Company {company_name} ({symbol}) not found in the database.")
        except Exception as e:
            print(f"❌ Error updating goals for {company_name} ({symbol}) in the database: {e}")
        finally:
            mongo_client.close()  # 关闭连接
    else:
        print(f"❌ Failed to connect to MongoDB. Goals for {company_name} ({symbol}) were not saved.")

# 主执行逻辑：提取目标并写入数据库
if __name__ == '__main__':
    # --- 配置 --- (根据实际情况修改)
    company = "NVIDIA"  # 示例公司名称
    symbol = "NVDA"     # 示例公司股票代码
    # 注意: 实际运行时需要确保 pdf_path 指向正确的文件
    pdf_path = "filtered_report.pdf" # 示例 PDF 路径 (需要存在于运行目录下或提供绝对路径)
    # --- 配置结束 ---

    print(f"Starting goal extraction and writing process for {company} ({symbol})...")

    # 1. 从 PDF 提取相关文本
    print(f"Extracting goal-related text from {pdf_path}...")
    extracted_text = extract_goals_by_page(pdf_path) # 或者使用 extract_goals_by_paragraph

    if not extracted_text:
        print(f"❌ Could not extract relevant text from {pdf_path}. Aborting.")
    else:
        print("Text extracted successfully. Calling AI to find goals...")
        # 2. 调用 AI 获取目标总结
        goals = call_deepseek_find_goals(company, extracted_text)

        if not goals or goals.strip().lower() == 'n/a': # 检查 AI 是否返回有效目标
            print(f"❌ AI did not find specific goals for {company} ({symbol}) or returned N/A.")
        else:
            print("Goals obtained from AI:")
            print("--------------------------------")
            print(goals)
            print("--------------------------------")
            # 3. 将目标写入数据库
            print(f"Attempting to write goals to database...")
            write_goal_to_db(symbol, company, goals)

    print("Process finished.")
