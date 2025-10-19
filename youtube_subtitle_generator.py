#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
YouTube 字幕生成器 v2.0
功能：
1. 从YouTube下载视频并转换为MP3
2. 使用whisper.cpp自动生成中文字幕
3. 美化的UI界面
4. 改进的线程处理
"""

import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext, messagebox
import subprocess
import threading
import os
import shutil
from pathlib import Path
from datetime import datetime
import queue

def find_executable(name):
    """查找可执行文件的完整路径"""
    path = shutil.which(name)
    if path:
        return path

    common_paths = [
        f'/usr/local/bin/{name}',
        f'/opt/homebrew/bin/{name}',
        f'/usr/bin/{name}',
        f'/bin/{name}',
    ]

    for path in common_paths:
        if os.path.exists(path) and os.access(path, os.X_OK):
            return path

    return name

class YouTubeSubtitleGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube 字幕生成器 v2.0")
        self.root.geometry("1000x780")
        self.root.resizable(True, True)

        # 主题颜色
        self.colors = {
            'bg': '#F5F7FA',
            'primary': '#FF0000',
            'secondary': '#1E90FF',
            'success': '#10B981',
            'text': '#2D3748',
            'text_light': '#718096',
            'white': '#FFFFFF',
            'border': '#E2E8F0'
        }

        self.root.configure(bg=self.colors['bg'])

        # 默认配置
        self.output_dir = str(Path.home() / "Downloads" / "AWS课程")
        self.cookies_file = str(Path.home() / "Downloads" / "youtube.txt")
        self.whisper_bin = "/tmp/whisper.cpp/build/bin/whisper-cli"
        self.whisper_model = "/tmp/whisper.cpp/models/ggml-base-q5_1.bin"

        # 消息队列
        self.message_queue = queue.Queue()
        self.processing = False
        self.process = None

        # 设置样式和UI
        self.setup_styles()
        self.setup_ui()
        self.process_messages()

    def setup_styles(self):
        """设置样式"""
        style = ttk.Style()
        style.theme_use('default')

        # Frame样式
        style.configure('TFrame', background=self.colors['bg'])
        style.configure('Card.TFrame',
                       background=self.colors['white'],
                       borderwidth=1,
                       relief='solid')

        # Label样式
        style.configure('TLabel',
                       background=self.colors['bg'],
                       foreground=self.colors['text'],
                       font=('Helvetica', 11))
        style.configure('Title.TLabel',
                       font=('Helvetica', 20, 'bold'),
                       foreground=self.colors['primary'])
        style.configure('Card.TLabel',
                       background=self.colors['white'],
                       foreground=self.colors['text'])

        # Button样式
        style.configure('TButton',
                       font=('Helvetica', 11),
                       padding=(15, 8))

        # Entry样式
        style.configure('TEntry',
                       fieldbackground=self.colors['white'],
                       foreground=self.colors['text'],
                       borderwidth=1,
                       padding=8)

        # Checkbutton样式
        style.configure('TCheckbutton',
                       background=self.colors['white'],
                       foreground=self.colors['text'],
                       font=('Helvetica', 11))

    def setup_ui(self):
        """设置UI"""
        # 主容器
        container = ttk.Frame(self.root, padding="20", style='TFrame')
        container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 标题
        title = ttk.Label(container, text="🎬 YouTube 字幕生成器",
                         style='Title.TLabel')
        title.grid(row=0, column=0, pady=(0, 20))

        # URL卡片
        url_card = self.create_card(container, "YouTube 视频链接")
        url_card.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=10)

        ttk.Label(url_card, text="单个视频URL:", style='Card.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=5)
        self.url_entry = ttk.Entry(url_card, width=70)
        self.url_entry.grid(row=0, column=1, padx=(10, 0), sticky=(tk.W, tk.E))

        ttk.Label(url_card, text="批量URL (每行一个):", style='Card.TLabel').grid(
            row=1, column=0, sticky=(tk.W, tk.N), pady=(10, 5))
        self.url_text = tk.Text(url_card, width=70, height=4,
                               font=('Helvetica', 11),
                               bg=self.colors['white'],
                               fg=self.colors['text'],
                               relief='solid',
                               borderwidth=1)
        self.url_text.grid(row=1, column=1, padx=(10, 0), pady=(10, 0),
                          sticky=(tk.W, tk.E))

        # 配置卡片
        config_card = self.create_card(container, "配置选项")
        config_card.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=10)

        # 输出目录
        ttk.Label(config_card, text="输出目录:", style='Card.TLabel').grid(
            row=0, column=0, sticky=tk.W, pady=5)
        dir_frame = ttk.Frame(config_card, style='Card.TFrame')
        dir_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        self.output_dir_entry = ttk.Entry(dir_frame, width=55)
        self.output_dir_entry.insert(0, self.output_dir)
        self.output_dir_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(dir_frame, text="浏览", command=self.browse_output_dir).grid(
            row=0, column=1, padx=(5, 0))
        dir_frame.columnconfigure(0, weight=1)

        # Cookies
        ttk.Label(config_card, text="Cookies文件:", style='Card.TLabel').grid(
            row=1, column=0, sticky=tk.W, pady=5)
        cookies_frame = ttk.Frame(config_card, style='Card.TFrame')
        cookies_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 0), pady=5)
        self.cookies_entry = ttk.Entry(cookies_frame, width=55)
        self.cookies_entry.insert(0, self.cookies_file)
        self.cookies_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        ttk.Button(cookies_frame, text="浏览", command=self.browse_cookies).grid(
            row=0, column=1, padx=(5, 0))
        cookies_frame.columnconfigure(0, weight=1)

        self.use_cookies_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(config_card, text="使用Cookies (下载受限视频)",
                       variable=self.use_cookies_var).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, pady=5)

        # 高级配置(可折叠)
        ttk.Label(config_card, text="Whisper路径:", style='Card.TLabel').grid(
            row=3, column=0, sticky=tk.W, pady=5)
        self.whisper_bin_entry = ttk.Entry(config_card, width=60)
        self.whisper_bin_entry.insert(0, self.whisper_bin)
        self.whisper_bin_entry.grid(row=3, column=1, sticky=(tk.W, tk.E),
                                   padx=(10, 0), pady=5)

        ttk.Label(config_card, text="Whisper模型:", style='Card.TLabel').grid(
            row=4, column=0, sticky=tk.W, pady=5)
        self.whisper_model_entry = ttk.Entry(config_card, width=60)
        self.whisper_model_entry.insert(0, self.whisper_model)
        self.whisper_model_entry.grid(row=4, column=1, sticky=(tk.W, tk.E),
                                     padx=(10, 0), pady=5)

        # 按钮区域
        button_frame = ttk.Frame(container, style='TFrame')
        button_frame.grid(row=3, column=0, pady=15)

        self.start_button = tk.Button(button_frame,
                                      text="🚀 开始处理",
                                      command=self.start_processing,
                                      bg=self.colors['primary'],
                                      fg='white',
                                      font=('Helvetica', 12, 'bold'),
                                      relief='flat',
                                      cursor='hand2',
                                      padx=30,
                                      pady=10)
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = tk.Button(button_frame,
                                     text="⏸ 停止",
                                     command=self.stop_processing,
                                     bg='#6B7280',
                                     fg='white',
                                     font=('Helvetica', 12, 'bold'),
                                     relief='flat',
                                     cursor='hand2',
                                     state=tk.DISABLED,
                                     padx=30,
                                     pady=10)
        self.stop_button.grid(row=0, column=1, padx=5)

        clear_button = tk.Button(button_frame,
                                text="🗑 清空日志",
                                command=self.clear_log,
                                bg='#E5E7EB',
                                fg=self.colors['text'],
                                font=('Helvetica', 12),
                                relief='flat',
                                cursor='hand2',
                                padx=30,
                                pady=10)
        clear_button.grid(row=0, column=2, padx=5)

        # 进度条
        self.progress = ttk.Progressbar(container, mode='indeterminate', length=800)
        self.progress.grid(row=4, column=0, pady=10, sticky=(tk.W, tk.E))

        # 状态标签
        self.status_label = tk.Label(container,
                                     text="✅ 就绪",
                                     bg=self.colors['bg'],
                                     fg=self.colors['success'],
                                     font=('Helvetica', 11, 'bold'))
        self.status_label.grid(row=5, column=0, sticky=tk.W)

        # 日志卡片
        log_card = self.create_card(container, "处理日志")
        log_card.grid(row=6, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=10)

        self.log_text = scrolledtext.ScrolledText(log_card,
                                                  width=90,
                                                  height=12,
                                                  font=('Monaco', 10),
                                                  bg='#1E293B',
                                                  fg='#E2E8F0',
                                                  insertbackground='white',
                                                  relief='flat',
                                                  state=tk.DISABLED)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置日志卡片的网格权重
        log_card.columnconfigure(0, weight=1)
        log_card.rowconfigure(0, weight=1)

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(6, weight=1)
        url_card.columnconfigure(1, weight=1)
        config_card.columnconfigure(1, weight=1)

    def create_card(self, parent, title):
        """创建卡片组件"""
        frame = tk.Frame(parent,
                        bg=self.colors['white'],
                        relief='flat',
                        borderwidth=0,
                        padx=15,
                        pady=15)

        if title:
            title_label = tk.Label(frame,
                                  text=title,
                                  bg=self.colors['white'],
                                  fg=self.colors['text'],
                                  font=('Helvetica', 12, 'bold'))
            title_label.grid(row=0, column=0, sticky=tk.W, pady=(0, 5))

            separator = tk.Frame(frame, height=1, bg=self.colors['border'])
            separator.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))

        content_frame = ttk.Frame(frame, style='Card.TFrame')
        content_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(2, weight=1)

        return content_frame

    def process_messages(self):
        """处理消息队列"""
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

        self.root.after(100, self.process_messages)

    def log(self, message):
        """添加日志(线程安全)"""
        self.message_queue.put(('log', message))

    def _do_log(self, message):
        """实际执行日志添加(仅在主线程)"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_status(self, message, color="black"):
        """更新状态(线程安全)"""
        self.message_queue.put(('status', {'text': message, 'color': color}))

    def _do_update_status(self, text, color):
        """实际更新状态(仅在主线程)"""
        icon = "✅" if "成功" in text or "就绪" in text else "🔄" if "处理" in text else "⚠️"
        self.status_label.config(text=f"{icon} {text}", fg=color)

    def clear_log(self):
        """清空日志"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def browse_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory()
        if directory:
            self.output_dir_entry.delete(0, tk.END)
            self.output_dir_entry.insert(0, directory)

    def browse_cookies(self):
        """选择cookies文件"""
        filename = filedialog.askopenfilename(
            title="选择Cookies文件",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            self.cookies_entry.delete(0, tk.END)
            self.cookies_entry.insert(0, filename)

    def start_processing(self):
        """开始处理"""
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

        self.processing = True
        self.message_queue.put(('button_state', {'button': 'start', 'state': tk.DISABLED}))
        self.message_queue.put(('button_state', {'button': 'stop', 'state': tk.NORMAL}))
        self.message_queue.put(('progress_start', None))

        thread = threading.Thread(target=self.process_urls, args=(urls,), daemon=True)
        thread.start()

    def stop_processing(self):
        """停止处理"""
        self.processing = False
        if self.process:
            self.process.terminate()
        self.update_status("已停止", self.colors['error'])
        self.log("⏸ 用户停止了处理")
        self.message_queue.put(('button_state', {'button': 'start', 'state': tk.NORMAL}))
        self.message_queue.put(('button_state', {'button': 'stop', 'state': tk.DISABLED}))
        self.message_queue.put(('progress_stop', None))

    def process_urls(self, urls):
        """处理URL列表"""
        output_dir = self.output_dir_entry.get().strip()
        cookies_file = self.cookies_entry.get().strip()
        use_cookies = self.use_cookies_var.get()
        whisper_bin = self.whisper_bin_entry.get().strip()
        whisper_model = self.whisper_model_entry.get().strip()

        os.makedirs(output_dir, exist_ok=True)

        total = len(urls)
        success_count = 0

        for idx, url in enumerate(urls, 1):
            if not self.processing:
                break

            self.update_status(f"处理 {idx}/{total}: {url}", self.colors['secondary'])
            self.log(f"\n{'='*60}")
            self.log(f"🎯 处理第 {idx}/{total} 个视频: {url}")

            try:
                self.log("📥 步骤1: 下载音频...")
                mp3_file = self.download_audio(url, output_dir, cookies_file, use_cookies)

                if not mp3_file or not self.processing:
                    continue

                self.log(f"✅ 下载完成: {os.path.basename(mp3_file)}")

                self.log("🤖 步骤2: 生成字幕...")
                srt_file = self.generate_subtitle(mp3_file, whisper_bin, whisper_model)

                if srt_file:
                    self.log(f"✅ 字幕生成完成: {os.path.basename(srt_file)}")
                    success_count += 1
                else:
                    self.log("❌ 字幕生成失败")

            except Exception as e:
                self.log(f"❌ 处理失败: {str(e)}")

        self.message_queue.put(('progress_stop', None))
        self.message_queue.put(('button_state', {'button': 'start', 'state': tk.NORMAL}))
        self.message_queue.put(('button_state', {'button': 'stop', 'state': tk.DISABLED}))

        if self.processing:
            self.update_status(f"完成！成功: {success_count}/{total}", self.colors['success'])
            self.log(f"\n{'='*60}")
            self.log(f"🎉 全部完成！成功处理 {success_count}/{total} 个视频")
            self.message_queue.put(('messagebox', {
                'title': '完成',
                'message': f'成功处理 {success_count}/{total} 个视频'
            }))

    def download_audio(self, url, output_dir, cookies_file, use_cookies):
        """下载音频"""
        try:
            yt_dlp_path = find_executable("yt-dlp")
            ffmpeg_path = find_executable("ffmpeg")
            ffmpeg_dir = os.path.dirname(ffmpeg_path) if ffmpeg_path else "/usr/local/bin"

            cmd = [
                yt_dlp_path,
                "-x",
                "--audio-format", "mp3",
                "--ffmpeg-location", ffmpeg_dir,
                "-o", f"{output_dir}/%(title)s.%(ext)s"
            ]

            if use_cookies and os.path.exists(cookies_file):
                cmd.extend(["--cookies", cookies_file])

            cmd.append(url)

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )

            for line in self.process.stdout:
                if not self.processing:
                    self.process.terminate()
                    return None
                line = line.strip()
                if line:
                    self.log(f"  {line}")

            self.process.wait()

            if self.process.returncode != 0:
                self.log(f"❌ 下载失败，退出码: {self.process.returncode}")
                return None

            mp3_files = list(Path(output_dir).glob("*.mp3"))
            if mp3_files:
                return str(max(mp3_files, key=lambda p: p.stat().st_mtime))
            else:
                self.log("❌ 找不到下载的MP3文件")
                return None

        except Exception as e:
            self.log(f"❌ 下载出错: {str(e)}")
            return None

    def generate_subtitle(self, mp3_file, whisper_bin, whisper_model):
        """生成字幕"""
        try:
            srt_file = f"{mp3_file}.srt"

            if os.path.exists(srt_file) and os.path.getsize(srt_file) > 0:
                self.log(f"ℹ️  字幕已存在，跳过: {os.path.basename(srt_file)}")
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

            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                cwd=os.path.dirname(mp3_file)
            )

            for line in self.process.stdout:
                if not self.processing:
                    self.process.terminate()
                    return None
                line = line.strip()
                if line and ("[" in line or "whisper" in line.lower()):
                    self.log(f"  {line}")

            self.process.wait()

            if self.process.returncode != 0:
                self.log(f"❌ 字幕生成失败，退出码: {self.process.returncode}")
                return None

            if os.path.exists(srt_file) and os.path.getsize(srt_file) > 0:
                return srt_file
            else:
                self.log("❌ 字幕文件未生成")
                return None

        except Exception as e:
            self.log(f"❌ 生成字幕出错: {str(e)}")
            return None

def main():
    root = tk.Tk()
    app = YouTubeSubtitleGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
