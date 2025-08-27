# 测试文件

本文件夹包含项目的测试文件，用于验证各个模块的功能和配置。

## 测试文件说明

- `test_imports.py` - 测试模块导入和基本组件初始化
- `test_logger.py` - 测试日志系统功能
- `test_ffmpeg_config.py` - 测试FFmpeg配置读取和保存

## 运行测试

```bash
# 测试模块导入
python3 test/test_imports.py

# 测试日志系统
python3 test/test_logger.py

# 测试FFmpeg配置
python3 test/test_ffmpeg_config.py
```

## 注意事项

- 测试文件主要用于开发阶段验证功能
- 运行测试前请确保已安装所有依赖
- 某些测试可能需要正确的配置文件才能正常运行 