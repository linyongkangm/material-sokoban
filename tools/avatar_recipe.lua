-- Murdoku-style featureless bust avatar, 64x64.
-- Feed to mcp__aseprite__run_lua_script with filename=<target>.aseprite.
-- Every shape is a row-width function, so the silhouette stays smooth: no
-- ellipse+rectangle joins, which is what produced square heads and temple tabs
-- in earlier attempts.
--
-- To build a roster variant, change only the palette block below.
--   hair  - sets the person apart at 1x
--   skin  - keep >= 3 steps from hair so the cap never merges with the face
--   shirt - the accent bar in the UI card should match this

local SKIN  = '#E8B48C'
local SKIND = '#C58A62'   -- chin shadow, the only second tone on the face
local HAIR  = '#33302E'
local TEAL  = '#5CACB5'
local TEALH = '#7CC3CB'   -- flat highlight band along the shoulder curve
local INK   = '#191922'

local spr = app.activeSprite
local lyr
for _, l in ipairs(spr.layers) do if l.name == 'art' then lyr = l end end
local cel = lyr:cel(spr.frames[1])
if not cel then
  cel = spr:newCel(lyr, spr.frames[1], Image(spr.width, spr.height, spr.colorMode), Point(0, 0))
end
-- assign first, then re-read: after `cel.image = ...` Aseprite owns the buffer,
-- and drawing into the old local reference silently goes nowhere
cel.image = Image(spr.width, spr.height, spr.colorMode)
cel.position = Point(0, 0)
local img = cel.image

local function col(hex)
  return Color(tonumber(string.sub(hex, 2, 3), 16),
               tonumber(string.sub(hex, 4, 5), 16),
               tonumber(string.sub(hex, 6, 7), 16), 255)
end
local occ = {}
for y = 0, 63 do occ[y] = {} for x = 0, 63 do occ[y][x] = false end end
local function pset(x, y, c)
  if x >= 0 and y >= 0 and x < 64 and y < 64 then
    img:putPixel(x, y, c)
    occ[y][x] = true
  end
end

-- Dome, near-parallel cheeks to the jaw angle, then a fast round to the chin.
-- A steady taper from temple to chin reads as a column, not a face.
local function head_hw(y)
  if y < 7 or y > 43 then return -1 end
  if y <= 24 then return 15 * math.sqrt(math.max(0, 1 - ((24 - y) / 17) ^ 2)) end
  if y <= 36 then return 15 - 0.10 * (y - 24) end
  if y <= 41 then return 13.8 - 1.10 * (y - 36) end
  return 8.3 - 1.60 * (y - 41)
end
local function head_at(x, y)
  local hw = head_hw(y)
  return hw >= 0 and math.abs(x - 32) <= hw
end

-- Hair rim fades continuously to zero at the cheekbone so the FACE stays the
-- widest part of the silhouette; a stepped falloff leaves a tab at each temple.
local function rim(y)
  return math.max(0, math.min(3, 3 - 0.30 * (y - 19)))
end
local function hair_at(x, y)
  local r = rim(y)
  if r <= 0 then return false end
  local ri = math.ceil(r)
  for dy = -ri, ri do for dx = -ri, ri do
    if dx * dx + dy * dy <= r * r + 0.4 and head_at(x + dx, y + dy) then return true end
  end end
  return false
end

for y = 0, 63 do for x = 0, 63 do
  if hair_at(x, y) then pset(x, y, col(HAIR)) end
end end
for y = 0, 63 do for x = 0, 63 do
  if head_at(x, y) then pset(x, y, col(SKIN)) end
end end
-- fringe on a shallow arc, not a straight cut
for x = 14, 50 do
  local hl = 16 + 0.14 * math.abs(x - 32)
  for y = 0, math.floor(hl) do
    if head_at(x, y) then pset(x, y, col(HAIR)) end
  end
end
-- neck narrower than the jaw, so the chin overhangs it
for y = 40, 56 do for x = 29, 36 do pset(x, y, col(SKIN)) end end
for x = 29, 36 do pset(x, 44, col(SKIND)) pset(x, 45, col(SKIND)) end
-- trapezius curve cropped by the frame: shoulders have no corners to look square
for x = 0, 63 do
  local d = math.abs(x - 32) / 30
  local top = 50 + 6 * (d ^ 2.4)
  for y = math.floor(top), 63 do pset(x, y, col(TEAL)) end
  for y = math.floor(top), math.floor(top) + 1 do pset(x, y, col(TEALH)) end
end

-- 2px ink border, dilated here rather than via outline_cel (which adds 1px per
-- call). occ tracks what we drew, so no getPixel round-trip is needed.
local ink = col(INK)
for y = 0, 63 do for x = 0, 63 do
  if not occ[y][x] then
    local hit = false
    for dy = -2, 2 do for dx = -2, 2 do
      if not hit and dx * dx + dy * dy <= 4.5 then
        local nx, ny = x + dx, y + dy
        if nx >= 0 and ny >= 0 and nx < 64 and ny < 64 and occ[ny][nx] then hit = true end
      end
    end end
    if hit then img:putPixel(x, y, ink) end
  end
end end

spr:saveAs(spr.filename)
print('AVATAR_OK')
