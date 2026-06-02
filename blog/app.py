"""
=============================================
 Flask 应用入口 — 所有路由和业务逻辑
 路由分为五大块：
   一、初始化（Flask、数据库、登录管理器）
   二、公开页面（首页、文章详情、分类筛选）
   三、用户认证（注册、登录、退出）
   四、个人中心（查看/编辑资料、我的文章）
   五、后台管理（发布/删除文章、删除评论）
=============================================
"""
import os
import uuid
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, abort)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Category, Article, Comment


# =============================================
# 一、应用初始化
# =============================================

app = Flask(__name__)
app.config.from_object(Config)            # 加载 config.py 中的所有配置
db.init_app(app)                          # 把 db 和 app 绑定（延迟初始化完成）

# Flask-Login 初始化
login_manager = LoginManager()
login_manager.init_app(app)
# 未登录用户访问 @login_required 保护的路由时，自动跳转到登录页
login_manager.login_view = 'login'
# 登录页闪现消息的类别（Flash 消息用 Bootstrap 风格分类）
login_manager.login_message = '请先登录再访问此页面。'
login_manager.login_message_category = 'info'


@login_manager.user_loader
def load_user(user_id):
    """
    Flask-Login 要求的回调函数。
    每次请求到来时，Flask-Login 从 session 中取出 user_id，
    调用这个函数加载完整的 User 对象，赋值给 current_user。
    这样所有模板都能直接用 current_user 判断登录状态。
    """
    return User.query.get(int(user_id))


# =============================================
# 二、辅助函数
# =============================================

def allowed_file(filename):
    """
    检查上传文件的扩展名是否在白名单中。
    返回 True 表示文件类型允许上传，False 表示不允许。
    """
    # rsplit('.', 1)：从右边开始分割一次，拿到最后一个点后面的内容
    # 例如 'a.b.c.png' → 'png'（只取最后一段，防止双扩展名绕过）
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS


# 在所有请求之前自动执行：把全部分类注入到模板上下文
# 这样 base.html 侧边栏的 categories 就不用每个路由单独传了
@app.context_processor
def inject_categories():
    """向所有模板注入 categories 和 now 变量"""
    return {
        'categories': Category.query.order_by(Category.name).all(),
        'now': datetime.utcnow()
    }


# =============================================
# 三、公开页面路由
# =============================================

@app.route('/')
@login_required
def index():
    """
    首页：分页展示最新文章（需登录）
    URL 参数：?page=页码（默认第 1 页）
    也服务于 /my-posts 路由，通过请求端点区分场景
    """
    page = request.args.get('page', 1, type=int)
    # 按创建时间倒序排列（最新发布的最前面），每页 6 篇
    pagination = Article.query \
        .order_by(Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html',
                           posts=posts,
                           pagination=pagination,
                           page_title='最新文章')


@app.route('/category/<int:id>')
@login_required
def category(id):
    """
    按分类筛选文章
    URL：/category/分类ID
    与首页共用 index.html 模板，通过 current_category 变量区分
    """
    # 先查分类是否存在，不存在返回 404
    cat = Category.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    # filter_by：按字段精确过滤，等价于 WHERE category_id = id
    pagination = Article.query \
        .filter_by(category_id=id) \
        .order_by(Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html',
                           posts=posts,
                           pagination=pagination,
                           current_category=cat,
                           page_title=f'分类：{cat.name}')


@app.route('/post/<int:id>')
@login_required
def post(id):
    """
    文章详情页：显示正文 + 评论列表 + 评论表单（需登录）
    URL：/post/文章ID
    """
    article = Article.query.get_or_404(id)
    # 获取这篇文章的所有评论，按时间正序排列（早的在前，形成对话时间线）
    comments = Comment.query \
        .filter_by(article_id=id) \
        .order_by(Comment.created_at.asc()) \
        .all()
    return render_template('post.html',
                           post=article,
                           comments=comments)


@app.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    """
    提交评论（登录用户和游客都可以评论）
    处理完自动重定向回文章详情页
    """
    # 先确保文章存在
    article = Article.query.get_or_404(id)
    author_name = request.form.get('author_name', '').strip()
    content = request.form.get('content', '').strip()

    # 后端校验：昵称和内容不能为空
    if not author_name:
        flash('请输入昵称。', 'error')
        return redirect(url_for('post', id=id))
    if not content:
        flash('请输入评论内容。', 'error')
        return redirect(url_for('post', id=id))

    comment = Comment(
        content=content,
        author_name=author_name,
        author_email=request.form.get('author_email', '').strip(),
        article_id=id
    )
    db.session.add(comment)
    db.session.commit()
    flash('评论发表成功！', 'success')
    return redirect(url_for('post', id=id))


@app.route('/my-posts')
@login_required
def my_posts():
    """
    我发布的文章列表
    与首页共用 index.html 模板，通过 my_posts 变量区分场景
    """
    page = request.args.get('page', 1, type=int)
    pagination = Article.query \
        .filter_by(author_id=current_user.id) \
        .order_by(Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html',
                           posts=posts,
                           pagination=pagination,
                           my_posts=True,
                           page_title='我的文章')


# =============================================
# 四、用户认证路由
# =============================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """
    注册页面
    GET 请求：显示注册表单
    POST 请求：处理注册逻辑
    """
    if current_user.is_authenticated:
        # 已登录用户无需再注册，直接跳首页
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        password_confirm = request.form.get('password_confirm', '').strip()

        # ---- 后端校验 ----
        # 1. 必填检查
        if not username or not password:
            flash('用户名和密码为必填项。', 'error')
            return render_template('register.html')

        # 2. 用户名长度
        if len(username) < 2 or len(username) > 50:
            flash('用户名长度应在 2~50 个字符之间。', 'error')
            return render_template('register.html')

        # 3. 密码长度
        if len(password) < 6:
            flash('密码长度不能少于 6 位。', 'error')
            return render_template('register.html')

        # 4. 两次密码一致
        if password != password_confirm:
            flash('两次输入的密码不一致。', 'error')
            return render_template('register.html')

        # 5. 用户名唯一性检查
        if User.query.filter_by(username=username).first():
            flash('该用户名已被注册，请换一个。', 'error')
            return render_template('register.html')

        # ---- 创建用户 ----
        new_user = User(
            username=username,
            # 密码绝不存明文！用 werkzeug 的哈希函数生成不可逆的密文
            password_hash=generate_password_hash(password),
            nickname=request.form.get('nickname', '').strip()
        )
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功！请登录。', 'success')
        return redirect(url_for('login'))

    # GET 请求：显示空白注册表单
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    登录页面
    GET 请求：显示登录表单
    POST 请求：验证登录
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash('请输入用户名和密码。', 'error')
            return render_template('login.html')

        # 查数据库找用户
        user = User.query.filter_by(username=username).first()

        # 验证密码：check_password_hash 自动从哈希值中提取盐并重新计算比较
        if user and check_password_hash(user.password_hash, password):
            # 密码正确 → 创建登录会话
            # remember=True：勾选了"记住我"，cookie 存 365 天
            login_user(user, remember=request.form.get('remember'))
            flash(f'欢迎回来，{user.nickname or user.username}！', 'success')
            # next 参数：登录后跳回之前想访问的页面
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误。', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """退出登录：清除 session，跳回首页"""
    logout_user()
    flash('已退出登录。', 'info')
    return redirect(url_for('index'))


# =============================================
# 五、个人中心路由（需登录）
# =============================================

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """
    个人中心：查看 / 编辑资料、上传头像
    一个 URL 处理两种操作，通过表单按钮的 name="action" 值区分
    """
    if request.method == 'POST':
        action = request.form.get('action', '')

        # ----- 操作一：更新个人资料 -----
        if action == 'update_profile':
            nickname = request.form.get('nickname', '').strip()
            bio = request.form.get('bio', '').strip()

            if len(nickname) > 50:
                flash('昵称不能超过 50 个字符。', 'error')
            elif len(bio) > 200:
                flash('个人简介不能超过 200 个字符。', 'error')
            else:
                current_user.nickname = nickname
                current_user.bio = bio
                db.session.commit()
                flash('资料更新成功！', 'success')

        # ----- 操作二：上传头像 -----
        elif action == 'update_avatar':
            file = request.files.get('avatar')
            if not file or file.filename == '':
                flash('请选择一张图片。', 'error')
            elif not allowed_file(file.filename):
                flash('只允许上传 PNG、JPG、JPEG、GIF 格式的图片。', 'error')
            else:
                # 用 UUID 重命名文件，防止：
                #   1. 多用户上传同名文件互相覆盖
                #   2. 文件名包含中文或特殊字符导致服务器兼容问题
                ext = file.filename.rsplit('.', 1)[1].lower()
                filename = f'{uuid.uuid4().hex}.{ext}'
                # 拼接保存路径
                save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                # 确保 uploads 目录存在（首次运行时可能还没有）
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                file.save(save_path)
                # 更新用户头像字段
                current_user.avatar = filename
                db.session.commit()
                flash('头像上传成功！', 'success')

        return redirect(url_for('profile'))

    # GET 请求：显示个人中心页面
    return render_template('profile.html', user=current_user)


# =============================================
# 六、后台管理路由（需登录）
# =============================================

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    """
    后台管理页面
    GET：显示发布表单 + 我的文章列表
    POST：发布新文章
    """
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', '').strip()

        # 后端校验
        if not title:
            flash('文章标题不能为空。', 'error')
        elif not content:
            flash('文章正文不能为空。', 'error')
        elif len(title) > 200:
            flash('标题不能超过 200 个字符。', 'error')
        else:
            article = Article(
                title=title,
                summary=summary,
                content=content,
                # 如果 category_id 为空字符串，转为 None（数据库 NULL）
                category_id=int(category_id) if category_id else None,
                author_id=current_user.id
            )
            db.session.add(article)
            db.session.commit()
            flash('文章发布成功！', 'success')
            return redirect(url_for('admin'))

    # GET 请求：获取当前用户的所有文章
    my_articles = Article.query \
        .filter_by(author_id=current_user.id) \
        .order_by(Article.created_at.desc()) \
        .all()
    return render_template('admin.html', my_articles=my_articles)


@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
def delete_article(id):
    """
    删除文章
    只有文章作者本人才能删除自己的文章
    """
    article = Article.query.get_or_404(id)

    # 权限检查：不是自己的文章不能删除
    if article.author_id != current_user.id:
        flash('你没有权限删除这篇文章。', 'error')
        return redirect(url_for('admin'))

    db.session.delete(article)
    db.session.commit()
    flash('文章已删除。', 'info')
    return redirect(url_for('admin'))


# =============================================
# 七、评论管理路由（需登录）
# =============================================

@app.route('/admin/comment/delete/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    """
    博主删除评论（任意登录用户都可以删评论，体现博主身份）
    删除评论时，其子回复也一并删除（级联删除由模型层 cascade 保证）
    """
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除。', 'info')
    # 删除后回到文章详情页
    return redirect(url_for('post', id=comment.article_id))
