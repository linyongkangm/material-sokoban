# material-sokoban — 像素画绘制方式

本仓库所有像素资产都是**生成出来的，不是手点像素**。每张精灵都是画在内存像素缓冲上的一堆几何函数，
算完再整体 blit 进 `.aseprite`。画风、验收阈值和重跑步骤都写在下文；改动任何一张图，请先读完
「画风不变量」和「验收门」两节，它们比代码注释更容易说明为什么长这样。

## 1. 目录与交付分层

| 路径 | 内容 | 性质 |
| --- | --- | --- |
| `tools/` | 全部生成器与校验脚本（`.py` / `.lua`）、`roster_locked.sha256`、跨类总览 `overview.png` | 源码，唯一真相 |
| `tiles/` | **唯一一套素材**：4 块整格（floor / box / goal / player）+ 16 件墙（四臂的全部子集）+ 4 件门窗贴面 + **没有生成器**的 `shelf`，各带 `.aseprite` 与 `_1x.png`；`master.aseprite`（20 切片，640×32）、`sheet.png` / `sheet_4x.png` / `with_shelf.png`、`wallset*.png` + `wallset.json` 与 `openings*.png` + `openings.json`（引擎图集）、`contact.png` / `scene.png` / `junctions.png`、户型图 `flatplan.png` 与家具总览 `furniture_contact.png` | 地块素材 |
| `tiles/furniture/` | 家具与摆件，**一件一个资源**：各带 `.aseprite` 与 `_1x.png`，加一份 `furniture.json` 清单（件数以 `gen_furniture.py` 的 `PIECES` 为准），尺寸按真实家具（1 格 = 32px = 1 米） | 可编辑源，`tools/gen_furniture.py` 生成 |
| `character/` | 12 人的交付 PNG（头像 / 徽章 / 色卡）、`pack.json`、名册条带、两张预览 | 交付层 |
| `character/avatars/` | 12 颗头骨的 `.aseprite` 源 + `_1x.png`，其中 6 位已锁定 | 可编辑源 |
| `character/tokens/` | 24 个 swatch / token 的 `.aseprite` 源 | 可编辑源 |
| `player/` | 主角走路与立绘交付物、平涂风头像 `avatar_player*`、`avatar_preview.png` | 交付层 |
| `characters.html` | 角色图鉴页，manifest **内联**（`file://` 下 Chrome 无法 XHR 同级 JSON） | 由 `tools/make_character_page.py` 生成 |

原先所有素材与脚本混在一个 `art/` 里，现按归属拆开；`lumine/`（荧的立绘与四方向走路）已整体删除，
只有 `tools/lumine.lua`、`tools/lumine_walk.lua` 和两个 preview 脚本还在，它们写往已不存在的目录，
属于**死脚本**，文件头已标注。

**地块只有一套了。** 原来 `tiles/` 是带明暗的着色集、`tiles/murdoku/` 是平涂集，同一个件画两遍。
着色集连同 `tools/gen_sokoban.py` 已整体删除，平涂集上移接管 `tiles/`，所有 `_murdoku` 后缀去掉；
`Grid` 画法内核搬进 `gen_murdoku.py`（它现在既是那四块整格的地块生成器，也是内核所在地）。
留两套的代价已经现过一次：门窗贴面当时只在平涂那侧画了，着色集根本没有窗。

地块 32×32，头像 64×64，主角走路 32×32；`tools/lumine*.lua` 的画布是 64×100。
注意脚本里 `spr.layers[1].name = 'art'` 指的是**图层名**，与旧的目录名无关，别改。

## 2. 两条驱动路径

**地块走 Python。** `tools/gen_murdoku.py` 里有一个 `Grid` 类（32×32 列表缓冲，
`rect / border / round_rect / ring_px / outline` 几个画法，`None` 保持透明），画完之后转成
`[{x, y, color}]` 像素清单，脚本把 MCP 调用序列写成 `calls.json`（`[[tool, args], ...]`），
由 `tools/mcp_client.py` 在**一个 stdio 连接内**重放（这条路径实测在这台机器上会卡住，现在只算备用，
实际出图走第 7 节的 `--lua` + `dofile`）：

```
create_canvas -> add_layer(flat) -> add_layer(ink)
  -> draw_pixels_at(flat) -> draw_pixels_at(ink)
  -> [outline_cel] -> export_frame(scale 1)
```

`draw_pixels_at` 接受的是**精灵全局坐标**，所以 `tiles/master.aseprite` 整张长条就是把同一批像素清单
每列平移 32px 再画一次，同时给每块地调用 `create_slice`，引擎才能按名字取。
`tools/gen_sheet.py` 专门产出这张长条。调用计划里的文件名是相对路径（`tiles/floor.aseprite`），
`mcp_client.py` 把 MCP 的 cwd 设成**仓库根**，所以产物会落到对应 subject 目录里。

**角色与动画走 Aseprite batch Lua。** `tools/roster.lua`、`tools/player.lua`、`tools/avatar_recipe.lua`、
`tools/character_pack.lua`（以及已死的 `tools/lumine.lua` / `lumine_walk.lua`）自带一个 `Canvas` 对象
（`px` + `occ` 两张表，方法 `box / disc / shiftY / flipX / outline / hair_shade / blit`），通过
`mcp__aseprite__run_lua_script` 执行
`pcall(dofile, 'E:/Material/material-sokoban/tools/player.lua')`。用文件 + `dofile` 而不是把长脚本内联
塞进一次调用，既避开调用体长度问题，也让脚本本身留在仓库里成为"这张图怎么来的"的记录。

派生关系是单向的：`roster.lua` 末尾把 `ROSTER_CHARS / ROSTER_INK / ROSTER_DIR` 暴露成全局，
`character_pack.lua` 先 `dofile('roster.lua')`，于是头像、色卡、徽章、`character/pack.json`
全部来自**同一份调色板**，不会各画各的然后漂移。（死掉的 `lumine_walk.lua` 当年也是同一手法：先
dofile `lumine.lua`，顺带把静态立绘重建一遍，所以两者不会失配。）

其余 `.py`（`compose.py`、`contact.png` / `scene.png`、`*_preview.py`、`overview.py`）都是 PIL 合成，
属于**评审环节而不是作画环节**：`compose.py` 会把地块贴进一张真实 Sokoban 关卡，因为接缝和调色板
不协调只有"真的平铺起来"才看得见。

**家具不是 32×32，而且分两个尺寸级。** `tools/gen_furniture.py` 用同一个画法内核（占用表 + 手动膨胀
墨线 + 平涂），但 `Piece` 的画布按真实家具体积给（双人床 2×2 格、单人床 1×2、地毯 3×2、摆件半格）。
**每件的确切尺寸不写在这里**——`tiles/furniture/furniture.json` 就是那张表，`--manifest` 每次重发，
抄进文档的那一份只会过期（沙发从 3×1 改成 2×1 就是现成的例子）。
另一级是**摆件**（花瓶 / 果盘 / 书 / 靠垫 / 地垫），半格 16×16、墨线 1px，
它们存在的意义就是"放在某个面上"。`ink()` 的膨胀**裁在自身框内**，所以一件家具永远不会把墨线伸进
隔壁一格——这是它能平铺进户型图的前提。
`tools/gen_flatplan.py` 再把它们摆成一张图：房间是矩形数组，**墙体由"跨房间的边"推导**（复用
`compose.py` 的 `arms_at` / `piece_for`，所以转角、丁字、端头盖帽和 16 件墙资产完全一致），
门就是**缺席的墙段**，窗是盖在墙带上的玻璃贴面。1 格 = 1 米，`SCALE = 4`。门窗贴面本身不在家具那
里——它们装在墙上，由 `gen_walls.py` 的 `OPENINGS` 一套四件（`window_{h,v}`、`door_leaf_{h,v}`）和墙
一起出，共用同一张剖面，所以盖上去不会错缝。

**叠放次序是模型，不是画图的先后。** `gen_furniture.LAYER` 一个字典说清每件东西站在什么上面（住在家具
那一侧，因为"站在什么上面"是它本身的属性，户型图和 `furniture.json` 都只引用它）：
`-2` 地面铺贴（地毯、地垫）→ `0` 家具 → `1` 摆件 → **墙** → 窗和门扇 → 标注。
墙画在家具**之上**是有意的：平面图里砌体是固定物、家具只是顶着它摆，所以伸到线上那部分必须被墙裁掉；
反过来画会让每张床、每个衣柜在自己那面墙上打一个洞，一整圈外框读成"断成几截的墙加中间的家具"。
摆件锚点允许小数（半格的东西要落在桌面正中），锚点就是它占地的左上角。
**房间之间的连接分两种**：`DOOR_SEGS` 有门有门扇，`OPEN_SEGS` 只是墙断了、不装门（垭口）。
判定标准是"这两个房间是不是同一个空间"——过道和客厅是同一片活动区，中间装一扇要开的门就不成立
（"过道进门进客厅，没有这样布局的"），所以那里是两格宽的开口；卧室、卫生间、厨房各自要关门，仍是门。
`audit()` 两种都查通不堵：开口查两侧格子，门再多查门扇扫到的那一格。
`audit()` 是一支真正的门，六种错都打印 `LAYOUT:` 并以非零码退出，而不是等眼睛在成品图里发现：
家具穿出墙、**同层**两件叠在一起（跨层叠是设计，花瓶和餐桌共用格子是对的）、摆件底下没有承托它的面、
**门被家具挡住**（一个门洞要空三格：门洞两侧各一格，加上门扇沿墙扫到的那一格——门扇 24px、比半格还长。
只查门扇那一侧，就会放过"主卧门开着，但沙发正好堵在客厅那一侧"这种情况）、
标注压在家具上、标注跑到别的房间。footprint 一律从生成出来的资产反查，所以资产改小一改，图会报错而
不会悄悄挤进去。`DOOR_SEGS` 就是这套户型的交通图，读一遍就知道"进门走到哪儿"通不通——第一版把它写成
了进门只能穿过厨房才到得了客厅，第二版主卧门开在 (2,4) 那格、正对沙发背，都是这么读出来的。

## 3. 画风不变量

- **墨线 `#191922`，2px，手动膨胀。** 依据自己维护的 `occ` 占用表，对空像素做 5×5 窗口
  `dx*dx + dy*dy <= 4.5` 判定。刻意不用 `outline_cel`：它每次只加 1px 而且是累加的，几何改一次就
  重新长一圈，重跑几次轮廓会把图形吃掉。
- **平涂，不做明暗斜坡**，最多一条亮带。`gen_murdoku.py` 的文档写得很直白：阴影缺失是设计而非缺陷，
  **不要靠加回 ramp 来"修"**。仓库里以前有过一套带明暗的着色集作对照，已经整体删掉——留着两套风格
  意味着每个新件都要画两遍、并且随时可能只画了一遍（门窗就是这么变成只有平涂才有的）。
- **主光固定在左上**：`y=0 / x=0` 那圈永远是受光边，`x1 / y1` 那圈是暗边。整套素材靠这一个约定读成
  同一个场景。**唯一的例外是窗**：玻璃是凹进去的洞，不是一条棱，给它画一条受光边就变成
  "一段带亮脊的墙"而不是"墙上开了个窗"。所以 `window_{h,v}` 上下（左右）完全对称——两侧各 2px 框、
  中间 6px 玻璃，剖面与它替换的那条墙带逐行相同。门扇不是例外，它是木板，照常受光。
- **色数预算（实测，不是愿望）**：

  | 地块 | 填充色（不含事后补上的墨线） |
  | --- | --- |
  | floor | 2 |
  | box | 3 |
  | goal | 5 |
  | player | 6 |
  | 墙 16 件 + 门窗 4 件（含 2px 墨线） | 3 |

  口径是 `gen_walls.py` 不带参数时自己打印的那份。全部 ≤8，没有例外——上一套着色集的主角 sprite 实测
  17 色（帽子、脸、背带裤、靴子各要一档暗部），那是它被删掉的又一个理由。
- **墙是格子的边，不是一格。** 墙带**含墨线共 10px**（6px 石面 + 两侧各 2px 墨线）居中在格线
  （`y = 15.5` / `x = 15.5`）上，件名就是"从中心块
  伸出哪些臂（N/E/S/W）"。**16 个朝向全部各自出一件，引擎不许旋转**：`wall_post`、`wall_h`、`wall_v`、
  `wall_cross`、`wall_end_{n,e,s,w}`、`wall_corner_{nw,ne,se,sw}`、`wall_tee_{n,e,s,w}`（丁字按**缺**
  哪一臂命名）。理由就是本仓库那条主光不变量——**旋转会把左上主光一起转走**，高光线跑到右边或下边，
  那件就凹下去了。第一版只交付 7 件并写了"角件丁字件旋转 90° 即可"，`compose.py` 的 mock 一拼就露馅：
  同一圈外框里有的凸有的凹。现在 `gen_walls.BY_ARMS` 是"臂集合 → 唯一资产"的查表（16 正好是四臂的全部
  子集，任何节点都查得到，无兜底），没有任何转置步骤。
  另外两条规则各被一次失败渲染教出来。**臂出口那一侧既不描墨线、也不做侧帮亮带**
  （`gen_walls.flank_out()`），否则每 32px 出现一道亮暗竖纹，墙又读回"格子的边"。
  **那条唯一亮带按带子的受光长边取**——横带第 13、14 行，竖带第 13、14 列，
  中心块只按真正穿过它的臂来取。它原先是按"上边两像素是不是空的"找的：竖着的带子那里永远不空，
  于是整条竖墙没有亮带，转角处横墙的亮线一头撞进一条平带里就断了，还是凸凹不一；而无条件两个方向都取，
  又会在每条笔直竖墙的正中留一个 2×2 亮块，把格线读回来。
- **墙只有一种：一条被声明的边就是一堵墙，压在边的正中。** 关卡数据仍按**每格自报四条边**存
  （`compose.py` 里的 `DECL` 就是这个模型），但**不再分单面双面**。以前分：两边都报同一条边画 10px
  整条（`wall_*` 16 件），只有一边报就由那一格画 5px 半条、贴在自己格子内侧（`halfwall_*` 15 件）。
  这个区分站不住——墙是边，边由两格共用，"半条边"不是关卡能表达的意思；而且它要 15 件额外资产、
  要"先画单面再画双面"的次序规则（半条横贯整条 32px 边，会插进整条带已占用的那 5px，把细轨墨线切在
  粗带身上）、要 1px 墨线的例外剖面、要单面件自己的角做斜接。全部删掉。现在 `DECL` 里任何一格报的
  任何一条边，都归一化到同一条线段键（`H` / `V` 两个集合，键是线不是"格 + 边"，所以两邻格各报一次
  也只有一条），画一件 `wall_*`。引擎侧剩两条铁律：**每条边只画一次**（两次就叠成 20px），
  **永不旋转**。
- **10px 这个数是被"占地"逼出来的，不是审美选择。** 墙带跨在格线上就必然向相邻两格各侵入 5px，而
  "每格放得下一个整块"与"墙压在格线上"两件事不能同时成立：第一版墙带 14px（侵 7px），墙画在最后会啃掉
  旁边箱子一条边，把墙画到箱子底下又会让墙凭空断掉 52px。所以**地块内容必须留 5px 边界余量**——箱子有
  2px **外**描边，因此填充要收到 `7..24`，加上描边才正好落在 `5..26`。实测：墙带占 11..20，箱子 5..26，
  零重叠。代价是墙带从"厚石条"变成"栏杆"级别的存在感，觉得太薄就
  回到 12px 总宽（侵 6px、箱子画 20px），两个数一起改才自洽。
- **图层顺序：地板 → 目标点 → 墙 → 箱子 → 主角。** 目标点是地面标记，本来就该在墙下面；箱子和角色
  站在格子里，压在墙带之上是俯视关卡的常规读法。主角地块因此**不缩**，仍占满 32px，靠这条顺序解决交叠。
- **地板自带的那圈 2px 黑网格已删除**：黑线现在只属于墙，"有黑线 = 这里有一道墙"是这套素材
  唯一的边界语言，地板只留 `LILAC_SEAM` 板缝。
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

- **`tools/check_roster.py`** — 直接从 `roster.lua` 解析调色板算 WCAG 相对亮度比。
  发色 vs 衬衫**硬阈值 2.7:1**（Edison 曾以 1.08:1 出厂，徽章的边和芯糊成一团）；
  发色 vs 肤色只作提示——浅色头发浅皮肤的嫌疑人靠墨线分得开，而且已批准的六人名册这一段实测就在
  1.07–1.11，把它设成失败只会训练所有人无视这道门。解析到的角色数少于 6 直接拒绝运行：静默返回空
  表会让下面所有检查同时变成空操作。`ACCEPTED` 表记录被明知接受的例外（目前只有 edison 的 1.88:1）。
- **`tools/roster_locked.sha256` + `check_roster.py --pin`** — 六位已定稿嫌疑人（ada / brigitte /
  cameron / darlene / edison / vinita）的 `.aseprite` 与 `_1x.png` 必须**字节不变**。新角色是纯增量，
  已锁区块永不改。**指纹缺失算 FAIL 而不是跳过**——这道门曾经就在"什么都没检查"地报通过。
- **`tools/player_preview.py:check_fresh()`** — 拿派生产物的 mtime 和 `player.aseprite` 比，落后就打印
  `STALE:`。这类"过期成品看起来完全正常"在本仓库已抓到过多起，预览一律做成脚本而不是临时命令就是为这个。
- **`tools/overview.png` 不在 `check_fresh()` 覆盖范围内**，而且真的过过期：2026-10-11 目录重排后重跑
  `overview.py`，与已提交版本逐像素比对，差异只落在第 D 节名册行的 Edison 一格（1876 px 与已锁定的
  `edison_1x.png` 不符），其余五格 0 差。那张总览是在 Edison 发色定稿之前生成的，此后一直冒充成品。
  结论：**派生产物要连着它引用的全部源一起重跑**，只重跑被改的那一张留不下这个证据。
- **`character_pack.lua` 的 `save_png()`** — 先删目标、再保存、然后重开确认写成功。`saveCopyAs`
  **写失败不会中断脚本**（目标被占用即可），于是上一轮的文件会留在原地冒充这一轮的成果。
- **1x 才是验收尺寸** — `roster_preview.py` 会输出真实 1x 条带："名册只有在游戏实际绘制的大小上还能
  分辨，才算成立"。

## 6. 已知不可复现的资产

`tiles/shelf.aseprite`（含 `_1x.png` / `_8x.png`）没有任何生成器产出它——
`gen_murdoku.py` 的 `TILES` 只有 floor / box / goal / player，`shelf` 只在 `overview.py` 的
展示清单里出现。它是当年用 MCP 绘图工具直接画出来的，所以：**重跑整套素材不会回去补这一格，
`overview.py` 与 `with_shelf.png` 却会照样引用它**。要改货架只能继续手改那张 `.aseprite`。

## 7. 重跑之前必须改的硬编码路径

Python 侧的路径常量已全部由 `__file__` 推导（`ROOT = dirname(dirname(__file__))`），仓库挪到别的盘
或别的目录不必再改。仍然写死绝对路径的只剩两处：

| 位置 | 现在写的 | 换机器 / 挪仓库时要改成 |
| --- | --- | --- |
| `tools/mcp_client.py` 的 `PY` | `H:\Program Files\Aseprite\aseprite-mcp\.venv\Scripts\python.exe` | 本机 aseprite-mcp 的 venv |
| `tools/*.lua` 的 `DIR / OUT / SRC` 与注释里的 `dofile` 示例 | `E:/Material/material-sokoban/...` | 仓库新根 |

`mcp_client.py` 的 cwd 由脚本自身位置推出，等于仓库根；调用计划里的相对文件名（`tiles/floor.aseprite`）
因此正好落到对应 subject 目录。

本机 `python` 是 WindowsApps 的空壳（调用即 `Permission denied`），上面那个 venv 里 `PIL` 与 `mcp`
都能正常 import（Python 3.13）。流程：

```
cd E:/Material/material-sokoban
"<venv python>" tools/gen_walls.py --lua            # 16 件墙 + 4 件门窗 -> tools/walls_gen.lua
"<venv python>" tools/gen_walls.py --sheet          # 墙体图集 wallset(.png/_4x.png/.json)
"<venv python>" tools/gen_walls.py --openings       # 门窗图集 openings(.png/_4x.png/.json)
"<venv python>" tools/gen_murdoku.py --lua floor,goal   # 指定的整格地块
"<venv python>" tools/gen_sheet.py --lua            # tiles/master.aseprite -> tools/sheet_gen.lua
"<venv python>" tools/gen_sheet.py --png            # tiles/sheet(.png/_4x.png)，逐列与地块比字节
"<venv python>" tools/gen_furniture.py --lua        # 全套家具     -> tools/furniture_gen.lua
"<venv python>" tools/gen_furniture.py --manifest   # 一件一个资源：furniture/furniture.json + 逐件字节校验
"<venv python>" tools/gen_furniture.py --contact    # 家具总览 furniture_contact.png
"<venv python>" tools/check_roster.py               # 名册改动后必跑
"<venv python>" tools/compose.py                    # contact / scene / junctions 三张评审图
"<venv python>" tools/gen_flatplan.py               # 户型图，纯 PIL 合成，不碰 Aseprite
"<venv python>" tools/overview.py                   # 全仓库总览 tools/overview.png
"<venv python>" tools/make_character_page.py        # 改完名册刷新 characters.html
```

`--sheet` 与 `--openings` 是两套"给引擎用"的导出（墙一张、门窗一张）。墙体图集的**槽位号就是臂的位掩码**：N=1、E=2、S=4、W=8，
0..15 是四臂的全部子集（0 号是 `wall_post`，即没有臂离开的节点），128×128 的 4×4。
关卡把一个节点的臂集合解析出来之后，取瓦片是算术而不是查表。`wallset.json` 里同时写死了三条反复被踩的
约定：墙压在格线正中（相对格子网格偏移半格）、**每条边只画一次**（两次叠成 20px）、**永远不要旋转**。
导出时逐槽和源 `_1x.png` 比字节，16 槽全过才算成（`slots verified`），差一像素就是废图。

门窗图集是一道更狠的门：**贴面必须和它替换的那条墙带共用剖面**。窗要横贯整 32px，而且上下框线必须
**正好压在墙带的 11..12 与 19..20 行上**——差一像素都不行，第一版窗框只有 12..19，每开一个窗都在墙的
外轮廓上留一道 32px 宽的缺口；门扇则整块待在墙带（含 2px 墨线）之内，否则就是一块靠在墙上的木板。
检查按轴向取正确的边——横件看行、竖件看列，这个搞反过一次，把好好的 `window_v` 报成不合格。门扇原来
比墙带上沿多出 1px，就是被这道门逼出来往下挪了一格。

家具**不进图集**：引擎把每件家具当独立对象摆，所以交付形态是一件一个 `.aseprite` 加一个 PNG，
`--manifest` 再写一份 `furniture/furniture.json` 说清每件是什么——像素尺寸、按 1 格 = 1 米折算的占地、
所在层（-2 地面铺贴 / 0 家具 / +1 台面摆件）、锚点（占地左上角）、用了几种颜色。层这张表住在
`gen_furniture` 而不是户型图脚本里：站在什么上面是**家具本身的属性**，`gen_flatplan` 只是引用它，
清单发布的也是同一张表。这道检查同样会咬人：把 `plant_1x.png` 缩一半再放大存回去，立刻报
`STALE: plant: plant_1x.png is not what the generator draws` 并非零退出——盘上一张过期的 PNG 和
当前的一模一样，只有重画一遍对字节才分得出来。

家具与户型这两行有先后：`--lua` 只写脚本，得先 `dofile` 出 `tiles/furniture/*_1x.png`，
`gen_flatplan.py` 才读得到贴图和它们的真实尺寸（尺寸是从资产反查的，不是写在表里的）。

上面带 `--lua` 的四行只写脚本，真正画图要在 MCP 里 `run_lua_script` 一次 `dofile` 掉它们，例如
`pcall(dofile, 'E:/Material/material-sokoban/tools/walls_gen.lua')`；`master.aseprite` 的切片用
batch Lua 的 `spr:newSlice(Rectangle(x, 0, 32, 32))` 建，切片 PNG 用 MCP 的 `export_frame` 导出。
**不要再走 `mcp_client.py script calls.json` 那条路**：它按调用逐个启动 Aseprite，72 个调用的批次
在这台机器上零输出、零产物地卡死过；`--calls` 形式仍留在 `gen_sheet.py` / `gen_murdoku.py` 里备用。
`tools/*_gen*.lua` 是一次性产物，改完 Python 重跑 `--lua` 就会覆盖，不必手工编辑。

角色与动画走 MCP：`run_lua_script` 里 `pcall(dofile, 'E:/Material/material-sokoban/tools/player.lua')`。
每次动过目录或画风常量，跑法分两层：**校验与合成脚本**（`check_roster` / `compose` / `roster_preview` /
`character_preview` / `player_preview` / `make_character_page` / `overview`）不写 `.aseprite`，可以随时
重跑；**生成器**会重写 `.aseprite`，只在素材确实要变时跑。要证明"只是搬家、没有重画"，就把整目录的
SHA-256 存一份基线，跑完再比：本次 `tiles/` 143 个文件前后一一对上，只有 3 个 `.aseprite` 字节不同
（容器里有每次保存都变的元数据，它们导出的 PNG 全部逐字节相同——所以差异不在像素上）。
派生图必须一起重跑并核对，`gen_sheet.py --png` 逐列与地块比字节就是为这件事。

读导出数据时要小心：`player/sheet.json` 由 **Aseprite 1.3.14.2** 导出（本机现装 1.3.18.6-dev），
且 `meta.scale` 写的是 `"1"`，而帧实际是 128×128（主角源 32×32）、帧间隔 1px 留白。
**缩放倍数请用 帧宽 ÷ 精灵宽 自己算，别信那个字段。**

## 8. 版本状态

独立仓库（`E:\Material` 本身不是仓库），分支 `main`，
origin `git@github.com:linyongkangm/material-sokoban.git`（SSH，本机推送正常）。

本节**故意不写提交数和工作区状态**——它们每提交一次就过期一次，而 `git log` 是权威的。判定方法：

- 推送与否：`git log origin/main..HEAD`（或 `git rev-list --count origin/main..HEAD`）为空才算同步；
  有输出就说明这份改动只存在于一块磁盘上。**提交不等于推送。**
- 提交信息约定：中文 `type(scope): 一句可见改动`，例如
  `feat(player): 修侧面头秃并给走路循环补摆臂与描边余量`。
- 触及第 5 节那些已锁资产之前，`tools/check_roster.py` 必须先通过，再连同
  `roster_locked.sha256` 一起提交。
