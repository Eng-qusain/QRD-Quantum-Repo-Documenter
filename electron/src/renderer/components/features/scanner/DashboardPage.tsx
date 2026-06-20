import React, { useCallback } from 'react';
import {
  Box,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  Stack,
  useTheme,
  alpha,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
} from '@mui/material';
import {
  FolderOpen,
  Description,
  Code,
  Analytics,
  Schedule,
  InsertDriveFile,
  PlayArrow,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useAppDispatch, useAppSelector } from '../../../store/hooks';
import { setProjectPath, scanProject } from '../../../store/slices/projectSlice';
import { addNotification } from '../../../store/slices/uiSlice';

export const DashboardPage: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { isLoaded, stats, name, path, isScanning, scanProgress } = useAppSelector(
    (s) => s.project
  );
  const excludePatterns = useAppSelector((s) => s.project.excludePatterns);

  const handleOpenProject = useCallback(async () => {
    const selected = await window.electron?.openDirectory();
    if (!selected) return;

    dispatch(setProjectPath(selected));
    await window.electron?.addRecentProject(selected);

    try {
      await dispatch(
        scanProject({ path: selected, excludePatterns })
      ).unwrap();
      dispatch(addNotification({ type: 'success', message: 'Project scanned successfully' }));
      navigate('/scanner');
    } catch (err) {
      dispatch(addNotification({ type: 'error', message: `Scan failed: ${err}` }));
    }
  }, [dispatch, navigate, excludePatterns]);

  const statCards = stats
    ? [
        { label: 'Total Files', value: stats.totalFiles.toLocaleString(), icon: <InsertDriveFile />, color: theme.palette.primary.main },
        { label: 'Lines of Code', value: stats.totalLines.toLocaleString(), icon: <Code />, color: theme.palette.secondary.main },
        { label: 'Languages', value: Object.keys(stats.languageDistribution).length, icon: <Analytics />, color: theme.palette.success.main },
        { label: 'Total Size', value: formatSize(stats.totalSize), icon: <Description />, color: theme.palette.warning.main },
      ]
    : [];

  return (
    <Box sx={{ p: 4, maxWidth: 1200, mx: 'auto' }}>
      {/* Header */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h4" fontWeight={700} gutterBottom>
          {isLoaded ? `Project: ${name}` : 'Welcome to RepoDoc Pro'}
        </Typography>
        <Typography variant="body1" color="text.secondary">
          {isLoaded
            ? `${path}`
            : 'Convert your software projects into professional PDF documentation'}
        </Typography>
      </Box>

      {/* Scanning progress */}
      {isScanning && (
        <Card sx={{ mb: 3, p: 2 }}>
          <Typography variant="body2" gutterBottom>
            Scanning project... {Math.round(scanProgress)}%
          </Typography>
          <LinearProgress variant="determinate" value={scanProgress} />
        </Card>
      )}

      {/* Open Project CTA */}
      {!isLoaded && !isScanning && (
        <Card
          sx={{
            mb: 4,
            p: 4,
            textAlign: 'center',
            border: `2px dashed ${alpha(theme.palette.primary.main, 0.3)}`,
            bgcolor: alpha(theme.palette.primary.main, 0.03),
            cursor: 'pointer',
            transition: 'all 0.2s',
            '&:hover': {
              borderColor: theme.palette.primary.main,
              bgcolor: alpha(theme.palette.primary.main, 0.06),
            },
          }}
          onClick={handleOpenProject}
        >
          <FolderOpen sx={{ fontSize: 64, color: theme.palette.primary.main, mb: 2 }} />
          <Typography variant="h5" fontWeight={600} gutterBottom>
            Open a Project
          </Typography>
          <Typography variant="body2" color="text.secondary" mb={3}>
            Select a folder containing your source code, scripts, or data files
          </Typography>
          <Button variant="contained" size="large" startIcon={<FolderOpen />}>
            Choose Project Directory
          </Button>
        </Card>
      )}

      {/* Stats cards */}
      {isLoaded && stats && (
        <>
          <Grid container spacing={3} sx={{ mb: 4 }}>
            {statCards.map((card) => (
              <Grid item xs={12} sm={6} md={3} key={card.label}>
                <Card>
                  <CardContent>
                    <Stack direction="row" alignItems="center" spacing={1.5}>
                      <Box
                        sx={{
                          p: 1,
                          borderRadius: 1.5,
                          bgcolor: alpha(card.color, 0.12),
                          color: card.color,
                          display: 'flex',
                        }}
                      >
                        {card.icon}
                      </Box>
                      <Box>
                        <Typography variant="h5" fontWeight={700}>
                          {card.value}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {card.label}
                        </Typography>
                      </Box>
                    </Stack>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>

          {/* Language distribution */}
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Language Distribution
                  </Typography>
                  <Stack spacing={1}>
                    {Object.entries(stats.languageDistribution)
                      .sort(([, a], [, b]) => b - a)
                      .slice(0, 8)
                      .map(([lang, count]) => {
                        const pct = Math.round((count / stats.totalFiles) * 100);
                        return (
                          <Box key={lang}>
                            <Stack direction="row" justifyContent="space-between" mb={0.5}>
                              <Typography variant="body2">{lang}</Typography>
                              <Typography variant="body2" color="text.secondary">
                                {count} files ({pct}%)
                              </Typography>
                            </Stack>
                            <LinearProgress
                              variant="determinate"
                              value={pct}
                              sx={{ height: 4, borderRadius: 2 }}
                            />
                          </Box>
                        );
                      })}
                  </Stack>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" fontWeight={600} gutterBottom>
                    Largest Files
                  </Typography>
                  <List dense disablePadding>
                    {stats.largestFiles.slice(0, 8).map((file) => (
                      <ListItem key={file.path} disablePadding sx={{ mb: 0.5 }}>
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          <InsertDriveFile fontSize="small" color="action" />
                        </ListItemIcon>
                        <ListItemText
                          primary={file.path.split('/').pop()}
                          secondary={`${file.lines.toLocaleString()} lines · ${formatSize(file.size)}`}
                          primaryTypographyProps={{ variant: 'body2', noWrap: true }}
                          secondaryTypographyProps={{ variant: 'caption' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Action buttons */}
          <Stack direction="row" spacing={2} mt={4}>
            <Button
              variant="contained"
              size="large"
              startIcon={<PlayArrow />}
              onClick={() => navigate('/export')}
            >
              Export Documentation
            </Button>
            <Button variant="outlined" startIcon={<FolderOpen />} onClick={handleOpenProject}>
              Open Different Project
            </Button>
            <Button variant="outlined" startIcon={<Analytics />} onClick={() => navigate('/scanner')}>
              Browse Files
            </Button>
          </Stack>
        </>
      )}

      {/* Feature highlights (no project loaded) */}
      {!isLoaded && !isScanning && (
        <Grid container spacing={3} mt={2}>
          {FEATURES.map((f) => (
            <Grid item xs={12} sm={6} md={4} key={f.title}>
              <Card sx={{ height: '100%' }}>
                <CardContent>
                  <Box sx={{ color: theme.palette.primary.main, mb: 1 }}>{f.icon}</Box>
                  <Typography variant="subtitle1" fontWeight={600} gutterBottom>
                    {f.title}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {f.description}
                  </Typography>
                  {f.tags && (
                    <Stack direction="row" flexWrap="wrap" gap={0.5} mt={1.5}>
                      {f.tags.map((t) => (
                        <Chip key={t} label={t} size="small" variant="outlined" />
                      ))}
                    </Stack>
                  )}
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`;
}

const FEATURES = [
  {
    icon: <Code sx={{ fontSize: 32 }} />,
    title: 'Source Code Export',
    description: 'Syntax-highlighted code with line numbers, language detection, and metadata.',
    tags: ['Python', 'JS', 'TS', 'YAML', 'SQL', '+9'],
  },
  {
    icon: <Analytics sx={{ fontSize: 32 }} />,
    title: 'AI Documentation',
    description: 'Auto-generate summaries, purpose, functions, inputs/outputs per file.',
    tags: ['Claude', 'GPT-4'],
  },
  {
    icon: <Description sx={{ fontSize: 32 }} />,
    title: 'Multiple Export Modes',
    description: 'Single PDF, folder-based PDFs, per-file, or full documentation package.',
    tags: ['Single', 'Folder', 'Package'],
  },
  {
    icon: <Schedule sx={{ fontSize: 32 }} />,
    title: 'Petroleum Data',
    description: 'LAS, DLIS, production data with well log plots and diagnostic charts.',
    tags: ['LAS', 'DLIS', 'LIS'],
  },
  {
    icon: <InsertDriveFile sx={{ fontSize: 32 }} />,
    title: 'Data Files',
    description: 'CSV, Excel, Parquet with statistics, schema, and chart previews.',
    tags: ['CSV', 'XLSX', 'Parquet'],
  },
  {
    icon: <FolderOpen sx={{ fontSize: 32 }} />,
    title: 'Large Repo Support',
    description: 'Handles repositories with 100,000+ files using background workers.',
    tags: ['100K+ files', 'Async'],
  },
];
