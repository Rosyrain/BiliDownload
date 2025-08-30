# BiliDownload 配置文件使用说明

## 配置文件概述

BiliDownload 现在使用统一的配置文件 `config.ini` 来管理所有设置，包括分类配置。不再需要单独的 `categories.json` 文件。

## 快速开始

1. **复制配置文件模板**：
   ```bash
   cp config_template.ini config.ini
   ```

2. **编辑配置文件**：
   使用任何文本编辑器打开 `config.ini` 文件

3. **重启程序**：
   修改配置后重启程序即可生效

## 配置文件结构

### [GENERAL] 节 - 基本设置
```ini
[GENERAL]
# 默认下载路径 (相对于项目根目录)
download_path = ./data/default
# FFmpeg 可执行文件路径
ffmpeg_path =
# 最大并发下载数
max_concurrent_downloads = 3
# 是否自动创建分类文件夹
auto_create_categories = true
# 默认分类名称
default_category = default
```

### [UI] 节 - 界面设置
```ini
[UI]
# 界面主题 (light/dark)
theme = light
# 窗口宽度
window_width = 1600
# 窗口高度
window_height = 1000
# 界面语言
language = zh_CN
```

### [DOWNLOAD] 节 - 下载设置
```ini
[DOWNLOAD]
# 下载块大小 (字节)
chunk_size = 8192
# 网络请求超时时间 (秒)
timeout = 30
# 下载失败重试次数
retry_count = 3
# 请求间隔时间 (秒)
delay_between_requests = 1
# 是否启用断点续传
enable_resume = true
# 下载进度更新频率 (毫秒)
progress_update_interval = 500
```

### [CATEGORIES] 节 - 分类配置
```ini
[CATEGORIES]
# 分类配置 - 格式：分类名 = 相对路径
# 支持多级分类，用 / 分隔
default = default
video = video
music = music
document = document

# 可以添加更多自定义分类
# tutorial = video/tutorial
# podcast = music/podcast
# ebook = document/ebook
```

### [ADVANCED] 节 - 高级设置
```ini
[ADVANCED]
# 是否启用详细日志
verbose_logging = false
# 日志文件最大大小 (MB)
max_log_size = 10
# 日志保留天数
log_retention_days = 30
# 是否启用代理
use_proxy = false
# 代理服务器地址
proxy_host =
# 代理服务器端口
proxy_port =
# 是否启用调试模式
debug_mode = false
```

## 分类系统说明

### 分类路径规则
- 分类路径相对于 `./data/` 目录
- 支持多级嵌套，用 `/` 分隔
- 程序会自动创建对应的文件夹结构

### 示例分类结构
```
data/
├── default/           # 默认分类
├── video/             # 视频分类
│   └── tutorial/      # 视频教程子分类
├── music/             # 音乐分类
│   └── podcast/       # 播客子分类
└── document/          # 文档分类
    └── ebook/         # 电子书子分类
```

### 添加自定义分类
1. 在 `[CATEGORIES]` 节中添加新行
2. 格式：`分类名 = 路径`
3. 例如：`tutorial = video/tutorial`
4. 保存文件并重启程序

### 删除分类
1. 从 `[CATEGORIES]` 节中删除对应行
2. 注意：不能删除 `default` 分类
3. 保存文件并重启程序

## 系列视频下载

当启用系列视频下载时，程序会：
1. 自动提取系列名称
2. 在选择的分类目录下创建系列文件夹
3. 将所有分P视频下载到该文件夹中

### 系列文件夹命名规则
- 自动从视频标题中提取系列名称
- 移除分P标识（如 "第1P"、"Part 1" 等）
- 清理特殊字符和多余空格

## 注意事项

1. **配置文件位置**：`config.ini` 应放在程序根目录
2. **路径分隔符**：Windows 和 Unix 系统都使用 `/` 作为路径分隔符
3. **编码格式**：配置文件使用 UTF-8 编码
4. **备份建议**：修改配置前建议备份原文件
5. **权限要求**：程序需要写入权限来创建目录结构

## 故障排除

### 常见问题
1. **配置不生效**：检查文件编码是否为 UTF-8
2. **目录创建失败**：检查程序是否有写入权限
3. **分类路径错误**：确保路径格式正确，使用 `/` 分隔

### 重置配置
如果配置文件损坏，可以：
1. 删除 `config.ini` 文件
2. 重启程序，会自动创建默认配置

## 版本兼容性

- 新版本完全兼容旧的 `config.ini` 格式
- 自动迁移 `categories.json` 中的分类配置
- 向后兼容所有现有设置
