import streamlit as st
import psycopg2
from supabase import create_client, Client
from datetime import datetime

st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

# ================= 核心配置区（直接写死） =================
SUPABASE_URL = "https://jkexkoplexlwkslfomom.supabase.co"
SUPABASE_KEY = "sb_publishable_zy5HhmPUG005upnERSSvuA_EYbPXKI8"
# ⚠️ 把下面的中文换成你真实的数据库密码，不要带方括号！
SUPABASE_DB_URL = "postgresql://postgres.jkexkoplexlwkslfomom:你的真实数据库密码@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres"

@st.cache_resource
def init_connection():
    try:
        # 用 psycopg2 建立底层连接，绕过 DNS 污染
        conn = psycopg2.connect(SUPABASE_DB_URL)
        # 建立 API 客户端，用于增删改查
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        return client, conn
    except Exception as e:
        st.error(f"数据库连接失败: {e}")
        return None, None

supabase, db_conn = init_connection()

# ================= 数据管理区（统一使用 supabase-py 的标准方法） =================
def get_posts():
    if supabase is None:
        return []
    try:
        res = supabase.table("posts").select("*").order("id", desc=True).execute()
        return res.data
    except Exception as e:
        st.error(f"读取文章失败，请检查数据库: {e}")
        return []

def add_post(author, title, content):
    data = {
        "author": author,
        "title": title,
        "content": content,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "comments": []
    }
    supabase.table("posts").insert(data).execute()

def update_post(post_id, title, content):
    data = {
        "title": title,
        "content": content,
        "time": datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
    }
    supabase.table("posts").update(data).eq("id", post_id).execute()

def delete_post(post_id):
    supabase.table("posts").delete().eq("id", post_id).execute()

def update_comments(post_id, comments_list):
    supabase.table("posts").update({"comments": comments_list}).eq("id", post_id).execute()

# ================= 界面展示区 =================
if "current_post_id" not in st.session_state:
    st.session_state.current_post_id = None

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
            if st.button(f"📄 {post['title']} (by {display_author})", key=str(post['id']), use_container_width=True):
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
            add_post(author.strip() if author.strip() else "匿名", title, content)
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
        st.subheader(f"💬 评论 ({len(current_post['comments'])})")
        
        for i, c in enumerate(current_post["comments"]):
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
                            update_comments(post_id, current_post["comments"])
                            st.rerun()
                    if st.button("🗑️ 撤回", key=f"del_c_{i}"):
                        current_post["comments"].pop(i)
                        update_comments(post_id, current_post["comments"])
                        st.rerun()
            st.write("") 
        
        with st.expander("🗣️ 写留言 / 评论", expanded=True):
            c_author = st.text_input("你的昵称 (选填)", key="c_author", placeholder="不填则显示为匿名")
            c_content = st.text_area("留言内容", key="c_content")
            if st.button("发送留言"):
                if c_content.strip():
                    new_comment = {
                        "author": c_author.strip() if c_author.strip() else "匿名",
                        "content": c_content,
                        "time": datetime.now().strftime("%Y-%m-%d %H:%M")
                    }
                    current_post["comments"].append(new_comment)
                    update_comments(post_id, current_post["comments"])
                    st.rerun()
                else:
                    st.warning("留言内容不能为空！")

elif st.session_state.current_post_id is None:
    st.title("👋 欢迎来到稚荷")
    st.info("这里是一个开放的树洞。你的文章和留言均已永久保存在云端，再也不会丢失。")