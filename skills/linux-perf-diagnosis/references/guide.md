# Linux 进程性能排查手册：从 top 到 perf

适用：Linux CPU 热点分析，含 Ubuntu、Debian、Fedora、ARM64 / Tegra 实时内核和 ROS 2 案例。

整理日期：2026-09-17。命令在**运行目标进程的 Linux 机器**上，用 Bash 或兼容 shell 执行。本文是操作手册，不代表已在你的机器上运行。

## 目录

1. 快速操作：改 PID、采样、导出
2. perf 安装与 Tegra 特殊情况
3. top / pidstat：谁在忙
4. perf：事件、线程、调用栈
5. 解读报告
6. 三个实际案例
7. 常见报错
8. strace 辅助分析
9. 优化验证与交接
10. 技能使用与资料来源

## 1. 快速操作：改 PID、采样、导出

前提：perf 已安装。尚未安装先看第 2 节。以下变量只在当前终端生效，新开终端需重新设置。

### 第一步：设置目标

修改第一行 PID。正常安装用 `PERF_BIN=perf`；Tegra 找不到内核对应版本时，改成第 2 节找到的绝对路径。

```bash
TARGET_PID=1985199
PERF_BIN=perf
PERF_EVENT=cycles
CALL_GRAPH=fp
RUN_DIR="/tmp/perf-${TARGET_PID}-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$RUN_DIR"
ps -p "$TARGET_PID" -o pid,comm,args
"$PERF_BIN" --version
```

`ps` 只有表头说明 PID 已失效；先找新 PID。重启程序后也要更新 TID。

### 第二步：采 30 秒

保持需要分析的业务负载，等待自动结束。`-p` 采整个进程的线程。

```bash
sudo "$PERF_BIN" record \
  -o "$RUN_DIR/perf.data" \
  -e "$PERF_EVENT" -F 99 \
  -p "$TARGET_PID" \
  --call-graph "$CALL_GRAPH" -- sleep 30
```

`cycles + fp` 是起点，不保证所有机器适用。事件报错看第 7 节，调用栈不完整看第 4 节。实时系统先在可接受的测试窗口短时低频采样，记录对控制周期的影响。

### 第三步：导出三份报告

```bash
sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" \
  --stdio --no-inline --no-children --call-graph none \
  --percent-limit 0.5 > "$RUN_DIR/self.txt"

sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" \
  --stdio --no-inline --children --call-graph none \
  --percent-limit 2 > "$RUN_DIR/children.txt"

sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" \
  --stdio --no-inline --no-children \
  --call-graph graph,0.5,caller --percent-limit 1 \
  > "$RUN_DIR/callers.txt"

head -n 65 "$RUN_DIR/self.txt"
head -n 65 "$RUN_DIR/children.txt"
printf '\n报告目录：%s\n' "$RUN_DIR"
```

先发 `self.txt`、`children.txt`，需要时再发完整 `callers.txt`。不要只截取调用链报告的前几十行：第一条热点就可能占几百行，把其他热点遮住。

## 2. perf 安装与 Tegra 特殊情况

### 2.1 确认系统

```bash
cat /etc/os-release
uname -r
uname -m
```

容器中 `uname` 显示宿主机内核；容器源可能没有对应工具。宿主机采样使用宿主机 PID，还需考虑容器权限和 PID 命名空间。

### 2.2 Ubuntu

标准 Ubuntu 内核优先安装匹配工具：

```bash
sudo apt update
sudo apt install linux-tools-common "linux-tools-$(uname -r)"
```

`linux-tools-common` 可能只提供启动脚本及公共文件，安装它不等于已有可用的 perf 二进制。

### 2.3 Debian / Fedora

Debian：

```bash
sudo apt update
sudo apt install linux-perf
```

Fedora：

```bash
sudo dnf install perf
```

其他发行版先查本发行版软件包，不套用 Ubuntu 包名。

### 2.4 Tegra / 实时内核缺包

本次使用 `6.8.12-rt-tegra`，曾出现：

```text
WARNING: perf not found for kernel ...
Unable to locate package linux-tools-...-tegra
```

这是启动脚本查找/包缺失问题，还没有开始采样。脚本提示的包名不一定存在，不必反复尝试。

可以安装仓库的通用工具，直接调用二进制：

```bash
sudo apt update
sudo apt install linux-tools-generic
find /usr/lib -path '*linux*tools*' -name perf -executable 2>/dev/null
```

从输出选择同架构、尽量接近运行内核版本的实际路径。下面只是示例，**必须替换成 find 的实际输出**：

```bash
PERF_BIN=/usr/lib/linux-tools/6.8.0-139-generic/perf
"$PERF_BIN" --version
sudo "$PERF_BIN" stat -e cpu-clock -- sleep 1
```

这通常无需更换/重启内核，但跨版本兼容性仍需验证。`stat` 成功不代表 `record` 采样可用。若仍不兼容，再考虑供应商工具或匹配内核源码的 `tools/perf` 构建方式。

继续使用 `"$PERF_BIN"`，直接输入 `perf` 可能再次走原来的启动脚本。不要覆盖 `/usr/bin/perf`。

## 3. top / pidstat：谁在忙

```bash
top -H -p "$TARGET_PID"
```

`P` 按 CPU 排序，`M` 按内存排序，`1` 展开各 CPU，`H` 切换线程，`q` 退出。

| 现象 | 正确理解 |
|---|---|
| 进程 CPU 130% | 默认模式下约占 1.3 个逻辑 CPU，不是整机满载 |
| 主线程 0%，工作线程忙 | 仍应采整个进程或繁忙线程 |
| S 状态但 CPU 高 | 状态是刷新瞬间，CPU 是区间统计 |
| 各线程 RES 相同 | 共享地址空间，不能累加 |
| 顶部 sy、wa | 整机指标，不能归到指定 PID |
| load 高 | 包含可运行及不可中断等待任务，结合核数及 CPU 空闲率分析 |
| VIRT 大 | 虚拟地址空间大，不等于实际物理内存使用量 |

看用户态、内核态和线程：

```bash
pidstat -t -u -p "$TARGET_PID" 1
```

Ctrl-C 结束。`pidstat` 来自 `sysstat` 包，例如 Ubuntu/Debian 用 `sudo apt install sysstat`。用户态高查业务热点；内核态高查系统调用、网络、读时钟等。CPU 低但响应慢，可能是在等待，on-CPU 采样不能解释全部延迟。

已知 TID 查进程 PID：

```bash
TARGET_TID=1985462
awk '/^(Name|Tgid|Pid):/' "/proc/$TARGET_TID/status"
```

`Tgid` 是进程 ID，`Pid` 是当前线程 ID。

## 4. perf：事件、线程、调用栈

### 4.1 范围与事件

- `-p "$TARGET_PID"`：整个进程的线程。
- `-t 线程ID1,线程ID2`：只看指定线程；结果不代表整个进程。
- `cycles`：硬件周期事件。
- `cpu-clock`：软件事件，但并非任何内核都支持其采样。

事件报错时，不带调用栈分别短测：

```bash
sudo "$PERF_BIN" record -o "$RUN_DIR/probe-cycles.data" \
  -e cycles -F 49 -p "$TARGET_PID" -- sleep 3
sudo "$PERF_BIN" record -o "$RUN_DIR/probe-clock.data" \
  -e cpu-clock -F 49 -p "$TARGET_PID" -- sleep 3
```

成功后将 `PERF_EVENT` 设成可用事件，回第 1 节正式采样。不带栈成功、带栈失败时，应检查调用栈支持，不是反复安装工具。

### 4.2 fp / dwarf

| 方式 | 条件与限制 |
|---|---|
| `fp` | 依赖程序/库保留帧指针，本次 Tegra 案例能追到业务入口 |
| `dwarf` | 使用展开信息和用户栈快照；省略帧指针时常有帮助；依赖工具展开支持 |
| `dwarf,32768` | 默认 8192 字节快照可能不足时，增大作一次对照 |

对照采集，不覆盖旧数据：

```bash
CALL_GRAPH=dwarf,32768
sudo "$PERF_BIN" record -o "$RUN_DIR/perf-dwarf.data" \
  -e "$PERF_EVENT" -F 99 -p "$TARGET_PID" \
  --call-graph "$CALL_GRAPH" -- sleep 20
```

读这个新文件时，report 的 `-i` 也要改为 `"$RUN_DIR/perf-dwarf.data"`。

DWARF 不一定比 fp 更完整。曾遇到 DWARF 到 SQLite 就断，而 fp 能追到 `PublishStatus()`；这不是所有 ARM64 的规则。增大快照仍无效时，检查展开兼容性，不无限增加快照或样本。

### 4.3 用现有数据单独看线程

先查记录里的线程：

```bash
sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" --tasks
```

再设置实际 TID：

```bash
TARGET_TID=1985462
sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" \
  --tid "$TARGET_TID" --stdio --no-children --call-graph none
```

线程名字相同不表示同一线程。过滤后百分比分母可能改变，不直接和全进程排行相加。

## 5. 解读报告

### 5.1 列的含义

| 列 | 含义 |
|---|---|
| Self / 关闭 Children 后的 Overhead | 采样直接落在该函数中的开销 |
| Children | 包含下层调用的累计开销，用于找业务入口 |
| Shared Object | 程序、动态库或内核 |
| `[k]` / `[.]` | 内核态 / 用户态符号 |
| Total Lost Samples | 丢失记录提示；为 0 不保证调用栈完整或没有偏差 |

`cycles` 的比例是采样估计的周期分布，不是 top 的整核百分比，也不是业务墙钟耗时。频率和业务负载变化会影响比较。

```text
业务函数      Children 30%, Self 1%
  → memcpy    Children 20%, Self 20%
```

不能合计成 50%；memcpy 已计入上层 30%。`graph` 分支显示总体贡献，嵌套不能重复相加；`fractal` 按分支相对比例展示，不能混读。

### 5.2 找到业务入口

```text
线程入口 → 定时器/回调 → 业务函数 → 库函数 → 实际热点
```

看到 malloc、锁、时钟、memcpy 只是开始。先确认哪个业务触发，再判断调用次数多还是单次成本高。交互查看：

```bash
sudo "$PERF_BIN" report -i "$RUN_DIR/perf.data" --no-children
```

方向键选择、Enter 查看操作，`h` 查看版本对应帮助，`q` 退出。更细可用 `perf annotate` 检查指令热点；源码行需要匹配的调试信息。

### 5.3 避免这些误判

- 锁热点不等于已证明锁竞争，可能只是大量无竞争加解锁。
- sleep 链里时钟耗 CPU，不代表睡眠时长在消耗 CPU。
- 出现 vDSO 名字不表示没有系统调用；继续到 `__arm64_sys_clock_gettime` 说明至少该路径进入内核。
- 多个库函数并列不等于同一调用链。
- 热点没显示不等于消失，先看过滤、阈值、负载及采样范围。
- 几百样本可判断方向，不适合对小百分比波动作精确收益承诺。

## 6. 三个实际案例

以下案例由原手册记录；2026-09-18 接入知识树时未取得原始采样文件、匹配二进制及源码进行独立复核。文中的“确认”指原案例的记录，不代表当前会话验证，也不能推广为所有同类程序的固定问题。

### 6.1 uploader 状态发布与 SQLite

```text
ROS 定时器 → UploaderNode::PublishStatus()
  → StateStore::List() → ListLocked() → LoadFilesForTask()
    ├─ sqlite3RunParser / sqlite3Parser
    ├─ sqlite3_step / sqlite3VdbeExec
    └─ sqlite3_finalize / sqlite3_free
```

某次 442 个样本里，原子交换 Self 13.38%，其中 LoadFilesForTask 分支 11.27%；mutex lock Self 8.26%，其中该路径 7.82%。分支已包含在对应 Self 中。

**确认：** 状态发布产生 SQL 解析、执行、销毁、分配和锁开销。

**待验证：** 每任务查一次文件（N+1）、每次重新 prepare、未变化仍全量查询、发布频率是否过高。

查 `PublishStatus()` 定时器、`ListLocked()` 循环及 `LoadFilesForTask()` SQL 生命周期。确认后考虑批量加载、仅查询需要字段、状态快照或复用预编译语句：

```text
prepare 一次 → bind → step → reset → 再 bind/step/reset → 最后 finalize
```

reset 不清空参数绑定，下一次要完整重新绑定或 clear_bindings。检查返回码、连接/语句线程归属和生命周期；不要关闭线程安全来省锁。

### 6.2 ros2_control 控制周期字符串比较

```text
ControllerManager::update() → trigger_update()
  → JointStateForwardController::update()
    → std::string::operator==  Self 9.51%
```

确认字符串比较来自该控制器；是否每周期双重循环找关节名称，要看源码。

如果证实重复查找，可建立名称到索引映射，周期内直接取值。消息名称/顺序变化必须重建；处理缺失、重复名称和字段长度差异，不能使用过期映射造成关节错配。

### 6.3 读时钟与统计/消息发布

某次 `ktime_get_ts64` Self 18.64%，`ktime_get_real_ts64` Self 8.26%，合计 26.90%。前者来源包括：

- `pal_statistics::StatisticsRegistry::publisherThreadCycle → Rate::sleep`：7.71%。
- WrenchStamped、JointState、DynamicJointState 的 RealtimePublisher / Fast DDS 路径：合计 8.88%。

确认读时钟有 CPU 开销，不等于忙循环或时钟源故障。先查统计及发布频率，区别遥测频率和控制更新频率；只在需求允许时对非关键统计/遥测做降频对照。`ros2 topic hz` 会增加订阅者，可能改变负载，使用时记录这一变化。

多个进程都读时钟较贵，可提出平台共享路径成本假设；需对照测量，不直接修改 clocksource。

## 7. 常见报错

| 现象 | 处理 |
|---|---|
| shell 显示 `>` | 检查未闭合引号；Ctrl-C 后重输。曾出现 `sleep 20'` 多单引号 |
| perf not found for kernel | 找二进制，用绝对路径，见第 2 节 |
| PMU Hardware doesn't support sampling | 文案不等于硬件坏；分别短测 cycles/cpu-clock，先不带栈 |
| No such process | 更新 PID/TID；核对 PID 命名空间 |
| Permission denied / Operation not permitted | 检查 sudo、容器能力和内核限制，不默认全局关闭限制 |
| stat 成功、record 失败 | 计数与采样支持不同，隔离事件/栈功能 |
| unknown 或裸地址 | 检查符号、展开信息、二进制匹配、栈方式 |
| 栈停在 libc/SQLite | 对比 fp/dwarf，必要时增大 DWARF 快照一次 |
| Cannot load tips.txt | 帮助提示文件缺失，不是数据损坏的证据 |

工具和展开能力检查：

```bash
uname -a
"$PERF_BIN" version --build-options
```

`PERF_BIN` 为真实 ELF 二进制绝对路径时：

```bash
ldd "$PERF_BIN" | grep -E 'libdw|libunwind|libelf'
```

没有匹配输出也可能是静态链接，不能单独判定不支持展开。不要对启动脚本做 ldd 后误判。

ARM64 返回地址的高位变化（如 `0x2cffff...`、`0x46ffff...`）可能与 PAC 有关，只是线索。先对照 fp，再查内核、perf、展开库，不建议关闭指针认证。

自己的程序保留正常优化和匹配调试信息，例如 `-O2 -g`；需要 fp 时保留帧指针。仅修改主程序编译选项不保证第三方库栈完整。不要为性能采样切换 `-O0` 改变真实负载。

## 8. strace 辅助分析

用于内核态开销、异常重试、文件访问。短时运行，与 perf 基线分开，避免扰动：

```bash
sudo timeout 5s strace -f -c -p "$TARGET_PID"
```

- `-c` 默认内核 CPU 时间；`-w` 才是包含阻塞等待的墙钟时间。
- `% time` 是系统调用统计内部比例，不是进程 CPU%，不含用户态计算。
- 调用次数除以采样时长才是频率；errors 需看 errno，可能是预期非阻塞返回。
- futex 次数或时间不能单独证明 CPU 高是锁竞争造成。

看路径、长度和错误码：

```bash
sudo timeout 3s strace -f -tt -T -yy -s 32 \
  -e trace=pread64,pwrite64,setsockopt,flock,sendto \
  -p "$TARGET_PID" -o "$RUN_DIR/syscalls.txt"
```

关注 FD 路径、读写长度、偏移、返回码；setsockopt 看选项和 errno。`-T` 是单次调用经过时间，不能把阻塞当 CPU。日志可能含数据片段，分享前检查。

## 9. 优化验证与交接

每次验证一个明确假设，例如减少全量查询、复用 SQL、缓存关节映射。比较相同输入规模、任务数、发布频率下的：

- CPU 和必要时的绝对 CPU 时间/周期。
- 业务吞吐、延迟及处理数量，保证不是少做业务换来下降。
- 相同事件、范围的 perf Self 和调用链。
- 实时控制的周期、deadline miss、抖动和功能正确性。

占比下降不代表总成本下降；占比上升也可能是其他路径优化后分母变小。先有限对照，波动或失败需要时再补采样。

给同事发送：

```text
系统/内核/架构：
PID 和进程命令：
业务负载（任务数、频率、输入量）：
perf 路径和版本：
采样命令（事件、栈方式、范围、时长）：
top/pidstat：
self.txt / children.txt：
重点调用链或完整 callers.txt：
相关函数源码（如可提供）：
```

保留 perf.data 可反复生成报告；跨机器分析需匹配程序、库和符号。DWARF 原始数据可能包含用户栈内容，分享前考虑敏感信息。

## 10. 技能使用与资料来源

配套技能：`linux-perf-diagnosis`。将压缩包中的同名目录放到 Codex 技能目录，例如 `~/.codex/skills/`；设置了 CODEX_HOME 时使用其下 skills 目录。发现技能后可调用：

```text
请使用 $linux-perf-diagnosis 分析这个进程。
我会提供 top 和 perf 输出，请区分事实与推测，给出可复制的下一步命令。
```

这份手册可以单独使用，不依赖 Codex。以下是原始文档及平台讨论；包名和功能需结合实际版本：

- [perf record](https://man7.org/linux/man-pages/man1/perf-record.1.html)、[perf report](https://man7.org/linux/man-pages/man1/perf-report.1.html)：范围、栈方式、百分比和调用链。
- [strace 官方手册源码](https://github.com/strace/strace/blob/master/doc/strace.1.in)：时间统计语义。
- [Debian linux-perf](https://packages.debian.org/stable/linux-perf)、[Fedora perf](https://packages.fedoraproject.org/pkgs/kernel-tools/perf/)：安装包。
- [Ubuntu 安装示例（Brendan Gregg）](https://github.com/brendangregg/Misc/blob/master/perf_events/perf.md)。
- [NVIDIA Tegra perf 讨论](https://forums.developer.nvidia.com/t/cant-install-and-run-perf/317946/12)：直接调用二进制的案例，不保证所有版本适用。
- [ARM64 指针认证](https://www.kernel.org/doc/html/latest/arch/arm64/pointer-authentication.html)、[perf PAC 展开问题讨论](https://lists.infradead.org/pipermail/linux-arm-kernel/2022-July/757446.html)：PAC 与历史兼容性线索。
- [SQLite 语句生命周期](https://www.sqlite.org/c3ref/stmt.html)、[reset 绑定语义](https://www.sqlite.org/c3ref/reset.html)。
