"""数据生成入口：遍历 manifest → 运行 builder → 输出到 MySQL schema"""

import sys
import importlib
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES_DIR = BASE_DIR / "databases"
BUILDERS_DIR = Path(__file__).resolve().parent / "builders"

sys.path.insert(0, str(BASE_DIR))
from data_builder import db as mysql_db
from data_builder.manifest import CATEGORIES, get_all_problems


def ensure_db(category):
    """每个 category 一个 MySQL schema：DROP 后重建，替代原删 .db 文件逻辑"""
    schema = category.db_file[:-3]  # "01_continuous_login.db" -> "01_continuous_login"
    return mysql_db.reset_schema(schema)


def run_all():
    """运行所有 builder 生成数据"""
    # 收集哪些 builder 需要运行
    builders_to_run = set()
    for prob in get_all_problems():
        if prob.tables:  # 有表的题目才需要 builder
            builders_to_run.add(prob.category_id)

    print(f"Building databases for {len(builders_to_run)} categories...")

    for cat in CATEGORIES:
        if cat.id not in builders_to_run:
            continue

        module_name = f"data_builder.builders.{cat.db_file.replace('.db', '')}"
        try:
            mod = importlib.import_module(module_name)
        except ImportError:
            print(f"  ⚠️  No builder found for {cat.id} ({cat.name}), skipping")
            continue

        conn = ensure_db(cat)
        print(f"  📦 {cat.name} ({cat.db_file})")

        if hasattr(mod, 'build'):
            mod.build(conn)
            print(f"     ✅ build() completed")

        conn.commit()

        # 打印表信息
        tables = conn.execute(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = DATABASE() ORDER BY table_name"
        ).fetchall()
        table_names = [t[0] for t in tables]
        for tname in table_names:
            cnt = conn.execute(f"SELECT COUNT(*) FROM `{tname}`").fetchone()[0]
            print(f"     📊 {tname}: {cnt} rows")

        conn.close()

    # 重建 progress.db 中的题目数据（以防 manifest 变更）
    from backend.database import init_progress_db, seed_problems
    init_progress_db()
    seed_problems()

    print(f"\nDone! {len(builders_to_run)} databases in {DATABASES_DIR}/")


if __name__ == "__main__":
    try:
        mysql_db.wait_for_mysql(timeout=30)
    except SystemExit:
        print("⚠️  MySQL 首次连接失败，5 秒后重试一次...")
        time.sleep(5)
        try:
            mysql_db.wait_for_mysql(timeout=30)
        except SystemExit as e:
            raise SystemExit(f"{e}\n请检查容器状态：docker compose ps && docker compose logs mysql")
    run_all()
