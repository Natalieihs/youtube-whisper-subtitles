#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
为YouTube字幕生成器创建应用图标
设计理念：YouTube红色 + 字幕文本元素
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_app_icon():
    """创建应用图标（多尺寸）"""

    # 颜色定义
    # YouTube红色主题
    youtube_red = (255, 0, 0)
    dark_bg = (30, 30, 35)
    white = (255, 255, 255)
    light_gray = (240, 240, 240)
    subtitle_blue = (100, 200, 255)

    sizes = [1024, 512, 256, 128, 64, 32, 16]  # macOS需要的所有尺寸

    for size in sizes:
        # 创建图像
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # 计算尺寸参数
        padding = size // 10
        corner_radius = size // 8

        # 绘制圆角矩形背景（渐变效果用纯色代替）
        draw.rounded_rectangle(
            [(padding, padding), (size - padding, size - padding)],
            radius=corner_radius,
            fill=dark_bg
        )

        # 绘制YouTube播放按钮
        play_center_x = size // 2
        play_center_y = size // 2 - size // 8
        play_size = size // 4

        # YouTube风格的播放按钮（红色圆形）
        draw.ellipse(
            [play_center_x - play_size, play_center_y - play_size,
             play_center_x + play_size, play_center_y + play_size],
            fill=youtube_red
        )

        # 白色播放三角形
        triangle_offset = play_size // 6
        triangle_points = [
            (play_center_x - triangle_offset, play_center_y - play_size // 2),
            (play_center_x - triangle_offset, play_center_y + play_size // 2),
            (play_center_x + play_size // 2, play_center_y)
        ]
        draw.polygon(triangle_points, fill=white)

        # 绘制字幕线条（下方）
        subtitle_y_start = play_center_y + play_size * 2
        subtitle_height = size // 30
        subtitle_gap = size // 40

        # 三行字幕效果
        for i in range(3):
            y = subtitle_y_start + i * (subtitle_height + subtitle_gap)
            # 每行长度不同，模拟真实字幕
            widths = [0.7, 0.85, 0.6]
            width_ratio = widths[i]
            x1 = padding * 2
            x2 = size - padding * 2
            line_width = (x2 - x1) * width_ratio
            x_start = x1 + (x2 - x1 - line_width) / 2

            draw.rounded_rectangle(
                [(x_start, y), (x_start + line_width, y + subtitle_height)],
                radius=subtitle_height // 2,
                fill=subtitle_blue
            )

        # 保存PNG图像
        img.save(f'icon_{size}x{size}.png')
        print(f"✓ 生成 icon_{size}x{size}.png")

    # 创建iconset目录
    iconset_dir = 'AppIcon.iconset'
    os.makedirs(iconset_dir, exist_ok=True)

    # 复制文件到iconset目录（macOS图标规范）
    icon_mapping = {
        16: ['icon_16x16.png'],
        32: ['icon_16x16@2x.png', 'icon_32x32.png'],
        64: ['icon_32x32@2x.png'],
        128: ['icon_128x128.png'],
        256: ['icon_128x128@2x.png', 'icon_256x256.png'],
        512: ['icon_256x256@2x.png', 'icon_512x512.png'],
        1024: ['icon_512x512@2x.png']
    }

    for size, filenames in icon_mapping.items():
        src = f'icon_{size}x{size}.png'
        for dest in filenames:
            os.system(f'cp {src} {iconset_dir}/{dest}')

    print(f"\n✓ iconset目录创建完成: {iconset_dir}")
    print("✓ 所有图标文件已生成")

    return iconset_dir

def create_icns(iconset_dir):
    """将iconset转换为.icns文件"""
    print("\n正在生成 .icns 文件...")
    result = os.system(f'iconutil -c icns {iconset_dir} -o app_icon.icns')

    if result == 0:
        print("✓ app_icon.icns 生成成功！")
        return True
    else:
        print("✗ .icns 生成失败")
        return False

if __name__ == '__main__':
    print("========================================")
    print("  YouTube字幕生成器 - 图标生成工具")
    print("========================================")
    print("")

    iconset_dir = create_app_icon()
    create_icns(iconset_dir)

    print("\n========================================")
    print("图标生成完成！")
    print("文件: app_icon.icns")
    print("========================================")
