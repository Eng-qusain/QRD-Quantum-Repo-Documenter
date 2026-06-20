import React from 'react';
import { Box, Typography, IconButton, Chip, Stack, Tooltip, useTheme } from '@mui/material';
import { ContentCopy, OpenInNew, Code } from '@mui/icons-material';
import { Light as SyntaxHighlighter } from 'react-syntax-highlighter';
import { atomOneDark, atomOneLight } from 'react-syntax-highlighter/dist/esm/styles/hljs';
import python from 'react-syntax-highlighter/dist/esm/languages/hljs/python';
import javascript from 'react-syntax-highlighter/dist/esm/languages/hljs/javascript';
import typescript from 'react-syntax-highlighter/dist/esm/languages/hljs/typescript';
import bash from 'react-syntax-highlighter/dist/esm/languages/hljs/bash';
import sql from 'react-syntax-highlighter/dist/esm/languages/hljs/sql';
import yaml from 'react-syntax-highlighter/dist/esm/languages/hljs/yaml';
import json from 'react-syntax-highlighter/dist/esm/languages/hljs/json';
import xml from 'react-syntax-highlighter/dist/esm/languages/hljs/xml';
import css from 'react-syntax-highlighter/dist/esm/languages/hljs/css';
import markdown from 'react-syntax-highlighter/dist/esm/languages/hljs/markdown';
import { useAppSelector } from '../../../store/hooks';

// Register languages
SyntaxHighlighter.registerLanguage('python', python);
SyntaxHighlighter.registerLanguage('javascript', javascript);
SyntaxHighlighter.registerLanguage('typescript', typescript);
SyntaxHighlighter.registerLanguage('tsx', typescript);
SyntaxHighlighter.registerLanguage('jsx', javascript);
SyntaxHighlighter.registerLanguage('bash', bash);
SyntaxHighlighter.registerLanguage('sh', bash);
SyntaxHighlighter.registerLanguage('sql', sql);
SyntaxHighlighter.registerLanguage('yaml', yaml);
SyntaxHighlighter.registerLanguage('yml', yaml);
SyntaxHighlighter.registerLanguage('json', json);
SyntaxHighlighter.registerLanguage('xml', xml);
SyntaxHighlighter.registerLanguage('css', css);
SyntaxHighlighter.registerLanguage('md', markdown);

export const CodePreview: React.FC = () => {
  const theme = useTheme();
  const { selectedFileContent, selectedFilePath, previewLanguage } = useAppSelector((s) => s.scanner);
  const isDark = theme.palette.mode === 'dark';

  const handleCopy = () => {
    if (selectedFileContent) navigator.clipboard.writeText(selectedFileContent);
  };

  const handleOpen = () => {
    if (selectedFilePath) window.electron?.openPath(selectedFilePath);
  };

  if (!selectedFileContent) {
    return (
      <Box sx={{
        display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center',
        height: '100%', color: 'text.disabled',
      }}>
        <Code sx={{ fontSize: 48, mb: 1 }} />
        <Typography variant="body2">Select a file to preview</Typography>
      </Box>
    );
  }

  const fileName = selectedFilePath?.split('/').pop() || '';
  const lineCount = selectedFileContent.split('\n').length;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header bar */}
      <Box sx={{
        px: 2, py: 1,
        display: 'flex', alignItems: 'center', gap: 1,
        borderBottom: `1px solid ${theme.palette.divider}`,
        bgcolor: theme.palette.background.paper,
        flexShrink: 0,
      }}>
        <Typography variant="body2" fontWeight={600} noWrap sx={{ flex: 1 }}>
          {fileName}
        </Typography>
        <Stack direction="row" spacing={0.5}>
          <Chip label={previewLanguage.toUpperCase()} size="small" variant="outlined" />
          <Chip label={`${lineCount.toLocaleString()} lines`} size="small" />
        </Stack>
        <Tooltip title="Copy content">
          <IconButton size="small" onClick={handleCopy}><ContentCopy fontSize="small" /></IconButton>
        </Tooltip>
        <Tooltip title="Open in system editor">
          <IconButton size="small" onClick={handleOpen}><OpenInNew fontSize="small" /></IconButton>
        </Tooltip>
      </Box>

      {/* Code */}
      <Box sx={{ flex: 1, overflow: 'auto', fontSize: 12 }}>
        <SyntaxHighlighter
          language={previewLanguage}
          style={isDark ? atomOneDark : atomOneLight}
          showLineNumbers
          lineNumberStyle={{ color: '#666', fontSize: 11, paddingRight: 16, minWidth: 40 }}
          customStyle={{
            margin: 0,
            padding: '12px 0',
            background: isDark ? '#0d1117' : '#f6f8fa',
            fontSize: 12,
            fontFamily: '"Fira Code", "Cascadia Code", monospace',
            minHeight: '100%',
          }}
          wrapLongLines
        >
          {selectedFileContent}
        </SyntaxHighlighter>
      </Box>
    </Box>
  );
};
