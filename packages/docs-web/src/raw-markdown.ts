export function hasRawMarkdownMirror(filePath: string | undefined): filePath is string {
  return filePath !== undefined && !filePath.endsWith('.mdx');
}
