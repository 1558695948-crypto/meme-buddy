# Meme Buddy

让桌面 AI 根据语境选择、展示与管理表情包的 Agent Skill。包含本地图片导入、去重、待标注队列、结构化检索及反馈偏好；生成图片与发送消息由宿主实际提供的工具完成。

## 安装

将仓库中的 `meme-buddy` 文件夹复制到 Agent 的 Skills 目录。例如 Codex：`~/.codex/skills/meme-buddy/`。需要 Python 3.9 或更新版本。

示例：

> 使用 meme-buddy 导入这个文件夹里的表情包，帮我看图标注。

> 开启自然表情模式，合适时配一张图回复。

启用范围取决于宿主对会话与 Skill 的支持；Skill 本身没有常驻聊天监听程序。

## 随附表情包

`sample-pack/` 包含 13 张已查看、标注的网络反应图，以及逐图来源和权利状态。导入到自己的本地图库：

```bash
python3 tools/import_sample_pack.py
```

该命令依次调用 Skill CLI，将图片复制到 `~/.meme-buddy/` 并导入标注。已有图片会按 SHA-256 去重，不带任何用户聊天、联系人或使用统计。

这些图片属于第三方素材，不因收录在本仓库而获得新的授权。部分来源的商业使用及再分发权尚未核实；具体见 `sample-pack/manifest.json`，不能将示例图片当成已授权的商业素材包。作者如需更正或移除，可通过仓库 Issue 联系维护者。

## 当前能力范围

- 本地 PNG/JPEG/WebP/GIF 导入与精确字节去重；
- 宿主看图理解梗和反讽，CLI 保存标注；
- 关键词和结构化标签召回，由 Agent 结合语境选择；
- 明确喜欢/不喜欢与使用统计分离，可清除反馈；
- 当前聊天展示图片，或在用户指定后使用宿主已有的外部消息工具。

当前没有 embedding 检索、感知去重或内置微信/飞书发送器。CLI 无网络依赖，库写入应顺序执行。

## 验证

```bash
python3 meme-buddy/scripts/test_meme_buddy.py
```
