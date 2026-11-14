import streamlit as st
import json
import os
from datetime import datetime

# ================= 配置区 =================
st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

DATA_FILE = "my_posts.json"

# ================= 本地数据管理区（无网络请求） =================
def load_posts():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def save_posts(posts):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(posts, f, ensure_ascii=False, indent=4)

# 初始化数据
if "posts" not in st.session_state:
    st.session_state.posts = load_posts()
if "current_post_id" not in st.session_state:
    st.session_state.current_post_id = None

# ================= 界面展示区 =================
with st.sidebar:
    st.title("🏠 稚荷")
    if st.button("➕ 写一篇新文章", use_container_width=True, type="primary"):
        st.session_state.current_post_id = "new"
        st.rerun()

    st.divider()
    st.write("📚 **全部文章**")
    
    if not st.session_state.posts:
        st.info("还没有文章，快来发第一篇吧！")
    else:
        for post in reversed(st.session_state.posts):
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
            new_post = {
                "id": str(int(datetime.now().timestamp())),
                "author": author.strip() if author.strip() else "匿名",
                "title": title,
                "content": content,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "comments": [],
                "likes": 0
            }
            st.session_state.posts.append(new_post)
            save_posts(st.session_state.posts)
            st.success("发布成功！")
            st.session_state.current_post_id = None
            st.rerun()

elif st.session_state.current_post_id is not None:
    post_id = st.session_state.current_post_id
    current_post = next((p for p in st.session_state.posts if p["id"] == post_id), None)
    
    if current_post:
        st.title(current_post["title"])
        st.caption(f"作者：{current_post.get('author')} | 发布于：{current_post.get('time')}")
        st.divider()
        
        with st.container(border=True):
            st.markdown(current_post["content"])
            
        # 点赞区域
        if "liked_posts" not in st.session_state:
            st.session_state.liked_posts = []
            
        current_likes = current_post.get("likes", 0)
        col_like, col_count, _ = st.columns([1.5, 3, 5])
        with col_like:
            if post_id not in st.session_state.liked_posts:
                if st.button("👍 点赞", type="primary", use_container_width=True):
                    current_post["likes"] = current_likes + 1
                    save_posts(st.session_state.posts)
                    st.session_state.liked_posts.append(post_id)
                    st.rerun()
            else:
                st.button("❤️ 已赞", disabled=True, use_container_width=True)
        with col_count:
            st.write(f"<div style='padding-top: 8px; color: gray;'>已有 {current_likes} 人点赞</div>", unsafe_allow_html=True)
            
        # 管理文章
        with st.expander("⚙️ 管理当前文章 (修改/撤回)"):
            with st.form("edit_post_form"):
                edit_title = st.text_input("修改标题", value=current_post["title"])
                edit_content = st.text_area("修改正文", value=current_post["content"], height=150)
                if st.form_submit_button("保存修改"):
                    current_post["title"] = edit_title
                    current_post["content"] = edit_content
                    current_post["time"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
                    save_posts(st.session_state.posts)
                    st.success("文章已修改！")
                    st.rerun()
            if st.button("🗑️ 撤回 (删除) 整篇文章", type="primary"):
                st.session_state.posts = [p for p in st.session_state.posts if p["id"] != post_id]
                save_posts(st.session_state.posts)
                st.session_state.current_post_id = None
                st.success("文章已删除！")
                st.rerun()
                
        st.divider()
        
        comments_list = current_post.get("comments", [])
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
                            save_posts(st.session_state.posts)
                            st.rerun()
                    if st.button("🗑️ 撤回", key=f"del_c_{i}"):
                        comments_list.pop(i)
                        save_posts(st.session_state.posts)
                        st.rerun()
            st.write("")
            
        # 写评论
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
                    comments_list.append(new_comment)
                    save_posts(st.session_state.posts)
                    st.rerun()
                else:
                    st.warning("留言内容不能为空！")

elif st.session_state.current_post_id is None:
    st.title("👋 欢迎来到稚荷")
    st.info("这里是一个开放的树洞。你的文章和留言都会保存在这里。")