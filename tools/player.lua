-- Protagonist: a detective. 32x32, four-direction walk cycle, plus a 64x64 bust.
-- Run via the MCP with:
--   local ok, err = pcall(dofile, 'E:/Material/material-sokoban/tools/player.lua')
--   print(ok and 'done' or err)
--
-- Read order of the design: saffron coat + belt + lapels say "detective", the
-- high pointed ponytail and the red scarf say "brisk", and the magnifying glass
-- echoes the reference site's own onboarding icon. No hat - it would cover the
-- hair and cost the gender cue the hair is carrying. No eyes: the face stays
-- blank like the roster, and the round spectacles carry the expression instead.
-- Deliberate chibi: head ~60% of the sprite, shoulders narrower than the hair,
-- coat cropped to the hip so three rows of leg show - long legs and a wide
-- stride are what make the walk read as energetic rather than stately.
-- Hair is its own oval, never the skull dilated (an even-width ring reads as a
-- helmet). Flat fills, 2px ink silhouette, no ramps.

local DIR = 'E:/Material/material-sokoban/player/'
local INK   = '#191922'
local SKIN  = '#F0BE96'
local HAIR  = '#8A5138'   -- chestnut, two steps lighter than the old mud brown
local HAIRL = '#AD6C4B'   -- crown light
local HAIRD = '#5E3322'   -- shadow where hair meets skin
local COAT  = '#F2C557'   -- primary: saffron instead of beige trench
local COATL = '#FFDE8A'   -- lit shoulder band
local COATD = '#C9922F'   -- lapels, belt, sleeve shade
local SCARF = '#E8564F'   -- accent; the thing that keeps moving after she does
local SCARFD= '#B93A3A'
local BOOT  = '#3B3550'
local LENS  = '#BFE3E8'

local function col(h)
  return Color(tonumber(string.sub(h, 2, 3), 16),
               tonumber(string.sub(h, 4, 5), 16),
               tonumber(string.sub(h, 6, 7), 16), 255)
end

local Canvas = {}
Canvas.__index = Canvas
function Canvas.new(w, h)
  return setmetatable({ w = w, h = h, px = {}, occ = {} }, Canvas)
end
function Canvas:get(x, y)
  if x < 0 or y < 0 or x >= self.w or y >= self.h then return nil end
  return self.px[y * self.w + x]
end
function Canvas:put(x, y, hex)
  x, y = math.floor(x), math.floor(y)
  if x < 0 or y < 0 or x >= self.w or y >= self.h then return end
  self.px[y * self.w + x] = hex
  self.occ[y * self.w + x] = true
end
function Canvas:box(x, y, w, h, hex)
  for j = 0, h - 1 do for i = 0, w - 1 do self:put(x + i, y + j, hex) end end
end
function Canvas:disc(cx, cy, rx, ry, hex)
  for y = math.floor(cy - ry), math.ceil(cy + ry) do
    for x = math.floor(cx - rx), math.ceil(cx + rx) do
      local dx, dy = (x + 0.5 - cx) / rx, (y + 0.5 - cy) / ry
      if dx * dx + dy * dy <= 1 then self:put(x, y, hex) end
    end
  end
end
function Canvas:flipX()
  local np, no = {}, {}
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    local k = y * self.w + x
    if self.px[k] then
      local nk = y * self.w + (self.w - 1 - x)
      np[nk] = self.px[k]
      no[nk] = true
    end
  end end
  self.px, self.occ = np, no
end
function Canvas:outline()
  local solid = {}
  for k, v in pairs(self.occ) do solid[k] = v end
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    if not solid[y * self.w + x] then
      local hit = false
      for dy = -2, 2 do for dx = -2, 2 do
        if not hit and dx * dx + dy * dy <= 4.5 then
          local nx, ny = x + dx, y + dy
          if nx >= 0 and ny >= 0 and nx < self.w and ny < self.h
             and solid[ny * self.w + nx] then hit = true end
        end
      end end
      if hit then self:put(x, y, INK) end
    end
  end end
end
-- Crown light follows the contour column by column; a fixed horizontal band
-- reads as a stripe laid over a box. Dark tone sits where hair meets skin.
function Canvas:hair_shade(depth)
  for x = 0, self.w - 1 do
    local run = 0
    for y = 0, self.h - 1 do
      local v = self:get(x, y)
      if v == HAIR and run < depth then
        self:put(x, y, HAIRL)
        run = run + 1
      elseif v ~= HAIR then
        run = 99
      end
    end
  end
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    if self:get(x, y) == HAIR then
      for _, d in ipairs({ { -1, 0 }, { 1, 0 }, { 0, -1 }, { 0, 1 } }) do
        if self:get(x + d[1], y + d[2]) == SKIN then
          self:put(x, y, HAIRD)
          break
        end
      end
    end
  end end
end
function Canvas:blit(img)
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    local hex = self.px[y * self.w + x]
    if hex then img:putPixel(x, y, col(hex)) end
  end end
end

-- ---- hair silhouette --------------------------------------------------
-- Half-height 8.0 centred on y=10, so the oval spans rows 3..17 and the 2px
-- ink ring still fits when the whole body bobs up a row on the passing frames.
-- The old 10/9 oval peaked at y=-1 and every frame had a flat-cut crown sitting
-- on the top edge of the cell.
local function hair_hw(y)
  local t = (10 - y) / 8
  if math.abs(t) >= 1 then return -1 end
  return 8.5 * math.sqrt(1 - t * t)
end

-- Two straight runs meeting in a point, not an arc: a smooth curve reads soft,
-- a kink off-centre reads brisk. The vertex sits right of centre, so the fringe
-- sweeps across her brow.
local function hairline(x)
  return math.min(10, 6 + 0.55 * math.abs(x - 18))
end

-- In profile the hair has to cover the whole back of the skull and only open a
-- window over the face. Reusing the front-view hairline left the crown and the
-- back bare, which is what read as bald.
local function hairline_side(x)
  return math.max(6, math.min(15, 6 + 1.1 * (x - 12)))
end

-- A lock that leans off the head and tapers to a point. Blunt rectangles hang;
-- a strand that leaves the skull at an angle and ends in a tip reads as hair
-- with momentum. rows = {lean, width} per row from the anchor.
local function lock(c, x0, y0, rows, sway)
  for i, r in ipairs(rows) do
    local lean, w = r[1], r[2]
    local off = (i > #rows - 4) and sway or 0
    c:box(x0 + lean + off - math.floor((w - 1) / 2), y0 + i - 1, w, 1, HAIR)
  end
end

-- High, gathered, and long enough to clear the shoulder. Anchored above the
-- ear, so it reads as a ponytail rather than just "hair that grew down".
local LOCK_FRONT = { { 0, 5 }, { 0, 4 }, { -1, 4 }, { -1, 3 }, { -2, 3 },
                     { -2, 2 }, { -3, 2 }, { -3, 1 }, { -4, 1 }, { -4, 1 }, { -5, 1 } }
local LOCK_BACK  = { { 0, 5 }, { 0, 5 }, { 0, 4 }, { 0, 4 }, { 1, 4 }, { 1, 3 },
                     { 1, 3 }, { 1, 2 }, { 2, 2 }, { 2, 1 } }
local LOCK_SIDE  = { { 0, 4 }, { 1, 3 }, { 2, 3 }, { 3, 2 }, { 4, 2 }, { 5, 1 } }

-- Round spectacles: the only mark on her blank face, and the cue that reads
-- "detective" before the coat does. Lenses reuse the magnifier tint so the
-- palette stays at ten colours.
local function glasses_front(c, y)
  c:box(11, y, 4, 4, INK); c:box(12, y + 1, 2, 2, LENS)
  c:box(17, y, 4, 4, INK); c:box(18, y + 1, 2, 2, LENS)
  c:box(15, y + 1, 2, 1, INK)                     -- bridge
end

local function glasses_side(c, y)
  c:box(9, y, 4, 4, INK); c:box(10, y + 1, 2, 2, LENS)
  c:box(13, y + 1, 3, 1, INK)                     -- temple back to the hair
end

-- 5px ring with a pale lens and a short handle, drawn so it overlaps the hand:
-- separated by a gap of transparency the ink outline turned it into a block
-- floating next to her. hx sends the handle away from the body.
local function magnifier(c, x, y, hx)
  c:box(x, y, 5, 5, INK)
  c:box(x + 1, y + 1, 3, 3, LENS)
  c:put(x + (hx > 0 and 4 or 0), y + 5, INK)
  c:put(x + (hx > 0 and 5 or -1), y + 6, INK)
end

-- dir: 'down' | 'up' | 'left' | 'right'   phase: 0..3
local function figure(c, dir, phase)
  local bobY = (phase == 1 or phase == 3) and -1 or 0
  local side = (dir == 'left' or dir == 'right')
  local back = (dir == 'up')
  -- The hair and the scarf end lag behind the step. That lag is most of what
  -- reads as energy at 32px: the body barely moves, the loose parts swing.
  local lag = (phase == 1) and -1 or (phase == 3) and 1 or 0
  -- the leading hand's vertical offset, so the magnifier rides with the arm
  local armY = 0

  -- legs: the cropped coat leaves three rows of leg instead of two, and the
  -- stride is a pixel wider. Legs are where a walk cycle lives.
  local ly = 26 + bobY
  if side then
    local lead = ({ [0] = -3, [1] = -1, [2] = 3, [3] = 1 })[phase] or 0
    c:box(15 + lead, ly, 3, 3, SKIN)
    c:box(15 + lead, ly + 3, 4, 3, BOOT)
  else
    local a = (phase == 0) and 3 or (phase == 2) and -3 or 0
    local lift = (phase == 1) and -1 or (phase == 3) and 1 or 0
    local l1h = (lift < 0) and 2 or 3
    local l2h = (lift > 0) and 2 or 3
    c:box(13 - a, ly, 3, l1h, SKIN)
    c:box(13 - a, ly + l1h, 3, 3, BOOT)
    c:box(16 + a, ly, 3, l2h, SKIN)
    c:box(16 + a, ly + l2h, 3, 3, BOOT)
  end

  -- trench, cropped to the hip: body, lit shoulder band, lapels, belt,
  -- sleeves, hands. In profile the visible arm belongs at the FRONT edge -
  -- centred on the torso it crossed the belt and read as a plus sign.
  local tx, tw = side and 11 or 9, side and 11 or 14
  c:box(tx, 18 + bobY, tw, 9, COAT)
  c:box(tx, 18 + bobY, tw, 2, COATL)
  if not side then
    if back then
      -- from behind a trench shows the yoke across the shoulders and the vent
      -- down the centre. The front lapels leaking onto this view was the same
      -- bug the Lumine cycle had.
      c:box(10, 20 + bobY, 12, 1, COATD)
      c:box(15, 21 + bobY, 2, 7, COATD)
    else
      for i = 0, 3 do
        c:put(15 - i, 19 + bobY + i, COATD)
        c:put(16 + i, 19 + bobY + i, COATD)
      end
    end
    -- arms counter-swing: without this the two contact frames differ only by
    -- the leg lift, and the walk reads as sliding
    local las = ({ [0] = -1, [1] = 0, [2] = 1, [3] = 0 })[phase]
    armY = las
    c:box(7, 19 + bobY + las, 2, 7, COATD)
    c:box(23, 19 + bobY - las, 2, 7, COATD)
    c:box(7, 26 + bobY + las, 2, 2, SKIN)
    c:box(23, 26 + bobY - las, 2, 2, SKIN)
  else
    c:box(11, 19 + bobY, 2, 7, COATD)
    c:box(11, 26 + bobY, 2, 2, SKIN)
    -- the hem at her back lifts a pixel on the passing frames, so the coat has
    -- weight instead of being a box bolted to the waist
    c:box(20 + lag, 24 + bobY, 3, 3, COAT)
    c:box(20 + lag, 26 + bobY, 3, 1, COATD)
  end
  c:box(tx, 23 + bobY, tw, 2, COATD)              -- belt

  -- head: hair oval, face punched in, curved fringe
  for y = 0, 31 do for x = 0, 31 do
    local w = hair_hw(y - bobY)
    if w >= 0 and math.abs(x - 16) <= w then c:put(x, y, HAIR) end
  end end
  if not back then
    -- The face sits forward in profile, and the profile hairline runs down to
    -- the nape behind it; otherwise the crown and the back of the head are bare.
    local fx = side and (dir == 'left' and -2.5 or 2.5) or 0
    c:disc(16 + fx, 10 + bobY, side and 5 or 6, side and 6 or 6.5, SKIN)
    for x = 8, 24 do
      local hl = math.floor((side and hairline_side or hairline)(x - fx)) + bobY
      for y = 0, hl do
        local w = hair_hw(y - bobY)
        if w >= 0 and math.abs(x - 16) <= w then c:put(x, y, HAIR) end
      end
    end
  end

  -- Scarf: a collar band plus an end down the chest. Drawn after the head so
  -- the hair could not eat it, and before the tails so the hair hangs over it.
  -- From behind the band drops a row, otherwise it sits on the hair and reads
  -- as a ribbon rather than a scarf.
  local sy = (back and 19 or 18) + bobY
  local sx, sw = 10, 12
  if side then sx, sw = 11, 9 end
  if back then sx, sw = 12, 8 end   -- narrow from behind, or the tail turns the
                                    -- band into a bow
  c:box(sx, sy, sw, 2, SCARF)
  if not back then
    local ex = side and 16 or 18
    c:box(ex + lag, 20 + bobY, 2, 4, SCARF)
    c:box(ex + lag, 23 + bobY, 2, 1, SCARFD)
  end

  c:hair_shade(2)

  -- The ponytail is drawn after the shading pass, so a restarted hair column
  -- cannot pick up a crown-light stripe.
  if side then
    lock(c, 22, 8 + bobY, LOCK_SIDE, lag)
  elseif back then
    lock(c, 16, 16 + bobY, LOCK_BACK, lag)
  else
    lock(c, 9, 9 + bobY, LOCK_FRONT, lag)
  end

  -- spectacles sit under the fringe; 'right' is a mirror of 'left', so the
  -- profile only ever needs the near lens
  if not back then
    if side then glasses_side(c, 10 + bobY) else glasses_front(c, 10 + bobY) end
  end

  -- glass in the leading hand; sheathed when walking away. It rides with the
  -- arm swing, otherwise the hand moves and the glass does not.
  if not back then
    if side then magnifier(c, 6, 24 + bobY, -1)
    else magnifier(c, 24, 24 + bobY - armY, 1) end
  end
end

local function build_walk()
  local dirs = { 'down', 'left', 'right', 'up' }
  local spr = Sprite(32, 32)
  spr.layers[1].name = 'art'
  for i = 2, #dirs * 4 do spr:newFrame() end
  for d, dir in ipairs(dirs) do
    for ph = 0, 3 do
      local fr = spr.frames[(d - 1) * 4 + ph + 1]
      local c = Canvas.new(32, 32)
      figure(c, dir == 'right' and 'left' or dir, ph)
      if dir == 'right' then c:flipX() end
      c:outline()
      local img = Image(32, 32, spr.colorMode)
      c:blit(img)
      local lyr = spr.layers[1]
      local cel = lyr:cel(fr)
      if cel then cel.image = img; cel.position = Point(0, 0)
      else spr:newCel(lyr, fr, img, Point(0, 0)) end
    end
    spr:newTag((d - 1) * 4 + 1, (d - 1) * 4 + 4).name = 'walk_' .. dir
  end
  spr:saveAs(DIR .. 'player.aseprite')
  local tags = {}
  for _, t in ipairs(spr.tags) do
    tags[#tags + 1] = t.name .. ' ' .. t.fromFrame.frameNumber .. '-' .. t.toFrame.frameNumber
  end
  local frames = #spr.frames
  spr:close()
  return frames, table.concat(tags, ', ')
end

-- ---- bust portrait ----------------------------------------------------
local function skull_hw(y)
  if y < 11 or y > 45 then return -1 end
  if y <= 25 then return 12 * math.sqrt(math.max(0, 1 - ((25 - y) / 14) ^ 2)) end
  if y <= 35 then return 12 - 0.10 * (y - 25) end
  if y <= 42 then return 11.0 - 0.72 * (y - 35) end
  return 5.9 - 1.3 * (y - 42)
end

-- an egg taller than the skull, so the side strips reach the jaw
local function phair_hw(y)
  local t = (22 - y) / 22
  if math.abs(t) >= 1 then return -1 end
  return 16.5 * math.sqrt(1 - t * t)
end

local function p_hairline(x)
  return math.min(28, 19 + 0.7 * math.abs(x - 27))
end

local function build_portrait()
  local spr = Sprite(64, 64)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  local c = Canvas.new(64, 64)
  for y = 0, 63 do for x = 0, 63 do
    local w = phair_hw(y)
    if w >= 0 and math.abs(x - 32) <= w then c:put(x, y, HAIR) end
  end end
  local function hat(x, y)
    local w = skull_hw(y)
    return w >= 0 and math.abs(x - 32) <= w
  end
  for y = 0, 63 do for x = 0, 63 do if hat(x, y) then c:put(x, y, SKIN) end end end
  for x = 16, 48 do
    local hl = math.floor(p_hairline(x))
    for y = 0, hl do
      local w = phair_hw(y)
      if w >= 0 and math.abs(x - 32) <= w then c:put(x, y, HAIR) end
    end
  end
  for y = 43, 56 do for x = 28, 36 do c:put(x, y, SKIN) end end
  -- coat with lapels over the shoulders
  for x = 0, 63 do
    local d = math.abs(x - 32) / 30
    local top = 52 + 5 * (d ^ 2.6)
    for y = math.floor(top), 63 do c:put(x, y, COAT) end
    for y = math.floor(top), math.floor(top) + 2 do c:put(x, y, COATL) end
  end
  for i = 0, 9 do
    c:put(26 - i, 52 + i, COATD)
    c:put(38 + i, 52 + i, COATD)
  end
  c:hair_shade(3)
  -- scarf over the collar, hair hanging past the jaw over the scarf
  c:box(22, 49, 20, 4, SCARF)
  for x = 22, 41 do c:put(x, 52, SCARFD) end
  c:box(34, 53, 7, 11, SCARF)
  c:box(39, 53, 2, 11, SCARFD)
  -- one pointed lock over the shoulder, nothing on the other side: the
  -- asymmetry is the difference between "hair" and "a hairstyle"
  lock(c, 25, 40, { { 0, 7 }, { 0, 6 }, { -1, 6 }, { -1, 5 }, { -2, 5 }, { -2, 4 },
                    { -3, 4 }, { -3, 3 }, { -4, 3 }, { -4, 2 }, { -5, 2 },
                    { -5, 1 }, { -6, 1 }, { -6, 1 } }, 0)
  -- same spectacles, scaled up: 9px round lenses with a 1px rim
  for _, cx in ipairs({ 26, 38 }) do
    c:disc(cx, 28, 4.6, 4.6, INK)
    c:disc(cx, 28, 3.1, 3.1, LENS)
  end
  c:box(31, 27, 3, 1, INK)
  c:outline()
  c:blit(img)
  spr:saveAs(DIR .. 'avatar.aseprite')
  spr:saveCopyAs(DIR .. 'avatar_64.png')
  spr:close()
end

local function build_swatch()
  local p = { COAT, COATL, COATD, SCARF, SCARFD, HAIR, HAIRL, HAIRD,
              SKIN, LENS, BOOT, INK }
  local spr = Sprite(#p * 8, 16)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  for y = 0, 15 do for x = 0, #p * 8 - 1 do img:putPixel(x, y, col(INK)) end end
  for i, hex in ipairs(p) do
    for y = 1, 14 do for x = (i - 1) * 8 + 1, (i - 1) * 8 + 6 do img:putPixel(x, y, col(hex)) end end
  end
  spr:saveAs(DIR .. 'swatch.aseprite')
  spr:saveCopyAs(DIR .. 'swatch.png')
  spr:close()
  return #p
end

local frames, tags = build_walk()
local n = build_swatch()
build_portrait()
print('PLAYER_OK frames=' .. frames .. ' tags: ' .. tags .. ' | swatch ' .. n .. ' colours')
