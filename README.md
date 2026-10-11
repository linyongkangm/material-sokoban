# material-sokoban — 像素画绘制方式

本仓库所有像素资产都是**生成出来的，不是手点像素**。每张精灵都是画在内存像素缓冲上的一堆几何函数，
算完再整体 blit 进 `.aseprite`。画风、验收阈值和重跑步骤都写在下文；改动任何一张图，请先读完
「画风不变量」和「验收门」两节，它们比代码注释更容易说明为什么长这样。

## 1. 目录与交付分层

| 路径 | 内容 | 性质 |
| --- | --- | --- |
| `art/` | 生成器脚本（`.py` / `.lua`）、可编辑 `.aseprite`、预览合成脚本 | 源码，唯一真相 |
| `art/tiles/`、`art/murdoku/tiles/` | 两套地块的 `.aseprite` + `_1x.png` | 生成物（可编辑源保留） |
| `art/avatars/`、`art/character/` | 嫌疑人头像、色卡、地图徽章的 `.aseprite` | 生成物 |
| `player/`、`lumine/`、`character/` | 交给引擎的 PNG / `sheet.json` / `pack.json` / GIF | 交付层 |
| `characters.html` | 角色图鉴页，manifest **内联**（`file://` 下 Chrome 无法 XHR 同级 JSON） | 由 `art/make_character_page.py` 生成 |

地块 32×32，头像 64×64，主角走路 32×32，荧的全身立绘与走路 64×100。

## 2. 两条驱动路径

**地块走 Python。** `art/gen_sokoban.py`、`art/gen_murdoku.py` 里有一个 `Grid` 类（32×32 列表缓冲，
`rect / border / round_rect / ring_px / outline` 几个画法，`None` 保持透明），画完之后转成
`[{x, y, color}]` 像素清单，脚本把 MCP 调用序列写成 `calls.json`（`[[tool, args], ...]`），
由 `art/mcp_client.py` 在**一个 stdio 连接内**重放：

```
create_canvas -> add_layer(base) -> add_layer(shade)
  -> draw_pixels_at(base) -> draw_pixels_at(shade)
  -> [outline_cel] -> export_frame(scale 1)
```

`draw_pixels_at` 接受的是**精灵全局坐标**，所以 `master.aseprite` 整张长条就是把同一批像素清单
每列平移 32px 再画一次，同时给每块地调用 `create_slice`，引擎才能按名字取。
`art/gen_sheet.py` 专门产出这张长条。

**角色与动画走 Aseprite batch Lua。** `art/roster.lua`、`art/player.lua`、`art/lumine.lua`、
`art/lumine_walk.lua`、`art/character_pack.lua` 自带一个 `Canvas` 对象（`px` + `occ` 两张表，
方法 `box / disc / shiftY / flipX / outline / hair_shade / blit`），通过 `mcp__aseprite__run_lua_script`
执行 `pcall(dofile, '<绝对路径>/art/player.lua')`。用文件 + `dofile` 而不是把长脚本内联塞进一次调用，
既避开调用体长度问题，也让脚本本身留在仓库里成为"这张图怎么来的"的记录。

派生关系是单向的：`roster.lua` 末尾把 `ROSTER_CHARS / ROSTER_INK / ROSTER_DIR` 暴露成全局，
`character_pack.lua` 先 `dofile('roster.lua')`，于是头像、色卡、徽章、`character/pack.json`
全部来自**同一份调色板**，不会各画各的然后漂移。`lumine_walk.lua` 同理先 dofile `lumine.lua`，
顺带把静态立绘重建一遍——这正是两者不会失配的原因。

其余 `.py`（`compose.py`、`contact.png` / `scene.png`、`*_preview.py`、`overview.py`）都是 PIL 合成，
属于**评审环节而不是作画环节**：`compose.py` 会把地块贴进一张真实 Sokoban 关卡，因为接缝和调色板
不协调只有"真的平铺起来"才看得见。

## 3. 画风不变量

- **墨线 `#191922`，2px，手动膨胀。** 依据自己维护的 `occ` 占用表，对空像素做 5×5 窗口
  `dx*dx + dy*dy <= 4.5` 判定。刻意不用 `outline_cel`：它每次只加 1px 而且是累加的，几何改一次就
  重新长一圈，重跑几次轮廓会把图形吃掉。
- **平涂，不做明暗斜坡**，最多一条亮带。`gen_murdoku.py` 的文档写得很直白：它是 `gen_sokoban.py`
  的**反面**，阴影缺失是设计而非缺陷，**不要靠加回 ramp 来"修"**。
- **主光固定在左上**：着色集里 `y=0 / x=0` 那圈永远是受光边，`x1 / y1` 那圈是暗边。整套素材靠这
  一个约定读成同一个场景。
- **色数预算（实测，不是愿望）**：

  | 地块 | 着色集填充色 | 平涂集填充色 |
  | --- | --- | --- |
  | floor | 4 | 3 |
  | wall | 6 | 3 |
  | box | 4 | 3 |
  | goal | 7 | 5 |
  | player | 17 | 6 |

  ≤8 色这条对地形成立；着色集的主角sprite 实测 17 色（帽子、脸、背带裤、靴子各自都要一档暗部）。
  表里不含事后补上的墨线。上面 `player` 那行是本仓库现存最大的偏离，改地块时请按 ≤8 走，不要拿它当依据。
- **轮廓是一条逐行半宽函数 `y -> hw`**，而不是"椭圆 + 矩形"拼接——拼接处必然出现方头和太阳穴凸起。
  嫌疑人更进一步：每颗头骨是一张**作者写死的 `(y, 半宽)` 锚点表**，于是颅形是每个角色自己的决定；
  `smooth` 迭代次数同样属于身份（平滑两轮得圆顶，`smooth=0` 保留硬折角给方下颌角色）。第二批六个
  锚点是刻意排在第一批的包络之外的（最宽处 y 13..32、面部下端 40..47、下颌半宽 2.6..5.5）。
- **头发永远是独立椭圆，不是头骨外扩。** 等宽环读作头盔；台阶式收束会在两侧太阳穴各留一块。
  顶部受光按列跟随轮廓（`hair_shade`），固定横带读作"贴在盒子上的条纹"。头发与皮肤相接处压暗一档。
  不对称的一束尖尾，才是"发型"和"头发"的区别。
- **脸部不画五官**（名册与女侦探都是），形体负责识别。唯一例外是 `lumine.lua` 里写明的：荧的琥珀
  瞳孔本身是剪影的一部分，所以她有眼睛和睫毛线，其余照旧平涂 + 2px 墨线、无 ramp。
- **角色的主色就是衬衫色**：它领头色卡、占据徽章最外环、驱动 UI 强调条，三者都从
  `character/pack.json` 读同一个 `primary`。曾经的做法是从头像里采样一个像素去猜，已废弃。

## 4. 走路循环的画法

四方向 × 四帧，每方向一个 `newTag('walk_<dir>')`。

- `right` 不单独画：按 `left` 画完再 `c:flipX()`。
- 身体几乎不动，**"劲"来自延迟**——头发、围巾末端、裙摆在下落帧比脚步慢一行。32px 下能量感基本全靠
  这几行滞后，而不是位移幅度。
- **双臂反摆**。没有它，两个 contact 帧只差在抬腿，走路变成"滑行"。
- 侧面视图必须有**自己的发际线**（`hairline_side`）。复用正面那一条会把头顶和后脑露出来，就是
  commit `9439755` 修的"侧面头秃"。
- 绘制顺序是有后果的：远侧手臂画在躯干之前（身体遮住它一半）；围巾画在头部之后（否则被头发吃掉）、
  发束之前（让头发垂在围巾上）；马尾在阴影 pass 之后补画，否则重新开始的那一列头发会染上一道顶光条。
- 平涂集里四肢与躯干之间留 **1px 全透明缝**，靠墨线洪泛去分隔同色的肢体；直接把缝画成深色会让它翻倍。
- 顶部留 `TOP` 行空气（荧取 4 行，画完统一 `c:shiftY(TOP)`），否则 2px 墨线会被裁掉。

## 5. 验收门（每一道都真抓到过 bug）

- **`art/check_roster.py`** — 直接从 `roster.lua` 解析调色板算 WCAG 相对亮度比。
  发色 vs 衬衫**硬阈值 2.7:1**（Edison 曾以 1.08:1 出厂，徽章的边和芯糊成一团）；
  发色 vs 肤色只作提示——浅色头发浅皮肤的嫌疑人靠墨线分得开，而且已批准的六人名册这一段实测就在
  1.07–1.11，把它设成失败只会训练所有人无视这道门。解析到的角色数少于 6 直接拒绝运行：静默返回空
  表会让下面所有检查同时变成空操作。`ACCEPTED` 表记录被明知接受的例外（目前只有 edison 的 1.88:1）。
- **`art/roster_locked.sha256` + `check_roster.py --pin`** — 六位已定稿嫌疑人（ada / brigitte /
  cameron / darlene / edison / vinita）的 `.aseprite` 与 `_1x.png` 必须**字节不变**。新角色是纯增量，
  已锁区块永不改。**指纹缺失算 FAIL 而不是跳过**——这道门曾经就在"什么都没检查"地报通过。
- **`art/player_preview.py:check_fresh()`** — 拿派生产物的 mtime 和 `player.aseprite` 比，落后就打印
  `STALE:`。本会话有两次过期成品看起来完全正常。预览一律做成脚本而不是临时命令，原因也在这里。
- **`character_pack.lua` 的 `save_png()`** — 先删目标、再保存、然后重开确认写成功。`saveCopyAs`
  **写失败不会中断脚本**（目标被占用即可），于是上一轮的文件会留在原地冒充这一轮的成果。
- **1x 才是验收尺寸** — `roster_preview.py` 会输出真实 1x 条带："名册只有在游戏实际绘制的大小上还能
  分辨，才算成立"。

## 6. 已知不可复现的资产

`art/murdoku/tiles/shelf.aseprite`（含 `_1x.png` / `_8x.png`）没有任何生成器产出它——
`gen_murdoku.py` 的 `TILES` 只有 floor / wall / box / goal / player，`shelf` 只在 `overview.py` 的
展示清单里出现。它是当年用 MCP 绘图工具直接画出来的，所以：**重跑平涂集会不回去补这一格，
`overview.py` 却会照样引用它**。要改货架只能继续手改那张 `.aseprite`。

## 7. 重跑之前必须改的硬编码路径

本仓库当年是在 `D:\Materials\sokoban` + 一套 `D:\Program Files\Aseprite` 上做的，两处**如今都不存在**，
脚本按原样跑必然失败：

| 位置 | 现在写的 | 应改为 |
| --- | --- | --- |
| `art/*.lua` 的 `DIR / OUT / SRC / ROSTER_DIR` 及注释里的 `dofile` 示例 | `D:/Materials/sokoban/...` | `E:/Material/material-sokoban/...` |
| `art/mcp_client.py` 的 `PY` | `D:\Program Files\Aseprite\aseprite-mcp\.venv\Scripts\python.exe` | `H:\Program Files\Aseprite\aseprite-mcp\.venv\Scripts\python.exe` |
| `art/mcp_client.py` 的 `ART`（MCP 的 cwd，相对文件名落点） | `D:\Materials\sokoban\art` | `E:\Material\material-sokoban\art` |

本机 `python` 是 WindowsApps 的空壳（调用即 `Permission denied`），但上面那个 venv 里 `PIL` 与 `mcp`
都能正常 import（Python 3.13，本次已实测）。所以流程是：

```
cd E:/Material/material-sokoban/art
"<H: venv python>" gen_sokoban.py wall          # 只重画 wall，写 calls.json
"<H: venv python>" mcp_client.py script calls.json
"<H: venv python>" check_roster.py              # 名册改动后必跑
"<H: venv python>" compose.py                   # 着色集；加参数 murdoku 出平涂集
```

角色与动画走 MCP：`run_lua_script` 里 `pcall(dofile, 'E:/Material/material-sokoban/art/player.lua')`。
> 上述路径修正是**待办**，本次会话只做了读取与色数实测，没有执行任何生成器重跑。

另外两条读导出数据时要小心：`player/sheet.json` 与 `lumine/lumine_walk.json` 由 **Aseprite 1.3.14.2**
导出（本机现装 1.3.18.6-dev），且其中 `meta.scale` 写的是 `"1"`，而帧实际是 128×128（主角源 32×32）
和 128×200（荧源 64×100），帧间隔 1px 留白。**缩放倍数请用 帧宽 ÷ 精灵宽 自己算，别信那个字段。**

## 8. 版本状态

独立仓库（`E:\Material` 本身不是仓库），分支 `main`，origin `git@github.com:linyongkangm/material-sokoban.git`。
2026-10-11 核对：工作区干净，`git log origin/main..HEAD` 为空即已全部推送；共 5 个提交，
2026-10-04 至 10-05，提交信息用中文 `feat(scope): ...` 描述每个可见改动。
提交不等于推送，这条同样适用。
