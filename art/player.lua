-- Protagonist: 32x32, four-direction walk cycle, plus a 64x64 portrait.
-- Run via the MCP with:  dofile('D:/Materials/sokoban/art/player.lua')
--
-- Style is the locked flat one: pastel fills, 2px ink silhouette, no ramps.
-- Palette matches art/murdoku/tiles/player.aseprite so the hero and the tile
-- set stay one family. Frames are laid out as 4 per direction:
--   0 contact-left, 1 passing, 2 contact-right, 3 passing
-- The passing frames sit 1px higher, which is what sells the step.

local DIR = 'D:/Materials/sokoban/player/'
local INK   = '#191922'
local SKIN  = '#E8B48C'
local SKIND = '#C58A62'
local HAIR  = '#33302E'
local SH    = '#5CACB5'   -- primary
local SHL   = '#7CC3CB'
local SHD   = '#2A5A68'
local PANTS = '#68497F'
local PANTSD= '#4E3760'
local BOOT  = '#2A2F3A'
local WHITE = '#FEFEFE'

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
-- 2px ink silhouette, dilated with a round kernel so corners stay soft
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
function Canvas:blit(img)
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    local hex = self.px[y * self.w + x]
    if hex then img:putPixel(x, y, col(hex)) end
  end end
end
-- left and right are mirrors; drawing both by hand only produced two nearly
-- identical rows
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

-- dir: 'down' | 'up' | 'left' | 'right'   phase: 0..3
local function figure(c, dir, phase)
  local bob = (phase == 1 or phase == 3) and -1 or 0
  local side = (dir == 'left' or dir == 'right')
  local back = (dir == 'up')
  local hw = side and 5 or 6.5             -- narrower than the shoulders

  -- legs: a 2px stance shift plus the body bob is what makes the step read
  local ly, lh = 25 + bob, 6
  if side then
    local lead = (phase == 0) and -2 or (phase == 2) and 2 or 0
    c:box(14 + lead, ly, 4, lh, PANTS)
    c:box(14 + lead, ly + lh - 2, 5, 2, BOOT)
  else
    local a = (phase == 0) and 2 or (phase == 2) and -2 or 0
    local l1, l2 = 11 - a, 18 + a
    c:box(l1, ly, 3, lh, PANTS)
    c:box(l2, ly, 3, lh, PANTS)
    c:box(l1 - 1, ly + lh - 2, 4, 2, BOOT)
    c:box(l2, ly + lh - 2, 4, 2, BOOT)
  end

  -- torso
  local tx = side and 11 or 9
  local tw = side and 10 or 14
  c:box(tx, 16 + bob, tw, 10, SH)
  c:box(tx, 16 + bob, tw, 2, SHL)          -- one flat highlight band, nothing more
  if not side then
    c:box(tx + 1, 25 + bob, tw - 2, 1, PANTSD)   -- belt
  end

  -- arms: swing opposite the legs, and stay attached to the torso
  if side then
    local sw = (phase == 0) and 1 or (phase == 2) and -1 or 0
    c:box(15 + sw * 2, 18 + bob, 3, 7, SHD)
    c:box(15 + sw * 2, 25 + bob, 3, 2, SKIN)
  else
    local sw = (phase == 0) and -1 or (phase == 2) and 1 or 0
    c:box(7, 18 + bob + sw, 2, 7, SHD)
    c:box(23, 18 + bob - sw, 2, 7, SHD)
    c:box(7, 25 + bob + sw, 2, 2, SKIN)     -- hands
    c:box(23, 25 + bob - sw, 2, 2, SKIN)
  end

  -- head: skull disc, hair cap above the brow line, then the face
  local hy = 10 + bob
  local face = side and (dir == 'left' and -1.5 or 1.5) or 0
  c:disc(16, hy, hw, 7, SKIN)
  if back then
    c:disc(16, hy - 1, hw + 1, 7.5, HAIR)   -- seen from behind: all hair
  else
    -- cap centred high: at hy-5 the hairline lands at y~10, leaving the brow
    -- clear. A cap centred any lower buried the eyes.
    c:disc(16 + face * 0.5, hy - 5, hw + 1, 5, HAIR)
    if side then
      c:disc(16 + face, hy + 1, hw - 1, 5.5, SKIN)
      c:box(16 + face * 2, hy + 1, 2, 2, INK)          -- one eye in profile
    else
      c:box(13, hy + 4, 6, 4, SKIN)                    -- jaw
      c:box(12, hy + 2, 2, 2, INK)                     -- eyes
      c:box(18, hy + 2, 2, 2, INK)
      c:box(15, hy + 5, 2, 1, SKIND)                   -- mouth
    end
  end
end

local function build_walk()
  local dirs = { 'down', 'left', 'right', 'up' }
  local spr = Sprite(32, 32)
  spr.layers[1].name = 'art'
  -- first frame already exists; add the remaining 15
  for i = 2, #dirs * 4 do spr:newFrame() end
  for d, dir in ipairs(dirs) do
    for ph = 0, 3 do
      local idx = (d - 1) * 4 + ph
      local fr = spr.frames[idx + 1]
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
    local tag = spr:newTag((d - 1) * 4 + 1, (d - 1) * 4 + 4)
    tag.name = 'walk_' .. dir        -- Tag.looped is read-only in 1.3
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

local function build_portrait()
  local spr = Sprite(64, 64)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  local c = Canvas.new(64, 64)
  -- bust: authored skull, hair cap, cropped shoulders (same rules as the roster)
  local function hw(y)
    if y < 9 or y > 45 then return -1 end
    if y <= 24 then return 14 * math.sqrt(math.max(0, 1 - ((24 - y) / 15) ^ 2)) end
    if y <= 36 then return 14 - 0.12 * (y - 24) end
    if y <= 43 then return 12.6 - 0.9 * (y - 36) end
    return 6.3 - 1.6 * (y - 43)
  end
  local function hat(x, y)
    local w = hw(y)
    return w >= 0 and math.abs(x - 32) <= w
  end
  for y = 0, 63 do for x = 0, 63 do
    local r = math.max(0, math.min(3, 3 - 0.30 * (y - 19)))
    if r > 0 then
      local ri = math.ceil(r)
      for dy = -ri, ri do for dx = -ri, ri do
        if dx * dx + dy * dy <= r * r + 0.4 and hat(x + dx, y + dy) then c:put(x, y, HAIR) end
      end end
    end
  end end
  for y = 0, 63 do for x = 0, 63 do if hat(x, y) then c:put(x, y, SKIN) end end end
  for x = 14, 50 do
    local hl = 17 + 0.13 * math.abs(x - 32)
    for y = 0, math.floor(hl) do if hat(x, y) then c:put(x, y, HAIR) end end
  end
  for y = 42, 58 do for x = 28, 36 do c:put(x, y, SKIN) end end
  for x = 28, 36 do c:put(x, 46, SKIND) c:put(x, 47, SKIND) end
  for x = 0, 63 do
    local d = math.abs(x - 32) / 30
    local top = 52 + 5 * (d ^ 2.6)
    for y = math.floor(top), 63 do c:put(x, y, SH) end
    for y = math.floor(top), math.floor(top) + 1 do c:put(x, y, SHL) end
  end
  c:outline()
  c:blit(img)
  spr:saveAs(DIR .. 'avatar.aseprite')
  spr:saveCopyAs(DIR .. 'avatar_64.png')
  spr:close()
end

local function build_swatch()
  local p = { SH, SHL, SHD, HAIR, SKIN, SKIND, PANTS, BOOT, INK }
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
