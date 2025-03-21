/**
 * Convert Markdown text to HTML.
 * This is a basic implementation and may not cover all Markdown features.
 * You can use a library like `markdown-it` for more advanced Markdown parsing.
 *
 * @param {string} markdown - The Markdown text to convert.
 * @returns {string} - The converted HTML.
 */
export function convertMarkdownToHtml(markdown) {
  if (!markdown) return '';

  // Normalize line endings
  markdown = markdown.replace(/\r\n|\r/g, '\n');

  // Split the markdown into lines
  const lines = markdown.split('\n');

  // Process each line individually
  const processedLines = lines.map(line => {
    // Process headers first
    line = line.replace(/^##### (.*$)/gim, '<h5>$1</h5>');
    line = line.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    line = line.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    line = line.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    line = line.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // Process other markdown elements
    line = line.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>'); // Bold text
    line = line.replace(/\*(.*?)\*/g, '<em>$1</em>'); // Italic text
    line = line.replace(/`(.*?)`/g, '<code>$1</code>'); // Inline code
    line = line.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2">$1</a>'); // Links
    line = line.replace(/^\* (.*$)/gim, '<li>$1</li>'); // Unordered lists
    line = line.replace(/^\d\. (.*$)/gim, '<li>$1</li>'); // Ordered lists
    line = line.replace(/__(.*?)__/g, '<u>$1</u>'); // Underline

    return line;
  });

  // Join the processed lines back together
  let html = processedLines.join('<br>');

  // Wrap lists
  html = html.replace(/<li>(.*?)<\/li>/g, '<ul><li>$1</li></ul>');
  html = html.replace(/<\/ul><ul>/g, ''); // Combine adjacent lists

  return html;
}

