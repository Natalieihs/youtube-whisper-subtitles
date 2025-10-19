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
        self.root.geometry("900x700")

        # 默认配置
        self.output_dir = str(Path.home() / "Downloads" / "AWS课程")
        self.cookies_file = str(Path.home() / "Downloads" / "youtube.txt")
        self.whisper_bin = "/tmp/whisper.cpp/build/bin/whisper-cli"
        self.whisper_model = "/tmp/whisper.cpp/models/ggml-base-q5_1.bin"

        self.setup_ui()

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

        self.stop_button = ttk.Button(button_frame, text="停止",
                                      command=self.stop_processing, state=tk.DISABLED)
        self.stop_button.grid(row=0, column=1, padx=5)

        ttk.Button(button_frame, text="清空日志",
                  command=self.clear_log).grid(row=0, column=2, padx=5)

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
        """添加日志消息"""
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
        """更新状态标签"""
        self.status_label.config(text=message, foreground=color)

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

        # 开始处理
        self.processing = True
        self.start_button.config(state=tk.DISABLED)
        self.stop_button.config(state=tk.NORMAL)
        self.progress.start()

        # 在新线程中处理
        thread = threading.Thread(target=self.process_urls, args=(urls,))
        thread.daemon = True
        thread.start()

    def stop_processing(self):
        """停止处理"""
        self.processing = False
        if self.process:
            self.process.terminate()
        self.update_status("已停止", "red")
        self.log("用户停止了处理")
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
        self.progress.stop()
        self.start_button.config(state=tk.NORMAL)
        self.stop_button.config(state=tk.DISABLED)

        if self.processing:
            self.update_status(f"完成！成功: {success_count}/{total}", "green")
            self.log(f"\n{'='*60}")
            self.log(f"全部完成！成功处理 {success_count}/{total} 个视频")
            messagebox.showinfo("完成", f"成功处理 {success_count}/{total} 个视频")

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

            if self.process.returncode != 0:
                self.log(f"下载失败，退出码: {self.process.returncode}")
                return None

            # 查找下载的MP3文件（最新的）
            mp3_files = list(Path(output_dir).glob("*.mp3"))
            if mp3_files:
                mp3_file = max(mp3_files, key=lambda p: p.stat().st_mtime)
                return str(mp3_file)
            else:
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
