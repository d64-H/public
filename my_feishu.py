import streamlit as st
import json
import os
from datetime import datetime

# ================= 配置区 =================
DATA_FILE = "bbs_data.json"  # 数据保存在这个本地文件里
st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

# ================= 数据管理区 =================
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 初始化数据
if "bbs_data" not in st.session_state:
    st.session_state.bbs_data = load_data()
if "current_post_id" not in st.session_state:
    st.session_state.current_post_id = None

# ================= 侧边栏 (文章列表) =================
with st.sidebar:
    st.title("🏠 自由留言板")
    
    if st.button("➕ 写一篇新文章", use_container_width=True, type="primary"):
        st.session_state.current_post_id = "new"
        st.rerun()

    st.divider()
    st.write("📚 **全部文章**")
    
    if not st.session_state.bbs_data:
        st.info("还没有文章，快来发第一篇吧！")
    else:
        # 按时间倒序显示
        for post in reversed(st.session_state.bbs_data):
            display_author = post['author'] if post['author'] else "匿名"
            if st.button(f"📄 {post['title']} (by {display_author})", key=post['id'], use_container_width=True):
                st.session_state.current_post_id = post['id']
                st.rerun()

# ================= 主界面 =================
if st.session_state.current_post_id == "new":
    # 【写新文章界面】
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
                "author": author.strip() if author.strip() else "匿名", # 如果没填，就赋值为匿名
                "title": title,
                "content": content,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "comments": []
            }
            st.session_state.bbs_data.append(new_post)
            save_data(st.session_state.bbs_data)
            st.success("发布成功！")
            st.session_state.current_post_id = new_post["id"]
            st.rerun()

elif st.session_state.current_post_id is not None:
    # 【查看文章及评论界面】
    current_post = next((p for p in st.session_state.bbs_data if p["id"] == st.session_state.current_post_id), None)
    
    if current_post:
        st.title(current_post["title"])
        st.caption(f"作者：{current_post['author']} | 发布于：{current_post['time']}")
        st.divider()
        
        # 显示正文
        with st.container(border=True):
            st.markdown(current_post["content"])
            
        st.divider()
        
        # 评论区
        st.subheader(f"💬 评论 ({len(current_post['comments'])})")
        
        # 展示已有评论
        for c in current_post["comments"]:
            st.markdown(f"**{c['author']}** 回复于 {c['time']}：\n> {c['content']}")
            st.write("") 
        
        # 发表新评论
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
                    save_data(st.session_state.bbs_data)
                    st.rerun()
                else:
                    st.warning("留言内容不能为空！")

elif st.session_state.current_post_id is None:
    # 【欢迎首页】
    st.title("👋 欢迎来到自由留言板")
    st.info("这里是一个开放的树洞。你可以随意发表文章，也可以匿名留言。点击左侧开始吧！")