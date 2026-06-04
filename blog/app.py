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
import requests  # 用于代理调用网易云音乐搜索API
from datetime import datetime
from flask import (Flask, render_template, request, redirect,
                   url_for, flash, abort, jsonify)
from flask_login import (LoginManager, login_user, logout_user,
                         login_required, current_user)
from flask_wtf.csrf import CSRFProtect  # CSRF 跨站请求伪造防护
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

from config import Config
from models import db, User, Category, Article, Comment, Tag

# 导入 db.or_ 用于组合查询条件（如搜索功能中的 OR 逻辑）
from sqlalchemy import or_ as db_or


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

# ---- CSRF 保护初始化 ----
# CSRFProtect 会拦截所有 POST/PUT/DELETE 请求，
# 验证请求中的 csrf_token（来自表单隐藏字段或 X-CSRFToken 请求头）
csrf = CSRFProtect(app)


# ---- 安全响应头 ----
# 每个 HTTP 响应都会经过此钩子，自动添加安全相关的响应头
# 这些头告诉浏览器启用安全策略，是"纵深防御"的一环
@app.after_request
def add_security_headers(response):
    """为所有 HTTP 响应添加安全头，增强浏览器端防护"""
    # 1. 禁止浏览器猜测 MIME 类型（防止将恶意脚本当作图片执行）
    response.headers['X-Content-Type-Options'] = 'nosniff'
    # 2. 禁止本站被其他网站用 <iframe> 嵌入（防止点击劫持攻击）
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    # 3. 关闭旧版浏览器的 XSS 过滤器（已废弃，显式关闭避免误判）
    response.headers['X-XSS-Protection'] = '0'
    # 4. 内容安全策略（CSP）：限制浏览器可以加载哪些来源的资源
    #    'self' = 只允许同源；外加 Google Fonts、Font Awesome、网易云音乐等 CDN
    response.headers['Content-Security-Policy'] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' cdn.jsdelivr.net busuanzi.ibruce.info; "
        "style-src 'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net; "
        "font-src 'self' fonts.gstatic.com cdn.jsdelivr.net; "
        "img-src 'self' data:; "
        "frame-src 'self' music.163.com; "
        "connect-src 'self'; "
        "media-src 'self'; "
    )
    return response


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


def api_response(ok, data=None, error=None, status=200):
    """
    统一的 JSON API 响应格式
    - 成功：{"ok": true, "data": ...}
    - 失败：{"ok": false, "error": "错误信息"}
    返回 (response_dict, status_code) 元组，可直接从路由返回
    """
    body = {'ok': ok}
    if ok:
        if data is not None:
            body['data'] = data
    else:
        body['error'] = error or '未知错误'
    return jsonify(body), status


def process_tags(tags_string):
    """
    处理逗号分隔的标签字符串，返回 Tag 对象列表
    "找到或创建"模式：如果标签已存在就复用，不存在就新建
    例如输入 "Python, Flask, 教程" → 返回 [Tag('Python'), Tag('Flask'), Tag('教程')]
    """
    tags = []
    if tags_string:
        for name in tags_string.split(','):
            name = name.strip()
            if name:
                # 查找已有标签或创建新标签
                tag = Tag.query.filter_by(name=name).first()
                if not tag:
                    tag = Tag(name=name)
                    db.session.add(tag)
                    db.session.flush()  # 立即生成 tag.id，但未提交
                tags.append(tag)
    return tags


# 在所有请求之前自动执行：把全部分类注入到模板上下文
# 这样 base.html 侧边栏的 categories 就不用每个路由单独传了
@app.context_processor
def inject_globals():
    """向所有模板注入 categories、now、site_name、full_header、stats、sidebar_recent_posts 变量"""
    return {
        'categories': Category.query.order_by(Category.name).all(),
        'now': datetime.utcnow(),
        'site_name': app.config['SITE_NAME'],  # 站点名称，所有模板可用
        'full_header': False,  # 默认非全屏 Header，首页路由会覆盖为 True
        # 站点统计数据：文章数、分类数、评论数，侧边栏和统计栏使用
        'stats': {
            'article_count': Article.query.filter_by(status='published').count(),
            'category_count': Category.query.count(),
            'comment_count': Comment.query.count(),
        },
        # 侧边栏"最新文章"小部件：只显示已发布的，取最近 5 篇
        'sidebar_recent_posts': Article.query
            .filter_by(status='published')
            .order_by(Article.is_pinned.desc(), Article.created_at.desc())
            .limit(5)
            .all(),
        # 网站信息小部件：最后更新时间（只考虑已发布的文章）
        'last_update_time': Article.query
            .filter_by(status='published')
            .order_by(Article.updated_at.desc())
            .first(),
    }


# =============================================
# 注册自定义 Jinja2 宏：递归渲染评论
# =============================================
# 把 render_comment 宏定义在 app.py 中，注册到 Jinja2 环境，
# 这样所有模板都能直接调用 {{ render_comment(comment) | safe }}
# 使用 app.jinja_env.from_string() 编译宏模板，
# 这样宏内部可以使用 Flask 全局模板变量（如 csrf_token()）
_comment_macro = app.jinja_env.from_string("""
{#- 递归渲染单条评论及其所有子回复 -#}
{% macro render_comment(comment) -%}
    <div class="comment-item" id="comment-{{ comment.id }}">
        <div class="comment-header">
            <strong>{{ comment.author_name }}</strong>
            <span class="comment-time">
                {{ comment.created_at.strftime('%Y-%m-%d %H:%M') }}
            </span>
        </div>
        <div class="comment-body">
            <p>{{ comment.content }}</p>
        </div>
        {#- 回复按钮：点击后展开行内回复表单 -#}
        <button type="button" class="btn-reply"
                data-comment-id="{{ comment.id }}"
                data-author-name="{{ comment.author_name }}">
            回复
        </button>
        {#- 行内回复表单（默认隐藏，点击"回复"后显示） -#}
        <div class="reply-form-inline" id="reply-form-{{ comment.id }}" style="display:none;">
            <form method="POST" action="{{ url_for('add_comment', id=comment.article_id) }}"
                  class="reply-form">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                <input type="hidden" name="parent_id" value="{{ comment.id }}">
                <div class="form-group">
                    <input type="text" name="author_name" required
                           placeholder="你的昵称"
                           class="form-input-sm">
                </div>
                <div class="form-group">
                    <textarea name="content" rows="2" required
                              placeholder="回复 {{ comment.author_name }}……"
                              class="form-input-sm"></textarea>
                </div>
                <div class="reply-form-actions">
                    <button type="submit" class="btn btn-primary btn-sm">提交回复</button>
                    <button type="button" class="btn btn-sm btn-cancel-reply"
                            data-comment-id="{{ comment.id }}">取消</button>
                </div>
            </form>
        </div>
        {#- 递归渲染这条评论的所有子回复 -#}
        {% if comment.replies.count() > 0 %}
            <div class="comment-replies">
                {% for reply in comment.replies %}
                    {{ render_comment(reply) }}
                {% endfor %}
            </div>
        {% endif %}
    </div>
{%- endmacro %}
""")

# 从编译好的模板中取出 render_comment 宏，注册到全局环境
app.jinja_env.globals['render_comment'] = _comment_macro.module.render_comment


# =============================================
# 三、公开页面路由
# =============================================

@app.route('/')
def index():
    """
    首页：分页展示最新文章
    URL 参数：
      ?page=页码（默认第 1 页）
      ?partial=1（AJAX 分页请求，只返回文章列表 HTML 片段）
    也服务于 /my-posts 路由，通过请求端点区分场景
    """
    page = request.args.get('page', 1, type=int)
    # ?partial=1：前端 AJAX 翻页时，只返回列表 + 分页，不带 Hero/统计栏
    partial = request.args.get('partial') == '1'
    # 只显示已发布的文章，按创建时间倒序，每页 6 篇
    pagination = Article.query \
        .filter_by(status='published') \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items

    return render_template('index.html' if not partial else '_post_list.html',
                           posts=posts,
                           pagination=pagination,
                           page_title='最新文章',
                           partial=partial,
                           full_header=True)


@app.route('/category/<int:id>')
def category(id):
    """
    按分类筛选文章
    URL：/category/分类ID
    URL 参数：
      ?page=页码（默认第 1 页）
      ?partial=1（AJAX 分页请求，只返回文章列表 HTML 片段）
    与首页共用 index.html 模板，通过 current_category 变量区分
    """
    # 先查分类是否存在，不存在返回 404
    cat = Category.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    # ?partial=1：前端 AJAX 翻页时，只返回列表 + 分页
    partial = request.args.get('partial') == '1'
    # 只显示已发布 + 指定分类的文章
    pagination = Article.query \
        .filter_by(category_id=id, status='published') \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html' if not partial else '_post_list.html',
                           posts=posts,
                           pagination=pagination,
                           current_category=cat,
                           page_title=f'分类：{cat.name}',
                           partial=partial)


@app.route('/post/<int:id>')
def post(id):
    """
    文章详情页：显示正文 + 评论列表 + 评论表单（需登录）
    URL：/post/文章ID
    URL 参数：
      ?partial=1（AJAX 导航请求，只返回内容区 HTML 片段）
    """
    # ?partial=1：前端 AJAX 导航时，只返回内容区，不带 header/sidebar/footer
    partial = request.args.get('partial') == '1'
    article = Article.query.get_or_404(id)
    # 阅读量统计：非作者访问时 +1（作者自己反复看不算）
    if not current_user.is_authenticated or current_user.id != article.author_id:
        article.views += 1
        db.session.commit()
    # 获取这篇文章的所有评论，按时间正序排列（早的在前，形成对话时间线）
    comments = Comment.query \
        .filter_by(article_id=id) \
        .order_by(Comment.created_at.asc()) \
        .all()
    return render_template('_post_content.html' if partial else 'post.html',
                           post=article,
                           comments=comments)


@app.route('/post/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_article(id):
    """
    编辑文章
    GET 请求：显示编辑表单（数据预填充）
    POST 请求：更新文章内容到数据库
    权限控制：只有文章作者本人才能编辑自己的文章
    """
    article = Article.query.get_or_404(id)

    # ---- 权限检查：不是自己的文章，不允许编辑 ----
    if article.author_id != current_user.id:
        flash('你没有权限编辑这篇文章。', 'error')
        return redirect(url_for('post', id=id))

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        summary = request.form.get('summary', '').strip()
        content = request.form.get('content', '').strip()
        category_id = request.form.get('category_id', '').strip()
        # 文章状态选择：'published' 或 'draft'
        status = request.form.get('status', 'published')

        # ---- 后端校验 ----
        if not title:
            flash('文章标题不能为空。', 'error')
        elif not content:
            flash('文章正文不能为空。', 'error')
        elif len(title) > 200:
            flash('标题不能超过 200 个字符。', 'error')
        else:
            # ---- 处理封面图上传（如果有新图就替换） ----
            file = request.files.get('cover_image')
            if file and file.filename != '' and allowed_file(file.filename):
                ext = file.filename.rsplit('.', 1)[1].lower()
                cover_filename = f'{uuid.uuid4().hex}.{ext}'
                os.makedirs(app.config['COVERS_FOLDER'], exist_ok=True)
                save_path = os.path.join(app.config['COVERS_FOLDER'], cover_filename)
                file.save(save_path)
                article.cover_image = cover_filename

            # 更新文章字段
            article.title = title
            article.summary = summary
            article.content = content
            article.status = status  # 草稿/发布状态
            # 更新标签
            article.tags = process_tags(request.form.get('tags', ''))
            # 如果 category_id 为空字符串，转为 None（数据库 NULL）
            article.category_id = int(category_id) if category_id else None
            # updated_at 字段由模型的 onupdate 参数自动更新，无需手动设置
            db.session.commit()
            flash('文章更新成功！', 'success')
            return redirect(url_for('post', id=id))

    # GET 请求：渲染编辑页面，把文章对象传给模板做预填充
    return render_template('edit.html', article=article)


@app.route('/post/<int:id>/comment', methods=['POST'])
@login_required
def add_comment(id):
    """
    提交评论（需登录）
    支持顶级评论和楼中楼回复（通过 parent_id 区分）
    - 普通表单提交：flash 消息 + 重定向回文章详情页
    - AJAX 请求（Accept: application/json）：返回 JSON，由前端动态插入 DOM
    """
    # 先确保文章存在
    article = Article.query.get_or_404(id)
    author_name = request.form.get('author_name', '').strip()
    content = request.form.get('content', '').strip()
    parent_id = request.form.get('parent_id', '').strip()

    # 判断是否为 AJAX 请求（前端 fetch 发送 JSON Accept 头）
    is_ajax = request.headers.get('Accept') == 'application/json'

    # 后端校验：昵称和内容不能为空
    if not author_name:
        if is_ajax:
            return api_response(False, error='请输入昵称。', status=400)
        flash('请输入昵称。', 'error')
        return redirect(url_for('post', id=id))
    if not content:
        if is_ajax:
            return api_response(False, error='请输入评论内容。', status=400)
        flash('请输入评论内容。', 'error')
        return redirect(url_for('post', id=id))

    # ---- 处理楼中楼回复：校验 parent_id ----
    parent = None
    if parent_id:
        # 查找父评论，确保它存在
        parent = Comment.query.get(int(parent_id))
        if not parent:
            if is_ajax:
                return api_response(False, error='要回复的评论不存在。', status=404)
            flash('要回复的评论不存在。', 'error')
            return redirect(url_for('post', id=id))
        # 安全检查：父评论必须属于同一篇文章（防止跨文章回复）
        if parent.article_id != id:
            if is_ajax:
                return api_response(False, error='回复的评论不属于当前文章。', status=400)
            flash('回复的评论不属于当前文章。', 'error')
            return redirect(url_for('post', id=id))

    comment = Comment(
        content=content,
        author_name=author_name,
        author_email=request.form.get('author_email', '').strip(),
        article_id=id,
        parent_id=int(parent_id) if parent_id else None  # 空字符串 → None
    )
    db.session.add(comment)
    db.session.commit()

    # AJAX 请求：返回 JSON，包含新评论的数据，前端动态插入 DOM
    if is_ajax:
        return api_response(True, data={
            'comment': {
                'id': comment.id,
                'author_name': comment.author_name,
                'content': comment.content,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M'),
                'parent_id': comment.parent_id
            }
        })

    flash('评论发表成功！', 'success')
    return redirect(url_for('post', id=id))


@app.route('/my-posts')
@login_required
def my_posts():
    """
    我发布的文章列表
    与首页共用 index.html 模板，通过 my_posts 变量区分场景
    URL 参数：?page=页码 & ?partial=1（AJAX 分页）
    """
    page = request.args.get('page', 1, type=int)
    partial = request.args.get('partial') == '1'
    pagination = Article.query \
        .filter_by(author_id=current_user.id) \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html' if not partial else '_post_list.html',
                           posts=posts,
                           pagination=pagination,
                           my_posts=True,
                           page_title='我的文章',
                           partial=partial)


@app.route('/tag/<int:id>')
def tag(id):
    """
    按标签筛选文章
    URL：/tag/标签ID
    与首页共用 index.html 模板
    """
    tag = Tag.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    partial = request.args.get('partial') == '1'
    # 通过关联表筛选：只显示已发布 + 包含此标签的文章
    pagination = Article.query \
        .filter_by(status='published') \
        .filter(Article.tags.any(id=tag.id)) \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items
    return render_template('index.html' if not partial else '_post_list.html',
                           posts=posts,
                           pagination=pagination,
                           page_title=f'标签：{tag.name}',
                           partial=partial)


@app.route('/search')
def search():
    """
    文章搜索：根据关键词模糊匹配标题和正文
    URL 参数：
      ?q=搜索关键词
      ?page=页码（默认第 1 页）
      ?partial=1（AJAX 分页请求，只返回文章列表 HTML 片段）
    搜索结果与首页共用 index.html 模板
    """
    q = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    partial = request.args.get('partial') == '1'

    # 空搜索或过长关键词 → 返回空结果
    if not q or len(q) > 100:
        return render_template('index.html' if not partial else '_post_list.html',
                               posts=[],
                               pagination=None,
                               page_title=f'搜索：{q}' if q else '搜索',
                               partial=partial,
                               search_query=q)

    # 只搜索已发布的文章
    # 用 db_or 组合条件：标题 OR 正文包含关键词
    pagination = Article.query \
        .filter_by(status='published') \
        .filter(db_or(
            Article.title.contains(q),
            Article.content.contains(q)
        )) \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .paginate(page=page, per_page=Config.POSTS_PER_PAGE, error_out=False)
    posts = pagination.items

    return render_template('index.html' if not partial else '_post_list.html',
                           posts=posts,
                           pagination=pagination,
                           page_title=f'搜索：{q}',
                           partial=partial,
                           search_query=q)


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
            music_id = request.form.get('music_id', '').strip()

            if len(nickname) > 50:
                flash('昵称不能超过 50 个字符。', 'error')
            elif len(bio) > 200:
                flash('个人简介不能超过 200 个字符。', 'error')
            elif len(music_id) > 30:
                flash('歌曲 ID 格式不正确。', 'error')
            else:
                current_user.nickname = nickname
                current_user.bio = bio
                # 音乐播放器：存网易云歌曲 ID，为空则不显示播放器
                current_user.music_id = music_id
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
                # ---- 清理旧头像文件 ----
                # 删除旧头像（保留 default.png，它是所有用户的默认头像）
                old_avatar = current_user.avatar
                if old_avatar and old_avatar != 'default.png':
                    old_path = os.path.join(app.config['UPLOAD_FOLDER'], old_avatar)
                    if os.path.exists(old_path):
                        os.remove(old_path)

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

    # GET 请求：显示个人中心页面（no_banner=True 去除全屏 Banner，只保留导航栏）
    return render_template('profile.html', user=current_user, no_banner=True)


# ---- 个人资料自动保存 API ----
# 前端通过 fetch 发 JSON，后端即时保存并返回结果
@app.route('/api/profile/save', methods=['POST'])
@login_required
@csrf.exempt  # 纯 JSON API，不经过 HTML 表单，豁免 CSRF 校验
def api_profile_save():
    """
    自动保存个人资料字段（昵称、简介、音乐ID）
    前端在用户输入时自动调用，无需点击保存按钮
    接收 JSON：{"field": "nickname", "value": "..."}
    也支持一次性提交多个字段：{"nickname": "...", "bio": "...", "music_id": "..."}
    """
    data = request.get_json(silent=True)
    if not data:
        return {'ok': False, 'error': '请求数据为空'}, 400

    # 支持两种格式：单字段（field + value）或多字段（直接传 nickname/bio/music_id）
    if 'field' in data and 'value' in data:
        # 单字段格式
        field = data['field']
        value = data['value'].strip() if data['value'] else ''

        # 校验长度
        limits = {'nickname': 50, 'bio': 200, 'music_id': 30}
        if field not in limits:
            return {'ok': False, 'error': f'未知字段: {field}'}, 400
        if len(value) > limits[field]:
            return {'ok': False, 'error': f'{field} 不能超过 {limits[field]} 个字符'}, 400

        setattr(current_user, field, value)
        db.session.commit()
        return {'ok': True, 'field': field, 'value': value}
    else:
        # 多字段格式：一次性提交多个字段
        updates = {}
        if 'nickname' in data:
            val = data['nickname'].strip()
            if len(val) > 50:
                return {'ok': False, 'error': '昵称不能超过 50 个字符'}, 400
            updates['nickname'] = val
        if 'bio' in data:
            val = data['bio'].strip()
            if len(val) > 200:
                return {'ok': False, 'error': '个人简介不能超过 200 个字符'}, 400
            updates['bio'] = val
        if 'music_id' in data:
            val = data['music_id'].strip()
            if len(val) > 30:
                return {'ok': False, 'error': '歌曲 ID 格式不正确'}, 400
            updates['music_id'] = val

        if not updates:
            return {'ok': False, 'error': '没有需要更新的字段'}, 400

        for k, v in updates.items():
            setattr(current_user, k, v)
        db.session.commit()
        return {'ok': True, 'updated': list(updates.keys())}
# ---- 修改密码 ----
@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """
    修改密码（需登录）
    验证旧密码正确性，新密码长度 ≥ 6，两次输入一致
    """
    old_password = request.form.get('old_password', '').strip()
    new_password = request.form.get('new_password', '').strip()
    confirm_password = request.form.get('confirm_password', '').strip()

    # 1. 校验旧密码是否正确（这是关键安全步骤：防止他人拿到登录态后改密码）
    if not check_password_hash(current_user.password_hash, old_password):
        flash('旧密码不正确。', 'error')
        return redirect(url_for('profile'))

    # 2. 新密码长度校验
    if len(new_password) < 6:
        flash('新密码长度不能少于 6 位。', 'error')
        return redirect(url_for('profile'))

    # 3. 两次输入一致性校验
    if new_password != confirm_password:
        flash('两次输入的新密码不一致。', 'error')
        return redirect(url_for('profile'))

    # 4. 更新密码哈希（绝不存明文！）
    current_user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    flash('密码修改成功！', 'success')
    return redirect(url_for('profile'))


# ---- 忘记密码 / 重置密码 ----
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature


def generate_reset_token(user_id):
    """
    生成密码重置令牌
    用 itsdangerous 的 URLSafeTimedSerializer 对 user_id 签名，
    令牌包含时间戳，可以设定有效期
    返回一个 URL 安全的字符串，可以直接拼接到重置链接中
    """
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return s.dumps(str(user_id))


def verify_reset_token(token):
    """
    验证密码重置令牌
    成功返回 user_id（整数），失败返回 None
    失败原因可能是：
      - 令牌过期（max_age 超出）
      - 签名伪造/篡改（BadSignature）
      - 令牌格式错误
    """
    s = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token, max_age=app.config['RESET_TOKEN_EXPIRY'])
        return int(user_id)
    except (SignatureExpired, BadSignature):
        # 签名过期或无效 → 返回 None
        return None


@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """
    忘记密码页面
    GET：显示表单（输入用户名）
    POST：查找用户，生成重置令牌，打印重置链接到控制台（学习阶段不接邮件服务）
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()

        if not username:
            flash('请输入用户名。', 'error')
            return render_template('forgot_password.html')

        # 查找用户
        user = User.query.filter_by(username=username).first()
        if not user:
            # 安全考虑：不告诉用户"该用户不存在"（防止枚举用户）
            # 但仍然显示成功消息，和真成功一样的提示
            flash('如果该账号存在，重置链接将被发送。', 'info')
            return redirect(url_for('login'))

        # 生成重置令牌并构建重置链接
        token = generate_reset_token(user.id)
        reset_url = url_for('reset_password', token=token, _external=True)

        # ---- 学习阶段：打印到控制台而非发邮件 ----
        # 生产环境中，这里应该用 smtplib 或 flask-mail 发邮件
        print('\n' + '=' * 60)
        print(f'[密码重置请求] 用户: {user.username}')
        print(f'[重置链接] {reset_url}')
        print('=' * 60 + '\n')

        flash('如果该账号存在，重置链接将被发送。请查看控制台输出。', 'info')
        return redirect(url_for('login'))

    # GET 请求：显示表单
    return render_template('forgot_password.html')


@app.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    重置密码页面（通过令牌访问）
    GET：验证令牌 → 显示新密码输入表单
    POST：验证令牌 + 密码校验 → 更新密码
    """
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    # 验证令牌
    user_id = verify_reset_token(token)
    if user_id is None:
        flash('重置链接已过期或无效，请重新申请。', 'error')
        return redirect(url_for('forgot_password'))

    user = User.query.get(user_id)
    if user is None:
        flash('用户不存在。', 'error')
        return redirect(url_for('forgot_password'))

    if request.method == 'POST':
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()

        if len(new_password) < 6:
            flash('新密码长度不能少于 6 位。', 'error')
        elif new_password != confirm_password:
            flash('两次输入的新密码不一致。', 'error')
        else:
            # 更新密码哈希
            user.password_hash = generate_password_hash(new_password)
            db.session.commit()
            flash('密码重置成功！请用新密码登录。', 'success')
            return redirect(url_for('login'))

        # 校验失败，回退到表单（保留 token 以便重试）
        return render_template('reset_password.html', token=token)

    # GET 请求：显示新密码输入表单
    return render_template('reset_password.html', token=token)


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
        # 文章状态：'publish' 按钮 → published，'draft' 按钮 → draft
        action = request.form.get('action', 'publish')

        # 后端校验
        if not title:
            flash('文章标题不能为空。', 'error')
        elif not content:
            flash('文章正文不能为空。', 'error')
        elif len(title) > 200:
            flash('标题不能超过 200 个字符。', 'error')
        else:
            # ---- 处理封面图上传 ----
            cover_filename = ''  # 默认空字符串，表示没有封面
            file = request.files.get('cover_image')
            if file and file.filename != '' and allowed_file(file.filename):
                # UUID 重命名，防止文件名冲突
                ext = file.filename.rsplit('.', 1)[1].lower()
                cover_filename = f'{uuid.uuid4().hex}.{ext}'
                # 确保 covers 目录存在
                os.makedirs(app.config['COVERS_FOLDER'], exist_ok=True)
                save_path = os.path.join(app.config['COVERS_FOLDER'], cover_filename)
                file.save(save_path)

            article = Article(
                title=title,
                summary=summary,
                content=content,
                # 如果 category_id 为空字符串，转为 None（数据库 NULL）
                category_id=int(category_id) if category_id else None,
                author_id=current_user.id,
                cover_image=cover_filename,  # 封面图文件名，为空表示无封面
                status='published' if action == 'publish' else 'draft'
            )
            # 处理标签：逗号分隔的标签名 → Tag 对象列表
            article.tags = process_tags(request.form.get('tags', ''))
            db.session.add(article)
            db.session.commit()
            flash('文章已发布！' if action == 'publish' else '草稿已保存。', 'success')
            return redirect(url_for('admin'))

    # GET 请求：获取当前用户的所有文章
    my_articles = Article.query \
        .filter_by(author_id=current_user.id) \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .all()
    return render_template('admin.html', my_articles=my_articles)


@app.route('/admin/pin/<int:id>', methods=['POST'])
@login_required
def pin_article(id):
    """
    切换文章置顶状态（需登录，仅作者本人）
    如果文章已被置顶 → 取消置顶
    如果文章未被置顶 → 置顶
    """
    article = Article.query.get_or_404(id)

    # 权限检查：只有文章作者本人才能操作
    if article.author_id != current_user.id:
        flash('你没有权限操作这篇文章。', 'error')
        return redirect(url_for('admin'))

    # 切换置顶状态
    article.is_pinned = not article.is_pinned
    db.session.commit()
    status_text = '已置顶' if article.is_pinned else '已取消置顶'
    flash(f'文章「{article.title}」{status_text}。', 'success')
    return redirect(url_for('admin'))


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
# 七、分类管理路由（需登录）
# =============================================


@app.route('/admin/category/add', methods=['POST'])
@login_required
def add_category():
    """
    添加新分类
    侧边栏通过 fetch 调用此接口，返回 JSON 以便前端动态插入 DOM
    """
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    # 后端校验：名称不能为空
    if not name:
        return api_response(False, error='分类名称不能为空。', status=400)
    if len(name) > 50:
        return api_response(False, error='分类名称不能超过 50 个字符。', status=400)
    if Category.query.filter_by(name=name).first():
        # 分类名必须唯一，防止重复
        return api_response(False, error=f'分类「{name}」已存在，请换一个名称。', status=400)

    # 创建新分类并写入数据库
    cat = Category(name=name, description=description)
    db.session.add(cat)
    db.session.commit()

    # 返回 JSON，包含新分类的 ID 和名称，前端用它动态插入列表
    return api_response(True, data={
        'category': {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description or ''
        }
    })


@app.route('/admin/category/edit/<int:id>', methods=['POST'])
@login_required
def edit_category(id):
    """
    编辑分类名称和描述
    URL 中的 id 是要编辑的分类 ID
    提交后重定向回 admin 页面
    """
    cat = Category.query.get_or_404(id)
    name = request.form.get('name', '').strip()
    description = request.form.get('description', '').strip()

    # 后端校验
    if not name:
        flash('分类名称不能为空。', 'error')
    elif len(name) > 50:
        flash('分类名称不能超过 50 个字符。', 'error')
    else:
        # 检查新名称是否与其他分类冲突（排除自己）
        existing = Category.query.filter_by(name=name).first()
        if existing and existing.id != id:
            flash(f'分类名「{name}」已被其他分类使用。', 'error')
        else:
            cat.name = name
            cat.description = description
            db.session.commit()
            flash(f'分类已更新为「{name}」。', 'success')

    return redirect(url_for('admin'))


@app.route('/admin/category/delete/<int:id>', methods=['POST'])
@login_required
def delete_category(id):
    """
    删除分类
    删除后，原本属于该分类的文章 category_id 会自动变为 NULL（不分类）
    这是因为 Article 表的外键 category_id 设置了 nullable=True
    """
    cat = Category.query.get_or_404(id)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f'分类「{name}」已删除，相关文章已变为「未分类」。', 'info')
    return redirect(url_for('admin'))


# =============================================
# 八、评论管理路由（需登录）
# =============================================

@app.route('/admin/comment/delete/<int:id>', methods=['POST'])
@login_required
def delete_comment(id):
    """
    删除评论（需登录）
    权限控制：只有以下两种身份可以删除评论：
      1. 文章作者 —— 管理自己文章下的评论
      2. 评论者本人 —— 删除自己发表的评论
    级联删除：删除评论时，其所有子回复一并删除（由模型层 cascade 保证）
    """
    comment = Comment.query.get_or_404(id)

    # ---- 权限检查：判断当前用户是否有权删除 ----
    # 身份一：文章作者（通过 comment.article.author_id 跨关系获取）
    is_article_author = (comment.article.author_id == current_user.id)
    # 身份二：评论者本人（Comment 表没有 user_id 外键，用昵称/用户名匹配）
    # 注意：字符串匹配不是最严谨的做法，但对于当前设计来说是可行的
    #       更严谨的做法是给 Comment 加 author_id 外键关联 User 表
    is_comment_author = (comment.author_name == current_user.nickname or
                         comment.author_name == current_user.username)

    if not is_article_author and not is_comment_author:
        flash('你没有权限删除这条评论。', 'error')
        return redirect(url_for('post', id=comment.article_id))

    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除。', 'info')
    # 删除后回到文章详情页
    return redirect(url_for('post', id=comment.article_id))


# =============================================
# 九、RSS 订阅源
# =============================================

@app.route('/feed.xml')
def feed():
    """
    RSS 2.0 订阅源
    返回最近 20 篇已发布文章的 XML，供 RSS 阅读器订阅
    """
    from flask import Response
    articles = Article.query \
        .filter_by(status='published') \
        .order_by(Article.is_pinned.desc(), Article.created_at.desc()) \
        .limit(20).all()

    site_url = request.url_root.rstrip('/')
    rss_items = []
    for a in articles:
        pub_date = a.created_at.strftime('%a, %d %b %Y %H:%M:%S +0000')
        article_url = f'{site_url}/post/{a.id}'
        # 摘要需要转义 HTML 标签（防止 RSS 阅读器把摘要当 HTML 解析）
        summary = a.summary or a.title
        rss_items.append(f'''    <item>
      <title>{a.title}</title>
      <link>{article_url}</link>
      <description>{summary}</description>
      <pubDate>{pub_date}</pubDate>
      <guid>{article_url}</guid>
    </item>''')

    xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>{app.config['SITE_NAME']}</title>
    <link>{site_url}</link>
    <description>记录学习与生活的点滴</description>
    <lastBuildDate>{datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')}</lastBuildDate>
{chr(10).join(rss_items)}
  </channel>
</rss>'''

    return Response(xml, mimetype='application/rss+xml')


# =============================================
# 十、音乐搜索路由（需登录）
# =============================================

@app.route('/api/search_songs')
@login_required
def search_songs():
    """
    歌曲搜索接口（GET，需登录）
    前端输入歌名 → 后端代理调用网易云公开搜索API → 返回歌曲列表JSON

    为什么不从前端直接调网易云API？
      1. 跨域（CORS）：网易云API不允许浏览器直接跨域请求
      2. 反爬：网易云会检查 Referer 和 User-Agent 请求头
      3. 安全：后端代理可以控制请求频率、过滤返回内容

    URL参数：?q=搜索关键词
    返回格式：{"songs": [{"id": "歌曲ID", "name": "歌名", "artist": "歌手"}]}
    """
    q = request.args.get('q', '').strip()

    # 空搜索或关键词过长（>50字符）→ 直接返回空列表，不发请求
    if not q or len(q) > 50:
        return jsonify({'songs': []})

    try:
        # 网易云音乐搜索API——这是公开接口，无需登录
        # type=1 表示搜单曲，limit=8 限制返回8条结果
        resp = requests.get(
            'https://music.163.com/api/search/get',
            params={'s': q, 'type': 1, 'limit': 10},
            headers={
                'Referer': 'https://music.163.com/',          # 必须带，否则被拦截
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            },
            timeout=5  # 5秒超时，避免前端一直等待
        )
        data = resp.json()

        # 提取我们关心的字段：歌曲ID、歌名、歌手名
        songs = []
        if data.get('code') == 200:
            for song in data.get('result', {}).get('songs', []):
                songs.append({
                    'id': str(song['id']),       # 转为字符串，方便前端直接拼接到iframe URL
                    'name': song['name'],         # 歌名
                    'artist': ', '.join(a['name'] for a in song.get('artists', []))  # 歌手（多人用逗号拼接）
                })

        return jsonify({'songs': songs})

    except Exception as e:
        # 网络错误、超时、JSON解析失败等 → 返回空列表
        # 生产环境中可以加日志记录，目前简单处理
        return jsonify({'songs': [], 'error': str(e)})


@app.route('/api/set_music', methods=['POST'])
@login_required
@csrf.exempt  # 纯 JSON API，CSRF token 不适用
def set_music():
    """
    快速切换歌曲接口（POST，需登录）
    前端选中歌曲后，通过 fetch POST 调用此接口保存到数据库

    接收JSON：{"music_id": "123456"}  或 {"music_id": ""} 表示关闭播放器
    返回JSON：{"ok": true}  或 {"ok": false, "error": "错误原因"}

    与个人中心保存的区别：
      - 这是纯API接口，只返回JSON，不重定向
      - 前端收到成功响应后，自己刷新 iframe 的 src
    """
    # request.get_json() 解析前端 fetch 发来的 JSON body
    data = request.get_json()
    music_id = data.get('music_id', '').strip() if data else ''

    # 如果传空字符串 → 关闭播放器（设置 music_id 为空）
    if not music_id:
        current_user.music_id = ''
        db.session.commit()
        return jsonify({'ok': True})

    # 校验长度（数据库字段限制30字符）
    if len(music_id) > 30:
        return jsonify({'ok': False, 'error': '歌曲ID过长'})

    # 保存到当前用户的 music_id 字段
    current_user.music_id = music_id
    db.session.commit()

    return jsonify({'ok': True})
