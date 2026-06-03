"""
=============================================
 Flask 应用配置文件
 集中管理所有配置项：数据库连接、密钥、上传路径等
 其他模块通过 app.config.from_object() 导入这些配置
=============================================
"""
import os

# 当前文件所在目录的绝对路径，用于拼接上传路径等
# os.path.abspath 把相对路径转成绝对路径，避免在不同目录运行 Flask 时路径错乱
BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """
    Flask 配置类
    使用类来组织配置项，方便后续扩展（如测试环境、生产环境的配置可以写在不同类里）
    """

    # ---------- 安全密钥 ----------
    # SECRET_KEY 的用途：
    #   1. Flask session 加密签名 → 防止用户篡改登录信息
    #   2. Flask 扩展的安全令牌（如表单 CSRF 保护）
    # 生产环境一定要换成随机字符串，不能泄露
    # 可以用 secrets.token_hex(32) 生成一个随机的 64 字符密钥
    SECRET_KEY = 'dev-secret-key-change-in-production-please'

    # ---------- 站点名称 ----------
    # 出现在浏览器标签页标题、导航栏 LOGO、页脚版权等位置
    SITE_NAME = '拾光小筑'

    # ---------- 数据库连接 ----------
    # 格式：mysql+pymysql://用户名:密码@主机地址:端口/数据库名?参数
    #   mysql+pymysql → 使用 PyMySQL 驱动连接 MySQL
    #   127.0.0.1:3306 → 本地 MySQL 默认端口
    #   blog           → 数据库名（需要先在 MySQL 中创建）
    #   ?charset=utf8mb4 → 支持 emoji 和所有 Unicode 字符
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:010210@127.0.0.1:3306/blog?charset=utf8mb4'

    # 关闭追踪修改信号，节省内存（Flask-SQLAlchemy 默认开启，我们不需要）
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ---------- 文件上传配置 ----------
    # 头像上传的目标文件夹（位于 blog/static/uploads/）
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')

    # 允许上传的文件扩展名（白名单，防止上传恶意文件）
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # 上传文件最大大小：10MB（单位是字节）
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024

    # ---------- 分页配置 ----------
    # 每页显示的文章数量
    POSTS_PER_PAGE = 6

    # ---------- 开发模式 ----------
    # 调试模式：修改代码后自动重启，修改模板后自动重载
    DEBUG = True
    # 明确开启模板自动重载（DEBUG=True 时默认开启，这里显式声明）
    TEMPLATES_AUTO_RELOAD = True
