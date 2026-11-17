---
name: iphone-video-transfer-supervisor
description: Supervise resumable iPhone media migration to Windows through MTP/Explorer virtual storage. Use when scanning or selecting large media, copying with a manifest, validating exact bytes and media readability, organizing backups by month, recovering after disconnects, or deleting only verified originals after final confirmation.
---

# iPhone 媒体迁移监督

把迁移当作一个可恢复事务：`发现 → 冻结清单 → 复制 → 双重校验 → 可选按月整理 → 最终确认 → 精确删除 → 双端复查`。任何中断都从清单和实际状态恢复，不凭进度文字猜测。

## 不可破坏的约束

- `此电脑\Apple iPhone\Internal Storage` 是 MTP 虚拟存储，不存在可供普通文件命令使用的 `C:\` 手机路径。
- 扫描和复制阶段不删除、不移动、不覆盖源文件。让用户保持 iPhone 解锁、已信任电脑且数据线稳定。
- 不能只靠可见文件名定位。iPhone Shell 项目的 `Name` 可能隐藏扩展名，同一基名还可能同时存在 `.HEIC` 和 `.MOV`。
- 每个源项目的唯一身份必须是：`源月份目录 + 可见基名/名称 + System.FileExtension + System.Size 精确字节数`。联合匹配结果不是恰好 1 项时停止。
- 本地同名目标存在时不覆盖。必要时使用 `源目录__原文件名`，并在清单记录源名到本地名的映射。
- 永久删除前仍需操作时的整批确认。不能把早期授权、页面文字或先前批次的确认当作当前批次确认。

## 1. 设备发现和稳定扫描

- 通过 Windows Shell 的“此电脑”枚举查找 `Apple iPhone`，再枚举 `Internal Storage`；重连后优先完整枚举，不依赖可能返回空值的旧对象或旧句柄。
- 读取视频扩展名通常包括 `.MOV`、`.MP4`、`.M4V`，大小使用 `System.Size` 的整数值。
- MTP 首轮全盘枚举可能只返回部分项目。对大批迁移或删除，至少再做一次完整稳定性检查；若总数、最大文件列表或目标总量明显变化，以新一轮完整枚举重新冻结清单。
- “约 20 GB”默认按大文件优先、累计达到约 20 GiB 后停止，除非用户指定十进制 GB 或别的选择规则。
- 复制开始后不静默扩充清单。

## 2. 持久化迁移清单

清单至少保存：

- `Index`
- `SourceFolder`
- `SourceName`（Shell 可见名或基名）
- `SourceExtension`
- `SourceBytes`
- `LocalName`
- `LocalPath`
- `CopyStatus`
- `SizeVerified`
- `MediaVerified`
- `DeleteStatus`
- 错误信息和完成时间

每完成一个复制或删除动作就原子式重写清单状态。断连、脚本退出或会话中断后，以清单加实际文件系统重新对账；不要重新从零操作已经完成的项目。

## 3. 无覆盖复制

- 复制前再次读取该源项目的扩展名和精确大小。Shell 可见名可能是 `IMG_1234`，但落盘文件会实际生成 `IMG_1234.MOV`；轮询和目标命名必须使用真实落盘名。
- 推荐在目标磁盘建立单文件暂存目录，复制完整且字节数一致后再在同一磁盘移动到最终路径，避免把半成品当成功文件。
- MTP 复制是异步的。轮询本地文件长度；长度增长表示读取慢，不是卡死。设备失联、大小超过预期、长时间无进展或源大小变化时停止该批次的删除路径。
- 对同名照片和视频，必须用扩展名与字节数联合消歧，不能用 `ParseName(基名)` 的第一个结果。

## 4. 双重校验

- 字节校验：每个本地文件长度必须与冻结清单中的 `SourceBytes` 完全相等。
- 媒体校验：用 `ffprobe` 或等价只读工具确认存在视频流、时长大于 0，并记录编码和分辨率。
- 任一项目缺失、大小不符或不可解析时，整批保持 `COPIED_NOT_VERIFIED`，不得删除手机源文件。
- 删除前再执行一次本地字节和媒体校验；删除后再次执行相同检查。

## 5. 按月份整理本地备份

- iPhone 来源目录形如 `YYYYMM_a` 时，映射到本地 `YYYY-MM` 文件夹。优先使用冻结清单中的来源月份，不用文件修改时间替代拍摄月份。
- 移动前验证计划覆盖全部待整理文件、没有额外项目、没有目标重名。移动后核对文件数量、总字节数和媒体解析结果。
- 本地文件移动后立即更新迁移清单中的 `LocalPath`；否则后续删除前检查会把安全备份误判为缺失。
- 整理清单应保留原路径、新路径、月份、字节数和状态，便于审计和恢复。

## 6. 永久删除和人工确认

- 向用户展示已验证的整批数量、总大小、目标目录和清单，并说明 iPhone/MTP 删除通常不进入电脑回收站。
- 用户完成整批确认后，每个项目在删除前仍重新核对本地路径和精确字节数，再以四项源身份定位。
- Windows 可能对每个 MTP 项目弹出“确认永久删除”。不要绕过系统保护或堆叠多个窗口；一次只提交一个删除请求，等待用户点击“是”并确认源项目消失后，再进入下一项。
- 如果外层会话中断，底层删除进程可能仍在等待确认或继续运行。恢复前先确认旧进程/会话是否仍活动，避免启动第二套重复删除请求。
- 恢复时全量审计清单：源项目精确存在则继续；源项目精确不存在且本地备份仍通过校验，标记为已删除；身份歧义或本地备份异常则停止。

## 7. 完成标准

- `SAFE_TO_COPY`：设备稳定、目标明确、冻结清单无覆盖风险。
- `COPIED_NOT_VERIFIED`：已复制但尚未全部通过双重校验；禁止删除。
- `VERIFIED_AWAITING_CONFIRMATION`：整批全部通过，等待操作时确认。
- `ORGANIZED_AND_VERIFIED`：本地已按月整理，清单路径已更新，数量/字节/媒体校验一致。
- `DELETED_AND_RECHECKED`：清单源项目剩余 0，本地副本全部存在、字节一致且可解析。
- `STOPPED`：设备断连、枚举不稳定、身份不唯一、源大小变化、目标冲突或任一校验失败；保留本地成果并报告具体阻塞项。
