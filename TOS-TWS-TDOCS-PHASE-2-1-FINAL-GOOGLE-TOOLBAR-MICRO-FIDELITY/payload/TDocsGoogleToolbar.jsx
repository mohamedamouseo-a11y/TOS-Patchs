import {
  AlignCenter, AlignLeft, AlignRight, AtSign, Bold, Image as ImageIcon, Italic, Link2,
  List, ListOrdered, Printer, RotateCcw, Strikethrough, Table2, Underline,
} from "lucide-react";

const FONT_FAMILIES = ["Arial", "Times New Roman", "Georgia", "Verdana"];
const ZOOM_LEVELS = [75, 90, 100, 125, 140];

function IconButton({ icon: Icon, label, onClick, flipped = false }) {
  return (
    <button
      type="button"
      className={`tws-docs-gtoolbar-icon${flipped ? " is-flipped" : ""}`}
      title={label}
      aria-label={label}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
    >
      <Icon size={16} strokeWidth={1.9} />
    </button>
  );
}

function Divider() {
  return <span className="tws-docs-gtoolbar-divider" aria-hidden="true" />;
}

export function TDocsGoogleToolbar({ lang = "en", zoom = 100, dir = "rtl", textSizes = [], actions }) {
  const ar = lang !== "en";
  const label = (en, arText) => ar ? arText : en;

  return (
    <div className="tws-docs-gtoolbar-shell" role="toolbar" aria-label={label("Document toolbar", "شريط أدوات المستند")}>
      <div className="tws-docs-gtoolbar-track">
        <IconButton icon={RotateCcw} label={label("Undo", "تراجع")} onClick={actions.undo} />
        <IconButton icon={RotateCcw} label={label("Redo", "إعادة")} onClick={actions.redo} flipped />
        <IconButton icon={Printer} label={label("Print", "طباعة")} onClick={actions.print} />
        <Divider />

        <select className="tws-docs-gtoolbar-select is-zoom" value={zoom} onChange={(event) => actions.setZoom(Number(event.target.value))} aria-label={label("Zoom", "التكبير")}>
          {ZOOM_LEVELS.map((value) => <option key={value} value={value}>{value}%</option>)}
        </select>
        <Divider />

        <select
          className="tws-docs-gtoolbar-select is-style"
          defaultValue=""
          onChange={(event) => { if (event.target.value) actions.paragraphStyle(event.target.value); event.target.value = ""; }}
          aria-label={label("Paragraph style", "نمط الفقرة")}
        >
          <option value="">{label("Normal text", "نص عادي")}</option>
          <option value="H1">{label("Title", "عنوان")}</option>
          <option value="H2">{label("Heading 2", "عنوان 2")}</option>
          <option value="H3">{label("Heading 3", "عنوان 3")}</option>
          <option value="BLOCKQUOTE">{label("Quote", "اقتباس")}</option>
        </select>

        <select className="tws-docs-gtoolbar-select is-font" defaultValue="Arial" onChange={(event) => actions.fontFamily(event.target.value)} aria-label={label("Font", "الخط")}>
          {FONT_FAMILIES.map((font) => <option key={font} value={font}>{font}</option>)}
        </select>

        <select className="tws-docs-gtoolbar-select is-size" defaultValue="14" onChange={(event) => actions.textSize(Number(event.target.value))} aria-label={label("Font size", "حجم الخط")}>
          {textSizes.map((size) => <option key={size} value={size}>{size}</option>)}
        </select>
        <Divider />

        <IconButton icon={Bold} label={label("Bold", "عريض")} onClick={actions.bold} />
        <IconButton icon={Italic} label={label("Italic", "مائل")} onClick={actions.italic} />
        <IconButton icon={Underline} label={label("Underline", "تحته خط")} onClick={actions.underline} />
        <IconButton icon={Strikethrough} label={label("Strikethrough", "يتوسطه خط")} onClick={actions.strike} />
        <Divider />

        <IconButton icon={Link2} label={label("Insert link", "إدراج رابط")} onClick={actions.link} />
        <IconButton icon={AtSign} label={label("Mention", "إشارة")} onClick={actions.mention} />
        <Divider />

        <IconButton icon={AlignLeft} label={label("Align left", "محاذاة لليسار")} onClick={actions.alignLeft} />
        <IconButton icon={AlignCenter} label={label("Align center", "توسيط")} onClick={actions.alignCenter} />
        <IconButton icon={AlignRight} label={label("Align right", "محاذاة لليمين")} onClick={actions.alignRight} />
        <IconButton icon={List} label={label("Bulleted list", "قائمة نقطية")} onClick={actions.bulletList} />
        <IconButton icon={ListOrdered} label={label("Numbered list", "قائمة مرقمة")} onClick={actions.numberedList} />
        <Divider />

        <IconButton icon={ImageIcon} label={label("Insert image", "إدراج صورة")} onClick={actions.image} />
        <IconButton icon={Table2} label={label("Insert table", "إدراج جدول")} onClick={actions.table} />
        <Divider />

        <button type="button" className="tws-docs-gtoolbar-direction" onMouseDown={(event) => event.preventDefault()} onClick={actions.toggleDirection} title={label("Text direction", "اتجاه النص")}>
          {dir === "rtl" ? "RTL" : "LTR"}
        </button>
      </div>
    </div>
  );
}
