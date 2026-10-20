# Torr Craft

基于 **PySide2 / Qt 5.15** 的真空系统监控低代码平台。用拖拽方式组态分子泵、干泵、角阀、插板阀、腔室与管道，实时显示开关、软件连接、转速与压力，并能把整张图纸导出为 Qt Designer 可解析的 `.ui` 文件。

![Torr Craft 界面预览](artifacts/torr-craft-preview.png)

## 已实现的需求

| # | 需求 | 实现 |
|---|---|---|
| 1 | 六类主要元素 | 腔室、分子泵、干泵、角阀、插板阀、管道 |
| 2 | 管道连接泵/阀/腔室 | 所有元件都有可连接的边缘端口，管道自动正交布线 |
| 3 | 双腔之间必须用插板阀隔离 | 直接创建“腔室 ↔ 腔室”管道会被拒绝；必须存在 `腔室 → 插板阀 → 腔室` 链路 |
| 4 | 五类实体元件可调整大小 | 选中后拖动 8 个控制点，或在属性检查器中精确输入宽高 |
| 5 | 开关状态 + 软件连接状态 | 泵/阀显示“在线/离线”与“运行中/已停止”或“已开启/已关闭”，双击或检查器可切换 |
| 6 | 分子泵、干泵显示转速 | 当前转速大号数字显示，带升速/降速仿真 |
| 7 | 导入/导出 Qt `.ui` | 完整的 Qt UI XML 读写；`pyside2-uic` 可正常编译导出的文件 |

此外还包含：

- 深色工业风编辑器、可拖拽组件库、画布网格与 10 px 吸附
- 单对象属性检查器、连接关系提示、工程脏状态跟踪
- 本地模拟遥测、运行状态联动（泵/阀关闭时管道流动动画停止）
- 新建、示例工程、另存为、打开、未保存确认
- 画布锁定模式，便于演示时防止误移动

## 快速开始

要求 Python 3.9（PySide2 5.15 目前没有 Python 3.11+ 的官方 wheel）和 PySide2 5.15.2。

```powershell
python -m pip install -r requirements.txt
python run.py
```

也可以：

```powershell
python -m torr_craft
```

首次启动会载入“**双腔真空系统**”示例。按 `Ctrl+N` 新建空白图纸。

### 常用快捷键

| 快捷键 | 操作 |
|---|---|
| `Ctrl+N` | 新建图纸 |
| `Ctrl+O` | 打开 / 导入 `.ui` |
| `Ctrl+S` | 保存；首次保存会询问路径 |
| `Ctrl+Shift+S` | 另存为 / 导出 `.ui` |
| `Ctrl+L` | 锁定 / 解锁画布 |
| `Ctrl+G` | 开关网格吸附 |
| `Esc` | 取消管道起点或退出管道模式 |
| `Delete` | 删除当前选中的元件或管道（画布获得焦点时） |

### 画布操作

- 从左侧组件库 **拖拽** 元件到画布，或在组件库卡片上 **单击** 快速添加。
- 单击元件选中；拖动主体移动；拖动 8 个角/边控制点缩放。
- 按住 `Alt` 拖动可临时关闭网格吸附。
- 双击泵/阀门切换运行状态或阀门开关。
- 点击工具栏“管道”或组件库“管道”，依次点击两个端点建立连接。
- 选中管道后按 `Delete` 或点击检查器中的“删除管道”。

## 连接规则

管道可连接：

```text
腔室 ↔ 分子泵 / 干泵 / 角阀 / 插板阀
泵   ↔ 分子泵 / 干泵 / 角阀 / 插板阀
阀   ↔ 角阀 / 插板阀 / 泵
```

禁止：

```text
腔室 ↔ 腔室                        ← 必须经插板阀隔离
腔室 → 角阀/泵 → 另一腔室          ← 绕过插板阀的间接通路同样禁止
元件 ↔ 同一元件
同一对元件之间的重复管道
```

连接校验基于整张拓扑图：移除所有插板阀后，每个连通分量中最多只能有一个腔室。这样即使通过角阀、泵等中间元件“绕路”，两个腔室也无法在无插板阀的情况下连通。

**关于“管道连接插板阀”的说明**：需求 2 列举的端口类型中没有插板阀，但需求 3 的“两个腔室必须用插板阀隔离”在图形上最自然的表达是 `腔室 → 插板阀 → 腔室`。因此本实现把插板阀也开放为管道端点。如果你希望插板阀采用“两个腔室背靠背、无需管道”的物理贴装方式，可以在此基础上增加一种“内联隔离”关系，而不必改变现有数据结构。

## `.ui` 文件说明

导出的是标准 Qt Designer UI XML 4.0：

```xml
<ui version="4.0">
  <class>VacuumSystem</class>
  <widget class="QWidget" name="VacuumSystem">
    <widget class="QWidget" name="canvas">
      <widget class="ChamberWidget" name="chamber_1">
        <property name="geometry"><rect>...</rect></property>
        <property name="deviceType" stdset="0"><string>chamber</string></property>
        <property name="pressure" stdset="0"><double>3.2e-7</double></property>
      </widget>
      <widget class="VacuumPipe" name="pipe_1">
        <property name="sourceId" stdset="0"><string>chamber_1</string></property>
        <property name="targetId" stdset="0"><string>gate_1</string></property>
      </widget>
    </widget>
  </widget>
  <customwidgets>...</customwidgets>
  <resources/><connections/><slots/>
</ui>
```

- 平台导入器按类名、`geometry`、`deviceType` 和自定义属性还原元件和管道。
- 元件使用真实的自定义 `QWidget` 子类，`VacuumPipe` 也是可加载的 `QWidget` 占位类，所以 `pyside2-uic examples/demo_system.ui` 可以生成可导入的 Python 模块。
- Qt Designer 本身没有 Torr Craft 的自定义控件插件，因此 Designer 中不会渲染元件外观；这不影响 `.ui` 文件作为交换格式和在本平台中的完整往返。
- 把平台导出的 `.ui` 再导入平台会保留元件类型、名称、位置、尺寸、在线状态、开关状态、目标转速、腔室压力和管道端点。
- 示例文件：[examples/demo_system.ui](examples/demo_system.ui)

## 环境提示

PySide2 5.15 的 `shiboken2` 在与 **NumPy 2.x** 共存时，可能向控制台打印一条 “A module that was compiled using NumPy 1.x…” 的 ABI 警告。这是 PySide2 运行时的环境提示，本程序不依赖 NumPy，可以忽略；如果希望控制台干净，可以执行：

```powershell
python -m pip install "numpy<2"
```

## 模拟遥测

当前版本不连接真实硬件，运行状态由本地仿真层驱动：

- 分子泵目标转速默认 `42,000 RPM`，干泵 `1,800 RPM`；启动后按速率升速，停止后降速。
- 在线状态为离线时，转速显示 `--`，管道流动动画停止。
- 软件连接、泵运行、阀门开关均可通过属性检查器或右键菜单切换。
- 修改目标转速后，当前转速会自动追随新目标。

如果需要接入真实设备，建议保留 UI 组件作为“视图”，新增一个设备服务层，按设备 ID 绑定：

```text
DeviceTransport (Modbus TCP / RTU / 串口 / 厂商 SDK)
        ↓ 轮询或订阅
TelemetrySnapshot(online, running, speed_rpm, pressure, ...)
        ↓
Canvas / Inspector 更新对应 DeviceWidget
```

当前的仿真入口在 `torr_craft/main_window.py::_on_tick` 和 `torr_craft/components/base.py::PumpBase.tick`，可以通过接口替换而不用改 UI。

## 项目结构

```text
torr_craft/
├─ app.py                  # QApplication 启动入口
├─ main_window.py          # 顶栏、工具栏、状态栏、文件操作、仿真时钟
├─ components/
│  ├─ base.py              # 元件基类、拖动/缩放/选择、泵动画
│  ├─ devices.py           # 五类真空元件绘制与阀门动画
│  ├─ pipe.py              # 管道模型、正交布线、命中检测、绘制
│  └─ canvas.py            # 画布、连接校验、选择、文档应用
├─ inspector.py            # 属性检查器
├─ palette.py              # 组件库
├─ document.py             # 文档数据类
├─ demo.py                 # 双腔示例工程
├─ ui_io.py                # Qt .ui 导入 / 导出
├─ theme.py                # 色彩、字体、全局 QSS
├─ widgets.py              # 开关、品牌标、组件卡片等
└─ icons.py                # 无外部资源的矢量图标
examples/demo_system.ui    # 可直接导入的示例工程
tests/test_platform.py     # 无头回归测试
tools/screenshot.py        # 生成 README 预览图
```

## 测试

```powershell
$env:QT_QPA_PLATFORM = "offscreen"
$env:QT_QPA_FONTDIR = "C:\Windows\Fonts"   # 无头模式需要字体目录
python -m unittest discover -s tests -v
```

覆盖：

- 元件缩放与最小尺寸
- 腔室直连被拒绝、经插板阀连接成功
- 重复管道被拒绝
- 删除元件时联动删除管道
- 泵升速/降速
- `.ui` 导出 → 读取 → 回填画布的属性往返
- 非法 `.ui` / 未隔离腔室管道的导入处理

生成预览图：

```powershell
python tools/screenshot.py
```

## 待确认的产品问题

1. **真实设备通信协议**：目前是模拟遥测。第一版是否需要 Modbus TCP/RTU、串口 ASCII 或某家厂商 SDK？是否需要轮询周期、断线重连和写寄存器？
2. **插板阀的连接方式**：本实现把插板阀作为管道端点。如果你们真实系统的插板阀是两个腔室之间的“内联法兰”，是否需要支持无需管道的“腔室—插板阀—腔室”贴装关系？
3. **`.ui` 的使用边界**：当前重点是与本平台往返以及通过 `pyside2-uic` 生成代码。是否还需要 Qt Designer 可视化插件，让 Designer 里也能看到这些元件？
4. **工艺参数**：除转速外，是否需要真空度、电流、温度、振动等遥测曲线和报警阈值？

这些点会显著影响通信层和属性模型，但在 UI 组态与 `.ui` 交换层之上都可以增量实现。
