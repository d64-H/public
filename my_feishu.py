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
                "author": author.strip() if author.strip() else "匿名",
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
        # 展示文章信息
        st.title(current_post["title"])
        st.caption(f"作者：{current_post['author']} | 发布于：{current_post['time']}")
        st.divider()
        
        # 展示正文
        with st.container(border=True):
            st.markdown(current_post["content"])
        
        # --- 新增：文章管理面板 ---
        with st.expander("⚙️ 管理当前文章 (修改/撤回)"):
            with st.form("edit_post_form"):
                edit_title = st.text_input("修改标题", value=current_post["title"])
                edit_content = st.text_area("修改正文", value=current_post["content"], height=150)
                if st.form_submit_button("保存修改"):
                    current_post["title"] = edit_title
                    current_post["content"] = edit_content
                    current_post["time"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
                    save_data(st.session_state.bbs_data)
                    st.success("文章已修改！")
                    st.rerun()
            
            # 删除操作放在 form 外面，防止误触
            if st.button("🗑️ 撤回 (删除) 整篇文章", type="primary"):
                st.session_state.bbs_data = [p for p in st.session_state.bbs_data if p["id"] != current_post["id"]]
                save_data(st.session_state.bbs_data)
                st.session_state.current_post_id = None
                st.success("文章已删除！")
                st.rerun()
        # ------------------------
            
        st.divider()
        
        # 评论区
        st.subheader(f"💬 评论 ({len(current_post['comments'])})")
        
        # 展示已有评论
        for i, c in enumerate(current_post["comments"]):
            col_content, col_manage = st.columns([8, 2])
            with col_content:
                st.markdown(f"**{c['author']}** 回复于 {c['time']}：\n> {c['content']}")
            with col_manage:
                # --- 新增：留言管理面板 ---
                with st.expander("⚙️ 操作"):
                    with st.form(key=f"edit_comment_{i}"):
                        new_c_content = st.text_area("修改留言", value=c["content"], key=f"c_txt_{i}", height=100)
                        if st.form_submit_button("保存修改"):
                            c["content"] = new_c_content
                            c["time"] = datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"
                            save_data(st.session_state.bbs_data)
                            st.rerun()
                    
                    if st.button("🗑️ 撤回", key=f"del_c_{i}"):
                        current_post["comments"].pop(i)
                        save_data(st.session_state.bbs_data)
                        st.rerun()
                # ------------------------
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
    st.title("👋 欢迎来到稚荷")
    st.info("这里是一个开放的树洞。你可以随意发表文章，也可以匿名留言。点击左侧开始吧！")