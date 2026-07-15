import json
import os
import urllib.parse

import streamlit as st
from streamlit_cookies_controller import CookieController

# Only mark cookies Secure once the app is actually served over HTTPS --
# the streamlit ingress is plain HTTP today (see k8s/manifests/base/apps/
# streamlit/ingress.yaml), and a Secure cookie is silently dropped by the
# browser over HTTP, which would break "stay logged in on reload". Flip
# this on via env var once TLS is in front of streamlit, no code change
# needed.
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "false").lower() == "true"

def _get_cookie_controller():
    if "cookie_controller" not in st.session_state:
        st.session_state.cookie_controller = CookieController()
    return st.session_state.cookie_controller

def get_session_cookie():
    return st.session_state.get("saved_session_cookie")

def get_username():
    return st.session_state.get("username")

def remember_login(username, session_cookie):
    controller = _get_cookie_controller()
    controller.set("eq_username", username, path="/", secure=COOKIE_SECURE, same_site="strict")
    controller.set("eq_session", session_cookie, path="/", secure=COOKIE_SECURE, same_site="strict")
    st.session_state.username = username
    st.session_state.saved_session_cookie = session_cookie
    st.session_state.session_validated = True

def forget_login():
    controller = _get_cookie_controller()
    try:
        controller.remove("eq_username", secure=COOKIE_SECURE, same_site="strict")
    except KeyError:
        pass
    try:
        controller.remove("eq_session", secure=COOKIE_SECURE, same_site="strict")
    except KeyError:
        pass
    st.session_state.username = None
    st.session_state.saved_session_cookie = None
    st.session_state.session_validated = False


def _decode_cookie(val):
    if not val: return val
    try:
        val = urllib.parse.unquote(val)
        if val.startswith('"') and val.endswith('"'):
            val = json.loads(val)
    except Exception:
        pass
    return val

def init_auth():
    # st.context.cookies reads straight from the incoming HTTP request
    # headers -- it's synchronous and always correct on the very first
    # script run of a fresh session. CookieController is a JS-backed
    # custom component: on a fresh session it returns its default ({})
    # until a round-trip to the browser completes, which needs an extra
    # rerun. Relying on that as a read fallback made the restored-login
    # state (and therefore which page/layout renders) flicker across
    # reruns on a hard reload. Reading is only ever needed from
    # st.context.cookies; CookieController is still needed for writes
    # (remember_login/forget_login), since that's the only way Python
    # can hand a value to the browser's document.cookie.
    cookie_user = _decode_cookie(st.context.cookies.get("eq_username"))
    cookie_session = _decode_cookie(st.context.cookies.get("eq_session"))

    if st.session_state.get("username") is None and cookie_user:
        st.session_state.username = cookie_user
        st.session_state.saved_session_cookie = cookie_session
        st.session_state.session_validated = False

    # If we have cookies but haven't validated the session in this streamlit instance yet
    if get_session_cookie() and get_username():
        if not st.session_state.get("session_validated"):
            from api_client import get_user_accounts
            
            # An actual invalid/expired token is already handled inside
            # get_user_accounts() -> _api_error(), which calls
            # forget_login() and redirects on a real 401. So a non-success
            # result here only ever means "couldn't confirm the session
            # right now" (backend restarting, a network blip, etc.) --
            # NOT "the session is invalid". Don't log the user out for
            # that; just leave the cookies alone and retry on the next
            # rerun.
            res = get_user_accounts()
            
            if res.get("status") == "success":
                st.session_state.session_validated = True
    else:
        st.session_state.username = None
        st.session_state.saved_session_cookie = None

def render_user_sidebar():
    username = get_username()
    if username:
        st.sidebar.markdown(f"👤 **{username}**")
        st.sidebar.divider()
        if st.sidebar.button("🚪 Log Out", use_container_width=True):
            from api_client import logout
            logout()
            forget_login()
            st.session_state.redirect_to = "pages/login.py"
            st.rerun()

def require_auth():
    if not get_username():
        st.switch_page("pages/login.py")
