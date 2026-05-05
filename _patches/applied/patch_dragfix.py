#!/usr/bin/env python3
"""
HI. Extension follow-up patch — make the "unknown company" badge draggable.

The unknown-company badge (?) appears on sites without a HI Grade.
Currently it returns from the function before the drag handler is attached.
This patch extracts the drag logic into a reusable function and calls it
for both badge variants.
"""
import sys, os, shutil

CHANGES = []

def patch_file(path, replacements):
    if not os.path.exists(path):
        print(f"⚠ Not found: {path}")
        return False
    src = open(path).read()
    original = src
    for label, old, new in replacements:
        if old in src:
            src = src.replace(old, new)
            CHANGES.append(f"  ✓ {os.path.basename(path)}: {label}")
        elif new in src:
            CHANGES.append(f"  ⊙ {os.path.basename(path)}: {label} (already applied)")
        else:
            CHANGES.append(f"  ✗ {os.path.basename(path)}: {label} (pattern not found)")
    if src != original:
        if not os.path.exists(path + '.dragfix.bak'):
            shutil.copy(path, path + '.dragfix.bak')
        open(path, 'w').write(src)
        return True
    return False


CONTENT_JS_PATCHES = [
    # Patch 1: Make the unknown-company badge draggable by calling makeDraggable() before return
    ("Make unknown-badge draggable",
     """    reqBadge.addEventListener('click', () => {
      window.open('https://thehibalance.org/#request&company=' + encodeURIComponent(domain), '_blank');
    });
    document.body.appendChild(reqBadge);
    return;
  }""",
     """    reqBadge.addEventListener('click', (e) => {
      if (reqBadge._wasDragged) { reqBadge._wasDragged = false; return; }
      window.open('https://thehibalance.org/#request&company=' + encodeURIComponent(domain), '_blank');
    });
    document.body.appendChild(reqBadge);
    makeBadgeDraggable(reqBadge);
    return;
  }"""),

    # Patch 2: Extract the drag logic from createBadge into a reusable function
    # Replace the inline drag code inside createBadge with a function call,
    # and add the makeBadgeDraggable() function definition above createBadge.
    ("Extract drag logic into reusable makeBadgeDraggable()",
     """  document.body.appendChild(badge);

  // ═══ DRAGGABLE BADGE ═══
  // Load saved position
  try {
    const saved = localStorage.getItem('hi_badge_pos');
    if (saved) {
      const pos = JSON.parse(saved);
      badge.style.bottom = 'auto';
      badge.style.left = Math.min(pos.x, window.innerWidth - 60) + 'px';
      badge.style.top = Math.min(pos.y, window.innerHeight - 70) + 'px';
    }
  } catch(e) {}

  let dragStartX, dragStartY, badgeStartX, badgeStartY, isDragging = false;
  
  badge.addEventListener('mousedown', (e) => {
    if (e.target.closest('.human-panel')) return;
    isDragging = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    const rect = badge.getBoundingClientRect();
    badgeStartX = rect.left;
    badgeStartY = rect.top;
    
    const onMove = (e2) => {
      const dx = e2.clientX - dragStartX;
      const dy = e2.clientY - dragStartY;
      if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
        isDragging = true;
        badge.style.bottom = 'auto';
        badge.style.left = Math.max(0, Math.min(badgeStartX + dx, window.innerWidth - 60)) + 'px';
        badge.style.top = Math.max(0, Math.min(badgeStartY + dy, window.innerHeight - 70)) + 'px';
        badge.style.transition = 'none';
      }
    };
    
    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      badge.style.transition = '';
      if (isDragging) {
        badge._wasDragged = true;
        try {
          localStorage.setItem('hi_badge_pos', JSON.stringify({
            x: parseInt(badge.style.left),
            y: parseInt(badge.style.top)
          }));
        } catch(e) {}
      }
    };
    
    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });""",
     """  document.body.appendChild(badge);
  makeBadgeDraggable(badge);"""),

    # Patch 3: Add the makeBadgeDraggable function definition before createBadge
    ("Insert makeBadgeDraggable() function",
     """/**
 * Create the floating score badge on the page.
 */
function createBadge(profile, filterResult, prefs) {""",
     """/**
 * Make any badge element draggable + persist position to localStorage.
 * Used for both the scored badge and the "unknown company" mini badge.
 */
function makeBadgeDraggable(badge) {
  // Load saved position
  try {
    const saved = localStorage.getItem('hi_badge_pos');
    if (saved) {
      const pos = JSON.parse(saved);
      badge.style.bottom = 'auto';
      badge.style.left = Math.min(pos.x, window.innerWidth - 60) + 'px';
      badge.style.top = Math.min(pos.y, window.innerHeight - 70) + 'px';
    }
  } catch(e) {}

  let dragStartX, dragStartY, badgeStartX, badgeStartY, isDragging = false;

  badge.addEventListener('mousedown', (e) => {
    if (e.target.closest('.human-panel')) return;
    isDragging = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    const rect = badge.getBoundingClientRect();
    badgeStartX = rect.left;
    badgeStartY = rect.top;

    const onMove = (e2) => {
      const dx = e2.clientX - dragStartX;
      const dy = e2.clientY - dragStartY;
      if (Math.abs(dx) > 5 || Math.abs(dy) > 5) {
        isDragging = true;
        badge.style.bottom = 'auto';
        badge.style.left = Math.max(0, Math.min(badgeStartX + dx, window.innerWidth - 60)) + 'px';
        badge.style.top = Math.max(0, Math.min(badgeStartY + dy, window.innerHeight - 70)) + 'px';
        badge.style.transition = 'none';
      }
    };

    const onUp = () => {
      document.removeEventListener('mousemove', onMove);
      document.removeEventListener('mouseup', onUp);
      badge.style.transition = '';
      if (isDragging) {
        badge._wasDragged = true;
        try {
          localStorage.setItem('hi_badge_pos', JSON.stringify({
            x: parseInt(badge.style.left),
            y: parseInt(badge.style.top)
          }));
        } catch(e) {}
      }
    };

    document.addEventListener('mousemove', onMove);
    document.addEventListener('mouseup', onUp);
  });
}

/**
 * Create the floating score badge on the page.
 */
function createBadge(profile, filterResult, prefs) {"""),
]


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--dir', default='.')
    args = parser.parse_args()
    root = os.path.abspath(args.dir)
    print(f"Patching extension at: {root}\n")

    if not os.path.exists(os.path.join(root, 'manifest.json')):
        print(f"ERROR: No manifest.json at {root}. Run from human-edge/ or pass --dir")
        sys.exit(1)

    patch_file(os.path.join(root, 'content.js'), CONTENT_JS_PATCHES)

    print("Changes:")
    for c in CHANGES:
        print(c)
    print()

if __name__ == '__main__':
    main()
