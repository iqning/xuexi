# 个人博客项目架构文档

## 技术栈

| 层 | 技术 |
|---|---|
| Web 框架 | Flask（Python） |
| 模板引擎 | Jinja2（Flask 内置） |
| 数据库 | MySQL |
| ORM | Flask-SQLAlchemy |
| 用户认证 | Flask-Login |
| 前端 | HTML + CSS（可选加 Vue） |

---

## 依赖清单

`
flask
flask-sqlalchemy
flask-login
pymysql
`

---

## 项目结构

`
blog/
├── app.py                 # Flask 入口，所有路由写在这里
├── config.py              # 数据库连接、密钥、上传路径等配置
├── models.py              # 所有数据库表定义
├── init_db.py             # 建表脚本，跑一次即可
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css      # 全局样式
│   └── uploads/           # 用户头像上传目录
└── templates/
    ├── base.html          # 页面骨架（头部/导航/侧栏/底部）
    ├── index.html         # 首页：文章列表 + 分页 + 分类筛选
    ├── post.html          # 文章详情 + 评论区
    ├── admin.html         # 后台：发布 / 删除文章
    ├── login.html         # 登录页
    ├── register.html      # 注册页
    └── profile.html       # 个人中心（查看 / 编辑资料）
`

---

## 数据表设计

### users（用户表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT | 主键，自增 |
| username | VARCHAR(50) | 登录名，唯一 |
| password_hash | VARCHAR(255) | 密码哈希（不存明文） |
| nickname | VARCHAR(50) | 显示昵称 |
| bio | VARCHAR(200) | 个人简介 |
| avatar | VARCHAR(255) | 头像路径，默认 default.png |
| created_at | DATETIME | 注册时间 |

### categories（分类表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT | 主键，自增 |
| name | VARCHAR(50) | 分类名，唯一 |
| description | VARCHAR(200) | 分类描述 |

### articles（文章表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT | 主键，自增 |
| title | VARCHAR(200) | 标题 |
| summary | VARCHAR(500) | 摘要 |
| content | TEXT | 正文（支持 HTML） |
| created_at | DATETIME | 创建时间 |
| updated_at | DATETIME | 更新时间 |
| author_id | INT | 外键 → users.id |
| category_id | INT | 外键 → categories.id（可为空） |

### comments（评论表）

| 字段 | 类型 | 说明 |
|---|---|---|
| id | INT | 主键，自增 |
| content | TEXT | 评论内容 |
| author_name | VARCHAR(50) | 评论者昵称 |
| author_email | VARCHAR(100) | 评论者邮箱（可选） |
| created_at | DATETIME | 评论时间 |
| article_id | INT | 外键 → articles.id |
| parent_id | INT | 外键 → comments.id（回复，可为空） |

> parent_id 非空表示回复某条评论，为空表示顶级评论。

### 表关系图

`
users ──< articles ──< comments
           │
categories ─┘
`

- users 1:N articles
- categories 1:N articles
- articles 1:N comments
- comments 1:N comments（自关联，支持楼中楼回复）

---

## 路由总览

### 公开页面

| 方法 | URL | 模板 | 说明 |
|---|---|---|---|
| GET | / | index.html | 首页，分页展示所有文章，右侧分类列表 |
| GET | /post/<id> | post.html | 文章详情 + 评论区 + 评论表单 |
| GET | /category/<id> | index.html | 按分类筛选文章 |

### 用户认证

| 方法 | URL | 模板 | 说明 |
|---|---|---|---|
| GET/POST | /register | register.html | 注册新用户 |
| GET/POST | /login | login.html | 登录 |
| GET | /logout | 无（重定向） | 退出登录 |

### 个人中心（需登录）

| 方法 | URL | 模板 | 说明 |
|---|---|---|---|
| GET/POST | /profile | profile.html | 查看 / 编辑个人资料 |
| GET | /my-posts | index.html | 我发布的文章列表 |

### 后台管理（需登录）

| 方法 | URL | 说明 |
|---|---|---|
| GET/POST | /admin | 查看文章列表 / 发布新文章 |
| POST | /admin/delete/<id> | 删除自己的文章 |

### 评论操作

| 方法 | URL | 说明 |
|---|---|---|
| POST | /post/<id>/comment | 提交评论（文章页内嵌表单） |
| POST | /admin/comment/delete/<id> | 博主删除评论（需登录） |

---

## 关键实现要点

### 密码安全
- 注册时用 werkzeug.security.generate_password_hash() 哈希后存库
- 登录时用 werkzeug.security.check_password_hash() 验证
- **绝不存明文密码**

### 登录状态管理
- 使用 Flask-Login 管理 session
- 需要登录的路由加 @login_required 装饰器
- User 模型需实现 is_authenticated、get_id() 等方法（继承 UserMixin）

### 文章内容
- 正文字段 content 存 HTML，渲染时用 {{ content | safe }}
- 后期可集成 Markdown 编辑器（如 SimpleMDE）

### 分页
- 使用 Article.query.paginate(page=page, per_page=6)
- 模板中判断 pagination.has_prev / has_next

### 头像上传
- 设置上传大小限制
- 文件名用 uuid 重命名防止冲突
- 图片格式校验

---

## 开发步骤

1. 初始化项目目录结构
2. 安装依赖：pip install flask flask-sqlalchemy flask-login pymysql
3. MySQL 创建数据库：CREATE DATABASE blog CHARACTER SET utf8mb4;
4. 编写 config.py，填入数据库连接信息
5. 编写 models.py，定义四张表及关系
6. 编写 pp.py，初始化 Flask 应用和 Flask-Login
7. 编写 init_db.py，执行 db.create_all() 建表
8. 实现页面路由
9. 实现用户认证路由
10. 编写 ase.html 骨架模板
11. 编写各页面模板
12. 编写 style.css 样式
13. 运行 lask run 测试

---

## 后期可选扩展

- 标签系统（多对多）
- 文章草稿 / 发布状态
- Markdown 编辑器
- RSS 订阅
- 搜索功能
- 访问量统计
- Vue.js 重写前端（前后端分离）
## 编写规则
-所有的代码都要有注释，且注释用中文编写
-每次不要一写写很多的代码，要分块写，并且询问我是否能明白这块代码的作用，不懂的你要为我讲解，毕竟这是一个半学习的项目