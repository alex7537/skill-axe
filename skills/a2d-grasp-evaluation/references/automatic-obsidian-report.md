# 自动测试报告：由测评仓库维护

## 职责与入口

- 唯一实现：`flow-matching-test-a2d-v2` 测评分支 `feat/a2d-eval-loop-v0` 的 `tools/a2d_eval_loop/watch_eval_to_obsidian.py`。
- 格式、输出与恢复说明：同仓库 `tools/a2d_eval_loop/docs/AUTO_REPORT.md`。遇到报告功能变更，在仓库修改并测试；不要往 skill 复制实现。
- 本 skill 负责启动前核对、默认挂载报告监控、验收同步和异常后补档。

## 本机配置

将 `config.example.json` 复制为本 skill 根目录的 `config.json`，填写 `eval_repo` 为已经核对的测评 checkout；或设置环境变量 `A2D_EVAL_REPO`。配置仅本机保存，不提交。不要自动切换正在使用的 checkout 分支。

推荐直接调用仓库脚本；旧命令 `python3 scripts/watch_eval_to_obsidian.py --batch <run> --vault <vault>` 仍可使用，该文件只有转发逻辑。不要把兼容入口当作第二份实现。

## 默认操作与验收

1. 新测试或恢复时核对批次、模型、冻结计划及确切 vault；读取仓库文档确认日志 schema。
2. 启动独立报告 observer，将日志、PID、实际 argv 写到该批次；这一步不能只写进 skill 而不执行。
3. 核对首份本地 `AUTO_REPORT.md` 与 vault `自动报告_<批次名>.md` 一致，索引链接存在且 observer 存活。
4. 报告开头使用“本轮目标与参数”简表，随后展示结果。参数来自冻结计划，缺失不猜测；修改目标时新建批次，不改写历史配置。
5. 完成或中断后核对终态已同步；整机断电或 observer 被关闭时，恢复后先用 `--once` 补档，再按需挂载 observer。暂停和异常不能冒充完整完成。
6. 发布代码、上传 GIF 或启动下一轮训练是独立行动；报告同步本身不授权这些操作。

只改变报告展示时，不重启 evaluator/server；若需更新 observer，先核对其 PID 与命令，只替换该 observer。不要修改原始测试记录或成功判据。
