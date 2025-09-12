# 简介
stepfundemo 用于测试 StepFun 开放平台的 API，涵盖语音、图像、聊天、文件、知识库等单个功能及各类最佳实践。

对应文档：StepFun 官方文档 https://platform.stepfun.com/docs/overview/quickstart

更新时间：2025年9月10日




# 前置条件

- 需拥有 StepFun 开放平台账户。
- Python 3.8 及以上版本
- Jupyter Notebook 6.5.2

# 测试内容
- [Agent_Solutions]agent应用【需要更新】
- [Basic_Samples] 用于集成到应用中的小型代码示例和片段。【基于欧文的代码样例，已完成】
- [Optimal_Practice] 针对特定场景和功能的最佳实践。【更新中 3/16】



# 快速开始准备

## 安装python包
使用以下命令安装 `requirements.txt` 中列出的所有 Python 模块和包：

```bash
pip install -r requirements.txt
```

## 设置环境变量

将你的 API 密钥添加到环境变量中：

- **变量名**: `STEPFUN_API_KEY`
- **变量值**: 你的 API 密钥

> API 密钥可从 [StepFun 接口密钥管理页面](https://platform.stepfun.com/interface-key) 获取

### Windows 用户

在命令提示符或 PowerShell 中执行：

```bash
setx STEPFUN_API_KEY "你的真实API密钥"
```


### macOS/Linux 用户

#### 确认当前使用的 shell

```bash
echo $SHELL
```

- 若输出 `/bin/bash` → 使用 bash，配置文件为 Linux 的 `~/.bashrc` 或 macOS 旧版的 `~/.bash_profile`。
- 若输出 `/bin/zsh` → 使用 zsh（macOS 10.15+ 默认 shell），配置文件为 `~/.zshrc`。


#### 打开配置文件：
以 macOS 常用的 zsh 为例,在终端输入以下命令，用系统自带的 nano 编辑器打开 `~/.zshrc`：
```bash
nano ~/.zshrc
```

#### 添加环境变量
1. 在打开的编辑器中，用方向键滑到文件末尾，粘贴以下内容（需将 `"你的真实API密钥"` 替换为你从 StepFun 平台获取的实际密钥）：
   ```bash
   # 设置 STEPFUN API 密钥（永久生效）
   export STEPFUN_API_KEY="你的真实API密钥"
   export STEPFUN_ENDPOINT="https://api.stepfun.com/v1"
   export STEPFUN_WSS_ENDPOINT="wss://api.stepfun.com/v1"
   ```


> 注意：密钥前后的引号需保留，且不要有多余空格。

2. 保存并退出
按以下步骤操作（以 nano 编辑器为例）：
- 按 `Control + O`（字母 O，非数字 0）；
- 按回车键确认保存路径；
- 按 `Control + X` 退出编辑器。


3. 使配置立即生效
在终端输入以下命令（根据所用 shell 选择对应命令）：
- 若用 zsh：`source ~/.zshrc`
- 若用 bash（Linux 或 macOS 旧版）：
  - Linux 系统：`source ~/.bashrc`
  - macOS 旧版 bash 系统：`source ~/.bash_profile`


#### 验证配置
1. 关闭当前终端，重新打开一个新终端；
2. 在新终端中输入 `echo $STEPFUN_API_KEY`；
3. 若输出你的 API 密钥，说明配置已永久生效（重启电脑后仍可正常读取）。




