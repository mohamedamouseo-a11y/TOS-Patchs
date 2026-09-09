import { useEffect, useRef, useState } from "react";

const TOP_MENUS_EN = [
  ["file", "File"], ["edit", "Edit"], ["view", "View"], ["insert", "Insert"],
  ["format", "Format"], ["data", "Data"], ["tools", "Tools"], ["extensions", "Extensions"], ["help", "Help"],
];
const TOP_MENUS_AR = [
  ["file", "ملف"], ["edit", "تحرير"], ["view", "عرض"], ["insert", "إدراج"],
  ["format", "تنسيق"], ["data", "بيانات"], ["tools", "أدوات"], ["extensions", "إضافات"], ["help", "مساعدة"],
];
const ALT_MENU_KEYS = { f: "file", e: "edit", v: "view", i: "insert", o: "format", d: "data", t: "tools", h: "help" };

function separator() { return { separator: true }; }

export function TSheetsGoogleMenuBar({
  lang = "en",
  canEdit,
  canShare,
  selectedCount = 0,
  hasFilter = false,
  sheetCount = 1,
  actions,
}) {
  const [openMenu, setOpenMenu] = useState("");
  const [openSubmenu, setOpenSubmenu] = useState("");
  const rootRef = useRef(null);
  const isAr = lang !== "en";
  const topMenus = isAr ? TOP_MENUS_AR : TOP_MENUS_EN;
  const hasSelection = selectedCount > 0;
  const t = (en, ar) => isAr ? ar : en;

  const menus = {
    file: [
      { label: t("Rename", "إعادة تسمية"), enabled: canEdit, action: actions.rename },
      { label: t("Version history", "سجل الإصدارات"), action: actions.versionHistory },
      separator(),
      {
        label: t("Import", "استيراد"), enabled: canEdit, items: [
          { label: t("Import CSV", "استيراد CSV"), action: actions.importCsv },
          { label: t("Import Excel (.xlsx)", "استيراد Excel (.xlsx)"), action: actions.importXlsx },
        ],
      },
      {
        label: t("Download", "تنزيل"), items: [
          { label: "Microsoft Excel (.xlsx)", action: actions.downloadXlsx },
          { label: t("Comma-separated values (.csv)", "قيم مفصولة بفواصل (.csv)"), action: actions.downloadCsv },
          { label: "PDF document (.pdf)", action: actions.downloadPdf },
        ],
      },
      separator(),
      { label: t("Print", "طباعة"), shortcut: "Ctrl+P", action: actions.print },
      { label: t("Share", "مشاركة"), enabled: canShare, action: actions.share },
    ],
    edit: [
      { label: t("Undo", "تراجع"), shortcut: "Ctrl+Z", enabled: canEdit, action: actions.undo },
      { label: t("Redo", "إعادة"), shortcut: "Ctrl+Y", enabled: canEdit, action: actions.redo },
      separator(),
      { label: t("Cut", "قص"), shortcut: "Ctrl+X", enabled: canEdit && hasSelection, action: actions.cut },
      { label: t("Copy", "نسخ"), shortcut: "Ctrl+C", enabled: hasSelection, action: actions.copy },
      { label: t("Paste", "لصق"), shortcut: "Ctrl+V", enabled: canEdit && hasSelection, action: actions.paste },
      {
        label: t("Paste special", "لصق خاص"), enabled: canEdit && hasSelection, items: [
          { label: t("Values only", "القيم فقط"), action: actions.pasteValues },
          { label: t("Format only", "التنسيق فقط"), action: actions.pasteFormats },
        ],
      },
      separator(),
      { label: t("Clear values", "مسح القيم"), shortcut: "Delete", enabled: canEdit && hasSelection, action: actions.clearValues },
      { label: t("Clear formatting", "مسح التنسيق"), enabled: canEdit && hasSelection, action: actions.clearFormatting },
      separator(),
      { label: t("Find and replace", "بحث واستبدال"), shortcut: "Ctrl+H", enabled: canEdit, action: actions.findReplace },
      { label: t("Select all", "تحديد الكل"), shortcut: "Ctrl+A", action: actions.selectAll },
    ],
    view: [
      { label: t("Full screen", "ملء الشاشة"), action: actions.fullscreen },
      { label: t("Show side panel", "إظهار اللوحة الجانبية"), action: actions.toggleInspector },
      separator(),
      {
        label: t("Freeze", "تجميد"), enabled: canEdit && hasSelection, items: [
          { label: t("Up to current row", "حتى الصف الحالي"), action: actions.freezeRows },
          { label: t("Up to current column", "حتى العمود الحالي"), action: actions.freezeCols },
          { label: t("No rows or columns", "إلغاء التجميد"), action: actions.clearFreeze },
        ],
      },
    ],
    insert: [
      { label: t("Sheet", "ورقة"), enabled: canEdit && sheetCount < 20, action: actions.addSheet },
      separator(),
      { label: t("Row", "صف"), enabled: canEdit, action: actions.addRow },
      { label: t("Column", "عمود"), enabled: canEdit, action: actions.addCol },
      separator(),
      { label: t("Chart", "رسم بياني"), enabled: canEdit && hasSelection, action: actions.addChart },
      { label: t("Pivot table", "جدول محوري"), enabled: canEdit && hasSelection, action: actions.addPivot },
      { label: t("Dropdown", "قائمة منسدلة"), enabled: canEdit && hasSelection, action: actions.addDropdown },
      { label: t("Named range", "نطاق مسمى"), enabled: canEdit && hasSelection, action: actions.addNamedRange },
    ],
    format: [
      {
        label: t("Text", "نص"), enabled: canEdit && hasSelection, items: [
          { label: t("Bold", "عريض"), shortcut: "Ctrl+B", action: actions.bold },
          { label: t("Italic", "مائل"), shortcut: "Ctrl+I", action: actions.italic },
          { label: t("Underline", "تحته خط"), shortcut: "Ctrl+U", action: actions.underline },
          { label: t("Strikethrough", "يتوسطه خط"), action: actions.strike },
        ],
      },
      {
        label: t("Font size", "حجم الخط"), enabled: canEdit && hasSelection, items: [10, 12, 14, 18, 24, 32].map((size) => ({ label: `${size}`, action: () => actions.fontSize(size) })),
      },
      {
        label: t("Number", "رقم"), enabled: canEdit && hasSelection, items: [
          { label: t("Automatic", "تلقائي"), action: () => actions.numberFormat("general") },
          { label: t("Number", "رقم"), action: () => actions.numberFormat("number") },
          { label: t("Currency", "عملة"), action: () => actions.numberFormat("currency") },
          { label: t("Percent", "نسبة مئوية"), action: () => actions.numberFormat("percent") },
          { label: t("Date", "تاريخ"), action: () => actions.numberFormat("date") },
          { label: t("Date time", "تاريخ ووقت"), action: () => actions.numberFormat("datetime") },
        ],
      },
      separator(),
      {
        label: t("Alignment", "محاذاة"), enabled: canEdit && hasSelection, items: [
          { label: t("Left", "يسار"), action: actions.alignLeft },
          { label: t("Center", "وسط"), action: actions.alignCenter },
          { label: t("Right", "يمين"), action: actions.alignRight },
          separator(),
          { label: t("Top", "أعلى"), action: actions.alignTop },
          { label: t("Middle", "وسط رأسي"), action: actions.alignMiddle },
          { label: t("Bottom", "أسفل"), action: actions.alignBottom },
        ],
      },
      { label: t("Wrapping", "التفاف النص"), enabled: canEdit && hasSelection, action: actions.wrap },
      {
        label: t("Merge cells", "دمج الخلايا"), enabled: canEdit && hasSelection, items: [
          { label: t("Merge", "دمج"), action: actions.merge },
          { label: t("Unmerge", "إلغاء الدمج"), action: actions.unmerge },
        ],
      },
      separator(),
      { label: t("Clear formatting", "مسح التنسيق"), enabled: canEdit && hasSelection, action: actions.clearFormatting },
    ],
    data: [
      { label: t("Sort range A → Z", "فرز النطاق أ → ي"), enabled: canEdit && hasSelection, action: actions.sortAsc },
      { label: t("Sort range Z → A", "فرز النطاق ي → أ"), enabled: canEdit && hasSelection, action: actions.sortDesc },
      separator(),
      { label: t("Create a filter", "إنشاء فلتر"), enabled: canEdit && hasSelection, action: actions.createFilter },
      { label: t("Filter by values", "فلترة حسب القيم"), enabled: canEdit && hasFilter && hasSelection, action: actions.filterValues },
      { label: t("Remove filter", "إزالة الفلتر"), enabled: canEdit && hasFilter, action: actions.clearFilter },
      separator(),
      { label: t("Data validation", "التحقق من البيانات"), enabled: canEdit && hasSelection, action: actions.addDropdown },
      { label: t("Conditional formatting", "تنسيق شرطي"), enabled: canEdit && hasSelection, action: actions.conditionalFormatting },
      { label: t("Named ranges", "النطاقات المسماة"), enabled: canEdit && hasSelection, action: actions.addNamedRange },
      separator(),
      { label: t("Protect range", "حماية النطاق"), enabled: canEdit && hasSelection, action: actions.protect },
      { label: t("Unprotect range", "إلغاء حماية النطاق"), enabled: canEdit && hasSelection, action: actions.unprotect },
    ],
    tools: [
      { label: t("Find and replace", "بحث واستبدال"), shortcut: "Ctrl+H", enabled: canEdit, action: actions.findReplace },
      { label: t("Comments", "التعليقات"), action: actions.comments },
      { label: t("Version history", "سجل الإصدارات"), action: actions.versionHistory },
      separator(),
      { label: t("Keyboard shortcuts", "اختصارات لوحة المفاتيح"), shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
    ],
    extensions: [
      { label: t("No extensions installed", "لا توجد إضافات مثبتة"), disabled: true },
    ],
    help: [
      { label: t("Keyboard shortcuts", "اختصارات لوحة المفاتيح"), shortcut: "Ctrl+/", action: actions.keyboardShortcuts },
      { label: t("T-Sheets help", "مساعدة T-Sheets"), action: actions.help },
    ],
  };

  function closeMenus() { setOpenMenu(""); setOpenSubmenu(""); }
  function chooseMenu(menuId) {
    setOpenSubmenu("");
    setOpenMenu((current) => current === menuId ? "" : menuId);
  }
  function cycleMenu(delta) {
    const currentIndex = Math.max(0, topMenus.findIndex(([id]) => id === openMenu));
    const nextIndex = (currentIndex + delta + topMenus.length) % topMenus.length;
    setOpenSubmenu("");
    setOpenMenu(topMenus[nextIndex][0]);
  }
  function runItem(item) {
    if (item.disabled || item.enabled === false || item.items?.length) return;
    item.action?.();
    closeMenus();
  }
  function handleRootKeyDown(event) {
    if (!openMenu) return;
    if (event.key === "Escape") { event.preventDefault(); closeMenus(); return; }
    if (event.key === "ArrowRight") { event.preventDefault(); cycleMenu(1); return; }
    if (event.key === "ArrowLeft") { event.preventDefault(); cycleMenu(-1); return; }
    if (event.key === "ArrowDown") {
      event.preventDefault();
      rootRef.current?.querySelector(`[data-menu-panel="${openMenu}"] button:not(:disabled)`)?.focus();
    }
  }

  useEffect(() => {
    function handlePointerDown(event) { if (!rootRef.current?.contains(event.target)) closeMenus(); }
    function handleKeyDown(event) {
      if (event.key === "Escape" && openMenu) { event.preventDefault(); closeMenus(); return; }
      if (event.altKey && !event.ctrlKey && !event.metaKey) {
        const menuId = ALT_MENU_KEYS[event.key.toLowerCase()];
        if (menuId) { event.preventDefault(); setOpenSubmenu(""); setOpenMenu(menuId); }
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
      if (item.separator) return <div key={key} className="tws-sheets-gmenu-separator" role="separator" />;
      const disabled = item.disabled || item.enabled === false;
      const hasSubmenu = Boolean(item.items?.length);
      return (
        <div key={key} className="tws-sheets-gmenu-item-wrap" onPointerEnter={() => setOpenSubmenu(hasSubmenu ? key : "")}>
          <button
            type="button"
            role="menuitem"
            disabled={disabled}
            className={`tws-sheets-gmenu-item${item.danger ? " is-danger" : ""}`}
            onClick={() => hasSubmenu ? setOpenSubmenu((current) => current === key ? "" : key) : runItem(item)}
            onKeyDown={(event) => {
              if (event.key === "ArrowRight" && hasSubmenu) { event.preventDefault(); setOpenSubmenu(key); }
              if (event.key === "Escape") closeMenus();
            }}
          >
            <span className="tws-sheets-gmenu-check">{item.checked ? "✓" : ""}</span>
            <span className="tws-sheets-gmenu-label">{item.label}</span>
            <span className="tws-sheets-gmenu-shortcut">{item.shortcut || ""}</span>
            <span className="tws-sheets-gmenu-arrow">{hasSubmenu ? (isAr ? "‹" : "›") : ""}</span>
          </button>
          {hasSubmenu && openSubmenu === key && (
            <div className="tws-sheets-gmenu-panel is-submenu" role="menu">
              {renderItems(item.items, key)}
            </div>
          )}
        </div>
      );
    });
  }

  return (
    <div ref={rootRef} className="tws-sheets-google-menu-bar" dir={isAr ? "rtl" : "ltr"} role="menubar" aria-label={t("Google Sheets style menus", "قوائم على نمط Google Sheets")} onKeyDown={handleRootKeyDown}>
      {topMenus.map(([id, label]) => (
        <div key={id} className="tws-sheets-google-top-menu">
          <button
            type="button"
            role="menuitem"
            aria-haspopup="menu"
            aria-expanded={openMenu === id}
            className={`tws-sheets-gmenu-trigger${openMenu === id ? " is-open" : ""}`}
            onClick={() => chooseMenu(id)}
            onPointerEnter={() => { if (openMenu && openMenu !== id) { setOpenSubmenu(""); setOpenMenu(id); } }}
          >{label}</button>
          {openMenu === id && (
            <div className="tws-sheets-gmenu-panel" data-menu-panel={id} role="menu">
              {renderItems(menus[id] || [], id)}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
