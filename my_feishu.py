import streamlit as st
import requests
import urllib3
from datetime import datetime

# 禁用安全警告（因为下面用 IP 直连时会忽略证书校验，防止满屏红字警告）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

st.set_page_config(page_title="稚荷", page_icon="📝", layout="wide")

# ================= 核心配置 =================
SUPABASE_KEY = "sb_publishable_zy5HhmPUG005upnERSSvuA_EYbPXKI8"
HOST = "jkexkoplexlwkslfomom.supabase.co"
# 强行指定 Cloudflare 的 Anycast IP，彻底绕过 Streamlit 云端的 DNS 解析失败问题
CLOUDFLARE_IPS = ["104.18.38.56", "104.16.0.1", "172.67.200.0"]

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Host": HOST,  # 关键：伪造真实的 Host 头，骗过 Supabase 网关
    "Prefer": "return=representation"
}

# 智能请求引擎：优先走域名，如果超时，立刻切换 IP 强连
def smart_request(method, endpoint, json_data=None):
    # 1. 先尝试正常域名请求
    try:
        url = f"https://{HOST}/rest/v1/{endpoint}"
        if method == "GET": res = requests.get(url, headers=HEADERS, timeout=5)
        elif method == "POST": res = requests.post(url, headers=HEADERS, json=json_data, timeout=5)
        elif method == "PATCH": res = requests.patch(url, headers=HEADERS, json=json_data, timeout=5)
        elif method == "DELETE": res = requests.delete(url, headers=HEADERS, timeout=5)
        if res.status_code in [200, 201, 204]: return res
    except Exception:
        pass # 如果失败，进入下面的 IP 强连模式

    # 2. 终极自救：直接连 IP（无论 DNS 怎么被污染，只要网络通，就能连上）
    for ip in CLOUDFLARE_IPS:
        try:
            url = f"https://{ip}/rest/v1/{endpoint}"
            if method == "GET": res = requests.get(url, headers=HEADERS, verify=False, timeout=5)
            elif method == "POST": res = requests.post(url, headers=HEADERS, json=json_data, verify=False, timeout=5)
            elif method == "PATCH": res = requests.patch(url, headers=HEADERS, json=json_data, verify=False, timeout=5)
            elif method == "DELETE": res = requests.delete(url, headers=HEADERS, verify=False, timeout=5)
            if res.status_code in [200, 201, 204]: return res
        except Exception:
            continue
            
    return None

# ================= 数据管理区 =================
def get_posts():
    res = smart_request("GET", "posts?select=*&order=id.desc")
    if res and res.status_code == 200:
        return res.json()
    st.error("网络连接超时，云端服务器正在努力重试。请刷新页面。")
    return []

def add_post(author, title, content):
    data = {"author": author, "title": title, "content": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M"), "comments": [], "likes": 0}
    res = smart_request("POST", "posts", json_data=data)
    return res and res.status_code in [200, 201]

def update_post(post_id, title, content):
    data = {"title": title, "content": content, "time": datetime.now().strftime("%Y-%m-%d %H:%M") + " (已编辑)"}
    smart_request("PATCH", f"posts?id=eq.{post_id}", json_data=data)

def delete_post(post_id):
    smart_request("DELETE", f"posts?id=eq.{post_id}")

def like_post(post_id, current_likes):
    smart_request("PATCH", f"posts?id=eq.{post_id}", json_data={"likes": current_likes + 1})

def update_comments(post_id, comments_list):
    smart_request("PATCH", f"posts?id=eq.{post_id}", json_data={"comments": comments_list})

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