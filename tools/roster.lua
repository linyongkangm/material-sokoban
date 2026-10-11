-- Suspect roster generator, 64x64 each. Run from Aseprite batch Lua, or via
-- the MCP with:  dofile('E:/Material/material-sokoban/tools/roster.lua')
--
-- Each skull is an AUTHORED profile: a list of (y, half-width) anchors, so the
-- cranial outline is a per-character choice rather than one formula with
-- different constants. `smooth` is part of the identity too -- rounding the
-- anchors gives a round dome, leaving them raw keeps hard polygon corners for
-- the square-jawed characters.

local DIR = 'E:/Material/material-sokoban/character/avatars/'
local INK = '#191922'

local function col(h)
  return Color(tonumber(string.sub(h, 2, 3), 16),
               tonumber(string.sub(h, 4, 5), 16),
               tonumber(string.sub(h, 6, 7), 16), 255)
end

-- Build a per-row half-width table from anchors, plus the derived landmarks
-- the hair and beard code needs.
local function skull(c)
  local HW = {}
  for y = 0, 63 do HW[y] = -1 end
  local a = c.prof
  for i = 1, #a - 1 do
    local y0, w0 = a[i][1], a[i][2]
    local y1, w1 = a[i + 1][1], a[i + 1][2]
    for y = y0, y1 do
      local t = (y1 == y0) and 0 or (y - y0) / (y1 - y0)
      HW[y] = w0 + (w1 - w0) * t
    end
  end
  if c.smooth then
    for _ = 1, c.smooth do
      local src = {}
      for y = 0, 63 do src[y] = HW[y] end
      for y = 1, 62 do
        if src[y - 1] >= 0 and src[y] >= 0 and src[y + 1] >= 0 then
          HW[y] = (src[y - 1] + 2 * src[y] + src[y + 1]) / 4
        end
      end
    end
  end
  local top, yc, yw, hwmax = 99, -1, 0, 0
  for y = 0, 63 do
    if HW[y] >= 0 then
      if y < top then top = y end
      if y > yc then yc = y end
      if HW[y] > hwmax then hwmax, yw = HW[y], y end
    end
  end
  c.hw_, c.top, c.yc, c.yw, c.hwmax = HW, top, yc, yw, hwmax
  c.chin = HW[yc - 1] >= 0 and HW[yc - 1] or 0
end

-- how far the hair stands outside the skull at this row
local function rim(c, y)
  local s = c.rim_style or c.hair_style
  if s == 'cap' then                       -- cropped, follows the skull
    if y < c.top then return 0 end
    if y <= c.yw - 4 then return c.rmax end
    return math.max(0, c.rmax - 0.7 * (y - (c.yw - 4)))
  elseif s == 'bob' then                   -- flares past the jaw, hard-cut base
    if y < c.top then return 0 end
    if y <= c.yc - 9 then return c.rmax end
    if y <= c.yc + 2 then return c.rmax + c.flare end
    return 0
  elseif s == 'long' then                  -- straight strands continue below
    if y < c.top then return 0 end
    if y <= c.yc then return c.rmax end
    return 0
  elseif s == 'horseshoe' then             -- bald crown, hair only at the sides
    if y < c.yw - 3 then return 0 end
    if y <= c.yc - 3 then return c.rmax end
    return 0
  elseif s == 'swept' then                 -- fuller on one side than the other
    if y < c.top then return 0 end
    if y <= c.yw then return c.rmax end
    return math.max(0, c.rmax - 0.5 * (y - c.yw))
  end
  return 0
end

local function in_hair(c, x, y)
  -- An afro is a real circle. Dilating the head by a constant just yields a
  -- fatter oval, which is the sameness this file exists to avoid.
  if c.hair_style == 'afro' then
    if y > c.yc + 1 then return false end
    local dx, dy = x + 0.5 - 32, y + 0.5 - (c.top + (c.afro_y or 9))
    -- the mass has to overhang the cheeks or it reads as a rim, not an afro
    local r = c.hwmax + (c.afro_r or 8)
    return dx * dx + dy * dy <= r * r
  end
  if c.shaved and x < 32 then return false end   -- undercut: one side bare
  local r = rim(c, y)
  if r <= 0 then return false end
  local ri = math.ceil(r)
  for dy = -ri, ri do for dx = -ri, ri do
    if dx * dx + dy * dy <= r * r + 0.4 then
      local hw = c.hw_[y + dy]
      if hw and hw >= 0 and math.abs(x + dx - 32) <= hw then return true end
    end
  end end
  return false
end

local function in_panel(c, x, y)
  if not (c.panels and y > c.yc and y <= c.panel_end) then return false end
  local edge = c.chin + c.rmax
  local lo = 32 - edge - c.pw
  local hi = 32 + edge
  return (x >= lo and x <= lo + c.pw) or (x >= hi - c.pw and x <= hi)
end

local function disc(px, py, rx, ry, x, y)
  local dx, dy = (x + 0.5 - px) / rx, (y + 0.5 - py) / ry
  return dx * dx + dy * dy <= 1
end

local function build(c)
  skull(c)
  local spr = Sprite(64, 64)
  spr.layers[1].name = 'art'
  local img = spr.cels[1].image
  local occ = {}
  local cmap = {}
  for y = 0, 63 do
    occ[y] = {}
    cmap[y] = {}
    for x = 0, 63 do occ[y][x] = false cmap[y][x] = nil end
  end
  local function pset(x, y, h)
    if x >= 0 and y >= 0 and x < 64 and y < 64 then
      img:putPixel(x, y, col(h)) occ[y][x] = true cmap[y][x] = h
    end
  end
  local function hat(x, y)
    local hw = c.hw_[y]
    return hw ~= nil and hw >= 0 and math.abs(x - 32) <= hw
  end

  if c.bun then
    for y = 0, 63 do for x = 0, 63 do
      if disc(c.bun[1], c.bun[3], c.bun[2], c.bun[4], x, y) then pset(x, y, c.hair) end
    end end
  end
  if c.pony then
    for y = 0, 63 do for x = 0, 63 do
      if disc(c.pony[1], c.pony[3], c.pony[2], c.pony[4], x, y) then pset(x, y, c.hair) end
    end end
  end

  for y = 0, 63 do for x = 0, 63 do
    if in_hair(c, x, y) then pset(x, y, c.hair) end
  end end
  for y = 0, 63 do for x = 0, 63 do
    if hat(x, y) then pset(x, y, c.skin) end
  end end
  -- fringe: independent slopes either side give a side part. A symmetric arc
  -- mirrors the outer edge and turns the hair into a frame.
  local fl, fr = c.fringe_l or 0.14, c.fringe_r or 0.14
  for x = 12, 52 do
    local hl = c.fringe + (x < 32 and fl * (32 - x) or fr * (x - 32))
    for y = 0, math.floor(hl) do
      if hat(x, y) then pset(x, y, c.hair) end
    end
  end
  if c.beard then
    -- U-shaped hairline: dips lowest under the mouth, climbs to the sideburns
    for y = 0, 63 do for x = 0, 63 do
      if hat(x, y) then
        local t = ((x - 32) / (c.hwmax + 1)) ^ 2
        if y >= c.beard + c.beard_rise * (1 - t) then pset(x, y, c.hair) end
      end
    end end
    for y = c.yc + 1, c.yc + c.beard_drop do
      local t = (y - c.yc) / c.beard_drop
      for x = 32 - c.chin + 1, 32 + c.chin - 1 do
        if math.abs(x - 32) <= (c.chin - 1) * (1 - t * t) then pset(x, y, c.hair) end
      end
    end
  end

  -- A uniform rim reads as a border, not as hair. Darken the hair where it
  -- touches skin and catch light along the crown so the mass gets structure.
  if c.hairl then
    for y = c.top, c.top + 2 do for x = 0, 63 do
      if cmap[y][x] == c.hair then pset(x, y, c.hairl) end
    end end
  end
  if c.haird then
    for y = 0, 63 do for x = 0, 63 do
      if cmap[y][x] == c.hair then
        local touching = false
        for _, d in ipairs({ { -1, 0 }, { 1, 0 }, { 0, -1 }, { 0, 1 } }) do
          local nx2, ny = x + d[1], y + d[2]
          if nx2 >= 0 and ny >= 0 and nx2 < 64 and ny < 64 and cmap[ny][nx2] == c.skin then
            touching = true
          end
        end
        if touching then pset(x, y, c.haird) end
      end
    end end
  end

  local nx = c.neck
  for y = c.yc - 4, 56 do for x = 32 - nx, 32 + nx do pset(x, y, c.skin) end end
  for x = 32 - nx, 32 + nx do pset(x, c.yc + 2, c.skind) pset(x, c.yc + 3, c.skind) end

  for x = 0, 63 do
    local d = math.abs(x - 32) / 30
    local top = c.sh_base + c.sh_amp * (d ^ c.sh_pow)
    for y = math.floor(top), 63 do pset(x, y, c.shirt) end
    for y = math.floor(top), math.floor(top) + 1 do pset(x, y, c.shirth) end
  end
  -- strands fall in front of the shoulders
  for y = 0, 63 do for x = 0, 63 do
    if in_panel(c, x, y) then pset(x, y, c.hair) end
  end end

  local ink = col(INK)
  for y = 0, 63 do for x = 0, 63 do
    if not occ[y][x] then
      local hit = false
      for dy = -2, 2 do for dx = -2, 2 do
        if not hit and dx * dx + dy * dy <= 4.5 then
          local nx2, ny = x + dx, y + dy
          if nx2 >= 0 and ny >= 0 and nx2 < 64 and ny < 64 and occ[ny][nx2] then hit = true end
        end
      end end
      if hit then img:putPixel(x, y, ink) end
    end
  end end

  spr:saveAs(DIR .. c.n .. '.aseprite')
  spr:saveCopyAs(DIR .. c.n .. '_1x.png')
  spr:close()
  return c.n .. ' top=' .. c.top .. ' wide@' .. c.yw .. '(' .. string.format('%.1f', c.hwmax) .. ')'
      .. ' chin@' .. c.yc .. '(' .. string.format('%.1f', c.chin) .. ')'
end

-- Profiles are (y, half-width). Read them as a skull silhouette:
-- where it is widest, how fast the crown closes, how blunt the jaw is.
local CHARS = {
  -- tall egg: widest high, long taper, small pointed chin
  { n='ada', skin='#E8B48C', skind='#C58A62', hair='#3B2A20',
    shirt='#5CACB5', shirth='#7CC3CB', smooth=2, fringe=16, neck=4,
    prof={{6,0},{10,7},{15,11},{22,13},{30,12},{37,9},{42,5.5},{44,0}},
    hair_style='cap', rmax=2,
    sh_base=51, sh_amp=6, sh_pow=2.4 },

  -- wide brick: near-flat top, vertical sides, blunt low jaw. The bob is
  -- parted to one side and shaded where it meets the skin, so the hair stops
  -- reading as a uniform frame around a punched-out window.
  { n='brigitte', skin='#EFC9AE', skind='#C99B7C', hair='#C6C6C6',
    haird='#9A9AA0', hairl='#E4E4E8',
    shirt='#68497F', shirth='#8A6AA3', smooth=0, fringe=16, fringe_l=0.45, fringe_r=0.05,
    neck=4,
    prof={{9,10},{11,14},{13,14.5},{33,14},{39,12.5},{43,10},{45,0}},
    hair_style='bob', rmax=3, flare=2,
    sh_base=50, sh_amp=7, sh_pow=2.0 },

  -- oblong: high narrow crown, parallel cheeks, narrow jaw, longest face
  { n='cameron', skin='#C98E62', skind='#A56E48', hair='#241C18',
    shirt='#E0A93F', shirth='#F1CB72', smooth=2, fringe=17, neck=4,
    prof={{4,0},{8,8},{14,12},{24,13},{33,12},{40,9.5},{45,6},{47,0}},
    hair_style='long', rmax=3, panels=true, panel_end=58, pw=6,
    sh_base=51, sh_amp=6, sh_pow=2.6 },

  -- pear/heart: narrow temples, widest at the jaw, then a quick point
  { n='darlene', skin='#F0C8A0', skind='#D2A176', hair='#8E4A2A',
    shirt='#B1E2DE', shirth='#D2F0ED', smooth=2, fringe=16, neck=4,
    prof={{8,0},{11,8},{16,11},{24,12.5},{32,14},{38,12.5},{42,8},{44,0}},
    hair_style='cap', rmax=2, bun={32, 9, 6, 7},
    sh_base=50, sh_amp=7, sh_pow=2.2 },

  -- block: flat top starting wide, straight sides, heavy square jaw.
  -- fringe=0 keeps the crown bare: the horseshoe rim alone supplies the sides,
  -- and any hairline value here would repaint the bald scalp as a cap.
  { n='edison', skin='#D9A07A', skind='#B87E58', hair='#6F7E7B',
    shirt='#A3ABD2', shirth='#C3C9E4', smooth=0, fringe=0, neck=6,
    prof={{9,11},{11,14.5},{13,15},{30,15},{37,14.5},{41,13},{43,11},{45,0}},
    hair_style='horseshoe', rmax=2, beard=26, beard_rise=6, beard_drop=4,
    sh_base=47, sh_amp=9, sh_pow=1.3 },

  -- drum: roundest cranium, widest at the temples, short rounded chin
  { n='vinita', skin='#E8B48C', skind='#C58A62', hair='#D8B45C',
    shirt='#A55142', shirth='#C8786A', smooth=3, fringe=14, neck=4,
    prof={{7,0},{10,10},{14,13.5},{20,14.5},{27,14},{33,11},{38,7},{40,0}},
    hair_style='swept', rmax=3, pony={43, 7, 30, 13},
    sh_base=51, sh_amp=6, sh_pow=2.5 },

  -- batch 2: profiles deliberately placed outside batch 1's envelope
  -- (batch 1: widest y 13..32, face end 40..47, chin half-width 2.6..5.5)

  -- angular diamond: widest at the temples, hard corners, shaved on one side.
  -- Shirt stays pale so the rust hair separates from it without brightening
  -- into his skin tone (a lighter rust measured 1.10:1 against the face).
  -- The jaw holds width to the chin: an earlier version tapered to 1.5 and
  -- gave him a cone face.
  { n='felix', skin='#E8B48C', skind='#C58A62', hair='#B85C38',
    shirt='#C8E0E6', shirth='#E0ECF0', smooth=0, fringe=16, neck=4,
    prof={{7,0},{11,9},{15,13},{19,14.5},{26,13},{34,11.5},{41,9},{44,6.5},{46,0}},
    hair_style='undercut', rim_style='cap', rmax=3, shaved=true,
    sh_base=51, sh_amp=6, sh_pow=2.2 },

  -- round crown + true circular afro, soft wide jaw
  { n='gwen', skin='#C98E62', skind='#A56E48', hair='#3A2A22',
    shirt='#E0685A', shirth='#F0917F', smooth=2, fringe=17, neck=4,
    prof={{9,0},{12,9},{16,12.5},{20,13.5},{28,13},{35,11},{40,8},{42,0}},
    hair_style='afro', rmax=3, afro_r=6, afro_y=10,
    sh_base=50, sh_amp=7, sh_pow=2.0 },

  -- longest face in the set, very close-cropped hair with a small topknot
  { n='hassan', skin='#A56E48', skind='#84552F', hair='#2F2A3A',
    shirt='#4E8FA0', shirth='#6FB2C2', smooth=2, fringe=15, neck=5,
    prof={{6,0},{10,8},{16,11.5},{26,12.5},{36,12},{44,9},{49,6},{51,0}},
    hair_style='cap', rmax=1, bun={32, 6, 5, 4},
    sh_base=53, sh_amp=6, sh_pow=2.6 },

  -- widest point deliberately low (broad jaw), heavy curtain hair
  { n='ingrid', skin='#F0C8A0', skind='#D2A176', hair='#6B4A3A',
    shirt='#C0A0D8', shirth='#DCBFEF', smooth=1, fringe=16, neck=5,
    prof={{8,0},{11,9},{15,12},{22,13.5},{30,14.2},{35,14.5},{40,12},{43,9},{45,0}},
    hair_style='long', rmax=3, panels=true, panel_end=56, pw=8,
    sh_base=51, sh_amp=6, sh_pow=2.4 },

  -- broad square skull with a full dark beard, low hairline
  { n='jorge', skin='#D9A07A', skind='#B87E58', hair='#4A4038',
    shirt='#D08B45', shirth='#E8B070', smooth=0, fringe=15, neck=6,
    prof={{9,0},{12,12},{14,14},{22,14.5},{32,14},{38,12},{41,10},{43,0}},
    hair_style='cap', rmax=2, beard=27, beard_rise=5, beard_drop=5,
    sh_base=48, sh_amp=8, sh_pow=1.6 },

  -- shortest face, chin-length bob flaring wide past the jaw
  { n='kim', skin='#EFC9AE', skind='#C99B7C', hair='#A67C52',
    shirt='#2E3D75', shirth='#4E5D95', smooth=3, fringe=16, neck=4,
    prof={{10,0},{13,9},{16,12},{19,13},{26,12.5},{32,10.5},{37,8},{39,0}},
    hair_style='bob', rmax=3, flare=4,
    sh_base=51, sh_amp=6, sh_pow=2.5 },
}

local out = {}
for _, c in ipairs(CHARS) do out[#out + 1] = build(c) end
print('ROSTER_V3 skull profiles:')
for _, s in ipairs(out) do print('  ' .. s) end

-- Exposed so character_pack.lua can derive tokens and swatches from the same
-- palette instead of duplicating it and drifting. Additive only: the avatar
-- design above is locked and untouched.
ROSTER_CHARS = CHARS
ROSTER_INK = INK
ROSTER_DIR = DIR
