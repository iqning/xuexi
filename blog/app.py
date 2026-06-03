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
        'now': datetime.utcnow(),
        'site_name': app.config['SITE_NAME'],  # 站点名称，所有模板可用
    }


# =============================================
# 注册自定义 Jinja2 宏：递归渲染评论
# =============================================
# 把 render_comment 宏定义在 app.py 中，注册到 Jinja2 环境，
# 这样所有模板都能直接调用 {{ render_comment(comment) | safe }}
# 宏用 Jinja2 的 Template 对象编译一次，避免每次请求都重新解析
from jinja2 import Template

_comment_macro = Template("""
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

    # 统计数据：文章总数、分类总数，供 Hero 横幅和统计栏使用
    stats = {
        'article_count': Article.query.count(),
        'category_count': Category.query.count(),
        'comment_count': Comment.query.count(),
    }

    return render_template('index.html',
                           posts=posts,
                           pagination=pagination,
                           page_title='最新文章',
                           stats=stats)


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

        # ---- 后端校验 ----
        if not title:
            flash('文章标题不能为空。', 'error')
        elif not content:
            flash('文章正文不能为空。', 'error')
        elif len(title) > 200:
            flash('标题不能超过 200 个字符。', 'error')
        else:
            # 更新文章字段
            article.title = title
            article.summary = summary
            article.content = content
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
        return {'success': False, 'message': '分类名称不能为空。'}
    if len(name) > 50:
        return {'success': False, 'message': '分类名称不能超过 50 个字符。'}
    if Category.query.filter_by(name=name).first():
        # 分类名必须唯一，防止重复
        return {'success': False, 'message': f'分类「{name}」已存在，请换一个名称。'}

    # 创建新分类并写入数据库
    cat = Category(name=name, description=description)
    db.session.add(cat)
    db.session.commit()

    # 返回 JSON，包含新分类的 ID 和名称，前端用它动态插入列表
    return {
        'success': True,
        'category': {
            'id': cat.id,
            'name': cat.name,
            'description': cat.description or ''
        }
    }


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
    博主删除评论（任意登录用户都可以删评论，体现博主身份）
    删除评论时，其子回复也一并删除（级联删除由模型层 cascade 保证）
    """
    comment = Comment.query.get_or_404(id)
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除。', 'info')
    # 删除后回到文章详情页
    return redirect(url_for('post', id=comment.article_id))


# =============================================
# 九、音乐搜索路由（需登录）
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
