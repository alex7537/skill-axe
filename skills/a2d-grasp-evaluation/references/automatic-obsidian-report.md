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

## 静态看板归档（2026-09-20）

独立仓库 `<github-owner>/a2d-eval` 已承接 observer 与 `dashboard/export_report.py`。新任务核对实际调用的是包含静态导出钩子的版本；旧进程不会自动升级。

- 完成、暂停或中断：先生成本地/Ob报告及 auto_report_status.json，再由同一快照导出 static_report。成功/有效/无效须逐项相等，不重新解释成功判据。
- 核对 static_report 的 results.json、REPORT.md 与原报告；缺失训练数据类型标待核实，不能从测试场景猜测。
- 同事部署整个静态目录，无需原始测试环境。静态快照标明归档时间和批次状态，不显示实时运行承诺。
- 上传前核对明确的目标仓库/分支和授权，记录提交 SHA；未推送就明确标记“本地已归档、待发布”。上传失败保留归档，不能影响测试任务。
- 当前钩子适用于本仓库 observer 的多场景 schema；其他 runner 单独验证适配，不声称所有历史任务自动生效。

## 已授权自动发布（2026-09-22）

用户已授权本机 A2D 测试终态快照自动发布至 `https://github.com/<github-owner>/a2d-eval.git` 的 main。后续本机任务挂载 observer 时默认添加 `--publish-remote https://github.com/<github-owner>/a2d-eval.git --publish-branch main`，无需每批重复询问。此授权仅限测试报告/静态结果，不扩展到权重、视频或其他仓库。

验收时检查 `publish_status.json` 的 state=published、commit及远端分支；不能把静态文件生成当作上传成功。上传器保留远端其他批次和训练数据，更新单批次及 reports/latest；失败最多重试3次，保留报告并明确待补传。旧 runner 必须适配或补传；skill 本身不是后台任务。
