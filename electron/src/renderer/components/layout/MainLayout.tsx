import React, { useState } from 'react';
import {
  Box,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Tooltip,
  Divider,
  Typography,
  IconButton,
  useTheme,
  alpha,
} from '@mui/material';
import {
  FolderOpen,
  Description,
  Analytics,
  Settings,
  Dashboard,
  ChevronLeft,
  ChevronRight,
  Storage,
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useAppSelector } from '../../hooks/useAppSelector';
import { useAppDispatch } from '../../hooks/useAppDispatch';
import { setSidebarCollapsed } from '../../store/slices/uiSlice';

const SIDEBAR_WIDTH = 240;
const SIDEBAR_COLLAPSED_WIDTH = 64;

interface NavItem {
  label: string;
  path: string;
  icon: React.ReactNode;
  badge?: number;
}

const navItems: NavItem[] = [
  { label: 'Dashboard', path: '/dashboard', icon: <Dashboard /> },
  { label: 'Project Scanner', path: '/scanner', icon: <FolderOpen /> },
  { label: 'Export', path: '/export', icon: <Description /> },
  { label: 'Statistics', path: '/stats', icon: <Analytics /> },
  { label: 'Settings', path: '/settings', icon: <Settings /> },
];

interface Props {
  children: React.ReactNode;
}

export const MainLayout: React.FC<Props> = ({ children }) => {
  const theme = useTheme();
  const navigate = useNavigate();
  const location = useLocation();
  const dispatch = useAppDispatch();
  const collapsed = useAppSelector((s) => s.ui.sidebarCollapsed);
  const projectName = useAppSelector((s) => s.project.name);
  const width = collapsed ? SIDEBAR_COLLAPSED_WIDTH : SIDEBAR_WIDTH;

  const isActive = (path: string) => location.pathname === path;

  return (
    <Box sx={{ display: 'flex', width: '100%', height: '100vh' }}>
      {/* Sidebar */}
      <Drawer
        variant="permanent"
        sx={{
          width,
          flexShrink: 0,
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          '& .MuiDrawer-paper': {
            width,
            overflow: 'hidden',
            boxSizing: 'border-box',
            borderRight: `1px solid ${theme.palette.divider}`,
            bgcolor: theme.palette.mode === 'dark' ? '#0d1117' : '#f8f9fa',
            transition: theme.transitions.create('width', {
              easing: theme.transitions.easing.sharp,
              duration: theme.transitions.duration.enteringScreen,
            }),
          },
        }}
      >
        {/* Logo area */}
        <Box
          sx={{
            display: 'flex',
            alignItems: 'center',
            px: 2,
            py: 1.5,
            minHeight: 56,
            borderBottom: `1px solid ${theme.palette.divider}`,
          }}
        >
          <Storage sx={{ color: theme.palette.primary.main, fontSize: 28, mr: collapsed ? 0 : 1.5 }} />
          {!collapsed && (
            <Box>
              <Typography variant="subtitle1" fontWeight={700} lineHeight={1.2}>
                RepoDoc
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Pro
              </Typography>
            </Box>
          )}
        </Box>

        {/* Project name */}
        {!collapsed && projectName && (
          <Box sx={{ px: 2, py: 1, bgcolor: alpha(theme.palette.primary.main, 0.08) }}>
            <Typography variant="caption" color="text.secondary" noWrap>
              Current Project
            </Typography>
            <Typography variant="body2" fontWeight={600} noWrap title={projectName}>
              {projectName}
            </Typography>
          </Box>
        )}

        {/* Navigation */}
        <List sx={{ pt: 1, flex: 1 }}>
          {navItems.map((item) => (
            <ListItem key={item.path} disablePadding>
              <Tooltip title={collapsed ? item.label : ''} placement="right">
                <ListItemButton
                  onClick={() => navigate(item.path)}
                  selected={isActive(item.path)}
                  sx={{
                    mx: 1,
                    mb: 0.5,
                    borderRadius: 1.5,
                    minHeight: 44,
                    justifyContent: collapsed ? 'center' : 'flex-start',
                    px: collapsed ? 1.5 : 2,
                    '&.Mui-selected': {
                      bgcolor: alpha(theme.palette.primary.main, 0.12),
                      color: theme.palette.primary.main,
                      '& .MuiListItemIcon-root': {
                        color: theme.palette.primary.main,
                      },
                    },
                    '&:hover': {
                      bgcolor: alpha(theme.palette.primary.main, 0.08),
                    },
                  }}
                >
                  <ListItemIcon
                    sx={{
                      minWidth: collapsed ? 0 : 36,
                      mr: collapsed ? 0 : 1,
                      color: isActive(item.path)
                        ? theme.palette.primary.main
                        : theme.palette.text.secondary,
                    }}
                  >
                    {item.icon}
                  </ListItemIcon>
                  {!collapsed && (
                    <ListItemText
                      primary={item.label}
                      primaryTypographyProps={{ variant: 'body2', fontWeight: isActive(item.path) ? 600 : 400 }}
                    />
                  )}
                </ListItemButton>
              </Tooltip>
            </ListItem>
          ))}
        </List>

        <Divider />

        {/* Collapse toggle */}
        <Box sx={{ p: 1, display: 'flex', justifyContent: collapsed ? 'center' : 'flex-end' }}>
          <IconButton
            size="small"
            onClick={() => dispatch(setSidebarCollapsed(!collapsed))}
            sx={{ color: theme.palette.text.secondary }}
          >
            {collapsed ? <ChevronRight fontSize="small" /> : <ChevronLeft fontSize="small" />}
          </IconButton>
        </Box>
      </Drawer>

      {/* Main content */}
      <Box
        component="main"
        sx={{
          flex: 1,
          overflow: 'auto',
          display: 'flex',
          flexDirection: 'column',
          bgcolor: theme.palette.background.default,
        }}
      >
        {children}
      </Box>
    </Box>
  );
};
