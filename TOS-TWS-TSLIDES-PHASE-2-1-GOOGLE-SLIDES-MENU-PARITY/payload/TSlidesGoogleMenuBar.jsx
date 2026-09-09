import { useEffect, useRef, useState } from "react";

const TOP_MENUS = [
  ["file", "File"],
  ["edit", "Edit"],
  ["view", "View"],
  ["insert", "Insert"],
  ["slide", "Slide"],
  ["format", "Format"],
  ["arrange", "Arrange"],
  ["tools", "Tools"],
  ["extensions", "Extensions"],
  ["help", "Help"],
];

const ALT_MENU_KEYS = { f: "file", e: "edit", v: "view", i: "insert", s: "slide", o: "format", r: "arrange", t: "tools", h: "help" };

function separator() {
  return { separator: true };
}

export function TSlidesGoogleMenuBar({
  canEdit,
  canShare,
  selectedCount = 0,
  selectedType = "",
  slideCount = 0,
  activeSlideIndex = 0,
  actions,
}) {
  const [openMenu, setOpenMenu] = useState("");
  const [openSubmenu, setOpenSubmenu] = useState("");
  const rootRef = useRef(null);

  const hasSelection = selectedCount > 0;
  const hasMultiSelection = selectedCount > 1;
  const hasThreeSelection = selectedCount > 2;
  const isText = selectedType === "text";

  const menus = {
    file: [
      { label: "New slide", shortcut: "Ctrl+M", enabled: canEdit, action: actions.newSlide },
      separator(),
      { label: "Rename", enabled: canEdit, action: actions.rename },
      { label: "Version history", action: actions.versionHistory },
      { label: "Share", enabled: canShare, action: actions.share },
      separator(),
      {
        label: "Download",
        items: [
          { label: "Microsoft PowerPoint (.pptx)", action: actions.downloadPptx },
          { label: "PDF document (.pdf)", action: actions.downloadPdf },
        ],
      },
      separator(),
      { label: "Print", shortcut: "Ctrl+P", action: actions.print },
      { label: "Present", shortcut: "Ctrl+F5", action: actions.present },
    ],
    edit: [
      { label: "Undo", shortcut: "Ctrl+Z", enabled: canEdit, action: actions.undo },
      { label: "Redo", shortcut: "Ctrl+Y", enabled: canEdit, action: actions.redo },
      separator(),
      { label: "Cut", shortcut: "Ctrl+X", enabled: canEdit && hasSelection, action: actions.cut },
      { label: "Copy", shortcut: "Ctrl+C", enabled: hasSelection, action: actions.copy },
      { label: "Paste", shortcut: "Ctrl+V", enabled: canEdit, action: actions.paste },
      { label: "Duplicate", shortcut: "Ctrl+D", enabled: canEdit && hasSelection, action: actions.duplicate },
      separator(),
      { label: "Delete", shortcut: "Delete", enabled: canEdit && hasSelection, danger: true, action: actions.deleteSelection },
      { label: "Select all elements", shortcut: "Ctrl+A", enabled: hasSelection || canEdit, action: actions.selectAll },
    ],
    view: [
      { label: "Full screen", action: actions.fullscreen },
      { label: "Present", shortcut: "Ctrl+F5", action: actions.present },
      separator(),
      { label: "Speaker notes", action: actions.speakerNotes },
      { label: "Filmstrip", checked: true, disabled: true },
    ],
    insert: [
      { label: "Text box", enabled: canEdit, action: actions.addText },
      { label: "Image", enabled: canEdit, action: actions.addImage },
      {
        label: "Shape",
        enabled: canEdit,
        items: [
          { label: "Rectangle", action: actions.addRectangle },
          { label: "Ellipse", action: actions.addEllipse },
        ],
      },
      {
        label: "Line",
        enabled: canEdit,
        items: [
          { label: "Line", action: actions.addLine },
          { label: "Arrow", action: actions.addArrow },
        ],
      },
      separator(),
      { label: "New slide", shortcut: "Ctrl+M", enabled: canEdit, action: actions.newSlide },
    ],
    slide: [
      { label: "New slide", shortcut: "Ctrl+M", enabled: canEdit, action: actions.newSlide },
      { label: "Duplicate slide", shortcut: "Ctrl+D", enabled: canEdit, action: actions.duplicateSlide },
      { label: "Delete slide", enabled: canEdit && slideCount > 1, danger: true, action: actions.deleteSlide },
      separator(),
      {
        label: "Apply layout",
        enabled: canEdit,
        items: [
          { label: "Title", action: actions.layoutTitle },
          { label: "Title + content", action: actions.layoutTitleContent },
          { label: "Image + text", action: actions.layoutImageText },
          { label: "Two columns", action: actions.layoutTwoColumns },
        ],
      },
      {
        label: "Change theme",
        enabled: canEdit,
        items: [
          { label: "Light", action: actions.themeLight },
          { label: "Dark", action: actions.themeDark },
          { label: "Blue", action: actions.themeBlue },
          { label: "Gold", action: actions.themeGold },
        ],
      },
      separator(),
      { label: "Move slide up", enabled: canEdit && activeSlideIndex > 0, action: actions.moveSlideUp },
      { label: "Move slide down", enabled: canEdit && activeSlideIndex < slideCount - 1, action: actions.moveSlideDown },
    ],
    format: [
      { label: "Bold", shortcut: "Ctrl+B", enabled: canEdit && hasSelection && isText, action: actions.bold },
      separator(),
      {
        label: "Opacity",
        enabled: canEdit && hasSelection,
        items: [
          { label: "100%", action: () => actions.opacity(1) },
          { label: "75%", action: () => actions.opacity(.75) },
          { label: "50%", action: () => actions.opacity(.5) },
          { label: "25%", action: () => actions.opacity(.25) },
        ],
      },
      {
        label: "Rotate",
        enabled: canEdit && hasSelection,
        items: [
          { label: "Rotate clockwise 15°", action: actions.rotateClockwise },
          { label: "Rotate counterclockwise 15°", action: actions.rotateCounterclockwise },
        ],
      },
    ],
    arrange: [
      {
        label: "Order",
        enabled: canEdit && hasSelection,
        items: [
          { label: "Bring to front", action: actions.bringToFront },
          { label: "Send to back", action: actions.sendToBack },
        ],
      },
      {
        label: "Align",
        enabled: canEdit && hasSelection,
        items: [
          { label: "Left", action: actions.alignLeft },
          { label: "Center", action: actions.alignCenter },
          { label: "Right", action: actions.alignRight },
          { label: "Top", action: actions.alignTop },
          { label: "Middle", action: actions.alignMiddle },
          { label: "Bottom", action: actions.alignBottom },
        ],
      },
      {
        label: "Distribute",
        enabled: canEdit && hasThreeSelection,
        items: [
          { label: "Horizontally", action: actions.distributeHorizontal },
          { label: "Vertically", action: actions.distributeVertical },
        ],
      },
      separator(),
      { label: "Group", shortcut: "Ctrl+G", enabled: canEdit && hasMultiSelection, action: actions.group },
      { label: "Ungroup", shortcut: "Ctrl+Shift+G", enabled: canEdit && hasSelection, action: actions.ungroup },
      separator(),
      {
        label: "Rotate",
        enabled: canEdit && hasSelection,
        items: [
          { label: "Rotate clockwise 15°", action: actions.rotateClockwise },
          { label: "Rotate counterclockwise 15°", action: actions.rotateCounterclockwise },
        ],
      },
    ],
    tools: [
      { label: "Comments", action: actions.comments },
      { label: "Version history", action: actions.versionHistory },
      { label: "Speaker notes", action: actions.speakerNotes },
      separator(),
      { label: "Keyboard shortcuts", shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
    ],
    extensions: [
      { label: "No extensions installed", disabled: true },
    ],
    help: [
      { label: "Keyboard shortcuts", shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
      { label: "T-Slides help", action: actions.help },
    ],
  };

  function closeMenus() {
    setOpenMenu("");
    setOpenSubmenu("");
  }

  function chooseMenu(menuId) {
    setOpenSubmenu("");
    setOpenMenu((current) => current === menuId ? "" : menuId);
  }

  function cycleMenu(delta) {
    const currentIndex = Math.max(0, TOP_MENUS.findIndex(([id]) => id === openMenu));
    const nextIndex = (currentIndex + delta + TOP_MENUS.length) % TOP_MENUS.length;
    setOpenSubmenu("");
    setOpenMenu(TOP_MENUS[nextIndex][0]);
  }

  function runItem(item) {
    if (item.disabled || item.enabled === false || item.items?.length) return;
    item.action?.();
    closeMenus();
  }

  function handleRootKeyDown(event) {
    if (!openMenu) return;
    if (event.key === "Escape") {
      event.preventDefault();
      closeMenus();
      return;
    }
    if (event.key === "ArrowRight") {
      event.preventDefault();
      cycleMenu(1);
      return;
    }
    if (event.key === "ArrowLeft") {
      event.preventDefault();
      cycleMenu(-1);
      return;
    }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      rootRef.current?.querySelector(`[data-menu-panel="${openMenu}"] button:not(:disabled)`)?.focus();
    }
  }

  useEffect(() => {
    function handlePointerDown(event) {
      if (!rootRef.current?.contains(event.target)) closeMenus();
    }
    function handleKeyDown(event) {
      if (event.key === "Escape" && openMenu) {
        event.preventDefault();
        closeMenus();
        return;
      }
      if (event.altKey && !event.ctrlKey && !event.metaKey) {
        const menuId = ALT_MENU_KEYS[event.key.toLowerCase()];
        if (menuId) {
          event.preventDefault();
          setOpenSubmenu("");
          setOpenMenu(menuId);
        }
      }
    }
    window.addEventListener("pointerdown", handlePointerDown);
    window.addEventListener("keydown", handleKeyDown);
    return () => {
      window.removeEventListener("pointerdown", handlePointerDown);
      window.removeEventListener("keydown", handleKeyDown);
    };
  }, [openMenu]);

  function renderItems(items, parentKey) {
    return items.map((item, index) => {
      const key = `${parentKey}-${index}`;
      if (item.separator) return <div key={key} className="tws-slides-google-menu-separator" role="separator" />;
      const disabled = item.disabled || item.enabled === false;
      const hasSubmenu = Boolean(item.items?.length);
      return (
        <div key={key} className="tws-slides-google-menu-item-wrap" onPointerEnter={() => setOpenSubmenu(hasSubmenu ? key : "")}>
          <button
            type="button"
            role="menuitem"
            disabled={disabled}
            className={`tws-slides-google-menu-item${item.danger ? " is-danger" : ""}`}
            onClick={() => hasSubmenu ? setOpenSubmenu((current) => current === key ? "" : key) : runItem(item)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" && hasSubmenu) {
                event.preventDefault();
                setOpenSubmenu(key);
              }
              if (event.key === "Escape") closeMenus();
            }}
          >
            <span className="tws-slides-google-menu-check">{item.checked ? "✓" : ""}</span>
            <span className="tws-slides-google-menu-label">{item.label}</span>
            <span className="tws-slides-google-menu-shortcut">{item.shortcut || ""}</span>
            <span className="tws-slides-google-menu-arrow">{hasSubmenu ? "›" : ""}</span>
          </button>
          {hasSubmenu && openSubmenu === key && (
            <div className="tws-slides-google-menu-panel is-submenu" role="menu">
              {renderItems(item.items, key)}
            </div>
          )}
        </div>
      );
    });
  }

  return (
    <div ref={rootRef} className="tws-slides-google-menu-bar" role="menubar" aria-label="Google Slides style menus" onKeyDown={handleRootKeyDown}>
      {TOP_MENUS.map(([id, label]) => (
        <div key={id} className="tws-slides-google-top-menu">
          <button
            type="button"
            role="menuitem"
            aria-haspopup="menu"
            aria-expanded={openMenu === id}
            className={`tws-slides-google-menu-trigger${openMenu === id ? " is-open" : ""}`}
            onClick={() => chooseMenu(id)}
            onPointerEnter={() => { if (openMenu && openMenu !== id) { setOpenSubmenu(""); setOpenMenu(id); } }}
          >
            {label}
          </button>
          {openMenu === id && (
            <div className="tws-slides-google-menu-panel" data-menu-panel={id} role="menu">
              {renderItems(menus[id] || [], id)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
