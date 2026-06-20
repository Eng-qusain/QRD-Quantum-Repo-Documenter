import React, { useMemo, useState, useCallback } from 'react';
import {
  Box, List, ListItem, ListItemButton, ListItemIcon, ListItemText,
  Typography, Collapse, useTheme, alpha,
} from '@mui/material';
import {
  Folder, FolderOpen, InsertDriveFile, Code, DataObject,
  Image, Description, BubbleChart, ChevronRight, ExpandMore,
} from '@mui/icons-material';

interface FileNode {
  id: string; name: string; type: 'file' | 'directory';
  relative_path: string; path: string; extension?: string;
  language?: string; line_count?: number; size?: number;
  children?: FileNode[];
}

interface Props {
  fileTree: FileNode | null;
  flatFiles: FileNode[];
  searchQuery: string;
  viewMode: 'tree' | 'list';
  onFileSelect: (path: string) => void;
  selectedPath: string | null;
}

function getFileIcon(node: FileNode, expanded?: boolean) {
  if (node.type === 'directory') {
    return expanded
      ? <FolderOpen fontSize="small" sx={{ color: '#dcb67a' }} />
      : <Folder fontSize="small" sx={{ color: '#dcb67a' }} />;
  }
  const ext = node.extension || '';
  if (['.py', '.js', '.ts', '.tsx', '.sh', '.sql'].includes(ext)) return <Code fontSize="small" color="primary" />;
  if (['.json', '.yaml', '.yml', '.toml'].includes(ext)) return <DataObject fontSize="small" color="secondary" />;
  if (['.png', '.jpg', '.svg', '.webp'].includes(ext)) return <Image fontSize="small" color="success" />;
  if (['.md', '.txt', '.pdf'].includes(ext)) return <Description fontSize="small" color="action" />;
  if (['.las', '.dlis'].includes(ext)) return <BubbleChart fontSize="small" color="warning" />;
  return <InsertDriveFile fontSize="small" color="action" />;
}

// ─── Recursive Tree Node (custom — no external tree-view library) ────────────
const TreeNode: React.FC<{
  node: FileNode;
  depth: number;
  onFileSelect: (path: string) => void;
  selectedPath: string | null;
  defaultExpanded?: boolean;
}> = ({ node, depth, onFileSelect, selectedPath, defaultExpanded = false }) => {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(defaultExpanded || depth === 0);
  const isDir = node.type === 'directory';
  const hasChildren = isDir && node.children && node.children.length > 0;
  const isSelected = node.path === selectedPath;

  const handleClick = useCallback(() => {
    if (isDir) {
      setExpanded((e) => !e);
    } else {
      onFileSelect(node.path);
    }
  }, [isDir, node.path, onFileSelect]);

  return (
    <>
      <ListItemButton
        onClick={handleClick}
        selected={isSelected}
        dense
        sx={{
          py: 0.3,
          pl: 1 + depth * 1.5,
          pr: 1,
          minHeight: 28,
          '&.Mui-selected': { bgcolor: alpha(theme.palette.primary.main, 0.12) },
          '&:hover': { bgcolor: alpha(theme.palette.primary.main, 0.06) },
        }}
      >
        {isDir && (
          <Box
            sx={{
              width: 16, height: 16, display: 'flex',
              alignItems: 'center', justifyContent: 'center', flexShrink: 0, mr: 0.25,
              visibility: hasChildren ? 'visible' : 'hidden',
            }}
          >
            {expanded ? <ExpandMore sx={{ fontSize: 16 }} /> : <ChevronRight sx={{ fontSize: 16 }} />}
          </Box>
        )}
        <ListItemIcon sx={{ minWidth: 24, mr: 0.5 }}>
          {getFileIcon(node, expanded)}
        </ListItemIcon>
        <ListItemText
          primary={node.name}
          primaryTypographyProps={{
            variant: 'body2',
            noWrap: true,
            fontWeight: isDir ? 600 : 400,
            fontSize: 13,
          }}
        />
        {!isDir && node.line_count ? (
          <Typography variant="caption" color="text.disabled" sx={{ ml: 1, flexShrink: 0 }}>
            {node.line_count.toLocaleString()}L
          </Typography>
        ) : null}
      </ListItemButton>

      {hasChildren && (
        <Collapse in={expanded} timeout="auto" unmountOnExit>
          {node.children!.map((child) => (
            <TreeNode
              key={child.id || child.path}
              node={child}
              depth={depth + 1}
              onFileSelect={onFileSelect}
              selectedPath={selectedPath}
            />
          ))}
        </Collapse>
      )}
    </>
  );
};

// ─── Main Component ────────────────────────────────────────────────────────────
export const FileTreeView: React.FC<Props> = ({
  fileTree, flatFiles, searchQuery, viewMode, onFileSelect, selectedPath,
}) => {
  const theme = useTheme();

  const filteredFiles = useMemo(() => {
    if (!searchQuery) return flatFiles;
    const q = searchQuery.toLowerCase();
    return flatFiles.filter((f) => f.name.toLowerCase().includes(q) || f.relative_path.toLowerCase().includes(q));
  }, [flatFiles, searchQuery]);

  // List / search view — flat results
  if (viewMode === 'list' || searchQuery) {
    return (
      <List dense disablePadding>
        {filteredFiles.map((f) => (
          <ListItem key={f.id} disablePadding>
            <ListItemButton
              selected={f.path === selectedPath}
              onClick={() => onFileSelect(f.path)}
              sx={{
                py: 0.5, px: 1.5,
                '&.Mui-selected': { bgcolor: alpha(theme.palette.primary.main, 0.1) },
              }}
            >
              <ListItemIcon sx={{ minWidth: 28 }}>{getFileIcon(f)}</ListItemIcon>
              <ListItemText
                primary={f.name}
                secondary={f.relative_path}
                primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                secondaryTypographyProps={{ variant: 'caption', noWrap: true }}
              />
              {f.line_count && (
                <Typography variant="caption" color="text.disabled">
                  {f.line_count.toLocaleString()}L
                </Typography>
              )}
            </ListItemButton>
          </ListItem>
        ))}
        {filteredFiles.length === 0 && (
          <Box sx={{ p: 3, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">No files match</Typography>
          </Box>
        )}
      </List>
    );
  }

  // Tree view — custom recursive renderer
  return (
    <Box sx={{ py: 0.5 }}>
      {fileTree ? (
        <TreeNode
          node={fileTree}
          depth={0}
          onFileSelect={onFileSelect}
          selectedPath={selectedPath}
          defaultExpanded
        />
      ) : (
        <Typography variant="body2" color="text.secondary" sx={{ p: 2 }}>
          No files loaded
        </Typography>
      )}
    </Box>
  );
};
