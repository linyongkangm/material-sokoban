-- Lumine (荧) from Genshin Impact - full-body pixel portrait, 64x100.
-- Run via the MCP with:
--   local ok, err = pcall(dofile, 'D:/Materials/sokoban/art/lumine.lua')
--   print(ok and 'done' or err)
--
-- Reference: Baidu Baike's entry describes her as "蓄着金色短发，发上稍高位置饰有
-- 两朵坎瑞亚国花，近耳处饰有羽毛，穿着为蓝白配色的异域服装" - short golden hair,
-- two Cathay nation flowers set high, a feather by the ear, blue and white
-- dress. The first pass here was waist-length from memory and was wrong; the
-- lengths below follow the source. Only one source was reachable (fandom and
-- miyoushe both failed), so treat the rest as interpretation.
--
-- The house style is broken in exactly one place: the roster and the Sokoban
-- heroine are featureless, but Lumine's eyes are part of her silhouette, so
-- she gets amber irises and a lash line. Everything else stays flat fills,
-- 2px ink, no ramps.

local DIR = 'D:/Materials/sokoban/lumine/'
local W, H = 64, 100
local CX = 32
local TOP = 4            -- air above the crown, so the ink outline is not cut

local INK    = '#241E33'
local HAIR   = '#E3C076'   -- deep enough against #FFE2C6 skin to stay two
local HAIRL  = '#F6E3A6'   -- shapes, not one pale blob (the Brigitte trap)
local HAIRD  = '#B4924C'
local SKIN   = '#FFE2C6'
local SKIND  = '#E9BE9B'
local EYE    = '#F2A93B'
local EYED   = '#8E5514'
local EYEW   = '#FFF7E4'
local MOUTH  = '#D5806F'
local DRESS  = '#F6F4EE'
local DRESSD = '#D6D2C8'
local GOLD   = '#E8B93C'
local GOLDL  = '#FFD974'
local SASH   = '#3A4A78'
local SASHD  = '#28325A'
local SHORTS = '#2E2B44'
local SOCK   = '#F2EFE8'
local SHOE   = '#3A3550'
local PETAL  = '#CFEFF3'

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
function Canvas:shiftY(dy)
  local np, no = {}, {}
  for k, v in pairs(self.px) do
    local x, y = k % self.w, math.floor(k / self.w)
    if y + dy < self.h then
      local nk = (y + dy) * self.w + x
      np[nk] = v
      no[nk] = true
    end
  end
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
function Canvas:blit(img)
  for y = 0, self.h - 1 do for x = 0, self.w - 1 do
    local hex = self.px[y * self.w + x]
    if hex then img:putPixel(x, y, col(hex)) end
  end end
end

-- ---- silhouette curves -------------------------------------------------
-- Short, per the source: a bob that ends at the jaw, not a mass hanging to
-- the waist. The hair is still its own shape rather than the head dilated -
-- wider crown, near-straight sides, blunt tips a hair's width past the cheeks.
local function hair_hw(y)
  if y > 26 then return -1 end
  if y <= 13 then return 12.5 * (1 - ((13 - y) / 14) ^ 2) ^ 0.45 end
  if y <= 21 then return 12.5 - 0.25 * (y - 13) end
  return math.max(9.4, 10.5 - 0.15 * (y - 21))
end

-- 15px of face inside a 25px head, so the temple locks have 5px of their own.
-- When the locks overlap the face the ink boundary doubles up and the whole
-- face turns into a narrow column with a mouth on it.
local function face_hw(y)
  if y < 8 or y > 26 then return -1 end
  if y <= 18 then return 8 * (1 - ((18 - y) / 10) ^ 2) ^ 0.45 end
  -- rounded jaw, not a straight taper
  return 8 * math.sqrt(math.max(0, 1 - ((y - 18) / 8) ^ 2))
end

-- Fringe as authored points, interpolated: anime hair is cut in triangles, and
-- a smooth arc here would read soft. The centre dips, the temples run long -
-- but only to y=18, because lower than that the points cover her cheeks and
-- the face collapses to the strip between the eyes.
local FRINGE = { { 19, 18 }, { 25, 12 }, { 29, 15 }, { 33, 12 }, { 37, 15 },
                 { 42, 12 }, { 47, 18 } }
local function fringe_y(x)
  if x <= FRINGE[1][1] then return FRINGE[1][2] end
  for i = 2, #FRINGE do
    local a, b = FRINGE[i - 1], FRINGE[i]
    if x <= b[1] then
      local t = (x - a[1]) / (b[1] - a[1])
      return a[2] + (b[2] - a[2]) * t
    end
  end
  return FRINGE[#FRINGE][2]
end

-- A strand that leaves the head at an angle and tapers to a point. Blunt
-- rectangles hang; these read as hair with weight and movement.
local function strand(c, x0, y0, y1, w0, lean, hex)
  local n = y1 - y0
  for i = 0, n do
    local t = i / n
    local w = math.max(1, math.floor(w0 * (1 - 0.75 * t) + 0.5))
    local x = x0 + math.floor(lean * t * t + 0.5)
    c:box(x - math.floor((w - 1) / 2), y0 + i, w, 1, hex or HAIR)
  end
end

-- Ink on the cloth/hair side of any skin boundary. Pale blonde on pale skin is
-- one mass otherwise, and a white dress swallows a wrist the same way.
local function ink_against(c, from)
  local hits = {}
  for y = 0, H - 1 do for x = 0, W - 1 do
    local v = c:get(x, y)
    if v == HAIR or v == HAIRD or v == DRESS or v == SOCK then
      for _, d in ipairs({ { -1, 0 }, { 1, 0 }, { 0, -1 }, { 0, 1 } }) do
        if c:get(x + d[1], y + d[2]) == from then
          hits[#hits + 1] = y * W + x
          break
        end
      end
    end
  end end
  for _, k in ipairs(hits) do c.px[k] = INK end
end

-- Kept at file scope and exported so the walk cycle draws the same face.
local function eye(c, x, inward)
  c:box(x, 16, 4, 4, EYE)
  c:box(x, 15, 4, 1, INK)
  c:box(inward > 0 and x or x + 2, 16, 2, 2, EYEW)     -- glint, outer top
  c:box(inward > 0 and x + 2 or x, 18, 2, 2, EYED)     -- pupil, toward the nose
  c:put(inward > 0 and x + 3 or x, 19, INK)
end

-- Two Cathay nation flowers set high on one side, a feather at the ear.
-- s shifts them with the head so the profile can place them.
local function ornaments(c, s)
  s = s or 0
  c:disc(37 + s, 6, 2.4, 2.4, PETAL); c:disc(37 + s, 6, 1, 1, GOLD)
  c:disc(42 + s, 10, 2.8, 2.8, PETAL); c:disc(42 + s, 10, 1.2, 1.2, GOLD)
  c:box(43 + s, 13, 2, 5, PETAL)
  c:put(44 + s, 17, HAIRD)
end

local function build(c)
  -- back hair
  for y = 0, H - 1 do for x = 0, W - 1 do
    local w = hair_hw(y)
    if w >= 0 and math.abs(x - CX) <= w then c:put(x, y, HAIR) end
  end end

  -- legs: shorts, bare thigh, knee-highs with a gold band, low shoes. The two
  -- legs keep a 2px gap of transparency - the ink outline floods it and the
  -- seam comes out exactly the house line weight.
  c:box(25, 57, 14, 6, SHORTS)
  strand(c, 28, 62, 67, 5, 0, SKIN)
  strand(c, 36, 62, 67, 5, 0, SKIN)
  c:box(26, 68, 5, 16, SOCK)
  c:box(33, 68, 5, 16, SOCK)
  c:box(26, 68, 5, 2, GOLD)
  c:box(33, 68, 5, 2, GOLD)
  c:box(25, 84, 6, 5, SHOE)
  c:box(33, 84, 6, 5, SHOE)

  -- dress: bodice, indigo sash with a gold buckle, flared skirt with a gold hem
  for y = 31, 43 do
    local hw = math.floor(8.5 - (y - 31) * 0.22)
    c:box(CX - hw, y, 2 * hw + 1, 1, DRESS)
    c:put(CX - hw, y, DRESSD)
    c:put(CX + hw, y, DRESSD)
  end
  c:box(24, 43, 16, 4, SASH)
  c:box(24, 46, 16, 1, SASHD)
  c:box(29, 44, 6, 3, GOLD)
  c:box(30, 45, 4, 1, GOLDL)
  for y = 47, 58 do
    local hw = math.floor(9 + (y - 47) * 0.45)
    c:box(CX - hw, y, 2 * hw + 1, 1, y >= 57 and GOLD or DRESS)
    if y < 57 then c:put(CX - hw, y, DRESSD); c:put(CX + hw, y, DRESSD) end
  end
  for i = 0, 5 do
    c:put(27 + i, 31 + i, GOLD)
    c:put(37 - i, 31 + i, GOLD)
  end

  -- detached sleeves: 1px of air from the bodice, flaring at the wrist into a
  -- dark cuff with gold trim, hands below. Kept narrow - wide sleeves plus a
  -- wide bodice fuse into one horizontal shelf across the shoulders.
  for y = 32, 47 do
    local wide = y >= 44
    local x, w = wide and 15 or 17, wide and 7 or 6
    c:box(x, y, w, 1, DRESS)
    c:box(64 - x - w, y, w, 1, DRESS)
    c:put(x, y, DRESSD)
    c:put(64 - x - 1, y, DRESSD)
  end
  c:box(15, 46, 7, 2, SASH)
  c:box(42, 46, 7, 2, SASH)
  c:box(15, 45, 7, 1, GOLD)
  c:box(42, 45, 7, 1, GOLD)
  c:box(17, 48, 5, 5, SKIN)
  c:box(42, 48, 5, 5, SKIN)

  -- neck, then the face over it
  c:box(29, 24, 7, 8, SKIN)
  for y = 0, H - 1 do for x = 0, W - 1 do
    local w = face_hw(y)
    if w >= 0 and math.abs(x - CX) <= w then c:put(x, y, SKIN) end
  end end

  -- fringe cut in points, then the two long front locks
  for x = 0, W - 1 do
    local hl = math.floor(fringe_y(x))
    for y = 0, hl do
      local w = hair_hw(y)
      if w >= 0 and math.abs(x - CX) <= w then c:put(x, y, HAIR) end
    end
  end
  strand(c, 22, 12, 27, 4, -2)
  strand(c, 42, 12, 27, 4, 2)

  -- eyes: a 1px lash line, an amber iris, a 2x2 glint, and the pupil pushed to
  -- the lower centre. Anything thinner and the face reads as squinting.
  eye(c, 26, 1)
  eye(c, 35, -1)
  c:box(30, 22, 4, 1, MOUTH)
  c:put(33, 21, MOUTH)

  ornaments(c, 0)

  ink_against(c, SKIN)

  -- crown light follows the contour column by column; a fixed horizontal band
  -- reads as a stripe laid over a box
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

-- Exported so the walk cycle is built from these exact curves and colours
-- rather than a copy that can drift.
LUMINE = {
  W = W, H = H, CX = CX, TOP = TOP, DIR = DIR, Canvas = Canvas, col = col,
  INK = INK, HAIR = HAIR, HAIRL = HAIRL, HAIRD = HAIRD, SKIN = SKIN,
  SKIND = SKIND, EYE = EYE, EYED = EYED, EYEW = EYEW, MOUTH = MOUTH,
  DRESS = DRESS, DRESSD = DRESSD, GOLD = GOLD, GOLDL = GOLDL, SASH = SASH,
  SASHD = SASHD, SHORTS = SHORTS, SOCK = SOCK, SHOE = SHOE, PETAL = PETAL,
  hair_hw = hair_hw, face_hw = face_hw, fringe_y = fringe_y,
  strand = strand, ink_against = ink_against, eye = eye, ornaments = ornaments,
}

local spr = Sprite(W, H)
spr.layers[1].name = 'art'
local img = spr.cels[1].image
local c = Canvas.new(W, H)
build(c)
c:shiftY(TOP)
c:outline()

-- the Traveler's star, added after the outline so it stays a clean sparkle
-- instead of getting an ink ring
for _, s in ipairs({ { 55, 26, 4 }, { 8, 44, 3 } }) do
  local x, y, r = s[1], s[2], s[3]
  c:box(x - r, y, 2 * r + 1, 1, GOLDL)
  c:box(x, y - r, 1, 2 * r + 1, GOLDL)
  c:put(x, y, DRESS)
end
c:blit(img)

local seen, n = {}, 0
for _, v in pairs(c.px) do
  if not seen[v] then seen[v] = true; n = n + 1 end
end
local minx, miny, maxx, maxy = W, H, -1, -1
for k in pairs(c.occ) do
  local x, y = k % W, math.floor(k / W)
  if x < minx then minx = x end
  if x > maxx then maxx = x end
  if y < miny then miny = y end
  if y > maxy then maxy = y end
end

-- saveCopyAs does not abort on a failed write, so delete first and prove the
-- file exists afterwards
local png = DIR .. 'lumine.png'
pcall(os.remove, png)
spr:saveAs(DIR .. 'lumine.aseprite')
spr:saveCopyAs(png)
local fh = io.open(png, 'rb')
if not fh then error('failed to write ' .. png) end
fh:close()
spr:close()

print(string.format('LUMINE_OK %dx%d colours=%d content x %d..%d y %d..%d',
                    W, H, n, minx, maxx, miny, maxy))
