#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import numpy as np
import logging
# 首映 bokeh 画图。
from bokeh.plotting import figure
from bokeh.embed import components
from bokeh.palettes import Spectral11
from bokeh.layouts import column, row, layout
from bokeh.models import ColumnDataSource, HoverTool, CheckboxGroup, LabelSet, Button, CustomJS, \
    CDSView, BooleanFilter, TabPanel, Tabs, Div, Styles, CrosshairTool, Span, BoxSelectTool, WheelZoomTool, PanTool, \
    BoxZoomTool, ZoomInTool, ZoomOutTool, RedoTool, ResetTool, SaveTool, UndoTool
import instock.core.tablestructure as tbs
import instock.core.indicator.calculate_indicator as idr
import instock.core.pattern.pattern_recognitions as kpr
import instock.core.kline.indicator_web_dic as iwd

__author__ = 'myh '
__date__ = '2023/4/6 '

# 定义证券软件常用的颜色方案
STOCK_COLORS = [
    '#FFA500',  # 橙色 - 成交量
    '#87CEEB',  # 天蓝色 - 5日均量
    '#90EE90',  # 淡绿色 - 10日均量
    '#FF4500',  # 红橙色 - 主要指标
    '#4169E1',  # 皇家蓝 - 次要指标
    '#32CD32',  # 酸橙色 - 辅助指标
    '#FFD700',  # 金色
    '#9370DB',  # 中等紫色
    '#20B2AA',  # 浅海洋绿
    '#FF69B4',  # 热粉红
    '#CD5C5C'   # 印度红
]

# 计算文字高度（假设每个字符宽度约为9pt）
def calc_text_width(text, font_size=9):
    return len(text) * (font_size)*1.8  # default 9pt per character

# 计算新标签的y偏移量
def calc_y_offset(labels, new_label, base_offset, font_size=9, is_up=True):
    new_width = calc_text_width(new_label, font_size)
    if not labels:
        return base_offset
    
    # 累加之前标签的高度（加上一些间距）
    total_offset = base_offset
    for label in labels:
        if is_up:
            total_offset += calc_text_width(label, font_size) + 5  # 5pt为标签间距
        else:
            total_offset -= calc_text_width(label, font_size) + 5
    
    return total_offset

def get_plot_kline(code, stock, date, stock_name):
    plot_list = []
    threshold = 360
    font_size = 7
    try:
        data = idr.get_indicators(stock, date, threshold=threshold)
        if data is None:
            return None

        stock_column = tbs.STOCK_KLINE_PATTERN_DATA['columns']
        data = kpr.get_pattern_recognitions(data, stock_column)
        if data is None:
            return None

        length = len(data.index)
        data['index'] = list(np.arange(length))
        # 处理形态信息
        pattern_info = []
        for k in stock_column:
            label_cn = stock_column[k]['cn']
            # 上涨形态
            label_mask_u = (data[k] > 0)
            data.loc[label_mask_u, f'{k}_pattern'] = label_cn + '(↑)'
            # 下跌形态
            label_mask_d = (data[k] < 0)
            data.loc[label_mask_d, f'{k}_pattern'] = label_cn + '(↓)'
            pattern_info.append(f'{k}_pattern')
        
        # 合并所有形态信息到一个字段
        data['patterns'] = ''
        for pattern in pattern_info:
            data['patterns'] = data['patterns'] + data[pattern].fillna('') + ' '
        data['patterns'] = data['patterns'].str.strip()

        # 数据源
        source = ColumnDataSource(data)

        # 涨跌
        inc = data['close'] >= data['open']
        dec = data['open'] > data['close']
        inc_source = ColumnDataSource(data.loc[inc])
        dec_source = ColumnDataSource(data.loc[dec])

        # 工具条
        tools = pan, box_select, box_zoom, wheel_zoom, zoom_in, zoom_out, undo, redo, reset, save = \
            PanTool(description="平移"), BoxSelectTool(description="方框选取"), BoxZoomTool(description="方框缩放"), \
                WheelZoomTool(description="滚轮缩放"), ZoomInTool(description="放大"), ZoomOutTool(description="缩小"), \
                UndoTool(description="撤销"), RedoTool(description="重做"), ResetTool(description="重置"), \
                SaveTool(description="保存", filename=f"InStock_{code}({date})")
        # 悬停
        tooltips = [('日期', '@date'), ('开盘', '@open'),
                    ('最高', '@high'), ('最低', '@low'),
                    ('收盘', '@close'), ('涨跌', '@quote_change%'),
                    ('金额', '@amount{¥0}'), ('换手', '@turnover%'),('形态', '@patterns{safe}')]

        hover = HoverTool(tooltips=tooltips, description="悬停")

        # 十字瞄准线
        crosshair = CrosshairTool(overlay=[Span(dimension="width", line_dash="dashed", line_width=2),
                                           Span(dimension="height", line_dash="dotted", line_width=2)],
                                  description="十字瞄准线")
        # K线图
        p_kline = figure(width=1500, height=470, x_range=(0, length + 1), min_border_left=80,
                         tools=tools, toolbar_location='above')
        # 均线
        sam_labels = ("close", "ma10", "ma20", "ma50", "ma200")
        for name, color in zip(sam_labels, STOCK_COLORS):
            p_kline.line(x='index', y=name, source=source, legend_label=tbs.get_field_cn(name, tbs.STOCK_STATS_DATA),
                         color=color, line_width=1.5, alpha=0.8)
        p_kline.legend.location = "top_left"
        p_kline.legend.click_policy = "hide"

        # 股价柱
        p_kline.segment(x0='index', y0='high', x1='index', y1='low', color='red', source=inc_source)
        p_kline.segment(x0='index', y0='high', x1='index', y1='low', color='green', source=dec_source)
        p_kline.vbar('index', 0.5, 'open', 'close', fill_color='red', line_color='red', source=inc_source,
                     hover_fill_alpha=0.5)
        p_kline.vbar('index', 0.5, 'open', 'close', fill_color='green', line_color='green', source=dec_source,
                     hover_fill_alpha=0.5)
        p_kline.add_tools(hover, crosshair)

        # 形态信息
        pattern_is_show = True  # 形态缺省是否显示
        checkboxes_args = {}
        checkboxes_code = """let acts = cb_obj.active;"""
        pattern_labels = []
        i = 0
        # 创建位置跟踪字典，记录每个位置的标签和高度
        position_tracker = {idx: {'up_labels': [], 'down_labels': []} for idx in data.index}
        for k in stock_column:
            label_cn = stock_column[k]['cn']
            label_mask_u = (data[k] > 0)
            label_data_u = data.loc[label_mask_u].copy()
            isHas = False
            if len(label_data_u.index) > 0:
                # 更新上方标签位置
                for idx in label_data_u.index:
                    y_offset = calc_y_offset(
                        position_tracker[idx]['up_labels'],
                        label_cn,
                        5,  # 基础上偏移
                        font_size,
                        True
                    )
                    label_data_u.loc[idx, 'y_offset'] = y_offset
                    position_tracker[idx]['up_labels'].append(label_cn)
                
                label_data_u.loc[:, 'label_cn'] = label_cn
                label_source_u = ColumnDataSource(label_data_u)
                locals()[f'pattern_labels_u_{str(i)}'] = LabelSet(x='index', y='high', text="label_cn",
                                                                source=label_source_u, x_offset=7, y_offset='y_offset',
                                                                angle=90, angle_units='deg', text_color='red',
                                                                text_font_style='bold', text_font_size="9pt",
                                                                visible=pattern_is_show)
                p_kline.add_layout(locals()[f'pattern_labels_u_{str(i)}'])
                checkboxes_args[f'lsu{str(i)}'] = locals()[f'pattern_labels_u_{str(i)}']
                checkboxes_code = f"{checkboxes_code}lsu{i}.visible = acts.includes({i});"
                pattern_labels.append(label_cn)
                isHas = True
                
            label_mask_d = (data[k] < 0)
            label_data_d = data.loc[label_mask_d].copy()
            if len(label_data_d.index) > 0:
                # 更新下方标签位置
                for idx in label_data_d.index:
                    y_offset = calc_y_offset(
                        position_tracker[idx]['down_labels'],
                        label_cn,
                        -5,  # 基础下偏移
                        font_size,
                        False
                    )
                    label_data_d.loc[idx, 'y_offset'] = y_offset
                    position_tracker[idx]['down_labels'].append(label_cn)
                
                label_data_d.loc[:, 'label_cn'] = label_cn
                label_source_d = ColumnDataSource(label_data_d)
                locals()[f'pattern_labels_d_{str(i)}'] = LabelSet(x='index', y='low', text='label_cn',
                                                                source=label_source_d, x_offset=-7, y_offset='y_offset',
                                                                angle=270, angle_units='deg',
                                                                text_color='green',
                                                                text_font_style='bold', text_font_size="9pt",
                                                                visible=pattern_is_show)
                p_kline.add_layout(locals()[f'pattern_labels_d_{str(i)}'])
                checkboxes_args[f'lsd{str(i)}'] = locals()[f'pattern_labels_d_{str(i)}']
                checkboxes_code = f"{checkboxes_code}lsd{i}.visible = acts.includes({i});"
                if not isHas:
                    pattern_labels.append(label_cn)
                    isHas = True
                
            if isHas:
                i += 1
        p_kline.xaxis.visible = False
        p_kline.min_border_bottom = 0

        # 交易量柱
        p_volume = figure(width=p_kline.width, height=120, x_range=p_kline.x_range,
                          min_border_left=p_kline.min_border_left, tools=tools, toolbar_location=None)
        vol_labels = ("vol_5", "vol_10")
        for name, color in zip(vol_labels, Spectral11):
            p_volume.line(x=data['index'], y=data[name], legend_label=name, color=color, line_width=1.5, alpha=0.8)
        p_volume.legend.location = "top_left"
        p_volume.legend.click_policy = "hide"
        p_volume.vbar('index', 0.5, 0, 'volume', color='red', source=inc_source)
        p_volume.vbar('index', 0.5, 0, 'volume', color='green', source=dec_source)
        p_volume.add_tools(crosshair)
        p_volume.xaxis.major_label_overrides = {i: date for i, date in enumerate(data['date'])}
        # p_volume.xaxis.major_label_orientation = pi / 4

        # 形态复选框
        pattern_checkboxes = CheckboxGroup(labels=pattern_labels,
                                           active=list(range(len(pattern_labels))) if pattern_is_show else [])
        # pattern_checkboxes.inline = True
        pattern_checkboxes.height = p_kline.height + p_volume.height
        if checkboxes_args:
            pattern_checkboxes.js_on_change('active', CustomJS(args=checkboxes_args, code=checkboxes_code))
        ck = column(row(pattern_checkboxes))

        # 按钮
        select_all = Button(label="全选")
        select_none = Button(label='全弃')
        select_all.js_on_event("button_click", CustomJS(args={'pcs': pattern_checkboxes, 'pls': pattern_labels},
                                                        code="pcs.active = Array.from(pls, (x, i) => i);"))
        select_none.js_on_event("button_click", CustomJS(args={'pcs': pattern_checkboxes},
                                                         code="pcs.active = [];"))

        # 指标
        tabs = []
        for conf in iwd.indicators_dic:
            p_indicator = figure(width=p_kline.width, height=150, x_range=p_kline.x_range,
                                 min_border_left=p_kline.min_border_left, tools=tools, toolbar_location=None)
            for name, color in zip(conf["dic"], STOCK_COLORS):
                if name == 'macdh' or name == 'ppoh':
                    up = [True if val > 0 else False for val in source.data[name]]
                    down = [True if val < 0 else False for val in source.data[name]]
                    view_upper = CDSView(filter=BooleanFilter(up))
                    view_lower = CDSView(filter=BooleanFilter(down))
                    p_indicator.vbar('index', 0.1, 0, name, legend_label=tbs.get_field_cn(name, tbs.STOCK_STATS_DATA),
                                     color='green', source=source, view=view_lower)
                    p_indicator.vbar('index', 0.1, name, 0, legend_label=tbs.get_field_cn(name, tbs.STOCK_STATS_DATA),
                                     color='red', source=source, view=view_upper)
                else:
                    p_indicator.line(x='index', y=name, legend_label=tbs.get_field_cn(name, tbs.STOCK_STATS_DATA),
                                     color=color, source=source, line_width=1.5, alpha=0.8)
            p_indicator.legend.location = "top_left"
            p_indicator.legend.click_policy = "hide"
            p_indicator.add_tools(crosshair)
            p_indicator.xaxis.visible = False
            p_indicator.min_border_bottom = 0
            div_indicator = Div(text=f"""★★★★★指标详细解读：{conf["desc"]}""", width=p_kline.width)
            tabs.append(TabPanel(child=column(p_indicator, row(div_indicator)), title=conf["title"]))
        tabs_indicators = Tabs(tabs=tabs, tabs_location='below', width=p_kline.width, stylesheets=[
            {'.bk-tab': Styles(padding='1px 1.4px', font_size='xx-small'),
             '.bk-tab.bk-active': Styles(background_color='yellow', color='red')}])

        # 关注
        if code.startswith(('1', '5')):
            div_attention = Div()
        else:
            import instock.lib.database as mdb
            table_name = tbs.TABLE_CN_STOCK_ATTENTION['name']
            _sql = f"SELECT EXISTS(SELECT 1 FROM `{table_name}` WHERE `code` = '{code}')"
            try:
                rc = mdb.executeSqlCount(_sql)
            except Exception as e:
                rc = 0
            if rc == 0:
                cvalue = "0"
                cname = "关注"
            else:
                cvalue = "1"
                cname = "取关"
            div_attention = Div(
                text=f"""<button id="attentionId" value="{cvalue}" onclick="attention('{code}',this);return false;">{cname}</button>""",
                width=47)

        # 东方财富股票页面
        if code.startswith("6"):
            code_name = f"SH{code}"
        else:
            code_name = f"SZ{code}"
        div_dfcf_hq = Div(
            text=f"""<a href="https://quote.eastmoney.com/{code_name}.html" target="_blank">{code}{stock_name}行情</a>""",
            width=150)
        if code.startswith(('1', '5')):
            div_dfcf_zl = Div()
        else:
            div_dfcf_zl = Div(
                text=f"""<a href="https://emweb.eastmoney.com/PC_HSF10/OperationsRequired/Index?code={code_name}" target="_blank">资料</a>""",
                width=40)
        div_dfcf_pr = Div(
            text=f"""<a href="https://www.ljjyy.com/archives/2023/04/100718.html" target="_blank">形态</a>""",
            width=40)

        # 组合图
        layouts = layout(row(
            column(
                row(children=[div_attention, div_dfcf_hq, div_dfcf_zl, div_dfcf_pr, select_all, select_none],
                    align='end'),
                p_kline,
                p_volume, tabs_indicators), ck))
        script, div = components(layouts)

        return {"script": script, "div": div}
    except Exception as e:
        logging.error(f"visualization.get_plot_kline处理异常：{e}")
    return None
