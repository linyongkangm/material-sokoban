-- Lumine walk cycle: 4 directions x 4 frames, 64x100 each.
-- dofiles tools/lumine.lua first, so the palette, the silhouette curves, her
-- face and the ink pass are literally the ones the still portrait uses. The
-- still is rebuilt as a side effect, which is what keeps the two in sync.
--
-- Run via the MCP with:
--   local ok, err = pcall(dofile, 'E:/Material/material-sokoban/tools/lumine_walk.lua')
-- DEAD SCRIPT: see lumine.lua -- the lumine/ output folder was deleted 2026-10-11.
--   print(ok and 'done' or err)

local ok0, err0 = pcall(dofile, 'E:/Material/material-sokoban/tools/lumine.lua')
if not ok0 then error('lumine.lua failed: ' .. tostring(err0)) end
local L = LUMINE

local W, H, CX, TOP = L.W, L.H, L.CX, L.TOP
local Canvas, ink_against = L.Canvas, L.ink_against
local INK, HAIR, HAIRL, HAIRD = L.INK, L.HAIR, L.HAIRL, L.HAIRD
local SKIN, SKIND, MOUTH = L.SKIN, L.SKIND, L.MOUTH
local DRESS, DRESSD, GOLD, GOLDL = L.DRESS, L.DRESSD, L.GOLD, L.GOLDL
local SASH, SASHD, SHORTS, SOCK, SHOE = L.SASH, L.SASHD, L.SHORTS, L.SOCK, L.SHOE
local hair_hw, face_hw, fringe_y, strand = L.hair_hw, L.face_hw, L.fringe_y, L.strand
local eye, ornaments = L.eye, L.ornaments

-- k narrows everything for the profile: a body seen from the side is about
-- three quarters as wide, and leaving it full width is what made the first
-- pass look like two arms floating outside the dress.

-- ---- parts -------------------------------------------------------------
-- swing is sideways for the front and back views, fore-and-aft in profile.
-- up lifts the whole leg, which is how the passing frames get their hop.
local function leg(c, cx, swing, up, by, far)
  local x, y = cx + swing, 62 + up + by
  c:box(x - 2, y, 5, 6, far and SKIND or SKIN)
  c:box(x - 2, y + 6, 5, 16, far and DRESSD or SOCK)
  c:box(x - 2, y + 6, 5, 2, far and SASH or GOLD)
  c:box(x - 3, y + 22, 6, 5, SHOE)
end

local function torso(c, by, k, back)
  for y = 31, 43 do
    local hw = math.floor((8.5 - (y - 31) * 0.22) * k)
    c:box(CX - hw, y + by, 2 * hw + 1, 1, DRESS)
    c:put(CX - hw, y + by, DRESSD)
    c:put(CX + hw, y + by, DRESSD)
  end
  local sw = math.floor(16 * k) + 1
  c:box(CX - math.floor(sw / 2), 43 + by, sw, 4, SASH)
  c:box(CX - math.floor(sw / 2), 46 + by, sw, 1, SASHD)
  if back then
    -- seen from behind there is no buckle and no V, only the centre seam
    for y = 31, 42 do c:put(CX, y + by, DRESSD) end
  else
    c:box(CX - 3, 44 + by, 6, 3, GOLD)
    c:box(CX - 2, 45 + by, 4, 1, GOLDL)
    if k > 0.9 then
      for i = 0, 5 do
        c:put(27 + i, 31 + i + by, GOLD)
        c:put(37 - i, 31 + i + by, GOLD)
      end
    end
  end
end

-- The hem swings further than the waist, so the skirt reads as cloth with
-- weight rather than a cone bolted to the hips.
local function skirt(c, by, sway, k)
  local sh = math.floor(14 * k) + 1
  c:box(CX - math.floor(sh / 2), 56 + by, sh, 6, SHORTS)
  for y = 47, 58 do
    local hw = math.floor((9 + (y - 47) * 0.45) * k)
    local s = (y >= 54) and sway or (y >= 51 and math.floor(sway / 2 + 0.5) or 0)
    local x0 = CX - hw + s
    c:box(x0, y + by, 2 * hw + 1, 1, y >= 57 and GOLD or DRESS)
    if y < 57 then
      c:put(x0, y + by, DRESSD)
      c:put(x0 + 2 * hw, y + by, DRESSD)
    end
  end
end

-- Front and back: one sleeve down each side of the dress. dy is the arm swing
-- - the whole sleeve and hand ride up or down together, which is what a limb
-- moving toward the camera looks like at this size.
local function arm(c, sgn, off, by, dy)
  dy = dy or 0
  for y = 32, 47 do
    local wide = y >= 44
    local x, w = wide and 15 or 17, wide and 7 or 6
    if sgn < 0 then
      c:box(x + off, y + by + dy, w, 1, DRESS)
      c:put(x + off, y + by + dy, DRESSD)
    else
      local mx = 64 - x - w
      c:box(mx + off, y + by + dy, w, 1, DRESS)
      c:put(mx + off + w - 1, y + by + dy, DRESSD)
    end
  end
  c:box(15 + off, 46 + by + dy, 7, 2, SASH)
  c:box(42 + off, 46 + by + dy, 7, 2, SASH)
  c:box(15 + off, 45 + by + dy, 7, 1, GOLD)
  c:box(42 + off, 45 + by + dy, 7, 1, GOLD)
  c:box(17 + off, 48 + by + dy, 5, 5, SKIN)
  c:box(42 + off, 48 + by + dy, 5, 5, SKIN)
end

-- Profile: both arms hang over the torso, the far one dimmed behind it and
-- swinging opposite to the near one.
local function arm_side(c, off, by, far)
  local x, w = (far and 33 or 26) + off, 6
  local cloth, cuff, hand = far and DRESSD or DRESS, far and SASHD or SASH,
                            far and SKIND or SKIN
  for y = 32, 47 do
    local wide = y >= 44
    c:box(x, y + by, wide and w + 1 or w, 1, cloth)
    c:put(x + (far and w - 1 or 0), y + by, far and SASHD or DRESSD)
  end
  c:box(x, 46 + by, w, 2, cuff)
  c:box(x, 45 + by, w, 1, far and SASHD or GOLD)
  c:box(x + 1, 48 + by, w - 2, 5, hand)
end

-- dir: 'down' | 'up' | 'left' | 'right'
local function head(c, dir, by, lag)
  local side = (dir == 'left' or dir == 'right')
  local back = (dir == 'up')
  local fx = side and (dir == 'left' and -3 or 3) or 0
  local k = side and 0.85 or 1
  local hx = CX + (side and fx * 0.5 or 0)

  -- bob, with the tips sheared sideways: hair swings a beat after the step
  for y = 0, H - 1 do for x = 0, W - 1 do
    local yy = y - by
    local w = hair_hw(yy)
    if w >= 0 then
      local s = (yy >= 21) and lag or 0
      if math.abs(x - s - hx) <= w * k then c:put(x, y, HAIR) end
    end
  end end

  if not back then
    for y = 0, H - 1 do for x = 0, W - 1 do
      local w = face_hw(y - by)
      if w >= 0 and math.abs(x - (CX + fx)) <= w then c:put(x, y, SKIN) end
    end end
    for x = 0, W - 1 do
      local hl = math.floor(fringe_y(x - fx))
      for y = 0, hl do
        local yy = y - by
        local w = hair_hw(yy)
        local s = (yy >= 21) and lag or 0
        if w >= 0 and math.abs(x - s - hx) <= w * k then c:put(x, y, HAIR) end
      end
    end
    -- the two long side locks are a front-view shape; in profile they stuck
    -- out past the skull as a floating tuft
    if not side then
      strand(c, 22 + lag, 12 + by, 27 + by, 4, -2)
      strand(c, 42 + lag, 12 + by, 27 + by, 4, 2)
    end
    if side then
      eye(c, CX + fx - 4, 1)
      c:box(CX + fx - 6, 22 + by, 3, 1, MOUTH)
    else
      eye(c, 26, 1)
      eye(c, 35, -1)
      c:box(30, 22 + by, 4, 1, MOUTH)
      c:put(33, 21 + by, MOUTH)
    end
  end

  -- flowers sit high on her left: screen right facing us, screen left seen
  -- from behind, hidden by the head in profile
  if back then ornaments(c, -17) end

  -- crown light follows the contour column by column
  for x = 0, W - 1 do
    local run = 0
    for y = 0, H - 1 do
      if c:get(x, y) == HAIR and run < 3 then
        c:put(x, y, HAIRL)
        run = run + 1
      elseif c:get(x, y) ~= HAIR then
        run = 99
      end
    end
  end
end

-- dir: 'down' | 'up' | 'left' | 'right'   phase: 0..3
local function figure(c, dir, phase)
  local by = (phase == 1 or phase == 3) and -1 or 0
  local side = (dir == 'left' or dir == 'right')
  local back = (dir == 'up')
  local lag = (phase == 1) and -1 or (phase == 3) and 1 or 0
  local passing = (phase == 1 or phase == 3)
  local k = side and 0.72 or 1

  -- legs: contact - passing - contact - passing. The two contact frames must
  -- not be the same drawing: from the front there is no fore-and-aft, so the
  -- stepping leg is shown one pixel off the ground instead.
  local spread = passing and 0 or 2
  local lup = (phase == 1) and 2 or (phase == 0) and 1 or 0
  local rup = (phase == 3) and 2 or (phase == 2) and 1 or 0
  if side then
    local fsw = ({ [0] = 3, [1] = 1, [2] = -3, [3] = -1 })[phase]
    leg(c, CX, -fsw, (fsw > 0) and lup or rup, by, true)
    leg(c, CX, fsw, (fsw > 0) and rup or lup, by, false)
  else
    leg(c, CX - 4, -spread, lup, by, false)
    leg(c, CX + 4, spread, rup, by, false)
  end

  -- the far arm goes down before the dress so the torso hides half of it
  local swing = ({ [0] = 2, [1] = 1, [2] = -2, [3] = -1 })[phase]
  if side then arm_side(c, -swing, by, true) end
  torso(c, by, k, back)
  skirt(c, by, lag, k)
  if side then
    arm_side(c, swing, by, false)
  else
    -- front and back: the arms counter-swing, one sleeve riding up while the
    -- other drops, so the two contact frames are not the same drawing
    local las = ({ [0] = -1, [1] = 0, [2] = 1, [3] = 0 })[phase]
    arm(c, -1, 0, by, las)
    arm(c, 1, 0, by, -las)
  end

  c:box(29, 24 + by, 7, 8, SKIN)
  head(c, dir, by, lag)
  if not back then ink_against(c, SKIN) end
end

-- ---- assemble ----------------------------------------------------------
local function build_walk()
  local dirs = { 'down', 'left', 'right', 'up' }
  local spr = Sprite(W, H)
  spr.layers[1].name = 'art'
  for i = 2, #dirs * 4 do spr:newFrame() end
  for d, dir in ipairs(dirs) do
    for ph = 0, 3 do
      local fr = spr.frames[(d - 1) * 4 + ph + 1]
      local c = Canvas.new(W, H)
      figure(c, dir == 'right' and 'left' or dir, ph)
      if dir == 'right' then c:flipX() end
      c:shiftY(TOP)
      c:outline()
      local img = Image(W, H, spr.colorMode)
      c:blit(img)
      local lyr = spr.layers[1]
      local cel = lyr:cel(fr)
      if cel then cel.image = img; cel.position = Point(0, 0)
      else spr:newCel(lyr, fr, img, Point(0, 0)) end
    end
    spr:newTag((d - 1) * 4 + 1, (d - 1) * 4 + 4).name = 'walk_' .. dir
  end
  local frames, tags = #spr.frames, {}
  for _, t in ipairs(spr.tags) do
    tags[#tags + 1] = t.name .. ' ' .. t.fromFrame.frameNumber .. '-' .. t.toFrame.frameNumber
  end
  spr:saveAs(L.DIR .. 'lumine_walk.aseprite')
  spr:close()
  return frames, table.concat(tags, ', ')
end

local frames, tags = build_walk()
print(string.format('LUMINE_WALK_OK frames=%d tags: %s', frames, tags))
