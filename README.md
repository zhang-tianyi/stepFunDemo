# Introduction
stepfundemo用于测试stepfun开放平台的api，包括语音、图像、chat、file、知识库等单个功能和各种最佳实践。
对应：stepfun官方文档 https://platform.stepfun.com/docs/overview/quickstart

更新时间：20250904

## Installation
Install all Python modules and packages listed in the requirements.txt file using the below command.

```python
pip install -r requirements.txt
```

## Prerequisites
stepfun开放平台账户

### For getting started:
- Add "STEPFUN_API_KEY" as variable name and \<Your API Key Value\> as variable value in the environment variables.
<br>
One can get the STEPFUN_API_KEY value from the https://platform.stepfun.com/interface-key 
 <br>
 Steps to set the key in the environment variables:        

      WINDOWS Users: 
         setx STEPFUN_API_KEY "REPLACE_WITH_YOUR_KEY_VALUE_HERE"

      MACOS/LINUX Users: 
         export STEPFUN_API_KEY="REPLACE_WITH_YOUR_KEY_VALUE_HERE"

第一步：确认你的终端 shell
先确定当前使用的是 bash 还是 zsh（两种 shell 的配置文件不同）：
在终端输入以下命令，按回车：
```bash
echo $SHELL
```

若输出 /bin/bash → 用 bash，配置文件是 ~/.bashrc（Linux）或 ~/.bash_profile（macOS 旧版）。
若输出 /bin/zsh → 用 zsh（macOS 10.15+ 默认 shell），配置文件是 ~/.zshrc。
第二步：修改配置文件（以 zsh 为例，最常用）
以 macOS 默认的 zsh 为例，步骤如下：
打开配置文件
在终端输入以下命令，用系统自带的 nano 编辑器打开 ~/.zshrc（简单易操作）：
```bash
nano ~/.zshrc
```
添加环境变量命令
在打开的 nano 编辑器中，按「下箭头」滑到文件末尾，粘贴以下内容（替换为你的真实密钥）：
```bash
# 设置 STEPFUN API 密钥（永久生效）
export STEPFUN_API_KEY="你的真实API密钥"
export STEPFUN_ENDPOINT="https://api.stepfun.com/v1"
export STEPFUN_WSS_ENDPOINT="wss://api.stepfun.com/v1"
```

注意：密钥前后的引号要保留，且不要有多余空格。
保存并退出 nano
按 Control + O（字母 O，不是数字 0）→ 按「回车」确认保存。
按 Control + X 退出编辑器，回到终端。
第三步：让配置立即生效（无需重启终端）
修改配置文件后，需让系统加载新配置，在终端输入以下命令：
若用 zsh：
```bash
source ~/.zshrc
```
若用 bash（Linux 或 macOS 旧版）：
```bash
source ~/.bashrc  # Linux
# 或
source ~/.bash_profile  # macOS 旧版 bash
```

第四步：验证永久生效
关闭当前终端，重新打开一个新终端。
输入 echo $STEPFUN_API_KEY，若输出你的密钥，说明永久生效（重启电脑后也能正常读取）

## Solutions
- [**Agent Solutions**]
- [**Basic Samples**] Small code samples and snippets for integration into your applications.
- [**Optimal Practice**]: Complete solutions for specific use cases and industry scenarios.

## Requirements
Python 3.8+
Jupyter Notebook 6.5.2