import { app, BrowserWindow, ipcMain, dialog, shell, Menu } from 'electron';
import { autoUpdater } from 'electron-updater';
import log from 'electron-log';
import Store from 'electron-store';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs';

// ─── Logging ────────────────────────────────────────────────────────────────
log.transports.file.level = 'info';
log.transports.console.level = 'debug';
autoUpdater.logger = log;

// ─── Store ──────────────────────────────────────────────────────────────────
const store = new Store({
  defaults: {
    windowBounds: { width: 1440, height: 900 },
    theme: 'dark',
    backendPort: 8765,
    recentProjects: [],
    exportDefaults: {
      mode: 'single',
      includeAI: true,
      includeCharts: true,
    },
  },
});

// ─── State ──────────────────────────────────────────────────────────────────
let mainWindow: BrowserWindow | null = null;
let backendProcess: ChildProcess | null = null;
const BACKEND_PORT = store.get('backendPort') as number;
const isDev = process.env.NODE_ENV === 'development';

// ─── Backend Management ─────────────────────────────────────────────────────
function getBackendPath(): string {
  if (isDev) {
    return path.join(__dirname, '../../backend');
  }
  return path.join(process.resourcesPath, 'backend');
}

function getPythonPath(): string {
  const backendPath = getBackendPath();

  // Prefer the bundled venv (created during CI build)
  const venvPaths: Record<string, string> = {
    win32: path.join(backendPath, '.venv', 'Scripts', 'python.exe'),
    darwin: path.join(backendPath, '.venv', 'bin', 'python'),
    linux: path.join(backendPath, '.venv', 'bin', 'python'),
  };

  const venvPython = venvPaths[process.platform];
  if (venvPython && fs.existsSync(venvPython)) {
    log.info(`Using bundled venv Python: ${venvPython}`);
    return venvPython;
  }

  // Fall back to system Python — install deps on first run
  log.warn('Bundled .venv not found — falling back to system Python');
  const systemPython = process.platform === 'win32' ? 'python' : 'python3';
  return systemPython;
}

async function ensureDependencies(): Promise<void> {
  const backendPath = getBackendPath();
  const venvPaths: Record<string, string> = {
    win32: path.join(backendPath, '.venv', 'Scripts', 'python.exe'),
    darwin: path.join(backendPath, '.venv', 'bin', 'python'),
    linux: path.join(backendPath, '.venv', 'bin', 'python'),
  };

  const venvPython = venvPaths[process.platform];
  if (venvPython && fs.existsSync(venvPython)) {
    return; // Already have bundled venv, nothing to do
  }

  log.info('Creating Python venv and installing dependencies (first run)...');
  mainWindow?.webContents.send('backend:installing');

  const systemPython = process.platform === 'win32' ? 'python' : 'python3';
  const venvDir = path.join(backendPath, '.venv');
  const requirementsTxt = path.join(backendPath, 'requirements.txt');

  await new Promise<void>((resolve, reject) => {
    const proc = spawn(systemPython, ['-m', 'venv', venvDir], { cwd: backendPath });
    proc.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`venv creation failed: ${code}`)));
    proc.stderr?.on('data', (d) => log.error(`[venv] ${d}`));
  });

  const pipPath = process.platform === 'win32'
    ? path.join(venvDir, 'Scripts', 'pip.exe')
    : path.join(venvDir, 'bin', 'pip');

  await new Promise<void>((resolve, reject) => {
    const proc = spawn(pipPath, ['install', '-r', requirementsTxt, '--quiet'], { cwd: backendPath });
    proc.on('exit', (code) => code === 0 ? resolve() : reject(new Error(`pip install failed: ${code}`)));
    proc.stderr?.on('data', (d) => log.error(`[pip] ${d}`));
  });

  log.info('Dependencies installed successfully');
}

async function startBackend(): Promise<void> {
  const pythonPath = getPythonPath();
  const backendPath = getBackendPath();
  const mainScript = path.join(backendPath, 'src', 'main.py');

  log.info(`Starting backend: ${pythonPath} ${mainScript}`);
  log.info(`Backend port: ${BACKEND_PORT}`);

  backendProcess = spawn(pythonPath, [mainScript, '--port', String(BACKEND_PORT)], {
    cwd: backendPath,
    env: {
      ...process.env,
      PYTHONPATH: path.join(backendPath, 'src'),
      REPODOC_PORT: String(BACKEND_PORT),
      REPODOC_ENV: isDev ? 'development' : 'production',
    },
  });

  backendProcess.stdout?.on('data', (data) => {
    log.info(`[Backend] ${data.toString().trim()}`);
  });

  backendProcess.stderr?.on('data', (data) => {
    log.error(`[Backend Error] ${data.toString().trim()}`);
  });

  backendProcess.on('exit', (code) => {
    log.warn(`Backend exited with code: ${code}`);
    if (code !== 0 && mainWindow) {
      mainWindow.webContents.send('backend:crashed', { code });
    }
  });

  // Wait for backend to be ready
  await waitForBackend();
}

async function waitForBackend(retries = 30, delayMs = 500): Promise<void> {
  for (let i = 0; i < retries; i++) {
    try {
      const { default: http } = await import('http');
      await new Promise<void>((resolve, reject) => {
        const req = http.get(`http://localhost:${BACKEND_PORT}/health`, (res) => {
          if (res.statusCode === 200) resolve();
          else reject(new Error(`Status: ${res.statusCode}`));
        });
        req.on('error', reject);
        req.setTimeout(1000, () => {
          req.destroy();
          reject(new Error('Timeout'));
        });
      });
      log.info('Backend is ready');
      return;
    } catch {
      await new Promise((r) => setTimeout(r, delayMs));
    }
  }
  throw new Error('Backend failed to start within timeout');
}

function stopBackend(): void {
  if (backendProcess) {
    log.info('Stopping backend process');
    backendProcess.kill('SIGTERM');
    backendProcess = null;
  }
}

// ─── Window Management ───────────────────────────────────────────────────────
function createWindow(): void {
  const { width, height } = store.get('windowBounds') as { width: number; height: number };
  const theme = store.get('theme') as string;

  mainWindow = new BrowserWindow({
    width,
    height,
    minWidth: 1024,
    minHeight: 768,
    show: false,
    titleBarStyle: process.platform === 'darwin' ? 'hiddenInset' : 'default',
    backgroundColor: theme === 'dark' ? '#0d1117' : '#ffffff',
    webPreferences: {
      preload: path.join(__dirname, '../preload/preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      webSecurity: true,
    },
    icon: path.join(__dirname, '../../resources/icon.png'),
  });

  // Load the app
  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools();
  } else {
    mainWindow.loadFile(path.join(__dirname, '../renderer/index.html'));
  }

  mainWindow.once('ready-to-show', () => {
    mainWindow!.show();
    mainWindow!.focus();
  });

  mainWindow.on('resize', () => {
    const [w, h] = mainWindow!.getSize();
    store.set('windowBounds', { width: w, height: h });
  });

  mainWindow.on('closed', () => {
    mainWindow = null;
  });

  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });

  buildMenu();
}

function buildMenu(): void {
  const template: Electron.MenuItemConstructorOptions[] = [
    {
      label: 'File',
      submenu: [
        {
          label: 'Open Project...',
          accelerator: 'CmdOrCtrl+O',
          click: () => mainWindow?.webContents.send('menu:open-project'),
        },
        { type: 'separator' },
        {
          label: 'Recent Projects',
          id: 'recent-projects',
          submenu: buildRecentProjectsMenu(),
        },
        { type: 'separator' },
        { label: 'Quit', accelerator: 'CmdOrCtrl+Q', click: () => app.quit() },
      ],
    },
    {
      label: 'Export',
      submenu: [
        {
          label: 'Single PDF',
          accelerator: 'CmdOrCtrl+Shift+E',
          click: () => mainWindow?.webContents.send('menu:export-single'),
        },
        {
          label: 'Documentation Package',
          click: () => mainWindow?.webContents.send('menu:export-package'),
        },
      ],
    },
    {
      label: 'View',
      submenu: [
        { label: 'Toggle Dark Mode', click: () => mainWindow?.webContents.send('menu:toggle-theme') },
        { type: 'separator' },
        { role: 'reload' },
        { role: 'toggleDevTools' },
        { type: 'separator' },
        { role: 'togglefullscreen' },
      ],
    },
    {
      label: 'Help',
      submenu: [
        {
          label: 'Documentation',
          click: () => shell.openExternal('https://repodoc.pro/docs'),
        },
        {
          label: 'Report Issue',
          click: () => shell.openExternal('https://github.com/repodoc/pro/issues'),
        },
        { type: 'separator' },
        { label: 'About RepoDoc Pro', click: () => mainWindow?.webContents.send('menu:about') },
      ],
    },
  ];

  if (process.platform === 'darwin') {
    template.unshift({
      label: app.name,
      submenu: [
        { role: 'about' },
        { type: 'separator' },
        { role: 'services' },
        { type: 'separator' },
        { role: 'hide' },
        { role: 'hideOthers' },
        { role: 'unhide' },
        { type: 'separator' },
        { role: 'quit' },
      ],
    });
  }

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function buildRecentProjectsMenu(): Electron.MenuItemConstructorOptions[] {
  const recent = store.get('recentProjects') as string[];
  if (!recent.length) return [{ label: 'No recent projects', enabled: false }];
  return recent.slice(0, 10).map((p) => ({
    label: p,
    click: () => mainWindow?.webContents.send('menu:open-recent', p),
  }));
}

// ─── IPC Handlers ────────────────────────────────────────────────────────────
function registerIpcHandlers(): void {
  // File/Directory dialogs
  ipcMain.handle('dialog:open-directory', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ['openDirectory'],
      title: 'Select Project Directory',
    });
    return result.canceled ? null : result.filePaths[0];
  });

  ipcMain.handle('dialog:save-file', async (_, opts: { defaultPath?: string; filters?: Electron.FileFilter[] }) => {
    const result = await dialog.showSaveDialog(mainWindow!, {
      title: 'Save PDF',
      defaultPath: opts.defaultPath || 'documentation.pdf',
      filters: opts.filters || [{ name: 'PDF Files', extensions: ['pdf'] }],
    });
    return result.canceled ? null : result.filePath;
  });

  ipcMain.handle('dialog:open-save-directory', async () => {
    const result = await dialog.showOpenDialog(mainWindow!, {
      properties: ['openDirectory', 'createDirectory'],
      title: 'Select Output Directory',
    });
    return result.canceled ? null : result.filePaths[0];
  });

  // Shell operations
  ipcMain.handle('shell:open-path', async (_, filePath: string) => {
    await shell.openPath(filePath);
  });

  ipcMain.handle('shell:show-item', async (_, filePath: string) => {
    shell.showItemInFolder(filePath);
  });

  // Store operations
  ipcMain.handle('store:get', (_, key: string) => store.get(key));
  ipcMain.handle('store:set', (_, key: string, value: unknown) => store.set(key, value));

  // Recent projects
  ipcMain.handle('projects:add-recent', (_, projectPath: string) => {
    const recent = store.get('recentProjects') as string[];
    const updated = [projectPath, ...recent.filter((p) => p !== projectPath)].slice(0, 10);
    store.set('recentProjects', updated);
    buildMenu();
  });

  // Backend info
  ipcMain.handle('backend:port', () => BACKEND_PORT);
  ipcMain.handle('backend:restart', async () => {
    stopBackend();
    await startBackend();
  });

  // File system
  ipcMain.handle('fs:exists', (_, filePath: string) => fs.existsSync(filePath));
  ipcMain.handle('fs:read-file', (_, filePath: string) => fs.readFileSync(filePath, 'utf-8'));
}

// ─── App Lifecycle ───────────────────────────────────────────────────────────
app.whenReady().then(async () => {
  log.info('App starting...');

  try {
    await ensureDependencies();
    await startBackend();
    log.info('Backend started successfully');
  } catch (err) {
    log.error('Failed to start backend:', err);
    dialog.showErrorBox(
      'Backend Error',
      `Failed to start the RepoDoc Pro backend.\n\nError: ${err}\n\nPlease ensure Python 3.10+ is installed and try again.`
    );
  }

  registerIpcHandlers();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });

  // Auto-update (production only)
  if (!isDev) {
    autoUpdater.checkForUpdatesAndNotify();
  }
});

app.on('window-all-closed', () => {
  stopBackend();
  if (process.platform !== 'darwin') app.quit();
});

app.on('before-quit', () => {
  stopBackend();
});

// ─── Auto-updater Events ─────────────────────────────────────────────────────
autoUpdater.on('update-available', () => {
  mainWindow?.webContents.send('updater:update-available');
});

autoUpdater.on('update-downloaded', () => {
  mainWindow?.webContents.send('updater:update-downloaded');
});

ipcMain.handle('updater:install', () => {
  autoUpdater.quitAndInstall();
});
