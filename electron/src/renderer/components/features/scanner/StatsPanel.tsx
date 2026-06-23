import React from 'react';
import { Box, Grid, Card, CardContent, Typography, LinearProgress, Stack, Chip, useTheme, alpha } from '@mui/material';
import { InsertDriveFile, Code, Analytics, Storage } from '@mui/icons-material';

import { ProjectStats } from '../../../store/slices/projectSlice';

interface Props { stats: ProjectStats | null; }

function formatSize(bytes: number): string {
  if (!bytes) return '0 B';
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export const StatsPanel: React.FC<Props> = ({ stats }) => {
  const theme = useTheme();
  if (!stats) return <Typography color="text.secondary">No statistics available</Typography>;

  const topLanguages = Object.entries(stats.languageDistribution || {})
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 12);

  const topExtensions = Object.entries(stats.extensionDistribution || {})
    .sort(([, a], [, b]) => (b as number) - (a as number))
    .slice(0, 10);

  const summaryCards = [
    { label: 'Total Files', value: stats.totalFiles?.toLocaleString(), icon: <InsertDriveFile />, color: theme.palette.primary.main },
    { label: 'Lines of Code', value: stats.totalLines?.toLocaleString(), icon: <Code />, color: theme.palette.secondary.main },
    { label: 'Total Size', value: formatSize(stats.totalSizeBytes), icon: <Storage />, color: theme.palette.success.main },
    { label: 'Languages', value: topLanguages.length, icon: <Analytics />, color: theme.palette.warning.main },
  ];

  return (
    <Box>
      <Typography variant="h5" fontWeight={700} mb={3}>Project Statistics</Typography>

      <Grid container spacing={2} mb={4}>
        {summaryCards.map((c) => (
          <Grid item xs={6} md={3} key={c.label}>
            <Card>
              <CardContent sx={{ pb: '12px !important' }}>
                <Stack direction="row" alignItems="center" spacing={1.5}>
                  <Box sx={{ p: 1, borderRadius: 1.5, bgcolor: alpha(c.color, 0.12), color: c.color, display: 'flex' }}>
                    {c.icon}
                  </Box>
                  <Box>
                    <Typography variant="h5" fontWeight={700}>{c.value}</Typography>
                    <Typography variant="caption" color="text.secondary">{c.label}</Typography>
                  </Box>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Language Distribution</Typography>
              <Stack spacing={1.5}>
                {topLanguages.map(([lang, count]) => {
                  const pct = Math.round(((count as number) / stats.totalFiles) * 100);
                  return (
                    <Box key={lang}>
                      <Stack direction="row" justifyContent="space-between" mb={0.5}>
                        <Typography variant="body2">{lang}</Typography>
                        <Typography variant="caption" color="text.secondary">{count as number} ({pct}%)</Typography>
                      </Stack>
                      <LinearProgress variant="determinate" value={pct} sx={{ height: 6, borderRadius: 3 }} />
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
              <Typography variant="h6" fontWeight={600} gutterBottom>File Extensions</Typography>
              <Stack direction="row" flexWrap="wrap" gap={1} mt={1}>
                {topExtensions.map(([ext, count]) => (
                  <Chip
                    key={ext}
                    label={`${ext || '(none)'} · ${count}`}
                    size="small"
                    variant="outlined"
                    sx={{ fontFamily: 'monospace' }}
                  />
                ))}
              </Stack>
            </CardContent>
          </Card>

          <Card sx={{ mt: 3 }}>
            <CardContent>
              <Typography variant="h6" fontWeight={600} gutterBottom>Largest Files</Typography>
              <Stack spacing={0.5}>
                {(stats.largestFiles || []).slice(0, 8).map((f: any, i: number) => (
                  <Stack key={i} direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="body2" noWrap sx={{ flex: 1, mr: 1 }} title={f.path}>
                      {f.path?.split('/').pop()}
                    </Typography>
                    <Stack direction="row" spacing={1} flexShrink={0}>
                      <Chip label={`${f.lines?.toLocaleString()}L`} size="small" />
                      <Chip label={formatSize(f.size)} size="small" variant="outlined" />
                    </Stack>
                  </Stack>
                ))}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};
