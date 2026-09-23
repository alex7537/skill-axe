---
name: linux-perf-diagnosis
description: Diagnose Linux process CPU hotspots using top, pidstat, strace and perf. Use for perf installation, sampling failures, call-chain interpretation and mapping hotspots to application code, including ARM64 Tegra real-time kernels and ROS 2 processes. Trigger on CPU 占用高、进程性能分析、热点定位 or perf 报告解读. Do not use as a general network, PLC handshake, GPU-kernel or off-CPU latency diagnosis skill.
---

# Linux 进程 CPU 性能排查

将 PID、截图、perf 文本或源码转化为可验证的热点结论及最短的下一步命令。默认中文，随用户语言调整。完整步骤见 [性能排查手册](references/guide.md)：安装看第 2 节，采样看第 1、3–4 节，解读看第 5–6 节，故障处理看第 7 节。

## 知识树归属与协作

归属：工程基础设施 → 运行排障（Runbooks）→ Linux 进程 CPU 性能分析。此技能是采样、热点解读与同负载验证流程的唯一维护入口。

- 网络成员、路由或 ZeroTier 链路异常 → `zerotier-diagnose`。
- TI-ONE SSH 端点、主机指纹或登录失败 → `tione-ssh-diagnose`；连接恢复后再对目标 Linux 进程采样。
- 已定位热点，但需理解业务调用关系 → 按需结合 `understand-codebase`；学习源码时可结合 `code-understanding-coach`。这些是可选协作技能，不是执行本技能的前置要求。
- CPU 低但响应慢，或 PLC 的 ACK/完成信号不一致 → 先收集等待、协议状态和时间线证据；不凭 CPU 采样推断网络、硬件或状态机根因。本技能不覆盖完整 off-CPU、GPU 或 PLC 诊断。

接入审阅日期：2026-09-18。来源为用户提供的 `linux-perf-diagnosis` 技能包（手册整理于 2026-09-17）；本次检查技能结构、职责和命令片段语法，未在 Linux/ROS 2/Tegra 上复测历史案例。

## 工作方式

1. 确认目标环境。远程 Linux 输出不意味着当前终端就在远程机器；不要在本地工作站操作远程 PID。利用已有发行版、内核、架构、PID 和成功的 perf 路径/事件/栈方式，不重复询问。
2. 初学者每轮给 1–3 个复制块。统一使用 `TARGET_PID`、`PERF_BIN`、`PERF_EVENT`、`RUN_DIR`；说明修改项、运行位置、时长及发回哪个文件。不固定历史 PID 或内核版本，不自动选第一个 perf 二进制。
3. 安装按发行版。Ubuntu 的 perf 可能只是按内核版本查找程序的脚本；定制内核缺包时，可尝试同架构、接近内核版本的仓库工具，绝对路径调用并验证。不保证跨版本兼容，不为普通采样建议更换实时内核。
4. 先找忙线程，再采整个进程。`-p` 是进程，`-t` 是指定线程。主线程 CPU=0 不代表进程空闲。重启后更新 ID。
5. 优先沿用已验证的事件和栈方式。可从 `cycles` 加 `fp` 起步，帧指针缺失时用 `dwarf`；事件失败先去掉调用栈，分别短测 `cycles` 与 `cpu-clock`。`stat` 成功不代表 `record` 可用。
6. 先给不带调用链的 Self 和 Children 排行，再展开重点路径或按 TID 分析。已有完整数据先重新 report，不重复 record。避免第一条长调用链截断其余热点。
7. 每项结论注明证据、采样范围和待确认假设。只在调用链/代码支持时归因到业务入口。有源码后提出最小修改和同负载验证，不把诊断扩展为生产配置修改。

## 分析边界

- top 默认单核 100%；整机 sy/wa/load 不是目标进程指标；load 包含不可中断等待；线程 RES 不能累加。
- perf cycles 百分比是采样估计的周期分布，不是整机 CPU 或墙钟延迟。Self 是落点；Children 含下层调用，父子不能相加。过滤可能改变分母。
- strace -c 默认内核 CPU 时间，-w 才是包含等待的墙钟时间。错误数、futex 时间和锁热点不能单独证明故障/锁竞争。短时使用 strace，与 perf 基线分开。
- sleep 链上的时钟热点表示执行相关代码时耗 CPU，不是睡眠时长；没有源码、频率证据不要断言忙循环。
- 裸地址不只是缺符号；区分符号解析、栈截断、展开信息缺失、二进制不匹配和 ARM64 PAC。异常高位地址只能提示 PAC，不能确诊。增大 DWARF 栈一次仍无效，换方法或检查环境。
- SQLite、锁和分配并列出现不等于同一调用路径。N+1、重复 prepare、轮询和关节名双重循环必须验证。
- 不把关闭 SQLite 线程安全、降低控制频率、改 QoS/clocksource 或放宽权限作为未经验证的快捷修复。

## 收尾

结论先行，附关键数值及简短业务调用链。数据不足时指出具体缺失的是全文、线程、栈还是源码，索取最小补充。优化后比较相同负载的 CPU、吞吐/延迟及相关实时 deadline/抖动；不能只凭热点占比下降宣告成功。最终交付热点路径、置信程度、改进建议与验证方法。不声称在无法连接的远程机器上完成操作。
