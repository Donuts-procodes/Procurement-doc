import type { DocumentSegment, DocumentStyleConfig } from "../types";

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
      html += `<p>${text}</p>`;
    } else if (node.type === "image") {
      const src = node.attrs?.src || "";
      const alt = node.attrs?.alt || "Image";
      html += `<div style="text-align:center; margin:16px 0;"><img src="${src}" alt="${alt}" style="max-width:100%; border-radius:8px;" /></div>`;
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
      html += `<table border="1" style="border-collapse:collapse; width:100%; margin:16px 0;">`;
      for (const row of node.content || []) {
        html += `<tr>`;
        for (const cell of row.content || []) {
          const isHeader = cell.type === "tableHeader";
          const tag = isHeader ? "th" : "td";
          const cellContent = (cell.content || []).map((p: any) => renderTextWithMarks(p.content)).join("<br>");
          html += `<${tag} style="padding:8px; border:1px solid #dadce0;">${cellContent}</${tag}>`;
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

function extractPlainTextFromSegment(seg: DocumentSegment): string {
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

export function exportToPdf(
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

  const bodyHtml = segments.map((seg) => extractHtmlFromSegment(seg)).join("\n<hr style='border:none; border-top:1px solid #e0e0e0; margin:24px 0;'>\n");

  const watermarkHtml = styleConfig.watermark
    ? `<div style="position:fixed; top:50%; left:50%; transform:translate(-50%, -50%) rotate(-45deg); font-size:90px; color:rgba(0,0,0,0.06); font-weight:800; pointer-events:none; z-index:9999; text-transform:uppercase; white-space:nowrap;">${styleConfig.watermark}</div>`
    : "";

  const fullHtml = `
    <!DOCTYPE html>
    <html>
      <head>
        <meta charset="utf-8">
        <title>${title}</title>
        <style>
          @page { size: ${layoutSize}; margin: 20mm; }
          body {
            font-family: ${styleConfig.fontFamily || "Inter, sans-serif"};
            font-size: ${styleConfig.fontSize || "15px"};
            line-height: ${styleConfig.paragraphSpacing || "1.4"};
            color: #202124;
            background-color: ${styleConfig.pageColor || "#ffffff"};
            padding: 24px;
            margin: 0;
          }
          h1, h2, h3, h4 { color: ${styleConfig.accentColor || "#1a73e8"}; margin-top: 20px; }
          p { margin-bottom: 12px; }
          table { width: 100%; border-collapse: collapse; margin: 16px 0; }
          th { background-color: #f1f3f4; }
          th, td { border: 1px solid #dadce0; padding: 10px; text-align: left; }
          img { max-width: 100%; height: auto; display: block; margin: 0 auto; }
          @media print {
            body { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
          }
        </style>
      </head>
      <body>
        ${watermarkHtml}
        <h1 style="text-align:center; color:${styleConfig.accentColor || "#1a73e8"}; margin-bottom:30px;">${title}</h1>
        ${bodyHtml}
      </body>
    </html>
  `;

  printWindow.document.open();
  printWindow.document.write(fullHtml);
  printWindow.document.close();

  printWindow.onload = () => {
    printWindow.focus();
    printWindow.print();
  };
}

export function exportToWord(
  segments: DocumentSegment[],
  title: string = "Document",
  styleConfig: DocumentStyleConfig
) {
  const bodyHtml = segments.map((seg) => extractHtmlFromSegment(seg)).join("\n<br>\n");

  const wordContent = `
    <html xmlns:o='urn:schemas-microsoft-com:office:office' xmlns:w='urn:schemas-microsoft-com:office:word' xmlns='http://www.w3.org/TR/REC-html40'>
      <head>
        <meta charset='utf-8'>
        <title>${title}</title>
        <style>
          body {
            font-family: ${styleConfig.fontFamily || "Calibri, sans-serif"};
            font-size: ${styleConfig.fontSize || "15px"};
            line-height: ${styleConfig.paragraphSpacing || "1.4"};
            color: #202124;
          }
          h1, h2, h3 { color: ${styleConfig.accentColor || "#1a73e8"}; }
          table { border-collapse: collapse; width: 100%; margin: 16px 0; }
          td, th { border: 1px solid #dadce0; padding: 8px; }
          img { max-width: 100%; }
        </style>
      </head>
      <body>
        <h1 style="text-align:center; color:${styleConfig.accentColor || "#1a73e8"};">${title}</h1>
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
