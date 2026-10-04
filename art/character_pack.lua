-- Per-character deliverable pack: avatar, colour swatch, and a map token.
-- Run via the MCP with:
--   dofile('D:/Materials/sokoban/art/character_pack.lua')
--
-- Palettes come from roster.lua's CHARS table, so the three products can never
-- disagree with the avatar. Editable .aseprite sources land in art/character/;
-- only the PNGs go into the delivery folder.

dofile('D:/Materials/sokoban/art/roster.lua')

local OUT = 'D:/Materials/sokoban/character/'
local SRC = 'D:/Materials/sokoban/art/character/'
local INK = ROSTER_INK
local CHARS = ROSTER_CHARS

local function col(h)
  return Color(tonumber(string.sub(h, 2, 3), 16),
               tonumber(string.sub(h, 4, 5), 16),
               tonumber(string.sub(h, 6, 7), 16), 255)
end

-- saveCopyAs does not abort the script when a write fails (a locked target is
-- enough), which silently leaves the previous run's file in place and looking
-- valid. Delete first so a failure shows up as a missing file, then confirm.
local function save_png(spr, path)
  pcall(os.remove, path)
  spr:saveCopyAs(path)
  local fh = io.open(path, 'rb')
  if not fh then error('failed to write ' .. path) end
  fh:close()
end

-- The character's primary colour is their shirt. It leads the swatch, owns the
-- token's outer band and drives the UI accent bar - all three read `primary`
-- from the manifest below, so nothing samples pixels to guess at it any more.
local function primary(c)
  assert(c.shirt, c.n .. ' has no shirt colour')
  return c.shirt
end

-- the character's own palette, primary first, then the rest head-to-body
local function palette(c)
  local p = { primary(c), c.shirth, c.hair }
  if c.hairl then p[#p + 1] = c.hairl end
  if c.haird then p[#p + 1] = c.haird end
  p[#p + 1] = c.skin
  p[#p + 1] = c.skind
  p[#p + 1] = INK
  return p
end

local function new_sprite(w, h)
  local spr = Sprite(w, h)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  return spr, img
end

-- token: concentric bands, primary colour owning the widest ring
local function token(c)
  local spr, img = new_sprite(32, 32)
  local cx, cy = 15.5, 15.5
  local bands = {
    { 14.0, INK }, { 13.0, c.shirth }, { 11.0, primary(c) },
    { 8.0, INK }, { 7.0, c.hair }, { 2.5, c.skin },
  }
  for y = 0, 31 do for x = 0, 31 do
    local d = math.sqrt((x + 0.5 - cx) ^ 2 + (y + 0.5 - cy) ^ 2)
    for _, b in ipairs(bands) do
      if d <= b[1] then img:putPixel(x, y, col(b[2])) end
    end
  end end
  spr:saveAs(SRC .. c.n .. '_token.aseprite')
  save_png(spr, OUT .. c.n .. '_token.png')
  spr:close()
end

-- swatch: one cell per colour, ink-separated, width follows the palette size
local function swatch(c)
  local p = palette(c)
  local w, h, cell = #p * 8, 16, 8
  local spr, img = new_sprite(w, h)
  for y = 0, h - 1 do for x = 0, w - 1 do img:putPixel(x, y, col(INK)) end end
  for i, hex in ipairs(p) do
    local x0 = (i - 1) * cell
    for y = 1, h - 2 do
      for x = x0 + 1, x0 + cell - 2 do img:putPixel(x, y, col(hex)) end
    end
  end
  spr:saveAs(SRC .. c.n .. '_swatch.aseprite')
  save_png(spr, OUT .. c.n .. '_swatch.png')
  spr:close()
  return #p
end

-- avatar: re-export the locked sprite under the delivery name
local function avatar(c)
  local spr = app.open(ROSTER_DIR .. c.n .. '.aseprite')
  save_png(spr, OUT .. c.n .. '_avatar.png')
  spr:close()
end

-- Single source of truth for anything downstream (the card accent bar used to
-- sample a pixel out of the avatar to guess at this).
local function write_manifest()
  local parts = {}
  for _, c in ipairs(CHARS) do
    parts[#parts + 1] = string.format('    {"name":"%s","primary":"%s","palette":["%s"]}',
      c.n, primary(c), table.concat(palette(c), '","'))
  end
  local f = io.open(OUT .. 'pack.json', 'w')
  f:write('{\n  "characters": [\n' .. table.concat(parts, ',\n') .. '\n  ]\n}\n')
  f:close()
end

local report = {}
for _, c in ipairs(CHARS) do
  avatar(c)
  local n = swatch(c)
  token(c)
  report[#report + 1] = string.format('%-9s primary %s  swatch %d colours', c.n, primary(c), n)
end
write_manifest()
print('CHARACTER_PACK -> ' .. OUT .. ' (+ pack.json manifest)')
for _, r in ipairs(report) do print('  ' .. r) end
