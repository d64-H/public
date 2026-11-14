import supadns
supadns.patch()  # 强制开启防 DNS 污染模式

import streamlit as st
import requests
from datetime import datetime
# ... 下面保持原样 ...
import supadns
supadns.patch() 
import streamlit as st
import requests
from datetime import datetime

# ================= 配置区 =================
st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

# 确保这里没有任何多余的空格或后缀
SUPABASE_URL = "https://jkexkoplexlwkslfomom.supabase.co"
SUPABASE_KEY = "sb_publishable_zy5HhmPUG005upnERSSvuA_EYbPXKI8"

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}
REST_URL = f"{SUPABASE_URL}/rest/v1/posts"

# ================= 数据管理区 =================
def get_posts():
    try:
        res = requests.get(f"{REST_URL}?select=*&order=id.desc", headers=HEADERS)
        if res.status_code == 200:
            return res.json()
        else:
            st.error(f"读取文章失败 (状态码 {res.status_code}): {res.text}")
            return []
    except Exception as e:
        st.error(f"网络请求异常: {e}")
        return []

def add_post(author, title, content):
    data = {
        "author": author, 
        "title": title, 
        "content": content, 
        "time": datetime.now().strftime("%Y-%m-%d %H:%M"), 
        "comments": [], 
        "likes": 0
    }
    res = requests.post(REST_URL, headers=HEADERS, json=data)
    if res.status_code not in [200, 201]:
        st.error(f"❌ 数据库拒绝写入！错误详情: {res.text}")
        return False
    return True

def update_post(post_id, title, content):
    data = {"title": title, "content": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"}
    res = requests.patch(f"{REST_URL}?id=eq.{post_id}", headers=HEADERS, json=data)
    if res.status_code not in [200, 204]:
        st.error(f"修改失败: {res.text}")

def delete_post(post_id):
    res = requests.delete(f"{REST_URL}?id=eq.{post_id}", headers=HEADERS)
    if res.status_code not in [200, 204]:
        st.error(f"删除失败: {res.text}")

def update_comments(post_id, comments_list):
    res = requests.patch(f"{REST_URL}?id=eq.{post_id}", headers=HEADERS, json={"comments": comments_list})
    if res.status_code not in [200, 204]:
        st.error(f"留言失败: {res.text}")

def like_post(post_id, current_likes):
    data = {"likes": current_likes + 1}
    res = requests.patch(f"{REST_URL}?id=eq.{post_id}", headers=HEADERS, json=data)
    if res.status_code not in [200, 204]:
        st.error(f"点赞失败: {res.text}")

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
        
        # 发表新评论
        with st.expander("🗣️ 写留言 / 评论", expanded=True):
            c_author = st.text_input("你的昵称 (选填)", key="c_author", placeholder="不填则显示为匿名")
            c_content = st.text_area("留言内容", key="c_content")
            if st.button("发送留言"):
                if c_content.strip():
                    new_comment = {"author": c_author.strip() if c_author.strip() else "匿名", "content": c_content, "time": datetime.now().strftime("%Y-%m-%d %H:%M")}
                    current_post["comments"].append(new_comment)
                    update_comments(post_id, current_post["comments"])
                    st.rerun()
                else:
                    st.warning("留言内容不能为空！")

elif st.session_state.current_post_id is None:
    st.title("👋 欢迎来到稚荷")
    st.info("这里是一个开放的树洞。你的文章和留言均已永久保存在云端，再也不会丢失。")