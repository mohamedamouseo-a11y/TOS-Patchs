import { useEffect, useRef, useState } from "react";

const TOP_MENUS = [
  ["file", "File"],
  ["edit", "Edit"],
  ["view", "View"],
  ["insert", "Insert"],
  ["format", "Format"],
  ["tools", "Tools"],
  ["extensions", "Extensions"],
  ["help", "Help"],
];

const ALT_MENU_KEYS = { f: "file", e: "edit", v: "view", i: "insert", o: "format", t: "tools", h: "help" };
const separator = () => ({ separator: true });

export function TDocsGoogleMenuBar({
  canEdit,
  canShare,
  selectionContext = {},
  pageSetup = {},
  zoom = 100,
  dir = "rtl",
  showOutline = true,
  actions,
}) {
  const [openMenu, setOpenMenu] = useState("");
  const [openSubmenu, setOpenSubmenu] = useState("");
  const rootRef = useRef(null);

  const inTable = Boolean(selectionContext.inTable);
  const onImage = Boolean(selectionContext.onImage);

  const menus = {
    file: [
      { label: "Rename", enabled: canEdit, action: actions.rename },
      { label: "Version history", action: actions.versionHistory },
      { label: "Share", enabled: canShare, action: actions.share },
      separator(),
      {
        label: "Download",
        items: [
          { label: "Microsoft Word (.docx)", action: actions.downloadDocx },
          { label: "PDF document (.pdf)", action: actions.downloadPdf },
        ],
      },
      {
        label: "Page setup",
        items: [
          { label: "Responsive", checked: pageSetup.size === "responsive", action: actions.pageResponsive },
          { label: "A4", checked: pageSetup.size === "a4", action: actions.pageA4 },
          { label: "Letter", checked: pageSetup.size === "letter", action: actions.pageLetter },
          separator(),
          { label: "Compact margins", checked: pageSetup.margin === "compact", action: actions.marginCompact },
          { label: "Normal margins", checked: pageSetup.margin === "normal", action: actions.marginNormal },
          { label: "Wide margins", checked: pageSetup.margin === "wide", action: actions.marginWide },
        ],
      },
      separator(),
      { label: "Print", shortcut: "Ctrl+P", action: actions.print },
    ],
    edit: [
      { label: "Undo", shortcut: "Ctrl+Z", enabled: canEdit, action: actions.undo },
      { label: "Redo", shortcut: "Ctrl+Y", enabled: canEdit, action: actions.redo },
      separator(),
      { label: "Cut", shortcut: "Ctrl+X", enabled: canEdit, action: actions.cut },
      { label: "Copy", shortcut: "Ctrl+C", action: actions.copy },
      { label: "Paste", shortcut: "Ctrl+V", enabled: canEdit, action: actions.paste },
      { label: "Select all", shortcut: "Ctrl+A", action: actions.selectAll },
      separator(),
      { label: "Find and replace", shortcut: "Ctrl+H", action: actions.findReplace },
    ],
    view: [
      { label: showOutline ? "Hide document outline" : "Show document outline", action: actions.toggleOutline },
      {
        label: `Zoom (${zoom}%)`,
        items: [
          { label: "75%", checked: zoom === 75, action: actions.zoom75 },
          { label: "90%", checked: zoom === 90, action: actions.zoom90 },
          { label: "100%", checked: zoom === 100, action: actions.zoom100 },
          { label: "125%", checked: zoom === 125, action: actions.zoom125 },
          { label: "140%", checked: zoom === 140, action: actions.zoom140 },
        ],
      },
    ],
    insert: [
      { label: "Image", enabled: canEdit, action: actions.image },
      { label: "Table", enabled: canEdit, action: actions.table },
      { label: "Link", shortcut: "Ctrl+K", enabled: canEdit, action: actions.link },
      { label: "Mention", enabled: canEdit, action: actions.mention },
      separator(),
      { label: "Header", enabled: canEdit, action: actions.header },
      { label: "Footer", enabled: canEdit, action: actions.footer },
      { label: "Page break", shortcut: "Ctrl+Enter", enabled: canEdit, action: actions.pageBreak },
    ],
    format: [
      {
        label: "Text",
        enabled: canEdit,
        items: [
          { label: "Bold", shortcut: "Ctrl+B", action: actions.bold },
          { label: "Italic", shortcut: "Ctrl+I", action: actions.italic },
          { label: "Underline", shortcut: "Ctrl+U", action: actions.underline },
          { label: "Strikethrough", action: actions.strike },
          separator(),
          { label: "Clear formatting", shortcut: "Ctrl+\\", action: actions.clearFormatting },
        ],
      },
      {
        label: "Paragraph styles",
        enabled: canEdit,
        items: [
          { label: "Normal text", action: actions.paragraph },
          { label: "Title", action: actions.heading1 },
          { label: "Heading 2", action: actions.heading2 },
          { label: "Heading 3", action: actions.heading3 },
          { label: "Quote", action: actions.quote },
        ],
      },
      {
        label: "Align & indent",
        enabled: canEdit,
        items: [
          { label: "Left", action: actions.alignLeft },
          { label: "Center", action: actions.alignCenter },
          { label: "Right", action: actions.alignRight },
          separator(),
          { label: "Increase indent", action: actions.indent },
          { label: "Decrease indent", action: actions.outdent },
        ],
      },
      {
        label: "Line & paragraph spacing",
        enabled: canEdit,
        items: [
          { label: "Single", action: actions.lineSingle },
          { label: "1.15", action: actions.line115 },
          { label: "1.5", action: actions.line15 },
          { label: "Double", action: actions.lineDouble },
          separator(),
          { label: "Add space before paragraph", action: actions.spaceBefore },
          { label: "Add space after paragraph", action: actions.spaceAfter },
          { label: "Remove paragraph spacing", action: actions.clearParagraphSpacing },
        ],
      },
      {
        label: "Bullets & numbering",
        enabled: canEdit,
        items: [
          { label: "Bulleted list", shortcut: "Ctrl+Shift+8", action: actions.bulletList },
          { label: "Numbered list", shortcut: "Ctrl+Shift+7", action: actions.numberedList },
        ],
      },
      {
        label: "Text direction",
        enabled: canEdit,
        items: [
          { label: "Right-to-left", checked: dir === "rtl", action: actions.rtl },
          { label: "Left-to-right", checked: dir === "ltr", action: actions.ltr },
        ],
      },
      separator(),
      {
        label: "Image options",
        enabled: canEdit && onImage,
        items: [
          { label: "25% width", action: actions.image25 },
          { label: "50% width", action: actions.image50 },
          { label: "75% width", action: actions.image75 },
          { label: "100% width", action: actions.image100 },
          separator(),
          { label: "Align left", action: actions.imageLeft },
          { label: "Align center", action: actions.imageCenter },
          { label: "Align right", action: actions.imageRight },
        ],
      },
      {
        label: "Table",
        enabled: canEdit && inTable,
        items: [
          { label: "Insert row below", action: actions.tableRow },
          { label: "Insert column right", action: actions.tableColumn },
          { label: "Delete row", action: actions.deleteTableRow },
          { label: "Delete column", action: actions.deleteTableColumn },
        ],
      },
    ],
    tools: [
      { label: "Word count", shortcut: "Ctrl+Shift+C", action: actions.wordCount },
      { label: "Comments", action: actions.comments },
      { label: "Version history", action: actions.versionHistory },
      { label: "Save named version", shortcut: "Ctrl+S", enabled: canEdit, action: actions.saveVersion },
      separator(),
      { label: "Keyboard shortcuts", shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
    ],
    extensions: [
      { label: "No extensions installed", disabled: true },
    ],
    help: [
      { label: "Keyboard shortcuts", shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
      { label: "T-Docs help", action: actions.help },
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

  useEffect(() => {
    function onPointerDown(event) {
      if (!rootRef.current?.contains(event.target)) closeMenus();
    }
    function onKeyDown(event) {
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
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [openMenu]);

  function renderItems(items, parentKey) {
    return items.map((item, index) => {
      const key = `${parentKey}-${index}`;
      if (item.separator) return <div key={key} className="tws-docs-google-menu-separator" role="separator" />;
      const disabled = item.disabled || item.enabled === false;
      const hasSubmenu = Boolean(item.items?.length);
      return (
        <div key={key} className="tws-docs-google-menu-item-wrap" onPointerEnter={() => setOpenSubmenu(hasSubmenu && !disabled ? key : "")}>
          <button
            type="button"
            role="menuitem"
            disabled={disabled}
            className="tws-docs-google-menu-item"
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => hasSubmenu ? (!disabled && setOpenSubmenu((current) => current === key ? "" : key)) : runItem(item)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" && hasSubmenu && !disabled) {
                event.preventDefault();
                setOpenSubmenu(key);
              }
              if (event.key === "Escape") closeMenus();
            }}
          >
            <span className="tws-docs-google-menu-check">{item.checked ? "✓" : ""}</span>
            <span className="tws-docs-google-menu-label">{item.label}</span>
            <span className="tws-docs-google-menu-shortcut">{item.shortcut || ""}</span>
            <span className="tws-docs-google-menu-arrow">{hasSubmenu ? "›" : ""}</span>
          </button>
          {hasSubmenu && openSubmenu === key && !disabled && (
            <div className="tws-docs-google-menu-panel is-submenu" role="menu">
              {renderItems(item.items, key)}
            </div>
          )}
        </div>
      );
    });
  }

  return (
    <div
      ref={rootRef}
      className="tws-docs-google-menu-bar"
      role="menubar"
      aria-label="Google Docs style menus"
      onKeyDown={(event) => {
        if (!openMenu) return;
        if (event.key === "ArrowRight") { event.preventDefault(); cycleMenu(1); }
        else if (event.key === "ArrowLeft") { event.preventDefault(); cycleMenu(-1); }
        else if (event.key === "ArrowDown") {
          event.preventDefault();
          rootRef.current?.querySelector(`[data-menu-panel="${openMenu}"] button:not(:disabled)`)?.focus();
        }
      }}
    >
      {TOP_MENUS.map(([id, label]) => (
        <div key={id} className="tws-docs-google-top-menu">
          <button
            type="button"
            role="menuitem"
            aria-haspopup="menu"
            aria-expanded={openMenu === id}
            className={`tws-docs-google-menu-trigger${openMenu === id ? " is-open" : ""}`}
            onMouseDown={(event) => event.preventDefault()}
            onClick={() => chooseMenu(id)}
            onPointerEnter={() => {
              if (openMenu && openMenu !== id) {
                setOpenSubmenu("");
                setOpenMenu(id);
              }
            }}
          >
            {label}
          </button>
          {openMenu === id && (
            <div className="tws-docs-google-menu-panel" data-menu-panel={id} role="menu">
              {renderItems(menus[id] || [], id)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
