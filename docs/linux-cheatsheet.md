# Linux 命令清单

按本项目实际会遇到的场景整理。这些命令通用于：
- SAP BAS 的终端
- `cf ssh` 进入的 CF 容器
- 本地 WSL / Git Bash / Mac terminal
- 任何 Linux / Unix 服务器

不是 Linux 完整教程，只覆盖实战常用部分。完整文档请查 `man <command>` 或 [tldr.sh](https://tldr.sh/)。

---

## 1. 当前位置 / 切换目录

```bash
pwd                                  # print working directory，当前在哪
cd /home/vcap/app                    # 切到绝对路径
cd ..                                # 上一级
cd ~                                 # 回到用户主目录（CF 容器是 /home/vcap，BAS 是 /home/user）
cd -                                 # 回到上一次所在目录（来回切换神器）
```

## 2. 列文件

```bash
ls                                   # 列当前目录（不显示隐藏文件）
ls -a                                # 显示所有，包括 .开头的隐藏文件
ls -l                                # long format，含权限/大小/时间
ls -la                               # 上面两个合一（最常用）
ls -lh                               # human readable，文件大小用 K/M/G
ls -lt                               # 按修改时间倒序
ls -lS                               # 按文件大小倒序
ls dir/                              # 列指定目录
```

## 3. 看文件内容

```bash
cat file.py                          # 打印整个文件
cat file1 file2                      # 打印多个文件（合并输出）

head file.py                         # 前 10 行
head -20 file.py                     # 前 20 行
head -c 200 file.py                  # 前 200 字节

tail file.py                         # 最后 10 行
tail -50 file.py                     # 最后 50 行
tail -f file.log                     # 实时跟踪文件新增（Ctrl+C 退出，看日志神器）

less file.py                         # 分页查看大文件（按 q 退出，/搜索，G 到末尾，gg 到开头）
```

## 4. 搜索文件内容（grep）

```bash
grep "pattern" file.py               # 在文件里搜
grep -i "pattern" file.py            # 不区分大小写
grep -n "pattern" file.py            # 显示行号
grep -r "pattern" .                  # 递归搜当前目录所有文件
grep -rn "pattern" .                 # 递归 + 显示行号（最常用）
grep -v "pattern" file.py            # 反向：列出 *不* 匹配的行
grep -c "pattern" file.py            # 只输出匹配行数
grep -A 3 "pattern" file.py          # 匹配行 + 后 3 行（After）
grep -B 3 "pattern" file.py          # 匹配行 + 前 3 行（Before）
grep -C 3 "pattern" file.py          # 前后各 3 行（Context）
```

正则模式：

```bash
grep -E "foo|bar" file.py            # 扩展正则，竖线表示"或"
grep -E "^def " app.py               # 行首匹配
grep "lang.*='zh'" tools/wikipedia.py
```

## 5. 找文件（find）

```bash
find . -name "*.py"                  # 当前目录及子目录所有 .py 文件
find . -type d                       # 只找目录
find . -type f                       # 只找文件
find . -name "*.py" -size +10k       # .py 文件且大于 10K
find . -mtime -7                     # 最近 7 天修改过的
find . -name "__pycache__" -exec rm -rf {} +    # 找到并删除（小心！）
```

## 6. 文件 / 目录操作

```bash
cp file1 file2                       # copy 单个文件
cp -r dir1 dir2                      # 递归复制目录
mv file1 file2                       # 移动 / 重命名
rm file                              # 删除文件
rm -r dir                            # 递归删除目录（! 不可恢复）
rm -rf dir                           # 递归 + 强制（最危险，慎用）

mkdir dir                            # 建目录
mkdir -p path/to/deep/dir            # 递归建多级目录

touch file.txt                       # 建空文件 / 更新文件时间戳
```

## 7. 系统资源

```bash
df -h                                # disk free，分区使用情况（h=human readable）
du -sh dir/                          # 单个目录占用大小
du -sh *                             # 当前目录下每项的占用
du -sh * | sort -h                   # 按大小排序

free -h                              # 内存使用
free -m                              # 单位 MB

top                                  # 实时进程监控（q 退出）
htop                                 # 增强版 top（可能没装）

ps                                   # 当前 shell 的进程
ps aux                               # 所有用户所有进程（最常用）
ps aux | grep python                 # 过滤包含 python 的
```

## 8. 环境变量

```bash
env                                  # 列出所有 env
env | grep AICORE                    # 过滤包含 AICORE 的
echo $PATH                           # 打印单个 env
echo $HOME                           # 用户主目录

export FOO=bar                       # 临时设置（仅当前 shell 及子进程）
unset FOO                            # 删除

# 永久设置（写入 shell 配置文件）
echo 'export FOO=bar' >> ~/.bashrc   # 下次登录或 source ~/.bashrc 后生效
```

## 9. 管道 (`|`) 与重定向 (`>`, `>>`, `<`)

管道：把上一个命令的**输出**送给下一个命令的**输入**。

```bash
ls | grep .py                        # ls 输出 → grep 过滤
ps aux | grep streamlit              # 进程列表 → 找 streamlit
cat file.log | tail -20              # = tail -20 file.log，但能再串
echo "hello" | wc -c                 # echo → 字符计数
env | sort                           # env → 排序
```

重定向：

```bash
ls > files.txt                       # 把 ls 的输出写入文件（覆盖）
ls >> files.txt                      # 追加到文件末尾
python script.py 2> errors.log       # 把错误流（stderr）写入文件
python script.py > out.log 2>&1      # 把标准输出和错误都写入文件
python script.py < input.txt         # 从文件读入作为输入
```

## 10. 文本处理（实用三件套）

```bash
wc file.py                           # word count，行数 / 词数 / 字节数
wc -l file.py                        # 只看行数

sort file.txt                        # 排序
sort -r file.txt                     # 倒序
sort -n file.txt                     # 按数字大小

uniq file.txt                        # 去重相邻重复行（通常先 sort 后 uniq）
sort file.txt | uniq -c              # 统计每行出现次数

cut -d, -f1 data.csv                 # 取 CSV 第一列
awk '{print $1}' file.txt            # 简单字段处理（取第一列）
sed 's/foo/bar/g' file.txt           # 替换 foo 为 bar
```

## 11. 网络 / HTTP

```bash
curl https://example.com             # 发 HTTP 请求，输出响应体
curl -i https://example.com          # 显示响应头
curl -X POST -d '{"x":1}' \
  -H 'Content-Type: application/json' \
  https://example.com/api            # POST JSON

wget https://example.com/file.tar.gz # 下载文件

ping google.com                      # 测连通性（CF 容器里通常没有）
nslookup en.wikipedia.org            # 查 DNS
dig en.wikipedia.org                 # 详细 DNS 查询
```

## 12. 压缩 / 解压

```bash
tar -xzf file.tar.gz                 # 解压 .tar.gz（如 cf download-droplet 出来的文件）
tar -czf out.tar.gz dir/             # 压缩目录为 .tar.gz

unzip file.zip                       # 解压 zip
zip -r out.zip dir/                  # 压缩目录为 zip
```

## 13. 文本编辑器（容器里没有 VSCode）

### nano（简单，适合新手）

```bash
nano file.py                         # 打开
# 编辑
# Ctrl+O 保存
# Ctrl+X 退出
```

### vi / vim（学习曲线陡峭，但所有 Linux 都有）

```bash
vi file.py
```

最少要会的：

| 操作 | 按键 |
|---|---|
| 进入插入模式（开始输入） | `i` |
| 退出插入模式 | `Esc` |
| 上下左右 | 方向键 或 `h j k l` |
| 保存 | `Esc` 然后 `:w` |
| 退出 | `Esc` 然后 `:q` |
| 保存并退出 | `Esc` 然后 `:wq` |
| 强制不保存退出 | `Esc` 然后 `:q!` |
| 搜索 | `/pattern` 然后回车，按 `n` 下一个 |
| 撤销 | `u` |

> 实战提醒：`cf ssh` 进容器后**改文件意义不大**（重启就丢），通常只用来快速看内容，看完用 `Ctrl+C` / `:q!` 退出就行。要持久化修改还是改本地代码 → `cf push`。

## 14. 常用快捷键

| 快捷键 | 作用 |
|---|---|
| `Ctrl+C` | 中断当前命令（最常用） |
| `Ctrl+D` | 退出当前 shell（等同 `exit`） |
| `Ctrl+L` | 清屏（等同 `clear`） |
| `Ctrl+A` | 光标移到行首 |
| `Ctrl+E` | 光标移到行尾 |
| `Ctrl+U` | 删除光标到行首之间的字符 |
| `Ctrl+K` | 删除光标到行尾之间的字符 |
| `Ctrl+R` | 反向搜索历史命令（神器） |
| `Tab` | 自动补全文件名 / 命令 |
| `Tab Tab` | 列出所有可能的补全 |
| ↑ / ↓ | 上一条 / 下一条历史命令 |
| `!!` | 执行上一条命令 |
| `!cf` | 执行最近一条以 `cf` 开头的命令 |

## 15. 用户 / 权限（基础）

```bash
whoami                               # 当前用户
id                                   # 当前用户的 uid / gid

chmod +x script.sh                   # 给文件加执行权限
chmod 644 file                       # rw-r--r--（文件常用）
chmod 755 dir                        # rwxr-xr-x（目录 / 脚本常用）

chown user:group file                # 改 owner / group（CF 容器里基本不用）
```

权限符号速查：

| 数字 | 字母 | 含义 |
|---|---|---|
| 4 | r | 读 |
| 2 | w | 写 |
| 1 | x | 执行 |
| 7 | rwx | 全部 |
| 6 | rw- | 读写 |
| 5 | r-x | 读和执行 |
| 4 | r-- | 只读 |

`chmod 755 file` = owner: rwx, group: rx, others: rx

## 16. Python 调用模式（容器里）

CF 容器里 Python 不在 PATH 上，得用绝对路径：

```bash
/home/vcap/deps/0/bin/python --version
/home/vcap/deps/0/bin/pip list
/home/vcap/deps/0/bin/python script.py
/home/vcap/deps/0/bin/python -c "import json; print(json.dumps({'a': 1}))"
```

执行 Python 标准库模块：

```bash
python3 -m json.tool < file.json     # 把 JSON 美化打印
python3 -m http.server 8000          # 起一个简单的 HTTP server
python3 -m venv .venv                # 建虚拟环境
```

## 17. 链接命令（`&&`, `||`, `;`）

```bash
cmd1 && cmd2                         # cmd1 成功才跑 cmd2（最常用）
cmd1 || cmd2                         # cmd1 失败才跑 cmd2
cmd1 ; cmd2                          # 都跑，不管 cmd1 是否成功
```

例：

```bash
mkdir -p logs && touch logs/app.log
cd .venv/bin/ && source activate     # 切目录后激活
pip install -r requirements.txt && streamlit run app.py
```

## 18. 后台执行 / 作业控制

```bash
long-command &                       # 后台执行
jobs                                 # 列出当前 shell 的作业
fg                                   # 把后台作业拉到前台
bg                                   # 暂停的作业转后台执行
Ctrl+Z                               # 暂停当前前台作业
nohup long-command &                 # 后台跑且 ssh 断开后不停
disown                               # 把作业从 shell 解绑（关 ssh 不杀进程）
```

## 19. 帮助系统

```bash
man ls                               # 完整文档（按 q 退出，/搜索）
ls --help                            # 简短帮助
which python                         # 命令在哪
type cd                              # 命令类型（builtin / alias / 二进制）
history                              # 看历史命令
history | grep ssh                   # 找历史中的 SSH 命令
```

---

## 20. 本项目实战常用组合

### A. 验证某个文件存在并看大小

```bash
ls -lh tools/wikipedia.py
```

### B. 在所有 Python 文件里搜某个关键词

```bash
grep -rn "search_wikipedia" --include="*.py" .
```

### C. 看 streamlit 占多少内存

```bash
ps aux | grep streamlit | grep -v grep
```

### D. 看 .env 里有哪些 key（不打印值）

```bash
grep -E "^[A-Z_]+=" .env | cut -d= -f1
```

### E. 验证一个 API 是否可达

```bash
curl -I https://en.wikipedia.org/w/api.php
# 看 HTTP/1.1 200 OK 就是通的
```

### F. 看磁盘上最大的 5 个目录

```bash
du -sh */ | sort -h | tail -5
```

### G. 实时看 streamlit 日志

```bash
tail -f /home/vcap/logs/staging_task.log
```

### H. 后台跑 streamlit 并保留日志

```bash
nohup streamlit run app.py > app.log 2>&1 &
# 之后 tail -f app.log 看输出
```

### I. 找最近修改的代码

```bash
find . -name "*.py" -mtime -1        # 最近 24 小时改过的 .py
```

### J. 一行检查 Python 是否能 import 某个包

```bash
python3 -c "import langchain; print(langchain.__version__)"
```

---

## 21. Windows ↔ Linux 命令对照

如果你来自 cmd / PowerShell：

| Windows | Linux |
|---|---|
| `dir` | `ls` |
| `cd` (无参数显示当前路径) | `pwd`（Linux 的 `cd` 无参数是回主目录） |
| `type file` | `cat file` |
| `cls` | `clear` |
| `findstr` | `grep` |
| `where` | `which` |
| `del` | `rm` |
| `copy` | `cp` |
| `move` | `mv` |
| `md` | `mkdir` |
| `rd` | `rmdir` / `rm -r` |
| `tasklist` | `ps aux` |
| `taskkill /pid` | `kill <pid>` |
| `set` | `env` 或 `export` |
| `echo %PATH%` | `echo $PATH` |
| `> nul` | `> /dev/null` |
| `\` 路径分隔符 | `/` 路径分隔符 |

---

更新日期：2026-05-09
