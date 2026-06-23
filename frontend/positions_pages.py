import streamlit as st

from api_client import (
    get_all_positions,
    get_positions_by_account,
    get_positions_by_ticker,
    get_positions_by_account_and_ticker,
)
from account_picker import account_select


def _render_positions_result(result, empty_message="No positions found."):
    if result["status"] == "success":
        if result["data"]:
            st.json(result["data"])
        else:
            st.info(empty_message)
    else:
        st.error(result["message"])


@st.fragment(run_every="15s")
def _all_positions_fragment():
    _render_positions_result(
        get_all_positions(),
        empty_message="No positions yet. Book a trade to see positions here.",
    )


def render_all_positions_page():
    st.header("📊 All Positions")
    st.caption("GET /positions")
    # Loads immediately and keeps polling -- no button needed.
    _all_positions_fragment()


@st.fragment(run_every="15s")
def _positions_by_account_fragment(account_id):
    _render_positions_result(get_positions_by_account(account_id))


def render_positions_by_account_page():
    st.header("📊 Positions by Account")
    st.caption("GET /positions/accounts/{account_id}")

    prefilled = st.session_state.pop("jump_to_account", None)
    account_id = account_select(preselect_account_id=prefilled)

    # Auto-loads (and keeps polling) as soon as an account is selected --
    # including immediately after jumping here from My Accounts.
    if account_id:
        _positions_by_account_fragment(account_id)


@st.fragment(run_every="15s")
def _positions_by_ticker_fragment(ticker):
    _render_positions_result(get_positions_by_ticker(ticker))


def render_positions_by_ticker_page():
    st.header("📊 Positions by Ticker")
    st.caption("GET /positions/ticker/{ticker}")

    ticker = st.text_input("Ticker", "AAPL")

    if ticker:
        _positions_by_ticker_fragment(ticker.upper())


@st.fragment(run_every="15s")
def _positions_by_account_and_ticker_fragment(account_id, ticker):
    _render_positions_result(get_positions_by_account_and_ticker(account_id, ticker))


def render_positions_by_account_and_ticker_page():
    st.header("📊 Positions by Account & Ticker")
    st.caption("GET /positions/accounts/{account_id}/ticker/{ticker}")

    account_id = account_select(key="pos_acct_ticker_select")
    ticker = st.text_input("Ticker", "AAPL")

    if account_id and ticker:
        _positions_by_account_and_ticker_fragment(account_id, ticker.upper())