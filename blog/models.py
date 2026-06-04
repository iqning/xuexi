"""
=============================================
 数据库模型定义
 使用 Flask-SQLAlchemy ORM 定义四张表：
   users → articles → comments（文章有作者）
   categories → articles（文章有分类）
   comments → comments（评论支持楼中楼回复）
=============================================
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

# 创建 SQLAlchemy 实例
# db 对象是操作数据库的核心：建表、查询、增删改都靠它
# 在这里创建但不绑定 Flask app，等 app.py 初始化时再绑定（延迟初始化）
db = SQLAlchemy()


# =============================================
# 一、用户表
# =============================================
class User(db.Model, UserMixin):
    """
    用户表：存储注册用户信息
    继承 UserMixin：Flask-Login 要求的，自动提供 is_authenticated、
    get_id() 等方法，不用我们自己写
    """
    __tablename__ = 'users'

    # ---- 列定义 ----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50), default='')
    bio = db.Column(db.String(210), default='')
    avatar = db.Column(db.String(255), default='default.png')
    # 网易云音乐外链播放器：存歌曲 ID（数字），为空表示不显示播放器
    # 例如歌曲 https://music.163.com/#/song?id=123456 → 存 "123456"
    music_id = db.Column(db.String(30), default='')
    # 邮箱：用于密码重置（选填）
    email = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- 关联关系 ----
    # articles 属性：通过 Article.author_id 反向查到这个用户写的所有文章
    # backref='author'：在 Article 对象上可以通过 .author 访问作者
    # lazy='dynamic'：返回查询对象而非列表，方便在此结果上继续过滤、排序、分页
    articles = db.relationship('Article', backref='author', lazy='dynamic')

    def __repr__(self):
        """打印 User 对象时显示用户名，调试用"""
        return f'<User {self.username}>'


# =============================================
# 二、分类表
# =============================================
class Category(db.Model):
    """
    分类表：文章的分类标签（如"Python"、"前端"、"数据库"等）
    """
    __tablename__ = 'categories'

    # ---- 列定义 ----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(200), default='')

    # ---- 关联关系 ----
    # 一个分类下有多篇文章
    articles = db.relationship('Article', backref='category', lazy='dynamic')

    def __repr__(self):
        return f'<Category {self.name}>'


# =============================================
# 三、文章表
# =============================================
class Article(db.Model):
    """
    文章表：博客的核心，存储文章内容和元信息
    外键：author_id → users.id（谁写的）
          category_id → categories.id（属于哪个分类，可为空）
    """
    __tablename__ = 'articles'

    # ---- 列定义 ----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    summary = db.Column(db.String(500), default='')
    content = db.Column(db.Text, nullable=False)
    # 创建时间和更新时间
    # default=datetime.utcnow：新建时自动填入
    # onupdate=datetime.utcnow：每次修改文章时自动更新为当前时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # 封面图路径，存储相对于 static/ 的路径（如 'covers/abc.jpg'），默认为空表示无封面
    cover_image = db.Column(db.String(255), default='')
    # 阅读量：文章详情页每次被非作者访问时 +1
    views = db.Column(db.Integer, default=0)
    # 文章状态：'published'（已发布，公开可见）或 'draft'（草稿，仅作者可见）
    status = db.Column(db.String(20), default='published')
    # 置顶标记：True 的文章在所有列表中排在最前面
    is_pinned = db.Column(db.Boolean, default=False)

    # ---- 外键 ----
    # db.ForeignKey('表名.列名')：建立外键约束，确保 author_id 的值在 users 表中真实存在
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    # ---- 关联关系 ----
    # 一篇文章有多条评论
    # cascade='all, delete-orphan'：删除文章时，文章下的所有评论也一起删除（级联删除）
    comments = db.relationship('Comment', backref='article', lazy='dynamic',
                               cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Article {self.title}>'


# =============================================
# 四、文章-标签关联表（多对多中间表）
# =============================================

# db.Table 创建关联表：不需要单独的模型类，只需要列定义
# SQLAlchemy 会自动通过 secondary 参数使用这张表
article_tags = db.Table('article_tags',
    db.Column('article_id', db.Integer, db.ForeignKey('articles.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tags.id'), primary_key=True)
)


# =============================================
# 五、标签表
# =============================================

class Tag(db.Model):
    """
    标签表：文章标签（如"Python"、"Flask"、"前端"）
    与文章是多对多关系：一篇文章可以有多个标签，一个标签下可以有多篇文章
    """
    __tablename__ = 'tags'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), unique=True, nullable=False)
    # articles 属性：通过 article_tags 关联表反向查找此标签下的所有文章
    # secondary=article_tags：指定中间关联表
    articles = db.relationship('Article', secondary=article_tags, backref='tags')

    def __repr__(self):
        return f'<Tag {self.name}>'


# =============================================
# 六、评论表
# =============================================
class Comment(db.Model):
    """
    评论表：文章评论，支持楼中楼回复
    外键：article_id → articles.id（哪篇文章的评论）
          parent_id → comments.id（回复哪条评论，为空则是顶级评论）
    自关联：parent_id 指向自己这张表的另一行，实现嵌套回复
    """
    __tablename__ = 'comments'

    # ---- 列定义 ----
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    content = db.Column(db.Text, nullable=False)
    author_name = db.Column(db.String(50), nullable=False)
    author_email = db.Column(db.String(100), default='')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # ---- 外键 ----
    article_id = db.Column(db.Integer, db.ForeignKey('articles.id'), nullable=False)
    # parent_id 可以为空：空 = 顶级评论，非空 = 回复某条评论
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)

    # ---- 关联关系 ----
    # 自关联：Comment 的 parent_id 指向 Comment 自己的 id
    # backref='replies'：通过 comment.replies 拿到这条评论的所有子回复
    # remote_side=[id]：告诉 SQLAlchemy "多的那边"是 parent_id，"一的那边"是 id
    replies = db.relationship('Comment', backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic')

    def __repr__(self):
        return f'<Comment by {self.author_name}>'
