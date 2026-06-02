"""
=============================================
 数据库建表脚本
 跑一次即可：python init_db.py
 作用：
   1. 根据 models.py 中的类定义自动创建所有表
   2. 向 categories 表中插入预设分类数据
=============================================
"""
from app import app, db
from models import Category

# 用 app.app_context() 创建应用上下文
# Flask-SQLAlchemy 在执行数据库操作时需要知道当前是哪个 Flask 应用
with app.app_context():
    # ---- 第一步：建表 ----
    # create_all() 会扫描所有继承 db.Model 的类，生成对应的 CREATE TABLE 语句
    # 如果表已存在，不会重复创建也不会覆盖（安全）
    db.create_all()
    print('[OK] 数据库表创建完成！')

    # ---- 第二步：插入预设分类 ----
    # 先查一下是不是已经有数据了（避免重复插入）
    if Category.query.count() == 0:
        default_categories = [
            Category(name='Python', description='Python 编程语言相关文章'),
            Category(name='前端', description='HTML、CSS、JavaScript 等前端技术'),
            Category(name='数据库', description='MySQL、Redis 等数据库相关'),
            Category(name='杂谈', description='生活、随笔、技术思考'),
        ]
        # add_all() 一次性添加多条记录
        db.session.add_all(default_categories)
        db.session.commit()
        print('[OK] 预设分类数据已插入！')
    else:
        print('[OK] 分类数据已存在，跳过插入。')
