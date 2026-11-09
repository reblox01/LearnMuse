# Room placement

You place furniture in a Basement Tycoon room render, or you
check a room sample by eye, using real-room logic. A render
that only composites is not a pass. Every item must read at
a believable size and stand on a real surface, in a place a
person would actually put it.

This skill comes from a real correction. On 8 and 9 Nov 2026
room renders were judged by eye and failed on placement:
a fridge too small, a lamp sitting on the floor, a rug on
a box, a bed in the wrong spot. Sohail's rule for fixing
them was short: use logic. The rule below is that logic,
written down so the next render starts from it instead of
re-discovering it.

## When to use

- Placing furniture in a Basement Tycoon room, in any of
  the four themes: Classic, Sketch, Neon, Cozy.
- Checking a room sample by eye before showing it to
  Sohail, or before wiring a new layout into /room.
- Deriving positions and sizes for a new item from the
  full-room picture, not from a single cutout.

Do not use it for shop icons, inventory lists, or
economy numbers. It is about where things stand in the
room picture, nothing else.

## The rules

Place furniture the way a real room works:

- Furniture against walls and in corners. A sofa, a bed,
  a desk, and a fridge belong with their back to a wall
  or tucked into a corner, never floating in the middle
  of the open floor.
- Rug flat on the open floor. A rug is never on a box,
  on a table, or half under a wall. It lies flat, in the
  open space where people walk.
- Neon and LED up high near the roof. A neon sign is
  decoration on the upper wall, never at floor level and
  never behind furniture where it cannot be seen.
- Poster at eye level. A poster hangs on a wall where a
  standing person looks at it, not near the floor and
  not near the roof.
- Lamp on a real surface, never on the floor. A lamp
  sits on a desk, a side table, or boxes. A lamp on the
  floor is a failure, even if the render looks tidy.
- Plant and cat on the floor, in an open spot. They
  stand on the floor where there is room, not on
  furniture and not blocking a doorway or a rug.
- Console near the TV. A console belongs beside or
  below the TV, close enough that the pairing reads
  at a glance.
- Fridge in a corner, at middle size, never bigger than
  the sofa. A fridge too small reads as a toy. A fridge
  bigger than the sofa reads as a wall. Middle size,
  in a corner, is the only correct read.
- Nothing on top of another item, except the TV on the
  bookshelf. The TV sits on the bookshelf. Everything
  else stands on the floor or on its own surface.

## How to place a new item

1. Look at the full room first, not the item alone.
   Find the wall or corner it belongs against, and the
   open floor it must not block.
2. Measure the item in the full-room picture. Use the
   bounding box from the final picture of the full
   room, then scale the front-facing cutout down so it
   fits without hiding the TV, the bookshelf, the lamp,
   or the desk behind it.
3. Put it on a real surface. Floor items stand on the
   floor. Lamp and small items stand on a desk, a side
   table, or boxes. Nothing floats, nothing hangs in
   mid-air unless it is neon, a poster, or a light
   meant to be up high.
4. Check the size against the sofa. The sofa is the
   reference object in the room. If the new item is
   bigger than the sofa and it is not supposed to be,
   shrink it. If it is so small it disappears next to
   the sofa, grow it.
5. Check the sample by eye in every theme the room
   ships in. A placement that works in Classic can
   fail in Neon if a glow hides an edge, or in Sketch
   if a line merges with a wall.

## Validated result

This rule was validated, not just written down. Room
samples v5 were verified by eye in all four themes,
all seven suites passed, commit 221cdc6, deploy
dep-dbp0l2ks728c73c0v2h0 live 18:03 UTC 9 Nov 2026,
and a live /room test at 19:02 local confirmed 745
coins, 120 style, 8/20 items, all eight owned items
visible. That is the standard a new placement must
meet: verified by eye, in all themes, with a live
test, not just a render that completed.

## Common pitfalls

- Judging a render only by whether it rendered. A
  composite that finishes is not a pass. Scale and
  placement are judged by eye, and a floating lamp
  or a wall-mounted TV is a failure even when the
  tests pass.
- Sizing from the cutout alone. A cutout has no
  room around it. Size from the full-room picture,
  or the item will hide what is behind it.
- Putting a rug, a lamp, or a small item where it
  looks neat in isolation, instead of where a real
  room puts it. Neat is not the test. Real is.
- Asking Sohail where each item goes. He already
  gave the rule: use logic. Apply it, show the
  sample, and let him correct the sample by eye.
- Treating one theme as proof for all four. Check
  every theme before calling a placement done.

## Hard rules

- Use logic, do not ask for placements item by item.
- Never show a sample you have not checked by eye
  for size and surface.
- Never put a lamp on the floor, a rug on a box, or
  a fridge bigger than the sofa.
- A placement that fails by eye is a failure, even
  when every test suite passes.

## Verification checklist

- [ ] Every item is against a wall, in a corner, or
  flat on the open floor, as its kind requires.
- [ ] Rug is flat on the open floor, not on a box.
- [ ] Neon and LED are up high near the roof.
- [ ] Poster is at eye level.
- [ ] Lamp is on a real surface, never on the floor.
- [ ] Plant and cat are on the floor in an open spot.
- [ ] Console is near the TV.
- [ ] Fridge is in a corner, middle size, never bigger
  than the sofa.
- [ ] Nothing is on top of another item, except the TV
  on the bookshelf.
- [ ] Each item reads at a believable size against the
  sofa and stands on a real surface.
- [ ] Sample checked by eye in all four themes before
  it was shown.
