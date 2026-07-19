"""数据生成入口：遍历 manifest → 运行 builder → 输出 SQLite 文件"""

import sys
import importlib
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATABASES_DIR = BASE_DIR / "databases"
BUILDERS_DIR = Path(__file__).resolve().parent / "builders"

sys.path.insert(0, str(BASE_DIR))
from data_builder.manifest import CATEGORIES, get_all_problems


def ensure_db(category):
    """为专题创建空白 SQLite 文件"""
    DATABASES_DIR.mkdir(parents=True, exist_ok=True)
    db_path = DATABASES_DIR / category.db_file
    if db_path.exists():
        db_path.unlink()  # 重建，确保数据一致
    return sqlite3.connect(str(db_path))


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
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        for (tname,) in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {tname}").fetchone()[0]
            print(f"     📊 {tname}: {count} rows")

        conn.close()

    # 重建 progress.db 中的题目数据（以防 manifest 变更）
    from backend.database import init_progress_db, seed_problems
    init_progress_db()
    seed_problems()

    print(f"\nDone! {len(builders_to_run)} databases in {DATABASES_DIR}/")


if __name__ == "__main__":
    run_all()
