# Cloud Foundry CLI 命令清单

按本项目（Python + Streamlit + Approuter + XSUAA + AI Core + HANA）实际工作流整理。
不是 CF CLI 完整文档，只覆盖你实际会用到的命令。

完整文档见官方：
<https://docs.cloudfoundry.org/cf-cli/cf-help.html>

---

## 1. 登录与环境定位

```bash
cf login -a <api-endpoint>           # 交互式登录（输用户名/密码/选 org+space）
cf login --sso -a <api-endpoint>     # 用公司 SSO 登录（推荐）
cf logout

cf api                               # 当前已登录的 API endpoint
cf target                            # 当前 user / org / space
cf target -o <org> -s <space>        # 切换 org / space

cf orgs                              # 所有 org
cf spaces                            # 当前 org 下的 space
```

---

## 2. 应用部署 (push)

```bash
cf push                              # 按 manifest.yml 推（最常用）
cf push <app-name>                   # 只推 manifest 里指定的某个 app
cf push --no-start                   # 推但不启动（先 set-env 后再 start）
cf push -f <other-manifest.yml>      # 用别的 manifest
cf push --strategy rolling           # 滚动更新（零停机）
```

> 本项目特殊场景：

```bash
cf push rag-chatbot-yf-backend       # 只重推 backend
cf push rag-chatbot-yf-router        # 只重推 router
```

---

## 3. 查看应用

```bash
cf apps                              # 当前 space 所有 app
cf app <app-name>                    # 单个 app 状态（实例 / 内存 / URL / binding）
cf events <app-name>                 # 历史事件（push / crash / restart 等）
```

---

## 4. 应用控制

```bash
cf start <app-name>                  # 启动
cf stop <app-name>                   # 停止
cf restart <app-name>                # 重启进程（不重新构建）
cf restage <app-name>                # 重新执行 buildpack 构建（env 改了之后必须）

cf scale <app-name> -i 2             # 改实例数
cf scale <app-name> -m 2G            # 改单实例内存
cf scale <app-name> -k 4G            # 改 disk
cf scale <app-name> -i 2 -m 2G -k 4G # 一次改全部

cf delete <app-name>                 # 删除 app
cf delete <app-name> -r              # 同时删除其专属 route
cf delete <app-name> -f              # 不交互式确认
```

---

## 5. 日志查看

```bash
cf logs <app-name>                   # 实时流式日志（Ctrl+C 退出）
cf logs <app-name> --recent          # 最近一段时间日志（最常用的故障排查命令）
```

---

## 6. 环境变量

```bash
cf env <app-name>                    # 查看 app 的所有 env（含 VCAP / user-provided）
cf set-env <app-name> KEY value      # 设置 user-provided env 变量
cf unset-env <app-name> KEY          # 删除某个 env 变量
```

> ⚠️ `cf set-env` / `cf unset-env` 之后必须 `cf restage <app>` 才生效（不是 `restart`）。

本项目最常用：

```bash
cf set-env rag-chatbot-yf-backend TAVILY_API_KEY <your_key>
cf restage rag-chatbot-yf-backend
```

---

## 7. 服务（service）管理

```bash
cf services                          # 当前 space 所有 service instance
cf service <instance-name>           # 单个 service 详情

cf marketplace                       # 列出可创建的 service 类型
cf marketplace -e <service>          # 某个 service 的 plan 列表

cf create-service <service> <plan> <instance-name>           # 默认参数
cf create-service <service> <plan> <instance-name> -c '<json-params>'  # 带配置（如 XSUAA 用 xs-security.json）
cf update-service <instance-name> -c '<json-params>'         # 更新配置
cf delete-service <instance-name>                            # 删除
```

> 本项目特例：

```bash
cf update-service rag-chatbot-yf-xsuaa -c xs-security.json
```

### Service binding（把 service 绑到 app）

```bash
cf bind-service <app-name> <instance-name>       # 之后要 restage 才生效
cf unbind-service <app-name> <instance-name>
```

### Service key（给本地开发用）

```bash
cf create-service-key <instance-name> <key-name>     # 创建一个 service key
cf service-keys <instance-name>                      # 列出某个 service 的所有 key
cf service-key <instance-name> <key-name>            # 查看 key 内容（含密码 / URL 等）
cf delete-service-key <instance-name> <key-name>
```

---

## 8. SSH 进入容器

### 8.1 基本登录

```bash
cf ssh <app-name>                       # 交互式 shell（最常用）
cf ssh <app-name> -i 1                  # 指定连接到第几个实例（0/1/2...，默认 0）
cf ssh <app-name> -c "<command>"        # 执行单条命令后立即退出（适合脚本化）
cf ssh <app-name> --skip-host-validation  # 跳过 host key 校验（碰到证书警告时用）
```

> 💡 多实例（`cf scale -i 3`）时 `-i N` 用来选择具体哪个 instance。如果只是"连其中一个"看看，省略 `-i` 默认进 instance 0。

### 8.2 退出容器

```bash
exit            # 标准退出
Ctrl+D          # 等同 exit
~.              # SSH 强制断开（敲快捷键 ~ 后跟 .，连接卡死时用）
```

### 8.3 容器内常用路径

| 路径 | 作用 |
|---|---|
| `/home/vcap/app` | 应用代码（你 `cf push` 上来的） |
| `/home/vcap/deps/0/bin/python` | buildpack 装的 Python |
| `/home/vcap/deps/0/bin/pip` | buildpack 装的 pip |
| `/home/vcap/staging_info.yml` | buildpack 元信息 |
| `/home/vcap/logs/` | streamlit / nodejs / staging 各种日志 |
| `$VCAP_SERVICES` | 服务绑定凭证 JSON |
| `$VCAP_APPLICATION` | 应用元信息 JSON |

### 8.4 容器内常用命令

#### 看代码

```bash
cd /home/vcap/app
ls -la                                  # 看 cf push 上来了哪些文件
cat tools/wikipedia.py
grep -rn 'action.*parse' .              # 搜代码
```

#### 看 Python 环境

```bash
which python                            # buildpack 装的 Python 路径
/home/vcap/deps/0/bin/python --version  # 版本
/home/vcap/deps/0/bin/pip list          # 已装的所有包
/home/vcap/deps/0/bin/pip show langchain  # 单个包详情
```

#### 看环境变量

```bash
env                                     # 所有 env
env | grep AICORE                       # 只看 AICORE_*
env | grep -i tavily                    # 不区分大小写

# VCAP 相关
echo $VCAP_APPLICATION | python3 -m json.tool        # 应用信息（实例 ID / 内存 / route 等）
echo $VCAP_SERVICES | python3 -m json.tool           # 所有 service binding 凭证
echo $VCAP_SERVICES | python3 -m json.tool | head -30
```

#### 直接跑 Python 测代码

```bash
# 单行测试某个 tool
/home/vcap/deps/0/bin/python -c "
from tools.wikipedia import search_wikipedia
import json
r = search_wikipedia.invoke({'query': '林彪', 'lang': 'zh'})
print(len(json.loads(r)['summary']))
"

# 进 Python REPL
/home/vcap/deps/0/bin/python
>>> from tools.wikipedia import search_wikipedia
>>> ...
>>> exit()
```

#### 看磁盘 / 内存 / 进程

```bash
df -h                                   # 磁盘占用（容器配额）
du -sh /home/vcap/app                   # app 目录占用
free -h                                 # 内存使用
ps aux                                  # 进程列表（看 streamlit 是否在跑）
top                                     # 实时 CPU / 内存（按 q 退出）
```

#### 看日志

```bash
ls -la /home/vcap/logs/                 # 所有日志文件
tail -f /home/vcap/logs/staging_task.log  # 实时跟踪 staging（buildpack）日志
tail -200 /home/vcap/logs/*.log         # 最后 200 行所有日志
```

### 8.5 端口转发（本地直连容器内 service）

把容器内某端口"映射"到本机，让你**在本机用浏览器/工具直接访问**容器里跑的服务。

```bash
cf ssh <app-name> -L <local-port>:<container-host>:<container-port>
```

例：

```bash
# 本机 8888 → 容器内的 streamlit (8080)
cf ssh rag-chatbot-yf-backend -L 8888:127.0.0.1:8080

# 然后在本机浏览器打开 http://localhost:8888
```

用途：

- 直接在本机浏览器访问容器内的 streamlit（不经过 router / SSO）
- 用 DBeaver / SQL 客户端连容器里的 HANA tunnel
- 接 Python debugger 远程调试

> ⚠️ SSH session 必须保持开着，关了 tunnel 就断。可以在另一个 terminal 里继续用。

### 8.6 一行命令模式（`-c`）

非交互式执行单条命令，**适合脚本化或快速一次性查询**：

```bash
cf ssh <app-name> -c "ls /home/vcap/app"
cf ssh <app-name> -c "cat /home/vcap/app/requirements.txt"
cf ssh <app-name> -c "/home/vcap/deps/0/bin/pip list | grep langchain"
cf ssh <app-name> -c "env | grep AICORE_BASE_URL"
```

> 💡 PowerShell 引号转义有坑（多层引号嵌套容易乱）。复杂命令最好用**交互式 shell** 而不是 `-c`。

### 8.7 启用 / 关闭 SSH

```bash
cf ssh-enabled <app-name>               # 是否允许 SSH
cf enable-ssh <app-name>                # 启用（仅该 app）
cf restart <app-name>                   # 启用后必须重启才生效
cf disable-ssh <app-name>               # 禁用（生产环境出于安全可能要关）

# Space 级别（影响该 space 下所有 app）
cf allow-space-ssh <space-name>
cf disallow-space-ssh <space-name>
cf space-ssh-allowed <space-name>       # 检查是否允许
```

> 默认通常都是允许 SSH 的，不用设置。**只有 `cf ssh` 报"SSH disabled"才需要 enable**。

### 8.8 SSH 故障排查

```bash
# 报 "permission denied / SSH not enabled"
cf ssh-enabled <app-name>               # 输出 "false" 就先 enable

# 报 "host key verification failed"
cf ssh <app-name> --skip-host-validation

# 连不上、卡死
cf app <app-name>                       # 先确认 app 真的在 running

# 报错 "you do not have permission..."
cf target                               # 确认 org/space 是对的
```

### 8.9 重要警告

容器内的修改**重启就丢**——`cf restart` / `cf restage` / 平台主动迁移都会让容器内的临时改动消失，回到 `cf push` 时的版本。

要持久化修改，**必须改本地代码 → `cf push`**，不能在容器里改。SSH 进去改文件只适合"快速验证假设"，确认问题后还是要走标准 push 流程。

---

## 9. 路由（route）

```bash
cf routes                                            # 当前 space 所有路由
cf map-route <app> <domain> --hostname <host>        # 给 app 加路由
cf unmap-route <app> <domain> --hostname <host>      # 解绑（路由还在，只是不指了）
cf delete-route <domain> --hostname <host>           # 彻底删除
cf domains                                           # 可用域
```

---

## 10. 网络策略（C2C）

```bash
cf network-policies                                  # 列出所有 C2C 策略
cf add-network-policy <src-app> <dst-app> --protocol tcp --port 8080
cf remove-network-policy <src-app> <dst-app> --protocol tcp --port 8080
```

> ⚠️ 本项目因 `network.write` 权限缺失，C2C 路线放弃了，使用公网 + 自校验 JWT 方案。这组命令暂不用。

---

## 11. 故障排查神器

按出问题频率排序：

```bash
cf logs <app-name> --recent          # 最近日志（最常用）
cf logs <app-name>                   # 实时日志
cf events <app-name>                 # crash / OOM / push 事件历史
cf app <app-name>                    # 实例状态、CPU、内存使用
cf ssh <app-name>                    # 进容器查文件
cf env <app-name>                    # 检查 env / VCAP 注入是否正确
cf restage <app-name>                # env 改了/绑了新 service 后必做
cf restart <app-name>                # 单纯重启进程
```

---

## 12. Droplet / staging 排查

```bash
cf droplets <app-name>                               # 该 app 的所有 droplet
cf download-droplet <app-name> --path ./droplet.tgz  # 下载当前 running droplet（看 buildpack 装了啥）
```

---

## 13. 杂项

```bash
cf curl /v3/apps                                     # 用 cf 的认证直接发 CF API 请求（高级排查）
cf version                                           # CLI 版本
cf help                                              # 完整帮助
cf help -a                                           # 按字母列出所有命令
cf <command> --help                                  # 单个命令帮助
```

---

## 14. 本项目高频组合操作

### A. 改了代码 → 重新部署

```bash
cf push rag-chatbot-yf-backend
```

### B. 改了 `TAVILY_API_KEY`（或新增 env）

```bash
cf set-env rag-chatbot-yf-backend TAVILY_API_KEY <new-value>
cf restage rag-chatbot-yf-backend
```

### C. 改了 `xs-security.json`（XSUAA 配置）

```bash
cf update-service rag-chatbot-yf-xsuaa -c xs-security.json
cf restage rag-chatbot-yf-backend
cf restage rag-chatbot-yf-router
```

### D. 应用启动失败的标准排查流程

```bash
cf logs rag-chatbot-yf-backend --recent              # 启动日志
cf events rag-chatbot-yf-backend                     # 是否 OOM / crash
cf app rag-chatbot-yf-backend                        # 实例状态
cf ssh rag-chatbot-yf-backend                        # 进容器手动起 streamlit / python 看真实错
cf env rag-chatbot-yf-backend                        # 检查 VCAP_SERVICES 里 binding 对不对
```

### E. 验证 wiki tool 在 CF 上是否是新版

```bash
cf ssh rag-chatbot-yf-backend -c "cd /home/vcap/app && grep -c 'action.*parse' tools/wikipedia.py"
# 返回 >=1 说明是新版 wiki 代码
```

### F. 在容器里测试某个 tool 的真实行为

```bash
cf ssh rag-chatbot-yf-backend
cd /home/vcap/app
/home/vcap/deps/0/bin/python << 'EOF'
from tools.weather import get_weather
import json
r = get_weather.invoke({"location": "Tokyo"})
print(r)
EOF
exit
```

### G. 查看 service binding 是否正确注入

```bash
cf ssh rag-chatbot-yf-backend -c "echo \$VCAP_SERVICES | python3 -m json.tool | head -50"
```

应能看到 `aicore`、`hana`、`xsuaa` 三个 binding 的 key 名。

### H. 本机直连容器内 streamlit（开发/调试用）

```bash
# Terminal 1: 开 tunnel
cf ssh rag-chatbot-yf-backend -L 8888:127.0.0.1:8080

# Terminal 2 / 浏览器: 访问 http://localhost:8888
```

> 这绕开了 router 和 SSO，可以快速测试后端本身的行为。注意 `auth_service.py` 里如果 `XSUAA_REQUIRE_AUTH=1` 会拒绝直连。

### I. 一键拆掉本项目所有部署

```bash
cf delete rag-chatbot-yf-backend -r -f
cf delete rag-chatbot-yf-router -r -f
cf delete-service rag-chatbot-yf-xsuaa -f
```

---

## 15. CF push 之后 env 是否会保留

| 操作 | 已设置的 env 是否保留 |
|---|---|
| `cf push <app>` 同名重推 | ✅ 保留（不会清掉之前 `cf set-env` 的内容） |
| `cf delete <app>` 之后再 push | ❌ 清空（app 是新的） |
| `cf restage` | ✅ 保留 |
| `cf restart` | ✅ 保留 |

`manifest.yml` 里 `env:` 块定义的会和 `cf set-env` 设的合并，**`cf set-env` 优先级更高**（在 push 时不会被 manifest 覆盖）。

---

## 16. 典型新项目首次部署的命令序列

```bash
# 1. 登录到正确 org/space
cf login --sso -a https://api.cf.eu10-004.hana.ondemand.com
cf target -o <your-org> -s <your-space>

# 2. 创建 XSUAA service
cf create-service xsuaa application rag-chatbot-yf-xsuaa -c xs-security.json

# 3. 推应用（不立即启动，先设密钥）
cf push --no-start

# 4. 设 Tavily key
cf set-env rag-chatbot-yf-backend TAVILY_API_KEY <key>

# 5. 启动
cf start rag-chatbot-yf-backend
cf start rag-chatbot-yf-router

# 6. 拿到 URL 测试
cf app rag-chatbot-yf-router         # 看 router 的 routes 字段
```

---

更新日期：2026-05-09
