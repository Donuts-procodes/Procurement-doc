import type { DocumentSegment, DocumentStyleConfig } from "../types";

const imageBase64Cache = new Map<string, string>();

async function convertImageUrlToBase64(url: string): Promise<string> {
  if (!url || url.startsWith("data:")) return url;
  if (imageBase64Cache.has(url)) return imageBase64Cache.get(url)!;

  try {
    const res = await fetch(url, { mode: "cors" });
    if (!res.ok) return url;
    const blob = await res.blob();
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result as string;
        imageBase64Cache.set(url, result);
        resolve(result);
      };
      reader.onerror = () => resolve(url);
      reader.readAsDataURL(blob);
    });
  } catch {
    return url;
  }
}

export async function extractHtmlFromSegmentAsync(seg: DocumentSegment): Promise<string> {
  if (!seg.content || typeof seg.content !== "object" || !("content" in seg.content)) {
    return `<p>No text content available.</p>`;
  }

  const nodes = (seg.content as any).content || [];
  let html = "";

  for (const node of nodes) {
    if (node.type === "heading") {
      const level = node.attrs?.level || 2;
      const text = renderTextWithMarks(node.content);
      html += `<h${level}>${text}</h${level}>`;
    } else if (node.type === "paragraph") {
      const text = renderTextWithMarks(node.content);
      const isDivider = text.includes("───") || text.includes("\u2500\u2500\u2500") || /^[─\-—_]{6,}$/.test(text.trim());
      if (isDivider) {
        html += `<hr style="border:0; border-top:1px solid #cbd5e1; margin:14px 0;" />`;
      } else if (text.includes("[") && text.includes("]") && (text.includes("Doc Type:") || text.includes("Target Pages:") || text.includes("Fact Check:") || text.includes("SLA Target:") || text.includes("Provenance:"))) {
        const badgeHtml = text.replace(/\[([^:]+):\s*([^\]]+)\]/g, (_m, k, v) => {
          return `<span style="display:inline-block; background-color:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; border-radius:4px; padding:2px 8px; margin:2px 4px; font-size:11px; font-weight:bold;">${k.trim()}: <span style="font-weight:normal;">${v.trim()}</span></span>`;
        });
        html += `<p style="margin:4px 0 10px 0; line-height:1.8;">${badgeHtml}</p>`;
      } else {
        html += `<p style="margin:0 0 10px 0; line-height:1.5;">${text}</p>`;
      }
    } else if (node.type === "horizontalRule") {
      html += `<hr style="border:0; border-top:1px solid #cbd5e1; margin:14px 0;" />`;
    } else if (node.type === "citation") {
      const srcId = node.attrs?.source_id || "^";
      const srcUrl = node.attrs?.url || `#citation-${srcId}`;
      html += `<sup style="font-size:10px; color:#1a73e8; margin:0 2px;"><a href="${srcUrl}" style="color:#1a73e8; text-decoration:none;">[${srcId}]</a></sup>`;
    } else if (node.type === "blockquote") {
      const bqContent = (node.content || [])
        .map((p: any) => renderTextWithMarks(p.content))
        .join("<br>");
      html += `<div style="border-left:4px solid #1a73e8; background-color:#eff6ff; padding:10px 14px; margin:14px 0; border-radius:4px; font-size:13px; color:#1e3a8a;">${bqContent}</div>`;
    } else if (node.type === "image") {
      let src = node.attrs?.src || "";
      if (src.includes("quickchart.io/mermaid") && !src.includes("format=png")) {
        src += "&format=png";
      }
      const base64Src = await convertImageUrlToBase64(src);
      const alt = node.attrs?.alt || "Document Graphic";
      const width = node.attrs?.width || "100%";
      const alignment = node.attrs?.alignment || "center";
      let alignStyle = "text-align:center; margin:16px 0;";
      if (alignment === "left") alignStyle = "text-align:left; margin:16px 16px 16px 0;";
      else if (alignment === "right") alignStyle = "text-align:right; margin:16px 0 16px 16px;";

      html += `<div style="${alignStyle}"><img src="${base64Src}" alt="${alt}" style="width:${width}; max-width:100%; height:auto; border-radius:6px; display:inline-block;" /></div>`;
    } else if (node.type === "bulletList") {
      html += `<ul>`;
      for (const item of node.content || []) {
        const itemParagraphs = item.content || [];
        for (const p of itemParagraphs) {
          html += `<li>${renderTextWithMarks(p.content)}</li>`;
        }
      }
      html += `</ul>`;
    } else if (node.type === "orderedList") {
      html += `<ol>`;
      for (const item of node.content || []) {
        const itemParagraphs = item.content || [];
        for (const p of itemParagraphs) {
          html += `<li>${renderTextWithMarks(p.content)}</li>`;
        }
      }
      html += `</ol>`;
    } else if (node.type === "table") {
      html += `<table border="1" style="border-collapse:collapse; mso-table-layout-alt:fixed; width:100%; margin:16px 0;">`;
      for (const row of node.content || []) {
        html += `<tr>`;
        for (const cell of row.content || []) {
          const isHeader = cell.type === "tableHeader";
          const tag = isHeader ? "th" : "td";
          const colspan = cell.attrs?.colspan ? ` colspan="${cell.attrs.colspan}"` : "";
          const rowspan = cell.attrs?.rowspan ? ` rowspan="${cell.attrs.rowspan}"` : "";
          const cellContent = (cell.content || []).map((p: any) => renderTextWithMarks(p.content)).join("<br>");
          const safeContent = cellContent.trim() ? cellContent : "&nbsp;";
          const headerStyle = isHeader
            ? "background-color:#f1f3f4; font-weight:bold; color:#202124;"
            : "background-color:#ffffff; color:#202124;";
          html += `<${tag}${colspan}${rowspan} style="padding:8px 10px; border:1px solid #dadce0; text-align:left; vertical-align:top; ${headerStyle}">${safeContent}</${tag}>`;
        }
        html += `</tr>`;
      }
      html += `</table>`;
    }
  }

  return html;
}

export function extractHtmlFromSegment(seg: DocumentSegment): string {
  if (!seg.content || typeof seg.content !== "object" || !("content" in seg.content)) {
    return `<p>No text content available.</p>`;
  }

  const nodes = (seg.content as any).content || [];
  let html = "";

  for (const node of nodes) {
    if (node.type === "heading") {
      const level = node.attrs?.level || 2;
      const text = renderTextWithMarks(node.content);
      html += `<h${level}>${text}</h${level}>`;
    } else if (node.type === "paragraph") {
      const text = renderTextWithMarks(node.content);
      const isDivider = text.includes("───") || text.includes("\u2500\u2500\u2500") || /^[─\-—_]{6,}$/.test(text.trim());
      if (isDivider) {
        html += `<hr style="border:0; border-top:1px solid #cbd5e1; margin:14px 0;" />`;
      } else if (text.includes("[") && text.includes("]") && (text.includes("Doc Type:") || text.includes("Target Pages:") || text.includes("Fact Check:") || text.includes("SLA Target:") || text.includes("Provenance:"))) {
        const badgeHtml = text.replace(/\[([^:]+):\s*([^\]]+)\]/g, (_m, k, v) => {
          return `<span style="display:inline-block; background-color:#eff6ff; color:#1d4ed8; border:1px solid #bfdbfe; border-radius:4px; padding:2px 8px; margin:2px 4px; font-size:11px; font-weight:bold;">${k.trim()}: <span style="font-weight:normal;">${v.trim()}</span></span>`;
        });
        html += `<p style="margin:4px 0 10px 0; line-height:1.8;">${badgeHtml}</p>`;
      } else {
        html += `<p style="margin:0 0 10px 0; line-height:1.5;">${text}</p>`;
      }
    } else if (node.type === "horizontalRule") {
      html += `<hr style="border:0; border-top:1px solid #cbd5e1; margin:14px 0;" />`;
    } else if (node.type === "citation") {
      const srcId = node.attrs?.source_id || "^";
      const srcUrl = node.attrs?.url || `#citation-${srcId}`;
      html += `<sup style="font-size:10px; color:#1a73e8; margin:0 2px;"><a href="${srcUrl}" style="color:#1a73e8; text-decoration:none;">[${srcId}]</a></sup>`;
    } else if (node.type === "blockquote") {
      const bqContent = (node.content || [])
        .map((p: any) => renderTextWithMarks(p.content))
        .join("<br>");
      html += `<div style="border-left:4px solid #1a73e8; background-color:#eff6ff; padding:10px 14px; margin:14px 0; border-radius:4px; font-size:13px; color:#1e3a8a;">${bqContent}</div>`;
    } else if (node.type === "image") {
      let src = node.attrs?.src || "";
      if (src.includes("quickchart.io/mermaid") && !src.includes("format=png")) {
        src += "&format=png";
      }
      const alt = node.attrs?.alt || "Document Graphic";
      const width = node.attrs?.width || "100%";
      const alignment = node.attrs?.alignment || "center";
      let alignStyle = "text-align:center; margin:16px 0;";
      if (alignment === "left") alignStyle = "text-align:left; margin:16px 16px 16px 0;";
      else if (alignment === "right") alignStyle = "text-align:right; margin:16px 0 16px 16px;";

      html += `<div style="${alignStyle}"><img src="${src}" alt="${alt}" style="width:${width}; max-width:100%; height:auto; border-radius:6px; display:inline-block;" /></div>`;
    } else if (node.type === "bulletList") {
      html += `<ul>`;
      for (const item of node.content || []) {
        const itemParagraphs = item.content || [];
        for (const p of itemParagraphs) {
          html += `<li>${renderTextWithMarks(p.content)}</li>`;
        }
      }
      html += `</ul>`;
    } else if (node.type === "orderedList") {
      html += `<ol>`;
      for (const item of node.content || []) {
        const itemParagraphs = item.content || [];
        for (const p of itemParagraphs) {
          html += `<li>${renderTextWithMarks(p.content)}</li>`;
        }
      }
      html += `</ol>`;
    } else if (node.type === "table") {
      html += `<table border="1" style="border-collapse:collapse; mso-table-layout-alt:fixed; width:100%; margin:16px 0;">`;
      for (const row of node.content || []) {
        html += `<tr>`;
        for (const cell of row.content || []) {
          const isHeader = cell.type === "tableHeader";
          const tag = isHeader ? "th" : "td";
          const colspan = cell.attrs?.colspan ? ` colspan="${cell.attrs.colspan}"` : "";
          const rowspan = cell.attrs?.rowspan ? ` rowspan="${cell.attrs.rowspan}"` : "";
          const cellContent = (cell.content || []).map((p: any) => renderTextWithMarks(p.content)).join("<br>");
          const safeContent = cellContent.trim() ? cellContent : "&nbsp;";
          const headerStyle = isHeader
            ? "background-color:#f1f3f4; font-weight:bold; color:#202124;"
            : "background-color:#ffffff; color:#202124;";
          html += `<${tag}${colspan}${rowspan} style="padding:8px 10px; border:1px solid #dadce0; text-align:left; vertical-align:top; ${headerStyle}">${safeContent}</${tag}>`;
        }
        html += `</tr>`;
      }
      html += `</table>`;
    }
  }

  return html;
}

export function renderTextWithMarks(content: any[]): string {
  if (!content || !Array.isArray(content)) return "";
  return content
    .map((node) => {
      if (node.type === "citation") {
        const srcId = node.attrs?.source_id || "^";
        const srcUrl = node.attrs?.url || `#citation-${srcId}`;
        return `<sup style="font-size:10px; color:#1a73e8; margin:0 2px;"><a href="${srcUrl}" style="color:#1a73e8; text-decoration:none;">[${srcId}]</a></sup>`;
      }
      let text = node.text || "";
      if (!text) return "";
      text = text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
      if (!node.marks || !Array.isArray(node.marks)) return text;

      let styles: string[] = [];
      let tagStart = "";
      let tagEnd = "";

      for (const mark of node.marks) {
        if (mark.type === "bold") {
          tagStart = `<strong>` + tagStart;
          tagEnd += `</strong>`;
        }
        if (mark.type === "italic") {
          tagStart = `<em>` + tagStart;
          tagEnd += `</em>`;
        }
        if (mark.type === "underline") {
          tagStart = `<u>` + tagStart;
          tagEnd += `</u>`;
        }
        if (mark.type === "strike" || mark.type === "strikeThrough") {
          tagStart = `<s>` + tagStart;
          tagEnd += `</s>`;
        }
        if (mark.type === "subscript") {
          tagStart = `<sub>` + tagStart;
          tagEnd += `</sub>`;
        }
        if (mark.type === "superscript") {
          tagStart = `<sup>` + tagStart;
          tagEnd += `</sup>`;
        }
        if (mark.type === "textStyle") {
          if (mark.attrs?.color) {
            styles.push(`color: ${mark.attrs.color}`);
          }
          if (mark.attrs?.style) {
            styles.push(mark.attrs.style);
          }
        }
        if (mark.type === "highlight" && mark.attrs?.color) {
          styles.push(`background-color: ${mark.attrs.color}`);
        }
      }

      if (styles.length > 0) {
        return `<span style="${styles.join("; ")}">${tagStart}${text}${tagEnd}</span>`;
      }
      return `${tagStart}${text}${tagEnd}`;
    })
    .join("");
}

export function extractPlainTextFromSegment(seg: DocumentSegment): string {
  if (!seg.content || typeof seg.content !== "object" || !("content" in seg.content)) {
    return "";
  }

  const nodes = (seg.content as any).content || [];
  let text = `=== ${seg.name} ===\n\n`;

  for (const node of nodes) {
    if (node.type === "heading") {
      const headingText = (node.content || []).map((c: any) => c.text || "").join("");
      text += `# ${headingText}\n`;
    } else if (node.type === "paragraph") {
      const pText = (node.content || []).map((c: any) => c.text || "").join("");
      text += `${pText}\n\n`;
    } else if (node.type === "bulletList") {
      for (const item of node.content || []) {
        for (const p of item.content || []) {
          const itemText = (p.content || []).map((c: any) => c.text || "").join("");
          text += `  • ${itemText}\n`;
        }
      }
      text += `\n`;
    } else if (node.type === "table") {
      for (const row of node.content || []) {
        const rowCells = (row.content || []).map((cell: any) => {
          return (cell.content || [])
            .map((p: any) => (p.content || []).map((c: any) => c.text || "").join(""))
            .join(" ");
        });
        text += `| ${rowCells.join(" | ")} |\n`;
      }
      text += `\n`;
    }
  }

  return text;
}

export async function exportToPdf(
  segments: DocumentSegment[],
  title: string = "Document",
  layoutSize: string = "A4",
  styleConfig: DocumentStyleConfig
) {
  const printWindow = window.open("", "_blank");
  if (!printWindow) {
    alert("Please allow popups to enable printing / PDF export.");
    return;
  }

  // Filter out any blank or empty pages before PDF export
  const validSegments = segments.filter((seg) => {
    const html = extractHtmlFromSegment(seg);
    return html && html !== "<p>No text content available.</p>" && html.replace(/<[^>]+>/g, "").trim().length > 0;
  });

  const segmentHtmlPromises = validSegments.map((seg) => extractHtmlFromSegmentAsync(seg));
  const segmentHtmls = await Promise.all(segmentHtmlPromises);

  const bodyHtml = segmentHtmls
    .map((html, idx) => `<div class="pdf-segment" data-segment-index="${idx}">${html}</div>`)
    .join("\n");

  const watermarkHtml = styleConfig.watermark
    ? `<div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-45deg); font-size:90px; color:rgba(0,0,0,0.05); font-weight:800; pointer-events:none; z-index:9999; text-transform:uppercase; white-space:nowrap;">${styleConfig.watermark}</div>`
    : "";

  const fullHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${title}</title>
        <style>
          @page { size: ${layoutSize}; margin: 15mm; }
          * { box-sizing: border-box; }
          html, body {
            margin: 0;
            padding: 0;
          }
          body {
            font-family: ${styleConfig.fontFamily || "Inter, sans-serif"};
            font-size: ${styleConfig.fontSize || "14px"};
            line-height: ${styleConfig.paragraphSpacing || "1.4"};
            color: #202124;
            background-color: ${styleConfig.pageColor || "#ffffff"};
            padding: 0;
          }
          h1, h2, h3, h4 {
            color: ${styleConfig.accentColor || "#1a73e8"};
            margin-top: 14px;
            margin-bottom: 6px;
            page-break-after: avoid;
            break-after: avoid;
            break-after: avoid-page;
            page-break-inside: avoid;
            break-inside: avoid;
            line-height: 1.25;
          }
          h1 { font-size: 22px; }
          h2 { font-size: 18px; }
          h3 { font-size: 15px; }
          p { margin-top: 0; margin-bottom: 10px; }
          .pdf-segment {
            page-break-inside: avoid;
            break-inside: avoid;
            page-break-after: always;
            break-after: page;
            margin-bottom: 0;
            padding: 0;
            box-sizing: border-box;
          }
          .pdf-segment:last-child {
            page-break-after: avoid !important;
            break-after: avoid !important;
          }
          table { width: 100%; border-collapse: collapse; margin: 12px 0; page-break-inside: avoid; break-inside: avoid; }
          thead { display: table-header-group; }
          tr { page-break-inside: avoid; break-inside: avoid; page-break-after: auto; }
          th { background-color: #f1f3f4; font-weight: bold; border: 1px solid #dadce0; padding: 8px 10px; text-align: left; }
          td { border: 1px solid #dadce0; padding: 8px 10px; text-align: left; vertical-align: top; }
          img { max-width: 100%; max-height: 480px; height: auto; display: block; margin: 0 auto; page-break-inside: avoid; break-inside: avoid; object-fit: contain; }
          .callout-box { border-left: 4px solid #1a73e8; background: #f8fafc; padding: 10px 12px; margin: 10px 0; page-break-inside: avoid; break-inside: avoid; }
          @media print {
            html, body {
              padding: 0 !important;
              margin: 0 !important;
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
            }
            .pdf-segment {
              page-break-after: always;
              break-after: page;
              margin-bottom: 0 !important;
            }
            .pdf-segment:last-child {
              page-break-after: avoid !important;
              break-after: avoid !important;
            }
          }
        </style>
      </head>
      <body>
        ${watermarkHtml}
        ${bodyHtml}
      </body>
    </html>
  `;

  printWindow.document.open();
  printWindow.document.write(fullHtml);
  printWindow.document.close();

  let printed = false;
  const triggerPrint = () => {
    if (printed) return;
    printed = true;
    const images = Array.from(printWindow.document.images);
    const promises = images.map((img) => {
      if (img.complete) return Promise.resolve();
      return new Promise((resolve) => {
        img.onload = () => resolve(true);
        img.onerror = () => resolve(false);
      });
    });
    Promise.all(promises).then(() => {
      setTimeout(() => {
        printWindow.focus();
        printWindow.print();
      }, 250);
    });
  };

  printWindow.onload = triggerPrint;
  setTimeout(triggerPrint, 1500);
}

export async function exportToWord(
  segments: DocumentSegment[],
  title: string = "Document",
  styleConfig: DocumentStyleConfig
) {
  const validSegments = segments.filter((seg) => {
    const html = extractHtmlFromSegment(seg);
    return html && html !== "<p>No text content available.</p>" && html.replace(/<[^>]+>/g, "").trim().length > 0;
  });

  const segmentHtmlPromises = validSegments.map((seg) => extractHtmlFromSegmentAsync(seg));
  const segmentHtmls = await Promise.all(segmentHtmlPromises);

  // Use only a single page break between segments, omitting page break for the very first segment (Page 1)
  const bodyHtml = segmentHtmls
    .map(
      (html, idx) =>
        `<div class="word-segment" style="${idx > 0 ? "page-break-before:always;" : ""} clear:both;">${html}</div>`
    )
    .join("\n");

  const wordContent = `
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head>
        <meta charset='utf-8'>
        <title>${title}</title>
        <style>
          body {
            font-family: ${styleConfig.fontFamily || "Calibri, sans-serif"};
            font-size: ${styleConfig.fontSize || "14px"};
            line-height: ${styleConfig.paragraphSpacing || "1.4"};
            color: #202124;
          }
          h1, h2, h3 { color: ${styleConfig.accentColor || "#1a73e8"}; page-break-after: avoid; }
          table { border-collapse: collapse; width: 100%; margin: 16px 0; mso-table-layout-alt: fixed; }
          th { background-color: #f1f3f4; font-weight: bold; border: 1px solid #dadce0; padding: 8px 10px; text-align: left; }
          td { border: 1px solid #dadce0; padding: 8px 10px; vertical-align: top; }
          img { max-width: 100%; height: auto; }
          .word-segment { page-break-inside: avoid; }
        </style>
      </head>
      <body>
        ${bodyHtml}
      </body>
    </html>
  `;

  const blob = new Blob([wordContent], { type: "application/msword;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${title.replace(/\s+/g, "_")}.doc`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

export function exportToTxt(segments: DocumentSegment[], title: string = "Document") {
  let plainText = `DOCUMENT: ${title}\n` + "=".repeat(40) + "\n\n";

  for (const seg of segments) {
    plainText += extractPlainTextFromSegment(seg) + "\n\n";
  }

  const blob = new Blob([plainText], { type: "text/plain;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${title.replace(/\s+/g, "_")}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
