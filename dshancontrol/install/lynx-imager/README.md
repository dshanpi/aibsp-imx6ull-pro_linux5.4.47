# LYNX Imager 基础版：i.MX6ULL Pro eMMC 开发镜像烧录

适用界面：LYNX Imager v0.1.0-rc.10。已实际查看 i.MX6ULL/eMMC 的“选择系统”页：该路线选择 UUU 脚本，不是直接选择 img.gz。

## 文件

本源码目录只提交配方和说明，不提交二进制。烧录时需从对应发布或同一固定构建输出取得下列镜像、引导文件及清单，再放到同一个工作目录。

本目录应完整保留：

- `flash-emmc.uuu`：在软件的“UUU 脚本 → 选择文件”中选择它。
- `u-boot-dtb.imx`：与镜像同次构建的 USB 下载引导程序。
- `DshanControl-v0.1.0-dev.20261125.1-imx6ull-pro.img`：原发布 img.gz 解压后的整盘镜像，562036736 字节（536 MiB）。
- `SHA256SUMS`：以上文件及说明的校验值。
- `provenance.json`：来源与验证范围。

不要将 `.img.gz` 改名为 `.uuu`，不要只复制脚本，不要使用其他板型的 U-Boot。

## 写入范围和前置条件

只适用于百问网 i.MX6ULL Pro、512 MiB RAM、eMMC、1024×600 LCD。先备份需要保留的系统和用户数据，并确认具有恢复手段。

这是全盘重装：写入 eMMC 用户区的镜像范围、替换分区表，并更新 eMMC boot0 引导程序和启动分区选择。新布局只有 FAT 启动分区和 ext4 根分区，不保留旧第三分区及其可访问性。它不是保留 `/data` 的分区升级，也不是桌面 OTA 包。无需额外执行全盘擦除。

配方固定选择 U-Boot MMC 1（该 BSP 的 USDHC2/eMMC），不能用于未核对存储映射的其他板卡。烧录前断开其他同类 USB 下载设备。

## 操作步骤

1. 把整个目录保存在短的本地路径，例如 `G:\\flash\\imx6ull`，保留文件名及相对位置。若拿到 ZIP，先全部解压。
2. 打开 LYNX Imager：“烧录系统 → 恩智浦 → i.MX 系列 → i.MX6ULL → eMMC → 下一步：选择系统”。
3. 保持“本地文件”和“UUU 脚本”路线，点击“选择文件”，选择本目录的 `flash-emmc.uuu`。不要选择 img.gz。让软件检查脚本及引用文件，再进入“设备连接”。如果提示配方被拒绝或缺少文件，停止并查看具体错误，不跳过检查。
4. 连接开发板的 USB OTG/下载口与电脑；调试串口另接电脑，用于观察启动。只接串口不能完成 UUU 下载。使用稳定供电和可传数据的 USB 线。
5. 推荐从 ROM USB 下载模式（SDP）开始：断电，依照该版主板丝印/官方手册设置 USB 下载启动，再上电或复位。不同硬件版本的拨码方向不能套用；本说明不臆造拨码位置。
6. 在“设备连接”页确认识别到 NXP i.MX6ULL 的 SDP 设备。UUU 加载本包 U-Boot 后会切换为 Fastboot，期间 USB 会重新枚举。识别不到时检查 OTG 口、线缆、启动模式以及软件给出的驱动提示。
7. 在“烧写系统”页核对型号、eMMC、所选脚本和破坏性写入范围；确认备份后由操作者开始烧录。等待所有 UUU 步骤成功，不要中途断电。这个配方不自动复位。
8. 结束后断电，将启动设置恢复为 eMMC，重新上电。串口使用 115200、8N1、无流控，观察 U-Boot、内核和根文件系统启动，再检查 1024×600 桌面与触摸。

若已有兼容 BSP 的 U-Boot，也可在串口中断自动启动、核对 `mmc list`/`mmc info` 后执行 `fastboot 0`，由同一配方进入 FB 阶段。但此时执行写入的是板上已有 U-Boot，必须确认其 NXP UUU 命令、MMC 1 和 bootloader/all 分区语义与配方一致；不能只凭 Fastboot 设备出现就认定兼容。首次验证优先用 SDP 加载本包引导文件。

## 验证范围

配方按当前安装的 UUU 1.5.243 内置 `emmc_all` 流程裁剪到 i.MX6ULL，并显式固定 MMC 1；已核对构建配置中的 Fastboot/UUU 支持、BSP 的 emmc_dev=1 和 bootloader 的 boot0 映射。

原镜像的压缩/解压 SHA256 已与发布交付一致，引导程序来自同一构建，另做嵌入内容一致性检查。`uuu -dry` 只验证离线配方，不接触设备，不证明 USB 烧录、读回校验或启动成功。LYNX 的导入校验和实机烧录仍需按界面执行，未声称已完成。

2026-11-25 实板修正：初版配方错误地固定 BOOT_ACK=0，覆盖了该 BSP 的 emmc_ack=1，导致内部启动回退到 SDP、串口没有启动输出。已读回校验 boot0 和用户区的 U-Boot CRC 一致；仅将 `mmc partconf 1 0 1 0` 改为 `mmc partconf 1 1 1 0` 后，实板启动进入 Buildroot 登录提示。重新烧录必须使用修正版配方。原系统镜像字节不变。

工厂镜像的特权硬件服务与 OTA 尚未完成设备契约、公钥及维护配置；Linux 启动通过不能代替桌面、触摸、业务及断电矩阵验收。

来源报告：https://github.com/dshanpi/DshanControl/blob/main/docs/IMX6ULL-SYSTEM-DELIVERY-20261125.md

主板源码：https://github.com/dshanpi/aibsp-imx6ull-pro_linux5.4.47/tree/ad0747ede81ce1c2e8660e0ce1a514e6addee4d5/dshancontrol
