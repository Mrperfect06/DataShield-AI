import React from 'react';
import { 
  ShieldAlert, 
  CheckCircle2, 
  AlertTriangle, 
  UserCheck, 
  Search, 
  Scale, 
  FileCheck2, 
  Flame,
  Terminal,
  FileCode
} from 'lucide-react';

/**
 * FormattedReport: Clean Light SaaS markdown renderer specifically tuned for
 * cybersecurity threat reports, incident analyses, and forensic audits.
 */
export default function FormattedReport({ content }) {
  if (!content) {
    return (
      <div className="text-slate-400 italic text-xs py-4 text-center">
        No forensic narrative generated yet.
      </div>
    );
  }

  const lines = content.split('\n');
  const elements = [];
  let tableBuffer = [];
  let inCodeBlock = false;
  let codeBuffer = [];

  const flushTable = () => {
    if (tableBuffer.length === 0) return;
    const headerRow = tableBuffer[0];
    const dataRows = tableBuffer.slice(2); // Skip separator row

    elements.push(
      <div key={`table-${elements.length}`} className="my-3 overflow-x-auto rounded-xl border border-slate-200 bg-white shadow-2xs">
        <table className="w-full text-left text-xs font-mono">
          <thead className="bg-slate-50 text-slate-700 border-b border-slate-200 uppercase tracking-wider text-[11px]">
            <tr>
              {headerRow.map((cell, idx) => (
                <th key={idx} className="px-3.5 py-2.5 font-bold text-slate-800">
                  {cell.trim()}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {dataRows.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-slate-50/80 transition-colors">
                {row.map((cell, cIdx) => (
                  <td key={cIdx} className="px-3.5 py-2 text-slate-700">
                    {formatInlineText(cell.trim())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableBuffer = [];
  };

  const flushCode = () => {
    if (codeBuffer.length === 0) return;
    elements.push(
      <div key={`code-${elements.length}`} className="my-3 bg-slate-900 text-emerald-400 p-3.5 rounded-xl border border-slate-800 font-mono text-xs overflow-x-auto shadow-xs">
        <pre>{codeBuffer.join('\n')}</pre>
      </div>
    );
    codeBuffer = [];
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code block fences
    if (line.trim().startsWith('```')) {
      if (inCodeBlock) {
        flushCode();
        inCodeBlock = false;
      } else {
        if (tableBuffer.length > 0) flushTable();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      continue;
    }

    // Markdown Table check
    if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
      const cells = line
        .trim()
        .slice(1, -1)
        .split('|')
        .map((c) => c.trim());
      tableBuffer.push(cells);
      continue;
    } else if (tableBuffer.length > 0) {
      flushTable();
    }

    // Empty lines
    if (!line.trim()) {
      elements.push(<div key={`sp-${i}`} className="h-2" />);
      continue;
    }

    // Level 2 Headings (## Heading)
    if (line.startsWith('## ')) {
      const title = line.replace(/^##\s+/, '').trim();
      let icon = <Flame className="h-4 w-4 text-orange-600" />;
      let badgeStyle = "bg-orange-50 text-orange-800 border-orange-200";

      if (title.includes('Incident') || title.includes('🚨') || title.includes('Threat')) {
        icon = <ShieldAlert className="h-4 w-4 text-rose-600" />;
        badgeStyle = "bg-rose-50 text-rose-800 border-rose-200";
      } else if (title.includes('🟢') || title.includes('Audit') || title.includes('Baseline') || title.includes('Safe')) {
        icon = <CheckCircle2 className="h-4 w-4 text-emerald-600" />;
        badgeStyle = "bg-emerald-50 text-emerald-800 border-emerald-200";
      } else if (title.includes('👤') || title.includes('Identity') || title.includes('Context')) {
        icon = <UserCheck className="h-4 w-4 text-blue-600" />;
        badgeStyle = "bg-blue-50 text-blue-800 border-blue-200";
      } else if (title.includes('🔍') || title.includes('Telemetry') || title.includes('Anomaly')) {
        icon = <Search className="h-4 w-4 text-purple-600" />;
        badgeStyle = "bg-purple-50 text-purple-800 border-purple-200";
      } else if (title.includes('⚖️') || title.includes('Policy') || title.includes('Regulatory')) {
        icon = <Scale className="h-4 w-4 text-amber-700" />;
        badgeStyle = "bg-amber-50 text-amber-800 border-amber-200";
      } else if (title.includes('🪤') || title.includes('Honey')) {
        icon = <AlertTriangle className="h-4 w-4 text-rose-600" />;
        badgeStyle = "bg-rose-100 text-rose-900 border-rose-300 font-extrabold";
      } else if (title.includes('🛡️') || title.includes('Recommended') || title.includes('Actions')) {
        icon = <FileCheck2 className="h-4 w-4 text-teal-600" />;
        badgeStyle = "bg-teal-50 text-teal-800 border-teal-200";
      }

      elements.push(
        <div key={`h2-${i}`} className="mt-4 mb-2 flex items-center space-x-2">
          <div className={`flex items-center space-x-1.5 px-3 py-1 rounded-xl border text-xs font-bold uppercase tracking-wider ${badgeStyle}`}>
            {icon}
            <span>{title}</span>
          </div>
          <div className="flex-1 h-px bg-slate-200"></div>
        </div>
      );
      continue;
    }

    // Level 3 Headings (### Heading)
    if (line.startsWith('### ')) {
      const title = line.replace(/^###\s+/, '').trim();
      elements.push(
        <h4 key={`h3-${i}`} className="text-xs font-bold text-slate-800 mt-2.5 mb-1 tracking-wide flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600"></span>
          <span>{title}</span>
        </h4>
      );
      continue;
    }

    // Bullet points (- or *)
    if (line.trim().startsWith('- ') || line.trim().startsWith('* ')) {
      const text = line.trim().replace(/^[-*]\s+/, '');
      elements.push(
        <div key={`li-${i}`} className="flex items-start space-x-2 text-xs text-slate-700 my-1 pl-1">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600 mt-1.5 shrink-0"></span>
          <div className="flex-1 leading-relaxed">{formatInlineText(text)}</div>
        </div>
      );
      continue;
    }

    // Numbered list items (1. 2.)
    if (/^\d+\.\s+/.test(line.trim())) {
      const match = line.trim().match(/^(\d+)\.\s+(.*)/);
      if (match) {
        const num = match[1];
        const text = match[2];
        elements.push(
          <div key={`num-${i}`} className="flex items-start space-x-2.5 text-xs text-slate-700 my-1.5 bg-white p-2.5 rounded-xl border border-slate-200 shadow-2xs">
            <span className="h-4 w-4 rounded-full bg-blue-100 text-blue-700 text-[10px] font-mono flex items-center justify-center shrink-0 mt-0.5 font-bold">
              {num}
            </span>
            <div className="flex-1 leading-relaxed font-medium">{formatInlineText(text)}</div>
          </div>
        );
        continue;
      }
    }

    // Blockquote (> Quote)
    if (line.trim().startsWith('>')) {
      const quote = line.trim().replace(/^>\s*/, '');
      elements.push(
        <div key={`bq-${i}`} className="my-2 p-3 bg-blue-50/60 border-l-3 border-blue-600 rounded-r-xl text-xs italic text-slate-700">
          {formatInlineText(quote)}
        </div>
      );
      continue;
    }

    // Standard paragraph
    elements.push(
      <p key={`p-${i}`} className="text-xs text-slate-700 leading-relaxed my-1">
        {formatInlineText(line)}
      </p>
    );
  }

  // Flush remaining table
  if (tableBuffer.length > 0) flushTable();
  if (codeBuffer.length > 0) flushCode();

  return <div className="space-y-1 font-sans">{elements}</div>;
}

/**
 * Parses bold (**text**), code (`text`), and links in inline markdown for light theme.
 */
function formatInlineText(text) {
  if (!text) return null;

  const parts = [];
  const regex = /(\*\*.*?\*\*|`.*?`)/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index));
    }

    const token = match[0];
    if (token.startsWith('**') && token.endsWith('**')) {
      const content = token.slice(2, -2);
      parts.push(
        <strong key={`b-${match.index}`} className="font-bold text-slate-900">
          {content}
        </strong>
      );
    } else if (token.startsWith('`') && token.endsWith('`')) {
      const code = token.slice(1, -1);
      let chipStyle = "bg-slate-100 text-slate-800 border-slate-200";
      if (code.includes('CANARY') || code.includes('TRAP')) {
        chipStyle = "bg-rose-100 text-rose-800 border-rose-300 font-bold";
      } else if (code.includes('SELECT') || code.includes('CRITICAL')) {
        chipStyle = "bg-purple-100 text-purple-800 border-purple-200 font-semibold";
      }

      parts.push(
        <code
          key={`c-${match.index}`}
          className={`px-1.5 py-0.5 rounded text-[11px] font-mono border mx-0.5 ${chipStyle}`}
        >
          {code}
        </code>
      );
    }
    lastIdx = regex.lastIndex;
  }

  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx));
  }

  return parts.length > 0 ? parts : text;
}
