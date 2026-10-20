# Torr Craft Qt Designer Plugin

这是给 **本机 `pyside2-designer`（Qt 5.15 Widgets Designer）** 使用的原生 C++ 插件。插件在 Designer 的 Widget Box 中增加：

- 腔室 `ChamberWidget`
- 分子泵 `MolecularPumpWidget`
- 干泵 `DryPumpWidget`
- 角阀 `AngleValveWidget`
- 插板阀 `GateValveWidget`
- 管道 `VacuumPipe`

Designer 中显示的是与 Torr Craft 视觉一致的预览控件，并暴露 `label`、`online`、`switchedOn`、`targetSpeed`、`pressure`、插板阀法兰、管道路由等属性。生成的 `.ui` 可以直接导入 Torr Craft。

> PySide2 的 `pyside2-designer` 不能像 PySide6 那样加载 Python 插件；它只接受 Qt C++ 插件（DLL）。因此本模块必须编译为 Qt 5.15.2、MSVC2019 x64 的 DLL。

## 快速安装（使用 CI 构建的 DLL）

仓库的 GitHub Actions 会编译插件并发布到 Releases。下载 `torr_craft_designer.dll` 后执行：

```powershell
powershell -ExecutionPolicy Bypass -File .\designer_plugin\install_designer_plugin.ps1 `
  -DllPath .\torr_craft_designer.dll -Launch
```

或者让脚本自动下载最新 Release：

```powershell
powershell -ExecutionPolicy Bypass -File .\designer_plugin\install_designer_plugin.ps1 `
  -DownloadLatest -Launch
```

脚本会安装到当前 Python 的：

```text
PySide2\plugins\designer\torr_craft_designer.dll
```

然后启动 `pyside2-designer`。Designer 左侧 Widget Box 会出现 **“Torr Craft 真空元件”** 分组。

## 本地编译

需要：

- Qt **5.15.2** `win64_msvc2019_64` 开发包，包含 `qttools`（Qt Designer 头文件/库）
- Visual Studio 2019/2022 Build Tools（x64）
- 与 PySide2 5.15.2 对应的 MSVC 运行库

在 **x64 Native Tools Command Prompt** 中：

```cmd
cd designer_plugin
qmake torr_craft_designer.pro CONFIG+=release
nmake
```

产物：

```text
designer_plugin\build\designer\torr_craft_designer.dll
```

运行探针（无需打开 Designer，验证插件能被 QPluginLoader 加载并渲染预览）：

```cmd
cd designer_plugin\tests
qmake probe.pro CONFIG+=release
nmake
set QT_QPA_PLATFORM=offscreen
.\build\probe.exe ..\build\designer\torr_craft_designer.dll ..\build\previews
```

探针输出每个组件的属性数量和预览 PNG。

## Designer 中的使用限制

- Designer 插件中的控件是**静态预览**：属性修改会改变标签/状态文字，但不会执行 Torr Craft 的完整遥测、管道自动布线或内联法兰逻辑。
- 管道 `VacuumPipe` 在 Designer 中是一个占位预览。由于 Qt Designer 的 Widget Box 没有“画布连线”概念，`sourceId`/`targetId` 仍需要在 Torr Craft 的属性中绑定；在 Designer 生成的 `.ui` 中会保留这些属性。
- 生成的 `.ui` 仍由 Torr Craft 的导入器还原为真正的 PySide2 元件；Designer 的预览控件不会进入运行时。
- 必须使用与 `pyside2-designer` 相同的 Qt 5.15.2 ABI。使用 Qt 6 或 MinGW 构建的 DLL 无法加载。

## 卸载

```powershell
powershell -ExecutionPolicy Bypass -File .\designer_plugin\install_designer_plugin.ps1 -Uninstall
```
