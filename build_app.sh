#!/bin/bash

# YouTube字幕生成器 - Mac应用打包脚本

# 切换到脚本所在目录
cd "$(dirname "$0")"

echo "========================================"
echo "  YouTube字幕生成器 - 应用打包"
echo "========================================"
echo ""

# 清理之前的构建
echo "清理之前的构建文件..."
rm -rf build dist *.spec

# 使用PyInstaller打包
echo "开始打包应用..."
python3 -m PyInstaller \
  --name="YouTube字幕生成器" \
  --windowed \
  --onedir \
  --icon=app_icon.icns \
  --osx-bundle-identifier=com.ytsubtitles.generator \
  --add-data="app_icon.icns:." \
  youtube_subtitle_generator.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✓ 应用打包成功！"
    echo ""
    echo "应用位置: dist/YouTube字幕生成器.app"
    echo ""

    # 显示应用信息
    ls -lh "dist/YouTube字幕生成器.app/Contents/MacOS/"

    echo ""
    echo "下一步："
    echo "1. 测试应用: open 'dist/YouTube字幕生成器.app'"
    echo "2. 安装到应用程序: cp -r 'dist/YouTube字幕生成器.app' /Applications/"
else
    echo ""
    echo "✗ 打包失败"
    exit 1
fi
