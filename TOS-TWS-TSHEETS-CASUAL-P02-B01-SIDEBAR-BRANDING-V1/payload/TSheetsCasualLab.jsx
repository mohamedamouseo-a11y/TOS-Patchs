import { useCallback } from "react";

// TOS_TWS_TSHEETS_CASUAL_P02_B01_SIDEBAR_BRANDING_V1
const TSHEETS_BRAND_STYLE = `
  .titlebar__brand {
    min-width: 96px !important;
    gap: 7px !important;
    justify-content: flex-start !important;
    cursor: default !important;
  }
  .titlebar__brand-icon {
    display: none !important;
  }
  .titlebar__brand::before {
    content: "";
    display: block;
    width: 28px;
    height: 32px;
    flex: 0 0 28px;
    border-radius: 7px;
    border: 1px solid rgba(5, 150, 105, 0.28);
    background-color: #10b981;
    background-image:
      repeating-linear-gradient(to right, transparent 0 8px, rgba(255,255,255,.72) 8px 9px),
      repeating-linear-gradient(to bottom, transparent 0 8px, rgba(255,255,255,.72) 8px 9px);
    box-shadow: 0 4px 12px rgba(5, 150, 105, .18);
  }
  .tos-tsheets-wordmark {
    display: inline-flex;
    align-items: center;
    white-space: nowrap;
    color: var(--color-text);
    font-size: 12px;
    font-weight: 800;
    letter-spacing: -0.01em;
  }
  @media (max-width: 920px) {
    .titlebar__brand {
      min-width: 30px !important;
    }
    .tos-tsheets-wordmark {
      display: none !important;
    }
  }
`;

function replaceCasualSheetsBrand(value) {
  return String(value || "").replace(/Casual Sheets/g, "T-Sheets");
}

function applyTsheetsBranding(frame) {
  const doc = frame?.contentDocument;
  const frameWindow = frame?.contentWindow;
  if (!doc || !frameWindow) return;

  doc.documentElement.dataset.tosTsheetsBranding = "p02-b01-v1";

  let style = doc.getElementById("tos-tsheets-branding-style");
  if (!style) {
    style = doc.createElement("style");
    style.id = "tos-tsheets-branding-style";
    style.textContent = TSHEETS_BRAND_STYLE;
    doc.head.appendChild(style);
  }

  function syncBrand() {
    if (doc.title.includes("Casual Sheets")) {
      doc.title = replaceCasualSheetsBrand(doc.title);
    }

    const brand = doc.querySelector(".titlebar__brand");
    if (brand) {
      brand.setAttribute("aria-label", "T-Sheets");
      brand.setAttribute("title", "T-Sheets");
      brand.setAttribute("href", "#");

      const icon = brand.querySelector(".titlebar__brand-icon");
      if (icon) {
        icon.setAttribute("alt", "T-Sheets");
      }

      if (!brand.querySelector(".tos-tsheets-wordmark")) {
        const wordmark = doc.createElement("span");
        wordmark.className = "tos-tsheets-wordmark";
        wordmark.textContent = "T-Sheets";
        brand.appendChild(wordmark);
      }
    }

    doc.querySelectorAll("[title],[aria-label],[alt]").forEach((element) => {
      ["title", "aria-label", "alt"].forEach((name) => {
        const current = element.getAttribute(name);
        if (current?.includes("Casual Sheets")) {
          element.setAttribute(name, replaceCasualSheetsBrand(current));
        }
      });
    });

    if (doc.body) {
      const walker = doc.createTreeWalker(doc.body, frameWindow.NodeFilter.SHOW_TEXT);
      const textNodes = [];
      while (walker.nextNode()) textNodes.push(walker.currentNode);
      textNodes.forEach((node) => {
        if (node.nodeValue?.includes("Casual Sheets")) {
          node.nodeValue = replaceCasualSheetsBrand(node.nodeValue);
        }
      });
    }
  }

  syncBrand();

  frameWindow.__tosTsheetsBrandObserver?.disconnect?.();
  const observer = new frameWindow.MutationObserver(() => syncBrand());
  observer.observe(doc.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
    attributes: true,
    attributeFilter: ["title", "aria-label", "alt"],
  });
  frameWindow.__tosTsheetsBrandObserver = observer;

  if (!frameWindow.__tosTsheetsBrandClickGuard) {
    doc.addEventListener(
      "click",
      (event) => {
        const target = event.target;
        const brand = target?.closest?.(".titlebar__brand");
        if (!brand) return;
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
      },
      true,
    );
    frameWindow.__tosTsheetsBrandClickGuard = true;
  }
}

export function TSheetsCasualLab() {
  const handleLoad = useCallback((event) => {
    applyTsheetsBranding(event.currentTarget);
  }, []);

  return (
    <section
      data-tsheets-casual-lab="p02-b01-v1"
      className="h-[calc(100dvh-64px)] min-h-[640px] w-full overflow-hidden bg-white"
    >
      <iframe
        title="T-Sheets Lab"
        src="/tws-casual-runtime/"
        className="h-full w-full border-0 bg-white"
        allow="clipboard-read; clipboard-write"
        onLoad={handleLoad}
      />
    </section>
  );
}
