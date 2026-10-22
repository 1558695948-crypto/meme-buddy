# Meme Buddy

让桌面 AI 根据语境选择、展示与管理表情包的 Agent Skill。包含本地图片导入、去重、待标注队列、结构化检索及反馈偏好；生成图片与发送消息由宿主实际提供的工具完成。

## 安装

将仓库中的 `meme-buddy` 文件夹复制到 Agent 的 Skills 目录。例如 Codex：`~/.codex/skills/meme-buddy/`。需要 Python 3.9 或更新版本。

示例：

> 使用 meme-buddy 导入这个文件夹里的表情包，帮我看图标注。

> 开启自然表情模式，合适时配一张图回复。

启用范围取决于宿主对会话与 Skill 的支持；Skill 本身没有常驻聊天监听程序。

首次使用时，AI会参考当前可见的对话，自行搜集一批它喜欢且适合双方聊天的表情，最多20张，不必凑满。检查、标注入库后保存完成状态，后续不重复初始化。没有搜索能力时会说明并暂缓；不会把私人对话原文发送给搜索网站。用户导入的素材包不受这20张上限限制。

## 随附表情包

`sample-pack/` 包含 13 张已查看、标注的网络反应图，以及逐图来源和权利状态。导入到自己的本地图库：

```bash
python3 tools/import_sample_pack.py
```

该命令依次调用 Skill CLI，将图片复制到 `~/.meme-buddy/` 并导入标注。已有图片会按 SHA-256 去重，不带任何用户聊天、联系人或使用统计。

这些图片属于第三方素材，不因收录在本仓库而获得新的授权。部分来源的商业使用及再分发权尚未核实；具体见 `sample-pack/manifest.json`，不能将示例图片当成已授权的商业素材包。作者如需更正或移除，可通过仓库 Issue 联系维护者。

## MoSo 通用表情包

`moso-pack/` 包含32枚 MoSo 原创衍生表情，统一白色折纸兔头、黑西装与橙色背景。每枚384×384，约18–28 KB；`overview.jpg` 提供总览。第26枚“回头见”已修正挥手手臂连接。母版和独立修正版均保留，可通过构建脚本重新导出。

```bash
python3 tools/import_sample_pack.py --pack moso-pack
```

此包由用户提供的 MoSo 形象参考生成并授权上传。第三方商业使用或再分发需另行取得权利方许可。

## 当前能力范围

- 本地 PNG/JPEG/WebP/GIF 导入与精确字节去重；
- 宿主看图理解梗和反讽，CLI 保存标注；
- 关键词和结构化标签召回，由 Agent 结合语境选择；
- 明确喜欢/不喜欢与使用统计分离，可清除反馈；
- 当前聊天展示图片，或在用户指定后使用宿主已有的外部消息工具。

当前没有 embedding 检索、感知去重或内置微信/飞书发送器。CLI 无网络依赖，库写入应顺序执行。

自主表达更新：AI自己决定用图时机、数量与是否复用。`catalog` 提供可分页的紧凑目录与真实路径，`get` 支持按ID批量取图；搜索不再按喜好或近期使用扣分。emotion/intent/relationship只有显式传入才精确过滤。中文召回仍依赖标签与Agent语境理解，不保证理解所有否定或反讽。

```bash
python3 meme-buddy/scripts/meme_buddy.py catalog --tag MoSo --limit 20
python3 meme-buddy/scripts/meme_buddy.py search --query '思考'
python3 meme-buddy/scripts/meme_buddy.py get <图片ID>
```

## 验证

```bash
python3 meme-buddy/scripts/test_meme_buddy.py
```
