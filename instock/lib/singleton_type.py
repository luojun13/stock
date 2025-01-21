#!/usr/bin/env python3
# -*- coding: utf-8 -*-


from threading import RLock


__author__ = 'myh '
__date__ = '2023/3/10 '

# 定义了一个名为 singleton_type 的元类，用于实现单例模式。单例模式确保一个类只有一个实例，并提供一个全局访问点。
# singleton_type 继承自 type，表示它是一个元类
class singleton_type(type):
    # RLock 是线程锁的一种，允许多次获取锁，但必须由同一线程释放。这里使用 RLock 来确保在多线程环境下创建单例实
    # 例时的线程安全。
    single_lock = RLock()

    def __call__(cls, *args, **kwargs):  # 创建cls的对象时候调用
        # 使用 with 语句和 single_lock 来确保以下代码块在多线程环境下是线程安全的
        with singleton_type.single_lock:
            # 检查cls是否已经有一个名为 _instance 的属性，如果没有，则创建一个
            if not hasattr(cls, "_instance"):
                cls._instance = super(singleton_type, cls).__call__(*args, **kwargs)  # 创建cls的对象

        return cls._instance
