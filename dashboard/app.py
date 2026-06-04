import time
import requests
import streamlit as st

API_URL = "http://localhost:8000"
API_KEY = "dev-secret-key"
HEADERS = {"X-API-Key": API_KEY}

st.set_page_config(page_title="DevOps Monitor", layout="wide")
st.title("DevOps Monitoring Dashboard")

tab1, tab2 = st.tabs(["System Metrics", "Servers"])

# ── Tab 1: Live metrics ────────────────────────────────────────────────────────
with tab1:
    if "history" not in st.session_state:
        st.session_state.history = {"cpu": [], "memory": []}

    placeholder = st.empty()

    try:
        data = requests.get(f"{API_URL}/metrics", timeout=3).json()
        st.session_state.history["cpu"].append(data["cpu_percent"])
        st.session_state.history["memory"].append(data["memory_percent"])
        if len(st.session_state.history["cpu"]) > 60:
            st.session_state.history["cpu"].pop(0)
            st.session_state.history["memory"].pop(0)

        with placeholder.container():
            col1, col2, col3 = st.columns(3)
            col1.metric("CPU %", f"{data['cpu_percent']}%")
            col2.metric("Memory %", f"{data['memory_percent']}%",
                        f"{data['memory_used_gb']} / {data['memory_total_gb']} GB")
            col3.metric("Disk %", f"{data['disk_percent']}%",
                        f"{data['disk_used_gb']} / {data['disk_total_gb']} GB")

            chart_data = {
                "CPU %": st.session_state.history["cpu"],
                "Memory %": st.session_state.history["memory"],
            }
            st.line_chart(chart_data)
    except Exception as e:
        st.error(f"Cannot reach API: {e}")

    time.sleep(2)
    st.rerun()

# ── Tab 2: Servers ─────────────────────────────────────────────────────────────
with tab2:

    @st.cache_data(ttl=5)
    def fetch_servers():
        try:
            return requests.get(f"{API_URL}/servers", timeout=3).json()
        except Exception:
            return []

    servers = fetch_servers()

    def color_status(val):
        colors = {"UP": "background-color: #d4edda", "DEGRADED": "background-color: #fff3cd", "DOWN": "background-color: #f8d7da"}
        return colors.get(val, "")

    if servers:
        import pandas as pd
        df = pd.DataFrame(servers)
        st.dataframe(df.style.applymap(color_status, subset=["status"]), use_container_width=True)
    else:
        st.info("No servers registered yet.")

    st.subheader("Register a server")
    with st.form("add_server"):
        name = st.text_input("Name")
        host = st.text_input("Host")
        port = st.number_input("Port", min_value=1, max_value=65535, value=8080)
        submitted = st.form_submit_button("Register")
        if submitted and name and host:
            r = requests.post(f"{API_URL}/servers", json={"name": name, "host": host, "port": port}, headers=HEADERS, timeout=3)
            if r.status_code == 201:
                st.success(f"Server '{name}' registered!")
                st.cache_data.clear()
            else:
                st.error(f"Error: {r.text}")

    if servers:
        st.subheader("Trigger health check")
        options = {f"{s['name']} (id={s['id']})": s["id"] for s in servers}
        selected = st.selectbox("Select server", list(options.keys()))
        if st.button("Check now"):
            sid = options[selected]
            r = requests.post(f"{API_URL}/servers/{sid}/check", timeout=10)
            if r.ok:
                result = r.json()
                st.success(f"Status: **{result['status']}**")
                st.cache_data.clear()
            else:
                st.error(f"Error: {r.text}")
