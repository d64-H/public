import streamlit as st
import requests
import time
from datetime import datetime

# ================= 配置区（已全部写死，无需任何修改） =================
st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

SUPABASE_URL = "https://jkexkoplexlwkslfomom.supabase.co"
# 已经修正了你说的 I8 问题
SUPABASE_KEY = "sb_publishable_zy5HhmPUG005upnERSSvuA_EYbPXKI8"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}
REST_URL = f"{SUPABASE_URL}/rest/v1/posts"

# ================= 数据管理区（带自动重试的请求引擎） =================
def safe_request(method, url, json_data=None):
    """自带 3 次重试机制的网络请求，防止云端 DNS 偶尔抽风"""
    for attempt in range(3):
        try:
            if method == "GET":
                res = requests.get(url, headers=HEADERS, timeout=10)
            elif method == "POST":
                res = requests.post(url, headers=HEADERS, json=json_data, timeout=10)
            elif method == "PATCH":
                res = requests.patch(url, headers=HEADERS, json=json_data, timeout=10)
            elif method == "DELETE":
                res = requests.delete(url, headers=HEADERS, timeout=10)
            
            if res.status_code in [200, 201, 204]:
                return res
        except requests.exceptions.RequestException as e:
            if attempt == 2: # 最后一次尝试也失败了
                st.error(f"网络连接超时，请稍后刷新重试。")
                return None
            time.sleep(1.5) # 失败后等 1.5 秒再试
    return None

def get_posts():
    res = safe_request("GET", f"{REST_URL}?select=*&order=id.desc")
    if res and res.status_code == 200:
        return res.json()
    return []

def add_post(author, title, content):
    data = {
        "author": author, "title": title, "content": content, 
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "comments": [], "likes": 0
    }
    res = safe_request("POST", REST_URL, json_data=data)
    if res and res.status_code in [200, 201]:
        return True
    st.error("发布失败，请稍后重试。")
    return False

def update_post(post_id, title, content):
    data = {"title": title, "content": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"}
    safe_request("PATCH", f"{REST_URL}?id=eq.{post_id}", json_data=data)

def delete_post(post_id):
    safe_request("DELETE", f"{REST_URL}?id=eq.{post_id}")

def like_post(post_id, current_likes):
    safe_request("PATCH", f"{REST_URL}?id=eq.{post_id}", json_data={"likes": current_likes + 1})

def update_comments(post_id, comments_list):
    safe_request("PATCH", f"{REST_URL}?id=eq.{post_id}", json_data={"comments": comments_list})

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
        
        # 点赞区域
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
        
        comments_list = current_post.get("comments") or []
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