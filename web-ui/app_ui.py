import streamlit as st
import auth_state
from theme import apply_theme

# We must set page config first
st.set_page_config(page_title="Equity Trading System", page_icon="📈", layout="wide")

apply_theme()
auth_state.init_auth()

def home_page():
    st.markdown("<style>[data-testid='stSidebar'] {display: none;} [data-testid='collapsedControl'] {display: none;}</style>", unsafe_allow_html=True)
    from auth_pages import render_register_page
    st.title("📈 Equity Trading System", anchor=False)
    st.subheader("Welcome to the platform. Please register to continue.", anchor=False)
    render_register_page()

print(f"DEBUG: Auth Check - Current username: {auth_state.get_username()}")
st.markdown('<style>#stDecoration {display: none;}</style>', unsafe_allow_html=True)

p_home = st.Page(home_page, title="Register", icon="🏠", default=True)
p_login = st.Page("pages/login.py", title="Login", icon="🔑", url_path="login")

p_my_accounts = st.Page("pages/my_accounts.py", title="My Accounts", icon="👤")
p_create_acc = st.Page("pages/create_account.py", title="Open Account", icon="➕")
p_update_acc = st.Page("pages/update_account.py", title="Update Account", icon="✏️")

p_all_pos = st.Page("pages/all_positions.py", title="Positions", icon="📊")

p_all_trades = st.Page("pages/all_trades.py", title="Trades", icon="💸")
p_enter_trade = st.Page("pages/enter_trade.py", title="Enter Trade", icon="🛒")
p_mass_trade = st.Page("pages/mass_trade.py", title="Mass Trade", icon="🚀")
p_trade_id = st.Page("pages/trade_by_id.py", title="By ID", icon="🔍")
p_update_trade = st.Page("pages/update_trade.py", title="Update Trade", icon="✏️")

auth_pages = [
    p_my_accounts, p_create_acc, p_update_acc,
    p_all_pos,
    p_enter_trade, p_mass_trade, p_all_trades, p_trade_id, p_update_trade
]
all_pages = [p_home, p_login] + auth_pages

if auth_state.get_username():
    pg = st.navigation(auth_pages)
else:
    pg = st.navigation(all_pages, position="hidden")

auth_state.render_user_sidebar()

if "redirect_to" in st.session_state:
    redirect_page = st.session_state.pop("redirect_to")
    st.switch_page(redirect_page)

pg.run()
