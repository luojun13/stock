#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import datetime
from instock.core.singleton_trade_date import stock_trade_date

__author__ = 'myh '
__date__ = '2023/4/10 '


def is_trade_date(date=None):
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return False
    if date in trade_date:
        return True
    else:
        return False


def get_previous_trade_date(date):
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return date
    tmp_date = date
    while True:
        tmp_date += datetime.timedelta(days=-1)
        if tmp_date in trade_date:
            break
    return tmp_date


def get_next_trade_date(date):
    trade_date = stock_trade_date().get_data()
    if trade_date is None:
        return date
    tmp_date = date
    while True:
        tmp_date += datetime.timedelta(days=1)
        if tmp_date in trade_date:
            break
    return tmp_date


OPEN_TIME = (
    (datetime.time(9, 15, 0), datetime.time(11, 30, 0)),
    (datetime.time(13, 0, 0), datetime.time(15, 0, 0)),
)


def is_tradetime(now_time):
    now = now_time.time()
    for begin, end in OPEN_TIME:
        if begin <= now < end:
            return True
    else:
        return False


PAUSE_TIME = (
    (datetime.time(11, 30, 0), datetime.time(12, 59, 30)),
)


def is_pause(now_time):
    now = now_time.time()
    for b, e in PAUSE_TIME:
        if b <= now < e:
            return True


CONTINUE_TIME = (
    (datetime.time(12, 59, 30), datetime.time(13, 0, 0)),
)


def is_continue(now_time):
    now = now_time.time()
    for b, e in CONTINUE_TIME:
        if b <= now < e:
            return True
    return False


CLOSE_TIME = (
    datetime.time(15, 0, 0),
)


def is_closing(now_time, start=datetime.time(14, 54, 30)):
    now = now_time.time()
    for close in CLOSE_TIME:
        if start <= now < close:
            return True
    return False


def is_close(now_time):
    now = now_time.time()
    for close in CLOSE_TIME:
        if now >= close:
            return True
    return False


def is_open(now_time):
    now = now_time.time()
    if now >= datetime.time(9, 30, 0):
        return True
    return False


def get_trade_hist_interval(date):
    """
    获取股票历史数据的时间区间，默认获取3年前的数据
    输入：date，格式为"%Y-%m-%d"
    返回值：date_start, is_not_in_trade
    """
    tmp_year, tmp_month, tmp_day = date.split("-")
    date_end = datetime.datetime(int(tmp_year), int(tmp_month), int(tmp_day))
    date_start = (date_end + datetime.timedelta(days=-(365 * 3))).strftime("%Y%m%d")

    now_time = datetime.datetime.now()
    now_date = now_time.date()
    is_trade_date_open_close_between = False
    if date_end.date() == now_date:
        if is_trade_date(now_date):
            # 当前日期是交易日
            if is_open(now_time) and not is_close(now_time):
                # 当前日期是交易日且交易中
                is_trade_date_open_close_between = True

    return date_start, not is_trade_date_open_close_between
    
def get_trade_date_last():
    """
    根据当前时间获取最近的交易日，收盘后返回当日，未收盘时返回上一个交易日
    返回值：run_date, run_date_nph 当前时间非交易日时，都为上一个交易日；为交易日已收盘时，都为当日；
           为交易日未开盘时，都为上一个交易日；为交易日交易中时，run_date为上一个交易日，run_date_nph为当日    
    """
    now_time = datetime.datetime.now()
    run_date = now_time.date()
    run_date_nph = run_date
    if is_trade_date(run_date):
        # 交易日
        if not is_close(now_time):
            # 未收盘，获取上一个交易日
            run_date = get_previous_trade_date(run_date)
            if not is_open(now_time):
                # 未开盘
                run_date_nph = run_date
        # 收盘，当日
    else:
        # 非交易日，获取上一个交易日
        run_date = get_previous_trade_date(run_date)
        run_date_nph = run_date
    return run_date, run_date_nph


def get_quarterly_report_date():
    now_time = datetime.datetime.now()
    year = now_time.year
    month = now_time.month
    if 1 <= month <= 3:
        month_day = '1231'
    elif 4 <= month <= 6:
        month_day = '0331'
    elif 7 <= month <= 9:
        month_day = '0630'
    else:
        month_day = '0930'
    return f"{year}{month_day}"


def get_bonus_report_date():
    now_time = datetime.datetime.now()
    year = now_time.year
    month = now_time.month
    if 2 <= month <= 6:
        year -= 1
        month_day = '1231'
    elif 8 <= month <= 12:
        month_day = '0630'
    elif month == 7:
        if now_time.day > 25:
            month_day = '0630'
        else:
            year -= 1
            month_day = '1231'
    else:
        year -= 1
        if now_time.day > 25:
            month_day = '1231'
        else:
            month_day = '0630'
    return f"{year}{month_day}"
