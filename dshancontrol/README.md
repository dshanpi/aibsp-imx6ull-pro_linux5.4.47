# DshanControl 原生桌面板级集成

本目录负责 **i.MX6ULL Pro / eMMC / 1024×600** 的板级代码。桌面、API、协议逻辑和 Go 涂鸦网关的唯一维护仓库是 [DshanControl](https://github.com/dshanpi/DshanControl)。本目录不复制应用组件，通过 `release-inputs.json` 固定应用完整提交和源码包 SHA-256。

本次为开发草稿。已有实板运行与用户确认的触摸证据属于此前按文件部署的实验室环境，不能代替新完整镜像的烧录验收。镜像、源码包、许可证、构建记录和校验文件放在 DshanControl Releases；本仓库只上传源码、配置和脱敏证据。

## 代码归属

| 路径 | 内容 |
| --- | --- |
| `board/buildroot/patches/linux/` | 1024×600 LCD/Goodix 触摸与 eMMC 保守参数补丁 |
| `board/buildroot/package/` | Qt/C++ 应用、SOEM 和 EtherCAT 目标包集成配方 |
| `board/buildroot/overlay/` | Goodix udev 分类、显示权限及禁用旧 LVGL 启动 |
| `board/buildroot/dshancontrol.fragment` | 交叉工具链依赖、Qt LinuxFB、无线、音视频、原生服务、时区和 ext4 配置 |
| `board/runtime/` | 持久数据挂载、Wi-Fi、音频、平台服务和桌面 SysV 启动 |
| `board/maintenance/` | 经单板实验室验证的 RAM 维护/有界分区更新脚本；有设备与布局前置条件 |
| `board/platform.json` | i.MX6ULL 设备节点与通道映射 |
| `release-inputs.json` | 应用 A、BSP 基线、内核/U-Boot 提交和归档哈希 |
| `prepare.py` | 校验 A/H 干净状态及迁移一致性，准备独立构建输出 |

本次迁入的板级代码与应用提交 `ab981454fd095fb1101bea317ab8dcc33d94897b` 中的板级快照逐文件一致。为保持本版可追溯构建，配方保留该快照布局并在准备时比对；后续板级改动在本仓库维护，并以新的硬件版本、应用引用和构建记录交付，不能修改既有标签。DshanControl 中的旧目录作为历史版本的重建输入保留。

## 固定来源构建

遵循仓库 `skills/imx6ull-build-guide`、`skills/imx6ull-buildroot-emmc-guide`；本集成使用 Buildroot 配置固定的 Bootlin ARM hard-float 工具链，不临时替换为宿主交叉编译器。需要 Ubuntu、Qt 主机测试依赖及至少约 100 GiB 构建空间。下载缓存可以复用，旧 `target` 不作为新镜像来源。

```sh
git clone https://github.com/dshanpi/aibsp-imx6ull-pro_linux5.4.47.git hardware
git -C hardware checkout imx6ull-pro-integration-v0.1.0-dev.20261125.1
git clone https://github.com/dshanpi/DshanControl.git application
git -C application checkout ab981454fd095fb1101bea317ab8dcc33d94897b
python3 hardware/dshancontrol/prepare.py --application "$PWD/application" --output "$PWD/build"
CCACHE=none CCACHE_DISABLE=1 make -C build/buildroot -j8
make -C build/buildroot legal-info
python3 application/scripts/verify_imx6ull_image.py --buildroot-output build/buildroot --output image-validation
python3 application/scripts/smoke_imx6ull_qemu.py --target build/buildroot/target --output arm-smoke
```

输出为 `build/buildroot/images/sdcard.img`、`boot.vfat`、`rootfs.ext2`（ext4）、`zImage`、`imx6ull-14x14-evk.dtb`、`u-boot-dtb.imx`。ARM 用户态模拟检查不能替代 Linux 内核、LCD、触摸或实板启动验收。

## 存储与部署边界

工厂整盘镜像为 8 MiB 偏移的 16 MiB FAT 启动分区加 512 MiB ext4 根分区。实验室现有设备为另一套三分区布局，p3 独立保存用户数据。直接整盘写入会覆盖分区表，不能宣称保留 p3。必须先确认镜像类型、实际 CID/分区布局、备份与恢复方式；运行中的挂载根分区不能直接 `dd` 覆盖。

安装工具统一入口：[LYNX](https://github.com/dshanpi/lynx-releases)。当前会话 MCP 不支持 NXP 软件切换下载模式；已有网络/RAM 维护脚本不代表通用 LYNX 安装已验收。本次发布整理不自动烧写设备。

新镜像默认启动 `/usr` 下的原生 API 和桌面，不包含 Python 运行时，也不携带 Wi-Fi 密码、云凭据、签名私钥、板端数据库或实验室 CID 配置。特权平台服务和 OTA 需要单独配置设备系统契约、可信公钥、持久存储和真实维护互锁；未配置时不宣称硬件 RPC/在线升级可用。已有生命周期适配器的实验室布局检查不能替代工业现场互锁。

## 验收与许可证

发布执行 [DSP-LINUX-001 1.1.0](https://github.com/dshanpi/EinkOS/blob/main/standards/linux-board-release/v1.1.0/SPEC.md)。绑定实际镜像哈希记录编译、内容检查、模拟运行和逐附件回下载结果。新镜像烧录/启动、物理断电矩阵、外部总线从站、真实官网/涂鸦业务、语音 SDK 和老化未通过前保持 Draft。

本目录迁入代码沿用 DshanControl 的 GPL-3.0-only；字体、SOEM、内核、U-Boot、Buildroot、无线固件和其他第三方组件遵守各自许可证。对应源码和 Buildroot `legal-info` 随镜像草稿交付，不能以应用源码包替代完整系统对应源码或厂商授权审核。

2026-11-25 第一次整机构建发现 tzdata 源文件组选项需要 `asia`，已在 `.1` 配方修复；本地时区仍为 `Asia/Shanghai`。原无 `.1` 标签保持不动，未形成镜像 Release；本版镜像使用新的应用/硬件固定提交。

本轮镜像草稿及全部远端附件的实际下载核验结果见 [2026-11-25 交付回执](DELIVERY-20261125.md)。
