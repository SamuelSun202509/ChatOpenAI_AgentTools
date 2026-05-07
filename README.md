# ChatOpenAI_rag

基于 **SAP Generative AI Hub (GPT-4o)** + **SAP HANA Cloud 向量库** + **Streamlit** 的 RAG Chatbot Demo。

代码可在 **本地 / SAP BAS / SAP BTP Cloud Foundry** 三个环境中同源运行。

---

## 项目结构

```
ChatOpenAI_rag/
├── app.py                 # Streamlit UI（仅 UI：侧边栏 + 聊天循环 + JWT auth gate）
├── auth_service.py        # XSUAA JWT 校验（CF 公开 route 的应用层防线）
├── agent_service.py       # KB 注册表 + mode 常量 + build_agent
├── rag_service.py         # Advanced RAG（Rewrite + Fusion）+ CLI 自测
├── prompts.py             # 所有 prompt 模板（RAG 3 个 + Agent 5 种 mode）
├── config.py              # 环境检测 + HANA 凭证加载
├── hana_service.py        # HANA 连接 + HanaDB 向量库工厂
├── llm_service.py         # LLM + embeddings 工厂（AI Core 代理）
├── init_aicore.py         # AI Core / Generative AI Hub 环境变量初始化
├── test.py                # 连通性自检（env / hana / llm / rag）
├── tools/                 # 所有 LangGraph @tool 定义统一在此
│   ├── __init__.py        #   单一 import surface
│   ├── knowledge_base.py  #   内部 HANA RAG 检索（参数化工厂）
│   ├── news_search.py     #   Tavily 实时新闻
│   ├── weather.py         #   Open-Meteo 当前天气（无 key）
│   └── wikipedia.py       #   English Wikipedia 摘要（无 key）
├── approuter/             # Node.js Approuter（XSUAA 入口）
│   ├── package.json
│   └── xs-app.json        #   开启 WebSocket 转发，Streamlit 才能渲染
├── xs-security.json       # XSUAA service 配置（scope / role-template / redirect）
├── manifest.yml           # Cloud Foundry 部署清单（backend + router）
├── requirements.txt
├── runtime.txt            # Python 3.13
├── .env.example           # 环境变量模板
├── .gitignore
├── .hanadb-config.json    # ⚠️ 本地/BAS 用，已 gitignore
└── .streamlit/
    └── config.toml
```

### 模块职责（依赖方向 ↓）

```
app.py ──┬──► auth_service.py        (CF 上每次请求做 JWT 校验)
         │
         └──► agent_service.py ──┬──► tools/  ──┬──► rag_service.py ──► hana_service.py
                                 │              ├──► (Tavily / Open-Meteo / Wikipedia)
                                 │              │
                                 ├──► llm_service.py
                                 ├──► prompts.py
                                 └──► init_aicore.py
                                                                                │
                       config.py ◄─────────────────────────────────────────────┘
```

- `rag_service` 是"纯算法"层，不感知 LangGraph / Streamlit；可单独 CLI 调用
- `tools/` 把所有 `@tool` 集中放在一处，添加新工具只动这一个目录
- `agent_service` 是"粘合层"，按 mode 选工具集 + 装配 LangGraph agent
- `auth_service` 独立，只做 XSUAA token 校验，UI / agent 层不关心
- `app.py` 只做 UI + JWT 网关

---

## 环境识别

`config.py` 在启动时自动识别：

| 环境 | 判定依据 | HANA 凭证来源 | 代理 |
|------|---------|--------------|------|
| `local` | 无 `VCAP_APPLICATION`、无 BAS 特征 | `.hanadb-config.json` | `USE_LOCAL_PROXY=1` 时启用 |
| `bas` | 存在 `WORKSPACE_ID` 或 `/home/user/projects/` | `.hanadb-config.json` | 忽略 |
| `cf` | 存在 `VCAP_APPLICATION` | `VCAP_SERVICES.hana[0].credentials` | 忽略 |

---

## Tools 与搜索 Modes

侧边栏的 `Search mode` 决定 LangGraph agent 这次会拿到哪些工具。

| Mode | 启用工具 | 选用 KB | 备注 |
|---|---|---|---|
| **Auto**（默认） | 4 个全部 | ✅ | LLM 自主决定调 1 个或多个 |
| Knowledge base only | `knowledge_base_search` | ✅ | 任何问题都先检索 KB |
| News search only | `tavily_search` | — | 实时新闻（过去一周） |
| Weather only | `get_weather` | — | Open-Meteo，先 geocode 再查天气 |
| Wikipedia only | `search_wikipedia` | — | English Wikipedia 摘要 |

四个工具的实现都在 `tools/` 下，添加新工具只需：

1. 在 `tools/<name>.py` 里写一个 `@tool` 函数（或返回 `@tool` 的工厂）
2. 在 `tools/__init__.py` re-export
3. 在 `agent_service.build_agent` 里按 mode 加进 `tools` 列表
4. 在 `prompts.build_agent_system_prompt` 里给 Auto / X-only 加描述

无需 API key 的 `weather` / `wikipedia` 适合零配置 demo；`tavily_search` 需要 `TAVILY_API_KEY`。

---

## 本地开发

### 1. 安装依赖

```bash
python -m venv .venv
.venv\Scripts\activate           # Windows
# source .venv/bin/activate      # macOS / Linux
pip install -r requirements.txt
```

> 注：本地推荐使用 Python 3.12 与 CF buildpack 保持一致。

### 2. 配置凭证

1. 复制 `.env.example` 为 `.env`，填入 AI Core / Tavily 凭证  
2. 把 HANA service key 的 JSON 保存为 `.hanadb-config.json`  
3. 如在企业网内需代理，设置 `USE_LOCAL_PROXY=1`

> ⚠️ 当前本地网络无法解析 HANA Cloud 主机名（DNS / IP 白名单限制）。本地只能测 LLM 部分，HANA RAG 需到 BAS 或 CF 运行。

### 3. 运行

```bash
# 跑自检（跳过 HANA）
python test.py --skip-hana

# 启动 Streamlit
streamlit run app.py
```

---

## SAP BAS 开发

### 1. 把项目打包上传

```bash
# 在本地项目根目录（确认 .hanadb-config.json 已存在）
tar --exclude='.venv' --exclude='__pycache__' --exclude='.git' -czf ChatOpenAI_rag.tgz .
```

在 BAS 里：`File → Open Workspace → Upload`，或用 `Terminal` 上传后解压。

### 2. 安装依赖

```bash
pip install --user -r requirements.txt
```

### 3. 配置 AI Core 与 Tavily

```bash
export TAVILY_API_KEY=tvly-xxx
# AI Core 二选一：
#  A) 存在 ~/.aicore/config.json
#  B) export AICORE_CLIENT_ID / AICORE_CLIENT_SECRET / AICORE_AUTH_URL / AICORE_BASE_URL
```

### 4. 连通性自检

```bash
python test.py
```

四项检查：env / hana / llm / rag，应该全部 OK。

### 5. 启动 Streamlit

```bash
streamlit run app.py --server.port 8080 --server.address 0.0.0.0
```

在 BAS 顶栏的 **Ports: Preview** 中打开 `8080` 端口。

---

## Cloud Foundry 部署

### 架构概览

```
浏览器
   │  https://<router>.cfapps.eu10-…
   ▼
Approuter (Node.js, public)         ← XSUAA OAuth2 入口；登录后拿 JWT
   │  forwardAuthToken: true
   │  WebSocket 必须开（Streamlit 依赖）
   ▼
Backend (Python/Streamlit, public)  ← 也有公开 route，但每次请求要校验 JWT
   │  app.py + auth_service.py
   │  bind: AI_Core, HanaDB, XSUAA
   ▼
SAP AI Core / HANA / Tavily / Open-Meteo / Wikipedia
```

为什么 backend 也是公开 route 而不是 `apps.internal`：CF 的 C2C 网络策略需要 `network.write` 权限，团队/学习账户通常没有。改成"公开 + 应用层 JWT 校验"等价安全：浏览器猜到 backend URL 直接访问会被 `auth_service.validate_authorization_header` 拦下。

### 1. 登录 + 确认 service 名称

```bash
cf login -a https://api.cf.eu10.hana.ondemand.com
cf services              # 确认 AI Core 与 HANA 实例名称
```

### 2. 创建 XSUAA 实例（一次性）

```bash
cf create-service xsuaa application rag-chatbot-yf-xsuaa -c xs-security.json
```

> 改了 `xs-security.json`（比如 step 2 加 scope）之后用 `cf update-service rag-chatbot-yf-xsuaa -c xs-security.json` 同步。**只是改 Python 代码不需要执行这步。**

### 3. 调整 manifest.yml

把 backend 的 `services:` 下的实例名改成你 Space 中实际名称：

```yaml
services:
  - AI_Core
  - HanaDB_SS222D0
  - rag-chatbot-yf-xsuaa   # backend 也绑定 XSUAA：用来读 VCAP credentials 校验 JWT
```

`manifest.yml` 同时声明两个应用：

| 应用 | 类型 | 路由 |
|---|---|---|
| `rag-chatbot-yf-backend` | Python buildpack（Streamlit） | 公开 cfapps.* |
| `rag-chatbot-yf-router` | Node.js buildpack（Approuter） | 公开 cfapps.*（用户从这里进） |

### 4. Approuter 配置要点

`approuter/xs-app.json` 必须开启 WebSocket，否则 Streamlit 永远停在灰色 skeleton：

```json
{
  "authenticationMethod": "route",
  "websockets": { "enabled": true },
  "routes": [
    { "source": "^/_stcore/stream$", "target": "/_stcore/stream",
      "destination": "rag-chatbot-backend",
      "authenticationType": "xsuaa", "csrfProtection": false },
    { "source": "^(.*)$", "target": "$1",
      "destination": "rag-chatbot-backend",
      "authenticationType": "xsuaa", "csrfProtection": false }
  ]
}
```

`xs-security.json` 的 `oauth2-configuration.redirect-uris` 必须包含 router 的公开 URL（`/**`），否则 SSO 跳转会失败。

### 5. 推送

```bash
cf push                                                # 推送两个应用
cf set-env rag-chatbot-yf-backend TAVILY_API_KEY tvly-xxx
cf restage rag-chatbot-yf-backend
```

之后只改 Python 代码再 push 时：

```bash
cf push rag-chatbot-yf-backend -f manifest.yml         # 只推 backend
# 改了 approuter/xs-app.json 才需要：
cf push rag-chatbot-yf-router  -f manifest.yml
```

### 6. 验证

```bash
cf app rag-chatbot-yf-router       # 拿 router 的公开 URL
```

打开浏览器访问 router URL：

1. 跳转到企业身份源（IAS / 企业 IdP）登录
2. 登录成功 → Streamlit 加载（约 20–40s 首次冷启动）→ 页面底部显示 `env=cf · signed in as <你的名字>`

直接访问 backend URL（绕过 router）应该立即看到红色 **🔒 Unauthorized** 卡，因为没有 JWT。

> Step 2（基于 BTP Subaccount Role 的访问控制）会在 `xs-security.json` 加 scope，给 approuter 的 route 加 `"scope"` 校验，并在 BTP Cockpit 创建 Role Collection 分配给用户/组。

---

## 故障排查

| 症状 | 原因 | 解决 |
|------|------|------|
| `Cannot resolve host name ...hanacloud.ondemand.com` | 本地不在 HANA IP 白名单 | 改到 BAS 运行，或让管理员添加本地公网 IP |
| `hdbcli.dbapi.Error: ... rc=11001` | DNS / 网络不通 | 同上 |
| `AI Core configuration not found` | 环境变量 / VCAP / 本地 config.json 都没有 | 见 `init_aicore.py` 顶部注释 |
| `TAVILY_API_KEY is not set` | 本地 `.env` 缺 key 或 CF 未 set-env | `.env` 加 `TAVILY_API_KEY=...` 或 `cf set-env` |
| 本地网络请求失败但公司环境 | 企业代理未开启 | `set USE_LOCAL_PROXY=1` |
| 走 router 登录后页面只剩灰 skeleton | approuter 没开 WebSocket | `xs-app.json` 加 `"websockets": { "enabled": true }`，重推 router |
| 登录后 SSO 跳转失败 / `redirect_uri` 错误 | `xs-security.json.oauth2-configuration.redirect-uris` 没含 router URL | 修正后 `cf update-service rag-chatbot-yf-xsuaa -c xs-security.json` |
| 直接访问 backend URL 没看到 Unauthorized 卡 | 等不够久 | 第一次访问要等 `init_aicore` 之前的 auth gate 触发；现在已经把 auth 提到最前，应该秒级响应 |
| `ERR_TOO_MANY_REDIRECTS` 进 router | `xs-app.json` 里有 `"welcomeFile": "/"` | 移除该字段 |

---

## HANA 对象说明

当前 `.hanadb-config.json` 指向的是 **Schema service instance**（`USR_xxx` 技术用户），适合向量表这种应用数据存储。

如果需要使用 HDI Container（`HanaDB_SS222D0.json`），两者任选其一即可，`config.py` 只认 `.hanadb-config.json` 文件名——需要切换时重命名覆盖即可。

---

## 许可证 / Author

UUS1SGH
