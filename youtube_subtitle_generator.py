#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube 字幕生成器
功能：
1. 从YouTube下载视频并转换为MP3
2. 使用whisper.cpp自动生成中文字幕
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
import re
import shutil
from pathlib import Path
from datetime import datetime
import queue

def find_executable(name):
    """查找可执行文件的完整路径"""
    # 首先尝试使用 shutil.which
    path = shutil.which(name)
    if path:
        return path

    # 如果失败，尝试常见路径
    common_paths = [
        f'/usr/local/bin/{name}',
        f'/opt/homebrew/bin/{name}',
        f'/usr/bin/{name}',
        f'/bin/{name}',
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    # 如果都失败，返回名称本身（让系统尝试）
    return name

class YouTubeSubtitleGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 字幕生成器")
        self.root.geometry("1000x750")

        # 设置主题颜色
        self.colors = {
            'bg': '#f0f0f5',
            'primary': '#FF0000',  # YouTube红色
            'secondary': '#64C8FF',  # 字幕蓝色
            'success': '#10B981',
            'warning': '#F59E0B',
            'error': '#EF4444',
            'text': '#1F2937',
            'text_light': '#6B7280',
            'white': '#FFFFFF',
            'border': '#E5E7EB'
        }

        self.root.configure(bg=self.colors['bg'])

        # 默认配置
        self.output_dir = str(Path.home() / "Downloads" / "AWS课程")
        self.cookies_file = str(Path.home() / "Downloads" / "youtube.txt")
        self.whisper_bin = "/tmp/whisper.cpp/build/bin/whisper-cli"
        self.whisper_model = "/tmp/whisper.cpp/models/ggml-base-q5_1.bin"

        # 消息队列，用于线程间通信
        self.message_queue = queue.Queue()

        # 设置样式
        self.setup_styles()
        self.setup_ui()

        # 启动消息处理
        self.process_messages()

    def setup_styles(self):
        """设置ttk样式"""
        style = ttk.Style()

        # 使用默认主题并自定义
        style.theme_use('default')

        # 配置TFrame样式
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame', background=self.colors['white'], relief='flat')

        # 配置TLabel样式
        style.configure('TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 11))
        style.configure('Title.TLabel',
                       font=('SF Pro Display', 24, 'bold'),
                       foreground=self.colors['primary'])
        style.configure('Card.TLabel',
                       background=self.colors['white'])

        # 配置TButton样式
        style.configure('Primary.TButton',
                       font=('SF Pro Display', 12, 'bold'),
                       padding=10)
        style.map('Primary.TButton',
                 foreground=[('active', self.colors['white'])],
                 background=[('active', '#CC0000')])

        # 配置TEntry样式
        style.configure('TEntry',
                       fieldbackground=self.colors['white'],
                       foreground=self.colors['text'],
                       padding=8)

        # 配置TCheckbutton样式
        style.configure('TCheckbutton',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('SF Pro Display', 11))
        style.configure('Card.TCheckbutton',
                       background=self.colors['white'])

    def process_messages(self):
        """处理来自工作线程的消息"""
        try:
            while True:
                msg_type, msg_data = self.message_queue.get_nowait()
                if msg_type == 'log':
                    self._do_log(msg_data)
                elif msg_type == 'status':
                    self._do_update_status(msg_data['text'], msg_data['color'])
                elif msg_type == 'progress_start':
                    self.progress.start()
                elif msg_type == 'progress_stop':
                    self.progress.stop()
                elif msg_type == 'button_state':
                    if msg_data['button'] == 'start':
                        self.start_button.config(state=msg_data['state'])
                    elif msg_data['button'] == 'stop':
                        self.stop_button.config(state=msg_data['state'])
                elif msg_type == 'messagebox':
                    messagebox.showinfo(msg_data['title'], msg_data['message'])
        except queue.Empty:
            pass

        # 每100ms检查一次队列
        self.root.after(100, self.process_messages)

    def setup_ui(self):
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title_label = ttk.Label(main_frame, text="YouTube 字幕生成器",
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=10)

        # URL输入区域
        url_frame = ttk.LabelFrame(main_frame, text="YouTube URL", padding="10")
        url_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(url_frame, text="视频URL:").grid(row=0, column=0, sticky=tk.W)
        self.url_entry = ttk.Entry(url_frame, width=70)
        self.url_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)

        # 批量URL输入
        ttk.Label(url_frame, text="批量URL\n(每行一个):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.url_text = scrolledtext.ScrolledText(url_frame, width=70, height=5)
        self.url_text.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # 配置区域
        config_frame = ttk.LabelFrame(main_frame, text="配置选项", padding="10")
        config_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # 输出目录
        ttk.Label(config_frame, text="输出目录:").grid(row=0, column=0, sticky=tk.W)
        self.output_dir_entry = ttk.Entry(config_frame, width=50)
        self.output_dir_entry.insert(0, self.output_dir)
        self.output_dir_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        ttk.Button(config_frame, text="浏览", command=self.browse_output_dir).grid(row=0, column=2)

        # Cookies文件
        ttk.Label(config_frame, text="Cookies文件:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.cookies_entry = ttk.Entry(config_frame, width=50)
        self.cookies_entry.insert(0, self.cookies_file)
        self.cookies_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(config_frame, text="浏览", command=self.browse_cookies).grid(row=1, column=2, pady=5)

        # 使用cookies选项
        self.use_cookies_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_frame, text="使用Cookies（需要登录YouTube才能下载某些视频）",
                       variable=self.use_cookies_var).grid(row=2, column=0, columnspan=3, sticky=tk.W)

        # Whisper配置
        ttk.Label(config_frame, text="Whisper路径:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.whisper_bin_entry = ttk.Entry(config_frame, width=50)
        self.whisper_bin_entry.insert(0, self.whisper_bin)
        self.whisper_bin_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        ttk.Label(config_frame, text="Whisper模型:").grid(row=4, column=0, sticky=tk.W, pady=5)
        self.whisper_model_entry = ttk.Entry(config_frame, width=50)
        self.whisper_model_entry.insert(0, self.whisper_model)
        self.whisper_model_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)

        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        self.start_button = ttk.Button(button_frame, text="开始处理",
                                       command=self.start_processing, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=5)

        ttk.Button(button_frame, text="处理本地MP3",
                  command=self.process_local_mp3, style="Accent.TButton").grid(row=0, column=1, padx=5)

        self.stop_button = ttk.Button(button_frame, text="停止",
                                      command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=2, padx=5)

        ttk.Button(button_frame, text="清空日志",
                  command=self.clear_log).grid(row=0, column=3, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=5)

        # 状态标签
        self.status_label = ttk.Label(main_frame, text="就绪", foreground="green")
        self.status_label.grid(row=5, column=0, columnspan=3, sticky=tk.W)

        # 日志区域
        log_frame = ttk.LabelFrame(main_frame, text="处理日志", padding="10")
        log_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)

        self.log_text = scrolledtext.ScrolledText(log_frame, width=80, height=15,
                                                  state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(6, weight=1)
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.processing = False
        self.process = None

    def browse_output_dir(self):
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def browse_cookies(self):
        filename = filedialog.askopenfilename(
            title="选择Cookies文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.cookies_entry.delete(0, tk.END)
            self.cookies_entry.insert(0, filename)

    def log(self, message):
        """添加日志消息(线程安全)"""
        self.message_queue.put(('log', message))

    def _do_log(self, message):
        """实际执行日志添加(仅在主线程)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, message, color="black"):
        """更新状态标签(线程安全)"""
        self.message_queue.put(('status', {'text': message, 'color': color}))

    def _do_update_status(self, text, color):
        """实际更新状态(仅在主线程)"""
        self.status_label.config(text=text, foreground=color)

    def process_local_mp3(self):
        """处理本地MP3文件"""
        # 让用户选择包含MP3文件的文件夹
        root_directory = filedialog.askdirectory(title="选择包含MP3文件的文件夹")
        if not root_directory:
            return

        # 获取所有子文件夹（包括当前文件夹）
        root_path = Path(root_directory)
        subdirs = [root_path] + [d for d in root_path.rglob("*") if d.is_dir()]

        # 筛选包含MP3文件的文件夹
        folders_with_mp3 = []
        for folder in subdirs:
            mp3_count = len(list(folder.glob("*.mp3")))
            if mp3_count > 0:
                folders_with_mp3.append((folder, mp3_count))

        if not folders_with_mp3:
            messagebox.showwarning("警告", f"在 {root_directory} 及其子文件夹中没有找到MP3文件")
            return

        # 显示文件夹选择对话框
        selected_folders = self.show_folder_selection_dialog(root_directory, folders_with_mp3)
        if not selected_folders:
            return

        # 验证配置
        whisper_bin = self.whisper_bin_entry.get().strip()
        if not os.path.exists(whisper_bin):
            messagebox.showwarning("警告", f"Whisper程序不存在: {whisper_bin}")
            return

        whisper_model = self.whisper_model_entry.get().strip()
        if not os.path.exists(whisper_model):
            messagebox.showwarning("警告", f"Whisper模型不存在: {whisper_model}")
            return

        # 收集选中文件夹中的所有MP3文件
        mp3_files = []
        for folder in selected_folders:
            mp3_files.extend(list(folder.glob("*.mp3")))

        self.log(f"从 {len(selected_folders)} 个文件夹中找到 {len(mp3_files)} 个MP3文件")

        # 开始处理
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()

        # 在新线程中处理
        thread = threading.Thread(target=self.process_local_mp3_files, args=(mp3_files, whisper_bin, whisper_model))
        thread.daemon = True
        thread.start()

    def show_folder_selection_dialog(self, root_dir, folders_with_mp3):
        """显示文件夹选择对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title("选择要处理的文件夹")
        dialog.geometry("600x400")

        # 说明文字
        ttk.Label(dialog, text=f"在 {root_dir} 中找到以下包含MP3的文件夹：",
                 font=("Arial", 12, "bold")).pack(pady=10)

        # 创建滚动框
        frame = ttk.Frame(dialog)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        scrollbar = ttk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        canvas = tk.Canvas(frame, yscrollcommand=scrollbar.set)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=canvas.yview)

        inner_frame = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner_frame, anchor='nw')

        # 存储复选框变量
        checkbox_vars = []
        root_path = Path(root_dir)

        for folder, mp3_count in folders_with_mp3:
            var = tk.BooleanVar(value=True)  # 默认全选
            checkbox_vars.append((var, folder))

            # 计算相对路径显示
            try:
                relative_path = folder.relative_to(root_path)
                display_text = f"{relative_path}  ({mp3_count} 个MP3)"
            except ValueError:
                display_text = f"{folder.name}  ({mp3_count} 个MP3)"

            ttk.Checkbutton(inner_frame, text=display_text, variable=var).pack(anchor='w', pady=2)

        inner_frame.update_idletasks()
        canvas.config(scrollregion=canvas.bbox("all"))

        # 按钮区域
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        selected_folders = []

        def on_confirm():
            selected_folders.extend([folder for var, folder in checkbox_vars if var.get()])
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        def select_all():
            for var, _ in checkbox_vars:
                var.set(True)

        def deselect_all():
            for var, _ in checkbox_vars:
                var.set(False)

        ttk.Button(button_frame, text="全选", command=select_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="全不选", command=deselect_all).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="确定", command=on_confirm, style="Accent.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="取消", command=on_cancel).pack(side=tk.LEFT, padx=5)

        # 等待对话框关闭
        dialog.transient(self.root)
        dialog.grab_set()
        self.root.wait_window(dialog)

        return selected_folders

    def process_local_mp3_files(self, mp3_files, whisper_bin, whisper_model):
        """批量处理本地MP3文件"""
        total = len(mp3_files)
        success_count = 0

        for idx, mp3_file in enumerate(mp3_files, 1):
            if not self.processing:
                break

            mp3_path = str(mp3_file)
            self.update_status(f"处理 {idx}/{total}: {mp3_file.name}", "blue")
            self.log(f"\n{'='*60}")
            self.log(f"处理第 {idx}/{total} 个文件: {mp3_file.name}")

            try:
                # 生成字幕
                self.log("生成字幕...")
                srt_file = self.generate_subtitle(mp3_path, whisper_bin, whisper_model)

                if srt_file:
                    self.log(f"✓ 字幕生成完成: {os.path.basename(srt_file)}")
                    success_count += 1
                else:
                    self.log("✗ 字幕生成失败")

            except Exception as e:
                self.log(f"✗ 处理失败: {str(e)}")

        # 完成
        self.message_queue.put(('progress_stop', None))
        self.message_queue.put(('button_state', {'button': 'start', 'state': tk.NORMAL}))
        self.message_queue.put(('button_state', {'button': 'stop', 'state': tk.DISABLED}))

        if self.processing:
            self.update_status(f"完成！成功: {success_count}/{total}", "green")
            self.log(f"\n{'='*60}")
            self.log(f"全部完成！成功处理 {success_count}/{total} 个文件")
            self.message_queue.put(('messagebox', {'title': '完成', 'message': f"成功处理 {success_count}/{total} 个MP3文件"}))

    def start_processing(self):
        """开始处理"""
        # 获取URL列表
        urls = []
        single_url = self.url_entry.get().strip()
        if single_url:
            urls.append(single_url)

        batch_urls = self.url_text.get("1.0", tk.END).strip().split("\n")
        for url in batch_urls:
            url = url.strip()
            if url and url not in urls:
                urls.append(url)

        if not urls:
            messagebox.showwarning("警告", "请输入至少一个YouTube URL")
            return

        # 验证配置
        output_dir = self.output_dir_entry.get().strip()
        if not output_dir:
            messagebox.showwarning("警告", "请选择输出目录")
            return

        whisper_bin = self.whisper_bin_entry.get().strip()
        if not os.path.exists(whisper_bin):
            messagebox.showwarning("警告", f"Whisper程序不存在: {whisper_bin}")
            return

        whisper_model = self.whisper_model_entry.get().strip()
        if not os.path.exists(whisper_model):
            messagebox.showwarning("警告", f"Whisper模型不存在: {whisper_model}")
            return

        # 开始处理 - 直接操作UI（这是在主线程中）
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()

        # 在新线程中处理
        thread = threading.Thread(target=self.process_urls, args=(urls,))
        thread.daemon = True
        thread.start()

    def stop_processing(self):
        """停止处理 - 这是在主线程中调用的"""
        self.processing = False
        if self.process:
            self.process.terminate()
        self.update_status("已停止", "red")
        self.log("用户停止了处理")
        # 直接操作UI（这是在主线程中）
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)
        self.progress.stop()

    def process_urls(self, urls):
        """处理URL列表"""
        output_dir = self.output_dir_entry.get().strip()
        cookies_file = self.cookies_entry.get().strip()
        use_cookies = self.use_cookies_var.get()
        whisper_bin = self.whisper_bin_entry.get().strip()
        whisper_model = self.whisper_model_entry.get().strip()

        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)

        total = len(urls)
        success_count = 0

        for idx, url in enumerate(urls, 1):
            if not self.processing:
                break

            self.update_status(f"处理 {idx}/{total}: {url}", "blue")
            self.log(f"\n{'='*60}")
            self.log(f"处理第 {idx}/{total} 个视频: {url}")

            try:
                # 步骤1: 下载MP3
                self.log("步骤1: 下载音频...")
                mp3_file = self.download_audio(url, output_dir, cookies_file, use_cookies)

                if not mp3_file or not self.processing:
                    continue

                self.log(f"✓ 下载完成: {os.path.basename(mp3_file)}")

                # 步骤2: 生成字幕
                self.log("步骤2: 生成字幕...")
                srt_file = self.generate_subtitle(mp3_file, whisper_bin, whisper_model)

                if srt_file:
                    self.log(f"✓ 字幕生成完成: {os.path.basename(srt_file)}")
                    success_count += 1
                else:
                    self.log("✗ 字幕生成失败")

            except Exception as e:
                self.log(f"✗ 处理失败: {str(e)}")

        # 完成
        self.message_queue.put(('progress_stop', None))
        self.message_queue.put(('button_state', {'button': 'start', 'state': tk.NORMAL}))
        self.message_queue.put(('button_state', {'button': 'stop', 'state': tk.DISABLED}))

        if self.processing:
            self.update_status(f"完成！成功: {success_count}/{total}", "green")
            self.log(f"\n{'='*60}")
            self.log(f"全部完成！成功处理 {success_count}/{total} 个视频")
            self.message_queue.put(('messagebox', {'title': '完成', 'message': f"成功处理 {success_count}/{total} 个视频"}))

    def download_audio(self, url, output_dir, cookies_file, use_cookies):
        """下载YouTube音频为MP3"""
        try:
            # 查找yt-dlp的完整路径
            yt_dlp_path = find_executable("yt-dlp")

            # 查找ffmpeg的完整路径
            ffmpeg_path = find_executable("ffmpeg")
            ffmpeg_dir = os.path.dirname(ffmpeg_path) if ffmpeg_path else "/usr/local/bin"

            cmd = [
                yt_dlp_path,
                "-x",  # 仅提取音频
                "--audio-format", "mp3",
                "--ffmpeg-location", ffmpeg_dir,  # 指定ffmpeg位置
                "-o", f"{output_dir}/%(title)s.%(ext)s"
            ]

            if use_cookies and os.path.exists(cookies_file):
                cmd.extend(["--cookies", cookies_file])

            cmd.append(url)

            self.log(f"执行命令: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            # 实时输出日志
            for line in self.process.stdout:
                if not self.processing:
                    self.process.terminate()
                    return None
                line = line.strip()
                if line:
                    self.log(f"  {line}")

            self.process.wait()

            # 先检查文件是否存在（优先级高于退出码）
            # 因为即使有警告导致退出码非0，文件也可能已经下载成功
            mp3_files = list(Path(output_dir).glob("*.mp3"))
            if mp3_files:
                mp3_file = max(mp3_files, key=lambda p: p.stat().st_mtime)
                if self.process.returncode != 0:
                    self.log(f"注意: yt-dlp 返回退出码 {self.process.returncode}，但文件已下载")
                return str(mp3_file)
            else:
                # 文件不存在才报告失败
                self.log(f"下载失败，退出码: {self.process.returncode}")
                self.log("找不到下载的MP3文件")
                return None

        except Exception as e:
            self.log(f"下载出错: {str(e)}")
            return None

    def generate_subtitle(self, mp3_file, whisper_bin, whisper_model):
        """生成字幕"""
        try:
            srt_file = f"{mp3_file}.srt"

            # 检查字幕是否已存在
            if os.path.exists(srt_file) and os.path.getsize(srt_file) > 0:
                self.log(f"字幕已存在，跳过: {os.path.basename(srt_file)}")
                return srt_file

            cmd = [
                whisper_bin,
                "-m", whisper_model,
                "-f", mp3_file,
                "-l", "zh",
                "-osrt",
                "-t", "16",
                "-p", "1"
            ]

            self.log(f"执行命令: {' '.join(cmd)}")

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.path.dirname(mp3_file)
            )

            # 实时输出日志
            for line in self.process.stdout:
                if not self.processing:
                    self.process.terminate()
                    return None
                line = line.strip()
                if line:
                    # 提取进度信息
                    if "whisper_print_progress" in line or "[" in line:
                        self.log(f"  {line}")

            self.process.wait()

            if self.process.returncode != 0:
                self.log(f"字幕生成失败，退出码: {self.process.returncode}")
                return None

            if os.path.exists(srt_file) and os.path.getsize(srt_file) > 0:
                return srt_file
            else:
                self.log("字幕文件未生成")
                return None

        except Exception as e:
            self.log(f"生成字幕出错: {str(e)}")
            return None

def main():
    root = tk.Tk()
    app = YouTubeSubtitleGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
