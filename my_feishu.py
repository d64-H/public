import streamlit as st
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime

# ================= 配置区 =================
st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

# ⚠️ 把下面这行里的 [填你的密码] 换成你真实的数据库密码！
# 千万不要带中括号，密码直接连着冒号和@
SUPABASE_DB_URL = "postgresql://postgres.jkexkoplexlwkslfomom:6KCGdxL608z6m9WX@aws-0-ap-southeast-1.pooler.supabase.com:5432/postgres"

@st.cache_resource
def init_connection():
    try:
        # 使用 psycopg2 直接连底层数据库，完美绕过 DNS 解析失败问题
        conn = psycopg2.connect(SUPABASE_DB_URL)
        return conn
    except Exception as e:
        st.error(f"❌ 数据库连接失败，请检查密码是否填写正确。报错详情: {e}")
        return None

db_conn = init_connection()

# ================= 数据管理区 =================
def get_posts():
    if db_conn is None:
        return []
    try:
        with db_conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM posts ORDER BY id DESC")
            return cur.fetchall()
    except Exception as e:
        db_conn.rollback()
        st.error(f"读取文章失败: {e}")
        return []

def add_post(author, title, content):
    if db_conn is None: return False
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "INSERT INTO posts (author, title, content, time, comments, likes) VALUES (%s, %s, %s, %s, %s, %s)",
                (author, title, content, datetime.now().strftime("%Y-%m-%d %H:%M"), Json([]), 0)
            )
            db_conn.commit()
        return True
    except Exception as e:
        db_conn.rollback()
        st.error(f"发布失败: {e}")
        return False

def update_post(post_id, title, content):
    if db_conn is None: return
    try:
        with db_conn.cursor() as cur:
            cur.execute(
                "UPDATE posts SET title = %s, content = %s, time = %s WHERE id = %s",
                (title, content, datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)", post_id)
            )
            db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        st.error(f"修改失败: {e}")

def delete_post(post_id):
    if db_conn is None: return
    try:
        with db_conn.cursor() as cur:
            cur.execute("DELETE FROM posts WHERE id = %s", (post_id,))
            db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        st.error(f"删除失败: {e}")

def like_post(post_id, current_likes):
    if db_conn is None: return
    try:
        with db_conn.cursor() as cur:
            cur.execute("UPDATE posts SET likes = %s WHERE id = %s", (current_likes + 1, post_id))
            db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        st.error(f"点赞失败: {e}")

def update_comments(post_id, comments_list):
    if db_conn is None: return
    try:
        with db_conn.cursor() as cur:
            cur.execute("UPDATE posts SET comments = %s WHERE id = %s", (Json(comments_list), post_id))
            db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        st.error(f"留言保存失败: {e}")

# ================= 界面展示区 =================
if "current_post_id" not in st.session_state:
    st.session_state.current_post_id = None
if "liked_posts" not in st.session_state:
    st.session_state.liked_posts = []

with st.sidebar:
    st.title("🏠 稚荷")
    if st.button("➕ 写一篇新文章", use_container_width=True, type="primary"):
        st.session_state.current_post_id = "new"
        st.rerun()

    st.divider()
    st.write("📚 **全部文章**")
    posts = get_posts()
    
    if not posts:
        st.info("还没有文章，快来发第一篇吧！")
    else:
        for post in posts:
            display_author = post.get('author') or "匿名"
            likes_str = f" 👍{post.get('likes', 0)}" if post.get('likes', 0) > 0 else ""
            if st.button(f"📄 {post['title']} (by {display_author}){likes_str}", key=str(post['id']), use_container_width=True):
                st.session_state.current_post_id = str(post['id'])
                st.rerun()

if st.session_state.current_post_id == "new":
    st.title("✍️ 写新文章")
    author = st.text_input("你的昵称 (选填)", placeholder="不填则显示为匿名")
    title = st.text_input("文章标题")
    content = st.text_area("正文内容 (支持 Markdown)", height=300)
    
    if st.button("发布文章", type="primary"):
        if not title or not content:
            st.warning("标题和内容不能为空哦！")
        else:
            if add_post(author.strip() if author.strip() else "匿名", title, content):
                st.success("发布成功！文章已永久保存至云端！")
                st.session_state.current_post_id = None
                st.rerun()

elif st.session_state.current_post_id is not None:
    post_id = int(st.session_state.current_post_id)
    current_post = next((p for p in posts if p["id"] == post_id), None)
    
    if current_post:
        st.title(current_post["title"])
        st.caption(f"作者：{current_post.get('author')} | 发布于：{current_post.get('time')}")
        st.divider()
        
        with st.container(border=True):
            st.markdown(current_post["content"])
        
        # ================= 点赞区域 =================
        current_likes = current_post.get("likes") or 0
        col_like, col_count, _ = st.columns([1.5, 3, 5])
        
        with col_like:
            if post_id not in st.session_state.liked_posts:
                if st.button("👍 点赞", type="primary", use_container_width=True):
                    like_post(post_id, current_likes)
                    st.session_state.liked_posts.append(post_id)
                    st.rerun()
            else:
                st.button("❤️ 已赞", disabled=True, use_container_width=True)
        with col_count:
            st.write(f"<div style='padding-top: 8px; color: gray;'>已有 {current_likes} 人点赞</div>", unsafe_allow_html=True)
        
        # 文章管理面板
        with st.expander("⚙️ 管理当前文章 (修改/撤回)"):
            with st.form("edit_post_form"):
                edit_title = st.text_input("修改标题", value=current_post["title"])
                edit_content = st.text_area("修改正文", value=current_post["content"], height=150)
                if st.form_submit_button("保存修改"):
                    update_post(post_id, edit_title, edit_content)
                    st.success("文章已修改！")
                    st.rerun()
            if st.button("🗑️ 撤回 (删除) 整篇文章", type="primary"):
                delete_post(post_id)
                st.session_state.current_post_id = None
                st.success("文章已删除！")
                st.rerun()
                
        st.divider()
        
        # 评论列表部分（兼容可能没有 comments 字段的情况）
        comments_list = current_post.get("comments")
        if comments_list is None:
            comments_list = []
            
        st.subheader(f"💬 评论 ({len(comments_list)})")
        
        for i, c in enumerate(comments_list):
            col_content, col_manage = st.columns([8, 2])
            with col_content:
                st.markdown(f"**{c['author']}** 回复于 {c['time']}：\n> {c['content']}")
            with col_manage:
                with st.expander("⚙️ 操作"):
                    with st.form(key=f"edit_comment_{i}"):
                        new_c_content = st.text_area("修改留言", value=c["content"], key=f"c_txt_{i}", height=100)
                        if st.form_submit_button("保存修改"):
                            c["content"] = new_c_content
                            c["time"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
                            update_comments(post_id, comments_list)
                            st.rerun()
                    if st.button("🗑️ 撤回", key=f"del_c_{i}"):
                        comments_list.pop(i)
                        update_comments(post_id, comments_list)
                        st.rerun()
            st.write("") 
        
        # 发表新评论
        with st.expander("🗣️ 写留言 / 评论", expanded=True):
            c_author = st.text_input("你的昵称 (选填)", key="c_author", placeholder="不填则显示为匿名")
            c_content = st.text_area("留言内容", key="c_content")
            if st.button("发送留言"):
                if c_content.strip():
                    new_comment = {"author": c_author.strip() if c_author.strip() else "匿名", "content": c_content, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
                    comments_list.append(new_comment)
                    update_comments(post_id, comments_list)
                    st.rerun()
                else:
                    st.warning("留言内容不能为空！")

elif st.session_state.current_post_id is None:
    st.title("👋 欢迎来到稚荷")
    st.info("这里是一个开放的树洞。你的文章和留言均已永久保存在云端，再也不会丢失。")